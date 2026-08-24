# web3bugs_3_H_05 — Agent A (Analyst) Case Analysis

Case ID: `web3bugs_3_H_05` | Contract: `CrossMarginAccounts` (abstract library-like contract) | Function: `belowMaintenanceThreshold(CrossMarginAccount storage account) internal returns (bool)`
Existing label: H-05, "Wrong liquidation logic" (Code4rena contest 3)
Source: `evaluation/RQ1/target_contracts_original/web3bugs_3_H_05.sol`; Report: `C:\Users\isjeon\Web3Bugs\reports\3.md`, section `## [[H-05] Wrong liquidation logic]`

## R1-1 — Reported Behavior Reconstruction

**Contract/function role**: `CrossMarginAccounts` holds the core cross-margin bookkeeping logic (borrowing, holdings, liquidation checks) for a `CrossMarginAccount` struct — deposits, borrows, and a liquidation gate. `belowMaintenanceThreshold` is the liquidation gate itself: it decides whether a given account may be liquidated by comparing its total holdings value against its total loan value, both expressed "in peg" (a shared reference currency), via the same-contract helpers `loanInPeg`/`holdingsInPeg`.

**Relevant locals (function body, lines 194-204)**:
```solidity
function belowMaintenanceThreshold(CrossMarginAccount storage account)
    internal
    returns (bool)
{
    uint256 loan = loanInPeg(account, true);
    uint256 holdings = holdingsInPeg(account, true);
    // The following should hold:
    // holdings / loan >= 1.1
    // =>
    return 100 * holdings >= liquidationThresholdPercent * loan;    // line 203 -- BUGGY
}
```
- `loan` (line 198) — total loan value of the account, in reference currency.
- `holdings` (line 199) — total holdings value of the account, in reference currency.
- `liquidationThresholdPercent` (state variable, declared line 35: "percentage of assets held per assets borrowed at which to liquidate") — the collateralization threshold, scaled by 100 (matching the `100 * holdings` scaling on the other side).
- The function's own comment (lines 200-202) states the intended safety condition directly: a healthy account satisfies `holdings / loan >= 1.1`; the `=>` signals that the return expression below is meant to derive from negating/complementing this ratio (the function's name is `belowMaintenanceThreshold`, so it should return true exactly when the *inverse* — the unhealthy condition — holds).

**Variable-value intent (line 203, whole `returnExpression`)**: the function should return `true` iff the account is *below* the maintenance threshold — the "1.1 => 110%" scaling itself is not in doubt (implied by the comment together with the code's own `100 *` factor) — but the exact boundary comparator is genuinely ambiguous between two sources, not settled by either alone: the source comment states the healthy condition inclusively as `holdings / loan >= 1.1`, whose strict logical complement is `holdings / loan < 1.1` (`100 * holdings < liquidationThresholdPercent * loan`); the report's own suggested fix instead reads `<=` (`return 100 * holdings <= liquidationThresholdPercent * loan;`, quoted below). Read together at face value, these two pieces of evidence disagree at the exact boundary (`holdings / loan == 1.1` would be simultaneously "healthy" per the comment's `>=` and "liquidatable" per the report's `<=`) — the benchmark itself doesn't settle which one is correct, and this record doesn't invent a resolution. **This ambiguity does not affect anything below**: R1-6's constructed scenario (`holdings/loan = 2.0`) sits far enough from the `1.1` boundary that `<` and `<=` agree on its classification, so the selected relation's discrimination is identical either way — the ambiguity is recorded for honesty about the general intended behavior, not because it threatens the selected annotation.

**Statement/line-level invariant**: liquidation should trigger when the account is under-collateralized relative to the configured threshold, never when it is safely over-collateralized — the comparison direction is the entire content of the invariant; there is no other logic in the function.

**Reported erroneous behavior** (audit report, verbatim): "The inequality in the last equation is wrong because it says the higher the holdings (margin + loan) compared to the loan, the higher the chance of being liquidated. The inverse equality was probably intended `return 100 * holdings <= liquidationThresholdPercent * loan;`. Users that shouldn't be liquidated can be liquidated, and users that should be liquidated cannot get liquidated."

**Patch intent** (evidence only, not transcribed): flip `>=` to `<=` on line 203 — evidence that the invariant is "return true exactly on the under-collateralized side," not evidence the annotation must read literally `<=` on the same operands.

**Bug-relevant intended numeric behavior**: `belowMaintenanceThreshold`'s return value must track the *under*-collateralized side of the `holdings` vs. `loan` comparison; the buggy code computes the comparison for the *over*-collateralized side instead, so the function's output is inverted relative to its own documented purpose.

## R1-2 — Intent Abstraction

Distinguishing property (patch syntax dropped): the boolean the function returns must equal "the account is under-collateralized" (`100 * holdings <= liquidationThresholdPercent * loan`), not its logical near-opposite. **Intent-level orientation: Value-centered** — a constraint on the function's own return value, not a broader multi-statement effect claim (there is only one meaningful statement in this function besides the two value definitions).

## R1-3 — Select the least implementation-specific sufficient relation (alternatives recorded, §7)

**Function-call check first (README's "before declaring alpha" step)**: `loan` and `holdings` are already-materialized locals by the time the target statement executes (defined at lines 198-199, unconditionally, strictly before line 203). The selected relation only needs to *reference* `loan`/`holdings`, never to *call* `loanInPeg`/`holdingsInPeg` inside the annotation itself — so the "external call whose result is otherwise unreachable" concern that motivated the old (retired) classification does not actually arise for the relation this pass selects. This is verified below, not assumed.

Alternatives considered:

1. **Bare accounting inequality, independent of `returnExpression`** (`100 * holdings <= liquidationThresholdPercent * loan`, asserted as a standalone fact about the account's state, without referencing the function's return value at all): **Rejected — does not discriminate.** `loan` and `holdings` are computed identically by the buggy and the patched code (the bug is confined to the return statement's comparison operator; nothing about how `loan`/`holdings` are computed changes). So this inequality's truth value is exactly the same whether the buggy or the fixed `belowMaintenanceThreshold` runs — it says nothing about whether the *function's output* is correct. Fails R1-3's condition (c): sufficient to reject buggy while accepting intended.
2. **Entry/Exit form on the return value** ($P_{ee}$, `intentValue (entry relOp exit)`): **Rejected — not applicable.** $P_{ee}$ compares the *same* expression's value at function entry vs. exit; a value computed only once, at the `return` statement, has no meaningful "entry" value to compare against (it does not exist until the function is nearly done). This rules out $P_{ee}$ on structural grounds, independent of discrimination.
3. **Fully general "iff" relation** (`returnExpression == (100 * holdings <= liquidationThresholdPercent * loan)`, holding unconditionally for all `loan`/`holdings`): this is, in principle, the least implementation-specific restatement of the reported intended behavior — it directly mirrors the function's own documented purpose with no scenario-specific numbers at all. **Rejected as inexpressible in the current grammar** (verified against `paper/first_revision/main.tex`'s `\label{fig:intent-grammar}`): `commonClause`'s comparison forms (`$C_{\text{cmp}}$`, `$C_{\text{ret}}$`) both require an `intentValue` (i.e. `arithExpr`) on each side; `arithFactor`'s alternatives are `number | [number,number] | varRef | (arithExpr)` — there is no production letting a relational sub-expression (`... <= ...`) appear as an operand of another comparison. A boolean comparison cannot be nested inside `intentValue`. This is a genuine, permanent grammar gap (structurally analogous to the collection-quantification gap the README already documents for R1-6, just over an arithmetic domain rather than an array/mapping), not a researcher's choice to weaken the claim.
4. **Return-value relation, under-collateralized scenario** (`returnExpression == 1`, instantiated at e.g. `loan = 1000, holdings = 900, liquidationThresholdPercent = 110`): discriminates (checked below, mirror-image of the selected scenario). Considered and valid, not selected only because scenario 5 more directly matches the report's own stated primary harm ("users that shouldn't be liquidated can be liquidated").
5. **Return-value relation, over-collateralized/healthy scenario** (`returnExpression == 0`, instantiated at `loan = 1000, holdings = 2000, liquidationThresholdPercent = 110`): **Selected.** Uses the grammar's `$C_{\text{ret}}$` form (`returnExpression relOp intentValue`) with `intentValue` a plain numeric literal (`0`, the boolean `false`'s only legal encoding under this grammar — there is no boolean-literal terminal, only `number`), no call inside the annotation, and no reuse of the patch's own `<=` operator syntax (the annotation compares a boolean outcome to a constant, not two arithmetic sides with the patched operator). Discriminates cleanly (arithmetic in R1-7).

**Selected**: `returnExpression == 0` under the constructed healthy-account scenario. It wins because it is the least implementation-specific form that is actually **expressible** (unlike (3)) and still **sufficient to discriminate** (unlike (1)), and it is picked over its mirror-image alternative (4) only because it matches the audit's own stated primary concern about wrongful liquidation of healthy accounts — a narrative-fit tiebreak between two otherwise symmetric, equally valid alternatives, recorded here per §7's transparency requirement.

**Precision note on "least implementation-specific" here**: implementation-specificity and scenario-specificity are different axes (README §3's definition of the former is about dependence on the *patch's exact arithmetic/statement structure*, not about how tied to one concrete precondition a relation is). `returnExpression == 0` scores well on the first axis — it doesn't reproduce the patch's `100 * holdings <= liquidationThresholdPercent * loan` structure or operator at all, just the boolean outcome — but it is highly scenario-specific (tied to one fixed `loan`/`holdings`/`liquidationThresholdPercent` combination), which is a direct, unavoidable consequence of (3)'s general form being inexpressible (R1-2's general property is narrowed to this one concrete instantiation precisely because the grammar can't state it generally — see R1-2's claim and R1-7's quantification note). "Least implementation-specific" should not be read as "general" here; the two are not the same claim.

## R1-4 — During vs Post

**Chosen: Post.** The relation concerns the function's own return value at function exit — exactly the case R1-4 lists as canonically Post ("a return value, a persistent state transition, a function-level invariant"). There is no branch structure and no intermediate statement-time value at stake (unlike `web3bugs_16_H_04`'s branch-conditioned During case); `loan` and `holdings` are defined unconditionally before the single return statement, so `@Post`'s joined `sigma_exit` introduces no ambiguity here (there is only one exit path, `R(l_ret)` for line 203).

## R1-5 — Relation form

**Return-value relation** via rule $(C_{\text{ret}})$: `returnExpression == intentValue`, with `intentValue` the literal `0`. Not $(P_{\text{ee}})$ (ruled out in R1-3, alternative 2 — no meaningful entry value for a once-computed return expression). Not forced to `<=`/`>=` by the patch's own operator (R1-5's explicit rule) — the selected relation doesn't even carry a comparison operator over `loan`/`holdings`; it asserts the *outcome* of that comparison under a fixed scenario.

## R1-6 — Target annotation

Attachment point: end of `belowMaintenanceThreshold`'s body, after the return statement (line 203), matching this project's existing `returnExpression` convention (e.g. `evaluation/RQ1/cases/web3bugs_5_H_12/web3bugs_5_H_12.sol`, which places `// @Post returnExpression == ...` as the last line of the function body).

```solidity
function belowMaintenanceThreshold(CrossMarginAccount storage account)
    internal
    returns (bool)
{
    uint256 loan = loanInPeg(account, true);
    uint256 holdings = holdingsInPeg(account, true);
    // The following should hold:
    // holdings / loan >= 1.1
    // =>
    return 100 * holdings >= liquidationThresholdPercent * loan;
    // @Post returnExpression == 0
}
```

**Concrete scenario the annotation is conditioned on** (per README's guidance that most During/Post relations in this benchmark are implicitly scenario-conditioned, not unconditional invariants): a healthy, over-collateralized account — `liquidationThresholdPercent = 110` (the "1.1" ratio from the function's own comment, scaled by 100 to match the code's own `100 * holdings` scaling — this is how the constant `110` is derived, not asserted from nowhere), `loan = 1000`, `holdings = 2000` (holdings/loan = 2.0, well above the 1.1 safety ratio). Under this precondition, the intended semantics is unambiguous: this account must not be flagged for liquidation, i.e. `returnExpression == 0`. This part of R1-6/R1-7 only needs the scenario to be a legal, *statable* precondition over in-scope identifiers — which it is — independent of whether it can actually be *driven* to these exact numbers by a legal debug annotation; that second, harder question is addressed below and turns out to matter for RQ1-B.

**Correction (later pass): `loan`/`holdings` cannot actually be pinned this way.** The paragraph above originally proposed pinning `loan`/`holdings` directly via `@LocalVar`. This is not legal — `@LocalVar` binds **function parameters** (README/`main.tex`: "@LocalVar (function parameters)"), not locals defined by an in-body computation; `belowMaintenanceThreshold`'s only parameter is `account`, and `loan`/`holdings` are computed from it via `loanInPeg`/`holdingsInPeg`, not supplied externally. Overriding a computed local directly would assert a value with no connection to what the function's own arithmetic actually produces — unsound, not merely inconvenient. The only legal way to steer this scenario is through `account`'s own (nested) fields — `account.borrowed[token]`, `account.borrowTokens`, `account.holdings[token]`, `account.holdingTokens` — since `account` genuinely is the parameter. But `loanInPeg`/`holdingsInPeg`'s real computation, starting from those fields, runs through `sumTokensInPegWithYield`/`sumTokensInPeg` → `yieldTokenInPeg`/`PriceAware.getCurrentPriceInPeg` → external price/yield lookups (`Lending(lending()).viewBorrowingYieldFP(...)`, `IUniswapV2Pair(...).getReserves()` several calls below `PriceAware`) that sit **outside `belowMaintenanceThreshold`'s own text** — and `@IReturn`, like every debug annotation, can only be written within the annotated function's own body. There is no legal annotation reaching those calls, so their return values stay ⊤ regardless of how `account`'s fields are set, and that ⊤ propagates into `loan`/`holdings` themselves. See the revised RQ1-B section below — this is expected to produce **Warning**, not the clean Violated/Satisfied split R1-7's arithmetic below shows for the hypothetical pinned scenario.

All referenced identifiers (`returnExpression`, and, implicitly, `loan`/`holdings`/`liquidationThresholdPercent` as the scenario's preconditions) are pre-existing, semantically meaningful in-scope values; no synthetic value is introduced beyond the scenario's own chosen numbers, whose derivation is documented above.

## R1-7 — Expressibility decision

- **Values referenceable at the point**: yes — `returnExpression` resolves against `R(l_ret)` for line 203's return statement, exactly the `$C_{\text{ret}}$` rule's mechanism; this is available in `@Post`'s field supply. The scenario's preconditions (`loan`, `holdings`, `liquidationThresholdPercent`) are, respectively, a local (live at function scope), a local, and a state variable — all legally referenceable via `varRef -> identifier subAccess*` at or before the annotated point.
- **Arithmetic/logical relation representable**: yes — a single comparison of `returnExpression` to the numeric literal `0` via `$C_{\text{ret}}$` and `relOp`'s `==`.
- **Observation point supported**: yes — `@Post` at function exit is exactly the context `$C_{\text{ret}}$` is designed for.
- **No function call inside `intentValue`**: confirmed in R1-3 — `loanInPeg`/`holdingsInPeg` are called earlier (lines 198-199) to produce `loan`/`holdings`, but neither the calls nor `loan`/`holdings` themselves appear inside the selected annotation's `intentValue` at all (`intentValue` here is just the literal `0`); the scenario that gives `loan`/`holdings` their values is established as a *precondition*, external to the annotation text, not as a call inside it.
- **Discrimination check (concrete scenario, worked arithmetic)** — *this is the mathematical argument that the relation is sufficient given these numbers; whether the engine can actually be driven to these exact numbers is a separate, RQ1-B question addressed below, where the answer turns out to be no*: fix `liquidationThresholdPercent = 110, loan = 1000, holdings = 2000`.
  - Intended (patched) code: `100 * 2000 = 200000` vs. `110 * 1000 = 110000`; `200000 <= 110000` is **false** → intended `belowMaintenanceThreshold` returns **`false` (0)** → matches the target annotation (Satisfied).
  - Buggy code: `100 * 2000 = 200000` vs. `110 * 1000 = 110000`; `200000 >= 110000` is **true** → buggy `belowMaintenanceThreshold` returns **`true` (1)** → violates the target annotation (Violated) — this is precisely the report's stated harm: a healthy account wrongly flagged for liquidation.
- **Scenario conditioning, stated explicitly**: the annotation holds given the stated precondition (this specific `loan`/`holdings`/`liquidationThresholdPercent` combination, representing a healthy account), not as a claim about every possible account state — consistent with README's guidance that Post relations in this benchmark are typically scenario-conditioned rather than bare unconditional invariants.
- **Quantification note**: the reported property is *not* naturally quantified over a collection (no "every account" or "every pool" structure) — it is a claim about a single account's boolean liquidation outcome under one arithmetic precondition. The general "for all `loan`, `holdings`" iff relation was found inexpressible in R1-3 (alternative 3) for a *different*, permanent grammar reason (no nested boolean comparison inside `intentValue`), not because of a missing quantifier over a collection — so this does not trigger the R1-6/R1-7 collection-quantification note or its associated Summary flag; it is recorded here only for transparency about why the general form was not used.

**Outcome: Expressible — Yes**, under the concrete healthy-account scenario constructed above.

## Usable/Unusable (§5)

**Usable** — all values the selected relation needs (`returnExpression`, and the scenario's `loan`/`holdings`/`liquidationThresholdPercent`) are directly referenceable in-grammar at the annotated point; purely a representational-resources fact, independent of whether the engine would resolve them precisely (deferred to RQ1-B). **Value-level** — the underlying defect is exactly "a wrong operator" (`>=` instead of `<=`) in a single comparison expression, the paper's own canonical value-level pattern; there is no structural/ordering defect (no missing call, no missing state update, no operation-ordering issue).

## RQ2-A — Specification profile

- **Relevant statements (3, all in `belowMaintenanceThreshold`)**: line 198 (`uint256 loan = loanInPeg(account, true);` — defines `loan`, one of the two values the target scenario pins); line 199 (`uint256 holdings = holdingsInPeg(account, true);` — defines `holdings`, the other); line 203 (target/disputed statement itself — counted as context establishing the attachment point and the return-value subject, per the self-substitution rule; its own algebra is *not* used as independent evidence for the relation — the relation was derived from the function's own comment (R1-1) stating the intended ratio, not by rewriting line 203 into itself). The function's comment at lines 200-202 is the primary textual evidence for R1-1's intent reconstruction but is not itself an executable statement, so it is not counted in this line total; its evidentiary role is recorded in R1-1 instead.
- **Unique relevant values (5)**: `account` (parameter — the argument threaded through the two definitions), `loan` (local), `holdings` (local), `liquidationThresholdPercent` (state variable), and the function's own return value (the boolean target the annotation constrains — included per §6's explicit rule that the constrained target value itself counts).
- **Additional functions required**: **None.** `loanInPeg`/`holdingsInPeg` are called at lines 198-199, but per README §6 Step 1's operational test, their *specific* computational behavior is not load-bearing to the *selected* relation: the annotation scenario-instantiates `loan` and `holdings` directly as free preconditions (a healthy 2:1 ratio), and the discrimination argument (R1-7) depends only on what `100 * holdings` vs. `liquidationThresholdPercent * loan` evaluates to given those fixed numbers — not on how `loanInPeg`/`holdingsInPeg` arrive at whatever numbers they arrive at. The one fact that *would* matter — that `loan` and `holdings` are commensurable, same-unit ("peg") quantities — is established directly by the target function's own comment (lines 200-202), which states the ratio between them, without opening either callee's body. (Not the two functions' `InPeg`-suffixed names — a naming convention alone is too weak a basis to lean on for a semantic guarantee; the comment is the actual evidence.) Changing `loanInPeg`/`holdingsInPeg`'s internal implementation (while still returning *some* peg-denominated uint256) would not move the selected relation's derivation or validity at all — so Step 1 excludes them, and per §6 they are not counted anywhere, not even as a case note. **This is a substantive departure from the old (retired) classification's implicit premise** that the external `Lending` contract's runtime state was needed: that premise applied to *resolving* `loan`/`holdings` precisely (an RQ1-B/engine-precision concern), not to *expressing* or *justifying* the selected relation, which never needed to look past `belowMaintenanceThreshold`'s own three statements.
- **Additional protocol/application-specific contracts/libraries required**: None, for the same reason — no cross-contract (`Lending`, `RoleAware`, `PriceAware`) or protocol-specific fact is load-bearing to the selected relation.
- **Case notes**: none identified. No generic library/language-semantics fact (e.g. a SafeMath-style overflow-checked op) was found load-bearing here either — the arithmetic involved (`uint256` multiplication of small scenario constants) does not depend on any wrap/revert distinction for the discrimination argument to hold.
- **Context breadth**: **1 (same-function context)** — the target statement plus the two immediately preceding same-function local definitions and the function's own comment; no other function, contract, or library is load-bearing.
- **External specification required**: **No.** (Per §6, R1-1's own use of the audit report never counts here.) The intended ratio is stated directly in the target function's own source comment (lines 200-202) — ordinary source-code evidence, not protocol/business convention beyond source + language semantics.

## RQ1-B / RQ2-B

Deferred per README §8 — not run in this pass. No predicted outcome recorded.

## Summary

- **Expressible: Yes** (under the concrete healthy-account scenario constructed in R1-6; the fully general, scenario-free "iff" relation is inexpressible for a permanent grammar reason — no nested boolean comparison inside `intentValue` — recorded in R1-3 alternative 3, but this does not block the narrower, scenario-conditioned claim actually selected).
- **Quantified property instantiated: No** — not a collection-quantified property; see R1-7's quantification note for why the (unrelated) general-iff inexpressibility is not conflated with this flag.
- **Target annotation**: `// @Post returnExpression == 0`, attached at the end of `belowMaintenanceThreshold`'s body (after line 203), conditioned on the scenario `liquidationThresholdPercent = 110, loan = 1000, holdings = 2000` (a healthy, over-collateralized account) — this scenario is legal to *state* (R1-6/R1-7), but **cannot be legally *driven* to these exact numbers**: `loan`/`holdings` are computed locals, not parameters, so `@LocalVar` cannot pin them directly, and the only legal path (setting `account`'s own nested fields) still routes through external price/yield lookups several calls below `belowMaintenanceThreshold`'s own text, out of `@IReturn`'s reach. Structural reasoning here points toward Warning at RQ1-B (formal prediction deferred, per README §10, to when that track actually runs).
- **Value-level, Usable, Post, return-value relation form.**
- Alternatives considered at R1-3: bare accounting inequality independent of the return value (rejected, non-discriminating), Entry/Exit form (rejected, structurally inapplicable), fully general iff relation (rejected, inexpressible — nested boolean comparison not in grammar), return-value relation on the under-collateralized mirror scenario (valid, not selected — narrative-fit tiebreak only), return-value relation on the healthy scenario (selected).
- RQ2-A headline: 3 relevant statements, 5 unique relevant values, 0 additional functions required (a substantive, freshly-derived finding — see RQ2-A above), 0 additional protocol-specific contracts/libraries, context breadth 1, external specification not required.
- RQ1-B/RQ2-B: deferred, not run in this pass.
