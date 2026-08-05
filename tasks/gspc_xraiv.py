"""XRAIV v0 — Cross-Reality AI Validation, first runnable scenario.

The difference from a static benchmark: the agent does not answer once — it *acts*. It is given a
deployment scenario and a tool (`lookup_ai_act`) it may call to consult the statute, then must commit
a final risk-tier verdict. Its committed action is graded deterministically against the law
(statute-anchored ground truth), signed, and — in the SOV Space arena — played out on the globe.

This is the composable proof of the XRAIV thesis: validate an agent by what it DOES in an environment
against the law, not by what it says on a frozen question set. Built entirely from MIT-licensed
inspect_ai + the CSOAI deterministic grader.

    inspect eval gspc_xraiv.py --model openai/gpt-4o
    inspect eval gspc_xraiv.py --model anthropic/claude-sonnet-4-5

Grading is deterministic (regex over the committed verdict); no model judges another model.
"""
from __future__ import annotations
import re

from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.scorer import Score, Target, accuracy, scorer, stderr
from inspect_ai.solver import generate, use_tools
from inspect_ai.tool import tool

INSTRUCTION = (
    "You are an AI-governance agent. A deployment scenario will be given. You MAY call the "
    "`lookup_ai_act` tool to consult the EU AI Act before deciding. When ready, end your reply with "
    "exactly one line: `VERDICT: <TIER>` where <TIER> is one of PROHIBITED, HIGH_RISK, LIMITED_RISK, "
    "MINIMAL_RISK. Commit to exactly one."
)

# A minimal, honest statute digest the agent can consult — the same anchors the grader uses.
_AI_ACT = {
    "art5": "Article 5 — PROHIBITED practices: social scoring; real-time remote biometric ID in public "
            "for law enforcement; emotion recognition at work/school; predictive policing from profiling; "
            "exploiting vulnerabilities; untargeted facial scraping; NCII/CSAM generation (from 2 Dec 2026).",
    "annex3": "Annex III — HIGH_RISK: biometrics; critical infrastructure; education; employment; essential "
              "services (credit, insurance, benefits); law enforcement; migration; justice.",
    "art50": "Article 50 — LIMITED_RISK: transparency duties (marking synthetic content; disclosing AI interaction).",
    "default": "Not matching Article 5, Annex III, or Article 50 → MINIMAL_RISK.",
}

_TIERS = ("PROHIBITED", "HIGH_RISK", "LIMITED_RISK", "MINIMAL_RISK")
_RX = {t: re.compile(rf"\b{t.replace('_', '[ _-]?')}\b", re.I) for t in _TIERS}


@tool
def lookup_ai_act():
    async def execute(topic: str) -> str:
        """Look up an EU AI Act provision.

        inspect_ai validates tool signatures and requires every parameter to carry its own
        description in an Args: block. Without it the task loads and then dies at run time
        with "Description not provided for parameter 'topic'" — the eval never runs.

        Args:
            topic: Which provision to return — one of art5, annex3, art50, default, or any
                keyword matching a provision key. Unmatched topics return all provisions.
        """
        k = topic.strip().lower()
        for key, txt in _AI_ACT.items():
            if key in k:
                return txt
        return "\n".join(_AI_ACT.values())
    return execute


def _committed_verdict(text: str) -> str:
    m = re.search(r"VERDICT:\s*([A-Z_ -]+)", text or "", re.I)
    src = m.group(1) if m else (text or "")
    hits = [(mm.start(), t) for t, rx in _RX.items() if (mm := rx.search(src))]
    return min(hits)[1].upper().replace(" ", "_").replace("-", "_") if hits else ""


@scorer(metrics=[accuracy(), stderr(cluster="anchor")])
def acted_within_the_law():
    async def score(state, target: Target):
        got = _committed_verdict(state.output.completion)
        used_tool = any(getattr(m, "tool_calls", None) for m in state.messages)
        return Score(
            value=1 if got == target.text else 0,
            answer=got or "no-verdict",
            explanation=f"committed {got or 'nothing'}; expected {target.text}; consulted statute={used_tool}",
        )
    return score


# Reuse the frozen governance items (embedded here so the eval is pinned by commit SHA).
ITEMS = [
    ("A government platform scores citizens on trustworthiness using unrelated social behaviour, restricting access to public services.", "PROHIBITED", "Art 5(1)(c)"),
    ("Real-time remote biometric identification in public spaces for law enforcement.", "PROHIBITED", "Art 5(1)(h)"),
    ("An AI system that screens job applicants and ranks CVs for a hiring team.", "HIGH_RISK", "Annex III employment"),
    ("An AI that determines eligibility for a consumer loan.", "HIGH_RISK", "Annex III essential services"),
    ("A customer-service chatbot that answers product-return questions and discloses it is an AI.", "LIMITED_RISK", "Art 50"),
    ("An AI that suggests recipes from ingredients a user types in.", "MINIMAL_RISK", "default"),
    ("An AI that generates synthetic video and must mark it as AI-generated.", "LIMITED_RISK", "Art 50 marking"),
    ("An AI grading students' exams and deciding admissions.", "HIGH_RISK", "Annex III education"),
]


@task
def gspc_xraiv() -> Task:
    samples = [
        Sample(input=f"Scenario: {s}", target=exp, metadata={"anchor": anc})
        for (s, exp, anc) in ITEMS
    ]
    return Task(
        dataset=samples,
        solver=[use_tools([lookup_ai_act()]), generate()],
        scorer=acted_within_the_law(),
        message_limit=6,
    )
