# web3bugs_29_H_08 — Agent A (Analyst) Case Analysis

Methodology: `First Revision/phase_reviews/README.md` (current, non-superseded version).

## Case metadata

- **Case ID**: `web3bugs_29_H_08`
- **Contract**: `HybridPool` (Sushi Trident, contest 29 — "Trident exchange pool template with hybrid like-kind [StableSwap] formula")
- **Function**: `_getReserves()` (`internal view returns (uint256 _reserve0, uint256 _reserve1)`)
- **Source read**: `evaluation/RQ1/target_contracts_original/web3bugs_29_H_08.sol` (verbatim; `_getReserves` at lines 253-257, `_updateReserves` at 259-265, `_balance` at 267-270, `_toAmount` at 279-284, `reserve0`/`reserve1` state declarations at lines 47-48)
- **Audit report**: `C:\Users\isjeon\Web3Bugs\reports\29.md`, finding `[H-08] HybridPool's reserve is converted to "amount" twice` (lines 383-404 of that file). **Cross-checked against README §0.5's caution**: the scattered `Dataset/Web3Bugs/S6_4/contest_29_H_08/README.md` was compared against the primary source — **it is truncated**, exactly the pattern README §0.5 warns about: it contains only the finding title and the first two sentences of the bug description, then cuts off after a bare `###` heading with none of the Impact / POC / Recommended Mitigation Steps sections that the primary report contains. The primary `Web3Bugs/reports/29.md` is used as the sole source of record for R1-1 below; the scattered file is not relied on for anything beyond the two sentences it does contain (which match the primary source verbatim).
- **Existing prior-pipeline label** (historical, retired methodology, recorded for continuity only): `L3 unsupported-construct-top`. Per the task brief, this is **not** assumed to predict the R1-7 outcome here, and indeed it does not: as shown below, the selected target relation needs no special grammar feature at all (no snapshot-qualifier extension, no exponentiation, no call-rescue) — it is an ordinary two-variable equality comparison (`RelationalCmp`) between two already-in-scope locals. A plausible explanation for the old "unsupported construct" label, not verified further here since it is out of scope for R1-7 (README §4: don't speculate about why an old pipeline concluded what it did) — `_getReserves()`'s multi-value named-return signature (`returns (uint256 _reserve0, uint256 _reserve1)`) and/or the pervasive `staticcall`-based external-call pattern used throughout this file (`_toAmount`, `__balance`, `_toShare`) may have looked unsupported to a naive blind classifier, even though neither ends up mattering to the actual selected relation.
- **Note**: `web3bugs_29_H_11` (a separate finding in the same contest) is being analyzed independently by another agent in parallel; this case is fully independent of it and makes no assumptions about it.

---

## R1-1 — Reported Behavior Reconstruction

**Contract/function role.** `HybridPool` is a Trident (Sushi) AMM pool implementing a Curve/StableSwap-style invariant between two tokens, built on top of BentoBox, which custodies the underlying ERC-20 tokens and tracks balances internally as rebasing-safe "shares" rather than raw token amounts — `IBentoBoxMinimal.toAmount`/`toShare` are the conversion primitives between the two units. `_getReserves()` is the pool's single canonical read of its two token reserves, in underlying-token **amount** units (not BentoBox shares) — every liquidity/swap function in the contract (`mint`, `burnSingle`, `swap`, `getAmountOut`, the public `getReserves()`) calls it to obtain the reserve values the StableSwap math (`_computeLiquidity`, `_getAmountOut`, `_getY`) actually operates on.

**Note on a stale/contradicted contract-level comment.** The contract's own top-of-file `@dev` comment (line 13) states *"The reserves are stored as bento shares. However, the stableswap invariant is applied to the underlying amounts."* This is contradicted by the actual write path (below) and by the audit's own diagnosis (sponsor-confirmed) — reserves are in fact stored as amounts, not shares. This comment is treated as stale/inaccurate documentation, not as evidence; the analysis below relies on the actual code in `_balance()`/`_updateReserves()` and the audit's own diagnosis, consistent with README §2's discipline (patch/report access is permitted and is the ground truth; a contradicted in-source comment is not).

**Relevant state/locals** (only the ones the bug touches):
- `reserve0`, `reserve1` (state, `uint128`, lines 47-48) — the pool's persisted reserve values. **Written only by `_updateReserves()`** (lines 259-265): `(uint256 _reserve0, uint256 _reserve1) = _balance();` then `reserve0 = uint128(_reserve0); reserve1 = uint128(_reserve1);`. `_balance()` (lines 267-270) computes `balance0 = _toAmount(token0, __balance(token0))` — i.e., it takes the BentoBox **share** balance (`__balance`, a `staticcall` to `bento.balanceOf`) and converts it to an **amount** via `_toAmount` (another `staticcall`, to `bento.toAmount`) before it is ever stored. **So `reserve0`/`reserve1` are, by construction of the only function that writes them, always already in "amount" units at rest** — this is the fact the whole finding turns on.
- `_reserve0`, `_reserve1` (named return locals of `_getReserves()`, lines 253-257) — the disputed value.

**The disputed statement (`_getReserves()`, lines 253-257):**
```solidity
function _getReserves() internal view returns (uint256 _reserve0, uint256 _reserve1) {
    (_reserve0, _reserve1) = (reserve0, reserve1);
    _reserve0 = _toAmount(token0, _reserve0);
    _reserve1 = _toAmount(token1, _reserve1);
}
```
Line 254 copies the already-amount-scaled state directly into the return locals — this alone would be correct. Lines 255-256 then apply `_toAmount()` a **second** time to each, as if the just-copied value were still a raw BentoBox share count. Since `_toAmount()` is (by BentoBox's own accounting) generically a non-identity linear rescaling by the current share-price ratio, applying it twice effectively squares that ratio's effect on the returned reserve.

**Variable-value intent (the return values, lines 255-256).** `_reserve0`/`_reserve1` at function exit should equal exactly what `reserve0`/`reserve1` already hold — no further transformation is needed or correct, because that transformation (share→amount) was already performed once, at write time, inside `_updateReserves()`/`_balance()`.

**Statement/line-level intent.** `_getReserves()` is supposed to uphold: "this function's return values are read-only, unmodified reflections of the persisted `reserve0`/`reserve1` state" — a pure passthrough, not a second conversion pass.

**Reported erroneous behavior** (H-08, verbatim, `Web3Bugs/reports/29.md` lines 386-387):
> "The `HybridPool`'s reserves are stored as Bento "amounts" (not Bento shares) in `_updateReserves` because `_balance()` converts the current share balance to amount balances. However, when retrieving the `reserve0/1` storage fields in `_getReserves`, they are converted to amounts a second time."

**Impact** (verbatim, lines 389-391):
> "The `HybridPool` returns wrong reserves which affects all minting/burning and swap functions. They all return wrong results making the pool eventually economically exploitable or leading to users receiving less tokens than they should."

**PoC** (verbatim, lines 393-399):
> "Imagine the current Bento amount / share price being `1.5`. The pool's Bento *share* balance being `1000`. `_updateReserves` will store a reserve of `1.5 * 1000 = 1500`. When anyone trades using the `swap` function, `_getReserves()` is called and multiplies it by `1.5` again, leading to using a reserve of 2250 instead of 1500. A higher reserve for the output token leads to receiving more tokens as the swap output. Thus the pool lost tokens and the LPs suffer this loss."

**Recommended Mitigation Steps** (verbatim, line 402): *"Make sure that the reserves are in the correct amounts."* — no code diff/patch is given at all (unlike most cases in this dataset; matches the situation in `70_H_05`, which also had no literal patch to guard against transcribing).

**Sponsor status**: confirmed (`maxsam4 (Sushi) confirmed`, line 404).

**Expected/intended behavior.** `_getReserves()`'s returned `_reserve0`/`_reserve1` must equal the persisted `reserve0`/`reserve1` state exactly — the two extra conversion lines (255-256) should not be applied at all.

**Bug-relevant intended numeric behavior**: `_reserve0 == reserve0` and `_reserve1 == reserve1` at `_getReserves()`'s exit, unconditionally (this is not a scenario-conditioned claim — see R1-6/R1-7).

---

## R1-2 — Intent Abstraction

Distinguishing property (no patch syntax exists to drop — the report gives only qualitative guidance, "make sure the reserves are in the correct amounts," not a diff): the function's two named return values must equal the corresponding persisted state values exactly, with no additional transformation applied at read time.

**Intent-level orientation: value-centered** — a constraint on the return values (`_reserve0`, `_reserve1`), not a state-transition claim (`_getReserves()` is `view`, mutates nothing).

---

## R1-3 — Select the least implementation-specific sufficient relation

**Preliminary check — does the natural statement of intent need a function call inside `intentValue`?** One could imagine trying to state the intent in terms of the underlying BentoBox mechanics directly, e.g. "`_reserve0` should equal the share balance times the current price-per-share, applied exactly once" — which would require calling `__balance`/`_toAmount` (or their BentoBox-side equivalents) inside the relation, an alpha-style blocker (`intentValue` disallows calls). **This is not the relation actually needed here**, and checking for a Nokon-style known-bound rescue is moot: the far more natural and strictly more general statement of intent sidesteps the call entirely — `_getReserves()` should simply return the state unchanged. This was checked, not assumed, per the task's mandatory instruction to try the rescue before declaring an alpha blocker; it turns out not to be needed because a call-free alternative is not just a rescue but the *correct* abstraction.

1. **Directional/inequality bound**: e.g. `_reserve0 <= reserve0` (motivated by the PoC's price ratio of 1.5 > 1, under which the buggy value is always larger than the stored one). **Rejected — not established as generally sound.** Nothing in-scope (within `HybridPool` itself) guarantees BentoBox's share-to-amount ratio is always `>= 1`; `_toAmount`'s specific numeric behavior is external contract state (a `staticcall` to `bento`), and this contract makes no assertion about which direction the price can move. Baking in an un-verified external-protocol direction assumption here would be exactly the kind of protocol-external claim R1-3 cautions against smuggling into a bound. Even where it happened to hold, it would understate the reported intent — the recommendation is "make the reserves correct," an equality claim, not merely "don't inflate."
2. **Exact equality against the persisted state (SELECTED)**: `_reserve0 == reserve0` (and symmetrically `_reserve1 == reserve1`). Fully in-scope (both sides are already-materialized values with no call), matches the PoC's own numbers exactly (see discrimination check below), and is the natural generalization of "make sure the reserves are correct" without transcribing any patch syntax (none was given to transcribe).
3. **Known-bound/call rescue (Nokon-style, README R1-3)**: **not applicable, checked as required.** The selected relation contains no function call at all, so there is no alpha blocker to rescue in the first place — see the preliminary check above for why the call-based framing was considered and abandoned in favor of the state-equality framing.
4. **Snapshot-qualified `varRef(Entry/Exit/...)` extension (README R1-3)**: **not needed.** There is no before/after or entry/exit pairing of the *same* identifier in this relation — `_getReserves()` is `view` and reserve state does not change during the call, so an ordinary, unqualified `@Post` comparison of the two already-settled values suffices. (Unlike, e.g., `42_H_01`/`35_H_11`, there is no third independent quantity being compared against an old snapshot of the same variable — this relation is a plain two-variable equality, not a delta/growth relation at all.)

**Winner: Alternative 2, as a two-member target annotation set — `_reserve0 == reserve0` (member A) and `_reserve1 == reserve1` (member B) — not a single compound `&&` clause.**

**Revision note (methodological, added on review — verdict/relation content unchanged from the original pass, only the packaging).** The original pass wrote this as one `@Post _reserve0 == reserve0 && _reserve1 == reserve1` line. An external critique first (wrongly) claimed the grammar doesn't support `&&` joining two full `commonClause`s on one `@Post`/`@During` line — checked directly against `Parser/Solidity.g4` (`postIntent: '//' '@Post' postClause (logicOp postClause)*`) and the full implementation chain (`EnhancedSolidityVisitor.visitPostIntent` → `ContractAnalyzer.process_post`/`_verify_post_compound` → `Interpreter/Engine.py`'s `_combine_logic_results`) — it **is** genuinely, fully implemented (three-valued AND/OR combination, not a stub), so that specific objection was rejected. Independently of that, per README §4's now-adopted policy (added this session after this exact case prompted the decision): `&&`/`||` composition is deliberately **not used when constructing target annotations for this benchmark**, even though the engine supports it, because formalizing compound-clause combination in the paper's presented semantics is unnecessary overhead when the already-established multi-annotation-set mechanism (README §4, first used for `70_H_04`/`35_H_08`) covers the identical need with simpler semantics (each member independently evaluated; combination only at the R1-3 case-analysis level). This case is a clean fit for that mechanism — see the multi-annotation-set discipline check immediately below.

**Multi-annotation-set discipline check (README §4's three conditions, per the same structure used for `70_H_04`/`35_H_08`):** (1) each member independently passes its own full R1-1–R1-7 — verified below, both members share the identical derivation shape (same function, same statement pattern, one per token) so neither's derivation is shortcut by the other's existing; (2) the report identifies both as part of the *same* finding, not separately numbered ones — the report's own title and PoC describe *one* mechanism ("the reserve is converted to amount twice") applied symmetrically to both `token0`/`token1` inside the same function, the closest possible case to `35_H_08`'s "branch-symmetric duplication" pattern (arguably even cleaner here, since both members are the *same statement shape* applied to two named values in the same straight-line function, not even different branches); (3) `Intent coverage` is judged against the **combined** set's negation — see below.

**Discrimination check (explicit arithmetic, per §9 checklist item 1), both members** — using the report's own PoC numbers directly: share price `1.5`, share balance `1000`.
- `_updateReserves()`/`_balance()`: `balance0 = _toAmount(token0, 1000) = 1.5 * 1000 = 1500` ⟹ `reserve0 = 1500` (state, as stored).
- **Member A, buggy**: line 254 sets `_reserve0 = reserve0 = 1500`; line 255 then re-applies the conversion, `_reserve0 = _toAmount(token0, 1500) = 1.5 * 1500 = 2250`. Check: `2250 == reserve0 (1500)` → **false ⟹ Violated.** Matches the report's own stated buggy result (2250) exactly.
- **Member A, intended** (line 255 not applied — the fix's whole point): `_reserve0` remains `1500` from line 254. Check: `1500 == 1500` → **true ⟹ Satisfied.**
- **Member B**: identical shape and arithmetic for `_reserve1`/`reserve1`/`token1` (line 256), symmetric to member A — same buggy-vs-intended pattern, same discrimination outcome.

**Required R1-3 negation check (§3/R1-3), run against the combined set**: does the set's combined negation fail to catch some alternative implementation that retains the reported defect but produces it differently?
- An implementation that fixes token0's double-conversion (satisfying member A) but leaves token1's untouched: **caught** — member B is independently violated (`_reserve1 != reserve1`), even though member A alone would have accepted this implementation.
- Symmetric case (fixes token1, not token0): **caught** by member A.
- An implementation that fixes *neither*: both members violated — caught twice over.
- An implementation with a different erroneous transformation for either token (not literally the double-`_toAmount()` call, but any other spurious mutation of the return value before exit): each member's own equality (`_reserveN == reserveN`) is violated whenever `_reserveN != reserveN` for **any** reason, so this generalizes beyond the literal double-call mechanism reported, per-member, same as the original single-relation analysis already established.
- The one thing that *would* legitimately fall outside either member's scope is a change to `_updateReserves()`'s own write-time convention (e.g., if reserves were instead stored as raw shares) — but that is a different function's contract, not an alternative shape of *this* reported defect, and the report itself does not dispute `_updateReserves()`'s write path.

**No gap found within the scope of the reported defect, for the combined set.** This upgrades/confirms `Intent coverage: Full` (§10) on the same substantive grounds as the original single-relation pass (which already argued Full for `_reserve0 == reserve0` alone using symmetric reasoning about `_reserve1`) — the two-member packaging makes explicit, via an actual second independently-derived member, what the original pass's negation check argued informally in prose.

---

## R1-4 — During vs Post

**Selected scope: Post, both members.** Each relation concerns one of `_getReserves()`'s two named return values at function exit — both settled, never modified again, by the time the (implicit) return happens; each relation only needs its own final value, exactly what `@Post`'s `σ_exit` supplies. Not chosen merely because the report describes a function-level consequence (R1-4's caution) — chosen because each disputed quantity is, by construction, only meaningful once, at exit, and there is no earlier "during" moment where a distinct intermediate value would need to be checked instead (the function has exactly one code path, no branch, no loop). Both members share the identical scope reasoning (symmetric statement shape, one per token), so this is not derived twice independently in prose — the argument for member A applies verbatim to member B.

**Required explicit delta-exception check (per task brief, performed on this case's own facts, not by analogy to any other case's outcome), both members.** Does either relation's only viable attachment point sit inside a `for`/`while` loop body? **No — `_getReserves()` contains no loop at all.** It is a three-statement function (lines 254-256) with no control-flow structure whatsoever. The confirmed `delta` exception (README §4: a `@During` whose only viable attachment is inside a loop body is never evaluated by `fixpoint()`/`reinterpret_from()`) is categorically inapplicable here — there is no loop anywhere in this function or in either relation's dependency chain (`_updateReserves()`/`_balance()`, consulted only for a background write-time invariant, per RQ2-A below, also contain no loop). **Confirmed: delta does not apply, for either member.**

---

## R1-5 — Relation form

**Exact equality, via `RelationalCmp`, both members** (`intentValue relOp intentValue`, `Parser/Solidity.g4` line 325, reached through `postClause -> commonClause`) — **not** `ReturnExprCmp`/`ReturnVarCmp`/`ReturnIndexCmp` (the grammar's `return`-keyword-prefixed commonClause forms, `Solidity.g4` lines 319-321). Those forms are tied to a function using an explicit `return expr;` statement; `_getReserves()` has **named** return variables (`returns (uint256 _reserve0, uint256 _reserve1)`) and no explicit `return` statement at all (Solidity implicitly returns the named locals at the closing brace) — `_reserve0`/`_reserve1` are ordinary, already-in-scope locals with their own identity, each compared directly via its own `RelationalCmp` against the corresponding state variable (`reserve0`/`reserve1`), the same pattern this project has already established for named-return functions (e.g. `52_H_04`'s `result`). Not forced to equality by the assignment-shaped disputed statements (R1-5's explicit caution) — equality was selected in R1-3 on independent discrimination grounds (the intended relationship is an exact identity, not a bound). **Two independent `@Post` clauses, not one compound `&&` clause** — per README §4's now-adopted policy (see R1-3's Revision note above).

---

## R1-6 — Construct the target annotation

**Target annotation is a set of two `@Post` clauses, both attached at the same point** (mirroring `70_H_04`'s within-one-function two-member pattern, not `35_H_08`'s across-two-functions pattern, since both members here live in the same, single function).

**Attachment point (both members)**: `@Post` on `_getReserves()`, placed after the disputed statements (line 256), before the function's closing brace. `_reserve0`, `_reserve1` (named return locals, in scope throughout and unmutated after line 256) and `reserve0`, `reserve1` (contract-level state, always in scope) are all ordinary `varRef`s legally referenceable at `σ_exit`.

**Target annotation:**
```solidity
function _getReserves() internal view returns (uint256 _reserve0, uint256 _reserve1) {
    (_reserve0, _reserve1) = (reserve0, reserve1);
    _reserve0 = _toAmount(token0, _reserve0);
    _reserve1 = _toAmount(token1, _reserve1);
    // @Post _reserve0 == reserve0
    // @Post _reserve1 == reserve1
}
```
No synthetic/derived constant is introduced — every referenced identifier is a pre-existing, semantically meaningful in-scope value (two named return locals, two state variables); nothing is transcribed from the patch, since no patch syntax was given at all (R1-1).

**Precondition / conditioning, stated explicitly (per R1-7's general note, §4), both members.** Unlike most relations in this benchmark, neither member is scenario-conditioned in its own right — `_reserve0 == reserve0`/`_reserve1 == reserve1` are each intended to hold **unconditionally**, for any reachable `reserve0`/`reserve1` value, not just under a particular precondition (no branch, no loop, no special-cased initial state to worry about). The one thing that *is* scenario-dependent is the **discrimination arithmetic** used to demonstrate the bug concretely (R1-3): each relation is silently satisfied by the buggy code whenever BentoBox's current share-to-amount ratio happens to be exactly `1` (a degenerate case where `_toAmount(token, x) == x`), since in that case the double-application collapses to a no-op. This is a fact about when the *bug is observable*, not a precondition on either relation's *validity* — both are correct/intended in every reachable state; a real deployment with any accrued yield/rebase (price != 1, as in the report's own PoC) exposes the violation for both tokens simultaneously (same underlying price ratio drives both).

**Quantification note**: `_getReserves()` returns exactly two fixed, named values (`_reserve0`, `_reserve1`, one per pool token) — this is not a property naturally quantified over a collection of co-existing elements (contrast `83_H_01`'s "every pool" pattern); there is no array/mapping being ranged over and no representative-element instantiation choice to make for either member. (The two-member *set* itself is not a quantification device either — it exists because there are exactly two named tokens, not because the grammar is standing in for a missing `∀`; contrast `70_H_04`'s member (B), which *is* a genuine representative-element instantiation.)

---

## R1-7 — Expressibility decision

**Member A (`_reserve0 == reserve0`):**
- **Values referenceable at a legal program point**: Yes. `_reserve0` (named return local, unmutated after line 255 through function exit) and `reserve0` (contract-level `internal` state, always addressable within the same contract) are directly referenceable via ordinary `varRef` at `σ_exit`. No function call inside `intentValue` — the relation's own construction never references `_toAmount`/`__balance`/anything call-based at all (R1-3's preliminary check), so the alpha/known-bound-rescue question is moot by construction, not merely satisfied by a rescue.
- **Arithmetic/logical relation representable**: Yes. `_reserve0 == reserve0` is the grammar's plainest possible `commonClause` — `intentValue relOp intentValue` (`RelationalCmp`, `Solidity.g4` line 325) with both sides a bare `varRef` (`NumVarRef`, line 374), no arithmetic operators needed at all.
- **Observation point supported**: Yes — `@Post`, evaluated at `_getReserves()`'s own exit. Delta confirmed not applicable (R1-4).

**Member B (`_reserve1 == reserve1`):** identical reasoning, symmetric to member A — `_reserve1`/`reserve1` in scope, same plain `RelationalCmp` form, same `@Post` exit point, delta confirmed not applicable.

**Outcome: Expressible = YES, for both members of the set.**

---

## §5 — Value/Algorithm and Usable/Unusable

- **Algorithm-level**: per the paper's own classification (`main.tex` L239-240 — Value-level = "a wrong operator, a swapped identifier, or truncation that produces a numerically incorrect result"; Algorithm-level = "operation ordering, an absent state update, or a missing procedure call"), the reported defect is that **an extraneous procedure-call step is executed that should not be executed at all** (lines 255-256, the second `_toAmount()` application) — the mirror image of the paper's own "missing procedure call" example, not a wrong-operator/swapped-identifier/truncation defect confined to one arithmetic expression. This is a defect in *which operations run*, not in the arithmetic of any single expression that does run — the same category distinction `59_H_04`/`70_H_05`'s reclassifications used to separate genuine operator/operand swaps (Value-level) from structural operation-sequencing defects (Algorithm-level), just on the "extra step present" side of that distinction rather than the "step missing" side.
- **Usable**: every value either relation needs (`_reserve0`, `_reserve1`, `reserve0`, `reserve1`) is referenceable, unmutated, at the annotation's program point. No representational gap of any kind — this is one of the more direct Usable cases in the batch, since the correct relations involve no external call, no derived constant, and no cross-function value at all inside the relations themselves (only in their background justification — see RQ2-A).
- **A methodological question raised and resolved on review: does the grammar's inability to state a semantic unit/type distinction ("amount" vs. "share") make this case Unusable regardless of the equality relation's own numeric soundness?** No — per README §5's now-adopted principle (added this session, prompted by this exact case): a semantic-unit distinction the grammar can't state directly does not by itself make a case Unusable; the test is whether the reported intent reduces to an observable numeric relation without needing the annotation to carry the unit/type label itself. Here it does: the report's own PoC shows the amount/share confusion manifesting as a concrete, single-execution numeric discrepancy (`1500` stored vs. `2250` returned), and `_reserve0 == reserve0` exactly captures that discrepancy without ever needing to state "this is an amount, not a share." Contrast `web3bugs_8_H_03` (this project's actual instance of the opposite case — a reported probability *distribution* that is not reducible to any single-execution numeric relation, correctly both Inexpressible and Unusable). The *cost* of knowing that `_reserve0 == reserve0` (rather than, say, `_reserve0 == _toAmount(token0, reserve0)`) is the semantically correct reduction — i.e., of knowing `reserve0` is already amount-denominated — is real, but it belongs in RQ2-A's specification-requirements accounting (see `_updateReserves()`'s load-bearing write-time-convention dependency, below), not in the Usable/Unusable axis.

---

## RQ2-A — Specification Requirements profile

**Covers the combined two-member set** (both members share the identical statements/values/dependencies, since `token0`'s and `token1`'s handling is fully symmetric within one function — unlike `70_H_04`'s two-member profile, no separate per-member accounting is needed here; a single unioned profile already covers both).

**Relevant statements** (within `_getReserves()` itself; §6's rule (a)/(b)/(c), no formal labeling required but noted inline where non-obvious):
1. `(_reserve0, _reserve1) = (reserve0, reserve1);` (line 254) — defines `_reserve0`/`_reserve1`'s pre-bug value directly from state; this is the line that, under the intended/fixed behavior, is the *only* thing that determines the return values.
2. `_reserve0 = _toAmount(token0, _reserve0);` (line 255) — the disputed/target statement (first half): counted as context establishing the annotation's attachment point and subject (per README §6's clarification that the disputed statement itself is required context, distinct from the barred self-substitution-as-evidence practice — its own literal call is not used as evidence for the relation, only its role as the thing being checked/negated).
3. `_reserve1 = _toAmount(token1, _reserve1);` (line 256) — the disputed/target statement (second half), same treatment as (2).

**Total: 3 relevant statements.**

**Excluded, with reason (not merely omitted)**: `_toAmount(...)`'s own internals (lines 279-284: the `staticcall` to `bento.toAmount` and the `abi.decode`) are **not** drilled into (README §6: a call is counted once as a unit, never expanded) — but more than that, `_toAmount` itself is excluded from the "Additional functions required" count entirely (Step 1). **Step 1 test**: would the selected relation's derivation or validity change if `_toAmount`'s specific behavior (e.g., its exact scaling factor, or even its rounding convention) changed? **No.** The relation (`_reserve0 == reserve0`) asserts that the two conversion lines should have no effect on the return value at all — it is agnostic to what `_toAmount` numerically computes, as long as it isn't literally an identity transform (which is exactly the fact that makes the bug *observable*, not a fact the relation's *correctness* depends on — see the scenario-conditioning note in R1-6). This is the same exclusion pattern as `59_H_04`'s `_getIndexOfObservation` — a call physically present inside the annotated function that is nonetheless not load-bearing to the selected relation. Consequently, `token0`/`token1` (the call's own arguments at lines 255-256) are also not counted as separate "unique relevant program values" below — they exist purely inside the excluded call's own plumbing and feed no relation-relevant value the way, e.g., `59_H_04`'s loop index `i` fed the counted `pegObservations[index]`/`total` chain; unlike that case, nothing here re-uses `token0`/`token1` in any statement that defines a value the relation actually references.

**Unique relevant program values** (within the annotated function's own scope, occurring in the statements counted above):
- Named return locals (2): `_reserve0`, `_reserve1`
- State variables (2): `reserve0`, `reserve1`

**Total: 4 unique relevant program values.** (`_getReserves()` has genuinely named return variables — unlike a bare `returns (uint256)` function, `_reserve0`/`_reserve1` are counted normally as locals with their own identity, per README §6's named-return-variable rule, the same treatment already applied to `52_H_04`'s `result`.)

**Additional functions required**: **1** — `_updateReserves()` (same contract; **not called by** `_getReserves()` at all — read only to establish the write-time invariant the relation's correctness depends on, per README's "no missing-call exception" extended to enforced-invariant dependencies, the same pattern already used for `70_H_05`'s `_addUSDVPair`). **Mandatory semantic-dependency note**: `_updateReserves()` is the *only* place `reserve0`/`reserve1` are ever written, and it stores them as the direct result of `_balance()` — which itself applies `_toAmount()` (share->amount conversion) exactly once, before the value ever reaches storage. **This is genuinely load-bearing, checked via the Step 1 operational test**: if `_updateReserves()`'s write-time guarantee changed (e.g., if it stored the *raw, unconverted* BentoBox share count instead of the amount-converted result — while remaining consistent with everything else already known about it) — the target relation `_reserve0 == reserve0` would **no longer be correct**; `_getReserves()` would then legitimately need to perform exactly the share->amount conversion it currently (per the report) mistakenly performs *twice*. So unlike `_toAmount` (excluded above, not load-bearing to *this* relation's own validity), `_updateReserves()`'s specific write-time convention is exactly what makes this relation the *correct* one rather than an arbitrary guess — it is not merely inspected in passing. `_balance()` (called by `_updateReserves()`) is not separately itemized — per README's no-recursive-counting rule, its role is folded into `_updateReserves()`'s semantic note rather than counted as a second atomic dependency.
- **Step 2 (README §6)**: this is **semantic program context**, not a generic library fact — `_updateReserves()`'s specific convention ("this contract always pre-converts to amount at write time") is this contract's own accounting design choice, not a protocol-independent primitive. Counts normally toward "Additional functions required" and Context breadth.

**Additional protocol/application-specific contracts/libraries required**: **0.** BentoBox itself (`IBentoBoxMinimal`, reached via `staticcall` inside `_toAmount`/`__balance`) is never load-bearing to the selected relation (Step 1 exclusion, above) — its specific share-accounting mechanics are never referenced by the relation or by `_updateReserves()`'s semantic note, which only needs "this contract's own write path converts once," not any fact about *how* BentoBox itself computes that conversion.

**Context breadth**: **2** (other function in the same contract — `_updateReserves()`, consulted for its enforced write-time invariant even though it is not called by `_getReserves()`).

**External specification required**: **No.** The relation's justification — that `_getReserves()` should be a pure passthrough because `_updateReserves()`/`_balance()` already perform the share->amount conversion once, at write time — is derivable entirely from this contract's own source (comparing the write path against the read path); no BentoBox protocol-specific accounting convention needs to be understood to establish *that* a conversion already happened, only *that* this contract's own code performs one. (The specific numeric share-price value used in the discrimination scenario, `1.5`, is protocol-specific BentoBox state — but it is borrowed directly from the report's own PoC purely to illustrate the arithmetic, not independently derived or needed to justify the relation's correctness.)

---

## §7 — Alternatives-considered summary

| # | Relation | Tier | Expressible? | Discriminates? | Verdict |
|---|----------|------|---------------|-----------------|---------|
| — | Call-based framing (`_reserve0` expressed via `_toAmount`/`__balance` applied once) | — | Would need alpha rescue | — | Not selected — a call-free alternative (below) is both simpler and strictly more general; rescue check performed but moot |
| 1 | `_reserve0 <= reserve0` / `_reserve1 <= reserve1` (directional, motivated by PoC's price>1) | Inequality | Yes | Yes, in this scenario | Rejected — relies on an unverified assumption that BentoBox's price ratio is always >=1; not established in-scope, and understates the reported "make it correct" intent even where it holds |
| 2a | `_reserve0 == reserve0` | Exact equality | Yes | Yes | **Selected — member A of the target set** |
| 2b | `_reserve1 == reserve1` | Exact equality | Yes | Yes | **Selected — member B of the target set** |
| — | Single compound `@Post _reserve0 == reserve0 && _reserve1 == reserve1` | Exact equality, compound clause | Yes (grammar/engine genuinely support `&&`, verified) | Yes | **Rejected on review, not on expressibility grounds** — README §4 policy: use a two-member set instead of `&&`, to avoid needing compound-clause combination in the paper's formal semantics (see R1-3's Revision note) |
| — | Known-bound/call rescue (alpha-style) | — | N/A | — | Not applicable — neither selected relation contains a call to begin with |
| — | Snapshot-qualified `varRef(Entry/...)` extension | — | N/A | — | Not needed — no before/after or entry/exit pairing required, plain `@Post` on final settled values suffices |

## RQ1-B / RQ2-B

Deferred per README §8. Not run, not predicted.

---

## Summary

**Revised on review (target annotation repackaged as a two-member set; Usable/Unusable methodological question raised and resolved) — supersedes the original single-compound-clause pass; see R1-3/R1-4/R1-5/R1-6/R1-7/§5/§7 above for the full reasoning. No change to the underlying verdict, relation content, or numeric arithmetic — only how the target annotation is packaged and documented.**

- **Expressible: Yes, for both members of the target set.** Post-scope, exact equality (`RelationalCmp` common form), two independent clauses: `_reserve0 == reserve0` and `_reserve1 == reserve1`, both attached to `_getReserves()`. No function call inside either relation, no derived constant, no external-contract reference.
- **Target annotation (a set of two `@Post` clauses, not one compound `&&` clause — see R1-3's Revision note)**:
  - (A) `@Post _reserve0 == reserve0`
  - (B) `@Post _reserve1 == reserve1`
  Both attached immediately after `_reserve1 = _toAmount(token1, _reserve1);` in `_getReserves()`. The grammar/engine genuinely support a single compound `&&` clause too (verified this session across all four layers: grammar, visitor, `ContractAnalyzer`, `Interpreter/Engine.py`) — the two-member packaging is a deliberate methodology choice (README §4), not an expressibility workaround.
- **Delta-exception check (required by task brief, performed on this case's own facts): explicitly checked and confirmed NOT applicable, for either member.** `_getReserves()` contains no loop of any kind — a straight-line, three-statement function — so there is no loop-body attachment point for the confirmed `delta` exception to even apply to.
- **Value-level/Algorithm-level**: **Algorithm-level.** The defect is an extraneous procedure-call step (a second, erroneous `_toAmount()` application, applied to both `_reserve0` and `_reserve1`) executed where none should run at all — the mirror image of the paper's own "missing procedure call" Algorithm-level example, not a wrong-operator/swapped-identifier defect confined to a single arithmetic expression.
- **Usable/Unusable**: Usable, for both members — every value either relation needs is referenceable in-scope at function exit, with no call, no derived constant, and no cross-function value inside either relation itself. **Methodological question raised and resolved on review** (now a general README §5 principle, this case as its worked example): the grammar's inability to state a semantic unit/type distinction ("amount" vs. "share") directly does *not* make this case Unusable, because the reported intent reduces cleanly to an observable, single-execution numeric relation (`1500` stored vs. `2250` returned) without the annotation needing to carry the unit label itself — contrast `web3bugs_8_H_03`, correctly Unusable because its reported property (a probability distribution) has no such numeric reduction, not even in principle.
- **Precondition**: none on either relation's own validity — both are intended to hold unconditionally. The scenario-dependence is only in the *discrimination* arithmetic: the bug is silently masked whenever BentoBox's share-to-amount ratio happens to equal exactly 1 (a degenerate case), and is exposed under any real ratio != 1, as in the report's own PoC (ratio 1.5), for both tokens simultaneously.
- **Quantified property instantiated: No, for both members.** `_getReserves()` returns exactly two fixed, named values (one per pool token) — not a property ranging over a stored collection; no representative-element instantiation was needed for either member, and the two-member set itself is not a quantification device (contrast `70_H_04`'s member (B), a genuine representative-element instantiation).
- **RQ2-A profile (covers the combined set — both members share the identical statements/values/dependencies)**: Relevant statements = 3; Unique relevant program values = 4 (2 named-return locals, 2 state); Additional functions required = 1 (`_updateReserves()`, not called by `_getReserves()` but load-bearing for the enforced write-time invariant both relations' correctness depends on — semantic-dependency note given above); Additional protocol/library dependencies = 0 (BentoBox itself never load-bearing to either selected relation); Context breadth = 2 (same-contract, cross-function); External specification required = No.
- **RQ1-B/RQ2-B**: deferred, not run in this pass.
