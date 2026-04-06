# agents/retrieval.py
from state import AppState
from vector_store import search_products
from logger import log_event, log_stage_start, log_stage_end


def _compute_style_coherence(items: list, style_tags: list) -> float:
    """
    Simple critic check — averages similarity scores and applies a
    style tag bonus if products match the concept style tags.
    A real Critic Agent would make a second LLM call to evaluate.
    REAL API SWITCH: replace with a Groq call that scores the selections.
    """
    if not items:
        return 0.0
    scores     = [item.get("similarity_score", 0) for item in items]
    base_score = sum(scores) / len(scores)

    # Style tag bonus — reward concepts where style terms appear in descriptors
    style_hits = 0
    for item in items:
        descriptor = item.get("style_descriptor", "").lower()
        for tag in style_tags:
            if tag.lower() in descriptor:
                style_hits += 1
                break

    style_bonus = (style_hits / len(items)) * 0.2
    return round(min(base_score + style_bonus, 1.0), 4)


def retrieval_agent(state: AppState) -> AppState:
    furniture_plan = state["furniture_plan"]
    concepts       = furniture_plan["concepts"]
    state = log_stage_start(state, "retrieval")
    state = log_event(state, "retrieval", "search_start",
        f"Starting product search for {len(concepts)} concepts",
        data={"num_concepts": len(concepts)})
    try:
        sourced = []
        for concept_plan in concepts:
            concept_name  = concept_plan["concept_name"]
            concept_index = concept_plan["concept_index"]
            total_budget  = concept_plan["total_budget"]
            planned_items = concept_plan["planned_items"]
            style_tags    = concept_plan.get("style_tags", [])
            selected_items = []
            total_cost = 0.0

            for item in planned_items:
                category    = item["category"]
                style_query = item["style_query"]
                budget_ceil = item["budget_ceiling"]
                max_width   = item.get("max_width_inches")

                state = log_event(state, "retrieval", "searching",
                    f"Searching for {category} matching '{style_query}' "
                    f"under ${budget_ceil}",
                    data={"category": category, "budget_ceiling": budget_ceil})

                candidates = search_products(
                    query=style_query, category=category, limit=5
                )
                chosen = _pick_best(candidates, budget_ceil, max_width)

                if chosen:
                    chosen["within_budget"]  = chosen["price"] <= budget_ceil
                    chosen["budget_ceiling"] = budget_ceil
                    selected_items.append(chosen)
                    total_cost += chosen["price"]

                    level = "success" if chosen["within_budget"] else "warning"
                    msg   = (
                        f"{'Selected' if chosen['within_budget'] else 'Best match (over budget)'}: "
                        f"'{chosen['name']}' ${chosen['price']} "
                        f"(similarity: {chosen['similarity_score']})"
                    )
                    state = log_event(state, "retrieval", "product_selected",
                        msg, level=level,
                        data={
                            "concept":          concept_name,
                            "category":         category,
                            "product_name":     chosen["name"],
                            "price":            chosen["price"],
                            "within_budget":    chosen["within_budget"],
                            "similarity_score": chosen["similarity_score"]
                        })
                else:
                    state = log_event(state, "retrieval", "no_match",
                        f"No product found for {category} in '{concept_name}'",
                        level="warning",
                        data={"concept": concept_name, "category": category})

            # Critic check — compute style coherence per concept
            coherence = _compute_style_coherence(selected_items, style_tags)
            state = log_event(state, "retrieval", "coherence_check",
                f"Style coherence for '{concept_name}': "
                f"{round(coherence * 100)}% "
                f"({'above' if coherence >= 0.75 else 'below'} 0.75 target)",
                level="success" if coherence >= 0.75 else "warning",
                data={"concept": concept_name, "coherence": coherence})

            sourced.append({
                "concept_name":     concept_name,
                "concept_index":    concept_index,
                "style_tags":       style_tags,
                "color_palette":    concept_plan["color_palette"],
                "items":            selected_items,
                "total_cost":       round(total_cost, 2),
                "budget_remaining": round(total_budget - total_cost, 2),
                "style_coherence":  coherence
            })

        state = log_event(state, "retrieval", "search_complete",
            "Product search completed for all concepts",
            level="success",
            data={"num_concepts": len(sourced)})
        state = log_stage_end(state, "retrieval")
        return {**state, "sourced_products": sourced, "error": None}

    except Exception as e:
        state = log_event(state, "retrieval", "search_failed",
            f"Retrieval failed: {str(e)}",
            level="error", data={"error": str(e)})
        state = log_stage_end(state, "retrieval")
        return {
            **state,
            "sourced_products": [],
            "error": f"retrieval_failed: {str(e)}"
        }


def _pick_best(candidates: list, budget_ceil: float,
               max_width: float) -> dict:
    # Pass 1: strict — in stock + budget + dimensions
    for c in sorted(candidates,
                    key=lambda x: x["similarity_score"], reverse=True):
        if not c["in_stock"]: continue
        if c["price"] > budget_ceil: continue
        if max_width and c["dimensions"]["width"] > max_width: continue
        return c
    # Pass 2: relax budget constraint
    for c in sorted(candidates,
                    key=lambda x: x["similarity_score"], reverse=True):
        if not c["in_stock"]: continue
        if max_width and c["dimensions"]["width"] > max_width: continue
        return c
    # Pass 3: best similarity regardless
    if candidates:
        return sorted(candidates,
                      key=lambda x: x["similarity_score"],
                      reverse=True)[0]
    return None