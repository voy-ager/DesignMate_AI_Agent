# state.py
from typing import TypedDict, Optional

class AppState(TypedDict):
    # Input — set by the API endpoint before the graph runs
    image_path: str
    budget: float
    style: str

    # Vision agent output (Contract 1: Vision → Planning)
    room_analysis: Optional[dict]

    # Planning agent output (Contract 2: Planning → Optimization)
    design_concepts: Optional[list]

    # Optimization agent output (Contract 3: Optimization → Retrieval)
    furniture_plan: Optional[dict]

    # Retrieval agent output (Contract 4: Retrieval → Rendering)
    sourced_products: Optional[list]

    # Rendering agent output
    render_urls: Optional[list]

    # Dialogue
    dialogue_history: Optional[list]
    budget_remaining: Optional[float]

    # Pitfall 1: agent failure routing
    error: Optional[str]
    retry_count: Optional[int]

    # Audit trail
    mode: Optional[str]

    # Phase 4: structured logging
    agent_logs: Optional[list]       # list of log event dicts
    stage_timings: Optional[dict]    # agent_start / agent_elapsed per stage
    metrics: Optional[dict]          # computed after pipeline completes