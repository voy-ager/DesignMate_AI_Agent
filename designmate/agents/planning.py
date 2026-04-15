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


def _use_pinecone() -> bool:
    return bool(os.getenv("PINECONE_API_KEY", "").strip())


def _fetch_catalog_from_pinecone() -> list:
    """
    Fetches all products from Pinecone and returns a compact list
    for the LLM to design with.
    """
    from pinecone import Pinecone
    pc    = Pinecone(api_key=os.getenv("PINECONE_API_KEY", ""))
    index = pc.Index("designmate-products")

    # Fetch all products using a dummy vector query with high top_k
    # We use a zero vector since we want all products, not semantic search
    import numpy as np
    dummy_vector = [0.0] * 384

    results = index.query(
        vector=dummy_vector,
        top_k=200,
        include_metadata=True
    )

    products = []
    for match in results.matches:
        meta = match.metadata
        dims = meta.get("dimensions", "{}")
        if isinstance(dims, str):
            try:
                dims = json.loads(dims)
            except Exception:
                dims = {}

        materials = meta.get("materials", "[]")
        if isinstance(materials, str):
            try:
                materials = json.loads(materials)
            except Exception:
                materials = []

        colors = meta.get("colors", "[]")
        if isinstance(colors, str):
            try:
                colors = json.loads(colors)
            except Exception:
                colors = []

        style_tags = meta.get("style_tags", "[]")
        if isinstance(style_tags, str):
            try:
                style_tags = json.loads(style_tags)
            except Exception:
                style_tags = []

        products.append({
            "product_id":   match.id,
            "category":     meta.get("category", ""),
            "name":         meta.get("name", ""),
            "price":        float(meta.get("price", 0)),
            "dimensions":   dims,
            "materials":    materials,
            "colors":       colors,
            "style_tags":   style_tags,
            "description":  meta.get("description", ""),
            "purchase_url": meta.get("purchase_url", ""),
        })

    return products


def _build_catalog_context(products: list) -> str:
    """
    Builds a compact catalog string for the LLM prompt.
    Groups products by category for easy reading.
    """
    by_category: dict = {}
    for p in products:
        cat = p["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(p)

    lines = ["AVAILABLE PRODUCTS CATALOG:"]
    for cat, items in sorted(by_category.items()):
        lines.append(f"\n[{cat.upper().replace('_', ' ')}]")
        for p in items:
            mats   = ", ".join(p["materials"][:3]) if p["materials"] else ""
            cols   = ", ".join(p["colors"][:3])    if p["colors"]    else ""
            styles = ", ".join(p["style_tags"][:2]) if p["style_tags"] else ""
            desc   = p["description"][:80] if p["description"] else ""
            lines.append(
                f"  ID: {p['product_id']} | {p['name']} | ${p['price']}"
                f" | {mats} | {cols} | {styles}"
                + (f" | {desc}" if desc else "")
            )

    return "\n".join(lines)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=8),
    retry=retry_if_exception_type(Exception),
    reraise=True
)
def _call_groq_planning(
    room_analysis: dict,
    budget: float,
    style: str,
    catalog_context: str
) -> list:
    """
    Calls Groq Llama 3.1 8B with the real product catalog.
    LLM selects specific products by ID instead of inventing style queries.
    """
    groq_key = os.getenv("GROQ_API_KEY", "")

    system_prompt = f"""You are an expert interior designer. You have access to a real product catalog.
Your job is to create exactly 3 distinct design concepts by selecting REAL products from the catalog.

{catalog_context}

Generate exactly 3 distinct design concepts as a JSON array.
Each concept MUST select 3-5 products from the catalog above using their exact product IDs.
Each concept must follow this schema exactly:
{{
  "concept_name": string,
  "style_tags": [string],
  "color_palette": {{"primary": hex_color, "secondary": hex_color, "accent": hex_color}},
  "budget_total": number,
  "budget_allocation": {{"seating": float, "tables": float, "textiles": float, "accessories": float}},
  "selected_products": [
    {{
      "product_id": string,
      "category": string,
      "reason": string
    }}
  ]
}}

RULES:
- Only use product IDs that exist in the catalog above
- Select products that fit the room type, style and budget
- Each concept must use different products (no repeats across concepts)
- Total cost of selected products must not exceed the budget
- Select products from different categories for variety
- Return ONLY the JSON array. No markdown, no explanation, no code blocks."""

    user_prompt = (
        f"Room analysis: {json.dumps(room_analysis)}\n"
        f"Budget: ${budget}\n"
        f"Preferred style: {style}\n"
        "Generate 3 distinct design concepts using real products from the catalog."
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
            "max_tokens": 3000,
            "temperature": 0.7
        },
        timeout=30
    )

    if resp.status_code != 200:
        raise Exception(f"Groq Planning API error: {resp.status_code} - {resp.text}")

    raw = resp.json()['choices'][0]['message']['content'].strip()

    # Strip markdown code blocks if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    concepts = json.loads(raw)
    for c in concepts:
        c["budget_total"] = budget

    return concepts


def _convert_to_required_items(concepts: list, all_products: list) -> list:
    """
    Converts the new selected_products format into required_items format
    so the rest of the pipeline (optimization, retrieval) works unchanged.
    """
    product_map = {p["product_id"]: p for p in all_products}

    for concept in concepts:
        selected = concept.get("selected_products", [])
        required_items = []
        for sel in selected:
            pid  = sel.get("product_id", "")
            prod = product_map.get(pid)
            if prod:
                required_items.append({
                    "category":        prod["category"],
                    "max_width_inches": prod["dimensions"].get("width"),
                    "style_query":     prod["name"],
                    "product_id":      pid,   # carry through for direct lookup
                })
        concept["required_items"] = required_items

        # Clean up selected_products from concept to keep state lean
        concept.pop("selected_products", None)

    return concepts


def planning_agent(state: AppState) -> AppState:
    """
    Planning agent — generates 3 design concepts.
    Catalog-grounded path: fetches real products from Pinecone, passes to Groq.
    LLM selects specific products by ID — no more invented style queries.
    Mock path: returns MOCK_DESIGN_CONCEPTS instantly (no API keys needed).
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
        return {
            **state,
            "design_concepts": concepts,
            "budget_remaining": budget,
            "error": None
        }

    # ── Real API + Pinecone catalog ───────────────────────────────────────────
    try:
        # Fetch catalog from Pinecone if available
        all_products    = []
        catalog_context = ""
        if _use_pinecone():
            state = log_event(state, "planning", "fetching_catalog",
                "Fetching product catalog from Pinecone...",
                data={"source": "pinecone"})
            all_products    = _fetch_catalog_from_pinecone()
            catalog_context = _build_catalog_context(all_products)
            state = log_event(state, "planning", "catalog_fetched",
                f"Fetched {len(all_products)} products from Pinecone",
                level="success",
                data={"product_count": len(all_products)})

        concepts = _call_groq_planning(
            room_analysis, budget, style, catalog_context
        )

        # Convert selected_products → required_items for downstream agents
        if all_products:
            concepts = _convert_to_required_items(concepts, all_products)

        for c in concepts:
            state = log_event(state, "planning", "concept_created",
                f"Design concept '{c['concept_name']}' created with "
                f"{len(c.get('required_items', []))} items",
                level="success",
                data={"concept_name": c["concept_name"],
                      "style_tags":   c.get("style_tags", [])})

        state = log_stage_end(state, "planning")
        return {
            **state,
            "design_concepts": concepts,
            "budget_remaining": budget,
            "error": None
        }

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