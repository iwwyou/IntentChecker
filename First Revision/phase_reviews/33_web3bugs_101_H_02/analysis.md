# web3bugs_101_H_02

## Final disposition

**Excluded — source already fixed (`excluded_fixed_code`).**

H-02 (`Web3Bugs/reports/101.md` lines 175-209, GitHub `code-423n4/2022-03-sublime-findings#21`) reports that `LenderPool.terminate()` computes a principal-withdrawal component in `borrowAsset`-denominated units and then passes it to `SAVINGS_ACCOUNT.withdrawShares(...)` as if it were a shares amount. The exact vulnerable expression and its localized fix are preserved in a duplicate finding, issue `#55` (`code-423n4/2022-03-sublime-findings#55`, marked as a duplicate of `#21`): the vulnerable line multiplies the *unconverted* `_notBorrowed` by the `totalSupply[_id]/_borrowedTokens` ratio, and the fix is to multiply the *already-shares-converted* `_notBorrowedInShares` instead. This benchmark's source (`evaluation/RQ1/target_contracts_original/web3bugs_101_H_02.sol`, L389) already performs exactly this shares-based computation:
```solidity
uint256 _actualNotBorrowedInShares = _notBorrowedInShares.mul(totalSupply[_id]).div(_borrowedTokens);
```
The reported H-02 defect is therefore not present in this benchmark's source, and this case is excluded from RQ1 rather than assigned an Expressibility outcome.

## Why it was not excluded previously

Exclusion screening is not new to this revision — the original evaluation already performed it, before the L1-L5 classification stage (README §1: 89 collected → 14 excluded → 75 eligible). This case passed that screening and was subsequently labeled `L5b` under the retired taxonomy. It was not caught at screening time because the evidence available then was limited to the compiled Web3Bugs report (`Web3Bugs/reports/101.md`), which reproduces only the primary finding `#21`'s own abbreviated snippet — a standard feature of compiled contest reports, which consolidate duplicate findings into one representative write-up rather than reproducing each duplicate's own text. That snippet does not show the `_notBorrowedInShares` conversion at all, so nothing in the locally-available report exposed the fact that this benchmark's source already implements the shares-based fix. The benchmark source was accordingly treated, at screening time, as still containing the reported defect.

## New evidence recovered during revision

During revision, provenance checking was extended past the compiled Web3Bugs report to the underlying Code4rena finding repository (`github.com/code-423n4/2022-03-sublime-findings`), where duplicate issue `#55` was found. Independently confirmed by direct fetch of both issues (not just the pasted content that prompted the check):
- **`#21`** (primary, sponsor-confirmed High): same abbreviated snippet as the local report; recommends replacing the entire computation with a bare `_sharesHeld`.
- **`#55`** (duplicate of `#21`): shows the fuller vulnerable expression, including the `_notBorrowedInShares = getSharesForTokens(...)` line the `#21`/report snippet omits, and gives a narrower, localized fix — swap `_notBorrowed` for `_notBorrowedInShares` in the ratio-scaling multiplication, leaving the rest of the computation unchanged.

`#55` does not compete with `#21` as an alternative or more-authoritative account of the bug — both target the same root cause (a borrowAsset-denominated value used where a shares-denominated one is required); `#55` simply preserves more of the original vulnerable code's context and states the fix at a finer grain. Read together, they establish precisely which single substitution (`_notBorrowed` → `_notBorrowedInShares`, in the ratio-scaling term only) constitutes the reported fix — and this benchmark's source already has it.

## Effect on evaluation

This is not a reclassification of the historical `L5b` label into an Expressibility outcome (Yes or No) — the case never reaches that stage. The exclusion criterion itself (`excluded_fixed_code`, already established and used elsewhere in this dataset — see `web3bugs_43_H_02`, `web3bugs_66_H_02` in `evaluation/RQ1/annotation_plans.md`) is unchanged; what changed is the evidence available to apply it, via expanded provenance checking. Accordingly: **do not fold this case into any table showing former-`L5` cases' Yes/No Expressibility outcomes** — track it separately as removed from the eligible pool during revised eligibility validation. This reduces the eligible-case denominator (75 → 74; the former-L5 pool 14 → 13) by one.

One line for a reviewer skimming for the net effect: *this case was not excluded because a new eligibility rule was introduced; it was excluded because revision-time provenance checking recovered upstream evidence that changed the outcome of an exclusion screening step that already existed in the original evaluation.*

---

## Investigation record (condensed; full derivations available in prior git history of this file)

This case went through four passes this session before reaching the disposition above. Recorded here for transparency (README §0/§7), not as competing live content.

1. **Fresh R1-1–R1-7 pass** (methodology retired the old `L5b`/bug-awareness reasoning, redid the case from scratch): reconstructed the reported defect as "the shares-withdrawal argument should equal `_sharesHeld`, not the ratio-scaled `_totalBorrowAsset`," selected `@During _totalBorrowAsset == _sharesHeld` as the target relation, and reached **Expressible = Yes** (Value-level, Usable; RQ2-A: 7 relevant statements, 10 unique values, 1 additional protocol-specific contract dependency, Context breadth 3, External spec required: No). The discrimination scenario required `totalSupply[_id] < _borrowedTokens`, reachable via a prior partial lender withdrawal post-`LIQUIDATED`/`CLOSED`.
2. **First review pass**: confirmed the derivation; added a clarification that "Satisfied" for the intended code in the discriminating scenario is a pre-call value comparison, since the report's own caveat says the recommended fix may itself revert there.
3. **Second review pass** ("source already patched?" hypothesis, prompted by a report-snippet/source mismatch): investigated and refuted at the time — traced `_withdrawLiquidity()`'s accounting and found the current code's ratio-scaling is only exact when the strategy exchange rate hasn't moved since an earlier partial withdrawal; once yield accrues in between, it **over-withdraws** (concrete trace: 541.32 shares computed vs. 500 genuinely held). This is a real, distinct, time/yield-dependent defect, independently useful to have on record, but is not itself a reported H-01/H-02 mechanism and was correctly not folded into this case's target relation.
4. **Third review pass** (structural objection: does the target relation actually satisfy R1-3's "supported by the reported intended behavior" condition?): found that the function's reachable state space splits into Region A (`totalSupply[_id] == _borrowedTokens`, where `_totalBorrowAsset == _sharesHeld` already holds on the *current* code — no discrimination possible) and Region B (the only region with discriminating power, and exactly the region the report's own caveat disclaims `_sharesHeld` in). A candidate rescue scenario (pre-start under-subscription) was checked and found to be dead code (`sharesHeld` is provably always `0`, hence the disputed branch never executes, whenever `totalSupply[_id] < _borrowedTokens` pre-accept). Concluded no report-supported, discriminating relation exists using `_sharesHeld` — disposition at the time: retract `Expressible: Yes`, record as "R1-1/R1-3 non-establishment," pending an aggregation decision (keep in pool vs. new exclusion reason).
5. **This pass**: recovered issue `#55` (see above), which resolves the open aggregation question directly — the reported H-02 mechanism (as most precisely stated by `#55`) is simply absent from this source, independent of and prior to the Region A/B analysis in pass 4. Final disposition: `excluded_fixed_code`.

Passes 3's Region A/B analysis and pass 2's yield-dependent over-withdrawal finding remain accurate observations about `terminate()`'s current behavior; neither is used as the basis for this exclusion, and neither should be read as claiming a residual, reportable defect exists — that question is out of scope once the case is excluded on H-02-specific grounds.
