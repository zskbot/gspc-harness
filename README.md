# gspc-harness — CSOAI governance benchmarks as runnable Inspect evals

Open, runnable evaluation tasks for AI-governance capability, built on
[Inspect](https://inspect.aisi.org.uk/) (UK AI Safety Institute).

**270 items across 4 task files.** Every one is self-contained: items ship as data in this
repository, nothing is downloaded, no API key is obtained from us, and no file here reads a
`.env`. Clone it and it runs.

## Install and run

```bash
git clone https://github.com/CSOAI-ORG/gspc-harness
cd gspc-harness
pip install inspect_ai openai
```

Against any OpenAI-compatible endpoint — here a local [Ollama](https://ollama.com) server,
which needs no key and costs nothing:

```bash
OPENAI_BASE_URL=http://localhost:11434/v1 OPENAI_API_KEY=dummy \
  inspect eval tasks/gspc_governance.py --model openai/qwen2.5:1.5b
```

Against a hosted model:

```bash
export OPENAI_API_KEY=sk-...
inspect eval tasks/govbench_inspect.py --model openai/gpt-4o
```

All four task files were run end to end on a clean clone before this README was written.

> This project is **not on PyPI**. There is no `pip install gspc-harness`. Install from
> this repository. (We learned this the hard way: a sibling repo told readers to
> `pip install govbench`, which installs an unrelated third party's package.)

## The tasks

| file | items | what it measures |
|---|---|---|
| `tasks/govbench_inspect.py` | 193 | Governance knowledge across 26 dimensions — retrieval faithfulness, cross-walk between frameworks, fundamental rights, redress, model attacks. Six task entry points; `govbench` runs all of it. |
| `tasks/defbench_inspect.py` | 45 | Refusal behaviour on a care battery: should the model refuse, and does it? Both directions scored — a model that refuses the benign half is broken too. |
| `tasks/gspc_governance.py` | 24 | EU AI Act risk-tier classification: PROHIBITED / HIGH_RISK / LIMITED_RISK / MINIMAL_RISK, each item anchored to the provision it turns on. |
| `tasks/gspc_xraiv.py` | 8 | Agentic — the model gets a `lookup_ai_act` tool and must reach a verdict having actually consulted the provision. Scores whether it **acted** within the law, not whether it recited it. |

`gspc_governance` includes the cases that separate applying the law from memorising
"Annex III = high risk": the Art 6(3)(a) narrow-procedural-task derogation, the Art 2(6)
research exclusion, and an Art 6(1) safety component that is high-risk *without* going
through Annex III.

## What this repository does not claim

- **No score is quoted here, for any model, including our own.** These are runnable
  instruments, not a leaderboard.
- **Watch the denominator.** `govbench_inspect` has 193 items in aggregate, but its 26
  dimensions hold roughly 5–15 items each. A per-dimension number is far below the n ≥ 30
  usable-items floor we require before attaching a confidence interval, and should not be
  reported as one. The aggregate task is the only slice with a defensible denominator.
- Scoring is deterministic — exact-label or containment matching on constrained output,
  not a model judging another model.
- CSOAI **measures**. It does not certify, and it issues no conformity marks. Nothing a run
  of this harness produces is a certification, an attestation of compliance, or advice.

## What is deliberately not here, and why

Two further Inspect modules exist in CSOAI's internal tree and are **not published,
because they do not run from a clean clone**:

- `care_cost_inspect` — its scorer imports `care_gate_v2`, which imports
  `sovereign_aiact_passport`. That is a dependency chain into internal code, not a leaf.
  Its 45 items are already represented here by `defbench_inspect`, which scores the same
  battery.
- `pqcbench_inspect` — it builds samples from a stored results file, asking a model to
  reproduce our own recorded PASS/FAIL cells. That measures recall of a CSOAI artefact
  rather than governance capability, and the file it reads is not where it looks for it.

There is likewise **no `lm-eval` task set** here. Task YAMLs for lm-evaluation-harness do
not exist yet; when they are written, they will land in this repository.

## Licence

Apache-2.0. See [LICENSE](LICENSE). Items and their statutory anchors may be reused with
attribution.
