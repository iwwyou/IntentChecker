# web3bugs_3_H_04 — Agent A (Analyst) Case Analysis

Case ID: `web3bugs_3_H_04` | Contract: `HourlyBondSubscriptionLending` (Marginswap) | Function: `viewHourlyBondAmount(address issuer, address holder) public view returns (uint256)`
Existing label: H-04, "Inconsistent usage of `applyInterest`" (Code4rena contest 3). No explicit sponsor-confirmation line is present in the report text for this finding (unlike some other findings in the same report); this does not affect the analysis, which relies on the report's own arithmetic argument, not on confirmation status.
Source: `evaluation/RQ1/target_contracts_original/web3bugs_3_H_04.sol`; Report: `C:\Users\isjeon\Web3Bugs\reports\3.md`, finding `[H-04]` (§0.5 — cross-checked against the scattered `Dataset/Web3Bugs/S6_2/contest_3_H_04/README.md`, which is byte-for-byte consistent with the primary source for this finding — no truncation found).
Reported bug lines (local numbering in `target_contracts_original/web3bugs_3_H_04.sol`): 95–97 (the `return bond.amount + applyInterest(...)` statement).

*(Background only, not used as a starting assumption per the task framing: this case was previously labeled under the retired L1a "loop-widening" taxonomy — specifically `evaluation/RQ1/annotation_plans.md`'s `not_detectable (L1a: loop-widening-precision-loss)` entry for this case, whose stated reason is that the needed value `cumulativeYield` is computed through `calcCumulativeYieldFP`'s `for` loop, and the old engine's fixpoint/widening over that loop was judged too imprecise to validate the annotation. R1-7 below explicitly re-examines this claim under the current methodology, including checking it against the confirmed `delta` loop-body-`@During` exception (README §4) — see R1-7.)*

## R1-1 — Reported Behavior Reconstruction

**Contract/function role**: `HourlyBondSubscriptionLending` (abstract, part of Marginswap's lending stack, `is BaseLending`) manages auto-renewing hourly bonds — depositors lock funds for most of each hour and earn floating interest tracked via a fixed-point (`FP32 = 2**32`, inherited from `BaseLending`) accumulator-ratio scheme: a bond records `yieldQuotientFP`, the accumulator's value at the moment the bond was (re)created, and interest owed is derived by comparing that stored value against the *current* accumulator value. `viewHourlyBondAmount(issuer, holder)` is the public, `view`-only read path a caller uses to see a bond's current interest-inclusive balance without mutating state.

**Relevant locals/state** (all inside `viewHourlyBondAmount`):
- `bond` (line 85) = `hourlyBondAccounts[issuer][holder]` — storage pointer to the bond record (`HourlyBond{amount, yieldQuotientFP, moduloHour}`).
- `yieldQuotientFP` (line 86) = `bond.yieldQuotientFP` — the accumulator value snapshotted when this bond's principal was last set.
- `cumulativeYield` (lines 88–92) = `viewCumulativeYieldFP(hourlyBondMetadata[issuer].yieldAccumulator, block.timestamp)` — the *current* accumulator value, view-computed by walking `calcCumulativeYieldFP` (linear sub-hour interpolation plus a `for`-loop compounding one multiplicative step per whole elapsed hour — see R1-7 for why this loop does not end up mattering to this case's verdict).
- `bond.amount` (state) — the bond's recorded principal.
- **The disputed statement (lines 94–98)**:
  ```solidity
  if (yieldQuotientFP > 0) {
      return
          bond.amount +
          applyInterest(bond.amount, cumulativeYield, yieldQuotientFP);
  }
  return bond.amount + 0;
  ```

**What `applyInterest` actually computes** (`Dependencies/BaseLending.sol`/`evaluation/RQ1/target_contracts_original/dependencies/BaseLending.sol`, lines 31–38, inherited into `HourlyBondSubscriptionLending` via `is BaseLending`):
```solidity
function applyInterest(uint256 balance, uint256 accumulatorFP, uint256 yieldQuotientFP)
    internal pure returns (uint256)
{
    // 1 * FP / FP = 1
    return (balance * accumulatorFP) / yieldQuotientFP;
}
```
This is a *ratio* formula: `balance × (accumulatorFP / yieldQuotientFP)`. *(A monotonicity claim — "accumulators only grow, so this ratio is always ≥ 1" — was dropped here on review: it isn't needed for, and isn't independently established anywhere this analysis actually checks, given `calcCumulativeYieldFP`'s own internals are excluded as non-load-bearing below (RQ2-A) — leaning on an unverified property of that same excluded function would be inconsistent. The conclusion below doesn't need it anyway — the in-file usage-pattern evidence immediately following is sufficient on its own.)* `applyInterest`'s return value is **already the new, interest-grown balance**, not a bare interest *delta* — established directly by how it's used, not by reasoning about its formula's range.

**Within-file corroborating evidence for this reading** — the report's own point ("It is unclear if `applyInterest` is supposed to return a new balance... or only the accrued interest... some calls add the return value to the old amount [and] some not") is independently confirmed *inside this same target file*, without needing to consult any contract outside `target_contracts_original/web3bugs_3_H_04.sol`: `updateHourlyBondAmount` (lines 59–77), the function that actually *mutates* `bond.amount`, uses the direct-assignment convention:
```solidity
uint256 oldAmount = bond.amount;
bond.amount = applyInterest(bond.amount, yA.accumulatorFP, yieldQuotientFP);   // line 68 — treats applyInterest's result as the full new balance
uint256 deltaAmount = bond.amount - oldAmount;                                 // delta is computed *separately*, afterward
```
`updateHourlyBondAmount` only derives `deltaAmount` *after* assigning `applyInterest`'s result directly into `bond.amount` — if `applyInterest` returned a bare delta, this line would double-count in the opposite direction from `viewHourlyBondAmount`'s bug. The fact that `deltaAmount` is computed as `newAmount - oldAmount` (not used as an addend) is only consistent with `applyInterest` returning the full new balance. (The report's own second quoted usage snippet, `balanceWithInterest = applyInterest(balance, yA.accumulatorFP, yieldQuotientFP);`, is verbatim `Lending.sol`'s `applyBorrowInterest`, outside this case's target file — used here only as additional corroboration, not as a required source; the in-file `updateHourlyBondAmount` comparison alone is sufficient and is the evidence actually relied on below.)

**Reported erroneous behavior** (report, verbatim): "It is unclear if the function `applyInterest` is supposed to return a new balance with the interest applied or only the accrued interest... This makes the code misbehave and return the wrong values for the balance and accrued interest." The report quotes exactly the buggy statement (`return bond.amount + applyInterest(bond.amount, cumulativeYield, yieldQuotientFP);`) as the "adds the return value to the old amount" case.

**Variable-value intent (lines 95–97)**: `viewHourlyBondAmount`'s return value must equal the interest-grown balance itself — `applyInterest(bond.amount, cumulativeYield, yieldQuotientFP)` — not that value plus a second, redundant copy of the un-grown principal.

**Statement/line-level intent**: the function is supposed to report the same interest-inclusive balance concept that `updateHourlyBondAmount` actually *commits* to storage; the `view` path exists precisely so a caller can preview that committed value without paying gas for a state write.

**Expected/intended behavior**: `viewHourlyBondAmount(issuer, holder) == applyInterest(bond.amount, cumulativeYield, yieldQuotientFP)` when `yieldQuotientFP > 0` (the branch actually exercised for any bond that has been created at least once); the extra `bond.amount +` term should not be there.

**Patch intent**: the report gives no diff/PR-style patch, only the general recommendation "make it consistent in all cases when calling this function." This is weaker evidence than a literal patch, but it directly names the abstraction used above (consistency with the non-additive usage) — R1-3 below constructs the target relation from the in-file `updateHourlyBondAmount` convention and `applyInterest`'s own definition, not by guessing at unstated patch syntax.

**Bug-relevant intended numeric behavior**: for any bond with `yieldQuotientFP > 0`, `viewHourlyBondAmount` must return exactly `applyInterest(bond.amount, cumulativeYield, yieldQuotientFP)` (`= bond.amount × cumulativeYield / yieldQuotientFP`); the current code instead returns `bond.amount` plus that value, roughly doubling the reported balance whenever meaningful interest has accrued.

## R1-2 — Intent Abstraction

Distinguishing property (patch syntax dropped — there is none to drop beyond the general recommendation): the returned balance must equal the interest-application formula's own output, not that output plus an extra, redundant `bond.amount` term. **Intent-level orientation: Value-centered** — a constraint on the function's return value (`returnExpression`), not a state-transition claim (the function is `view`; nothing persists across the call).

## R1-3 — Select the least implementation-specific sufficient relation (alternatives recorded, §7)

**Preliminary check — does this relation need a function call inside `intentValue`?** The natural statement of intent is "`returnExpression` equals `applyInterest(bond.amount, cumulativeYield, yieldQuotientFP)`," and the grammar's `intentValue` (`arithExpr`, `Parser/Solidity.g4`) has no call syntax at all — only literals, `varRef`s (with member/index/snapshot-qualifier access), parenthesized arithmetic, `+ - * / % **`. This looks like it could force an alpha (function-call) blocker. It does not: `applyInterest` is a `pure`, single-expression helper (`(balance * accumulatorFP) / yieldQuotientFP`, `BaseLending.sol` lines 31–38) — its entire behavior *is* that one arithmetic expression, so it can be inlined verbatim as ordinary `arithExpr` arithmetic (`(bond.amount * cumulativeYield) / yieldQuotientFP`) rather than called. This is a stronger position than README's Nokon-style "known-bound rescue" (which substitutes a *bound* for an *unknown* call result) — here the call's *exact* formula is known and trivially expressible, so no bound/approximation is needed at all, and R1-3's "known-bound rescue" check is satisfied a fortiori.

1. **Directional (weakest tier)**: not naturally applicable. `viewHourlyBondAmount` is `view`, so there is no entry/exit state-transition to bound directionally, and the reported defect is a fixed, deterministic over-count (not an ordering/monotonicity property across calls) — the same "not applicable" situation `34_H_01`/`71_H_11` recorded for their pure/pure-adjacent functions.
2. **Inequality (upper bound)**: `returnExpression <= (bond.amount * cumulativeYield) / yieldQuotientFP`. **Expressible, and discriminates** (see arithmetic below: buggy value is always `>=` intended, with equality only in the degenerate case `bond.amount == 0`, since the bug is literally "add a non-negative extra term"). **Not selected**: the true intended value is not naturally a bound — it is a single, exactly-determined quantity (`applyInterest`'s formula applied to three already-known in-scope operands), so an inequality buys no independence from the patch's arithmetic that the equality doesn't already have (both reference the identical RHS expression; per README's explicit caution, operator strength alone does not measure implementation-specificity). Using a bound here would also *understate* the reported intent: the report's actual complaint is a specific inconsistency between two usages of the same value, not merely "don't return more than X."
3. **Exact equality (SELECTED)**: `returnExpression == (bond.amount * cumulativeYield) / yieldQuotientFP`. Matches the value R1-1's in-file evidence establishes as correct exactly, discriminates (below), and every operand (`bond.amount`, `cumulativeYield`, `yieldQuotientFP`) is a pre-existing, semantically meaningful, already-computed in-scope value — no synthetic constant, no literal transcription of the patch (there is no patch text to transcribe from).

**Required check (§3/R1-3)**: does this equality's negation fail to catch some alternative implementation that retains the *reported* defect — the redundant re-addition of `bond.amount` on top of `applyInterest`'s already-grown balance — but produces it differently? **No gap**: the reported defect is, by its nature, "an extra additive `bond.amount` term is present that shouldn't be" — regardless of how that extra term is algebraically arranged or reached (written as `bond.amount + applyInterest(...)` verbatim, or any equivalent rearrangement that still nets out to adding `bond.amount` on top of the correct value), the result differs from `(bond.amount * cumulativeYield) / yieldQuotientFP` by exactly `bond.amount` whenever `bond.amount > 0` (shown generally below), so the exact equality catches every such variant. *(A different hypothetical bug — swapping `applyInterest`'s last two arguments, i.e. `bond.amount * yieldQuotientFP / cumulativeYield` — is also caught by this relation whenever `cumulativeYield ≠ yieldQuotientFP`, but that's a separate, differently-shaped defect (a wrong ratio direction, not a redundant addition), not the reported one; noted only as an incidental additional catch, not used as the basis for this check, revised on review since citing an unrelated bug as the primary "no gap" evidence didn't actually target the required question.)* No alternative-defect gap was found for this relation; unlike some other cases in this batch, the exact-equality selection here does not need an `Intent coverage: Partial` flag on this specific ground (see RQ2-A / summary for the final coverage call, which is Full).

**Winner: Alternative 3 (exact equality).**

**Discrimination check (explicit arithmetic, per §9 checklist item 1).** Scenario: `bond.amount = 1000`, `yieldQuotientFP = FP32 = 4294967296` (accumulator value at bond creation — baseline growth factor 1.0×), `cumulativeYield = 2 × FP32 = 8589934592` (accumulator has since doubled — growth factor 2.0×, a legitimate output of `calcCumulativeYieldFP` for a large-enough elapsed time/rate, though the specific derivation is not load-bearing here — see R1-7).
- `applyInterest(1000, 8589934592, 4294967296) = (1000 × 8589934592) / 4294967296 = 2000`.
- **Buggy** (current code): `return = 1000 + 2000 = 3000`. Check: `3000 == 2000` → **false ⟹ Violated.**
- **Intended** (consistent with `updateHourlyBondAmount`'s convention): `return = 2000`. Check: `2000 == 2000` → **true ⟹ Satisfied.**

General argument (not just this one scenario): buggy `= bond.amount + applyInterest(...)`, intended `= applyInterest(...)`; buggy `−` intended `= bond.amount ≥ 0`, with equality (no observable bug) only when `bond.amount == 0` — a degenerate case with no bond to view in the first place. For any bond with nonzero principal, the two values differ and the relation is violated on the buggy code.

## R1-4 — During vs Post

**Chosen: Post.** The relation concerns `returnExpression` — R1-4's own listed Post category ("the relation concerns... a return value") applies directly, not by default but because that is exactly the quantity R1-2 identifies as the constrained value. There is no meaningful During reading here: `bond.amount`, `cumulativeYield`, and `yieldQuotientFP` are all already-settled by the time the `return` executes (nothing mutates after), so a `@During` immediately before the `return` and a `@Post` evaluated at exit would observe identical values — Post is chosen because it is the semantically appropriate scope for "the value this call reports," not because the patch is single-statement-shaped (no patch statement exists to be shaped by) and not because R1-4's "function-level consequence" language is being applied loosely.

## R1-5 — Relation form

Exact equality via the `returnExpression`-specific common-form rule: `commonClause: 'returnExpression' relOp intentValue # ReturnExprCmp`. Not a call-argument or Entry/Exit form — no snapshot-qualified references are needed (nothing changes across the function; `view`, no state mutation), unlike `42_H_01`/`35_H_11`'s use of the new `varRef(Entry)`/`varRef(Before)` extension for genuinely before/after-conditioned relations.

## R1-6 — Construct the target annotation

**Attachment point**: inside the `if (yieldQuotientFP > 0)` branch (lines 94–98), immediately after the disputed `return` statement — the textual placement convention used elsewhere in this project's `@Post` write-ups (e.g. `42_H_01`) even though `@Post`'s semantics evaluate at `σ_exit`.

**Scenario precondition this instantiation relies on (README's scenario-conditioning note, §4/R1-7)**: the relation as written is conditioned on `yieldQuotientFP > 0` — the exact branch condition already present in the source. This is not a cosmetic restriction: with `yieldQuotientFP == 0` (the `else` branch, `return bond.amount + 0;` — an untouched/never-funded bond record), the RHS `(bond.amount * cumulativeYield) / yieldQuotientFP` divides by zero and is undefined; that branch is not part of the reported bug (`applyInterest` is never invoked there) and the annotation is not intended to characterize it. This mirrors `42_H_01`'s zero-baseline scenario-conditioning (§4's general note that most During/Post relations in this benchmark hold given stated preconditions, not as bare unconditional invariants) — the concrete debug/batch scenario used at RQ1-B time (deferred) would pin `yieldQuotientFP` to a nonzero value, keeping this branch the only one exercised.

**Target annotation**:
```solidity
HourlyBond storage bond = hourlyBondAccounts[issuer][holder];
uint256 yieldQuotientFP = bond.yieldQuotientFP;

uint256 cumulativeYield =
    viewCumulativeYieldFP(
        hourlyBondMetadata[issuer].yieldAccumulator,
        block.timestamp
    );

if (yieldQuotientFP > 0) {
    return
        bond.amount +
        applyInterest(bond.amount, cumulativeYield, yieldQuotientFP);
    // @Post returnExpression == (bond.amount * cumulativeYield) / yieldQuotientFP
}
return bond.amount + 0;
```
All referenced identifiers (`bond.amount`, `cumulativeYield`, `yieldQuotientFP`) are ordinary in-scope values at the function's exit — a storage-struct field access, a local holding a prior call's already-materialized result, and a local copy of another storage field, respectively. No synthetic constant is introduced (contrast with README's `900`/Nokon-style derived-constant guidance, which does not apply here since every operand is a live program value, not a scenario-specific literal).

**Quantification note**: the property is naturally per-bond (one `(issuer, holder)` pair, the function's own parameters) — not a claim quantified over a stored collection of co-existing elements (contrast `web3bugs_83_H_01`'s "every pool" case). No representative-element instantiation issue applies; `issuer`/`holder` are ordinary function parameters, not a chosen element out of a mapping/array the annotation itself has to range over.

## R1-7 — Expressibility decision

**Values referenceable at a legal program point**: Yes. `bond.amount` (struct field via a storage pointer local), `yieldQuotientFP` (local), and `cumulativeYield` (local, holding an already-completed call's result) are all ordinary in-scope identifiers at the function's exit — nothing needed here is behind an external contract boundary or missing a proxy.

**Arithmetic/logical relation representable**: Yes. `(bond.amount * cumulativeYield) / yieldQuotientFP` is ordinary `arithExpr` (multiplication then division, both within `arithTerm`), and `returnExpression == ...` is the grammar's dedicated `ReturnExprCmp` common-form rule.

**No function call inside `intentValue`**: confirmed not an issue (R1-3's preliminary check) — `applyInterest`'s entire body is inlined as arithmetic since it is a one-line pure formula, not merely bounded.

**Observation point supported — explicit check against the confirmed `delta` (loop-body-`@During`) exception, per the task's instruction to verify this independently rather than assume the old L1a label's conclusion or copy `71_H_11`/`34_H_01`'s outcome.** The old pipeline's `annotation_plans.md` entry for this exact case argues *not_detectable* specifically because `cumulativeYield` is computed via `calcCumulativeYieldFP`'s `for` loop (compounding once per elapsed hour), and its fixpoint/widening treatment of that loop was judged too imprecise. Checking this against the current methodology's two, now-separated questions:
  - **Is the *old* argument (widening imprecision) in scope for R1-7 at all?** No — README §4 is explicit that R1-7 does not consider "whether the engine can validate it" or "whether abstract interpretation would produce ⊤"; that is an RQ1-B (Engine Validatability) question, deferred (§8). The old L1a label conflated exactly this (an engine-precision claim) with expressibility, which is the general mistake this session's restructuring exists to correct (README §0) — not a case-specific coincidence.
  - **Does the one confirmed, source-verified R1-7 exception (delta: a `@During` whose only viable attachment point is inside a loop body is never evaluated at all, `Interpreter/Engine.py`) apply here regardless?** No, and this is a structurally different situation from `71_H_11`/`34_H_01`, checked directly rather than assumed: this case's target relation is a **`@Post`** attached to `viewHourlyBondAmount`, evaluated at that function's own exit — a program point that is not inside any loop (`viewHourlyBondAmount` itself contains no loop at all). The loop lives inside `calcCumulativeYieldFP`, a *different* function, two call-hops away (`viewHourlyBondAmount` → `viewCumulativeYieldFP` → `calcCumulativeYieldFP`), and it has already fully executed and returned by the time `cumulativeYield` is used in our relation — the relation only ever references `cumulativeYield` as an already-materialized local, exactly the way `71_H_11`'s Alternative 2/3 treated `_deductionFromIndex`/`_shareOfIndex` as materialized locals without needing to attach anything inside their own computation. The delta exception is specifically about an annotation's *own* attachment point being inside a loop body (`_process_during_annotations` never being reached for loop-interior nodes) — it says nothing about whether one of the annotation's *operands* was, several calls earlier, itself produced by a function that happens to contain a loop. **Delta does not apply.**
  - Whether the *engine*, at RQ1-B time, can precisely propagate `cumulativeYield`'s value across two internal call boundaries (through a loop-containing callee) without widening to a useless interval is a real, separate, and legitimate question — but it is an RQ1-B precision/call-return-propagation question, not an R1-7 fact, and is flagged below as a caution for that later, deferred track rather than folded into this verdict.

**Outcome: Expressible = YES.**

## §5 — Value/Algorithm and Usable/Unusable

- **Value-level** — per the paper's own classification (`main.tex`, §"Value-level errors---logic errors at the value level: a wrong operator, a swapped identifier, or truncation that produces a numerically incorrect result"): the reported defect is precisely a wrong/extra operator (a spurious `+ bond.amount` term applied to an otherwise-correct formula), not a structural/ordering defect — no missing procedure call, no absent state update, no reordering. This is the textbook Value-level pattern.
- **Usable** — every value the relation needs (`bond.amount`, `cumulativeYield`, `yieldQuotientFP`) is referenceable, as an ordinary in-scope identifier, at the annotation's program point; nothing is behind an external-contract boundary or otherwise unreachable (§5, purely a representational-resources question, independent of R1-7's engine-precision caution above).

## RQ2-A — Specification Requirements profile

**Relevant statements** (within `viewHourlyBondAmount` itself; the call to `viewCumulativeYieldFP`/`calcCumulativeYieldFP` is treated atomically per README §6 — see "Additional functions required" below for why its own internal loop is not drilled into, and is in fact not load-bearing at all):
1. `HourlyBond storage bond = hourlyBondAccounts[issuer][holder];` (line 85) — defines `bond`, whose `.amount` field is an operand of the relation.
2. `uint256 yieldQuotientFP = bond.yieldQuotientFP;` (line 86) — defines `yieldQuotientFP`, an operand and the branch-gating condition's own subject.
3. `uint256 cumulativeYield = viewCumulativeYieldFP(hourlyBondMetadata[issuer].yieldAccumulator, block.timestamp);` (lines 88–92) — defines `cumulativeYield`, an operand; the statement itself (including its two call arguments) is counted, but the callee's own internal computation is not (see below).
4. `if (yieldQuotientFP > 0) { ... }` (line 94) — control-gating statement: determines which branch (and therefore which return expression) executes; the relation is scoped to this branch (R1-6's scenario-conditioning note).
5. `return bond.amount + applyInterest(bond.amount, cumulativeYield, yieldQuotientFP);` (lines 95–97) — the disputed/target statement itself: read as context to identify the annotation's attachment point and subject, not as self-justifying evidence for the relation (its own literal formula is not "self-substituted" into the target relation — the target relation is derived independently, from `applyInterest`'s definition and `updateHourlyBondAmount`'s corroborating usage, and only *compared against* this statement).

Total: **5 relevant statements.** (`updateHourlyBondAmount`'s line 68, used in R1-1 purely to *discover* the intended convention, is not counted — per README §3/§6, evidence that only helps identify the intended behavior, without the selected relation's own validity depending on it, is excluded, the same way the audit report itself is never counted.)

**Unique relevant program values** (within the statements above) *(revised on review — `returnExpression` no longer separately counted)*:
- Parameters: `issuer`, `holder` (2)
- State: `bond.amount`, `bond.yieldQuotientFP` (read once, into `yieldQuotientFP`), `hourlyBondMetadata[issuer].yieldAccumulator` (3)
- Local: `bond` (storage pointer alias), `yieldQuotientFP`, `cumulativeYield` (3)
- Global: `block.timestamp` (1)

Total: **9 unique relevant program values.** **General rule applied** (README §6, added this session): `viewHourlyBondAmount` declares a bare, unnamed return (`returns (uint256)`), so the target relation's `returnExpression` is the grammar's `C_ret` synthetic reference to the already-counted target statement (5) itself, not an independently-defined program value — it has no declaration/definition site of its own to trace. (Contrast a named return variable, e.g. `web3bugs_52_H_04`'s `returns (uint256 result)` — there, `result` stays counted as a genuine local.)

**Additional functions required**: **1** — `applyInterest` (`BaseLending.sol`, inherited into `HourlyBondSubscriptionLending` via `is BaseLending`, i.e. a same-contract call after inheritance, not a separate deployed contract). **Semantic-dependency note**: the target relation's RHS, `(bond.amount * cumulativeYield) / yieldQuotientFP`, is `applyInterest`'s own body verbatim (`(balance * accumulatorFP) / yieldQuotientFP`) — the relation's derivation depends specifically on this being a *multiplicative ratio* formula (not, say, an additive delta); if `applyInterest`'s formula changed, the relation's RHS would need to change with it. This is exactly the "generic vs. protocol-specific" Step 2 distinction (README §6): `applyInterest` is Marginswap's own custom fixed-point interest-application convention (documented only by its own one-line comment and usage pattern), not a well-known external primitive (unlike, say, SafeMath's `.add()`) — it counts as a real dependency, not a case-note-only generic fact.

**`viewCumulativeYieldFP`/`calcCumulativeYieldFP` are explicitly *not* counted here** (Step 1, README §6): the target relation treats `cumulativeYield` purely as an opaque, already-materialized operand — its value is used exactly as-is on both the buggy and intended sides of the comparison. Applying the Step 1 operational test directly: if `calcCumulativeYieldFP`'s specific compounding formula (including its `for` loop) were changed to compute a *different* accumulator value — while remaining consistent with everything else already established about it (an FP32-scaled accumulator of the kind `applyInterest`'s second argument expects) — the target relation's derivation and validity would **not** change; the relation would still correctly discriminate the "extra `+ bond.amount`" bug for whatever value `cumulativeYield` ends up holding. This is a stronger exclusion than "inspected only in passing" — `cumulativeYield`'s value is genuinely used, but the specific *mechanism* that produced it (including the loop the old L1a label focused on) is not load-bearing to this relation at all, so per README §6's Step 1 it is excluded from the record entirely, not merely left uncounted as a case note.

**Additional protocol/application-specific contracts/libraries required**: **0.** `applyInterest` is reached via inheritance (`is BaseLending`), not a separately deployed contract or an imported library requiring its own understanding beyond "this is the formula" (already captured above); no interface/external-protocol boundary is crossed.

**Context breadth**: **2** (other function in the same contract, reached via inheritance — `applyInterest`). Not 1 (the relation is not target-statement/same-function-only, since it depends on a named external formula) and not 3 (no cross-contract/interface call is involved — inheritance is compile-time flattening, not a runtime cross-contract call).

**External specification required**: **No.** Everything the selected relation depends on — `applyInterest`'s formula, the FP32 fixed-point convention, and the in-file convention comparison against `updateHourlyBondAmount` — is derivable from the source code itself (this target file plus its directly inherited base contract) and ordinary arithmetic/language semantics; no protocol-external accounting/business convention had to be separately looked up.

## §7 — Alternatives-considered summary

| # | Relation | Tier | Expressible? | Discriminates? | Verdict |
|---|----------|------|---------------|-----------------|---------|
| 1 | Directional/monotonicity | Directional | N/A | N/A | Not applicable — `view` function, no entry/exit transition; defect is a fixed over-count, not an ordering property |
| 2 | `returnExpression <= (bond.amount * cumulativeYield) / yieldQuotientFP` | Inequality, upper bound | Yes | Yes | Rejected — intended value is exactly-determined, not naturally a bound; no added independence over equality |
| 3 | `returnExpression == (bond.amount * cumulativeYield) / yieldQuotientFP` | Exact equality | Yes | Yes | **Selected** |

## RQ1-B / RQ2-B

Deferred per README §8. Not run, not predicted. **Caution flagged for that later track** (not part of this verdict): although `viewCumulativeYieldFP`/`calcCumulativeYieldFP`'s internal loop is not load-bearing to the *selected relation's content* (RQ2-A above), the *engine's* ability to precisely propagate `cumulativeYield`'s concrete/interval value across two internal call boundaries (through a loop-containing callee) at RQ1-B execution time is a genuine, separate open question — this is exactly the kind of call-return-propagation-through-a-loop scenario the old L1a label's *engine-behavior* observation (as opposed to its now-rejected expressibility conclusion) may still be relevant to, and should be checked empirically rather than assumed either way when RQ1-B is run for this case.

## Summary

- **Expressible: Yes.** Values referenceable, arithmetic representable, observation point (`@Post` at `viewHourlyBondAmount`'s exit) supported — explicitly checked against, and found not blocked by, the confirmed `delta` loop-body-`@During` exception (README §4): the loop lives inside a different, already-returned callee, not at this annotation's own attachment point.
- **Target relation**: `returnExpression == (bond.amount * cumulativeYield) / yieldQuotientFP` (scenario-conditioned on `yieldQuotientFP > 0`, matching the source's own branch condition), attached `@Post` at `viewHourlyBondAmount`'s exit.
- **Quantified property instantiated: No** — the relation is per-`(issuer, holder)` bond, matching the function's own parameters; no collection/mapping-wide property had to be narrowed to one representative element.
- Value-level, **Usable**, `@Post`, exact-equality common-form (`ReturnExprCmp`).
- **RQ2-A profile**: 5 relevant statements, 9 unique relevant program values *(was 10 — `returnExpression` no longer separately counted, see RQ2-A above)*, 1 additional function required (`applyInterest`, same-contract via inheritance, semantic dependency noted above), 0 additional protocol contracts/libraries, Context breadth 2, External specification required: No. `viewCumulativeYieldFP`/`calcCumulativeYieldFP` (and its loop) explicitly excluded from all counts — inspected but confirmed not load-bearing to the selected relation (Step 1, README §6).
- **Old L1a label**: reclassified. The old `not_detectable (L1a: loop-widening-precision-loss)` conclusion rested entirely on an engine-precision argument about `calcCumulativeYieldFP`'s loop — out of scope for R1-7 under the current methodology (an RQ1-B question, deferred), and, independently, the loop turns out not to be load-bearing to the selected relation at all (RQ2-A), and is not at this annotation's own attachment point (so the confirmed `delta` exception, which *is* a legitimate R1-7 consideration, does not apply either). Both the general "engine-precision claims are out of scope for R1-7" point and the specific "is this a delta case" check were verified directly for this case rather than assumed from `71_H_11`/`34_H_01`'s outcomes.
- RQ1-B/RQ2-B: deferred, not run in this pass; one caution flagged above for whoever runs RQ1-B later (call-return propagation through `calcCumulativeYieldFP`'s loop is untested and could still produce a Warning rather than Violated, independent of this case's Expressible=Yes verdict).
