# metrics.py
# Comprehensive agentic AI workflow metrics from a completed AppState.

AGENTS = ["vision", "planning", "optimization", "retrieval", "rendering"]

LATENCY_THRESHOLDS = {
    "vision":       {"fast": 3.0,  "slow": 8.0},
    "planning":     {"fast": 2.0,  "slow": 6.0},
    "optimization": {"fast": 0.5,  "slow": 2.0},
    "retrieval":    {"fast": 2.0,  "slow": 6.0},
    "rendering":    {"fast": 10.0, "slow": 25.0},
}


def _speed_grade(agent: str, elapsed: float) -> str:
    t = LATENCY_THRESHOLDS.get(agent, {"fast": 2.0, "slow": 6.0})
    if elapsed <= t["fast"]:  return "fast"
    if elapsed <= t["slow"]:  return "normal"
    return "slow"


def compute_metrics(state: dict) -> dict:
    metrics    = {}
    agent_logs = state.get("agent_logs") or []
    timings    = state.get("stage_timings") or {}
    sourced    = state.get("sourced_products") or []
    concepts   = state.get("design_concepts") or []
    room       = state.get("room_analysis") or {}
    budget     = state.get("budget", 1)

    def logs_for(agent):
        return [l for l in agent_logs if l.get("agent") == agent]

    def count_event(agent, event):
        return sum(1 for l in agent_logs
                   if l.get("agent") == agent and l.get("event") == event)

    # ── 1. LATENCY + SPEED GRADE ─────────────────────────────────────────────
    stage_latencies, speed_grades = {}, {}
    total_latency = 0.0
    slowest_agent, slowest_time = None, 0.0

    for agent in AGENTS:
        key = f"{agent}_elapsed"
        if key in timings:
            t = round(timings[key], 4)
            stage_latencies[agent] = t
            speed_grades[agent]    = _speed_grade(agent, t)
            total_latency += t
            if t > slowest_time:
                slowest_time, slowest_agent = t, agent

    metrics["latency"] = {
        "per_agent_seconds": stage_latencies,
        "speed_grades":      speed_grades,
        "total_seconds":     round(total_latency, 4),
        "slowest_agent":     slowest_agent,
        "slowest_seconds":   round(slowest_time, 4),
        "agents_completed":  len(stage_latencies),
        "agents_total":      len(AGENTS),
    }

    # ── 2. BUDGET + SPEND BREAKDOWN ───────────────────────────────────────────
    total_items, within_budget, over_budget = 0, 0, 0
    concept_budget_results, all_costs = [], []

    for concept in sourced:
        c_total, c_within, c_over = 0, 0, 0
        for item in concept.get("items", []):
            total_items += 1
            if item.get("within_budget"):
                within_budget += 1; c_within += 1
            else:
                over_budget += 1; c_over += 1
            c_total += item.get("price", 0)
        all_costs.append(c_total)
        concept_budget_results.append({
            "concept_name":        concept.get("concept_name"),
            "total_cost":          round(c_total, 2),
            "budget":              budget,
            "utilization_pct":     round(c_total / budget * 100, 1) if budget else 0,
            "budget_remaining":    round(budget - c_total, 2),
            "within_budget":       c_over == 0,
            "items_within_budget": c_within,
            "items_over_budget":   c_over,
        })

    budget_accuracy = round(within_budget / total_items, 4) if total_items else 0.0

    metrics["budget"] = {
        "accuracy":               budget_accuracy,
        "accuracy_pct":           round(budget_accuracy * 100, 1),
        "total_items_evaluated":  total_items,
        "items_within_budget":    within_budget,
        "items_over_budget":      over_budget,
        "avg_concept_cost":       round(sum(all_costs) / len(all_costs), 2) if all_costs else 0.0,
        "min_concept_cost":       round(min(all_costs), 2) if all_costs else 0.0,
        "max_concept_cost":       round(max(all_costs), 2) if all_costs else 0.0,
        "budget_target":          budget,
        "concepts_within_budget": sum(1 for c in concept_budget_results if c["within_budget"]),
        "concepts_over_budget":   sum(1 for c in concept_budget_results if not c["within_budget"]),
        "per_concept":            concept_budget_results,
    }

    # ── 3. STYLE COHERENCE ────────────────────────────────────────────────────
    all_scores, concept_scores = [], []
    for concept in sourced:
        scores = [
            item.get("similarity_score")
            for item in concept.get("items", [])
            if item.get("similarity_score") is not None
        ]
        if scores:
            avg = round(sum(scores) / len(scores), 4)
            all_scores.extend(scores)
            concept_scores.append({
                "concept_name":  concept.get("concept_name"),
                "coherence":     avg,
                "coherence_pct": round(avg * 100, 1),
                "target_met":    avg >= 0.75,
                "num_items":     len(scores),
            })

    coherence_avg = round(sum(all_scores) / len(all_scores), 4) if all_scores else 0.0

    metrics["style_coherence"] = {
        "avg":                   coherence_avg,
        "avg_pct":               round(coherence_avg * 100, 1),
        "min":                   round(min(all_scores), 4) if all_scores else 0.0,
        "max":                   round(max(all_scores), 4) if all_scores else 0.0,
        "target":                0.75,
        "target_met":            coherence_avg >= 0.75,
        "concepts_above_target": sum(1 for c in concept_scores if c["target_met"]),
        "per_concept":           concept_scores,
    }

    # ── 4. CONSTRAINT SATISFACTION ────────────────────────────────────────────
    opt_logs       = logs_for("optimization")
    spatial_passes = sum(1 for l in opt_logs if "PASSED" in l.get("message", ""))
    spatial_fails  = sum(1 for l in opt_logs if "FAILED" in l.get("message", ""))
    total_spatial  = spatial_passes + spatial_fails
    spatial_rate   = round(spatial_passes / total_spatial, 4) if total_spatial else 1.0

    budget_triggers = sum(1 for l in opt_logs if "ceiling set to" in l.get("message", ""))
    zero_ceilings   = sum(1 for l in opt_logs
                          if "ceiling set to $0" in l.get("message", ""))

    constraint_rate = round((spatial_rate + budget_accuracy) / 2, 4)

    metrics["constraint_satisfaction"] = {
        "overall_rate":          constraint_rate,
        "overall_pct":           round(constraint_rate * 100, 1),
        "spatial_pass_rate":     spatial_rate,
        "spatial_pass_pct":      round(spatial_rate * 100, 1),
        "spatial_checks_passed": spatial_passes,
        "spatial_checks_failed": spatial_fails,
        "spatial_checks_total":  total_spatial,
        "budget_ceiling_triggers": budget_triggers,
        "zero_budget_categories":  zero_ceilings,
        "budget_accuracy":         budget_accuracy,
        "budget_accuracy_pct":     round(budget_accuracy * 100, 1),
    }

    # ── 5. PLANNING QUALITY ───────────────────────────────────────────────────
    all_tags, items_per_concept = [], []
    for c in concepts:
        all_tags.extend(c.get("style_tags", []))
        items_per_concept.append(len(c.get("required_items", [])))

    unique_tags    = list(set(all_tags))
    tag_diversity  = round(len(unique_tags) / max(len(all_tags), 1), 4)
    avg_items      = round(sum(items_per_concept) / len(items_per_concept), 2) \
                     if items_per_concept else 0.0

    metrics["planning"] = {
        "concepts_generated":      len(concepts),
        "avg_items_per_concept":   avg_items,
        "total_style_tags":        len(all_tags),
        "unique_style_tags":       unique_tags,
        "unique_style_tag_count":  len(unique_tags),
        "style_tag_diversity":     tag_diversity,
        "style_tag_diversity_pct": round(tag_diversity * 100, 1),
        "planning_mode":           "real" if count_event("planning", "generating_concepts") else "mock",
        "api_fallback_triggered":  bool(count_event("planning", "api_failed")),
        "planning_latency_seconds": round(timings.get("planning_elapsed", 0), 4),
        "per_concept": [
            {
                "concept_name":  c.get("concept_name"),
                "style_tags":    c.get("style_tags", []),
                "items_planned": len(c.get("required_items", [])),
                "budget_total":  c.get("budget_total", 0),
            }
            for c in concepts
        ],
    }

    # ── 6. RETRIEVAL PRECISION ────────────────────────────────────────────────
    ret_logs         = logs_for("retrieval")
    products_selected = count_event("retrieval", "product_selected")
    products_rejected = count_event("retrieval", "no_match")
    over_budget_picks = sum(1 for l in ret_logs
                            if "over budget" in l.get("message", "").lower())
    total_searches    = count_event("retrieval", "searching")
    fill_rate         = round(products_selected / max(total_searches, 1), 4)

    # Per category precision
    category_hits:   dict = {}
    category_misses: dict = {}
    for l in ret_logs:
        data = l.get("data", {})
        cat  = data.get("category", "")
        if not cat:
            continue
        if l.get("event") == "product_selected":
            category_hits[cat]   = category_hits.get(cat, 0) + 1
        elif l.get("event") == "no_match":
            category_misses[cat] = category_misses.get(cat, 0) + 1

    all_cats = set(list(category_hits.keys()) + list(category_misses.keys()))
    category_precision = {
        cat: round(
            category_hits.get(cat, 0) /
            max(category_hits.get(cat, 0) + category_misses.get(cat, 0), 1),
            4
        )
        for cat in all_cats
    }

    metrics["retrieval_precision"] = {
        "fill_rate":          fill_rate,
        "fill_rate_pct":      round(fill_rate * 100, 1),
        "total_searches":     total_searches,
        "products_selected":  products_selected,
        "products_rejected":  products_rejected,
        "over_budget_picks":  over_budget_picks,
        "no_match_count":     products_rejected,
        "category_precision": category_precision,
        "retrieval_latency_seconds": round(timings.get("retrieval_elapsed", 0), 4),
    }

    # ── 7. TOOL USAGE PER AGENT ───────────────────────────────────────────────
    render_urls      = state.get("render_urls") or []
    real_renders     = sum(1 for r in render_urls if r.get("mode") == "real")
    fallback_renders = sum(1 for r in render_urls if r.get("mode") == "mock_fallback")
    mock_renders     = sum(1 for r in render_urls if r.get("mode") == "mock")

    groq_v_calls  = count_event("vision",   "api_call")
    groq_v_fails  = count_event("vision",   "api_failed")
    groq_p_calls  = count_event("planning", "generating_concepts")
    groq_p_fails  = count_event("planning", "api_failed")
    pinecone_hits = count_event("retrieval","product_selected")
    pinecone_miss = count_event("retrieval","no_match")

    total_calls    = groq_v_calls + groq_p_calls + len(render_urls) + total_searches
    total_failures = groq_v_fails + groq_p_fails + fallback_renders

    # Top events per agent
    def top_events(agent, n=3):
        from collections import Counter
        events = [l.get("event") for l in logs_for(agent)]
        return [{"event": e, "count": c} for e, c in Counter(events).most_common(n)]

    metrics["tool_calls"] = {
        "total_calls":          total_calls,
        "total_failures":       total_failures,
        "overall_success_rate": round(1 - total_failures / max(total_calls, 1), 4),
        "overall_success_pct":  round((1 - total_failures / max(total_calls, 1)) * 100, 1),
        "groq_vision": {
            "calls":        groq_v_calls,
            "failures":     groq_v_fails,
            "success_rate": round(1 - groq_v_fails / max(groq_v_calls, 1), 4),
            "top_events":   top_events("vision"),
            "latency_seconds": round(timings.get("vision_elapsed", 0), 4),
        },
        "groq_planning": {
            "calls":        groq_p_calls,
            "failures":     groq_p_fails,
            "success_rate": round(1 - groq_p_fails / max(groq_p_calls, 1), 4),
            "top_events":   top_events("planning"),
            "latency_seconds": round(timings.get("planning_elapsed", 0), 4),
        },
        "pinecone": {
            "searches":     total_searches,
            "hits":         pinecone_hits,
            "misses":       pinecone_miss,
            "hit_rate":     round(pinecone_hits / max(total_searches, 1), 4),
            "hit_rate_pct": round(pinecone_hits / max(total_searches, 1) * 100, 1),
            "top_events":   top_events("retrieval"),
            "latency_seconds": round(timings.get("retrieval_elapsed", 0), 4),
        },
        "huggingface_flux": {
            "calls":         len(render_urls),
            "real_renders":  real_renders,
            "mock_renders":  mock_renders,
            "fallbacks":     fallback_renders,
            "success_rate":  round(real_renders / max(len(render_urls), 1), 4),
            "success_pct":   round(real_renders / max(len(render_urls), 1) * 100, 1),
            "top_events":    top_events("rendering"),
            "latency_seconds": round(timings.get("rendering_elapsed", 0), 4),
        },
    }

    # ── 8. MEMORY / SESSION ───────────────────────────────────────────────────
    dialogue_history   = state.get("dialogue_history") or []
    refinement_cycles  = max(0, len(dialogue_history) // 2)
    state_fields       = [
        "image_path", "budget", "style", "room_analysis",
        "design_concepts", "furniture_plan", "sourced_products",
        "render_urls", "dialogue_history", "agent_logs", "stage_timings"
    ]
    populated = [f for f in state_fields if state.get(f)]

    import json
    try:
        state_size_kb = round(len(json.dumps({
            k: v for k, v in state.items() if k != "agent_logs"
        })) / 1024, 2)
    except Exception:
        state_size_kb = 0.0

    metrics["memory"] = {
        "session_state_completeness":     round(len(populated) / len(state_fields), 4),
        "session_state_completeness_pct": round(len(populated) / len(state_fields) * 100, 1),
        "populated_state_fields":         populated,
        "total_state_fields":             len(state_fields),
        "dialogue_turns":                 len(dialogue_history),
        "refinement_cycles":              refinement_cycles,
        "has_active_session":             bool(state.get("image_path")),
        "state_size_kb":                  state_size_kb,
        "total_log_events_stored":        len(agent_logs),
        "retry_count":                    state.get("retry_count", 0),
        "mode":                           state.get("mode", "mock"),
    }

    # ── 9. ACTIONS ────────────────────────────────────────────────────────────
    stages_started   = sum(1 for l in agent_logs if l.get("event") == "stage_start")
    stages_completed = sum(1 for l in agent_logs if l.get("event") == "stage_end")
    api_calls_total  = groq_v_calls + groq_p_calls + len(render_urls) + total_searches

    total_decisions  = products_selected + products_rejected + spatial_passes + spatial_fails
    correct          = products_selected + spatial_passes

    metrics["actions"] = {
        "stages_started":          stages_started,
        "stages_completed":        stages_completed,
        "stage_completion_rate":   round(stages_completed / max(stages_started, 1), 4),
        "total_decisions":         total_decisions,
        "correct_decisions":       correct,
        "decision_accuracy":       round(correct / max(total_decisions, 1), 4),
        "decision_accuracy_pct":   round(correct / max(total_decisions, 1) * 100, 1),
        "products_selected":       products_selected,
        "products_rejected":       products_rejected,
        "api_calls_total":         api_calls_total,
        "spatial_checks_passed":   spatial_passes,
        "spatial_checks_failed":   spatial_fails,
        "budget_ceiling_triggers": budget_triggers,
        "pipeline_retries":        state.get("retry_count", 0),
        "fallback_triggered":      bool(state.get("error")),
    }

    # ── 10. CONCEPT DIVERSITY ─────────────────────────────────────────────────
    concept_sets = []
    for concept in sourced:
        ids = {item.get("product_id") for item in concept.get("items", [])}
        concept_sets.append(ids)

    overlap_scores = []
    pairwise = []
    if len(concept_sets) >= 2:
        names = [c.get("concept_name", f"Concept {i}") for i, c in enumerate(sourced)]
        for i in range(len(concept_sets)):
            for j in range(i + 1, len(concept_sets)):
                a, b = concept_sets[i], concept_sets[j]
                if a and b:
                    overlap = round(len(a & b) / max(len(a), len(b)), 4)
                    overlap_scores.append(overlap)
                    pairwise.append({
                        "pair":    f"{names[i]} vs {names[j]}",
                        "overlap": overlap,
                        "overlap_pct": round(overlap * 100, 1),
                        "diverse": overlap < 0.60,
                    })

    avg_overlap     = round(sum(overlap_scores) / len(overlap_scores), 4) if overlap_scores else 0.0
    diversity_score = round(1 - avg_overlap, 4)

    # Style tag overlap between concepts
    concept_tag_sets = [set(c.get("style_tags", [])) for c in concepts]
    tag_overlaps = []
    if len(concept_tag_sets) >= 2:
        for i in range(len(concept_tag_sets)):
            for j in range(i + 1, len(concept_tag_sets)):
                a, b = concept_tag_sets[i], concept_tag_sets[j]
                if a and b:
                    tag_overlaps.append(len(a & b) / max(len(a | b), 1))
    avg_tag_overlap = round(sum(tag_overlaps) / len(tag_overlaps), 4) if tag_overlaps else 0.0

    metrics["concept_diversity"] = {
        "diversity_score":      diversity_score,
        "diversity_score_pct":  round(diversity_score * 100, 1),
        "avg_product_overlap":  avg_overlap,
        "avg_tag_overlap":      avg_tag_overlap,
        "diversity_target_met": avg_overlap < 0.60,
        "pairwise_overlaps":    pairwise,
    }

    # ── 11. ERROR RATE ────────────────────────────────────────────────────────
    errors_by_agent = {}
    for agent in AGENTS:
        errs = [l for l in logs_for(agent) if l.get("level") == "error"]
        warns = [l for l in logs_for(agent) if l.get("level") == "warning"]
        if errs or warns:
            errors_by_agent[agent] = {
                "errors":   len(errs),
                "warnings": len(warns),
                "messages": [l.get("message") for l in (errs + warns)][:5],
            }

    error_logs   = [l for l in agent_logs if l.get("level") == "error"]
    warning_logs = [l for l in agent_logs if l.get("level") == "warning"]
    completed    = len(stage_latencies) == len(AGENTS)

    handoffs = {
        "vision_to_planning":        bool(state.get("room_analysis")),
        "planning_to_optimization":  bool(state.get("design_concepts")),
        "optimization_to_retrieval": bool(state.get("furniture_plan")),
        "retrieval_to_rendering":    bool(state.get("sourced_products")),
        "rendering_complete":        bool(state.get("render_urls")),
    }
    handoff_rate = round(sum(handoffs.values()) / len(handoffs), 4)

    metrics["pipeline_health"] = {
        "completed":            completed,
        "status":               "success" if completed and not state.get("error") else
                                "partial" if stage_latencies else "failed",
        "error":                state.get("error"),
        "handoff_success_rate": handoff_rate,
        "handoff_success_pct":  round(handoff_rate * 100, 1),
        "handoffs":             handoffs,
        "error_count":          len(error_logs),
        "warning_count":        len(warning_logs),
        "error_rate":           round(len(error_logs) / max(len(agent_logs), 1), 4),
        "error_rate_pct":       round(len(error_logs) / max(len(agent_logs), 1) * 100, 1),
        "errors_by_agent":      errors_by_agent,
        "agents_succeeded":     len(stage_latencies),
        "agents_failed":        len(AGENTS) - len(stage_latencies),
        "total_log_events":     len(agent_logs),
    }

    # ── SUMMARY ───────────────────────────────────────────────────────────────
    tool_success = round(1 - total_failures / max(total_calls, 1), 4)
    autonomy     = round((handoff_rate + tool_success + budget_accuracy + coherence_avg) / 4, 4)

    metrics["summary"] = {
        "overall_score":              round((budget_accuracy + coherence_avg + handoff_rate) / 3, 4),
        "overall_score_pct":          round((budget_accuracy + coherence_avg + handoff_rate) / 3 * 100, 1),
        "autonomy_score":             autonomy,
        "autonomy_score_pct":         round(autonomy * 100, 1),
        "budget_accuracy_pct":        round(budget_accuracy * 100, 1),
        "style_coherence_pct":        round(coherence_avg * 100, 1),
        "constraint_satisfaction_pct":round(constraint_rate * 100, 1),
        "planning_diversity_pct":     round(tag_diversity * 100, 1),
        "retrieval_fill_rate_pct":    round(fill_rate * 100, 1),
        "concept_diversity_pct":      round(diversity_score * 100, 1),
        "handoff_success_pct":        round(handoff_rate * 100, 1),
        "tool_success_pct":           round(tool_success * 100, 1),
        "action_accuracy_pct":        round(correct / max(total_decisions, 1) * 100, 1),
        "total_latency_seconds":      round(total_latency, 4),
        "pipeline_status":            metrics["pipeline_health"]["status"],
        "mode":                       state.get("mode", "mock"),
    }

    return metrics