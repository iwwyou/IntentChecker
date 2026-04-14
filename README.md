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
│   ├── RQ1/                      # main mitigation experiment (20 annotated cases + 55 limitation cases)
│   ├── RQ3/                      # comparison with GPTScan / NumScout / ScType
│   └── validation_soundness/     # validation-engine brute-force soundness check (440 cases)
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

### 2. Run a single case

```bash
python main.py evaluation/RQ1/cases/web3bugs_5_H_07/web3bugs_5_H_07.json
```

The output prints the verification verdict
(`SATISFIED` / `WARNING` / `VIOLATED`) per intent annotation and the
total analysis time.

### 3. Reproduce a research question

| RQ | Section | Driver script |
| -- | --- | --- |
| **RQ1** — Mitigation | `evaluation/RQ1/` | `python evaluation/RQ1/run_all.py` |
| **RQ2** — Annotation expressibility | `evaluation/RQ1/` (limitation taxonomy) | `python evaluation/RQ1/run_all.py` (same cases, classified post-hoc) |
| **RQ3** — Comparison with existing tools | `evaluation/RQ3/` | `python evaluation/RQ3/rq3_comparison.py` |
| Validation-engine soundness | `evaluation/validation_soundness/` | `python evaluation/validation_soundness/algorithm_soundness.py` |

> **Note on naming.** The paper's `RQ1`/`RQ2` correspond to a single
> physical experiment (the 20-case mitigation set + the 55 not_detectable
> cases) which lives under `evaluation/RQ1/`. The earlier
> validation-engine brute-force check, which used to be called
> `evaluation/RQ1/`, is now under `evaluation/validation_soundness/`.
> The `paper/` LaTeX still uses the original RQ1/RQ2/RQ3 labels.

## RQ3 — Comparison with GPTScan, NumScout, ScType

RQ3 compares IntentChecker against three publicly available baselines.
Each baseline lives in its own GitHub repository and is **not vendored**
into this repo. A single bash script clones them all at the exact commits
used for the paper, applies the small local-mod patches we needed, and
provisions one Python 3.10+ virtualenv per tool:

```bash
bash evaluation/RQ3/setup_rq3_tools.sh                 # installs gptscan + numscout + sctype
bash evaluation/RQ3/setup_rq3_tools.sh gptscan         # one tool only
bash evaluation/RQ3/setup_rq3_tools.sh web3bugs        # also clone the Web3Bugs dataset
bash evaluation/RQ3/setup_dependencies.sh              # npm/yarn install for each Web3Bugs project
```

After running the script, each tool sits under
`evaluation/RQ3/tools/<tool>/` with its own venv, and the in-repo
`run_<tool>.py` driver picks the venv up automatically.

Per-tool setup notes, pinned commits, and a description of every patch
file:

- [GPTScan](evaluation/RQ3/patches/gptscan/README.md)
- [NumScout](evaluation/RQ3/patches/numscout/README.md)
- [ScType](evaluation/RQ3/patches/sctype/README.md)

### Host-side prerequisites for RQ3

| Need | What for | How to get it |
| ---: | :--- | :--- |
| `solc-select` | versioned Solidity binaries (`0.6.12`–`0.8.10`) | `pipx install solc-select && solc-select install 0.6.12 0.7.6 0.8.0 0.8.3 0.8.4 0.8.10` |
| Node + `npm` / `yarn` | hardhat compilation of Web3Bugs projects | https://nodejs.org/, then `bash evaluation/RQ3/setup_dependencies.sh` |
| Web3Bugs clone | per-contest source contracts | `bash evaluation/RQ3/setup_rq3_tools.sh web3bugs` (clones into `evaluation/RQ3/web3bugs/`) |
| OpenAI API key | GPTScan uses GPT-4 internally | Supply it via `--key sk-...`, `export OPENAI_API_KEY=sk-...`, or the interactive prompt `run_gptscan.py` shows when neither is set. No key is bundled in the repo. |

### Configurable paths (env vars)

| Env var | Default | Used by |
| ---: | :--- | :--- |
| `SOLC_ARTIFACTS` | `~/.solc-select/artifacts` | `run_gptscan.py`, `run_numscout.py`, `run_sctype.py` |
| `WEB3BUGS_CONTRACTS` | `evaluation/RQ3/web3bugs/contracts` if present, else `~/Web3Bugs/contracts` | all RQ3 drivers |
| `SOLC_COPY_TARGETS` | unset | optional — extra dirs to mirror solc into (pathsep-separated) |
| `NUMSCOUT_EXPERIMENT_DIR` | `~/NumScout/.../95_Samples_Run` | one-shot scripts in `scripts/` only |

### Reproducing the paper's RQ3 figures and tables

```bash
# (after install.sh + setup_rq3_tools.sh + per-case runs)
python evaluation/RQ3/rq3_comparison.py
```

This regenerates `evaluation/RQ3/figures/{detection_heatmap,time_comparison,detection_rate}.pdf`
and copies `time_comparison.pdf` into `paper/figure/rq3_time_comparison.pdf`.

## VSCode extension (`intent-checker/`)

The repo also ships a small VSCode extension that talks to a local
IntentChecker instance over WebSockets (`WebSocketServer.py`). It is
**optional** for reproducibility — every experiment in the paper runs
through `python main.py` directly. To build the extension:

```bash
cd intent-checker
npm install
# launch a VSCode "Run Extension" debug session
```

## Citing

If you use IntentChecker in academic work, please cite the companion
paper. A BibTeX entry will be added once the paper has a final venue.

## License

To be determined before public release.
