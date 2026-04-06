# evaluator.py
# Test suite runner for the paper's evaluation section.
# Runs the full pipeline against 5 predefined test cases.
# Called by POST /evaluate endpoint.

from graph import app_graph
from metrics import compute_metrics

TEST_CASES = [
    {
        "id": "TC1",
        "description": "Small modern living room, tight budget",
        "budget": 1000.0,
        "style": "modern",
        "image_path": "uploads/mock_test.jpg"
    },
    {
        "id": "TC2",
        "description": "Medium scandinavian living room, mid budget",
        "budget": 2000.0,
        "style": "scandinavian",
        "image_path": "uploads/mock_test.jpg"
    },
    {
        "id": "TC3",
        "description": "Large contemporary living room, high budget",
        "budget": 5000.0,
        "style": "contemporary",
        "image_path": "uploads/mock_test.jpg"
    },
    {
        "id": "TC4",
        "description": "Minimalist room, very tight budget",
        "budget": 500.0,
        "style": "minimalist",
        "image_path": "uploads/mock_test.jpg"
    },
    {
        "id": "TC5",
        "description": "Industrial style, generous budget",
        "budget": 3500.0,
        "style": "industrial",
        "image_path": "uploads/mock_test.jpg"
    }
]


def run_evaluation() -> dict:
    """
    Runs all test cases through the full pipeline.
    Returns structured results table ready for the paper.
    """
    import os
    # Create a dummy image for test cases if it doesn't exist
    os.makedirs("uploads", exist_ok=True)
    if not os.path.exists("uploads/mock_test.jpg"):
        # Create a 1x1 white JPEG as placeholder
        with open("uploads/mock_test.jpg", "wb") as f:
            f.write(bytes([
                0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46,
                0x49, 0x46, 0x00, 0x01, 0x01, 0x00, 0x00, 0x01,
                0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
                0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08,
                0x07, 0x07, 0x07, 0x09, 0x09, 0x08, 0x0A, 0x0C,
                0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
                0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D,
                0x1A, 0x1C, 0x1C, 0x20, 0x24, 0x2E, 0x27, 0x20,
                0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
                0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27,
                0x39, 0x3D, 0x38, 0x32, 0x3C, 0x2E, 0x33, 0x34,
                0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
                0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4,
                0x00, 0x1F, 0x00, 0x00, 0x01, 0x05, 0x01, 0x01,
                0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04,
                0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0xFF,
                0xC4, 0x00, 0xB5, 0x10, 0x00, 0x02, 0x01, 0x03,
                0x03, 0x02, 0x04, 0x03, 0x05, 0x05, 0x04, 0x04,
                0x00, 0x00, 0x01, 0x7D, 0x01, 0x02, 0x03, 0x00,
                0x04, 0x11, 0x05, 0x12, 0x21, 0x31, 0x41, 0x06,
                0x13, 0x51, 0x61, 0x07, 0x22, 0x71, 0x14, 0x32,
                0x81, 0x91, 0xA1, 0x08, 0x23, 0x42, 0xB1, 0xC1,
                0x15, 0x52, 0xD1, 0xF0, 0x24, 0x33, 0x62, 0x72,
                0x82, 0x09, 0x0A, 0x16, 0x17, 0x18, 0x19, 0x1A,
                0x25, 0x26, 0x27, 0x28, 0x29, 0x2A, 0x34, 0x35,
                0x36, 0x37, 0x38, 0x39, 0x3A, 0x43, 0x44, 0x45,
                0x46, 0x47, 0x48, 0x49, 0x4A, 0x53, 0x54, 0x55,
                0x56, 0x57, 0x58, 0x59, 0x5A, 0x63, 0x64, 0x65,
                0x66, 0x67, 0x68, 0x69, 0x6A, 0x73, 0x74, 0x75,
                0x76, 0x77, 0x78, 0x79, 0x7A, 0x83, 0x84, 0x85,
                0x86, 0x87, 0x88, 0x89, 0x8A, 0x92, 0x93, 0x94,
                0x95, 0x96, 0x97, 0x98, 0x99, 0x9A, 0xA2, 0xA3,
                0xA4, 0xA5, 0xA6, 0xA7, 0xA8, 0xA9, 0xAA, 0xB2,
                0xB3, 0xB4, 0xB5, 0xB6, 0xB7, 0xB8, 0xB9, 0xBA,
                0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0xC7, 0xC8, 0xC9,
                0xCA, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8,
                0xD9, 0xDA, 0xE1, 0xE2, 0xE3, 0xE4, 0xE5, 0xE6,
                0xE7, 0xE8, 0xE9, 0xEA, 0xF1, 0xF2, 0xF3, 0xF4,
                0xF5, 0xF6, 0xF7, 0xF8, 0xF9, 0xFA, 0xFF, 0xDA,
                0x00, 0x08, 0x01, 0x01, 0x00, 0x00, 0x3F, 0x00,
                0xFB, 0xD2, 0x8A, 0x28, 0x03, 0xFF, 0xD9
            ]))

    results = []
    summary = {
        "total_cases":                len(TEST_CASES),
        "passed":                     0,
        "failed":                     0,
        "avg_budget_accuracy":        0.0,
        "avg_style_coherence":        0.0,
        "avg_total_latency":          0.0,
        "avg_constraint_satisfaction": 0.0
    }

    for tc in TEST_CASES:
        print(f"[Evaluator] Running test case {tc['id']}: {tc['description']}")
        initial_state = {
            "image_path":       tc["image_path"],
            "budget":           tc["budget"],
            "style":            tc["style"],
            "room_analysis":    None,
            "design_concepts":  None,
            "furniture_plan":   None,
            "sourced_products": None,
            "render_urls":      None,
            "dialogue_history": [],
            "budget_remaining": tc["budget"],
            "error":            None,
            "retry_count":      0,
            "mode":             None,
            "agent_logs":       [],
            "stage_timings":    {},
            "metrics":          None
        }

        try:
            final_state = app_graph.invoke(initial_state)
            metrics = compute_metrics(final_state)
            final_state["metrics"] = metrics

            passed = (
                metrics.get("budget_accuracy", 0) >= 0.5 and
                metrics.get("style_coherence_avg", 0) >= 0.60
            )

            results.append({
                "test_case_id":               tc["id"],
                "description":                tc["description"],
                "budget":                     tc["budget"],
                "style":                      tc["style"],
                "status":                     "passed" if passed else "failed",
                "budget_accuracy":            metrics.get("budget_accuracy"),
                "style_coherence_avg":        metrics.get("style_coherence_avg"),
                "constraint_satisfaction":    metrics.get("constraint_satisfaction_rate"),
                "total_latency_seconds":      metrics.get("total_latency_seconds"),
                "concepts_within_budget":     metrics.get("concepts_within_budget"),
                "concepts_over_budget":       metrics.get("concepts_over_budget"),
                "diversity_target_met":       metrics.get("diversity_target_met"),
                "coherence_target_met":       metrics.get("coherence_target_met"),
                "error":                      final_state.get("error")
            })

            if passed:
                summary["passed"] += 1
            else:
                summary["failed"] += 1

            summary["avg_budget_accuracy"]        += metrics.get("budget_accuracy", 0)
            summary["avg_style_coherence"]        += metrics.get("style_coherence_avg", 0)
            summary["avg_total_latency"]          += metrics.get("total_latency_seconds", 0)
            summary["avg_constraint_satisfaction"] += metrics.get("constraint_satisfaction_rate", 0)

            print(f"[Evaluator] {tc['id']} — "
                  f"budget_accuracy: {metrics.get('budget_accuracy')}, "
                  f"coherence: {metrics.get('style_coherence_avg')}, "
                  f"latency: {metrics.get('total_latency_seconds')}s")

        except Exception as e:
            print(f"[Evaluator] {tc['id']} FAILED with exception: {e}")
            results.append({
                "test_case_id": tc["id"],
                "description":  tc["description"],
                "status":       "error",
                "error":        str(e)
            })
            summary["failed"] += 1

    n = len(TEST_CASES)
    summary["avg_budget_accuracy"]         = round(summary["avg_budget_accuracy"] / n, 4)
    summary["avg_style_coherence"]         = round(summary["avg_style_coherence"] / n, 4)
    summary["avg_total_latency"]           = round(summary["avg_total_latency"] / n, 4)
    summary["avg_constraint_satisfaction"] = round(summary["avg_constraint_satisfaction"] / n, 4)

    return {"summary": summary, "results": results}