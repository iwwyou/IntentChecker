# web3bugs_113_H_05 — Agent A (Analyst) Case Analysis

Case ID: `web3bugs_113_H_05` | Contract: `NFTPairWithOracle` (contest 113, AbraNFT) | Function: `_lend(address lender, uint256 tokenId, TokenLoanParams memory accepted, bool skim) internal`
Existing label: H-05, "Mistake while checking LTV to lender accepted LTV" (submitted by catchup, also found by WatchPug, gzeon, and hyh; sponsor `cryptolyndon` confirmed, "the first to note this particular issue").
Source: `evaluation/RQ1/target_contracts_original/web3bugs_113_H_05.sol`; Report: `C:\Users\isjeon\Web3Bugs\reports\113.md`, finding `[H-05]` (§0.5 primary/authoritative source).
**Cross-checked against the scattered `Dataset/Web3Bugs/S6_4/contest_113_H_05/README.md` per §0.5's mandatory caution.** In this case the scattered file is **not truncated** — it reproduces the finding's full body verbatim (title, byline, the LTV-direction explanation, and the worked example), matching the primary source line-for-line. The primary source additionally carries the `### Proof of Concept` heading (a bare link to `NFTPairWithOracle.sol#L316`, no separate narrative PoC beyond the inline worked example already in the body), the `### Recommended Mitigation Steps` section (`params.ltvBPS <= accepted.ltvBPS`), and the sponsor-confirmation comment — all absent from the scattered excerpt but not contradictory to it. Primary source used throughout below; no discrepancy found, unlike `71_H_11`/`83_H_01`/`65_H_01`.
Reported bug line (local numbering in `target_contracts_original/web3bugs_113_H_05.sol`): 316, the fourth conjunct of the `require` spanning lines 312–318.

**Old-methodology background — explicitly not imported as a conclusion (per task instructions).** Under the retired L1–L5 taxonomy this case was labeled `not_detectable (L5b: wrong-validation-operator)`, reasoning that re-validating an already-written `require` condition "requires knowing the require is wrong." That reasoning is bug-awareness, which is not a concept this methodology uses (§3) — it is discarded outright, not merely revisited. The old reasoning also flagged `feesEarnedShare += protocolFeeShare` (L342, which depends on `bentoBox.toShare()` at L325) as a secondary `L2a: interface-call-return-top` blocker. **This is addressed directly below (R1-3): the relation this fresh pass selects never references `feesEarnedShare`, `protocolFeeShare`, or any `bentoBox` call at all, so that blocker is inapplicable to the selected relation regardless of whether BentoBox's interface CFG is now pkl'd** — it is not re-litigated because it was never load-bearing for this case's actual defect (the LTV comparison, lines 312–318, is fully decided before the `bentoBox.toShare()` call at line 325 is ever reached).

---

## R1-1 — Reported Behavior Reconstruction

**Contract role**: `NFTPairWithOracle` is a private, single-collateral NFT lending pool (BoringCrypto/Sushi "Private Pool" pattern) — a borrower posts one ERC-721 as collateral and requests a loan with self-chosen terms (`TokenLoanParams`: `valuation`, `duration`, `annualInterestBPS`, `ltvBPS`, `oracle`); a lender then commits funds against those terms via `lend`/`requestAndBorrow`/`takeCollateralAndLend`, all of which funnel into the internal `_lend`.

**Function role**: `_lend` is the sole gate through which a lender's capital actually gets committed against a borrower's requested loan. Its first responsibility (before any funds move) is to verify that the loan terms actually being executed (`params`, the borrower's on-chain request, loaded from `tokenLoanParams[tokenId]`) are no worse for the lender than the terms the lender explicitly signed off on (`accepted`, the `_lend`/`lend` parameter — per the NatSpec on `lend()`, "Loan parameters as the lender saw them, for security"). Only after that validation does it optionally check an oracle-implied LTV bound, move BentoBox shares (fees, borrower payout), and mark the loan `LOAN_OUTSTANDING`.

**Relevant locals/parameters**:
- `params` (local, `TokenLoanParams memory`, L308: `TokenLoanParams memory params = tokenLoanParams[tokenId];`) — the borrower's actually-requested, on-chain-stored loan terms; this is what will actually execute if the require at L312–318 passes.
- `accepted` (parameter, `TokenLoanParams memory`) — the lender's off-chain-approved terms, passed by the caller (`lend`, or reconstructed from a signature in `requestAndBorrow`/`takeCollateralAndLend`); this is the lender's own stated floor/ceiling for each term.
- `ltvBPS` field (struct-level NatSpec on `TokenLoanParams`, L36: "Required to avoid liquidation") — the loan-to-value ratio, in basis points, that determines how much collateral cushion protects the lender if the NFT's value falls. A **lower** `ltvBPS` is safer/better for the lender (thinner debt relative to collateral value, more room before the position is underwater); a **higher** `ltvBPS` is worse for the lender (thinner cushion, closer to/over-collateralization risk).

**The disputed statement (L312–318)**:
```solidity
// Valuation has to be an exact match, everything else must be at least
// as good for the lender as `accepted`.
require(
    params.valuation == accepted.valuation &&
        params.duration <= accepted.duration &&
        params.annualInterestBPS >= accepted.annualInterestBPS &&
        params.ltvBPS >= accepted.ltvBPS,
    "NFTPair: bad params"
);
```
The in-function comment (L310–311) states the governing invariant directly: except for `valuation` (exact match), every other term of the executing loan (`params`) must be at least as good for the lender as what the lender accepted (`accepted`). The other two comparable clauses already implement this correctly and consistently: `duration <= accepted.duration` (a shorter actual loan is safer for the lender — less time for the collateral to lose value — so the executing duration must not exceed what the lender accepted), `annualInterestBPS >= accepted.annualInterestBPS` (a higher actual rate is better for the lender, so the executing rate must not fall below what the lender accepted). The fourth clause, `params.ltvBPS >= accepted.ltvBPS`, breaks this pattern: since a **lower** LTV is what's better for the lender, the "at least as good for the lender" invariant requires the executing `params.ltvBPS` to be no **greater** than `accepted.ltvBPS` — i.e. `params.ltvBPS <= accepted.ltvBPS`. The current code requires the opposite (`>=`), which actually enforces "the executing LTV must be at least as bad as what the lender accepted."

**Variable-value intent (L316)**: at the point this require is evaluated, `params.ltvBPS` (the LTV that will actually govern the executing loan) must be no greater than `accepted.ltvBPS` (the maximum LTV the lender agreed to be exposed to).

**Statement/line-level intent**: the entire require block (L312–318) is the one and only gate that protects the lender from having a worse loan than they explicitly signed off on actually execute against their capital; each of its four conjuncts independently enforces "no worse for the lender" along one dimension of `TokenLoanParams`.

**Reported erroneous behavior** (H-05, verbatim, primary source): *"It comments in the `_lend()` function that lender accepted conditions must be at least as good as the borrower is asking for. The line which checks the accepted LTV (lender's LTV) against borrower asking LTV is: `params.ltvBPS >= accepted.ltvBPS`, This means lender should be offering a lower LTV, which must be the opposite way around. I think this may have the potential to strand the lender, if he enters a lower LTV. For example borrower asking LTV is 86%. However, lender enters his accepted LTV as 80%. lend() will execute with 86% LTV and punish the lender, whereas it should revert and acknowledge the lender that his bid is not good enough."*

**Proof of Concept** (primary source): a bare link to `NFTPairWithOracle.sol#L316` — no separate narrative beyond the worked 86%/80% example already quoted above (this is the finding's full PoC; nothing is truncated or omitted relative to the scattered excerpt here).

**Recommended Mitigation Steps** (verbatim, primary source): *"The condition should be changed as: `params.ltvBPS <= accepted.ltvBPS`,"*

**Expected/intended behavior**: at the require's evaluation point, `params.ltvBPS <= accepted.ltvBPS` must hold for `_lend` to proceed; the current `>=` instead lets a strictly-worse-for-the-lender LTV execute (report's 86%-vs-80%-accepted example) and, symmetrically (not the report's own framing, but a direct consequence of the same flipped operator, noted here only as corroborating structural context, not as an independent second mechanism — see R1-3's coverage discussion), incorrectly reverts on loans whose LTV is strictly better for the lender than what they accepted.

**Patch intent**: a literal single-operator flip (`>=` → `<=`) on the fourth conjunct only, scoped to that one comparison — used as direct evidence of which quantity (`params.ltvBPS`, `accepted.ltvBPS`) and which direction is correct; not transcribed mechanically as the annotation's justification (§2/§3) — the direction is independently corroborated by the struct's own NatSpec ("`ltvBPS`: Required to avoid liquidation") and by the require's own two sibling clauses, which already implement the same "no worse for the lender" pattern correctly for `duration`/`annualInterestBPS`.

**Bug-relevant intended numeric behavior**: at the point in `_lend` where the four-way require is evaluated, the executing loan's `params.ltvBPS` must not exceed the lender's `accepted.ltvBPS`; the current code instead requires `params.ltvBPS` to be at least `accepted.ltvBPS`, letting the loan proceed with an LTV worse than what the lender agreed to.

---

## R1-2 — Intent Abstraction

Distinguishing property (patch's one-operator flip used only as evidence for *which* comparison and direction is correct, not transcribed as annotation syntax beyond that): `params.ltvBPS` must be bounded above by `accepted.ltvBPS`, not bounded below by it. **Intent-level orientation: Value-centered** — a constraint on the relationship between two already-fully-computed values (both fields are set once, at struct-load/parameter-bind time, and never reassigned anywhere in `_lend`), not a state-transition or effect claim. This is a plain comparison-operator defect within an otherwise-structurally-correct four-way validation expression — the closest analogue among this project's own vocabulary is exactly what the old (now-discarded) L5b tag's own name described, "wrong-validation-operator," minus the bug-awareness framing that made it uncounted before.

---

## R1-3 — Select the least implementation-specific sufficient relation

**Preliminary check — does this relation need a function call inside `intentValue`?** No. Both `params.ltvBPS` and `accepted.ltvBPS` are plain struct-field reads (`varRef` with `.ltvBPS` member access, grammar-legal per `Solidity.g4`'s `subAccess: '.' identifier`) on values already fully resident in memory at the require's evaluation point — `params` from a mapping load (L308), `accepted` from the function's own parameter list. No alpha-style blocker to check; the known-bound/exact-formula-inlining rescues (§4) are not needed because there was never a call to rescue around. **This also directly resolves the old-methodology background note**: the flagged `bentoBox.toShare()`/`feesEarnedShare` concern (L325/L342) belongs to code that executes strictly *after* this require and is never referenced by the selected relation — it is not a blocker for this relation at all, independent of whether BentoBox's interface CFG is pkl'd.

1. **Directional/state-change relation (weakest tier): not applicable to this relation's nature.** README's directional tier is framed around a persistent value's Entry-vs-Exit or Before-vs-After movement (e.g. `65_H_01`'s `lastFee(Exit) > lastFee(Entry)`). Neither `params.ltvBPS` nor `accepted.ltvBPS` is a persistent state variable, and neither changes value anywhere within `_lend` — `params` is loaded once (L308) and never reassigned; `accepted` is a `memory` parameter, likewise never reassigned. There is no meaningful "before/after" or "entry/exit" pair to state a directional relation over; this tier is recorded here as genuinely inapplicable to this case's relation shape, not silently skipped.
2. **Inequality / bound (SELECTED): `params.ltvBPS <= accepted.ltvBPS`.** Matches the value and direction R1-1 establishes as correct: the exact recommended-fix comparison, independently corroborated by the struct's own NatSpec and the require's two sibling "no worse for the lender" clauses (not mechanically copied from the patch alone — §2/§3 note matching the patch is not itself a problem when it is independently the correct specification).
3. **Relational invariant**: this selected relation is simultaneously an "inequality/bound" and a "relational invariant between two independent operands" in README's tier list — the two tiers effectively collapse into one candidate here, since `accepted.ltvBPS` is itself a live program value (not a fixed constant), so tier 2's bound and tier 3's invariant are the same relation.
4. **Exact equality (`params.ltvBPS == accepted.ltvBPS`): considered, rejected.** This would be strictly more implementation-specific than what the intended behavior actually requires — the patch's own `<=` explicitly *permits* the borrower's requested LTV to be strictly better for the lender than what they accepted (e.g. borrower requests 75%, lender accepted up to 80% — a legitimate, intended-to-succeed loan). An equality would wrongly flag this legitimate scenario as Violated, over-constraining past what the reported/intended behavior supports. Rejected on R1-3's own selection condition (a): not supported by the reported intended behavior.
5. **Strict inequality (`params.ltvBPS < accepted.ltvBPS`): considered, rejected.** Rejected for the same reason as equality in the other direction: the patch's `<=` explicitly permits the boundary case `params.ltvBPS == accepted.ltvBPS` (executing LTV exactly matches what the lender accepted) to succeed. A strict `<` would wrongly flag that legitimate boundary scenario as Violated.

**Winner: Alternative 2 (`params.ltvBPS <= accepted.ltvBPS`, non-strict bound).**

**Required check (§3/R1-3)**: does this relation's negation fail to catch some alternative implementation that retains the reported defect but produces it differently? Checked against three distinct alternative shapes:
- **The actual buggy code** (`params.ltvBPS >= accepted.ltvBPS`): caught, shown explicitly below.
- **A stricter-but-still-flipped variant** (e.g. `params.ltvBPS > accepted.ltvBPS`): still lets through any `params.ltvBPS` strictly greater than `accepted.ltvBPS` — caught by the same negation (our check is independent of the buggy require's own strictness, since it re-evaluates the operands directly rather than depending on the buggy require's boolean outcome at all).
- **A missing-clause variant** (the fourth conjunct dropped from the require entirely): any `params.ltvBPS` value, however far above `accepted.ltvBPS`, would let `_lend` proceed. Still caught — our `@During` is placed independently after the require and reads `params.ltvBPS`/`accepted.ltvBPS` directly.
- No alternative implementation that lets an LTV worse than the lender's acceptance execute escapes this relation's negation. **No gap found**; no `Intent coverage: Partial` flag needed on this ground.

**Discrimination check (explicit arithmetic, per §9 checklist item 1).** Scenario constructed directly from the report's own worked example: `params.ltvBPS = 8600` (86%), `accepted.ltvBPS = 8000` (80%).
- **Buggy** (actual code, L316 `>=`): `8600 >= 8000` → **true** → require passes, no revert, `_lend` proceeds at 86% LTV. `@During` check: `8600 <= 8000` → **false ⟹ Violated.** Exactly reproduces the reported consequence.
- **Intended** (per the recommended fix, `<=`), same input: `8600 <= 8000` → **false** → require reverts; transaction does not complete, matching the report's own "it should revert."
- **Soundness check** (legitimate-loan scenario): `params.ltvBPS = 7500` (75%), `accepted.ltvBPS = 8000` (80%). Intended code: `7500 <= 8000` → true → passes; `@During` check: `7500 <= 8000` → **true ⟹ Satisfied.** (Under the actual buggy code, this input instead reverts — `7500 >= 8000` is false — a second, unreported-by-name corollary of the same flipped operator: legitimate loans better for the lender get wrongly rejected. **Not treated as a second target-annotation-set member**, per README §4's finding-level-completeness scope discipline: this is a mechanical restatement of the *same* single flipped-operator defect, not a genuinely distinct, independently-reported mechanism — the report names only one bug (`params.ltvBPS >= accepted.ltvBPS` should be `<=`), and both the "worse-LTV-wrongly-accepted" and "better-LTV-wrongly-rejected" consequences follow automatically from correcting that one comparison; there is nothing a second relation would independently need to check.)

---

## R1-4 — During vs Post

**Chosen: During — driven by the relation's own nature, not by bug-specific reachability convenience.** `params.ltvBPS <= accepted.ltvBPS` is a **validation-gate correctness property**: a claim about whether one specific statement-time check (the require at L312–318) enforces the right condition. This is what the require *is*, independent of which particular input any reported defect happens to involve — README's During criterion ("an intermediate expression... a statement-time value... tied to one statement") applies to this kind of property directly, on its own terms.

A genuine competing framing was considered and is worth recording explicitly, not dismissed by default: `params.ltvBPS <= accepted.ltvBPS` could instead be read as a **function-level postcondition** — "a successfully-completed `_lend()` call must respect the lender's accepted LTV" — which would argue for `@Post`. This framing is not wrong; it matches README's own Post criterion ("a function-level invariant") and is, in one sense, *less* implementation-specific than During (it doesn't presuppose that the check lives in exactly this one require rather than being split across statements or written as an if-revert). It was not selected here because the reported defect's own nature is about the validation logic's own local correctness, not about `_lend`'s exit-time contract as such — but this is a real judgment call between two legitimate framings, not a case where Post is structurally blocked (contrast `web3bugs_16_H_04`'s branch-join problem or `web3bugs_101_H_02`'s deleted-storage problem, where Post is not merely dispreferred but actually incorrect).

**Explicitly not chosen for reachability convenience.** An earlier draft of this justification leaned on the fact that `_lend` has further, unrelated revert points downstream of L318 (the oracle-price require at L322, BentoBox transfers) — reasoning that `@During` avoids tying evaluability to code that has nothing to do with the reported defect. That observation is true but was rejected as the *primary* justification on review: choosing an observation point specifically because it is known (from the reported defect's own scenario) to still catch the bug even if something unrelated reverts afterward is a scope choice shaped by knowledge of the specific bug — the retired bug-awareness framing (§3) creeping back into an R1-4 decision, structurally, even though the formal L1–L5 classification itself is gone. It is recorded here only as a secondary, corroborating observation about the During choice's robustness, not as the reason for the choice — the primary justification is, and must be, the relation's own nature as a validation-gate property, which would hold regardless of what downstream code happens to do. No `varRef(Before/After/Assign)` snapshot qualifier is needed either way: neither operand has more than one relevant value within the function.

**Required explicit delta-exception check (README §4/R1-7, per task instructions).** `_lend` contains **no loop of any kind** — confirmed by reading its entire body (L300–350): two requires, an optional oracle check, three BentoBox transfer/skim branches, and a final state update, no `for`/`while` anywhere. **Delta confirmed not applicable, trivially.**

---

## R1-5 — Relation form

**Non-strict inequality (upper bound)** via the grammar's general `RelationalCmp` common-form rule (`intentValue relOp intentValue`, `Parser/Solidity.g4` line 325), reached through `duringClause -> commonClause`. Both operands are plain `varRef`s with a single `.ltvBPS` member-access `subAccess` (`Parser/Solidity.g4` lines 379–386) — no snapshot qualifier, no arithmetic beyond the bare comparison. **Not forced to any particular form by the patch's own shape** — the non-strict `<=` was selected in R1-3 on independently-demonstrated grounds.

---

## R1-6 — Construct the target annotation

**Attachment point**: immediately after the require block (L312–318), before the oracle-price check (L320).

**Scenario precondition this instantiation relies on**: `tokenLoan[tokenId].status == LOAN_REQUESTED` (the require at L307's own existing gate — reachability only) and the two `ltvBPS` values as constructed in R1-3's discrimination check.

**Target annotation**:
```solidity
function _lend(
    address lender,
    uint256 tokenId,
    TokenLoanParams memory accepted,
    bool skim
) internal {
    TokenLoan memory loan = tokenLoan[tokenId];
    require(loan.status == LOAN_REQUESTED, "NFTPair: not available");
    TokenLoanParams memory params = tokenLoanParams[tokenId];

    // Valuation has to be an exact match, everything else must be at least
    // as good for the lender as `accepted`.
    require(
        params.valuation == accepted.valuation &&
            params.duration <= accepted.duration &&
            params.annualInterestBPS >= accepted.annualInterestBPS &&
            params.ltvBPS >= accepted.ltvBPS,
        "NFTPair: bad params"
    );
    // @During params.ltvBPS <= accepted.ltvBPS

    if (params.oracle != INFTOracle(0)) {
        ...
    }
    ...
}
```
Both referenced identifiers (`params.ltvBPS`, `accepted.ltvBPS`) are ordinary in-scope struct-field values — a local (loaded from a state mapping) and a function parameter, respectively. No synthetic constant is introduced.

**Quantification note**: plain scalar-field comparison on the one loan being processed (`tokenId` selects a single record, not an iteration over `tokenLoanParams`'s full domain) — not a claim quantified over "every outstanding loan." No representative-element instantiation issue applies (contrast `83_H_01`'s `poolInfo[1]`).

---

## R1-7 — Expressibility decision

**Values referenceable**: Yes — `params`/`accepted`, both ordinary in-scope identifiers, `.ltvBPS` a legal `subAccess`. Neither behind an external-contract boundary.

**Arithmetic/logical relation representable**: Yes — a single `RelationalCmp`, no arithmetic beyond the bare comparison.

**No function call inside `intentValue`**: confirmed (R1-3). **This directly supersedes the old L2a/`bentoBox.toShare()` concern**: that concern was never about this relation's own operands — it was about a different, later statement (`feesEarnedShare += protocolFeeShare`, L342) not referenced here.

**Observation point supported — delta check**: `_lend` contains no loop anywhere. **Delta confirmed not applicable, trivially.**

**Outcome: Expressible = YES.**

**This differs from the old L5b (`not_detectable`) label.** The old blocker was bug-awareness ("requires knowing the require is wrong"), a question this methodology does not ask (§3). Once set aside, all R1-7 questions resolve affirmatively.

---

## Section 5 — Value/Algorithm and Usable/Unusable

- **Value-level** — a wrong-operand/wrong-operator defect within an otherwise-complete, otherwise-correct expression: three of the require's four conjuncts are already correctly directed; only the fourth's comparison operator is inverted. No step of the intended computation is missing, no procedure call absent, no ordering wrong — the textbook Value-level shape.
- **Usable** — both values referenceable, no representational gap. The LTV-direction semantic distinction does not itself need to be encoded in the grammar (same reasoning `29_H_08` established) — the resulting relation is an ordinary numeric comparison.

---

## RQ2-A — Specification Requirements profile

**Relevant statements** (within `_lend` itself):
1. `TokenLoanParams memory params = tokenLoanParams[tokenId];` (L308) — defines `params`, an operand of the relation.
2. `require(params.valuation == accepted.valuation && ... && params.ltvBPS >= accepted.ltvBPS, "NFTPair: bad params");` (L312–318) — the disputed/target statement itself: attachment point, and source of `accepted`'s appearance in-scope. Counted as context (§6), never as self-justifying evidence.

Total: **2 relevant statements.**

**Excluded, with reason**:
- `TokenLoan memory loan = tokenLoan[tokenId];` (L306) and `require(loan.status == LOAN_REQUESTED, ...)` (L307) — pure reachability gate, structurally identical to `65_H_01`'s excluded `if (lastFee == 0)`. Excluded entirely.
- L320–349 (oracle check, BentoBox transfers, `feesEarnedShare` update, final state write) — execute strictly after the attachment point, not load-bearing for the relation.

**Unique relevant program values**:
- State/mapping (container, 1): `tokenLoanParams`.
- Parameter (1): `tokenId` — the mapping key at L308. **Counted, not excluded (corrected on review)**: the loop-index-exclusion rule (README §6) applies to a *loop* index, whose own value is mechanical iteration plumbing that no relation in this dataset depends on. `tokenId` is not a loop index — it is a `_lend` function parameter, fixed once per call, that determines *which loan record* `params` denotes; changing it changes which loan's terms `params.ltvBPS` actually refers to, and a reader must trace it to know that. This is the same treatment `web3bugs_112_H_01` already gives its own mapping-key parameter `account` ("the mapping key for Member B, and the value a reader must trace to know who the recipient is") — applying that same precedent here for consistency.
- Local (extracted value, 1): `params`.
- Parameter (1): `accepted`.

Total: **4 unique relevant program values.**

**Additional functions required: 0.** **Additional protocol/application-specific contracts/libraries required: 0.** **Context breadth: 1** (same-function).

**External specification required: Yes.** The source's own comment states the general "at least as good for the lender" invariant but not the LTV-direction fact itself — that lower LTV is safer for the lender is a general lending/collateralized-debt domain convention, not spelled out in the source text. This is generic (Step 2, README §6), not AbraNFT-specific: **the relation depends on the generic collateralized-lending convention that a lower LTV is safer for the lender.**

---

## Section 7 — Alternatives-considered summary

| # | Relation | Tier | Expressible? | Discriminates? | Verdict |
|---|----------|------|---------------|-----------------|---------|
| 1 | (directional/state-change form) | Directional | N/A | N/A | Not applicable — no Entry/Exit or Before/After pair exists for either operand |
| 2 | `params.ltvBPS <= accepted.ltvBPS` | Inequality/bound | Yes | Yes | **Selected** |
| 3 | `params.ltvBPS == accepted.ltvBPS` | Exact equality | Yes | Over-constrains | Rejected — flags a legitimate better-than-accepted loan |
| 4 | `params.ltvBPS < accepted.ltvBPS` | Strict inequality | Yes | Over-constrains | Rejected — flags the legitimate exact-match boundary |

---

## RQ1-B / RQ2-B

Deferred per README §8. Not run, not predicted. No loop, no `abi.decode`/`staticcall` pattern, no external call upstream of the attachment point.

---

## Summary

- **Expressible: Yes.** Values referenceable, arithmetic representable, observation point (`@During`) supported; delta not applicable (no loop).
- **This differs from the old L5b label** — the old blocker was bug-awareness, retired under §3; the old L2a/`bentoBox.toShare()` concern is also confirmed inapplicable to the selected relation.
- **Target relation**: `params.ltvBPS <= accepted.ltvBPS`, `@During` on `_lend`, immediately after the L312–318 require.
- **Quantified property instantiated: No.**
- **Value-level, Usable, `@During`, non-strict-inequality (`RelationalCmp`).**
- **RQ2-A**: 2 relevant statements, 4 unique relevant program values (`tokenId` counted, per review, as the mapping key a reader must trace — not a mechanical loop index; same treatment as `web3bugs_112_H_01`'s `account`), 0 additional functions, 0 additional libraries, Context breadth 1, External specification required: Yes (generic lending convention).
- **RQ1-B/RQ2-B**: deferred.
- **Review corrections applied**: (1) R1-4's During justification rewritten to ground the choice in the relation's own nature (a validation-gate correctness property) rather than in bug-specific downstream-reachability convenience, which read too close to the retired bug-awareness framing on reflection — a competing Post (function-level-postcondition) framing is now recorded explicitly as a legitimate alternative, not dismissed by default. (2) `tokenId` corrected from excluded to counted in RQ2-A's unique relevant program values (3→4), per the `web3bugs_112_H_01` mapping-key precedent. (3) A dangling cross-reference to the now-retired "Summary's Intent coverage discussion" (R1-3's discrimination check) replaced with the actual reasoning inline.
