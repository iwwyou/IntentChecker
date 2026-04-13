# NumScout setup notes (RQ3 reproducibility)

NumScout is one of the four tools compared in RQ3.
`evaluation/RQ3/setup_rq3_tools.sh` clones it into
`evaluation/RQ3/tools/numscout/` (gitignored) at a pinned commit and
creates a dedicated venv.

## Upstream version

| Field | Value |
| ---: | :--- |
| Upstream | https://github.com/NumScout/NumScout |
| Pinned commit | `3abc0f3b` (matches the version used for the paper) |
| Python | 3.10+ |

## Local modifications captured by `local_mods.patch`

1. **`feature_detector/semantic_analysis.py` — `safeTransfer` handler
   typo fix.**
   In NumScout's `precision_loss_analysis`, the `.safeTransfer` branch
   pops a stack value into a local named `value` but then references a
   different (unbound) name `amount` when calling
   `check_operator_order_issue` and `add_token_flow`. This raises
   `UnboundLocalError` at runtime and aborts analysis on every contract
   that uses `safeTransfer` (e.g., `web3bugs_45_H_01`). The patch
   simply replaces `amount` with `value` so the existing stack value is
   passed through.

   This is a NumScout source bug, **not** a behavior change introduced
   for the experiments. Without the patch, several detectable Web3Bugs
   cases produce no output rather than the expected defect signal.

## Web3Bugs cases that need `workdir_numscout_patched/`

Two Web3Bugs cases use external libraries with `public`/`external`
visibility, which compile to bytecode with linker placeholders
(`__$...$__`) that NumScout's symbolic-execution backend cannot resolve.
For those cases we hand-edited the contracts to **inline** the library
functions (changing `public`/`external` → `internal`), preserving
semantics:

- `evaluation/RQ3/workdir_numscout_patched/run_Swap/Swap_patched.sol`
  (Web3Bugs 51, SwapUtils + MathUtils inlined)
- `evaluation/RQ3/workdir_numscout_patched/run_Exchange/Exchange_patched.sol`
  (Web3Bugs 77, MathLib inlined)

These are committed under `evaluation/RQ3/workdir_numscout_patched/`
(specifically excluded from the workdir-* gitignore rule) and
`run_numscout.py` automatically picks them up. The semantic-equivalence
argument and the patches themselves are documented in the paper's
"Threats to Validity" and "Experimental Setup" sections.

## Setup

```bash
bash evaluation/RQ3/setup_rq3_tools.sh numscout
```

Result:

```
evaluation/RQ3/tools/numscout/
├── tool.py
├── feature_detector/
├── cfg_builder/
├── inputter/
├── requirements.txt
├── venv/
└── ...
```

## Running

```bash
python evaluation/RQ3/run_numscout.py --case web3bugs_45_H_01 --run run1
python evaluation/RQ3/run_numscout.py --annotated-only --run run1
```

`run_numscout.py` automatically:

- Looks up the per-case `solc` version, copies the matching binary into
  `tools/numscout/venv/Scripts/solc.exe` (Windows) or `bin/solc` (Unix),
  and falls back to `solc-select use <ver>` when `solc-select` is on
  PATH.
- For Web3Bugs cases, runs `npx hardhat flatten` (or `npx sol-merger`
  for projects with circular imports) before invoking NumScout.
- For NumScout's bundled benchmark contracts, uses the pre-flattened
  `Dataset/Numscout/contraction/...` files under the repo.
- Retries with tighter limits (`-ll 2 -dl 100`) when path explosion
  causes the default run to time out.

Outputs land in `evaluation/RQ3/outputs/numscout/<run>/`.
