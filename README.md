# gspc-harness — CSOAI governance benchmarks as runnable Inspect evals

Open, runnable evaluation tasks for AI-governance capability, built on
[Inspect](https://inspect.aisi.org.uk/) (UK AI Safety Institute).

**270 items across 4 task files, 241 of them carrying an answer key.** Every task is
self-contained: items ship as data in this repository, nothing is downloaded, no API key is
obtained from us, and no file here reads a `.env`. Clone it and it runs.

## Install and run

```bash
git clone https://github.com/CSOAI-ORG/gspc-harness
cd gspc-harness
pip install inspect_ai openai
```

### One command per axis

Each task file runs standalone. Substitute any Inspect-supported model.

```bash
inspect eval tasks/gspc_governance.py  --model openai/gpt-4o   # governance  — 24 items
inspect eval tasks/gspc_xraiv.py       --model openai/gpt-4o   # agentic     —  8 items
inspect eval tasks/defbench_inspect.py --model openai/gpt-4o   # safety      — 45 items
inspect eval tasks/govbench_inspect.py --model openai/gpt-4o   # governance  — 193 items
```

Any OpenAI-compatible endpoint works — here a local [Ollama](https://ollama.com) server,
which needs no key and costs nothing:

```bash
OPENAI_BASE_URL=http://localhost:11434/v1 OPENAI_API_KEY=dummy \
  inspect eval tasks/gspc_governance.py --model openai/qwen2.5:1.5b
```

To check the harness itself without spending anything, run it against Inspect's built-in
mock provider. This exercises task discovery, dataset construction, solver, scorer and
metrics without contacting any API:

```bash
inspect eval tasks/gspc_governance.py --model mockllm/model
```

**Verification status.** All four task files, and all ten task entry points, were loaded,
built and run end to end on a clean clone at the current commit using `mockllm/model`.
That verifies the harness mechanics, not model quality — no score for any model, ours
included, is published here.

> This project is **not on PyPI**. There is no `pip install gspc-harness`. Install from
> this repository. (We learned this the hard way: a sibling repo told readers to
> `pip install govbench`, which installs an unrelated third party's package.)

## The tasks

| file | items | usable | what it measures |
|---|---|---|---|
| `tasks/govbench_inspect.py` | 193 | 164 | Governance knowledge across 26 dimensions — retrieval faithfulness, cross-walk between frameworks, fundamental rights, redress, model attacks. Six task entry points; `govbench` runs all of it, and is the only task clearing the n ≥ 30 interval floor. |
| `tasks/defbench_inspect.py` | 45 | 45 | Refusal behaviour on a care battery: should the model refuse, and does it? Both directions scored — a model that refuses the benign half is broken too. |
| `tasks/gspc_governance.py` | 24 | 24 | EU AI Act risk-tier classification: PROHIBITED / HIGH_RISK / LIMITED_RISK / MINIMAL_RISK, each item anchored to the provision it turns on. |
| `tasks/gspc_xraiv.py` | 8 | 8 | Agentic — the model gets a `lookup_ai_act` tool and must reach a verdict having actually consulted the provision. Scores whether it **acted** within the law, not whether it recited it. |

"usable" is the maximum denominator: items carrying an answer key. The realised
`usable_n` for a given run can be lower still, because an unparsed answer is UNMEASURED
rather than wrong — see the honesty register below.

`gspc_governance` includes the cases that separate applying the law from memorising
"Annex III = high risk": the Art 6(3)(a) narrow-procedural-task derogation, the Art 2(6)
research exclusion, and an Art 6(1) safety component that is high-risk *without* going
through Annex III.

## The honesty register

These four rules are **implemented in [`tasks/_gspc_scoring.py`](tasks/_gspc_scoring.py)**,
not merely asserted here. A claim a harness makes about itself is worth exactly as much as
the code behind it, so each rule below names the mechanism that enforces it.

1. **Grading is deterministic.** Exact-label or containment matching on constrained output.
   No model judges another model, so the same answer always scores the same.

2. **An unparsed answer is reported UNMEASURED — never scored wrong.** A model that returns
   something we cannot parse has not been measured on that item; scoring it 0 would convert
   "we do not know" into "the model failed". Such items score `NOANSWER` and **leave the
   denominator** (`accuracy_measured`), and are counted separately (`unmeasured`).
   Note this is *not* Inspect's default: stock `accuracy()` maps `NOANSWER` to 0.0 and
   keeps it in the denominator, which is why this repository ships its own metric.
   With every item unparsed, accuracy reports `nan` and `usable_n` 0 — never `0.000`.

3. **`usable_n >= 30` gates every interval, including ours.** Below 30 usable items,
   `stderr_gated` returns `NaN` instead of a number, so the floor is enforced by the
   harness rather than left to whoever writes up the result. At present only the aggregate
   `govbench` task clears it; **every other task in this repository reports no interval by
   construction.** That is intended behaviour, not a defect.

4. **CSOAI measures. It does not certify.** No conformity marks are issued. Nothing a run
   of this harness produces is a certification, an attestation of compliance, or advice.

Every scorer therefore reports four numbers together — `accuracy_measured`, `usable_n`,
`unmeasured`, `stderr_gated` — so the denominator an accuracy was computed over is always
visible next to the accuracy itself.

### Known limits of the item set

- **29 of the 193 `govbench` items ship without an answer key** (24 in `robustness`, 5 in
  `fairness`) and are reported UNMEASURED rather than scored. The aggregate task's real
  denominator is therefore **164, not 193**. These items are a defect in our data, not in
  the model under test, and charging a model for our missing key would be exactly the error
  rule 2 exists to prevent. They are kept, and disclosed, rather than quietly deleted.
- **No score is quoted here, for any model, including our own.** These are runnable
  instruments, not a leaderboard.
- **Watch the denominator.** `govbench`'s 26 dimensions hold roughly 5–15 items each, so
  every per-dimension task is far below the n ≥ 30 floor and reports no interval. The
  aggregate task is the only slice with a defensible denominator.
- **No external dataset is fetched.** Items live in this repository, so no rename or
  redirect of any hosted dataset can silently change what this harness measures.

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
