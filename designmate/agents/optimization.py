# agents/optimization.py
from ortools.sat.python import cp_model
from state import AppState
from logger import log_event, log_stage_start, log_stage_end

# Minimum budget fraction per category — prevents $0 ceilings
MIN_FRACTION = 0.10


def _run_ortools(concept: dict, room_analysis: dict) -> dict:
    budget     = concept["budget_total"]
    allocation = concept["budget_allocation"]
    items      = concept["required_items"]
    model      = cp_model.CpModel()
    solver     = cp_model.CpSolver()

    room_width_inches = room_analysis.get("dimensions", {}).get("width_ft", 12) * 12
    walkway_clearance = room_analysis.get("constraints", {}).get("walkway_clearance_inches", 36)

    budget_cents   = int(budget * 100)
    item_ceilings  = {}
    spatial_checks = []

    for item in items:
        category           = item["category"]
        bucket             = _get_bucket(category)
        allocated_fraction = allocation.get(bucket, MIN_FRACTION)

        # Enforce minimum fraction so no item gets a $0 ceiling
        allocated_fraction = max(allocated_fraction, MIN_FRACTION)

        ceiling_cents = int(budget_cents * allocated_fraction)
        var = model.new_int_var(0, ceiling_cents, f"spend_{category}")
        item_ceilings[category] = {"var": var, "ceiling_cents": ceiling_cents}

        # Spatial validation
        max_width = item.get("max_width_inches")
        if max_width:
            available = room_width_inches - walkway_clearance
            passed    = max_width <= available
            spatial_checks.append({
                "category":          category,
                "item_width_inches": max_width,
                "wall_width_inches": room_width_inches,
                "clearance_inches":  room_width_inches - max_width,
                "walkway_required":  walkway_clearance,
                "passed":            passed
            })

    model.add(sum(v["var"] for v in item_ceilings.values()) <= budget_cents)
    model.maximize(sum(v["var"] for v in item_ceilings.values()))
    status = solver.solve(model)

    planned_items = []
    for item in items:
        category     = item["category"]
        ceiling_data = item_ceilings[category]
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            ceiling = solver.value(ceiling_data["var"]) / 100
        else:
            bucket  = _get_bucket(category)
            ceiling = budget * max(allocation.get(bucket, MIN_FRACTION), MIN_FRACTION)

        # Final safety — never allow $0 ceiling
        if ceiling == 0:
            ceiling = round(budget * MIN_FRACTION, 2)

        planned_items.append({
            "category":         category,
            "max_width_inches": item.get("max_width_inches"),
            "style_query":      item["style_query"],
            "budget_ceiling":   round(ceiling, 2)
        })

    return {
        "concept_name":   concept["concept_name"],
        "concept_index":  concept.get("concept_index", 0),
        "style_tags":     concept["style_tags"],
        "color_palette":  concept["color_palette"],
        "planned_items":  planned_items,
        "total_budget":   budget,
        "spatial_checks": spatial_checks
    }


def _get_bucket(category: str) -> str:
    mapping = {
        "sofa":          "seating",
        "sectional":     "seating",
        "accent_chair":  "seating",
        "coffee_table":  "tables",
        "side_table":    "tables",
        "dining_table":  "tables",
        "rug":           "textiles",
        "throw_blanket": "textiles",
        "curtains":      "textiles",
        "floor_lamp":    "accessories",
        "wall_art":      "accessories",
        "plant":         "accessories",
        "bookshelf":     "accessories",
        "bed_frame":     "seating",
    }
    return mapping.get(category, "accessories")


def optimization_agent(state: AppState) -> AppState:
    concepts      = state["design_concepts"]
    room_analysis = state.get("room_analysis", {})
    room_width_ft = room_analysis.get("dimensions", {}).get("width_ft", 12)

    state = log_stage_start(state, "optimization")
    state = log_event(state, "optimization", "solver_start",
        f"OR-Tools CP-SAT solver starting for {len(concepts)} concepts",
        data={"num_concepts": len(concepts), "room_width_ft": room_width_ft})

    try:
        plans = []
        for i, concept in enumerate(concepts):
            concept["concept_index"] = i
            plan = _run_ortools(concept, room_analysis)
            plans.append(plan)

            for item in plan["planned_items"]:
                state = log_event(state, "optimization", "item_planned",
                    f"Optimization: '{concept['concept_name']}' / "
                    f"{item['category']} ceiling set to ${item['budget_ceiling']}",
                    data={
                        "concept":        concept["concept_name"],
                        "category":       item["category"],
                        "budget_ceiling": item["budget_ceiling"]
                    })

            for check in plan.get("spatial_checks", []):
                status  = "PASSED" if check["passed"] else "FAILED"
                level   = "success" if check["passed"] else "warning"
                wall_ft = round(check["wall_width_inches"] / 12, 1)
                clear   = check["clearance_inches"]
                state = log_event(
                    state, "optimization", "spatial_check",
                    f"Spatial check: {check['category']} "
                    f"({check['item_width_inches']}\") on "
                    f"{wall_ft}ft wall. Clearance: {clear}\". {status}",
                    level=level,
                    data=check
                )

        state = log_event(state, "optimization", "solver_complete",
            "OR-Tools solver completed all concepts",
            level="success", data={"num_plans": len(plans)})
        state = log_stage_end(state, "optimization")
        return {**state, "furniture_plan": {"concepts": plans}, "error": None}

    except Exception as e:
        state = log_event(state, "optimization", "solver_failed",
            f"OR-Tools failed — using fallback allocation: {str(e)}",
            level="error", data={"error": str(e)})
        plans = []
        for i, concept in enumerate(concepts):
            budget     = concept["budget_total"]
            allocation = concept["budget_allocation"]
            planned_items = []
            for item in concept["required_items"]:
                bucket  = _get_bucket(item["category"])
                ceiling = round(budget * max(allocation.get(bucket, MIN_FRACTION), MIN_FRACTION), 2)
                planned_items.append({
                    "category":         item["category"],
                    "max_width_inches": item.get("max_width_inches"),
                    "style_query":      item["style_query"],
                    "budget_ceiling":   ceiling
                })
            plans.append({
                "concept_name":   concept["concept_name"],
                "concept_index":  i,
                "style_tags":     concept["style_tags"],
                "color_palette":  concept["color_palette"],
                "planned_items":  planned_items,
                "total_budget":   budget,
                "spatial_checks": []
            })
        state = log_stage_end(state, "optimization")
        return {
            **state,
            "furniture_plan": {"concepts": plans},
            "error": f"optimization_fallback: {str(e)}"
        }