# web3bugs_59_H_04 — Agent A Analysis (R1-1 → R1-7, RQ2-A)

Methodology: `First Revision/phase_reviews/README.md` (current, non-superseded version).

## Case metadata

- **Case ID**: `web3bugs_59_H_04`
- **Contract**: `AuctionBurnReserveSkew` (Malt, contest 59)
- **Function**: `getPegDeltaFrequency()`
- **Source read**: `evaluation/RQ1/target_contracts_original/web3bugs_59_H_04.sol` (verbatim, lines 116–132 for the function; line 134–136 for `_getIndexOfObservation`)
- **Audit report**: `C:\Users\isjeon\Web3Bugs\reports\59.md`, H-04, "`AuctionBurnReserveSkew.getPegDeltaFrequency()` Wrong implementation can result in an improper amount of excess Liquidity Extension balance to be used at the end of an auction" (line 239 in that file). **Cross-checked against README §0.5's caution**: the scattered per-finding file `Dataset/Web3Bugs/S6_4/contest_59_H_04/README.md` was compared line-by-line against `Web3Bugs/reports/59.md`'s H-04 section — **identical, no truncation found** for this case (unlike `71_H_11`/`83_H_01`). The report contains no separate PoC/Recommendation section beyond the one inline sentence quoted below; there is nothing more to find upstream.
- **Existing prior-pipeline label** (historical, retired methodology, recorded for continuity only): `L1a loop-widening`. See R1-4/R1-7 below — the actual defect and selected relation turn out **not** to require any loop-interior observation point at all, so the old "loop-widening" framing does not describe what actually blocks (or, here, does not block) this case. This is exactly the possibility the task brief flagged: the old-classification bucket does not guarantee the case attaches inside a loop body the same way `71_H_11`/`34_H_01` did — see the explicit delta-exception check in R1-4 below.

---

## R1-1 — Reported Behavior Reconstruction

**Contract role** (brief, since it clarifies the semantics of the values involved): `AuctionBurnReserveSkew` decides, at the end of an auction, how much of the excess Liquidity Extension (LE) balance to burn vs. retain, based on a running measure of how often the protocol has recently needed active stabilization above vs. below peg (`pegObservations`, an array of 0/1 markers — 1 = "above peg" stabilization, 0 = "below peg").

**Function role**: `getPegDeltaFrequency()` computes a basis-points-scaled (×10000) frequency of "above peg" observations over the last `auctionAverageLookback` recorded observations (or fewer, if fewer than `auctionAverageLookback` observations have been recorded yet). Its result feeds `consult()`'s `skew` computation, which in turn feeds `getRealBurnBudget()`'s burn-amount decision — the report's own impact statement (`getRealBurnBudget`/downstream LE depletion) traces directly through this call chain.

**Relevant locals/state**:
- `count` (state, L31) — total number of observations recorded so far (monotonically incremented once per call to `addAbovePegObservation`/`addBelowPegObservation`).
- `auctionAverageLookback` (state, L25, default 10, settable) — the configured window size, i.e. how many of the most recent observations should be averaged.
- `pegObservations` (state array, L24) — circular buffer of 0/1 markers, pre-filled with zeros for `_period` slots at `initialize()` (L54-56), then overwritten circularly as observations accrue.
- `initialIndex` (local, L117, conditionally reassigned L120-122) — the loop's start index: `count - auctionAverageLookback` if `count > auctionAverageLookback`, else `0`.
- `total` (local, L124, accumulated L126-129) — sum of `pegObservations[index]` for `i` ranging `[initialIndex, count)`. **The number of terms actually summed is exactly `count - initialIndex`** (loop bound: `for (uint256 i = initialIndex; i < count; ++i)`).
- Return value (**the buggy statement, L131**): `total * 10000 / auctionAverageLookback`.

**Variable-value intent (L131, the return expression).** The returned frequency should equal `10000 × (total observations actually summed that were "above peg") / (number of observations actually summed)`. The denominator the code currently uses, `auctionAverageLookback`, is only correct when the loop actually summed `auctionAverageLookback` terms — true exactly when `count >= auctionAverageLookback` (in that regime `count - initialIndex == auctionAverageLookback`, verified algebraically below). When `count < auctionAverageLookback`, `initialIndex == 0` and the loop only summed `count` terms, not `auctionAverageLookback` — so dividing by the larger, not-yet-reached `auctionAverageLookback` understates the true average.

**Statement/line-level intent.** The function is trying to uphold: "the returned value is the basis-points average of exactly the observations the loop summed" — i.e. the denominator must track the *actual* number of terms summed, not the *configured target* window size.

**Reported erroneous behavior** (H-04, verbatim): "When `count < auctionAverageLookback`, at L131, it should be `return total * 10000 / count;`. The current implementation will return a smaller value than expected." Sponsor (`0xScotch`) confirmed and argued for *higher* severity ("could manifest in liquidity extension being depleted to zero"); judge raised to High.

**Expected/intended behavior**: for the branch `count < auctionAverageLookback`, the report's own recommendation is `total * 10000 / count`. For the untouched branch (`count >= auctionAverageLookback`), the current `/auctionAverageLookback` is not reported as wrong (and is in fact correct — see algebra below). Both branches are subsumed by a single general formula: **`total * 10000 / (count - initialIndex)`** — see R1-2/R1-3 for why this generalization is preferred over transcribing the report's branch-conditioned literal fix.

**Algebraic identity used throughout (verified directly, not patch-copied)**: `count - initialIndex == min(count, auctionAverageLookback)`.
- If `count > auctionAverageLookback`: `initialIndex = count - auctionAverageLookback` ⟹ `count - initialIndex = auctionAverageLookback`.
- If `count <= auctionAverageLookback`: `initialIndex = 0` ⟹ `count - initialIndex = count`.

So `count - initialIndex` is *always* exactly the number of loop iterations, and it equals `count` precisely in the reported buggy branch (`count < auctionAverageLookback` ⟹ `count <= auctionAverageLookback` ⟹ this case) and equals `auctionAverageLookback` (the code's current, in-that-branch-correct divisor) otherwise.

**Concrete scenario (constructed, not from the report — the report gives no PoC/patch section beyond the one-line fix)**: `auctionAverageLookback = 10` (the contract's own default, L25), `count = 3` (an early-lifecycle call, before the lookback window has filled — realistic and reachable, since `count` starts at 0 and only increments one at a time via `addAbovePegObservation`/`addBelowPegObservation`), observations recorded so far `pegObservations[0..2] = [1, 1, 0]` ⟹ `total = 2`, `initialIndex = 0` (since `3 > 10` is false).
- **Buggy**: `return total * 10000 / auctionAverageLookback = 2 * 10000 / 10 = 2000`.
- **Intended** (report's own formula for this branch): `total * 10000 / count = 2 * 10000 / 3 = 6666` (floor division).
- **General formula** (R1-2/R1-3, below): `total * 10000 / (count - initialIndex) = 2 * 10000 / (3 - 0) = 6666` — matches the report's branch-specific formula exactly, as expected from the algebraic identity above.
- Buggy (2000) vs. intended (6666): confirms "will return a smaller value than expected."

**Patch intent**: the report's fix is a literal single-line substitution, `/auctionAverageLookback` → `/count`, scoped to one branch (`count < auctionAverageLookback`). Used here as corroborating evidence only (§2/§3) — the general `count - initialIndex` form used below is *derived independently* from the loop's own bound structure, not transcribed from the report, and is strictly more general (it also covers the untouched branch with the same single expression, which the report's literal one-line fix does not attempt to do).

---

## R1-2 — Intent Abstraction

Governing question: the returned value must equal `10000 × total / (number of terms the loop actually summed)`, where "number of terms actually summed" is a quantity already fully determined by two already-computed in-scope locals (`count`, `initialIndex`) — not the *configured* lookback window size, which the current code uses instead.

**Orientation: value-centered** — a constraint on the return value (the buggy statement's own RHS/lvalue-equivalent), in terms of other already-materialized in-scope values. Not a state-transition claim (the function is `view`, has no persistent-state side effects).

---

## R1-3 — Select the least implementation-specific sufficient relation

1. **Directional/monotonicity relation**: e.g. "returnExpression increases as the proportion of above-peg observations among those summed increases." **Rejected — not discriminating.** This holds identically for both the buggy and the intended formula (both are monotonically increasing in `total` for fixed denominator); it says nothing about which denominator is used, so it cannot distinguish buggy from intended on any scenario. It also isn't really what "wrong denominator" is about.
2. **Trivial range bound**: `returnExpression <= 10000`. **Rejected — not discriminating.** True under both buggy and intended arithmetic (both are basis-points-scaled averages of a 0/1 sequence, hence always `<= 10000` and `>= 0`); says nothing about the divisor bug.
3. **Inequality tied to the correct denominator**: `returnExpression >= total * 10000 / (count - initialIndex)`. **Discriminates.** On the scenario above: intended holds with equality (`6666 >= 6666`, true); buggy fails (`2000 >= 6666`, false) — because the buggy divisor is always `>= count - initialIndex` (shown algebraically in R1-1), the buggy value is always `<=` the intended value, so this lower bound is violated exactly when the bug manifests (`count < auctionAverageLookback`) and holds with equality otherwise. **Viable candidate.**
4. **Exact equality (SELECTED)**: `returnExpression == total * 10000 / (count - initialIndex)`. Discriminates identically to (3) — same RHS expression, only the comparator differs. Per README's explicit caution (echoed in `34_H_01`'s R1-3 Alternative 5), operator strength alone does not establish implementation-specificity: since (3) and (4) share the exact same RHS, choosing `==` over `>=` buys no independence from the patch's arithmetic that `>=` didn't already have, and loses none either. What tips the choice to `==`: the intended quantity is, by its own nature, a *precise statistic* (a running average, scaled) — the report's own framing ("it should be X") describes an exact intended value, not merely a floor the actual value must clear. Equality is the semantically accurate claim here, not an over-specification (no rounding-mode ambiguity is being pinned arbitrarily — both sides use the same `total * 10000` numerator and ordinary integer division, so there's nothing extra `==` is fixing beyond what `>=` already fixes).
5. **Report's literal branch-conditioned fix**: `count < auctionAverageLookback → returnExpression == total * 10000 / count`. **Rejected in favor of (4).** This is what the report states, but restated directly it (a) requires an explicit conditional/branch structure in the annotation that the grammar's common forms don't need here, and (b) is strictly less general than (4) — it says nothing about the untouched branch, whereas `total * 10000 / (count - initialIndex)` is a single unconditioned expression that is correct (and non-trivially so, matching the *current, non-buggy* code) in both branches. Choosing (4) over (5) is the preferred, less-patch-specific abstraction per §2/§3's discipline: same discriminating power, strictly more general, and derived from the loop's own bound (`count - initialIndex` = iteration count) rather than copied from the patch's literal replacement.
6. **Known-bound/call rescue (Nokon-style, README R1-3)**: **not applicable.** There is no function call anywhere in the selected relation or in `getPegDeltaFrequency` itself (the one internal call, `_getIndexOfObservation`, is not load-bearing for this relation at all — see RQ2-A below) — no alpha-style blocker exists to rescue in the first place.
7. **Snapshot-qualified `varRef(Entry/Exit/...)` extension (README R1-3, this session's grammar addition)**: **not needed.** The relation needs only the *final* (σ_exit / Post) values of `total`, `count`, `initialIndex` — there is no before/after or entry/exit pairing of the *same* identifier anywhere in this relation (unlike `42_H_01`'s `debts == debts(Entry) + increasingDebt` or `35_H_11`'s `feeGrowthOutside1 == feeGrowthGlobal - feeGrowthOutside1(Before)`). A plain, ordinary `@Post` equality over already-in-scope locals/state suffices.

**Winner: Alternative 4** — `returnExpression == total * 10000 / (count - initialIndex)`.

**Discrimination check (explicit arithmetic, per §9 checklist item 1)** — see R1-1's worked scenario (`auctionAverageLookback=10, count=3, total=2`): buggy `2000`, intended/general-formula `6666`, relation false on buggy, true (equality) on intended. A second scenario in the *untouched* branch confirms the general formula doesn't wrongly flag correct behavior there: `auctionAverageLookback=10, count=15` ⟹ `initialIndex = 15-10=5`, loop sums 10 terms (`i=5..14`), say `total=6` ⟹ buggy `= 6*10000/10 = 6000`; general formula `= 6*10000/(15-5) = 6*10000/10 = 6000` — **identical**, relation holds (equality) on the current, already-correct code in this branch, as it should (no false positive).

**Required R1-3 sufficiency check (§3/R1-3's negation check)**: does this relation's negation fail to catch some alternative implementation that retains the reported defect but produces it differently? The reported defect is entirely a "which denominator does the final division use" defect, and this relation is an *exact* equality pinning the correct denominator directly — any implementation that used a wrong divisor (this one, or some other wrong divisor) would violate it; any implementation using the right divisor satisfies it, regardless of the internal mechanism used to arrive at `total`. The one thing this relation does **not** verify is whether `total` itself was accumulated correctly (i.e., whether `_getIndexOfObservation`'s circular-buffer indexing is correct) — but that is a *different*, unreported defect, not an alternative form of *this* reported one. See "Intent coverage" below for why this is judged Full, not Partial, given the reported defect is specifically and only about the denominator.

---

## R1-4 — During vs Post

**Relation-driven scope: Post.** The relation concerns the function's return value at exit — not an intermediate, statement-time value. `total`, `count`, `initialIndex` are all already-settled locals/state by the time the `return` statement executes; the relation only needs their final values, exactly what `@Post`'s `σ_exit` reference environment supplies. This is not chosen merely because the report describes a function-level consequence (R1-4's explicit caution) — it's chosen because the quantity being constrained (the returned frequency) is, by construction, only meaningful once, at `return`.

**Required explicit check (per task brief): does this case hit the confirmed loop-body-`@During`-never-evaluated exception (`delta`, README §4/R1-7), the way `71_H_11`/`34_H_01` did?** **No — and this is worth stating explicitly rather than assuming from the old `L1a loop-widening` label.** The buggy statement itself (`return total * 10000 / auctionAverageLookback;`, L131) is **not inside the `for` loop** — it is the statement immediately *after* the loop closes (L129 closes the loop body, L131 is the return, both inside the function but the return is unconditionally reached after the loop, never inside it). The only viable attachment point for the selected relation is `@Post` at function exit, which is categorically outside the loop-body-observation-point exception (that exception is specifically about `@During` annotations whose *only* viable attachment is inside a loop body; `@Post` is evaluated at σ_exit regardless of what control-flow structures the function body contains, and is unaffected by the fixpoint/`reinterpret_from()` mechanics documented in README §4). Unlike `71_H_11` (`_redeemAmount`, assigned and consumed *inside* the loop, no Post-reachable alternative) and `34_H_01` (the bug's own loop-mutated counter destroyed the only in-scope reference), here the defect's own location — the final division — was never inside the loop to begin with; the loop's only role for this relation is to *produce* `total`, a plain in-scope accumulator value referenced the same way any other pre-computed local would be. **Confirmed: delta does not apply to this case.**

(Separately, and out of scope for this R1-7/R1-4 expressibility question per README §4's explicit instruction not to consider engine precision here: the *engine's* fixpoint/widening treatment of the loop that produces `total` may still affect what value it computes for `total` at RQ1-B time — that is a precision/Warning question, addressed only as a forward-looking note below, not part of the Expressible verdict.)

---

## R1-5 — Relation form

**Exact equality**, via the grammar's dedicated return-value form: `commonClause -> returnExpression relOp intentValue` (`C_ret`, `paper/first_revision/main.tex` line 493), reached through `postClause -> commonClause`. Not forced to equality by the assignment/return-shaped statement (R1-5's explicit caution) — equality was selected in R1-3 on independent discrimination-vs-implementation-specificity grounds, and a documented, in-repo precedent for exactly this construction exists in the grammar reference itself: `@Post returnExpression == _balance - mapToken_tokenAmount[_token]` (`main.tex` line 1438, `Pools.getAddedAmount`).

---

## R1-6 — Construct the target annotation

**Attachment point**: `@Post` on function `getPegDeltaFrequency()` (placed immediately before the function's closing brace, after the `return` statement — a common-form `@Post` clause is evaluated against `σ_exit`, independent of exactly which line inside the function body it's textually placed on, following the same convention as `83_H_01`/`3_H_05`). `total`, `count`, `initialIndex`, and the return expression are all in scope at exit: `count` and `auctionAverageLookback` are contract-level `public` state variables (`varRef -> identifier`, always in scope); `total` and `initialIndex` are locals declared at the function's top level (not inside any nested block that closes before `return`), so both retain their settled values through to the closing brace.

**Target annotation:**
```solidity
function getPegDeltaFrequency() public view returns (uint256) {
    uint256 initialIndex = 0;
    uint256 index;

    if (count > auctionAverageLookback) {
      initialIndex = count - auctionAverageLookback;
    }

    uint256 total = 0;

    for (uint256 i = initialIndex; i < count; ++i) {
      index = _getIndexOfObservation(i);
      total = total + pegObservations[index];
    }

    return total * 10000 / auctionAverageLookback;
    // @Post returnExpression == total * 10000 / (count - initialIndex)
  }
```

No concrete numeric constant needed beyond the literal `10000` already present in the source itself (the same scaling constant the buggy code already uses) — the annotation introduces no new externally-derived number.

**Precondition, stated explicitly (added on review)**: the generalized denominator `count - initialIndex` is only evaluable — let alone valid — for executions with at least one recorded observation (`count > 0`). At `count = 0`, `initialIndex = 0` too (the `if (count > auctionAverageLookback)` guard is false), so `count - initialIndex = 0` and the annotation's RHS becomes a division by zero, even though the actual buggy code returns cleanly (`0 * 10000 / auctionAverageLookback = 0`, since `auctionAverageLookback` is never 0). The report's own recommended fix (`/count`) carries the identical implicit assumption — it is not a weakness specific to the generalized form selected here. This is not established as guaranteed by any caller/invariant inspected in this pass; treat `count > 0` as a precondition of the target relation (consistent with R1-1's own scenario, `count = 3`), not as a claim that the relation is a function-wide invariant for every reachable state. The `count = 0` boundary is a separate, unaddressed question unless the surrounding protocol establishes this precondition elsewhere.

---

## R1-7 — Expressibility decision

- **Values referenceable at a legal program point**: Yes. `total`, `initialIndex` (locals, unmodified after their respective assignment points through function exit), `count`, `auctionAverageLookback` (public state) are all directly referenceable via ordinary `varRef` at `σ_exit`. No function call inside `intentValue` — the one internal call in the function, `_getIndexOfObservation`, does not appear in the relation at all (see RQ2-A below for why it isn't load-bearing), so the R1-3 alpha/known-bound-rescue question doesn't even arise.
- **Arithmetic/logical relation representable**: Yes. `total * 10000 / (count - initialIndex)` is an ordinary `arithTerm`/`arithAdd` expression — multiplication, division, and a parenthesized subtraction are all directly supported by the grammar's `arithExpr`/`arithTerm`/`arithFactor` productions (`Parser/Solidity.g4` lines 346-375, confirmed by direct grammar read), and `returnExpression relOp intentValue` (`C_ret`) is a first-class `commonClause` form with an existing precedent in the grammar reference itself (`main.tex` line 1438).
- **Observation point supported**: Yes — `@Post`, evaluated at function exit. **Explicitly checked against the delta exception** (per task instructions, since this case's old classification bucket, `L1a loop-widening`, is the same bucket as two confirmed delta instances): the buggy statement and the selected relation's attachment point are both *after* the `for` loop closes, never inside its body — the loop's only role is producing the already-settled `total` value that `@Post` reads at `σ_exit`, exactly like any other pre-loop-computed local. The delta exception (README §4: `fixpoint()`/`reinterpret_from()` never evaluate a `@During` whose only viable attachment is inside a loop body) is about `@During` placement specifically; it does not apply to a `@Post` clause evaluated at function exit, regardless of what loops the function body contains upstream of that exit. **Confirmed not applicable here** — this case does not reduce to the `71_H_11`/`34_H_01` pattern, despite sharing their old `L1a` label.

**Outcome: Expressible = YES.**

*(Forward-looking note, out of scope for this Expressible verdict per README §4's explicit instruction not to consider engine precision at R1-7, recorded only for RQ1-B planning: the loop that produces `total` is still a `for` loop over a variable-length range, and this engine's fixpoint computation may widen/join `total`'s value across iterations when actually run — a precision question, not an expressibility one. If it does, the likely RQ1-B outcome is `Warning` rather than a clean `Violated`, similar to the loop-adjacent risk flagged for other cases in this batch (e.g. `42_H_01`'s non-view external call). This is a prediction for a later, deferred track, not a claim made here.)*

---

## §5 — Value/Algorithm and Usable/Unusable

- **Value-level** *(revised — was Algorithm-level; see rationale below)*: per the paper's own definition (`main.tex` L239-240 — Value-level = "a wrong operator, a swapped identifier, or truncation that produces a numerically incorrect result"; Algorithm-level = "operation ordering, an absent state update, or a missing procedure call"), the reported defect is exactly a **swapped-operand** case: the final division uses the wrong denominator identifier (`auctionAverageLookback` instead of `count - initialIndex`). The loop, the accumulation of `total`, and `initialIndex`'s conditional computation are all correct and untouched by the bug — the relation *references* these already-correct intermediate quantities, but nothing about their computation is what's wrong. The original "Algorithm-level" call conflated "the correct formula involves several intermediate quantities" with "the defect is structural" — these are different questions under the paper's test, and this case is the same pattern as `35_H_11`'s `feeGrowthOutside0` vs. `feeGrowthOutside1` (wrong field/operand selected, aggregation structure itself untouched), not `52_H_34`'s pre-upgrade case (which genuinely required restructuring the accumulation order, not just swapping one operand).
- **Usable**: every value the relation needs (`total`, `count`, `initialIndex`, the return expression itself) is referenceable in-scope at the annotation's program point (function exit). No representational gap of any kind.

---

## RQ2-A — Specification Requirements profile

**Relevant statements** (within `getPegDeltaFrequency` itself; §6's rule (a)/(b)/(c), no formal labeling required but noted inline where non-obvious):
1. `uint256 initialIndex = 0;` (L117) — initializes a value the relation directly references.
2. `if (count > auctionAverageLookback) { initialIndex = count - auctionAverageLookback; }` (L120-122) — **not** a bare reachability gate; this conditionally *redefines* `initialIndex`, an operand the relation's RHS (`count - initialIndex`) depends on. (a)-type, and the specific instance of the README §6 caution bullet ("a statement inspected to confirm reachability may also redefine a value the relation depends on") applying here.
3. `uint256 total = 0;` (L124) — initializes the accumulator the relation references.
4. `for (uint256 i = initialIndex; i < count; ++i)` (L126, loop header only) — (c)-type: establishes the independent fact the relation's soundness actually rests on, namely that the loop runs exactly `count - initialIndex` times. This is the fact that makes `count - initialIndex` the *correct* divisor in the first place (rather than an arbitrary re-derivation of the patch) — it is read directly off the loop's own bounds, not asserted.
5. `total = total + pegObservations[index];` (L128, loop body accumulation statement) — (a)-type, defines `total`'s settled value, which the relation references directly. Counted once as the statement that defines the accumulator; not expanded further (its own operand `index` is discussed in the exclusion note below).
6. `return total * 10000 / auctionAverageLookback;` (L131) — the disputed/target statement itself; counted as context establishing the annotation's attachment point and subject (per README §6's explicit clarification that this is required, distinct from the barred self-substitution-as-evidence practice — this statement's own literal arithmetic is not used as evidence for the relation, only its role as the thing being checked).

**Total: 6 relevant statements.**

**Excluded, with reason (not merely omitted)**: `index = _getIndexOfObservation(i);` (L127) and the callee `_getIndexOfObservation` itself (L134-136, `return _index % auctionAverageLookback;`). **Step 1 test (README §6)**: would the selected relation's derivation or validity change if `_getIndexOfObservation`'s specific behavior changed (e.g., a different, even incorrect, index-mapping formula)? **No.** The selected relation (`returnExpression == total * 10000 / (count - initialIndex)`) treats `total` as an already-materialized, opaque accumulator value — it asserts that the *final division* uses the correct denominator for whatever numerator resulted from summing `count - initialIndex` terms, and says nothing about which specific `pegObservations` entries were summed or whether the circular-buffer indexing itself is correct. Changing `_getIndexOfObservation`'s formula would change what `total` numerically *is*, but not whether the relation *holds* for that resulting `total`. Not load-bearing → excluded entirely per README §6 Step 1 (not counted as an "Additional function required," not even as a case note).

**Unique relevant program values** (within the annotated function's own scope, occurring in the statements counted above) *(revised on review — two general counting rules applied, README §6, added this session)*:
- State variables (3): `count`, `auctionAverageLookback`, `pegObservations`
- Locals (3): `initialIndex`, `total`, `index`

**Total: 6 unique relevant program values.** *(Was 8.)* Two corrections from the original list:
1. **`returnExpression` dropped.** `getPegDeltaFrequency` declares a bare, unnamed return (`returns (uint256)`), so `returnExpression` is the grammar's `C_ret` synthetic reference to the already-counted target statement (#6, the `return` line) itself — it has no independent declaration/definition site to trace, unlike a genuine named local/state variable. (Contrast a function with a *named* return variable, e.g. `web3bugs_52_H_04`'s `returns (uint256 result)` — there, `result` stays counted, since it's a real named local with its own identity.)
2. **`i` (loop index) dropped, not replaced.** A value reached via `container[index]` inside a counted statement is represented by the container and the extracted result, not the raw index — but unlike `52_H_04`/`52_H_34` (where `i` indexes `_pairs[i]` directly inside a counted, load-bearing statement), `i` here never appears in any counted statement except its own declaring loop header (#4) — its only other occurrence is inside the *excluded* `index = _getIndexOfObservation(i)` statement. `index` (the actual key used against the container `pegObservations`, already listed) and `pegObservations` (the container itself, already listed as a state variable) already cover this access path; there is no separate "extracted result" variable here the way `pairData` is in `52_H_04`/`52_H_34`, so nothing is added in `i`'s place.

**Additional functions required**: **0.** `_getIndexOfObservation` fails Step 1 (see above) and is excluded from the count entirely, not merely from "load-bearing" status.

**Additional protocol/application-specific contracts/libraries required**: **0.** The function uses plain `+`/`*`/`/` operators throughout (no `SafeMath` calls despite `using SafeMath for uint256;` being declared at the contract level — that library is used elsewhere in the contract, e.g. `consult()`/`getAverageParticipation()`, but not inside `getPegDeltaFrequency()` itself), so there is no generic-library dependency to even case-note here.

**Context breadth**: **1** (same-function context — every value the relation needs is defined within `getPegDeltaFrequency()` itself; no other function, contract, or external protocol convention is consulted).

**External specification required**: **No.** The relation is derivable entirely from the source code's own control/data flow (the loop's bound structure) and ordinary arithmetic — no protocol/business/domain convention beyond what's already legible in `AuctionBurnReserveSkew.sol` itself is needed to justify the selected relation.

---

## §7 — Alternatives-considered summary

| # | Relation | Tier | Expressible? | Discriminates? | Verdict |
|---|----------|------|---------------|-----------------|---------|
| 1 | Monotonicity of `returnExpression` in the above-peg proportion | Directional | Yes | No | Rejected — holds identically under buggy and intended arithmetic |
| 2 | `returnExpression <= 10000` | Trivial bound | Yes | No | Rejected — holds under both, says nothing about the divisor |
| 3 | `returnExpression >= total * 10000 / (count - initialIndex)` | Inequality, correct denominator | Yes | Yes | Viable, not selected |
| 4 | `returnExpression == total * 10000 / (count - initialIndex)` | Exact equality | Yes | Yes | **Selected** |
| 5 | `count < auctionAverageLookback → returnExpression == total * 10000 / count` | Branch-conditioned, patch-literal | Yes | Yes | Rejected — strictly less general than #4, requires branch structure the grammar doesn't need here |
| — | Known-bound/call rescue (alpha-style) | — | N/A | — | Not applicable — no call in the relation or the function to begin with |
| — | Snapshot-qualified `varRef(Entry/...)` extension | — | N/A | — | Not needed — no before/after or entry/exit pairing required, plain `@Post` on final values suffices |

## RQ1-B / RQ2-B

Deferred per README §8. Not run, not predicted (the loop-widening/`Warning`-risk note in R1-7 is a forward-looking caution for that later track, not a recorded outcome).

---

## Summary

- **Expressible: Yes.** Post-scope, exact equality (`C_ret` common form): `returnExpression == total * 10000 / (count - initialIndex)`, attached to `getPegDeltaFrequency()`.
- **Delta-exception check (required by task brief given the shared `L1a loop-widening` old-classification bucket with `71_H_11`/`34_H_01`): explicitly checked and confirmed NOT applicable.** The buggy statement and the selected relation's only viable attachment point are both the `return` statement immediately after the `for` loop closes — never inside the loop body. The loop's sole role for this relation is producing the already-settled `total` accumulator, referenced the same way any other pre-computed in-scope local would be at `@Post`. This case does not share `71_H_11`/`34_H_01`'s actual blocking mechanism despite the shared old label.
- **Value-level/Algorithm-level**: **Value-level** *(revised on review — was Algorithm-level; see §5)*. The defect is a swapped-denominator-operand error (`auctionAverageLookback` vs. `count - initialIndex`), matching the paper's own Value-level definition directly; the loop/accumulation structure itself is correct and untouched. The prior Algorithm-level call incorrectly equated "the correct formula combines several intermediate quantities" with "the defect is structural" — same pattern as `35_H_11`'s `feeGrowthOutside0`/`feeGrowthOutside1` mix-up (Value-level), not `52_H_34`'s pre-upgrade accrual-restructuring case (genuinely Algorithm-level).
- **Usable/Unusable**: Usable — every needed value is referenceable in-scope at function exit.
- **Precondition (added on review): `count > 0`.** The relation's RHS (`count - initialIndex`) is undefined (division by zero) at `count = 0`, unlike the actual buggy code, which returns `0` cleanly in that case since `auctionAverageLookback` is never 0. The report's own `/count` fix carries the same implicit assumption. Recorded as a scenario precondition (matching R1-1's own `count = 3` scenario), not as a claim that the relation is a function-wide invariant over every reachable state — see R1-6.
- **Quantified property instantiated: No.** The relation concerns one scalar return value for one call under one concrete `count`/`auctionAverageLookback`/`pegObservations` state; it does not instantiate any array/mapping-quantified reported property on a representative element (contrast `83_H_01`'s pool-selection pattern) — `pegObservations` is consulted only through the already-aggregated `total`.
- **RQ2-A profile**: Relevant statements = 6; Unique relevant program values = 6 *(revised on review, was 8 — see RQ2-A above: `returnExpression` and the loop index `i` no longer separately counted)* (3 state / 3 local); Additional functions required = 0 (`_getIndexOfObservation` excluded, non-load-bearing per Step 1); Additional protocol/library dependencies = 0; Context breadth = 1 (same-function); External specification required = No.
- **RQ1-B/RQ2-B**: deferred, not run in this pass. Forward-looking-only note: the loop producing `total` may be subject to fixpoint widening at engine-execution time, which is a precision question for RQ1-B (possible `Warning`), not a factor in this Expressible verdict.
