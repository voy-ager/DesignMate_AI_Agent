# agents/vision.py
import os
import json
import base64
import requests
from pathlib import Path
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

from state import AppState
from mock_data import MOCK_ROOM_ANALYSIS
from logger import log_event, log_stage_start, log_stage_end

def _use_real_api() -> bool:
    return bool(os.getenv("GROQ_API_KEY", "").strip())


def _parse_room_analysis(text: str) -> dict:
    """
    Parses Llama 4 Scout's natural language response into structured room_analysis dict.
    This is the JSON parser the expert described — converts unstructured VLM output
    into the exact schema our Planning and Optimization agents expect.
    REAL API SWITCH: tune the prompt in _call_llama4_vision to get cleaner JSON output.
    """
    import re

    # Try direct JSON parse first
    try:
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception:
        pass

    # Fallback: extract key values with regex
    result = {
        "room_type": "living_room",
        "dimensions": {
            "width_ft": 12,
            "length_ft": 14,
            "area_sqft": 168,
            "ceiling_height_ft": 9
        },
        "windows": [{"wall": "west", "width_ft": 4, "height_ft": 5, "natural_light": "afternoon"}],
        "doors": [{"wall": "north", "width_ft": 3}],
        "lighting": {"natural_direction": "west", "quality": "warm_afternoon"},
        "floor_type": "hardwood",
        "wall_color": "#F5F0E8",
        "existing_features": [],
        "constraints": {
            "max_sofa_width_inches": 84,
            "walkway_clearance_inches": 36
        }
    }

    # Extract room type
    text_lower = text.lower()
    for room in ["living room", "bedroom", "kitchen", "bathroom", "office",
                 "dining room", "auditorium", "conference"]:
        if room in text_lower:
            result["room_type"] = room.replace(" ", "_")
            break

    # Extract dimensions using regex
    dim_patterns = [
        r'(\d+)\s*(?:x|by|×)\s*(\d+)\s*(?:feet|ft|foot)',
        r'(\d+)\s*(?:feet|ft)\s*(?:wide|width).*?(\d+)\s*(?:feet|ft)\s*(?:long|length|deep)',
        r'width[:\s]+(\d+).*?length[:\s]+(\d+)',
    ]
    for pattern in dim_patterns:
        match = re.search(pattern, text_lower)
        if match:
            w, l = int(match.group(1)), int(match.group(2))
            result["dimensions"]["width_ft"] = w
            result["dimensions"]["length_ft"] = l
            result["dimensions"]["area_sqft"] = w * l
            result["constraints"]["max_sofa_width_inches"] = min(84, (w - 2) * 12)
            break

    # Extract floor type
    for floor in ["hardwood", "carpet", "tile", "laminate", "vinyl", "concrete"]:
        if floor in text_lower:
            result["floor_type"] = floor
            break

    return result


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=8),
    retry=retry_if_exception_type(Exception),
    reraise=True
)
def _call_llama4_vision(image_path: str) -> dict:
    """
    REAL API SWITCH: Uses Groq Llama 4 Scout for vision analysis.
    To switch back to GPT-4 Vision: change model to "gpt-4o" and
    update the client to use OpenAI SDK instead of requests.
    """
    groq_key = os.getenv("GROQ_API_KEY", "")

    with open(image_path, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode("utf-8")

    # Detect image format from extension
    ext = os.path.splitext(image_path)[-1].lower()
    mime = "image/jpeg" if ext in [".jpg", ".jpeg"] else "image/png"

    prompt = """Analyze this room image and return a JSON object with EXACTLY this structure:
{
  "room_type": "living_room",
  "dimensions": {"width_ft": 12, "length_ft": 14, "area_sqft": 168, "ceiling_height_ft": 9},
  "windows": [{"wall": "west", "width_ft": 4, "height_ft": 5, "natural_light": "afternoon"}],
  "doors": [{"wall": "north", "width_ft": 3}],
  "lighting": {"natural_direction": "west", "quality": "warm_afternoon"},
  "floor_type": "hardwood",
  "wall_color": "#F5F0E8",
  "existing_features": [],
  "constraints": {"max_sofa_width_inches": 84, "walkway_clearance_inches": 36}
}
Replace the values with what you actually see. Return ONLY the JSON, no other text."""

    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {groq_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "meta-llama/llama-4-scout-17b-16e-instruct",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime};base64,{image_b64}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 500
        },
        timeout=30
    )

    if resp.status_code != 200:
        raise Exception(f"Groq Vision API error: {resp.status_code} - {resp.text}")

    raw = resp.json()['choices'][0]['message']['content'].strip()
    return _parse_room_analysis(raw)


def vision_agent(state: AppState) -> AppState:
    """
    Vision agent — analyzes room image.
    Mock path: returns MOCK_ROOM_ANALYSIS instantly.
    Real path: calls Groq Llama 4 Scout with retry + JSON parsing fallback.
    REAL API SWITCH: set GROQ_API_KEY in .env to activate real vision.
    """
    retry_count = state.get("retry_count", 0)
    state = log_stage_start(state, "vision")

    if not _use_real_api():
        state = log_event(state, "vision", "mock_mode",
            "Vision agent running in mock mode — returning mock room analysis",
            data={"room_type": MOCK_ROOM_ANALYSIS["room_type"]})
        state = log_stage_end(state, "vision")
        return {
            **state,
            "room_analysis": MOCK_ROOM_ANALYSIS,
            "error": None,
            "mode": "mock",
            "retry_count": 0
        }

    state = log_event(state, "vision", "api_call",
        "Calling Groq Llama 4 Scout to analyze room image",
        data={"image_path": state["image_path"],
              "model": "llama-4-scout-17b-16e-instruct"})
    try:
        result = _call_llama4_vision(state["image_path"])
        state = log_event(state, "vision", "analysis_complete",
            f"Room identified as {result.get('room_type', 'unknown')} "
            f"{result.get('dimensions', {}).get('area_sqft', '?')} sqft",
            level="success",
            data=result)
        state = log_stage_end(state, "vision")
        return {
            **state,
            "room_analysis": result,
            "error": None,
            "mode": "real",
            "retry_count": 0
        }
    except Exception as e:
        state = log_event(state, "vision", "api_failed",
            f"Groq Vision failed — falling back to mock: {str(e)}",
            level="error", data={"error": str(e)})
        state = log_stage_end(state, "vision")
        return {
            **state,
            "room_analysis": MOCK_ROOM_ANALYSIS,
            "error": f"vision_agent_failed: {str(e)}",
            "mode": "mock_fallback",
            "retry_count": retry_count + 1
        }