# web3bugs_79_H_02 — Agent A (Analyst) Case Analysis

Case ID: `web3bugs_79_H_02` | Contract: `LaunchEvent` (contest 79, Trader Joe / RocketJoe) | Function: `createPair() external`
Existing label (former L1–L5 taxonomy, **retired — see README §0, not used to drive this pass**): `not_detectable (L5b: wrong-code)` — this old label and its "requires bug-awareness because the NatSpec only states the scale factor, not the complete formula" reasoning are **not treated as authoritative** here; a fresh R1-1→R1-7 pass is performed independently below.
Source: `evaluation/RQ1/target_contracts_original/web3bugs_79_H_02.sol`; Report: `C:\Users\isjeon\Web3Bugs\reports\79.md`, finding `[H-02]` (§0.5 primary/authoritative source).
**Cross-checked against the scattered `Dataset/Web3Bugs/S6_4/contest_79_H_02/README.md` per §0.5's mandatory caution: confirmed truncated.** The scattered file reproduces only the finding's title, byline, the "floor price not reached" framing sentence, the NatSpec quote, the "check is correct but..." sentence, and the buggy code snippet — it is missing the `#### Example` walkthrough (the concrete WBTC numeric scenario), the `#### Recommendation` section, and the sponsor-confirmation exchange, all present in the primary source (`Web3Bugs/reports/79.md`). This matches the exact truncation pattern §0.5 warns about (`71_H_11`/`83_H_01`/`65_H_01`); the primary source is used throughout below. The `LaunchEvent.sol` copy bundled alongside the scattered README was checked line-for-line against `target_contracts_original/web3bugs_79_H_02.sol` for the relevant lines (392–408) and is textually identical — no source discrepancy, only a report-excerpt discrepancy.
Reported bug line (local numbering in `target_contracts_original/web3bugs_79_H_02.sol`): 398 (the `tokenAllocated = (wavaxReserve * 10**token.decimals()) / floorPrice;` assignment inside `createPair`'s floor-price-adjustment branch).

---

## R1-1 — Reported Behavior Reconstruction

**Contract role**: `LaunchEvent` is a liquidity-launch/price-discovery contract (RocketJoe). Users deposit AVAX (as WAVAX) during phases 1–2; in phase 3, `createPair()` takes the accumulated WAVAX (`wavaxReserve`) and the issuer's tokens (`tokenReserve`) and creates a JoePair (AMM pool) via `router.addLiquidity`. A `floorPrice` (AVAX per token, "scaled to 1e18" per its own NatSpec, line 59) protects the issuer: if the WAVAX actually raised implies an average sale price below `floorPrice`, `createPair()` reduces the amount of tokens sent to the pool (`tokenAllocated`) so the pool is seeded at (at least) the floor price instead of diluting the issuer's tokens at a below-floor price.

**Function role**: `createPair()` computes `tokenAllocated` (initially the full `tokenReserve`), checks whether the floor price is met, and if not, recomputes `tokenAllocated` to the (smaller) amount of tokens that, paired with the actual `wavaxReserve`, would exactly hit `floorPrice`. It then approves and calls `router.addLiquidity`, records `pair`/`wavaxAllocated`, zeroes `wavaxReserve`, and decrements `tokenReserve` by `tokenAllocated`.

```solidity
uint256 tokenAllocated = tokenReserve;                                    // L392

// Adjust the amount of tokens sent to the pool if floor price not met
if (
    floorPrice > (wavaxReserve * 10**token.decimals()) / tokenAllocated   // L395-396
) {
    tokenAllocated = (wavaxReserve * 10**token.decimals()) / floorPrice;  // L398: BUGGY
    tokenIncentivesForUsers =
        (tokenIncentivesForUsers * tokenAllocated) /
        tokenReserve;                                                     // L399-401
    tokenIncentiveIssuerRefund =
        tokenIncentivesBalance -
        tokenIncentivesForUsers;                                          // L402-404
}
```

**Relevant locals/state**:
- `floorPrice` (state, `uint256 public floorPrice`) — minimum AVAX-per-token sale price, set once at initialization from an issuer-supplied `_floorPrice`. NatSpec (line 59): `/// @dev floorPrice is scaled to 1e18`.
- `wavaxReserve` (state, `uint256 private`) — the exact WAVAX amount raised and held for pool seeding at this point in `createPair`.
- `tokenReserve` (state, `uint256 private`) — the issuer's tokens set aside for the pool/incentives; `tokenAllocated`'s initial value.
- `tokenAllocated` (local, `uint256`) — the actual amount of the issuing token that will be sent to `router.addLiquidity`; this is the disputed value.
- `token` (state, `IERC20Metadata public token`) — the issuing ERC20 token, whose `decimals()` is called (an external `view` call) at both L396 and L398.

**The disputed statement (L398)**: `tokenAllocated = (wavaxReserve * 10**token.decimals()) / floorPrice;`. The multiplicand `10**token.decimals()` scales `wavaxReserve` by the *token's own decimals* before dividing by `floorPrice`, but `floorPrice` is documented and used elsewhere as a fixed 1e18-scaled quantity, independent of `token`'s decimals. For any `token` with decimals ≠ 18, this multiplicand is wrong.

**Variable-value intent (L398)**: on any execution reaching this branch (floor price not met), the recomputed `tokenAllocated` must equal the amount of token that, combined with `wavaxReserve`, prices the pool at exactly `floorPrice` (both operands expressed in `floorPrice`'s own 1e18 scale) — i.e. `wavaxReserve * 1e18 / floorPrice`, not `wavaxReserve * 10**token.decimals() / floorPrice`.

**Statement/line-level intent**: the branch as a whole exists to uphold the invariant "the pool is never seeded at a price below `floorPrice`, by reducing the token side rather than requiring more WAVAX." The multiplication by "some 1e18-scale-compatible factor" is a necessary step of that computation (converting `wavaxReserve`, a WAVAX-denominated quantity, into the same fixed-point scale `floorPrice` is expressed in) — the step itself is present in both the buggy and intended code, only the specific scale constant used is wrong.

**Reported erroneous behavior** (H-02, verbatim, primary source `Web3Bugs/reports/79.md`): *"In `LaunchEvent.createPair`, when the floor price is not reached (`floorPrice > wavaxReserve * 1e18 / tokenAllocated`), the tokens to be sent to the pool are lowered to match the raised WAVAX at the floor price. Note that the `floorPrice` is supposed to have a precision of 18... The `floorPrice > (wavaxReserve * 1e18) / tokenAllocated` check is correct but the `tokenAllocated` computation involves the `token` decimals: `// @audit should be wavaxReserve * 1e18 / floorPrice` / `tokenAllocated = (wavaxReserve * 10**token.decimals()) / floorPrice;` This computation does not work for `token`s that don't have 18 decimals."*

**A scope note on the report's own framing (recorded for transparency, not folded into the target relation)**: the report's prose asserts the *condition* at L395-396 (`floorPrice > (wavaxReserve * 1e18) / tokenAllocated`) "is correct," but the actual source at L396 (verified identical in both `target_contracts_original/web3bugs_79_H_02.sol` and the scattered dataset's bundled `LaunchEvent.sol`) reads `floorPrice > (wavaxReserve * 10**token.decimals()) / tokenAllocated` — i.e. the *same* `10**token.decimals()` term appears in the condition too, not literally `1e18` as the report's prose states. **We do not treat this as a confirmed determination that L396 is in fact correct** (it may or may not be — nothing here establishes that either way) **— we treat it as a report/source inconsistency, and deliberately do not expand H-02's scope beyond the assignment (L398) the report's own text and Recommendation explicitly identify.** This is a scope decision, not a correctness finding about L396. R1-1 through R1-6 below follow the report's own stated scope accordingly — the L396 condition is treated as reachability/scenario context, not as a second disputed statement — consistent with §2 ("recommended fix... this benchmark's ground truth *is* the audit report").

**Proof of Concept / Example** (verbatim scenario, primary source only — **absent from the scattered excerpt**, §0.5): *"Assume I want to sell 1.0 wBTC = 1e8 wBTC (8 decimals) at 2,000.0 AVAX = 2,000 * 1e18 AVAX. The `floorPrice` is `2000e18 * 1e18 / 1e8 = 2e31`. Assume the Launch event only raised 1,000.0 AVAX - half of the floor price for the issued token amount of 1.0 WBTC (it should therefore allocate only half a WBTC) - and the token amount will be reduced as: `floorPrice = 2e31 > 1000e18 * 1e18 / 1e8 = 1e31 = actualPrice`. Then, `tokenAllocated = 1000e18 * 1e8 / 2e31 = 1e29 / 2e31 = 0` and no tokens would be allocated, instead of `0.5 WBTC = 0.5e8 WBTC`."*

**Recommendation** (verbatim, primary source only, **absent from the scattered excerpt**): *"The new `tokenAllocated` computation should be `tokenAllocated = wavaxReserve * 1e18 / floorPrice;`."*

**Sponsor comment**: *"[cryptofish7 (Trader Joe) confirmed and commented](...): Fix: https://github.com/traderjoe-xyz/rocket-joe/pull/76"* — confirmed by the sponsor, no dispute of the auditor's characterization; no judge-level dissent recorded (this is the report's sole H-02, straightforward confirm-and-fix outcome).

**Expected/intended behavior**: on any call to `createPair()` reaching the floor-price-adjustment branch, `tokenAllocated` must equal `wavaxReserve * 1e18 / floorPrice` — exactly the recommended fix's literal target, matching `floorPrice`'s own documented 1e18 scale rather than `token`'s decimals.

**Patch intent**: a literal one-line substitution of the multiplicand (`10**token.decimals()` → `1e18`) inside the existing L398 assignment — no new statement, no new branch, no removed statement; used below as evidence for *which* constant is correct (R1-3), not transcribed mechanically as annotation syntax beyond that (§2/§3: matching the patch's target value is not itself a problem when, as here, it genuinely is the correct specification).

**Bug-relevant intended numeric behavior**: for any call to `createPair()` reaching the branch where `floorPrice` is not met, `tokenAllocated` (as reassigned by that branch) must equal `wavaxReserve * 1e18 / floorPrice`; the current code instead computes `wavaxReserve * 10**token.decimals() / floorPrice`, which coincides with the correct value only when `token.decimals() == 18`, and otherwise under- or over-allocates tokens to the pool (under-allocates, potentially to 0, for `decimals() < 18`; over-allocates for `decimals() > 18`), directly diluting or over-paying the issuer relative to the intended floor-price guarantee.

**Independent check on the task's flagged concern — is `token.decimals()` already bound to an in-scope local?** No. Grepped the entire file for `decimals` (`grep -n decimals web3bugs_79_H_02.sol`): the only two occurrences in the whole contract are L396 and L398, both direct external calls `token.decimals()` — there is no state variable or local anywhere in the contract (e.g. no cached `tokenDecimals`) that already holds this value. This matters for R1-3 below, but turns out not to matter in the way the task's framing anticipates (see R1-3): the *correct* formula does not need `token.decimals()` at all, so there is no call to rescue in the first place.

---

## R1-2 — Intent Abstraction

Distinguishing property (patch's literal one-constant substitution used only as evidence for *which* value is correct, not transcribed as annotation syntax beyond that): in the floor-price-adjustment branch, the reassigned `tokenAllocated`'s value must equal `wavaxReserve * 1e18 / floorPrice`, not `wavaxReserve * 10**token.decimals() / floorPrice`. **Intent-level orientation: Value-centered** — a constraint on a specific computed value (`tokenAllocated`) at a specific statement, not a state-transition/effect claim; the formula's overall shape (`wavaxReserve * <scale> / floorPrice`) is present and structurally correct in both buggy and intended code, only one operand (`<scale>`) is wrong.

---

## R1-3 — Select the least implementation-specific sufficient relation

**Preliminary check — does this relation need a function call inside `intentValue`?** This is the task's flagged concern, checked directly: the *buggy* code's own formula calls `token.decimals()`, but the *correct* formula per the report's own Recommendation (`wavaxReserve * 1e18 / floorPrice`) does not reference `token.decimals()` at all — the fix's entire content is to replace the call-based term with the fixed constant `1e18`. So the target relation's RHS is `wavaxReserve * 1e18 / floorPrice`: two state variables and one constant, no call anywhere. **No alpha-style blocker to rescue** — this is a stronger, cleaner outcome than either of the two rescue mechanisms R1-3 usually reaches for (known-bound substitution, or exact-formula inlining): the call isn't merely avoidable via a substitute, the *correct specification itself contains no call*, because the reported defect is precisely that the buggy code called a function it should never have needed to call at all.

**Constant-derivation check (task-flagged, R1-6 guidance applied here since it determines whether `1e18` is a legitimate operand at all)**: is `1e18` "a number that appears nowhere in the source," requiring scenario-specific derivation (README's `900`-style guidance)? No — `1e18` is already used as an ordinary literal scale-factor constant twice elsewhere in this same contract, in the same fixed-point-scaling role: L273 `tokenReserve = (balance * 1e18) / (1e18 + _tokenIncentivesPercent);` and L363 `feeAmount = (_amount * getPenalty()) / 1e18;`. It is also directly documented as `floorPrice`'s own scale via NatSpec at L59 (`/// @dev floorPrice is scaled to 1e18`) and restated in the constructor's own param doc (`/// @param _floorPrice The minimum price the token is sold at`, cross-referenced with the report's own quote of the `@dev` line). `1e18` is therefore a genuine, protocol-fixed scaling constant sourced directly from the contract's own documentation and precedent usage — not a synthetic, scenario-derived literal needing the `900`-style derivation writeup.

1. **Directional/bound (weakest tier)**: `tokenAllocated <= tokenReserve`. **Rejected — does not discriminate.** By construction, this branch only ever reduces `tokenAllocated` relative to its L392 initial value (`tokenReserve`), regardless of which scale constant is used — both the buggy and the intended formula satisfy `<=` for any decimals value where the branch is entered, so this catches nothing about *which* scale is used.
2. **Inequality bound, fixed direction**: `tokenAllocated > 0`. **Rejected — does not discriminate in general**, even though it happens to catch the report's own WBTC (8-decimal) example (buggy value is exactly 0 there). For a token with, say, 6 decimals (e.g. USDC-shaped), the buggy formula produces `wavaxReserve * 1e6 / floorPrice` — smaller than the correct `wavaxReserve * 1e18 / floorPrice` by a factor of `1e12`, but still strictly positive for a large enough `wavaxReserve`. A `> 0` bound would report Satisfied on this still-defective execution, missing it entirely. Also directionally fragile: for a hypothetical token with decimals `> 18` (not excluded by the ERC20 standard), the buggy formula *over*-allocates rather than under-allocates, so no single fixed-direction bound (`>=` or `<=` against the correct value) could discriminate both under- and over-allocation cases with one relation — only equality is direction-agnostic.
3. **Exact equality (SELECTED)**: `tokenAllocated == wavaxReserve * 1e18 / floorPrice`. Matches the value R1-1 establishes as correct exactly (the literal Recommendation target), and is the only relation form immune to both the "still positive but wrong" gap of alternative 2 and the directionality problem noted above.

**Required check (§3/R1-3)**: does this equality's negation fail to catch some alternative implementation that retains the *reported* defect — a `tokenAllocated` recomputed with the wrong scale factor — but produces it differently? Checked against three distinct alternative shapes:
- **The actual buggy code** (`10**token.decimals()`, `decimals()==8`, WBTC scenario): caught, shown in the discrimination check below.
- **The same defect at a different decimals value** (`decimals()==6`, e.g. a USDC-shaped token): buggy `tokenAllocated = wavaxReserve * 1e6 / floorPrice`, strictly less than the correct `wavaxReserve * 1e18 / floorPrice` by a factor of `1e12` (still nonzero) — caught by the equality (Violated, since the two differ by a factor of `1e12`), where alternative 2's `> 0` bound would have missed it. This is the concrete instance motivating equality's selection over alternative 2, not a hypothetical aside.
- **A near-miss "partial fix"** — e.g. an implementation that substitutes `10**18` written as `1e17` (an off-by-one order of magnitude, or any similarly near-but-wrong constant) instead of the exact `1e18`: caught by the exact equality (Violated), same rationale as the calibration case's near-miss check.
- No alternative implementation that still uses a wrong scale constant in this formula escapes the exact equality's negation. **No gap found**; this specific relation does not need an `Intent coverage: Partial` flag on this ground (a separate, broader Intent-coverage question — whether the relation also covers the report's downstream `tokenIncentivesForUsers`/`tokenIncentiveIssuerRefund` consequences — is addressed in the Summary below).

**Winner: Alternative 3 (exact equality).**

**Discrimination check (explicit arithmetic, per §9 checklist item 1).** Scenario constructed directly from the report's own worked Example (verbatim numbers): `tokenReserve = 1e8` (1.0 WBTC, 8 decimals — the issuer's tokens set aside), `wavaxReserve = 1000e18 = 1e21` (1,000.0 AVAX actually raised), `floorPrice = 2e31` (computed by the report as `2000e18 * 1e18 / 1e8`, i.e. a 2,000 AVAX floor for 1.0 WBTC), `token.decimals() = 8`.
- **Reachability check** (L395-396 condition, context only — not part of the target relation itself, see R1-4): `(wavaxReserve * 10**decimals()) / tokenAllocated(initial=tokenReserve) = (1e21 * 1e8) / 1e8 = 1e21`. Is `floorPrice (2e31) > 1e21`? Yes — branch entered, matching the report's own "floor price not reached" framing.
- **Buggy** (current code, L398 as written): `tokenAllocated = (wavaxReserve * 10**decimals()) / floorPrice = (1e21 * 1e8) / 2e31 = 1e29 / 2e31 = 0.005 →` floors to `0` (integer division). Check: `0 == wavaxReserve * 1e18 / floorPrice = 1e21 * 1e18 / 2e31 = 1e39 / 2e31 = 5e7`? → **false ⟹ Violated.** (Matches the report's own stated buggy result exactly: "no tokens would be allocated.")
- **Intended** (per the recommended fix, `wavaxReserve * 1e18 / floorPrice` substituted at L398): `tokenAllocated = 1e39 / 2e31 = 5e7`. Check: `5e7 == 5e7` → **true ⟹ Satisfied.** (Matches the report's own stated correct result exactly: "`0.5 WBTC = 0.5e8 WBTC`", and `5e7 = 0.5e8`.)

---

## R1-4 — During vs Post

**Chosen: During.** The relation concerns a statement-time value of a local variable (`tokenAllocated`), immediately consumed a few lines later as call arguments to `router.addLiquidity` (a "call argument" use, one of README's own explicit During examples) and as an operand of the subsequent `tokenReserve -= tokenAllocated;` state update — not a function return value (`createPair` has no return value) and not most naturally framed as an entry/exit relation on persistent state (unlike `65_H_01`'s `lastFee`, `tokenAllocated` is an ordinary local, freshly computed by an *existing* statement at this specific point, not an absent update). README's own caution applies in the opposite direction here from the `65_H_01`/`SwordCrowdsale`/`CDP.update` precedent: those cases chose Post *despite* an assignment-shaped patch because the relation's own nature (final persisted state, or — for `65_H_01` — no existing statement at all to attach a During to) called for it; here, the relation's own nature (an intermediate, statement-time value defined and consumed entirely within one function body, at one clearly identifiable existing assignment) is the textbook During case README describes directly ("a statement-time value... tied to one statement").

**No Entry/Exit/Before/After/Assign snapshot syntax is needed.** The relation is checked at the point immediately following the L398 assignment; the default (unqualified) `@During` reference to `tokenAllocated` already denotes its current, just-assigned value at that program point — there is no need to distinguish `tokenAllocated`'s pre- vs. post-assignment value inside the relation itself (unlike, e.g., `web3bugs_42_H_01`'s `debts == debts(Entry) + increasingDebt`, which genuinely needs to mix two different snapshots of the *same* identifier). `wavaxReserve` and `floorPrice` are both state variables not modified anywhere in `createPair` prior to this point, so their plain (unqualified) reference is unambiguous.

**Required explicit delta-exception check (README §4/R1-7, per task instructions).** `createPair()` contains **no loop of any kind** — confirmed by reading its entire body (lines 377–435: a `require`, a local declaration, an `if` with no loop inside it, an external call, five persistent-state updates, and an `emit`). No candidate loop-body attachment point exists at all to even consider; the confirmed engine fact (`fixpoint()`'s `transfer_function` never reaching `_process_during_annotations` for a loop-interior node) has nothing to apply to. **Delta confirmed not applicable, trivially.**

---

## R1-5 — Relation form

**Exact equality** via the grammar's general `RelationalCmp` common-form rule (`intentValue relOp intentValue`, `Parser/Solidity.g4` line 325), reached through `duringClause -> commonClause`. Classified as a **statement-time value relation** (a plain equality between the just-assigned local `tokenAllocated` and an arithmetic expression over two in-scope state variables and one constant) — not an Entry/Exit or Before/After pairing (contrast `65_H_01`'s `lastFee == block.timestamp`, which is Post-scoped persistent-state, or `42_H_01`'s genuinely snapshot-mixing form). Not forced to equality by the patch's assignment shape (R1-5's explicit caution) — equality was selected in R1-3 on independent, concretely-demonstrated discrimination grounds (the still-positive-but-wrong 6-decimals near-miss, and the bidirectional under-/over-allocation argument, both of which a fixed-direction bound would miss).

---

## R1-6 — Construct the target annotation

**Attachment point**: immediately after the disputed `tokenAllocated = (wavaxReserve * 10**token.decimals()) / floorPrice;` statement (L398), inside the `if (floorPrice > ...)` branch — the textual-placement convention used elsewhere in this project's `@During` write-ups.

**Reachability precondition and defect-exposing scenario condition (README's scenario-conditioning note, §4/R1-7 — two distinct things, named separately to avoid conflating them)**: the relation is only *exercised at all* given the **reachability precondition** `floorPrice > (wavaxReserve * 10**token.decimals()) / tokenReserve` (the branch's own existing condition — "floor price not met" using the *initial* `tokenAllocated == tokenReserve`). Separately, the relation is only *defect-exposing* (i.e., actually distinguishes buggy from intended, rather than being vacuously satisfied by both) given `token.decimals() != 18` — this is not a precondition of the intended relation itself (`tokenAllocated == wavaxReserve * 1e18 / floorPrice` is equally true, and equally the correct specification, for an 18-decimal token; it simply isn't *discriminating* there, since `10**18 == 1e18` makes the buggy and intended formulas coincide numerically). Neither condition needs to be written into the annotation itself — both are properties of the concrete debug/batch scenario that would be used at RQ1-B time (deferred) to route execution into this specific branch and, separately, to choose a decimals value that actually exposes the defect, matching this project's established precedent for stating reachability/discrimination preconditions in prose rather than inside the relation (e.g. `65_H_01`'s `lastFee(Entry) != 0` precondition).

**Target annotation**:
```solidity
uint256 tokenAllocated = tokenReserve;

// Adjust the amount of tokens sent to the pool if floor price not met
if (
    floorPrice > (wavaxReserve * 10**token.decimals()) / tokenAllocated
) {
    tokenAllocated = (wavaxReserve * 10**token.decimals()) / floorPrice;
    // @During tokenAllocated == wavaxReserve * 1e18 / floorPrice
    tokenIncentivesForUsers =
        (tokenIncentivesForUsers * tokenAllocated) /
        tokenReserve;
    tokenIncentiveIssuerRefund =
        tokenIncentivesBalance -
        tokenIncentivesForUsers;
}
```
All three operands (`tokenAllocated`, `wavaxReserve`, `floorPrice`) are ordinary in-scope values at this program point — a local and two state variables, respectively — plus the constant `1e18`, whose sourcing is established above (a documented, contract-wide fixed-point scale, not a scenario-derived synthetic literal). No function call anywhere in the relation.

**Quantification note**: the property is a plain scalar-value check (`tokenAllocated`, `wavaxReserve`, `floorPrice` are all single state/local values, not array/mapping elements) — not a claim quantified over a stored collection of co-existing elements. No representative-element instantiation issue applies.

---

## R1-7 — Expressibility decision

**Values referenceable at a legal program point**: Yes. `tokenAllocated` (local, `varRef`, current/just-assigned value under `@During`), `wavaxReserve` and `floorPrice` (state variables, `varRef`) are all ordinary in-scope identifiers at this exact program point — nothing needed here is behind an external-contract boundary or missing a proxy.

**Arithmetic/logical relation representable**: Yes. `tokenAllocated == wavaxReserve * 1e18 / floorPrice` is a single `intentValue relOp intentValue` (`RelationalCmp`) with two ordinary arithmetic operators (`*`, `/`) over in-scope operands and one constant — well within the grammar's `arithFactor`/`arithTerm` arithmetic.

**No function call inside `intentValue`**: confirmed not an issue (R1-3's preliminary check, directly addressing the task's flagged concern) — the *buggy* code calls `token.decimals()`, but the *correct* formula the relation states does not; the fix's entire content is removing that call, not working around it. No known-bound rescue or exact-formula-inlining rescue was needed because there was no call to rescue in the target relation in the first place.

**Observation point supported — explicit check against the confirmed `delta` (loop-body-`@During`) exception, per task instructions.** As established in R1-4: `createPair()` contains no loop anywhere in its body, and the relation is attached immediately after an ordinary (non-loop-interior) statement. **Delta confirmed not applicable, trivially** — no candidate loop-body attachment point exists at all.

**Outcome: Expressible = YES.**

**This directly contradicts the retired L5b label's reasoning** (see header note): that reasoning treated the gap between the NatSpec's bare "scaled to 1e18" comment and the full corrected formula as a bug-awareness barrier ("constructing the fix requires bug awareness"), which is not a concept this methodology evaluates (README §3). Independently re-derived here: the relation is expressible not merely despite that gap, but because `1e18` is directly sourced from source-code precedent (two other same-file usages, L273/L363) and the NatSpec's own explicit statement of `floorPrice`'s scale (L59) — no interface call, no external protocol lookup, and (per R1-3's preliminary check) no call-inside-`intentValue` blocker of any kind, since the corrected formula contains no call at all.

---

## Section 5 — Value/Algorithm and Usable/Unusable

- **Value-level** — per the paper's own classification and README §5's grounding guidance ("if the intended computation's steps are all present and only a single operand/operator/constant within one otherwise-complete expression is wrong, that's Value-level"): the buggy and intended formulas are structurally identical (`wavaxReserve * <scale> / floorPrice`), differing only in the multiplicand (`10**token.decimals()` vs. `1e18`). No processing step is missing — the "convert `wavaxReserve` into `floorPrice`'s own scale" step is present in both versions, only its scale constant is wrong. This is, if anything, a cleaner Value-level instance than most in this dataset: the fix does not add a missing operation, it *removes* an erroneous one (the `token.decimals()` call) and replaces it with a fixed constant — there is no unused helper function or spare procedure whose presence might tempt an Algorithm-level framing (contrast `web3bugs_16_H_06`'s `toWad`), and no ambiguity to resolve.
- **Usable** — all three values the relation needs (`tokenAllocated`, `wavaxReserve`, `floorPrice`) are referenceable, as ordinary in-scope identifiers, at the annotation's program point (immediately after the disputed assignment); the constant `1e18` is directly documented in-contract, not behind any external boundary. Nothing here depends on `token.decimals()` at all — a clean, unambiguous Usable case (§5, purely a representational-resources question).

---

## RQ2-A — Specification Requirements profile

**Relevant statements** (within `createPair` itself):
1. `uint256 tokenAllocated = tokenReserve;` (L392) — the declaration/initial-definition site of `tokenAllocated`, the relation's own target/lvalue; needed to know `tokenAllocated` is a local seeded from `tokenReserve` before this branch potentially reassigns it. Counted per (a): "define the values appearing in the target relation."
2. `if (floorPrice > (wavaxReserve * 10**token.decimals()) / tokenAllocated) { ... }` (L395–396) — the branch containing the target statement; counted as attachment-point/reachability context, the same role `web3bugs_65_H_01`'s counted `else if (startSupply == 0) { return; }` played, not a sibling/excluded gate. **This statement being counted and its embedded `token.decimals()` call being excluded (below) are answers to two different questions, not a tension**: "Relevant statements" asks whether a reader needs this statement to locate/understand the attachment point (yes — it's the target statement's own containing branch, precedented by `65_H_01`); "Additional functions required" separately asks whether the *selected relation's own truth-value* depends on this call's specific return value (no — see below). A statement can legitimately be counted as structural context while a call embedded inside it is excluded as non-load-bearing to the relation itself; these are not the same test and README §6 defines them separately.
3. `tokenAllocated = (wavaxReserve * 10**token.decimals()) / floorPrice;` (L398) — the disputed/target statement itself, the annotation's attachment point and subject. Counted as context (its own algebra is barred from counting as self-justifying evidence for the relation, per README's explicit self-substitution note, but the statement itself — as the site defining the constrained value — belongs in the count like any other statement in the annotated function).

Total: **3 relevant statements.**

**Excluded, with reason (Step 1, README §6)**:
- **`token.decimals()`** (the call itself, appearing in both L396 and L398): **Step 1 test applied directly** — "if the entity's relevant semantic guarantee were changed... would the target relation's derivation or validity change?" The selected relation (`tokenAllocated == wavaxReserve * 1e18 / floorPrice`) does not reference `token.decimals()` at all; its validity is entirely independent of what `token.decimals()` returns. Changing `token.decimals()`'s return value would change *whether* the L395-396 condition is entered for a *given* `wavaxReserve`/`floorPrice` pair (a reachability/scenario-construction fact, already captured in prose as this case's discrimination precondition), but would not change the selected relation's own derivation or truth-value once that branch is reached. Per README §6 Step 1's explicit instruction: **"don't count it anywhere, not even as a case note. It's not part of the record at all."** Excluded from "Additional functions required," from "Unique relevant program values," and from any case note — while still being explained here in prose for transparency (the same discipline `web3bugs_83_H_01`'s pool-0 investigation and this project's "alternative-rejection inspection doesn't count" corollary use).
- L399–404 (`tokenIncentivesForUsers`/`tokenIncentiveIssuerRefund` recomputation, immediately following the target statement): read during R1-1 to fully understand the branch's downstream consequences, but neither defines an operand of the selected relation nor gates its reachability — a pure downstream consequence of `tokenAllocated`, not load-bearing for `tokenAllocated`'s own correctness. Excluded entirely (not a case note), matching the "alternative-rejection inspection doesn't count" corollary's treatment of investigated-but-non-load-bearing code.
- L407–435 (the `approve`/`addLiquidity` calls onward): read to establish that `tokenAllocated` is subsequently consumed as a call argument and in a state decrement (supporting the R1-4 During-vs-Post choice), but none of this downstream code redefines `tokenAllocated` or otherwise affects the selected relation's soundness. Excluded entirely.

**Unique relevant program values**:
- Local (1): `tokenAllocated` (the relation's own constrained target value; also the L395-396 condition's denominator in its pre-reassignment form).
- State (2): `wavaxReserve`, `floorPrice` — both are direct operands of the selected relation's RHS, and both also appear in the L395-396 condition.
- State (1): `tokenReserve` — occurs in the counted L392 statement (defines `tokenAllocated`'s initial value); not itself an operand of the relation's RHS, but a value a reader must trace to understand `tokenAllocated`'s pre-branch state, the same role `web3bugs_65_H_01`'s `startSupply` played.

Total: **4 unique relevant program values** (1 local / 3 state). `token` (the `IERC20Metadata` state variable) is **not** counted separately — its only appearance in the counted statements is as the receiver of the excluded `decimals()` call; per the same Step 1 exclusion, it carries no independent role once that call is excluded.

**Additional functions required: 0.** `token.decimals()` is the only function call touched by any counted statement, and it is excluded per Step 1 (not load-bearing for the selected relation) — see above. No other call appears in the counted statements.

**Additional protocol/application-specific contracts/libraries required: 0.**

**Context breadth: 1** (same-function context). The relation's own two RHS operands (`wavaxReserve`, `floorPrice`) need no same-function context to evaluate as bare state reads, but understanding the scenario (why this branch executes, and `tokenAllocated`'s pre-branch state) requires the two same-function statements above (L392, L395-396) — not 0, and not 2+ since no sibling function or external contract's own logic needs to be understood (the state variables' *setting* happens elsewhere — `depositAVAX`, the initializer — but the relation only needs their *current* value at this point, the same scoping `web3bugs_65_H_01`'s `lastFee` used).

**External specification required: No.** Everything the selected relation depends on — the `wavaxReserve * 1e18 / floorPrice` target formula and the `1e18` scale constant itself — is derivable directly from the contract's own NatSpec (`floorPrice is scaled to 1e18`, L59) and precedent usage (L273, L363) plus the report's literal recommended fix; no protocol-external accounting/business convention beyond the source and the report had to be separately looked up.

---

## Section 7 — Alternatives-considered summary

| # | Relation | Tier | Expressible? | Discriminates? | Verdict |
|---|----------|------|---------------|-----------------|---------|
| 1 | `tokenAllocated <= tokenReserve` | Directional/bound | Yes | No | Rejected — true for both buggy and intended code regardless of which scale constant is used; the branch reduces `tokenAllocated` from `tokenReserve` either way |
| 2 | `tokenAllocated > 0` | Inequality bound, fixed direction | Yes | Yes, but incompletely | Rejected — catches the report's own WBTC (decimals=8) example (buggy value is exactly 0) but the required negation check finds a concrete near-miss it would miss: a 6-decimal token's buggy value is smaller-but-nonzero (`wavaxReserve*1e6/floorPrice`), and a >18-decimal token's buggy value would be *larger* than correct (over-allocation), so no fixed-direction bound discriminates both failure directions |
| 3 | `tokenAllocated == wavaxReserve * 1e18 / floorPrice` | Exact equality | Yes | Yes | **Selected** — catches the actual buggy code (WBTC scenario), the 6-decimal near-miss alternative #2 would have missed, and is direction-agnostic (catches both under- and over-allocation) |

---

## RQ1-B / RQ2-B

Deferred per README §8. Not run, not predicted. No caution comparable to `web3bugs_29_H_11`'s confirmed `abi.decode` crash or `web3bugs_70_H_03`'s live-Chainlink-call concern applies here — the relation involves no external call at all (the one call in the buggy code, `token.decimals()`, is entirely absent from the target relation itself, per R1-3), no loop, and no snapshot-qualifier (`Entry`/`Exit`/`Before`/`After`/`Assign`) syntax, so none of this project's confirmed engine-caution patterns are implicated. This is a forward-looking observation for whoever runs RQ1-B, not a substitute for actually running it.

---

## Summary

- **Expressible: Yes.** Values referenceable (`tokenAllocated`, `wavaxReserve`, `floorPrice`, all ordinary in-scope identifiers; `1e18` a documented, contract-wide fixed-point constant), arithmetic representable (a single equality over two multiplication/division operators), no call inside `intentValue` (the corrected formula, per the report's own Recommendation, drops `token.decimals()` entirely rather than needing a rescue for it), observation point (`@During` immediately after the L398 assignment) supported — explicitly checked against, and trivially not blocked by, the confirmed `delta` loop-body-`@During` exception (README §4): `createPair()` contains no loop anywhere in its body.
- **This differs from the old L5b label.** The retired reasoning called this case `not_detectable` on a "requires bug-awareness" ground that is not part of this methodology (README §3). The fresh pass finds the case cleanly **Expressible = Yes**: `1e18` is directly sourced from in-contract NatSpec and precedent usage (not merely "the scale factor" in isolation, as the old reasoning framed it, but a literal constant already used identically twice elsewhere in the same file), and — contrary to what the task's framing flagged as a potential concern — the corrected formula does not need `token.decimals()` at all, so the call-inside-`intentValue` restriction the old reasoning implicitly worried about never actually applies to the selected relation.
- **Target relation**: `tokenAllocated == wavaxReserve * 1e18 / floorPrice`, attached `@During` immediately after the disputed `tokenAllocated = (wavaxReserve * 10**token.decimals()) / floorPrice;` assignment inside `createPair`'s floor-price-adjustment branch. Reachability-conditioned on the branch's own existing "floor price not met" condition; separately, defect-exposure requires `token.decimals() != 18` (otherwise the buggy and intended formulas coincide numerically and the relation would be trivially satisfied on the buggy code too — the relation itself is equally correct at 18 decimals, just non-discriminating there, not conditioned on decimals in any deeper sense).
- **Quantified property instantiated: No** — `tokenAllocated`, `wavaxReserve`, `floorPrice` are all plain scalar values, not elements of a stored collection the annotation would need to range over.
- **Value-level** (the buggy and intended formulas share the identical structural shape `wavaxReserve * <scale> / floorPrice`; only the multiplicand is wrong — no missing processing step, and the fix removes a call rather than requiring one), **Usable** (all three needed values directly referenceable; `1e18` documented in-contract, no external-boundary dependency), `@During`, exact-equality common-form (`RelationalCmp`).
- **RQ2-A profile**: 3 relevant statements (L392's `tokenAllocated` declaration, L395-396's gating condition — with its `token.decimals()` call explicitly excluded per Step 1 as non-load-bearing for the selected relation, not even as a case note — and L398 the target statement itself), 4 unique relevant program values (1 local / 3 state: `tokenAllocated`, `wavaxReserve`, `floorPrice`, `tokenReserve`), 0 additional functions required, 0 additional protocol contracts/libraries, Context breadth 1 (same-function), External specification required: No.
- **Methodological judgment calls made in this pass**: (1) treated the report's own prose claim that the L395-396 condition "is correct" as descriptive/paraphrased rather than literal (the actual source condition also contains `10**token.decimals()`), and followed the report's explicit Recommendation scope (L398 only) rather than second-guessing or expanding the finding's boundary myself; (2) applied R1-3's preliminary call-inside-`intentValue` check directly against the task's flagged concern and found the concern resolved by construction — the corrected formula never needed the call in the first place, a stronger outcome than either the known-bound or exact-formula-inlining rescue mechanisms would have produced; (3) confirmed `1e18` requires no scenario-specific derivation (R1-6) because it is independently sourced from in-contract NatSpec and two other same-file precedent usages; (4) selected exact equality over a `> 0` bound specifically because the required negation check surfaced a concrete under-decimals near-miss (6-decimal token) the bound would miss, and a bidirectional (over/under-allocation) argument that no fixed-direction bound could resolve; (5) excluded `token.decimals()` from all RQ2-A numeric/ordinal counts per Step 1's load-bearing test, despite it appearing in a counted context statement (L395-396), and explained the exclusion in prose rather than silently omitting it.
- **RQ1-B/RQ2-B**: deferred, not run in this pass; no case-specific engine-precision caution identified — no call, no loop, and no snapshot-qualifier syntax anywhere in the selected relation or its attachment point.
