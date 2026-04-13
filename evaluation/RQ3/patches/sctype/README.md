# ScType setup notes (RQ3 reproducibility)

ScType is one of the four tools compared in RQ3. It is a Slither
detector plugin (`slither --detect tcheck`).
`evaluation/RQ3/setup_rq3_tools.sh` clones it into
`evaluation/RQ3/tools/sctype/` (gitignored) at a pinned commit and
installs it as an editable package inside a dedicated venv.

## Upstream version

| Field | Value |
| ---: | :--- |
| Upstream | https://github.com/NioTheFirst/ScType |
| Pinned commit | `24deb8c1` (matches the version used for the paper) |
| Python | 3.10+ |

## Local modifications captured by `local_mods.patch`

1. **`setup.py` — pin `crytic-compile` to the released PyPI version.**
   Upstream `setup.py` installs crytic-compile from the
   `crytic/crytic-compile@dev` git branch. That branch has changed in
   ways that no longer build cleanly against the rest of ScType's
   pinned dependencies, so the patch flips the line back to
   `crytic-compile>=0.3.1,<0.4.0` (released wheel). No detector logic
   is touched.

## Type-annotation files (`evaluation/RQ3/sctype_typefiles/`)

ScType requires per-contract type-annotation files (`*_types.txt` and
`*_ftypes.txt`). The annotations for the seven Web3Bugs cases that
overlap between ScType's benchmark and our evaluation are committed
under `evaluation/RQ3/sctype_typefiles/`, mirroring the directory
layout ScType expects:

```
sctype_typefiles/
├── Badger_Dao_p2/...
├── Perennial/...
├── PoolTogether/...
├── Sublime_p2/...
├── Vader_Protocol_p1/...
├── Vader_Protocol_p3/...
└── yAxis_p2/...
```

`run_sctype.py` copies the right files into each Web3Bugs project's
`hardhat_root` before invoking slither, then cleans them up
afterwards.

## Setup

```bash
bash evaluation/RQ3/setup_rq3_tools.sh sctype
```

Result:

```
evaluation/RQ3/tools/sctype/
├── slither/                # ScType's modified slither tree
├── financial_type_keys.py
├── setup.py                # patched to use PyPI crytic-compile
├── pyproject.toml
└── venv/                   # editable install: pip install -e .
```

## Running

```bash
python evaluation/RQ3/run_sctype.py --case web3bugs_5_H_07 --run run1
python evaluation/RQ3/run_sctype.py --all --run run1
```

`run_sctype.py` will:

1. Look up each case's hardhat project root under
   `evaluation/RQ3/web3bugs/contracts/<case>/...`
2. `npx hardhat compile` if `artifacts/build-info/` is missing
3. `solc-select use <version>` (and copy the binary into the ScType
   venv as a backup)
4. Copy the type files from `sctype_typefiles/` into the hardhat root
5. Invoke `slither --detect tcheck --compile-force-framework hardhat .`
6. Parse the output and clean up the staged type files

Requirements on the host beyond what `setup_rq3_tools.sh` installs:

- `solc-select` with the appropriate Solidity versions
  (`0.6.12 0.7.6 0.8.3 0.8.9 0.8.10`)
- `node` + `npm`/`yarn` for hardhat compilation (per-project — see
  `bash evaluation/RQ3/setup_dependencies.sh`)
- The Web3Bugs clone (`bash evaluation/RQ3/setup_rq3_tools.sh web3bugs`)

Outputs land in `evaluation/RQ3/outputs/sctype/<run>/`.
