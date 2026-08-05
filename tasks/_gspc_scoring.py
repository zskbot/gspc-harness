"""The GSPC scoring contract, shared by every task in this repository.

Two rules are implemented here rather than merely asserted in prose, because a claim a
harness makes about itself is worth exactly as much as the code behind it.

RULE 1 — AN ANSWER WE COULD NOT PARSE IS *UNMEASURED*, NEVER WRONG.
    A model that emits an unparseable answer has not been measured on that item. Scoring it
    0 silently converts "we do not know" into "the model failed", which flatters every
    competitor whose output happens to fit our regex and punishes verbosity rather than
    error. Unparsed items therefore score NOANSWER and LEAVE THE DENOMINATOR.

    Note that inspect_ai's stock `accuracy()` does NOT do this: its default `value_to_float`
    maps NOANSWER -> 0.0 and keeps the item in the denominator. Returning NOANSWER without
    also replacing the metric would report the unparsed item as wrong anyway. That is why
    `accuracy_measured` exists.

RULE 2 — usable_n >= 30 GATES EVERY INTERVAL, INCLUDING OURS.
    Below 30 usable items an interval is noise presented as precision. `stderr_gated`
    returns NaN rather than a number in that case, so the gate is enforced by the harness
    instead of being left to the good manners of whoever writes up the result. Every task
    in this repository except `govbench` is currently below that floor, and so reports no
    interval. That is the intended, honest behaviour — not a defect.

Both metrics report alongside `usable_n` and `unmeasured` so a reader can always see the
denominator the accuracy was computed over.
"""
from __future__ import annotations

from inspect_ai.scorer import (
    Metric,
    NOANSWER,
    SampleScore,
    ValueToFloat,
    metric,
    stderr,
    value_to_float,
)

#: Below this many usable (parsed) items, no confidence interval is reported.
USABLE_N_FLOOR = 30


def _is_measured(sample_score: SampleScore) -> bool:
    """True when the item produced a parseable answer, i.e. it was actually measured."""
    return sample_score.score.value != NOANSWER


@metric(scores="unreduced")
def accuracy_measured(to_float: ValueToFloat = value_to_float()) -> Metric:
    """Accuracy over PARSED answers only — unparsed items leave the denominator.

    Contrast with inspect_ai's stock `accuracy()`, which scores NOANSWER as 0.0 and keeps
    it in the denominator, thereby reporting "we could not read this" as "the model got
    this wrong".
    """

    def metric_fn(scores: list[SampleScore]) -> float:
        usable = [s for s in scores if _is_measured(s)]
        if not usable:
            return float("nan")
        return sum(to_float(s.score.value) for s in usable) / float(len(usable))

    return metric_fn


@metric(scores="unreduced")
def usable_n() -> Metric:
    """Number of items that yielded a parseable answer. The accuracy denominator."""

    def metric_fn(scores: list[SampleScore]) -> float:
        return float(len([s for s in scores if _is_measured(s)]))

    return metric_fn


@metric(scores="unreduced")
def unmeasured() -> Metric:
    """Number of items reported UNMEASURED — attempted, but not parseable. Never scored wrong."""

    def metric_fn(scores: list[SampleScore]) -> float:
        return float(len([s for s in scores if not _is_measured(s)]))

    return metric_fn


@metric(scores="unreduced")
def stderr_gated(
    to_float: ValueToFloat = value_to_float(), cluster: str | None = None
) -> Metric:
    """Clustered standard error, WITHHELD (NaN) while usable_n < USABLE_N_FLOOR.

    The clustered estimator is inspect_ai's `stderr(cluster=...)`, a direct implementation
    of Miller (arXiv:2411.00640) Appendix A including the C/(C-1) finite-cluster
    correction. Our items are grouped by dimension/anchor/category, so an unclustered
    standard error understates uncertainty; Miller measured up to 3.05x understatement.

    Clustering fixes the estimator. It does not manufacture sample size — hence the gate.
    """
    inner = stderr(to_float=to_float, cluster=cluster)

    def metric_fn(scores: list[SampleScore]) -> float:
        usable = [s for s in scores if _is_measured(s)]
        if len(usable) < USABLE_N_FLOOR:
            return float("nan")
        return inner(usable)

    return metric_fn


def gspc_metrics(cluster: str) -> list[Metric]:
    """The standard GSPC metric block. Use this rather than assembling one per task."""
    return [accuracy_measured(), usable_n(), unmeasured(), stderr_gated(cluster=cluster)]


__all__ = [
    "USABLE_N_FLOOR",
    "accuracy_measured",
    "usable_n",
    "unmeasured",
    "stderr_gated",
    "gspc_metrics",
]
