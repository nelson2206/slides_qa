from __future__ import annotations

from comparator import compare_results


def _slide(n: int, score: int, severity: str | None = None, title: str = "") -> dict:
    return {
        "slide_number": n,
        "score": score,
        "severity": severity,
        "action_title": {"current_title": title},
    }


def test_compare_results_detects_improvement():
    v1 = {"slides": [_slide(1, 4, "critical"), _slide(2, 7, "warning")]}
    v2 = {"slides": [_slide(1, 8, "nit"), _slide(2, 7, "warning")]}
    diff = compare_results(v1, v2)
    assert diff["aggregate"]["score_delta"] > 0
    assert len(diff["improved"]) == 1
    assert diff["improved"][0]["slide_number"] == 1
    assert diff["improved"][0]["direction"] == "improved"


def test_compare_results_detects_regression():
    v1 = {"slides": [_slide(1, 9, "ok")]}
    v2 = {"slides": [_slide(1, 4, "critical")]}
    diff = compare_results(v1, v2)
    assert diff["aggregate"]["score_delta"] < 0
    assert len(diff["regressed"]) == 1
    assert diff["regressed"][0]["direction"] == "regressed"


def test_compare_results_classifies_unchanged():
    v1 = {"slides": [_slide(1, 8, "nit")]}
    v2 = {"slides": [_slide(1, 8, "nit")]}
    diff = compare_results(v1, v2)
    assert len(diff["unchanged"]) == 1
    assert diff["aggregate"]["score_delta"] == 0


def test_compare_results_handles_added_and_removed_slides():
    v1 = {"slides": [_slide(1, 7, "warning"), _slide(2, 8, "nit")]}
    v2 = {"slides": [_slide(1, 7, "warning"), _slide(3, 9, "ok")]}
    diff = compare_results(v1, v2)
    assert {s["slide_number"] for s in diff["added"]} == {3}
    assert {s["slide_number"] for s in diff["removed"]} == {2}


def test_compare_results_aggregate_severity_deltas():
    v1 = {"slides": [_slide(1, 4, "critical"), _slide(2, 4, "critical")]}
    v2 = {"slides": [_slide(1, 9, "ok"), _slide(2, 9, "ok")]}
    diff = compare_results(v1, v2)
    agg = diff["aggregate"]
    assert agg["sev_delta"]["critical"] == -2
    assert agg["sev_delta"]["ok"] == 2


def test_compare_results_direction_uses_severity_then_score():
    """Severity change trumps small score wobble."""
    # Same score-bucket but score changed by 1 → severity unchanged → 'improved'
    v1 = {"slides": [_slide(1, 7, "warning")]}
    v2 = {"slides": [_slide(1, 8, "nit")]}
    diff = compare_results(v1, v2)
    assert diff["per_slide"][0]["direction"] == "improved"
