# GPTScan setup notes (RQ3 reproducibility)

GPTScan is one of the four tools compared in RQ3. The repo does **not**
vendor its source — `evaluation/RQ3/setup_rq3_tools.sh` clones it into
`evaluation/RQ3/tools/gptscan/` (which is gitignored) at a pinned commit
and provisions a dedicated venv.

## Upstream version

| Field | Value |
| ---: | :--- |
| Upstream | https://github.com/GPTScan/GPTScan |
| Pinned commit | `29a17477` (matches the version used for the paper) |
| Python | 3.10+ (the wheels in `requirements_win.txt` target CPython 3.10) |

## Local modifications captured by `local_mods.patch`

1. **`src/analyze_pipeline.py` — LLM call timeout `90s` → `300s`.**
   The default 90-second deadline trips on long completions for the
   larger Web3Bugs contracts; bumping the timeout removes spurious
   `ask_with_timeout` failures while leaving the analysis logic
   identical.

2. **`src/tasks.py` — re-use pre-compiled hardhat artifacts.**
   `compile_project()` now passes `ignore_compile=True` and
   `hardhat_ignore_compile=True` to the underlying `falcon.Falcon`
   call. We pre-compile each Web3Bugs project once via
   `compile_hardhat()` in `evaluation/RQ3/run_gptscan.py`, then point
   GPTScan at the existing `artifacts/build-info/` instead of letting
   crytic-compile re-run a hardhat compile per case (which is slow,
   reorders solc output, and sometimes fails on projects that need a
   custom env).

Both modifications are functional optimizations only; they do **not**
change which findings GPTScan emits.

## Setup

```bash
# From the repo root
bash evaluation/RQ3/setup_rq3_tools.sh gptscan
```

After the script finishes you will have:

```
evaluation/RQ3/tools/gptscan/
├── src/                       # GPTScan source at the pinned commit
├── requirements_win.txt
├── venv/                      # dedicated Python 3.10+ virtualenv
└── ...
```

## Running

`evaluation/RQ3/run_gptscan.py` invokes the venv automatically. It also
needs:

- **An OpenAI API key.** The repo ships **no default key** — the script
  resolves one from, in priority order:
  1. The `--key sk-...` CLI flag
  2. The `OPENAI_API_KEY` environment variable
  3. An interactive `getpass()` prompt (hidden input) when neither of
     the above is set and stdin is a TTY
  If none of the three is provided, the script exits with an error.
  GPTScan itself makes GPT-4 calls per case, so review OpenAI's current
  per-token pricing before launching a full run.
- `solc-select` with the per-case Solidity versions installed
  (`solc-select install 0.6.12 0.7.6 0.8.0 0.8.3 0.8.4 0.8.10 ...`)
- The Web3Bugs dataset cloned at `evaluation/RQ3/web3bugs/contracts/`
  (run `bash evaluation/RQ3/setup_rq3_tools.sh web3bugs` to fetch it)
  with each contest's `npm install` / `yarn install` complete
  (`bash evaluation/RQ3/setup_dependencies.sh`)

Example:

```bash
python evaluation/RQ3/run_gptscan.py --case web3bugs_5_H_07 --run run1
python evaluation/RQ3/run_gptscan.py --annotated-only --run run1
```

Outputs land in `evaluation/RQ3/outputs/gptscan/<run>/`.
