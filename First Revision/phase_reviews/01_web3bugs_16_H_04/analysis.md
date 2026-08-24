# web3bugs_16_H_04 — Agent A (Analyst) Case Analysis

Case ID: `web3bugs_16_H_04` | Contract: `Balances` (library) | Function: `applyTrade(Position memory position, Trade memory trade, uint256 feeRate) internal pure returns (Position memory)`
Existing label: H-04, "Logic error in fee subtraction" (Code4rena contest 16, sponsor-confirmed)
Source: `evaluation/RQ1/target_contracts_original/web3bugs_16_H_04.sol`; Report: `Dataset/Web3Bugs/S6_4/contest_16_H_04/README.md`

## R1-1 — Reported Behavior Reconstruction

**Contract/function role**: `Balances` is a pure-computation library (no storage) for Tracer Protocol's perpetual-swap accounting. `applyTrade` computes the new `Position {quote, base}` resulting from executing a `Trade {price, amount, side}` against an existing position, including a trading fee.

**Relevant locals**: `quoteChange` (line 179, `PRBMathSD59x18.mul(signedAmount, signedPrice)`) — signed notional value of the trade. `fee` (line 180, `getFee(trade.amount, trade.price, feeRate)`) — inside `getFee` (lines 205–214) it is `PRBMathUD60x18.mul(quoteChange_local, feeRate).toInt256()`, where both operands are `uint256`; **`fee` is therefore non-negative by type construction**, not by convention. `newQuote` (lines 182/187/190) — the value the bug corrupts.

**The two branches**:
```solidity
if (trade.side == Perpetuals.Side.Long) {
    newBase = position.base + signedAmount;
    newQuote = position.quote - quoteChange + fee;      // line 187 — BUGGY
} else if (trade.side == Perpetuals.Side.Short) {
    newBase = position.base - signedAmount;
    newQuote = position.quote + quoteChange - fee;       // line 190 — correct pattern
}
```
- **Variable-value intent (line 187)**: the trader's new quote balance after a long trade = pre-trade quote balance ± notional price movement, **minus** the fee owed.
- **Statement-level invariant**: fee must always reduce the trader's quote balance regardless of side — a cost, never a credit. The Short branch already respects this; Long does not.

**Reported erroneous behavior** (audit report): "the current code subtracts a fee from the short position and adds it to the long... This issue causes withdrawal problems, since Tracer thinks it can withdraw the collected fees, leaving the users with an incorrect amount of quote tokens." Sponsor-confirmed valid.

**Patch intent** (evidence only, not transcribed): change `+fee` to `-fee` on line 187 — evidence that the invariant is "fee always reduces `newQuote`," not evidence the annotation must read literally `-fee`.

**Bug-relevant intended numeric behavior**: In the `Long` branch, the fee must never increase `newQuote`; it must reduce it relative to what the notional-price adjustment alone gives. The bug adds a non-negative quantity where intent requires subtraction.

## R1-2 — Intent Abstraction

Distinguishing property (patch syntax dropped): the fee term must not push `newQuote` above the fee-free adjustment `position.quote - quoteChange`, since `fee` is never negative. **Intent-level orientation: Value-centered** — a constraint on `newQuote` immediately after its assignment, not a broader effect claim.

## R1-3 — Select the least implementation-specific sufficient relation (alternatives recorded, §7)

1. **Directional/state-change** (e.g. `newQuote` vs. `position.quote` direction alone): **rejected — not discriminating**. *(Corrected during Agent B review — see `review.md`: the original justification incorrectly claimed `quoteChange` could be negative.)* `quoteChange` is in fact always non-negative in this function (`trade.amount`/`trade.price` are `uint256`, and `PRBMathSD59x18.mul` of two non-negative operands stays non-negative), so sign ambiguity is not the issue. The real reason a bare directional check fails to discriminate is **relative magnitude**: whenever `quoteChange > fee` (e.g. `quoteChange=100, fee=10`), the buggy line still satisfies `newQuote <= position.quote` (`position.quote - 100 + 10 = position.quote - 90`) even though it's wrong — the notional term dominates and hides the fee-sign bug. A directional claim ignoring `quoteChange`'s magnitude relative to `fee` can't isolate the fee-sign bug in the common case where the notional adjustment outweighs the fee.
2. **Inequality/bound**: `newQuote <= position.quote - quoteChange`. *(Wording sharpened per README's precision-scoping guidance, R1-3.)* `fee` is `getFee`'s `PRBMathUD60x18.mul(...)` result — a `uint256`, non-negative unconditionally by type construction, no execution-semantics assumption needed — subsequently cast via `.toInt256()`; on any execution that completes without reverting, that cast preserves non-negativity (a standard safe-cast reverts rather than wraps on overflow, and `fee`'s magnitude here is far under `int256`'s range regardless). So on all successful executions, `fee >= 0`, hence intended (`... - fee`) always satisfies the bound (equality when `fee==0`); buggy (`... + fee`) violates it whenever `fee > 0`. **Selected.**
3. **Relational invariant / known-bound rescue** (README's Nokon-style pattern): not needed — `fee` is an ordinary in-scope local, not an unreachable call result, so there's no call to route around; this tier collapses into (2) with no added benefit.
4. **Exact equality**: `newQuote == position.quote - quoteChange - fee`. Discriminates, but no more than (2) on any scenario with `fee > 0` — it is the maximally patch-specific option (literally the patched line). **Rejected**: strictly more implementation-specific than (2) for zero gain in discriminating power, which is exactly what §2/§7 caution against.

**Selected**: `newQuote <= position.quote - quoteChange`. It wins because it is supported by the reported invariant, expressible from in-scope observables, and exactly as discriminating as exact equality while being decoupled from the patch's specific arithmetic — the weaker directional option was rejected purely for failing to discriminate, not on a "prefer weak" default (per README's explicit caveat).

## R1-4 — During vs Post

**Chosen: During.** The relation is a branch-specific, statement-time value: `newQuote` right after line 187, inside the `Long` arm only. `@Post`'s `σ_exit` is a **joined** state across both branches (Long and Short merge before `return newPosition;`); evaluating `newQuote` there would blur it with the Short branch's already-correct value, which is exactly wrong for a Long-only invariant. This is distinguished from the README's `SwordCrowdsale`/`CDP.update` precedent (assignment-shaped patches that became Post): those were function-wide, unconditioned directional facts about persistent state; here the relation is inherently conditioned on which branch executes, so Post's join works against it.

## R1-5 — Relation form

Inequality (upper bound) via the common-form `intentValue relOp intentValue` rule $(C_{\text{cmp}})$, inside `@During` (`ref(Γ)=σ_{pt}`). Not Entry-Exit ($P_{ee}$) since that rule compares the *same* expression at entry vs. exit, whereas here two *different* expressions are compared at the same point. Not forced to equality by the assignment-shaped patch (R1-5's explicit rule).

## R1-6 — Target annotation

Attachment point: immediately after `newQuote = position.quote - quoteChange + fee;` (line 187), inside the `Long` branch.

```solidity
if (trade.side == Perpetuals.Side.Long) {
    newBase = position.base + signedAmount;
    newQuote = position.quote - quoteChange + fee;
    // @During newQuote <= position.quote - quoteChange
} else if (trade.side == Perpetuals.Side.Short) {
    ...
```

All three identifiers are pre-existing, semantically meaningful in-scope values (a local, a struct-member access on a parameter, a local); no synthetic value, no concrete constant needing derivation, no mechanical transcription of the patch's `-fee` expression.

## R1-7 — Expressibility decision

- Values referenceable at the point: yes — `newQuote`, `quoteChange` (locals, live), `position.quote` (unmutated parameter member), all via `varRef → identifier subAccess*`.
- Arithmetic/relation representable: yes — subtraction + `<=` via `arithAdd`/$(C_{\text{cmp}})$.
- Observation point supported: yes — `@During` at a program point inside a specific branch is exactly `σ_pt`.
- No function call inside the `intentValue` — `getFee(...)` is called earlier to produce `fee`, but `fee` itself is not referenced in the selected annotation at all (only its sign mattered, established in R1-1/R1-3), so the call-avoidance question doesn't even arise here.

**Outcome: Expressible — Yes.**

## Usable/Unusable (§5)

**Usable** — all needed values are directly referenceable in-grammar at the annotated point; purely a representational-resources fact. **Value-level** (direct bound on a specific value, not an algorithm/ordering property).

## RQ2-A — Specification profile

*(Recounted per README §6's simplified rules — third refinement pass: (1) a called function is counted once as a unit under "Additional functions required," its own internal lines are no longer itemized into "Relevant statements"; (2) "Relevant control predicates" dropped as a separately-counted metric; (3) the formal operand-defining/soundness-justifying labeling dropped in favor of a plain inline note wherever a statement's relevance isn't obvious from the annotation text alone.)*

- **Relevant statements (6, all in `applyTrade`)**: lines 177–180 (define `signedAmount`, `signedPrice`, `quoteChange`, `fee`; `fee` — line 180 — doesn't appear in the relation text itself, it's included because it's the anchor point establishing that a fee value exists and gets computed by a call, which matters for the non-negativity argument that makes the bound valid), line 185 (`if (trade.side == Long)`, gates whether line 187 executes), line 187 (target statement itself — not self-substitution; the bound was derived independently from the fee-as-cost invariant, not by rewriting line 187 into itself). `getFee`'s own two internal lines are no longer itemized here — see "Additional functions required" below, where the same fact (`fee >= 0`) is now stated once, not twice.
- **Unique relevant values (10)**: parameters/members — `position.quote`, `trade.amount`, `trade.price`, `trade.side`, `feeRate` (5); locals — `signedAmount`, `signedPrice`, `quoteChange`, `fee`, `newQuote` (5). Unchanged by the recount — none of these were ever internal-only to `getFee`'s own body.
- **Additional functions required**: `getFee` (1) — a function of *this same contract* (`Balances`). Load-bearing (README §6 Step 1): the selected bound is only valid because `fee >= 0`, and that fact is established inside `getFee` (its `uint256` computation is non-negative by type construction; the subsequent `.toInt256()` cast preserves this on any execution that completes without reverting — see R1-3). Step 2: same-contract semantic context, not a generic library fact — counts normally toward context breadth.
- **Additional protocol/application-specific contracts/libraries required**: None. The only cross-code dependencies are same-contract (`getFee`, above) or generic library facts (the case notes immediately below), not an external protocol-specific contract or library.
- **Case notes (load-bearing but generic — pass README §6's Step-1 filter, excluded from counted metrics at Step 2, not the same as "not needed")**:
  - `PRBMathUD60x18`/`PRBMathSD59x18` — their `mul` on non-negative operands yields non-negative results, one link in the `fee >= 0` chain (see R1-3's precision-scoped statement). Protocol-independent fixed-point-arithmetic fact, would hold identically in any contract using these libraries.
  - The `.toInt256()` cast inside `getFee` — R1-3's discrimination argument explicitly depends on this cast reverting (rather than silently wrapping) on overflow; genuinely load-bearing (Step 1: yes, the argument would break if it wrapped instead), but generic safe-casting semantics with nothing Tracer-Protocol-specific about it (Step 2: case note, not counted). *(Corrected during the second refinement pass — the original text called this "boilerplate, not load-bearing," which mixed up the two questions; the accurate reason it's excluded from counted metrics is genericness, not irrelevance — see README §6.)*
- **Context breadth**: 2 (other function in same contract — `getFee` — needed only to justify the bound's soundness; the operands themselves are same-function, breadth 1). The PRBMath library fact above does not raise this per the case note above. Separately, R1-1's intent reconstruction drew on the report's cross-reference to `TracerPerpetualSwaps.sol` L272 (not available locally, not needed beyond the report's own text) — noted as report-level corroboration, not folded into the breadth score.
- **External specification required**: No. *(Per README §6, R1-1's use of the audit report is excluded from this field by definition — every case uses the report, so its use is never evidence either way here.)* The question is narrower: once R1-1/R1-2 already establish the intended behavior (fee is a cost, must reduce `newQuote`), does justifying *this specific relation* need protocol/business convention beyond source code + language semantics? No — the bound follows from `fee`'s own in-contract definition and type/cast semantics alone.

## Summary

- **Expressible: Yes.**
- **Target annotation**: `// @During newQuote <= position.quote - quoteChange`, attached immediately after line 187 (inside the `Long` branch of `applyTrade`).
- Value-level, Usable, During, inequality/bound form.
- **Quantified property instantiated: No** — the relation targets a single trade's `newQuote`, not a collection-quantified property; no instantiation-on-a-representative-element issue here.
- Alternatives considered at R1-3: directional (rejected, non-discriminating), bound (selected), known-bound-rescue variant (collapses into bound, no distinct case here), exact equality (rejected, over-specific with no added discrimination).
- RQ1-B/RQ2-B: deferred, not run in this pass.
