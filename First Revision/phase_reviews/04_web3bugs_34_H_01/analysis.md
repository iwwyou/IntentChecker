# web3bugs_34_H_01 — Agent A (Analyst) Case Analysis

Case ID: `web3bugs_34_H_01` | Contract: `DrawCalculator` | Function: `_numberOfPrizesForIndex(uint8 _bitRangeSize, uint256 _prizeTierIndex) internal pure returns (uint256)`
Existing label: H-01, "The formula of number of prizes for a degree is wrong" (Code4rena contest 34, sponsor-confirmed and patched)
Source: `evaluation/RQ1/target_contracts_original/web3bugs_34_H_01.sol`; Report: `C:\Users\isjeon\Web3Bugs\reports\34.md` (§0.5 — primary/authoritative source; the finding is `[[H-01] ...]`)
Reported bug lines: 422–424 (local numbering matches the report's `L423-431` recommendation-anchor range for the same function)

*(Background only, not used as a starting assumption per the task framing: this case was previously labeled under the retired L1a "loop-widening" taxonomy. R1-1–R1-7 below are derived fresh; the outcome below was reached independently of that old label and does not rely on any widening/engine-precision argument — see R1-7.)*

## R1-1 — Reported Behavior Reconstruction

**Contract/function role**: `DrawCalculator` computes a user's PoolTogether prize by matching their picks against a winning random number, splitting the total prize pool across tiers ("degrees") by bit-range matches. `_numberOfPrizesForIndex` is a pure combinatorial helper: given a tier's `_bitRangeSize` (bits per match chunk) and the tier's index `_prizeTierIndex` (`n`, degree of exact matches), it computes how many distinct pick values fall into that exact tier — used as the divisor in `_calculatePrizeTierFraction` (line 381: `prizeFraction / numberOfPrizesForIndex`) to split each tier's fractional prize evenly across its winners.

**Relevant locals**:
- `bitRangeDecimal` (line 419): `2**uint256(_bitRangeSize)` — the branching factor `b`, i.e. how many distinct values one bit-range chunk of the random number can take. Constant for the whole function body once assigned.
- `numberOfPrizesForIndex` (line 420 initial value, mutated lines 422–424, returned line 427) — the value the bug corrupts.
- `_prizeTierIndex` (parameter, `uint256`, passed **by value**) — doubles as the loop's own decrementing counter (line 424: `_prizeTierIndex--`), which is the mechanism at the center of this case (see R1-6/R1-7).

**The buggy computation**:
```solidity
uint256 bitRangeDecimal = 2**uint256(_bitRangeSize);
uint256 numberOfPrizesForIndex = bitRangeDecimal**_prizeTierIndex;

while (_prizeTierIndex > 0) {
    numberOfPrizesForIndex -= bitRangeDecimal**(_prizeTierIndex - 1);   // lines 422-424 — BUGGY loop
    _prizeTierIndex--;
}

return numberOfPrizesForIndex;
```
- **Variable-value intent (the function's return value)**: for tier index `n = _prizeTierIndex > 0`, the returned count must equal `b^n − b^(n−1)` (documented protocol formula, cited in the report from PoolTogether's own prize-distribution spec). For `n = 0`, it must equal `1`.
- **Statement/line-level invariant**: the loop is supposed to perform exactly *one* subtraction (`b^(n−1)`) from the initial `b^n` term, not an entire descending geometric series. As written, the loop iterates `n` times, subtracting `b^(n−1) + b^(n−2) + ... + b^0` in total — every term below the first, not just the first.

**Reported erroneous behavior** (audit report, H-01): the report gives two independent proofs that the correct formula is `f(bitRange, n) = b^n − b^(n−1)`, and states the current code instead computes `b^n − b^(n−1) − b^(n−2) − ...`, which "will be smaller than expected, as a result, `prize for a degree` will be larger than expected. Making the protocol giving out more prizes than designed." Sponsor-confirmed and patched (PR referenced in the report).

**Expected/intended behavior**: `numberOfPrizesForIndex == bitRangeDecimal**_prizeTierIndex - bitRangeDecimal**(_prizeTierIndex - 1)` whenever the original `_prizeTierIndex > 0`; `== 1` when `_prizeTierIndex == 0` (this base case is already correct in the current code, since the loop body never executes when `_prizeTierIndex` starts at `0` — confirmed numerically below).

**Patch intent** (evidence only, not transcribed): the report's recommended replacement removes the loop entirely —
```solidity
if (_prizeTierIndex > 0) {
    return ( 1 << _bitRangeSize * _prizeTierIndex ) - ( 1 << _bitRangeSize * (_prizeTierIndex - 1) );
} else {
    return 1;
}
```
This is evidence that (a) the invariant is a two-term difference, not an accumulated multi-term subtraction, and (b) the fix eliminates the loop/counter structure altogether. It is *not* evidence that the annotation must use the patch's `1 << ...` bit-shift spelling — the function already has an in-scope, semantically equivalent name for the same quantity (`bitRangeDecimal = 2**_bitRangeSize`), which is used in R1-3/R1-6 below in preference to the patch's literal syntax (§2/§3).

**Bug-relevant intended numeric behavior**: for any call with `_prizeTierIndex = n > 0`, the value ultimately returned by `_numberOfPrizesForIndex` must equal `bitRangeDecimal^n − bitRangeDecimal^(n−1)` — an exact combinatorial count, not merely a bound — and the current loop instead subtracts every lower power down to `bitRangeDecimal^0`, undercounting whenever `n ≥ 2`.

## R1-2 — Intent Abstraction

Distinguishing property (patch syntax dropped): the return value must equal `bitRangeDecimal^n − bitRangeDecimal^(n−1)`, not a value further reduced by the sum of all strictly-lower powers. **Intent-level orientation: Value-centered** — a constraint on the return value `numberOfPrizesForIndex`, not a broader effect/state-transition claim (the function is `pure` and has no persistent state to transition).

## R1-3 — Select the least implementation-specific sufficient relation (alternatives recorded, §7)

1. **Directional (loose lower bound)**: `numberOfPrizesForIndex >= bitRangeDecimal**(_prizeTierIndex - 1)`. **Rejected — not discriminating.** Concrete check at `bitRangeSize=4` (`b=16`), `n=2`: RHS `= 16^1 = 16`; buggy value `= 239` (derivation below) satisfies `239 >= 16` — the bound is satisfied by the buggy output too, so it never flags the bug.
2. **Directional (loose upper bound at the intended value)**: `numberOfPrizesForIndex <= bitRangeDecimal**_prizeTierIndex - bitRangeDecimal**(_prizeTierIndex - 1)`. **Rejected — not discriminating, for the opposite reason.** Since the buggy loop only ever subtracts *additional* non-negative terms beyond the correct single term, the buggy value is always `≤` the intended value (equal iff `n ≤ 1`, strictly less for `n ≥ 2` — proof: buggy `= b^n − Σ_{i=0}^{n-1} b^i = intended − Σ_{i=0}^{n-2} b^i`, and each `b^i ≥ 1`). At `n=2, b=16`: buggy `=239 <= 240` = true — again satisfied by the buggy output, so an upper bound at the intended value never flags this bug (the direction of the error is *below* the bound, not above it).
3. **Inequality / lower bound at the intended value**: `numberOfPrizesForIndex >= bitRangeDecimal**_prizeTierIndex - bitRangeDecimal**(_prizeTierIndex - 1)`. Discriminates: at `n=2`, buggy `239 >= 240` is false (flags the bug); intended `240 >= 240` is true (holds, with equality). **Viable candidate.**
4. **Relational invariant / known-bound rescue** (README's Nokon-style pattern): **not applicable here.** This pattern substitutes a known bound for an unreachable *function-call result* inside a relation. There is no function call anywhere in this relation or this function — the blocker examined in R1-6/R1-7 is a different mechanism entirely (an ordinary in-function local/parameter whose *historical* value is overwritten by the very loop under test, not a call result). There is nothing a call-result bound could substitute for.
5. **Exact equality**: `numberOfPrizesForIndex == bitRangeDecimal**_prizeTierIndex - bitRangeDecimal**(_prizeTierIndex - 1)`. Discriminates identically to (3) on every scenario checked (the RHS is byte-for-byte the same expression in both; only the comparator differs), and is the semantically accurate claim for what is, by nature, an *exact* combinatorial count rather than a bound relationship. Per README's explicit caution, operator strength alone does not measure implementation-specificity — here (3)'s `>=` buys no independence from the patch's arithmetic relative to (5)'s `==`, since both reference the identical RHS expression. **Selected as the notional R1-3 winner** (see R1-6/R1-7 — this selection turns out not to be constructible as an annotation, for a reason orthogonal to the choice between (3) and (5)).
6. **Parameter-mutation side channel** (considered and rejected — not a standard R1-3 tier, included for transparency because it is a real, discriminating-looking alternative): `@Post _prizeTierIndex(entry == exit)`, or equivalently `changed(_prizeTierIndex, false)`. On the *current* buggy code this is violated for every call with `n ≥ 1` (the loop always drains `_prizeTierIndex` to `0`); on the *specific* recommended patch (which deletes the loop) it would hold trivially for every `n`. It therefore "discriminates" in a narrow logical sense. **Rejected for two reasons**: (a) it is wrong-target — it says nothing about `numberOfPrizesForIndex`'s value, the actual quantity R1-1's reported impact ("smaller than expected"/"giving out more prizes than designed") is about; it would flag `n=1` calls as violated even though the *returned count is already correct* for `n=1` (verified in the discrimination check below), a false positive relative to the real bug. (b) it is patch-implementation-specific in exactly the way §2/§3 warn against: it happens to flip in step with *this one* recommended patch (which eliminates the loop), but an equally valid alternative fix that kept a corrected loop (e.g. one that stops after a single iteration) would still mutate `_prizeTierIndex` away from `n` and would be wrongly flagged as buggy by this annotation. Excluded from the candidate set.

**Selected relation (notional)**: exact equality, `numberOfPrizesForIndex == bitRangeDecimal**_prizeTierIndex - bitRangeDecimal**(_prizeTierIndex - 1)`, for the branch where the original `_prizeTierIndex > 0`. **This selection is not constructible as an annotation** — R1-6 shows why, and the reason applies equally to alternative (3); it is not a consequence of choosing equality over the bound.

**Discrimination check (explicit arithmetic, per §9 checklist item 1)**: `bitRangeSize = 4` ⇒ `bitRangeDecimal = 16`.
- `n = 1` (does **not** discriminate — included to show the bug's actual threshold): buggy: start `16^1=16`; loop iter (`_prizeTierIndex=1`): subtract `16^0=1` → `15`; decrement to `0`, loop ends; return `15`. Intended: `16^1 − 16^0 = 16 − 1 = 15`. **Match** — the bug does not manifest at `n=1`.
- `n = 2` (discriminates): buggy: start `16^2=256`; iter 1 (`_prizeTierIndex=2`): subtract `16^1=16` → `240`, decrement to `1`; iter 2 (`_prizeTierIndex=1`): subtract `16^0=1` → `239`, decrement to `0`, loop ends; return `239`. Intended: `16^2 − 16^1 = 256 − 16 = 240`. **Mismatch** (`239 ≠ 240`) — confirms the selected relation is violated on the buggy code and would hold on the patched code, for a scenario where the bug actually manifests.

## R1-4 — During vs Post

**Natural choice: Post.** The relation concerns the function's return value, a function-exit property (README's During/Post criteria, §4/R1-4) — not an intermediate, statement-time value. This is not chosen merely because the report describes a function-level consequence (R1-4's explicit caution); it is chosen because the *quantity being constrained*, `numberOfPrizesForIndex`'s final settled value, only exists once, at the point of `return` — there is no meaningful "During" reading of "the count this function computes" prior to the loop finishing.

As shown in R1-6/R1-7, **no scope choice — During at any point, or Post — actually succeeds** in referencing everything the relation needs simultaneously; this subsection records the scope that would be natural if the relation were constructible.

## R1-5 — Relation form

Common form: exact equality via `intentValue relOp intentValue`, rule (C_cmp) — not Entry-Exit rule (P_ee), since (P_ee) compares the *same* expression `e` at entry vs. exit, whereas this relation compares `numberOfPrizesForIndex` (an exit-time quantity) against a *different* expression built from `bitRangeDecimal` and `_prizeTierIndex`. Not forced to equality by the assignment-shaped/loop-shaped statement (R1-5's explicit rule) — equality was selected in R1-3 on independent discrimination-vs-implementation-specificity grounds.

## R1-6 — Attempted construction of the target annotation (fails — see below)

**Naive attempt** (attach `@Post` to the function, referencing the R1-3-selected relation directly):
```solidity
function _numberOfPrizesForIndex(uint8 _bitRangeSize, uint256 _prizeTierIndex)
    internal
    pure
    returns (uint256)
{
    uint256 bitRangeDecimal = 2**uint256(_bitRangeSize);
    uint256 numberOfPrizesForIndex = bitRangeDecimal**_prizeTierIndex;

    while (_prizeTierIndex > 0) {
        numberOfPrizesForIndex -= bitRangeDecimal**(_prizeTierIndex - 1);
        _prizeTierIndex--;
    }

    return numberOfPrizesForIndex;
    // @Post numberOfPrizesForIndex == bitRangeDecimal**_prizeTierIndex - bitRangeDecimal**(_prizeTierIndex - 1)   -- BROKEN, see below
}
```
**Why this fails**: `_prizeTierIndex` is passed **by value** and is reused as the loop's own decrementing counter (line 424). By the time `numberOfPrizesForIndex` holds its settled value (immediately before `return`, i.e. exactly the point a `@Post` common-form annotation's reference environment `ref(Γ) = σ_exit` observes), `_prizeTierIndex` has been driven to `0` for *every* call where the original value was `≥ 1` — the loop runs until the condition `_prizeTierIndex > 0` is false. So the annotation above does not evaluate against the original tier index `n` at all; it silently evaluates `_prizeTierIndex - 1` at `_prizeTierIndex = 0`, which is not the intended quantity (and is itself an underflow on a `uint256` if evaluated as written).

**Checking every other candidate point in the function** — none has both facts at once:
- **Before the loop** (right after line 420): `_prizeTierIndex` still equals the original `n`, and `bitRangeDecimal` is available — but `numberOfPrizesForIndex` at this point is only the *un-corrected* initial term `bitRangeDecimal^n`; the loop (buggy or not) has not run yet, so nothing here reflects the actual computation under test. A `@During` annotation here could never be violated by the loop's bug at all, since evaluation happens strictly before the loop executes.
- **Inside the loop, after the final iteration's subtraction but before its decrement** (i.e. right after line 423 on the loop's *last* pass): `numberOfPrizesForIndex` already holds its final (buggy) value here — but at that point `_prizeTierIndex` has already been decremented down to `1` by every *prior* iteration, regardless of what the original `n` was (checked directly against the R1-3 discrimination trace above: at `n=2`, `_prizeTierIndex = 1` on the loop's last pass, not `2`). So this point has the settled value but never the original `n` either (except in the degenerate case `n=1`, which is exactly the case that does not discriminate the bug — see R1-3's discrimination check).
- **Any other in-scope identifier**: `bitRangeDecimal` never changes but does not encode `n`; no other local exists in this function to hold a separate, un-mutated copy of the original tier index.

**Considered-and-rejected repair (hardcode both operands to bypass the mutated identifier)**: replace the relation with an unconditional numeric literal, e.g. `@Post numberOfPrizesForIndex == 240` (the `n=2, bitRangeSize=4` scenario constant from the discrimination check), eliminating any reference to `_prizeTierIndex` from the annotation text. **Rejected**: unlike a legitimate concrete-constant substitution (R1-6's guidance, and the README's Nokon `250000` precedent, where *one* otherwise-unreachable sub-quantity is replaced by a known bound while the relation stays a genuine symbolic relation over live variables), this would eliminate the *entire* input-output relationship R1-1/R1-2 identified as the bug-relevant behavior, replacing it with an assertion that is false for almost every other input and carries no indication — anywhere in the annotation itself — that it depends on a specific, externally-assumed `_prizeTierIndex`. This is also not an instance of README's sanctioned "instantiate a collection-quantified property on one representative element" pattern (R1-6): that pattern keeps the *relation* symbolic and only fixes *which* array/mapping element it ranges over; here the relation itself would have to be deleted, not merely instantiated. Not accepted as a faithful expression of the R1-2/R1-3 relation.

**Considered-and-rejected repair (per-iteration `@During`, added in a later pass while re-examining `web3bugs_71_H_11`)**: instead of comparing the *original* `n` against the *final* `numberOfPrizesForIndex`, check a per-iteration relation using only values that are simultaneously in scope at one point inside the loop — e.g. right after line 423's subtraction, before the line-424 decrement, using the loop-local *current* `_prizeTierIndex` (call it `k`, the value on that pass) instead of the original `n`:
```solidity
numberOfPrizesForIndex -= bitRangeDecimal**(_prizeTierIndex - 1);
// @During numberOfPrizesForIndex == bitRangeDecimal**_prizeTierIndex - bitRangeDecimal**(_prizeTierIndex - 1)   -- attempted rescue
_prizeTierIndex--;
```
This sidesteps R1-6's original blocker (original-`n`-vs-final-value can never co-occur) since both operands are read at the same instant, on the same loop pass. It does **not** survive, but for a different, independent reason: this is a loop-body `@During`, and per README §4/R1-7's confirmed architectural exception (established while resolving `web3bugs_71_H_11` in this same review pass — `Interpreter/Engine.py`'s `fixpoint()`/`reinterpret_from()` never evaluate a `@During` attached inside a loop body), the engine would never evaluate this annotation regardless of its content being otherwise sound. This is the same **delta** blocker as `71_H_11`'s, not a second instance of beta. **Verdict unaffected**: the case's primary/first-found blocker is still R1-6's beta (no in-scope reference to the original `_prizeTierIndex` survives to any single-point `@Post`), so the tag stays **beta** — this per-iteration alternative is recorded only for completeness/transparency, since it was a candidate that looked promising before the delta exception was confirmed, and would also have failed even if beta's value-availability problem hadn't already ruled it out first.

**Conclusion**: R1-6 cannot produce a fixed target annotation, attached at any legal program point in `_numberOfPrizesForIndex`, that is both grammatically legal and a faithful expression of the R1-2/R1-3 relation.

## R1-7 — Expressibility decision

Per the task framing, this decision considers only grammar/scope facts (values referenceable at a legal point, arithmetic representable, observation point supported) — explicitly **not** whether abstract interpretation would widen the loop to top, whether the engine would report Warning vs. Violated, or any other engine-precision question (all out of scope for R1-7, deferred to RQ1-B). The blocker identified below is independent of all of that: it is established purely from the function's control/data flow (which value each identifier holds at each program point), not from how any analysis engine would evaluate it. A perfectly precise, non-widening analyzer would face exactly the same obstacle, because the textual/temporal co-reference the relation needs simply is not offered by the grammar.

- **Values referenceable at the point**: `numberOfPrizesForIndex`'s settled value *is* referenceable at exit (`σ_exit`) — but `_prizeTierIndex`'s *original* value is not referenceable anywhere the settled `numberOfPrizesForIndex` is also available (R1-6). No in-scope identifier, at any single reachable program point, holds both facts.
- **Arithmetic/relation representable**: the arithmetic itself (`bitRangeDecimal**_prizeTierIndex - bitRangeDecimal**(_prizeTierIndex - 1)`, compared by `==` or `>=` to `numberOfPrizesForIndex`) is ordinary and well within the grammar's exponentiation/subtraction/comparison forms — this is not the blocking factor.
- **Observation point supported**: both `@During` (single `σ_pt`) and `@Post` (common forms use a single, uniform `ref(Γ) = σ_exit`) are supported observation *kinds* in general — but neither offers a reference environment that mixes an entry-time value of one identifier with an exit-time value of another. The one rule that does span entry and exit, (P_ee), compares a *single* expression `e` at both times, not two different expressions (R1-5) — it cannot be repurposed to pair `_prizeTierIndex@entry` with `numberOfPrizesForIndex@exit`.
- **No function call inside `intentValue`** — not the issue here; there is no call anywhere in this relation, so the alpha/Nokon-rescue question does not arise (R1-3, item 4).

**Outcome: Expressible — No.**

**Tag: beta** — no in-scope variable/expression exists to reference the needed value (the original `_prizeTierIndex`) at the point where the relation needs to be checked. This is a value-availability fact, not a relation-form fact: if `_prizeTierIndex`'s original value happened to survive to function exit (e.g. if the loop used a separate counter instead of consuming the parameter itself), the exact same relation would be an entirely ordinary, single-point `@Post` common-form equality — no multi-point/structural relation form would be needed. The mechanism is specific to this function (an ordinary value parameter destroyed by being reused as its own loop's decrementing counter) rather than the more usual beta pattern of "the value lives in another contract's state" (e.g. `web3bugs_59_H_05`), but it is the same taxonomic category: the needed value has no live in-scope reference at the required point.

## Usable/Unusable (§5)

**Unusable** — the value needed to represent the intended relation (`_prizeTierIndex`'s original value, at the point `numberOfPrizesForIndex`'s final value is known) is not referenceable in any form the intent model can use; this is purely a representational-resources fact (§5), not a claim about whether a developer could have noticed the bug. **Value-level** (a direct equality/bound on a specific return value, not an algorithm/ordering property).

## RQ2-A — Specification profile

**Not applicable.** Per README §6, RQ2-A applies only to Expressible cases. This case is Expressible: No (beta) — no structural profile is recorded.

## RQ1-B / RQ2-B

Deferred, per README §8 and the task instructions — engine execution is explicitly out of scope for this analysis pass. No predicted outcome is recorded here.

## Summary

- **Expressible: No** — **beta** (no in-scope reference to the needed value — the original `_prizeTierIndex` — survives to the point where the relation would need to be checked; `_prizeTierIndex` is consumed as the buggy loop's own counter, per R1-6/R1-7).
- **Target annotation**: none constructible (R1-6). The relation that *would* have been used, had the value survived, is the notional R1-3 selection:
  `numberOfPrizesForIndex == bitRangeDecimal**_prizeTierIndex - bitRangeDecimal**(_prizeTierIndex - 1)` (for the original `_prizeTierIndex > 0`), intended as a `@Post` common-form exact equality — blocked at R1-6/R1-7, not a valid final annotation.
- Value-level, **Unusable**, notional scope Post, notional relation form exact equality (blocked before construction).
- **Quantified property instantiated: No** — the relation is conditioned on one call's input (`_prizeTierIndex = n > 0`, a standard scenario-conditioned relation per R1-7's general note), not a property naturally quantified over a stored collection/array/mapping accessed within one execution; no representative-element instantiation issue applies here.
- Alternatives considered at R1-3: two directional bounds (both rejected, non-discriminating in opposite directions — see arithmetic above), a lower-bound inequality (viable, discriminates), the Nokon-style known-bound/call rescue (not applicable — no function call is involved in the blocker), exact equality (selected notionally, same discriminating power as the bound with no added implementation-specificity), and a parameter-mutation side-channel relation (rejected — wrong target and over-fit to one specific patch's structure, not a genuine expression of R1-1's reported behavior). Additionally, at R1-6 (checked in a later pass): a per-iteration `@During` using the loop-local current `_prizeTierIndex` instead of the original `n` (rejected — not because of beta's value-availability problem, but independently blocked by the same **delta** loop-body-observation-point exception confirmed for `71_H_11`; recorded for transparency, does not change the verdict or tag).
- RQ1-B/RQ2-B: deferred, not run in this pass.
