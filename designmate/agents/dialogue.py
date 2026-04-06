# agents/dialogue.py
# Dialogue agent — handles conversational refinement via POST /refine.
# Maintains dialogue_history in AppState across turns.
# Re-invokes the pipeline from Planning onwards with updated constraints.

import os
import json
from state import AppState
from mock_data import MOCK_DESIGN_CONCEPTS
import copy

def _use_real_api() -> bool:
    return bool(os.getenv("OPENAI_API_KEY", "").strip())


def _parse_refinement_mock(message: str, state: AppState) -> dict:
    """
    Mock refinement parser — applies simple keyword rules to modify state.
    REAL API SWITCH: replace this function body with a GPT-4o-mini call
    that interprets the message and returns the same dict structure.
    """
    message_lower = message.lower()
    updates = {}

    # Budget adjustments
    if "reduce budget" in message_lower or "cheaper" in message_lower or "less expensive" in message_lower:
        updates["budget"] = state["budget"] * 0.8
        updates["note"] = "Budget reduced by 20%"

    elif "increase budget" in message_lower or "more expensive" in message_lower or "luxury" in message_lower:
        updates["budget"] = state["budget"] * 1.2
        updates["note"] = "Budget increased by 20%"

    # Style adjustments
    if "rustic" in message_lower:
        updates["style"] = "rustic"
        updates["note"] = updates.get("note", "") + " Style changed to rustic"

    elif "minimalist" in message_lower or "minimal" in message_lower:
        updates["style"] = "minimalist"
        updates["note"] = updates.get("note", "") + " Style changed to minimalist"

    elif "scandinavian" in message_lower or "scandi" in message_lower:
        updates["style"] = "scandinavian"
        updates["note"] = updates.get("note", "") + " Style changed to scandinavian"

    elif "contemporary" in message_lower or "modern" in message_lower:
        updates["style"] = "modern"
        updates["note"] = updates.get("note", "") + " Style changed to modern"

    if not updates:
        updates["note"] = "No specific changes detected — regenerating with same constraints"

    return updates


def _parse_refinement_real(message: str, state: AppState) -> dict:
    """
    REAL API SWITCH: this function replaces _parse_refinement_mock when
    OPENAI_API_KEY is set. Uses GPT-4o-mini to interpret the user message
    and return structured updates to apply to AppState.
    """
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=300,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a design assistant. The user wants to refine their room design. "
                    "Extract any changes they want and return ONLY a JSON object with these "
                    "optional fields:\n"
                    '{"budget": number, "style": string, "note": string}\n'
                    "Only include fields that actually changed. "
                    "Return ONLY the JSON, no markdown."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Current budget: ${state['budget']}\n"
                    f"Current style: {state['style']}\n"
                    f"User message: {message}"
                )
            }
        ]
    )
    raw = response.choices[0].message.content.strip()
    return json.loads(raw)


def dialogue_agent(state: AppState, user_message: str) -> AppState:
    """
    Dialogue agent — processes a refinement message and updates AppState.
    Returns updated state ready to re-run through Planning → Rendering.
    """
    print(f"[Dialogue] Processing message: '{user_message}'")

    # Append user message to history
    history = state.get("dialogue_history", []) or []
    history.append({
        "role": "user",
        "content": user_message
    })

    # Parse refinement
    try:
        if _use_real_api():
            updates = _parse_refinement_real(user_message, state)
        else:
            updates = _parse_refinement_mock(user_message, state)
    except Exception as e:
        print(f"[Dialogue] Parse failed: {e}. Proceeding with no changes.")
        updates = {"note": f"Parse error: {str(e)}"}

    note = updates.pop("note", "Refinement applied")
    print(f"[Dialogue] {note}")

    # Append assistant acknowledgement to history
    history.append({
        "role": "assistant",
        "content": note
    })

    # Apply updates to state — reset downstream fields so pipeline re-runs
    updated_state = {
        **state,
        "dialogue_history":  history,
        "design_concepts":   None,   # forces re-planning
        "furniture_plan":    None,   # forces re-optimization
        "sourced_products":  None,   # forces re-retrieval
        "render_urls":       None,   # forces re-rendering
        "error":             None,
        "retry_count":       0
    }

    # Apply any budget/style changes
    if "budget" in updates:
        updated_state["budget"] = updates["budget"]
        updated_state["budget_remaining"] = updates["budget"]
    if "style" in updates:
        updated_state["style"] = updates["style"]

    return updated_state