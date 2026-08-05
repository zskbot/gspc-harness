# gspc-harness — CSOAI governance benchmarks as runnable Inspect evals

Open, runnable evaluation tasks for AI-governance capability, built on
[Inspect](https://inspect.aisi.org.uk/) (UK AI Safety Institute).

Two tasks ship here. Both are **self-contained** — the items live in the source file, there
is no dataset to download, no API key to obtain from us, and no part of this repository
reads a `.env`. Clone it and it runs.

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
inspect eval tasks/gspc_governance.py --model openai/gpt-4o
```

Both commands above were run end to end on a clean install before this README was written.

> This project is **not on PyPI**. There is no `pip install gspc-harness`. Install from
> this repository. (We learned this the hard way: a sibling repo told readers to
> `pip install govbench`, which installs an unrelated third party's package.)

## The tasks

| task | file | items | what it measures |
|---|---|---|---|
| `gspc_governance` | `tasks/gspc_governance.py` | 24 | EU AI Act risk-tier classification: given a deployment scenario, return PROHIBITED / HIGH_RISK / LIMITED_RISK / MINIMAL_RISK. Every item carries the provision it turns on (Art 5(1)(c), Annex III 4(a), Art 6(3)(a) …). |
| `gspc_xraiv` | `tasks/gspc_xraiv.py` | 8 | Agentic: the model gets a `lookup_ai_act` tool and must reach a verdict having actually consulted the provision. Scores whether it **acted within the law**, not whether it recited it. |

`gspc_governance` includes the cases that separate a model that has memorised "Annex III =
high risk" from one that can apply the law: the Art 6(3)(a) narrow-procedural-task
derogation, the Art 2(6) research exclusion, and an Art 6(1) safety component that is
high-risk *without* going through Annex III.

## What this repository does not claim

- **No score is quoted here, for any model, including our own.** Both tasks are below the
  n ≥ 30 usable-items floor we require before attaching a confidence interval to a number.
  These are runnable instruments; they are not yet a leaderboard.
- Scoring is deterministic — an exact-label match on a constrained output, not a model
  judging another model.
- CSOAI **measures**. It does not certify, and it issues no conformity marks. Nothing a
  run of this harness produces is a certification, an attestation of compliance, or advice.

## What is deliberately not in this repository, and why

Four further Inspect modules exist in CSOAI's internal tree — `govbench_inspect`,
`defbench_inspect`, `pqcbench_inspect`, `care_cost_inspect`. They are **not published here
because they do not currently run from a clean clone**:

- they import scoring code from their parent repository via `sys.path` manipulation, and
- that parent module opens a `.env` file at import time and raises `FileNotFoundError`
  without it.

A public harness must not depend on a secret-bearing file that no external user can have.
Decoupling them is tracked work. Publishing them in their present state would have shipped
four tasks that fail on the first command in this README, which is worse than shipping two
that work.

There is likewise **no `lm-eval` task set** in this repository. Task YAMLs for
lm-evaluation-harness do not exist yet; when they do, they will land here.

## Licence

Apache-2.0. See [LICENSE](LICENSE). Items and their statutory anchors may be reused with
attribution.
