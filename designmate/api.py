# api.py
import os
import shutil
import uuid
import asyncio
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from dotenv import load_dotenv

load_dotenv()

from state import AppState
from graph import app_graph
from agents.dialogue import dialogue_agent
from metrics import compute_metrics

app = FastAPI(title="DesignMate AI", version="0.4-phase4")
from fastapi.staticfiles import StaticFiles
os.makedirs("uploads/renders", exist_ok=True)
app.mount("/renders", StaticFiles(directory="."), name="renders")

# CORS — required for Next.js frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # REAL API SWITCH: restrict to your domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# In-memory session store
# REAL API SWITCH: replace with PostgreSQL/Supabase for production
_sessions: dict = {}


@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    budget: float = Form(...),
    style: str = Form(default="modern")
):
    file_id    = str(uuid.uuid4())
    ext        = os.path.splitext(file.filename)[-1] or ".jpg"
    image_path = os.path.join(UPLOAD_DIR, f"{file_id}{ext}")

    with open(image_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    initial_state: AppState = {
        "image_path":       image_path,
        "budget":           budget,
        "style":            style,
        "room_analysis":    None,
        "design_concepts":  None,
        "furniture_plan":   None,
        "sourced_products": None,
        "render_urls":      None,
        "dialogue_history": [],
        "budget_remaining": budget,
        "error":            None,
        "retry_count":      0,
        "mode":             None,
        "agent_logs":       [],
        "stage_timings":    {},
        "metrics":          None
    }

    try:
        final_state = app_graph.invoke(initial_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Compute and attach metrics
    metrics = compute_metrics(final_state)
    final_state["metrics"] = metrics
    _sessions[file_id] = final_state

    return JSONResponse(content={
        "session_id":       file_id,
        "status":           "ok" if not final_state.get("error") else "partial",
        "mode":             final_state.get("mode"),
        "room_analysis":    final_state.get("room_analysis"),
        "design_concepts":  final_state.get("design_concepts"),
        "furniture_plan":   final_state.get("furniture_plan"),
        "sourced_products": final_state.get("sourced_products"),
        "render_urls":      final_state.get("render_urls"),
        "agent_logs":       final_state.get("agent_logs"),
        "metrics":          metrics,
        "error":            final_state.get("error")
    })


@app.post("/refine")
async def refine(
    session_id: str = Form(...),
    message: str = Form(...)
):
    if session_id not in _sessions:
        raise HTTPException(status_code=404,
                            detail="Session not found. Call /analyze first.")

    current_state = _sessions[session_id]
    updated_state = dialogue_agent(current_state, message)

    try:
        from langgraph.graph import StateGraph
        from agents.planning import planning_agent
        from agents.optimization import optimization_agent
        from agents.retrieval import retrieval_agent
        from agents.rendering import rendering_agent

        def route_after_planning(state):
            return "optimization" if state.get("design_concepts") else "__end__"
        def route_after_optimization(state):
            return "retrieval" if state.get("furniture_plan") else "__end__"
        def route_after_retrieval(state):
            return "rendering" if state.get("sourced_products") else "__end__"
        def route_after_rendering(state):
            return "__end__"

        refine_graph = StateGraph(AppState)
        refine_graph.add_node("planning",     planning_agent)
        refine_graph.add_node("optimization", optimization_agent)
        refine_graph.add_node("retrieval",    retrieval_agent)
        refine_graph.add_node("rendering",    rendering_agent)
        refine_graph.set_entry_point("planning")
        refine_graph.add_conditional_edges("planning",     route_after_planning,
            {"optimization": "optimization", "__end__": "__end__"})
        refine_graph.add_conditional_edges("optimization", route_after_optimization,
            {"retrieval": "retrieval", "__end__": "__end__"})
        refine_graph.add_conditional_edges("retrieval",    route_after_retrieval,
            {"rendering": "rendering", "__end__": "__end__"})
        refine_graph.add_conditional_edges("rendering",    route_after_rendering,
            {"__end__": "__end__"})

        compiled    = refine_graph.compile()
        final_state = compiled.invoke(updated_state)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    metrics = compute_metrics(final_state)
    final_state["metrics"] = metrics
    _sessions[session_id]  = final_state

    return JSONResponse(content={
        "session_id":       session_id,
        "status":           "ok" if not final_state.get("error") else "partial",
        "mode":             final_state.get("mode"),
        "dialogue_history": final_state.get("dialogue_history"),
        "sourced_products": final_state.get("sourced_products"),
        "render_urls":      final_state.get("render_urls"),
        "agent_logs":       final_state.get("agent_logs"),
        "metrics":          metrics,
        "budget":           final_state.get("budget"),
        "style":            final_state.get("style"),
        "error":            final_state.get("error")
    })


@app.get("/stream/{session_id}")
async def stream_logs(session_id: str):
    """
    SSE endpoint — streams agent_logs from a completed session to frontend.
    Pitfall 3: sends keepalive ping every 5 seconds.
    Frontend connects with: new EventSource('/stream/{session_id}')
    """
    async def event_generator():
        if session_id not in _sessions:
            yield {"data": '{"error": "session not found"}'}
            return

        state = _sessions[session_id]
        logs  = state.get("agent_logs") or []

        # Stream all existing logs
        for log in logs:
            import json
            yield {"data": json.dumps(log)}
            await asyncio.sleep(0.05)   # small delay for smooth frontend animation

        # Keepalive — pitfall 3
        while True:
            yield {"data": '{"event": "keepalive"}'}
            await asyncio.sleep(5)

    return EventSourceResponse(event_generator())


@app.get("/metrics/{session_id}")
async def get_metrics(session_id: str):
    """Returns computed metrics for a session."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found.")
    state   = _sessions[session_id]
    metrics = state.get("metrics") or compute_metrics(state)
    return JSONResponse(content={"session_id": session_id, "metrics": metrics})


@app.post("/evaluate")
async def evaluate():
    """
    Runs the full evaluation test suite.
    Returns results table for the paper.
    Warning: takes ~30 seconds to run all 5 test cases.
    """
    from evaluator import run_evaluation
    try:
        results = run_evaluation()
        return JSONResponse(content=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    openai_set    = bool(os.getenv("OPENAI_API_KEY", "").strip())
    replicate_set = bool(os.getenv("REPLICATE_API_TOKEN", "").strip())
    return {
        "status":           "running",
        "openai_mode":      "real" if openai_set    else "mock",
        "replicate_mode":   "real" if replicate_set else "mock",
        "active_sessions":  len(_sessions),
        "phase":            4
    }