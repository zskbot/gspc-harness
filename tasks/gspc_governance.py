"""GSPC-Governance (COAI-Bench) — EU AI Act risk-tier classification, as an Inspect eval.

By CSOAI, an independent AI-measurement body. Deterministic grading against statute-anchored ground
truth — no LLM judge, so the same answer always scores the same. This is the governance axis of the
GSPC family; it is the first AI-governance benchmark family registered in Inspect Evals.

HONEST SCOPE (the methods contribution): across the 12 governance/agent benchmarks this collides
with, none report item difficulty, item discrimination, dead-item analysis, confidence intervals, or
a minimum-n publication threshold. We report all five and DECLINE to quote an interval on any axis
below usable_n >= 30. This axis is n=24; treat per-axis numbers as directional until n>=30. What is
unmatched here is the METHOD (deterministic grading, published psychometrics), not the sample size.

    inspect eval gspc_governance.py --model openai/gpt-4o
"""
from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.scorer import Score, Target, accuracy, scorer, stderr
from inspect_ai.solver import generate

INSTRUCTION = 'You are classifying an AI system under Regulation (EU) 2024/1689 (the EU AI Act).\\nReply with EXACTLY ONE of these tokens and nothing else — no punctuation, no explanation:\\nPROHIBITED | HIGH_RISK | LIMITED_RISK | MINIMAL_RISK\\n\\nPROHIBITED   = an Article 5 prohibited practice.\\nHIGH_RISK    = Annex III high-risk, or a safety component under Article 6(1).\\nLIMITED_RISK = not high-risk, but Article 50 transparency duties apply (the system\\n               interacts with people, or generates/manipulates content).\\nMINIMAL_RISK = none of the above.\\n\\nScenario: '

# 24 statute-anchored items, frozen. Pinned by this file's commit SHA (no external asset).
ITEMS = [['A government platform scores citizens on trustworthiness using unrelated social behaviour, and the score restricts access to public services.', 'PROHIBITED', 'Art 5(1)(c) social scoring'], ["A wellness app assigns each employee a 'community contribution score' from their social media and off-duty behaviour; low scores reduce access to company benefits.", 'PROHIBITED', 'Art 5(1)(c) social scoring — benign framing, same practice'], ['A retailer scrapes CCTV and public webcam feeds to build a facial recognition database with no targeting criteria.', 'PROHIBITED', 'Art 5(1)(e) untargeted facial scraping'], ['Police run live facial recognition on a public square to identify anyone on a watchlist, with no judicial authorisation and no imminent threat.', 'PROHIBITED', 'Art 5(1)(h) real-time remote biometric ID in public'], ['An AI ranks job applicants and filters CVs before any human sees them.', 'HIGH_RISK', 'Annex III 4(a) employment — recruitment'], ['A hospital deploys a triage model that orders emergency patients by urgency.', 'HIGH_RISK', 'Annex III 5(a) essential services / emergency triage'], ['A bank uses a model to decide consumer creditworthiness for mortgage applications.', 'HIGH_RISK', 'Annex III 5(b) creditworthiness'], ['A university admissions system scores applicants and determines who is admitted.', 'HIGH_RISK', 'Annex III 3(a) education access'], ['A model assesses asylum applications and recommends grant or refusal to caseworkers.', 'HIGH_RISK', 'Annex III 7 migration and asylum'], ['An AI component controls pressure regulation in a municipal drinking-water network.', 'HIGH_RISK', 'Annex III 2 critical infrastructure safety component'], ['An insurer uses AI for risk assessment and pricing of life and health insurance.', 'HIGH_RISK', 'Annex III 5(c) life/health insurance risk assessment'], ['A retail website runs a customer-service chatbot that answers questions about orders.', 'LIMITED_RISK', 'Art 50(1) disclosure that the user interacts with an AI'], ['A marketing tool generates photorealistic images of people for ad campaigns.', 'LIMITED_RISK', 'Art 50(2) synthetic content marking'], ['A newsroom tool produces synthetic voice-overs of presenters reading published articles.', 'LIMITED_RISK', 'Art 50(4) deep fake / synthetic audio disclosure'], ["A spam filter classifies inbound email for a company's staff mailboxes.", 'MINIMAL_RISK', 'No Annex III use case — employment context but not an employment decision'], ['A warehouse uses AI to optimise pallet placement and forklift routing for throughput.', 'MINIMAL_RISK', 'Industrial optimisation, no Annex III category, no safety component'], ["A video game uses AI to adapt enemy difficulty to the player's skill.", 'MINIMAL_RISK', 'Recital ic — AI in video games, minimal risk'], ['Software flags CVs containing keywords and forwards them to a recruiter, who reads every CV in full regardless and makes all decisions. It performs a narrow procedural task and does not materially influence the outcome.', 'MINIMAL_RISK', 'Art 6(3)(a) derogation — narrow procedural task, no material influence'], ['A call-centre tool infers the emotional state of employees from their voice during calls and reports it to their managers.', 'PROHIBITED', 'Art 5(1)(f) emotion inference in the workplace'], ['A security product categorises people from facial images to infer their ethnicity and political orientation.', 'PROHIBITED', 'Art 5(1)(g) biometric categorisation inferring protected attributes'], ['An AI is the safety component of a surgical robot, and that robot needs third-party conformity assessment under the Medical Devices Regulation.', 'HIGH_RISK', 'Art 6(1) — safety component of a regulated product; NOT via Annex III'], ['A model is developed and used solely for scientific research and is never placed on the market or put into service.', 'MINIMAL_RISK', 'Art 2(6) — scientific research and development is out of scope'], ['An AI profiles which residents of a city are likely to commit a crime, based purely on personality traits and background, with no link to objective verifiable facts.', 'PROHIBITED', 'Art 5(1)(d) predictive policing on profiling alone'], ['A model that detects manufacturing defects on a bottling line is used to route faulty bottles to a reject bin. No person is assessed and no regulated product safety function depends on it.', 'MINIMAL_RISK', 'Industrial QC — no Annex III use, not an Art 6(1) safety component']]

import re
_TIERS = ("PROHIBITED", "HIGH_RISK", "LIMITED_RISK", "MINIMAL_RISK")
_RX = {t: re.compile(rf"\b{t.replace('_', '[ _-]?')}\b", re.I) for t in _TIERS}

def _extract_tier(text: str) -> str:
    hits = [(m.start(), t) for t, rx in _RX.items() if (m := rx.search(text or ""))]
    return min(hits)[1].upper().replace(" ", "_").replace("-", "_") if hits else ""

@scorer(metrics=[accuracy(), stderr(cluster="anchor")])
def tier_match():
    async def score(state, target: Target):
        got = _extract_tier(state.output.completion)
        return Score(value=1 if got == target.text else 0,
                     answer=got or "declined",
                     explanation=f"expected {target.text}")
    return score

@task
def gspc_governance() -> Task:
    samples = [Sample(input=INSTRUCTION + "\n\nScenario: " + s, target=exp, metadata={"anchor": anc})
               for (s, exp, anc) in ITEMS]
    return Task(dataset=samples, solver=generate(), scorer=tier_match())
