"""PQCBench as Inspect tasks — the continuity lens (post-quantum readiness).

Wraps the 5 PQC criteria × 5 SIGIL chains = 25 cells. The test asks: does your signing
chain survive a post-quantum migration? The honest measured answer is 1/25 — the one
PASS is C2PA's alg_agility via COSE header; everything else fails because no SIGIL
chain names an algorithm and none supports hybrid signatures.

    inspect eval pqcbench_inspect.py --model ollama/qwen2.5:0.5b
    inspect eval pqcbench_inspect.py@pqcbench_continuity --model openai/gpt-4o

HONEST STATE (2026-07-28):
    1 of 25 criteria pass. The failing subject is US.
    All four SIGIL chains fail every criterion.
    NIST IR 8547 disallows EdDSA after 2035.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from inspect_ai import Task, task
    from inspect_ai.dataset import Sample
    from inspect_ai.scorer import Score, Target, accuracy, scorer, stderr
    from inspect_ai.solver import generate
    _HAVE_INSPECT = True
except ImportError:
    _HAVE_INSPECT = False

    def task(f):
        return f

    class _Stub:
        def __init__(self, **kw):
            self.__dict__.update(kw)

    Task = Score = Target = _Stub

    class Sample(_Stub):
        pass


def _pqc_samples() -> list:
    """Build Inspect Samples from pqcbench.json.

    The results dict has crit_name entries AND meta entries (records, signed_records).
    Skip the meta entries — only criteria have pass/fail outcomes.
    """
    pq = json.load(open(Path(__file__).resolve().parent.parent / "benchmark-results" / "pqcbench.json"))
    out = []
    criteria = list(pq.get("criteria", {}).keys())
    for subject, cells in pq.get("results", {}).items():
        for crit_name, outcome in cells.items():
            if not isinstance(outcome, dict):  # skip meta entries
                continue
            target = "PASS" if outcome.get("pass") else "FAIL"
            detail = outcome.get("detail", "")
            out.append(Sample(
                input=f"{subject}: {crit_name}",
                target=target,
                id=f"pqc-{hash(subject + crit_name) % 100000:05d}",
                metadata={"subject": subject, "criterion": crit_name,
                          "mode": "pass" if outcome.get("pass") else "fail",
                          "detail": detail},
            ))
    return out


if _HAVE_INSPECT:
    @scorer(metrics=[accuracy(), stderr(cluster="subject")])
    def pqcbench_scorer():
        """Scores whether model can predict the measured PQC outcome for each (chain, criterion)."""
        async def score(state, target: Target) -> Score:
            answer = state.output.completion or ""
            lo = answer.lower()
            expected = state.metadata.get("mode")
            actual = "pass" if "pass" in lo and ("yes" in lo or "true" in lo or "pass" in lo) else "fail"
            ok = actual == expected
            return Score(value=1.0 if ok else 0.0, answer=answer[:200],
                         explanation=f"expected {expected}, model said {actual}")
        return score

    @task
    def pqcbench_continuity() -> Task:
        """All 25 (subject × criterion) cells from PQCBench."""
        return Task(dataset=_pqc_samples(), solver=generate(), scorer=pqcbench_scorer(),
                    name="pqcbench-continuity", metadata={"benchmark": "pqcbench", "lens": "continuity"})

    @task
    def pqcbench_alg_agility() -> Task:
        """Subset: does the chain name a signing algorithm? NIST IR 8547 hard requirement."""
        samples = [s for s in _pqc_samples() if s.metadata["criterion"] == "alg_agility"]
        return Task(dataset=samples, solver=generate(), scorer=pqcbench_scorer(),
                    name="pqcbench-alg-agility", metadata={"benchmark": "pqcbench", "lens": "continuity", "criterion": "alg_agility"})


if __name__ == "__main__":
    s = _pqc_samples()
    subjects = sorted(set(x.metadata["subject"] for x in s))
    criteria = sorted(set(x.metadata["criterion"] for x in s))
    print(f"  PQCBench → Inspect: {len(s)} samples ({len(subjects)} subjects × {len(criteria)} criteria)")
    print(f"  inspect_ai installed: {_HAVE_INSPECT}")
    print(f"  subjects: {subjects}")
    print(f"  criteria: {criteria}")
    print(f"  exported tasks: pqcbench_continuity, pqcbench_alg_agility")
