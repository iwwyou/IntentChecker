# web3bugs_29_H_11 — Agent B (Reviewer) Review

Reviewing: `First Revision/phase_reviews/21_web3bugs_29_H_11/analysis.md` (Agent A's R1-1→R1-7 pass on `ConstantProductPool.burnSingle`, contest 29, finding H-11).

**Verdict: Approved, no corrections required.** Every claim flagged by the task brief as needing independent re-verification checked out exactly as Agent A stated.

---

## 1. Sign-flip arithmetic (the load-bearing claim) — independently re-derived, CONFIRMED

Re-derived both branches from scratch from `_getAmountOut`'s own formula (read directly from source, `web3bugs_29_H_11.sol` L330–336: `amountInWithFee = amountIn * MAX_FEE_MINUS_SWAP_FEE; amountOut = (amountInWithFee * reserveAmountOut) / (reserveAmountIn * MAX_FEE + amountInWithFee)`), with `swapFee=30` → `MAX_FEE=10000`, `MAX_FEE_MINUS_SWAP_FEE=9970`, `_reserve0=_reserve1=1000`, `balance0=1000`, `balance1=1100`, `totalSupply=1000`, `liquidity=100`.

`amount0 = 100`, `amount1 = 110` (both confirmed).

**Branch A** (`tokenOut==token1`): buggy `_getAmountOut(100,900,890)` → `887,330,000/9,997,000 = 88` (floor) → `amount1=198`. Intended `_getAmountOut(100,900,990)` → `987,030,000/9,997,000 = 98` (floor) → `amount1=208`. **Buggy 198 < intended 208.** Matches.

**Branch B** (`tokenOut==token0`): buggy `_getAmountOut(110,890,900)` → `987,030,000/9,996,700 = 98` (floor) → `amount0=198`. Intended `_getAmountOut(110,990,900)` → `987,030,000/10,996,700 = 89` (floor) → `amount0=189`. **Buggy 198 > intended 189.** Matches.

Every intermediate product/quotient was recomputed independently (not just re-stated) and all floor-division boundaries were checked (e.g. Branch B intended: `10,996,700×89=978,706,300`, remainder `8,323,700 < 10,996,700`, confirming floor=89, not 90). **Sign flip confirmed exactly as claimed** — the same underlying pool drift produces buggy<intended on one branch and buggy>intended on the mirror branch, because the drifted token (`balance1`, +100 over reserve) sits on the swap's `reserveOut` side in Branch A (monotonically increasing in `reserveOut`) but on the `reserveIn` side in Branch B (monotonically decreasing in `reserveIn`). This is the correct, load-bearing reason no single directional/bound relation can be sound across both branches, and it holds up under from-scratch recomputation.

## 2. Scattered README truncation — read directly, CONFIRMED

Read `Dataset/Web3Bugs/S6_3/contest_29_H_11/README.md` in full: it reproduces the report title, byline, body prose, and the one code excerpt verbatim, then ends immediately after the `HybridPool` footnote with an empty `###` placeholder heading. It is **missing both `#### Impact` and `#### Recommended Mitigation Steps`** entirely. Cross-checked against the primary source `Web3Bugs/reports/29.md` (lines 481–507): both sections are present there — the "returns slightly less swap amounts" impact sentence and the literal recommended fix `_getAmountOut(amount0, balance0 - amount0, balance1 - amount1)`. Confirms the exact §0.5 truncation pattern; Agent A correctly used the primary source throughout and correctly flagged this as load-bearing (the recommended fix anchors R1-2/R1-3's target formula).

## 3. Multi-annotation-set (README §4) legitimacy — own judgment: justified, with Agent A's caveat appropriate

Checked the three README §4 conditions directly against the case: (1) each member independently carries its own full R1-1–R1-7 (confirmed — Branch A and Branch B sections are both fully derived, not one compressed into the other); (2) not a separately-numbered finding — both branches sit inside the one function this H-11 finding names, confirmed by reading the source (L156–193 is one function, `if`/`else` on the same `tokenOut` decode); (3) Intent coverage is judged against the combined negation, and the required check (README §3's negation test) does surface a genuine gap for a Branch-A-only selection — an implementation patching only the excerpted line would silently leave Branch B's identical defect undetected, which I verified by re-reading the source: Branch B's `_reserve1 - amount1` / `_reserve0 - amount0` at L183 is untouched by the report's literal one-line fix suggestion. Agent A's explicit flag that this is "branch-symmetric duplication of one defect pattern," narrower than `70_H_04`'s two-distinct-mechanisms case, is the right call — I'd add nothing to it; it's an honest, not inflated, framing, and the set genuinely closes a real detection gap rather than padding for its own sake.

## 4. `(Before)` qualifier necessity — grammar-verified, CONFIRMED

Read `Parser/Solidity.g4` directly (lines 369–373, 648–653): `ENTRY`/`EXIT` are guarded by the semantic predicate `{not self.inDuring}?`, and `BEFORE`/`AFTER`/`ASSIGN` by `{self.inDuring}?` — i.e. it is a hard, parser-enforced split, not a convention, exactly as Agent A stated. Also read `paper/first_revision/main.tex`'s validation-context table (Table, `\label{tab:validation-context}`, lines 435–462): `@During`'s field supply includes `σ_pt`/`σ_before`/`σ_assign` but not `σ_exit`; `@Post`'s includes `σ_entry`/`σ_exit` but not `σ_before`/`σ_assign`. Confirms Agent A's claim that `@Post`'s Entry/Exit pairing has no way to express a same-statement old/new self-reference for a value (`amount0`/`amount1`) that is declared mid-function (L167/168) and therefore has no meaningful `σ_entry`. Also spot-checked the cited `web3bugs_35_H_11` precedent JSON (`evaluation/RQ1/cases/web3bugs_35_H_11/web3bugs_35_H_11.json`) — it does contain the exact cited annotation `ticks[nextTickToCross].feeGrowthOutside1 == feeGrowthGlobal - ticks[nextTickToCross].feeGrowthOutside1(Before)`, confirming the precedent citation is accurate, not fabricated.

One additional check I ran that Agent A's writeup doesn't spell out but which the record depends on being correct: the unqualified LHS convention. Confirmed against `main.tex` line 522 ("an unqualified varRef... reads ref(Γ)") and the field-supply table (`@During` includes `σ_pt`, the state *at the annotated program point* — i.e., after the statement, since the annotation is placed immediately following it): an unqualified reference under `@During` correctly resolves to the post-statement value, matching Agent A's claim that the bare LHS `amount1`/`amount0` needs no explicit `(After)`. I also independently re-verified each `(Before)` placement is used only for the self-modified variable in each branch (`amount1(Before)` in A, `amount0(Before)` in B) and left correctly unqualified where a variable is read but not reassigned by that statement (`amount0` in A, `amount1` in B) — this matches Solidity's own `+=` desugaring (RHS evaluated against the pre-assignment value) and I found no qualifier misplacement in either annotation member.

## 5. RQ2-A exclusion of `_getReserves()`/`_reserve0`/`_reserve1` — sound

Re-applied README §6's Step-1 operational test directly: would changing `_getReserves()`'s specific return values change the *selected* relations' derivation or validity? No — neither relation (A) nor (B) references `_reserve0`/`_reserve1` anywhere in its RHS; both are stated entirely in terms of `balance0`/`balance1`/`amount0`/`amount1`/the two fee constants. The engine evaluates `amount1(Before)` from the actual runtime state, independent of what formula the (buggy) statement itself used — so `_reserve0`/`_reserve1`'s values have no bearing on whether the corrected relation holds. Confirmed this is a legitimate application of the "alternative-rejection inspection doesn't count" corollary (§6): `_getReserves()` was essential to *explaining why the buggy formula is wrong* (R1-3), not to *validating the selected relation's own truth*. No soundness issue found in this exclusion, or in the parallel exclusion of `_mintFee`/`_balance()`'s internals (both correctly treated as opaque value-producers per the `web3bugs_3_H_04`/`59_H_04` precedent already established in this project).

---

## Checklist (§9)

1. **Discrimination check**: explicit arithmetic re-derived from scratch (§1 above), matches Agent A's stated numbers exactly on both branches.
2. **Relation-strength appropriateness**: confirmed equality is necessary, not habit — the sign-flip makes any inequality/bound unsound on the mirror-branch scenario, verified independently.
3. **During/Post and relation-form justification**: confirmed against the grammar/paper's own field-supply semantics, not merely asserted.
4. **Expressibility correctness**: all referenced identifiers (`amount0`, `amount1`, `balance0`, `balance1`, `MAX_FEE`, `MAX_FEE_MINUS_SWAP_FEE`) verified in-scope by direct source read (L157–168); no smuggled call — `_getAmountOut`'s formula is exactly and fully inlined (verified term-by-term in §1 above, no discrepancy).
5. **Self-substitution contamination**: none found — the target relations are derived from `_getAmountOut`'s independent definition, not from algebraic manipulation of the buggy statement itself.
6. **RQ2-A scope sanity**: 7 relevant statements / 11 unique values is neither over- nor under-inclusive on independent review; the `_getReserves()` exclusion is correctly justified (§5 above), and no additional relevant statement was found missing on a fresh read of L156–193.

## Delta-exception and source line numbers — additionally spot-checked

Direct `grep` against the source file confirms every cited line number (157/158/159/167/168/175/183) matches Agent A's citations exactly, and confirms `burnSingle` (L156–193) contains no `for`/`while` loop — the delta exception genuinely does not apply, as claimed.

## Summary

No arithmetic errors, no citation errors, no grammar misreadings, no soundness gaps found. The sign-flip claim — the single most load-bearing fact in this case's rejection of every inequality/bound alternative — is correct under independent from-scratch recomputation. The truncation finding is verified by direct reading of both files. The multi-annotation-set framing is justified under README §4's own criteria and Agent A's "branch-symmetric duplication" caveat is the right level of honesty about it. The `(Before)` qualifier's necessity is grammar-confirmed, not merely asserted, including the finer point of exactly which operand in each branch needs the qualifier. The RQ2-A exclusion of `_getReserves()`/reserve locals is a correct application of the alternative-rejection corollary.

**Agreement: Full agreement with Agent A's Expressible=Yes (both members), Intent coverage=Full, Usable, Value-level verdicts, and RQ2-A profile.** No edits made to `analysis.md`.
