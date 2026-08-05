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

import json as _json
from pathlib import Path as _Path


def _load_json(name):
    """Load vendored items. These modules previously imported the parent repo or read a
    results file that is not in this repository, so they loaded and then died at RUN time
    with 'No inspect tasks were found' — advertised in the README and broken on the first
    command."""
    return _json.loads((_Path(__file__).resolve().parent.parent / "data" / name).read_text())


import json
import sys
from pathlib import Path


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


# Fail loudly before ANY inspect_ai symbol is used. This guard previously sat just
# above the first @task, which is below the first @scorer — so the module still died
# with a bare NameError on `scorer` instead of saying inspect_ai was missing.
if not _HAVE_INSPECT:
    raise ImportError("inspect_ai is required to build these tasks. Install it with: pip install inspect_ai")

def _pqc_samples() -> list:
    """Build capability items, not recall items.

    The previous version asked the model to reproduce a stored verdict: the input was
    "<subject>: <criterion>" and the target was the PASS/FAIL cell CSOAI had already
    published. A model that had read our results page would score well without being able
    to reason about post-quantum continuity at all, and a model that had not would be
    guessing. That measures recall of a published artefact, not governance capability.

    Each item now states the CRITERION and the OBSERVED EVIDENCE, and asks whether the
    evidence satisfies the criterion. The subject is deliberately withheld, so the stored
    verdict cannot be looked up or recognised — the model has to apply the rule to the
    facts. Same cells, same ground truth, a different question.
    
    MAJORITY-CLASS WARNING, and it is severe. The ground truth is 24 FAIL to 1 PASS,
    because the five measured formats genuinely fail almost every post-quantum continuity
    criterion. A model that answers FAIL to every item scores 0.96 without reading a word.
    Any accuracy from this task must be reported against that 0.96 floor, not against 0.5,
    and a score below 0.96 is worse than a constant. This axis discriminates almost
    nothing as it stands and should not be quoted as a capability result until the item
    set includes formats that pass.
    """
    pq = _load_json("pqcbench.json")
    criteria = pq.get("criteria", {})
    out = []
    for subject, cells in pq.get("results", {}).items():
        for crit_name, outcome in cells.items():
            if not isinstance(outcome, dict):  # meta entries carry no verdict
                continue
            definition = criteria.get(crit_name)
            detail = (outcome.get("detail") or "").strip()
            # An item with no criterion definition or no evidence cannot be answered from
            # what it states, so it is not asked. Dropping it beats scoring a guess.
            if not definition or not detail:
                continue
            out.append(Sample(
                input=(
                    "A signed-record format was assessed against one post-quantum "
                    "continuity criterion.\n\n"
                    f"CRITERION ({crit_name}): {definition}\n\n"
                    f"OBSERVED: {detail}\n\n"
                    "Does the observed evidence satisfy the criterion? "
                    "Reply with exactly one word: PASS or FAIL."
                ),
                target="PASS" if outcome.get("pass") else "FAIL",
                id=f"pqc-{crit_name}-{abs(hash(subject + crit_name)) % 10000:04d}",
                metadata={"criterion": crit_name,
                          "mode": "pass" if outcome.get("pass") else "fail",
                          # subject is kept for auditing the item, never shown to the model
                          "subject": subject},
            ))
    return out


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
