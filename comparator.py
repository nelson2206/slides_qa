"""Holmes comparator — diff two QA results to surface what changed between
deck versions.

Inputs are the `result` dicts returned by `qa.run_local_qa` / `qa.run_full_qa`.
The comparator does not care which slide is 'v1' vs 'v2' — it just computes
deltas keyed by slide_number, plus aggregate metrics.
"""
from __future__ import annotations

from typing import Any

from qa import SEVERITY_ORDER, severity_for


# Severity ranks for "got better / got worse" detection
_SEV_RANK = {"critical": 0, "warning": 1, "nit": 2, "ok": 3}


def _avg_score(slides: list[dict[str, Any]]) -> float:
    scores = [s.get("score") for s in slides if s.get("score") is not None]
    return sum(scores) / len(scores) if scores else 0.0


def _severity_counts(slides: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {s: 0 for s in SEVERITY_ORDER}
    for s in slides:
        sev = s.get("severity") or severity_for(s.get("score"))
        counts[sev] = counts.get(sev, 0) + 1
    return counts


def _slide_short_label(slide: dict[str, Any]) -> str:
    """Best human-readable label for a slide: action_title.current_title or '#N'."""
    n = slide["slide_number"]
    title = ((slide.get("action_title") or {}).get("current_title") or "").strip()
    if title:
        return f"#{n} · {title[:70]}{'…' if len(title) > 70 else ''}"
    return f"#{n}"


def compare_results(result_v1: dict[str, Any], result_v2: dict[str, Any]) -> dict[str, Any]:
    """Compute the delta between two QA results.

    Returns:
      {
        'aggregate': { score_v1, score_v2, score_delta, sev_v1, sev_v2 },
        'per_slide': [ { slide_number, label, score_v1, score_v2, score_delta,
                         severity_v1, severity_v2, direction } ],
        'improved': [...subset of per_slide...],
        'regressed': [...subset of per_slide...],
        'unchanged': [...subset of per_slide...],
        'added': [...slides only in v2...],
        'removed': [...slides only in v1...],
      }
    """
    slides_v1 = result_v1.get("slides") or []
    slides_v2 = result_v2.get("slides") or []

    by_n_v1 = {s["slide_number"]: s for s in slides_v1}
    by_n_v2 = {s["slide_number"]: s for s in slides_v2}

    all_nums = sorted(set(by_n_v1.keys()) | set(by_n_v2.keys()))

    per_slide: list[dict[str, Any]] = []
    improved: list[dict[str, Any]] = []
    regressed: list[dict[str, Any]] = []
    unchanged: list[dict[str, Any]] = []
    added: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []

    for n in all_nums:
        s1 = by_n_v1.get(n)
        s2 = by_n_v2.get(n)

        if s1 is None and s2 is not None:
            added.append({
                "slide_number": n,
                "label": _slide_short_label(s2),
                "score_v2": s2.get("score"),
                "severity_v2": s2.get("severity") or severity_for(s2.get("score")),
            })
            continue
        if s1 is not None and s2 is None:
            removed.append({
                "slide_number": n,
                "label": _slide_short_label(s1),
                "score_v1": s1.get("score"),
                "severity_v1": s1.get("severity") or severity_for(s1.get("score")),
            })
            continue
        if s1 is None or s2 is None:
            continue

        sev1 = s1.get("severity") or severity_for(s1.get("score"))
        sev2 = s2.get("severity") or severity_for(s2.get("score"))
        score1 = s1.get("score")
        score2 = s2.get("score")
        score_delta = (
            (score2 or 0) - (score1 or 0)
            if (score1 is not None and score2 is not None)
            else 0
        )
        # Direction by SEVERITY first (more meaningful than ±1 score wobble)
        if _SEV_RANK[sev2] > _SEV_RANK[sev1]:
            direction = "improved"
        elif _SEV_RANK[sev2] < _SEV_RANK[sev1]:
            direction = "regressed"
        elif score_delta > 0:
            direction = "improved"
        elif score_delta < 0:
            direction = "regressed"
        else:
            direction = "unchanged"

        row = {
            "slide_number": n,
            "label": _slide_short_label(s2),  # use v2 label as the "current"
            "score_v1": score1,
            "score_v2": score2,
            "score_delta": score_delta,
            "severity_v1": sev1,
            "severity_v2": sev2,
            "direction": direction,
        }
        per_slide.append(row)
        if direction == "improved":
            improved.append(row)
        elif direction == "regressed":
            regressed.append(row)
        else:
            unchanged.append(row)

    aggregate = {
        "score_v1": _avg_score(slides_v1),
        "score_v2": _avg_score(slides_v2),
        "sev_v1": _severity_counts(slides_v1),
        "sev_v2": _severity_counts(slides_v2),
        "slide_count_v1": len(slides_v1),
        "slide_count_v2": len(slides_v2),
    }
    aggregate["score_delta"] = aggregate["score_v2"] - aggregate["score_v1"]
    aggregate["sev_delta"] = {
        k: aggregate["sev_v2"].get(k, 0) - aggregate["sev_v1"].get(k, 0)
        for k in SEVERITY_ORDER
    }

    return {
        "aggregate": aggregate,
        "per_slide": per_slide,
        "improved": improved,
        "regressed": regressed,
        "unchanged": unchanged,
        "added": added,
        "removed": removed,
    }
