# Case Production Pipeline — Automation Plan (direction only, not started)

Status: **direction agreed, not yet implemented**. Revisit when the user starts building real cases (i.e., after RQ2-A specification-profile review is done and the RQ1/RQ2 case-analysis methodology in `README.md` is being scaled to the remaining cases). Nothing described here has been built.

## Context

Reconstructed from `PROCESS_GUIDE.md`/`PROCESS_GUIDE_v2.md` + backed-up scripts (`temp/copy_target_contracts.py`, `preprocess_contraction.py`, `rename_reserved_identifiers.py`, `collect_dependencies.py`, `generate_case_jsons.py`, and the live `Dependencies/main.py`) how the original 20-case pipeline actually worked, and where the manual bottlenecks were. Full discussion in the conversation this plan was drafted from; this file records only the agreed direction.

## Per-stage automation plan

| Stage | Current state | Planned change |
|---|---|---|
| 0. Fetch original `.sol` | `copy_target_contracts.py`, fully automatic (dataset.csv-driven) | Keep as-is |
| 1. Contraction (trim to bug-relevant function + its deps within the same contract) | Fully manual | Claude drafts the trimmed contraction from source + report; user approves via diff |
| 2. Strip imports/comments/constructor/SPDX | `preprocess_contraction.py`, automatic | Keep as-is |
| 3. Reserved-word identifier rename | `rename_reserved_identifiers.py`, automatic | Keep as-is |
| 4. `.sol` → JSON code records | `slice_solidity()`, automatic | Keep as-is |
| 5. Dependency identification/fetch/trim | Fully manual (no script found for this) | Claude recursively resolves imports, reuses existing files under `Dependencies/{interfaces,libraries,contracts}/` where possible, drafts trimmed stubs for new ones (same style as `SafeMath.sol`'s hand-trimmed stub); user spot-checks only the new files |
| 6. Dependency build order (parent-before-child) | Manual hardcoded list (`_con_order` in `Dependencies/main.py`, explicitly commented as "not worth automating" at ~20-file scale) | Replace with a topological sort over parsed `contract X is A, B` / `using L for T` declarations — no judgment call involved, pure graph algorithm, worth it now that the case count is growing |
| 7. pkl pre-analysis | `Dependencies/main.py`, automatic | Keep as-is, feed it the auto-computed order from stage 6 |
| 8. Intent/debug annotation values | Manual, decided from scratch per case | Derive mechanically from the case's own `analysis.md` — R1-1's reconstructed discrimination scenario already pins concrete numeric values for every relevant variable, and R1-6 already pins the exact target annotation text + attachment line. This is not new work, just structured extraction of what R1-1–R1-7 already produced. |
| 9. Case JSON assembly | Manual, hardcoded per-case in `generate_case_jsons.py`-style scripts | Script that reads the structured extraction from stage 8 and assembles code + intent + `@Debugging BEGIN/END` + debug records in the required order (mirrors what `generate_case_jsons.py` did, minus the hand-typed per-case Python) |
| 10. Run + check VIOLATED/WARNING/ERROR | `run_all.py`, automatic | Keep as-is, but **actually running the engine is RQ1-B/RQ2-B territory, which is explicitly deferred this pass** — this stage stays prepared-but-not-executed until the user says to proceed with engine execution |

## Where the user stays in the loop

1. **Approve the contraction draft** (diff review, not writing from scratch).
2. **Spot-check any newly-fetched/trimmed dependency file** (files already present in `Dependencies/` are reused with zero review).
3. **Review final execution results** (VIOLATED/WARNING/ERROR triage is a human call).

Everything else (fetching, ordering, preprocessing, JSON assembly) is meant to be mechanical.

## Open question, not yet decided

Whether to build the dependency-import-resolver + topo-sort script first (lowest risk, pure automation, no judgment involved) before tackling the contraction-drafting or case-JSON-assembly automation. Proposed as the starting point but not agreed yet — revisit when work actually starts.
