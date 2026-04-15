# agents/planning.py
import os
import json
import copy
import requests
from pathlib import Path
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

from state import AppState
from mock_data import MOCK_DESIGN_CONCEPTS
from logger import log_event, log_stage_start, log_stage_end


def _use_real_api() -> bool:
    return bool(os.getenv("GROQ_API_KEY", "").strip())


CATEGORY_MAP = {
    "coffee table":   "coffee_table",
    "side table":     "side_table",
    "end table":      "side_table",
    "area rug":       "rug",
    "rug":            "rug",
    "floor rug":      "rug",
    "floor lamp":     "floor_lamp",
    "table lamp":     "floor_lamp",
    "lamp":           "floor_lamp",
    "lighting":       "floor_lamp",
    "accent chair":   "accent_chair",
    "armchair":       "accent_chair",
    "chair":          "accent_chair",
    "lounge chair":   "accent_chair",
    "throw blanket":  "throw_blanket",
    "blanket":        "throw_blanket",
    "throw":          "throw_blanket",
    "sectional sofa": "sofa",
    "sectional":      "sofa",
    "couch":          "sofa",
    "loveseat":       "sofa",
    "sofa":           "sofa",
    "bookcase":       "bookshelf",
    "bookshelf":      "bookshelf",
    "shelving unit":  "bookshelf",
    "shelving":       "bookshelf",
    "dining table":   "dining_table",
    "dining":         "dining_table",
    "bed frame":      "bed_frame",
    "bed":            "bed_frame",
    "side table":     "side_table",
    "nightstand":     "side_table",
}


def _normalize_categories(concepts: list) -> list:
    for c in concepts:
        for item in c.get("required_items", []):
            cat = item.get("category", "").lower().strip()
            item["category"] = CATEGORY_MAP.get(cat, cat.replace(" ", "_"))
    return concepts


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=8),
    retry=retry_if_exception_type(Exception),
    reraise=True
)
def _call_groq_planning(room_analysis: dict, budget: float, style: str) -> list:
    groq_key = os.getenv("GROQ_API_KEY", "")

    system_prompt = """You are an expert interior designer. Generate exactly 3 distinct design concepts as a JSON array.
Each concept must follow this schema exactly:
{
  "concept_name": string,
  "style_tags": [string],
  "color_palette": {"primary": hex_color, "secondary": hex_color, "accent": hex_color},
  "budget_total": number,
  "budget_allocation": {"seating": float, "tables": float, "textiles": float, "accessories": float},
  "required_items": [{"category": string, "max_width_inches": number_or_null, "style_query": string}]
}
Use ONLY these category values: sofa, coffee_table, rug, floor_lamp, accent_chair, throw_blanket, bookshelf, dining_table, bed_frame, side_table
Return ONLY the JSON array. No markdown, no explanation, no code blocks."""

    user_prompt = (
        f"Room analysis: {json.dumps(room_analysis)}\n"
        f"Budget: ${budget}\n"
        f"Preferred style: {style}\n"
        "Generate 3 distinct design concepts that fit this specific room."
    )

    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {groq_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt}
            ],
            "max_tokens": 2000,
            "temperature": 0.7
        },
        timeout=30
    )

    if resp.status_code != 200:
        raise Exception(f"Groq Planning API error: {resp.status_code} - {resp.text}")

    raw = resp.json()['choices'][0]['message']['content'].strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    concepts = json.loads(raw)
    for c in concepts:
        c["budget_total"] = budget

    concepts = _normalize_categories(concepts)
    return concepts


def planning_agent(state: AppState) -> AppState:
    print(f"[DEBUG] use_real_api: {_use_real_api()}, GROQ_KEY: {bool(os.getenv('GROQ_API_KEY'))}")
    """
    Planning agent — generates 3 design concepts.
    Real path: Groq designs freely, Pinecone finds closest products in retrieval.
    Mock path: returns MOCK_DESIGN_CONCEPTS instantly.
    """
    room_analysis = state["room_analysis"]
    budget        = state["budget"]
    style         = state["style"]

    state = log_stage_start(state, "planning")
    state = log_event(state, "planning", "generating_concepts",
        f"Generating 3 design concepts for {style} style, ${budget} budget",
        data={"style": style, "budget": budget,
              "room_type": room_analysis.get("room_type", "unknown")})

    # ── Mock mode ─────────────────────────────────────────────────────────────
    if not _use_real_api():
        concepts = copy.deepcopy(MOCK_DESIGN_CONCEPTS)
        for c in concepts:
            c["budget_total"] = budget
            state = log_event(state, "planning", "concept_created",
                f"Design concept '{c['concept_name']}' created with "
                f"{len(c['required_items'])} items (mock)",
                level="success",
                data={"concept_name": c["concept_name"],
                      "style_tags": c["style_tags"]})
        state = log_stage_end(state, "planning")
        return {**state, "design_concepts": concepts, "budget_remaining": budget, "error": None}

    # ── Real API ──────────────────────────────────────────────────────────────
    try:
        concepts = _call_groq_planning(room_analysis, budget, style)
        for c in concepts:
            state = log_event(state, "planning", "concept_created",
                f"Design concept '{c['concept_name']}' created with "
                f"{len(c['required_items'])} items",
                level="success",
                data={"concept_name": c["concept_name"],
                      "style_tags": c["style_tags"]})
        state = log_stage_end(state, "planning")
        return {**state, "design_concepts": concepts, "budget_remaining": budget, "error": None}

    except Exception as e:
        state = log_event(state, "planning", "api_failed",
            f"Groq Planning failed — falling back to mock: {str(e)}",
            level="error", data={"error": str(e)})
        concepts = copy.deepcopy(MOCK_DESIGN_CONCEPTS)
        for c in concepts:
            c["budget_total"] = budget
        state = log_stage_end(state, "planning")
        return {
            **state,
            "design_concepts": concepts,
            "budget_remaining": budget,
            "error": f"planning_agent_failed: {str(e)}"
        }