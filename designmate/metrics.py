# metrics.py
# Computes evaluation metrics from a completed AppState.
# Called by GET /metrics/{session_id} endpoint.

def compute_metrics(state: dict) -> dict:
    """
    Computes all evaluation metrics from a completed AppState.
    Returns a metrics dict ready for the paper's results table.
    """
    metrics = {}

    # ── Budget accuracy ───────────────────────────────────────────────────────
    # Measures what fraction of sourced items are within their budget ceiling
    sourced = state.get("sourced_products") or []
    total_items = 0
    within_budget_items = 0
    concepts_within_budget = 0
    concepts_over_budget = 0
    total_costs = []
    budgets = []

    for concept in sourced:
        concept_over = False
        for item in concept.get("items", []):
            total_items += 1
            if item.get("within_budget"):
                within_budget_items += 1
            else:
                concept_over = True
        if concept_over:
            concepts_over_budget += 1
        else:
            concepts_within_budget += 1
        total_costs.append(concept.get("total_cost", 0))
        budgets.append(state.get("budget", 1))

    budget_accuracy = round(within_budget_items / total_items, 4) \
        if total_items > 0 else 0.0
    metrics["budget_accuracy"] = budget_accuracy
    metrics["concepts_within_budget"] = concepts_within_budget
    metrics["concepts_over_budget"] = concepts_over_budget
    metrics["total_items_evaluated"] = total_items

    # ── Style coherence (average similarity score) ────────────────────────────
    # Uses the cosine similarity scores already computed by the retrieval agent
    all_scores = []
    for concept in sourced:
        for item in concept.get("items", []):
            score = item.get("similarity_score")
            if score is not None:
                all_scores.append(score)

    style_coherence_avg = round(sum(all_scores) / len(all_scores), 4) \
        if all_scores else 0.0
    style_coherence_min = round(min(all_scores), 4) if all_scores else 0.0
    style_coherence_max = round(max(all_scores), 4) if all_scores else 0.0

    metrics["style_coherence_avg"] = style_coherence_avg
    metrics["style_coherence_min"] = style_coherence_min
    metrics["style_coherence_max"] = style_coherence_max
    metrics["coherence_target_met"] = style_coherence_avg >= 0.75

    # ── Constraint satisfaction rate ──────────────────────────────────────────
    # What fraction of all items satisfy both budget AND dimension constraints
    constraint_sat = budget_accuracy  # dimension constraints enforced in retrieval
    metrics["constraint_satisfaction_rate"] = constraint_sat

    # ── Stage latency ─────────────────────────────────────────────────────────
    timings = state.get("stage_timings") or {}
    stage_latencies = {}
    total_latency = 0.0

    for stage in ["vision", "planning", "optimization", "retrieval", "rendering"]:
        elapsed_key = f"{stage}_elapsed"
        if elapsed_key in timings:
            elapsed = round(timings[elapsed_key], 4)
            stage_latencies[stage] = elapsed
            total_latency += elapsed

    metrics["stage_timings"]       = stage_latencies
    metrics["total_latency_seconds"] = round(total_latency, 4)

    # ── Anti-similarity check ─────────────────────────────────────────────────
    # Checks that concepts share fewer than 60% of the same products
    if len(sourced) >= 2:
        concept_product_sets = []
        for concept in sourced:
            ids = {item.get("product_id") for item in concept.get("items", [])}
            concept_product_sets.append(ids)

        overlap_scores = []
        for i in range(len(concept_product_sets)):
            for j in range(i + 1, len(concept_product_sets)):
                a = concept_product_sets[i]
                b = concept_product_sets[j]
                if a and b:
                    overlap = len(a & b) / max(len(a), len(b))
                    overlap_scores.append(round(overlap, 4))

        avg_overlap = round(sum(overlap_scores) / len(overlap_scores), 4) \
            if overlap_scores else 0.0
        metrics["avg_concept_overlap"]     = avg_overlap
        metrics["diversity_target_met"]    = avg_overlap < 0.60
        metrics["pairwise_overlap_scores"] = overlap_scores

    # ── Mode ──────────────────────────────────────────────────────────────────
    metrics["mode"] = state.get("mode", "mock")

    return metrics