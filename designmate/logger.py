# logger.py
# Structured agent logging layer.
# Every agent calls log_event() to emit a structured JSON log event.
# Events are stored in AppState["agent_logs"] and streamed via SSE to frontend.
# Pitfall 2: logs are capped at MAX_LOGS_PER_SESSION to keep state lean.

from datetime import datetime, timezone
from typing import Optional

MAX_LOGS_PER_SESSION = 100


def log_event(
    state: dict,
    agent: str,
    event: str,
    message: str,
    level: str = "info",
    data: Optional[dict] = None
) -> dict:
    """
    Creates a structured log event and appends it to state["agent_logs"].
    Returns the updated state dict.

    Args:
        state:   current AppState dict
        agent:   which agent is logging e.g. "vision", "planning"
        event:   short event identifier e.g. "item_planned", "api_failed"
        message: human-readable description shown in Agent Thought Trace
        level:   "info" | "warning" | "error" | "success"
        data:    optional dict of structured data for the event
    """
    event_obj = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent":     agent,
        "event":     event,
        "level":     level,
        "message":   message,
        "data":      data or {}
    }

    # Print to server console as before
    level_prefix = {
        "info":    "[INFO]",
        "warning": "[WARN]",
        "error":   "[ERROR]",
        "success": "[OK]"
    }.get(level, "[INFO]")
    print(f"{level_prefix} [{agent.upper()}] {message}")

    # Append to agent_logs in state
    current_logs = state.get("agent_logs") or []
    current_logs = current_logs + [event_obj]

    # Pitfall 2: cap at MAX_LOGS_PER_SESSION — trim oldest if over limit
    if len(current_logs) > MAX_LOGS_PER_SESSION:
        current_logs = current_logs[-MAX_LOGS_PER_SESSION:]

    return {**state, "agent_logs": current_logs}


def log_stage_start(state: dict, agent: str) -> dict:
    """Logs stage start and records start time in stage_timings."""
    import time
    timings = state.get("stage_timings") or {}
    timings[f"{agent}_start"] = time.time()
    state = {**state, "stage_timings": timings}
    return log_event(state, agent, "stage_start", f"{agent.title()} agent started")


def log_stage_end(state: dict, agent: str) -> dict:
    """Logs stage end and records elapsed time in stage_timings."""
    import time
    timings = state.get("stage_timings") or {}
    start_key = f"{agent}_start"
    if start_key in timings:
        elapsed = round(time.time() - timings[start_key], 4)
        timings[f"{agent}_elapsed"] = elapsed
        state = {**state, "stage_timings": timings}
        return log_event(
            state, agent, "stage_end",
            f"{agent.title()} agent completed in {elapsed}s",
            level="success",
            data={"elapsed_seconds": elapsed}
        )
    return log_event(state, agent, "stage_end", f"{agent.title()} agent completed")
