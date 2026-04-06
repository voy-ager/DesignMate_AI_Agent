# graph.py
from langgraph.graph import StateGraph

from state import AppState
from agents.vision import vision_agent
from agents.planning import planning_agent
from agents.optimization import optimization_agent
from agents.retrieval import retrieval_agent
from agents.rendering import rendering_agent


def route_after_vision(state: AppState) -> str:
    if state.get("error") and state.get("retry_count", 0) >= 3:
        print(f"[Router] Vision failed 3 times. Halting.")
        return "__end__"
    return "planning"


def route_after_planning(state: AppState) -> str:
    if not state.get("design_concepts"):
        print("[Router] Planning produced no concepts. Halting.")
        return "__end__"
    return "optimization"


def route_after_optimization(state: AppState) -> str:
    if not state.get("furniture_plan"):
        print("[Router] Optimization produced no plan. Halting.")
        return "__end__"
    return "retrieval"


def route_after_retrieval(state: AppState) -> str:
    if not state.get("sourced_products"):
        print("[Router] Retrieval produced no products. Halting.")
        return "__end__"
    return "rendering"              # Phase 3: was "__end__"


def route_after_rendering(state: AppState) -> str:
    return "__end__"


def build_graph():
    graph = StateGraph(AppState)

    graph.add_node("vision",       vision_agent)
    graph.add_node("planning",     planning_agent)
    graph.add_node("optimization", optimization_agent)
    graph.add_node("retrieval",    retrieval_agent)
    graph.add_node("rendering",    rendering_agent)

    graph.set_entry_point("vision")

    graph.add_conditional_edges(
        "vision",
        route_after_vision,
        {"planning": "planning", "__end__": "__end__"}
    )
    graph.add_conditional_edges(
        "planning",
        route_after_planning,
        {"optimization": "optimization", "__end__": "__end__"}
    )
    graph.add_conditional_edges(
        "optimization",
        route_after_optimization,
        {"retrieval": "retrieval", "__end__": "__end__"}
    )
    graph.add_conditional_edges(
        "retrieval",
        route_after_retrieval,
        {"rendering": "rendering", "__end__": "__end__"}
    )
    graph.add_conditional_edges(
        "rendering",
        route_after_rendering,
        {"__end__": "__end__"}
    )

    return graph.compile()


app_graph = build_graph()