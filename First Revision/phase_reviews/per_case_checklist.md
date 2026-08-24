# Per-Case Checklist (analysis + review + build, combined)

For each of the 35 remaining cases (21 former L1-L3 + 14 former L5, `16_H_04` included). Steps run in this order per case — contraction/dependency/JSON build now happens the same day as analysis/review, not as a separate later pass. Paced at ~7 cases/day.

Engine execution (RQ1-B — actually running the case and getting Violated/Warning/Error) is **not** included below; it's still deferred per standing instruction. This checklist takes a case up through a ready-to-run case JSON.

## 1. Prepare the packet
- Source: `evaluation/RQ1/target_contracts_original/<case_id>.sol` (verbatim, read-only reference for R1-1 — never edit).
- Report: `C:\Users\isjeon\Web3Bugs\reports\<contest_number>.md` — **authoritative source per README §0.5**. Do not default to `Dataset/Web3Bugs/.../README.md` (confirmed unreliable/truncated for at least 2 of the first 3 pilot cases).
- Patch/recommendation section if present (permitted to read per README §2 — evidence only, never mechanically transcribed).

## 2. R1-1 → R1-7 (README §4)
- R1-1 Reported Behavior Reconstruction (bug-relevant intended numeric behavior, in prose).
- R1-2 Intent Abstraction (value-centered vs. effect/state-transition-centered).
- R1-3 Select least implementation-specific sufficient relation — **alternatives table required** (§7): what was tried, why each alternative lost.
- R1-4 During vs Post (driven by the relation's nature, not patch shape).
- R1-5 Relation form classification.
- R1-6 Construct target annotation (attachment point; document any concrete-constant derivation; flag quantification-over-collection if applicable).
- R1-7 Expressibility decision: Yes/No. If No → alpha/beta/gamma tag(s).

## 3. RQ2-A specification profile (only if Expressible = Yes)
- Relevant statements — scoped to the annotated function only; a called function (same-contract or cross-contract) is counted once under "Additional functions required," never expanded into its own internal lines.
- Unique relevant program values — same function-local scoping; include the constrained target value itself.
- Additional functions required — **each entry needs a one-line semantic-dependency note** ("required because its behavior establishes ...").
- Additional protocol/application-specific contracts/libraries required.
- Context breadth (0-4).
- External specification required (Yes/No) — audit-report use never counts here.
- Quantified property instantiated (Yes/No) transparency flag.

## 4. Write `phase_reviews/<case_id>/analysis.md`
Full R1-1–R1-7 trace + RQ2-A profile + Summary block, matching the format already used in the 3 pilot cases.

## 5. Review pass (README §9 checklist)
- Discrimination check — re-derive the concrete scenario's arithmetic independently, don't take a self-reported "yes it discriminates" at face value.
- Relation-strength appropriateness (equality reached out of habit? weakened too far?).
- During/Post + relation-form justification.
- Expressibility correctness — values genuinely in scope, no smuggled function calls.
- Self-substitution contamination check.
- RQ2-A scope sanity (over/under-inclusive backward slice).

## 6. Write `phase_reviews/<case_id>/review.md`
Corrections tied to specific R1-phases; reconcile into `analysis.md` (or an addendum, per the established pattern in the 3 pilot cases).

## 7. Structural check
`python check_case_completeness.py <case_id>` — fix any MISSING/STALE flags before moving on.

## 8. Draft the contraction
`evaluation/RQ1/target_contracts_contraction/<case_id>.sol` — trim to the bug-relevant function(s) identified in R1-1, plus whatever same-contract context they call. Keep verbatim (no fabricated edits).

## 9. Preprocess
Run `preprocess_contraction.py` (fixed version — see `First Revision/engine_code_changes.md`) on the contraction; run `rename_reserved_identifiers.py` if any reserved-word identifiers appear.

## 10. Dependencies
Check `Dependencies/{interfaces,libraries,contracts}/` first — reuse anything already there. For anything new: check `evaluation/RQ1/target_contracts_original/dependencies/` (the raw cache found this session) before fetching externally. Trim only if genuinely unused by this contract's own code (keep full function sets for shared libraries, per the `SafeMath.sol` convention) — don't drop functions just because *this* case doesn't call them. Run through `Dependencies/main.py` to pkl once added.

## 11. Assemble the case JSON
Extract intent annotation (from R1-6) and debug annotation values (from R1-1's concrete discrimination scenario — the numbers are already worked out there) into `evaluation/RQ1/cases/<case_id>/<case_id>.json`, following the record order (code → intent → `@Debugging BEGIN` → debug → `@Debugging END`) and startLine-uniqueness rules documented in `PROCESS_GUIDE.md`/`PROCESS_GUIDE_v2.md`.

---

Not included: actually running the case through the engine (RQ1-B) — still deferred. Also not included: the 20 already-deferred former-L4 cases (separate, lighter-lift triage per README §1) and RQ2-B (runtime measurement).
