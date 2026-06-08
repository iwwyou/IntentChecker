# IntentChecker

Specification-driven static analysis for numeric logic errors in Solidity
smart contracts. IntentChecker takes developer-supplied *intent
annotations* (pre/post conditions and debug-time invariants) and verifies
them by abstract interpretation over an interval-topology domain, with a
graded `Satisfied / Warning / Violated` signal.

This repository contains the reference implementation, the evaluation
infrastructure for RQ1–RQ3, and reproducibility material for the
companion paper.

## Repository layout

```
.
├── main.py                       # CLI entry point — runs IntentChecker on a case JSON
├── run_case.py                   # convenience wrapper around main.py
├── requirements.txt              # IntentChecker runtime deps
├── install.sh                    # bootstrap script (creates ./.venv, installs deps)
│
├── Analyzer/                     # ContractAnalyzer, GuardianVerificationEngine, CFG builder
├── Domain/                       # interval / boolean / address abstract domains
├── Interpreter/                  # transfer-function evaluation
├── Parser/                       # ANTLR-generated Solidity 0.4–0.8 parser + visitor
├── Utils/                        # shared CFG helpers
├── Dependencies/                 # interface registry, type aliases
├── Libraries/                    # built-in library models (SafeMath, etc.)
│
├── intent-checker/               # VSCode extension front-end (FastAPI WebSocket bridge)
├── Dataset/                      # Web3Bugs + NumScout source corpora used by the paper
│
├── evaluation/
│   ├── RQ1/                      # mitigation experiment — 20 annotated cases × 3 timing runs +
│   │                             #   per-case complexity metrics + scatter-plot generator
│   ├── RQ2/                      # L4/L5 limitation taxonomy — 55 not_detectable cases classified
│   │                             #   along three axes (bug nature / proxy type / L4a sub-axis)
│   ├── RQ3/                      # comparison with GPTScan / NumScout / ScType
│   │                             #   (per-tool drivers + post-hoc aggregator)
│   ├── validation_soundness/     # interval-engine brute-force soundness check (440 combinations)
│   └── DappSCAN_contract_analysis/  # dataset triage notes (not in paper)
│
├── paper/                        # LaTeX sources, figures, tables (frozen per-revision)
└── scripts/                      # one-off dataset / preprocessing helpers
```

## Quick start

### 1. Install IntentChecker

Requires **Python 3.10+**.

```bash
git clone https://github.com/iwwyou/IntentChecker.git
cd IntentChecker
bash install.sh        # creates ./.venv and installs requirements.txt
```

The script auto-detects `python3.10`/`python3.11`/`python3.12` (use
`PYTHON=python3.11 bash install.sh` to force a specific interpreter)
and creates `./.venv`.

Activate the venv:

```bash
source .venv/bin/activate          # macOS / Linux
.venv\Scripts\activate             # Windows (cmd or PowerShell)
```

> **Always run with the `./.venv` interpreter.** IntentChecker requires
> `networkx>=3.4` (pinned in `requirements.txt`). An older `networkx`
> (e.g. `2.5.x`, common in a system/global Python) **silently** breaks
> dependency and library loading: the interface/type-alias registry comes
> up empty and analysis aborts with errors like `member 'sub' is not a
> recognised global-member`, `Modifier 'nonReentrant' is not defined`, or
> `Type 'X' is not defined ...`. Evaluation drivers spawn `main.py` via
> `sys.executable`, so they inherit whatever interpreter launched them —
> launching `run_all.py` / `collect_metrics.py` with the wrong Python makes
> previously-passing cases turn into spurious `ERROR`s. Check with
> `python -c "import networkx; print(networkx.__version__)"`.

### 2. Run a single case

```bash
python main.py evaluation/RQ1/cases/web3bugs_5_H_07/web3bugs_5_H_07.json
```

The output prints the verification verdict
(`SATISFIED` / `WARNING` / `VIOLATED`) per intent annotation and the
total analysis time.

### 3. Reproduce a research question

Each RQ is a separate physical experiment with its own driver(s). Run
them in the listed order — RQ1 timing CSVs are an input to RQ3's
comparison aggregator.

#### RQ1 — Mitigation (20 annotated cases)

```bash
# 3 timing runs + complexity metrics + Pearson correlations
python evaluation/RQ1/collect_metrics.py --runs 3
# Scatter-plot figure (paper/figure/rq1_scatter.pdf)
python evaluation/RQ1/plot_correlations.py
```

`collect_metrics.py --runs 3` calls `run_all.py` three times under the
hood, snapshots each run as `evaluation/RQ1/rq1_run{1,2,3}.csv`,
aggregates per-case mean/stdev/min/max into `rq1_metrics.csv`, and
writes Pearson r per metric to `rq1_correlations.csv`. To re-run a
single case manually use `python evaluation/RQ1/run_all.py --case Nokon`.

#### RQ2 — L4/L5 limitation taxonomy (55 not_detectable cases)

```bash
python evaluation/RQ2/l4_l5_classification.py
```

Each case is hand-reviewed in `evaluation/RQ2/l4_l5_case_review.md`; the
verdict (bug nature, proxy type, L4a sub-axis) is encoded as a Python
dataclass entry in `l4_l5_classification.py`. Running the script
regenerates `l4_l5_classification.csv` and prints summary tabulations.

#### RQ3 — Comparison with GPTScan / NumScout / ScType

```bash
# Run each baseline 3× (annotated-only is enough for Table 9)
for run in run1 run2 run3; do
  python evaluation/RQ3/run_gptscan.py  --run $run --annotated-only
  python evaluation/RQ3/run_numscout.py --run $run --annotated-only
  python evaluation/RQ3/run_sctype.py   --run $run --annotated-only
done
# 51_H_02 / 77_H_01 need the library-inlined variants for NumScout
python evaluation/RQ3/run_numscout_patched.py --run run2
python evaluation/RQ3/run_numscout_patched.py --run run3
# Aggregate into the comparison table + figure
python evaluation/RQ3/rq3_comparison.py
```

The aggregator reads IntentChecker timings from
`evaluation/RQ1/rq1_run{1,2,3}.csv` and per-baseline outputs from
`evaluation/RQ3/outputs/{gptscan,numscout,sctype}/run{1,2,3}/`, then
emits `rq3_comparison_table.csv`, `rq3_comparison_summary.md`, and the
three figure PDFs (`figures/{detection_heatmap,time_comparison,detection_rate}.pdf`).
`time_comparison.{pdf,png}` is also copied into `paper/figure/rq3_time_comparison.{pdf,png}`.

#### Validation-engine soundness (interval comparison)

```bash
python evaluation/validation_soundness/algorithm_soundness.py
```

Brute-force enumerates 11 interval-topology layouts × 5 width profiles ×
8 comparison operators (440 combinations) and verifies each against the
engine's analytic output. Use `--csv` for a per-case CSV, `--summary`
for an aggregate count.

## RQ3 — Setting up the baselines

The reproduce-RQ3 quick-start above assumes `run_gptscan.py` /
`run_numscout.py` / `run_sctype.py` are already executable. This
section covers the one-time setup those drivers depend on. The
baselines live in their own GitHub repositories and are **not
vendored** here — a single bash script clones them at the exact commits
used for the paper, applies the local-mod patches we needed, and
provisions one Python 3.10+ virtualenv per tool:

```bash
bash evaluation/RQ3/setup_rq3_tools.sh                 # installs gptscan + numscout + sctype
bash evaluation/RQ3/setup_rq3_tools.sh gptscan         # one tool only
bash evaluation/RQ3/setup_rq3_tools.sh web3bugs        # also clone the Web3Bugs dataset
bash evaluation/RQ3/setup_dependencies.sh              # npm/yarn install for each Web3Bugs project
```

Each tool ends up at `evaluation/RQ3/tools/<tool>/` with its own venv,
which the in-repo `run_<tool>.py` driver picks up automatically.

Per-tool setup notes, pinned commits, and a description of every patch
file:

- [GPTScan](evaluation/RQ3/patches/gptscan/README.md)
- [NumScout](evaluation/RQ3/patches/numscout/README.md)
- [ScType](evaluation/RQ3/patches/sctype/README.md)

### Host-side prerequisites

| Need | What for | How to get it |
| ---: | :--- | :--- |
| `solc-select` | versioned Solidity binaries (`0.6.12`–`0.8.10`) | `pipx install solc-select && solc-select install 0.6.12 0.7.6 0.8.0 0.8.3 0.8.4 0.8.10` |
| Node + `npm` / `yarn` | hardhat compilation of Web3Bugs projects | https://nodejs.org/, then `bash evaluation/RQ3/setup_dependencies.sh` |
| Web3Bugs clone | per-contest source contracts | `bash evaluation/RQ3/setup_rq3_tools.sh web3bugs` (clones into `evaluation/RQ3/web3bugs/`) |
| OpenAI API key | GPTScan uses GPT-4 internally | Supply via `--key sk-...`, `export OPENAI_API_KEY=sk-...`, or the interactive prompt `run_gptscan.py` shows when neither is set. No key is bundled. |

### Configurable paths (env vars)

| Env var | Default | Used by |
| ---: | :--- | :--- |
| `SOLC_ARTIFACTS` | `~/.solc-select/artifacts` | `run_gptscan.py`, `run_numscout.py`, `run_sctype.py` |
| `WEB3BUGS_CONTRACTS` | `evaluation/RQ3/web3bugs/contracts` if present, else `~/Web3Bugs/contracts` | all RQ3 drivers |
| `SOLC_COPY_TARGETS` | unset | optional — extra dirs to mirror solc into (pathsep-separated) |
| `NUMSCOUT_EXPERIMENT_DIR` | `~/NumScout/.../95_Samples_Run` | one-shot scripts in `scripts/` only |

### NumScout patched variants for 51_H_02 / 77_H_01

Two web3bugs cases (`51_H_02`, `77_H_01`) call `public`/`external`
library functions that compile to unresolved library placeholders
(`__$<hash>$__`) in the bytecode. NumScout's bytecode parser raises
`incomplete push instruction` on those placeholders before analysis
starts. `evaluation/RQ3/workdir_numscout_patched/` contains
library-inlined `*_patched.sol` variants; `run_numscout_patched.py`
runs NumScout on those and writes the result as
`outputs/numscout/run{N}/<case>_patched.json`. `rq3_comparison.py`
prefers `*_patched.json` over the failed plain run when both exist.

## Citing

If you use IntentChecker in academic work, please cite the companion
paper. A BibTeX entry will be added once the paper has a final venue.

## License

To be determined before public release.
