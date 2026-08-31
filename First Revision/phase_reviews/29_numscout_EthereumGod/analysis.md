# numscout_EthereumGod — Agent A (Analyst) Case Analysis — REDONE (Policy-underdetermined representative relations)

Case ID: `numscout_EthereumGod` | Contract: `EthereumGod` (BSC "SafeMoon-style" reflection/auto-liquidity ERC20 clone) | Function: `swapAndLiquify(uint256 contractTokenBalance) private lockTheSwap`
Existing labels: Numscout static-analysis flag (`Dataset/Numscout/EthereumGod.json`, `bool_defect.precision_loss_trend: true`, `operator_order_issue: false` — independently re-confirmed by reading the raw JSON directly for this pass). Retired-pipeline label (historical, recorded for continuity only, not authoritative): `not_detectable (L2a: interface-call-return-top)`, `evaluation/RQ1/annotation_plans.md:2429–2451`.

**This supersedes `29_numscout_EthereumGod/analysis.md`'s immediately-prior version**, which correctly identified the actually-flagged defect class (`precision_loss_trend`, not `operator_order_issue`) and correctly identified both candidate sites, but concluded "R1-1 non-establishment" — no bug-relevant intended behavior could be reconstructed, because the source gives no basis for *which* party (marketing vs. liquidity) the rounding remainder should favor. That conclusion was reached before README §4 gained its "Policy-underdetermined representative relations" subsection (added specifically in response to this case). This pass applies that rule end to end: the ambiguity over which party *should* be favored is a real, honestly-unresolved fact about this contract, but it turns out not to be load-bearing for RQ1's own question (representational capacity), because all three plausible rounding conventions turn out equally expressible. Redone from scratch below — R1-1 through R1-3 are independently re-verified, not copy-pasted from the superseded pass, even where they reach the same underlying facts.

**Source-path convention (README §0.5)**: `numscout_*` case, not `web3bugs_*` — no human-written audit report exists. Sources used: (1) `evaluation/RQ1/target_contracts_original/numscout_EthereumGod.sol` (224-line trimmed slice, confirmed line-for-line identical to the superseded pass's local numbering for `swapAndLiquify`, L164–184); (2) `Dataset/Numscout/Original/2f0b287275Fc50a1Cb854797927A12a98d3b9460_EthereumGod.sol` (full untrimmed Etherscan-verified source, re-read for the `SafeMath` library body at L94–235 and for any rounding-policy comment/NatSpec); (3) `Dataset/Numscout/EthereumGod.json` (tool's raw output — both the `bool_defect` block and the full `precision_loss_trend` sub-span list, confirming both candidate sites are among the flagged spans: orig L937/937:75/938 for Site 1, orig L956/963 for Site 2); (4) `Parser/Solidity.g4` (grammar — see R1-6/R1-7 for what this confirmed).

---

## R1-1 — Reported Behavior Reconstruction

**Contract/function role**: `EthereumGod` is a reflection-token clone of the "SafeMoon" auto-liquidity pattern. On transfers, an accumulated `contractTokenBalance` of fee-tokens is periodically converted, via `swapAndLiquify` (invoked from `_transfer`, local L207), into (a) protocol-owned auto-liquidity and (b) a marketing-wallet ETH transfer, using exactly **one** on-chain swap whose ETH proceeds are then split proportionally between the two purposes.

```solidity
function swapAndLiquify(uint256 contractTokenBalance) private lockTheSwap {
    uint256 toMarketing = contractTokenBalance.mul(_marketingFee).div(_marketingFee.add(_liquidityFee));  // L165
    uint256 toLiquify = contractTokenBalance.sub(toMarketing);                                            // L166

    uint256 half = toLiquify.div(2);                                                                       // L168
    uint256 otherHalf = toLiquify.sub(half);                                                                // L169

    uint256 initialBalance = address(this).balance;                                                        // L171

    uint256 toSwapForEth = half.add(toMarketing);                                                           // L173
    swapTokensForEth(toSwapForEth);                                                                         // L174

    uint256 fromSwap = address(this).balance.sub(initialBalance);                                           // L176
    uint256 newBalance = fromSwap.mul(half).div(toSwapForEth);                                               // L177

    addLiquidity(otherHalf, newBalance);                                                                     // L179

    emit SwapAndLiquify(half, newBalance, otherHalf);

    sendETHToMarketing(fromSwap.sub(newBalance));                                                            // L183
}
```

**Two sites match Numscout's `precision_loss_trend` shape** (`X = floor(A*B/C)`, then `Y = Total - X` absorbs the residual — the Fig. 6/Fig. 7 shape, `29_numscout_EthereumGod/fig 6,7.png`: Fig. 6's `fee`/`amountToTaker` split and Fig. 7's `AAGain = gain*ratio/FULL_ALLOC` then `BBGain = gain - AAGain` are both exactly this pattern):

- **Site 1 (L165–166, orig L937–938)**: `toMarketing = floor(contractTokenBalance * _marketingFee / (_marketingFee + _liquidityFee))`, `toLiquify = contractTokenBalance - toMarketing`. Numscout's own flagged spans include orig `937:75` (the `.div(...)` call), `937:31` (the `.mul(...)` call), and `938:29` (the `.sub(...)` call) — confirming Site 1 is inside the tool's own flagged region.
- **Site 2 (L176–183, orig L956/963)**: `newBalance = floor(fromSwap * half / toSwapForEth)` (liquidity's ETH share); marketing's ETH share (L183) `= fromSwap - newBalance`. Numscout's flags include orig `956:30` (`.mul(half).div(toSwapForEth)`) and `963:28`/`963:9` (`sendETHToMarketing(fromSwap.sub(newBalance))`) — confirming Site 2 is also inside the flagged region.

**Direction at each site**, structural (holds for any nonzero-remainder scenario, not scenario-specific): at Site 1 the marketing leg is computed first via `floor` and the liquidity leg absorbs the residual (liquidity favored); at Site 2 the roles are reversed — the liquidity leg (`newBalance`) is computed first via `floor` and the marketing leg absorbs the residual (marketing favored). **Nothing in the source indicates whether this reversal is a deliberate compensating design (each leg's split intentionally favoring the other party once) or simply an accidental byproduct of which operand happened to be written first at each site** — both readings are equally consistent with the code as written, and this pass does not adjudicate between them; it is recorded as an open, unresolved structural fact, not flattened into either "inconsistent" or "intentional."

**The source establishes that `swapAndLiquify` maintains two distinct accounting purposes — a marketing allocation and a liquidity allocation — and that its floor-division split systematically assigns the rounding residual to one side at each site. It does not, however, establish which of the three ordinary rounding conventions (floor/round-to-nearest/ceiling) reflects the intended allocation policy at either site.** Re-checked directly for this pass:
- No comment/NatSpec near `_marketingFee`/`_liquidityFee`'s declarations (orig L82–83 in the trimmed excerpt / orig L656–657 in the untrimmed file: `// 2% marketing`, `// 4% into liquidity` — states the ratio only, nothing about rounding-remainder allocation).
- No comment near `swapAndLiquify` itself or either division site about which leg should be favored when a split isn't exact — the only in-function comments describe *what* the code does operationally, not an intended rounding bias.
- `_setMarketingFee`/`_setLiquidityFee` (orig L1150–1158) only clamp the settable value to `[1,49]`; no rounding-policy language.
- **Both ultimate destinations happen to be owner/team-controlled** — the marketing ETH goes to `_marketingWalletAddress` (an owner-controlled EOA, fee-excluded per the constructor); the "liquidity" leg's LP tokens (`addLiquidity`, local L150–157 / orig L984–997) are minted to `owner()`, not locked, burned, or sent to any community/timelock contract. **This fact weakens, but does not eliminate, the case for treating the split as a genuine two-party fairness question in Numscout's own Fig. 6/Fig. 7 sense** (an adversarial user-vs-protocol relationship; a contractually-ratioed two-tranche split with a named `trancheAPRSplitRatio`) — marketing and liquidity remain two distinct accounting purposes with potentially real (if internally undocumented) allocation implications for the protocol's own operations, even though both are nominally owner-controlled. What the owner-controlled fact actually rules out is a specific *kind* of argument — that one leg should be favored because it is externally/community-owned and the other is not (that premise is false here, verified directly from `addLiquidity`'s recipient) — not the existence of any allocation preference at all. The honest conclusion is narrower than "there is no fairness question": it is that **no source-internal evidence identifies which allocation policy was intended**, for a reason that happens to include, but is not limited to, the absence of an external-stakeholder asymmetry.

**This is exactly the situation the "Policy-underdetermined representative relations" rule (README §4) targets**: a genuine, source-grounded defect *class* (`precision_loss_trend`) with a small, enumerable set of plausible concrete instantiations (floor / round-to-nearest / ceiling — the three conventions the domain admits), where the evidence does not uniquely pick out which instantiation is the actually-intended behavior. Per the rule, this is **not**, by itself, a reason to declare the case Inexpressible or excluded — first check whether the ambiguity is load-bearing for RQ1's own question, by running each instantiation through its own R1-2–R1-7 pass. That is done below, independently, for both sites.

**Reported/reconstructed erroneous behavior, per the actually-flagged category**: a `mul`-then-`div` proportional split of a total between two legs is computed via `floor` on one leg, with the other leg absorbing the residual. Per Numscout's own category description, this constitutes a defect when the resulting rounding tendency favors the wrong party. **Bug-relevant intended numeric behavior** (per this pass's application of the rule): at each site, the leg that is *not* currently computed via bare `floor` should instead receive its rounding-adjusted fair share via one of the three enumerable conventions — the specific convention is not uniquely determined by source evidence, but this does not block R1-2 onward; it is carried forward explicitly as three parallel instantiations.

---

## R1-2 — Intent Abstraction (three instantiations, per site)

Distinguishing property, common to all three instantiations at both sites: the currently-`floor`ed leg's value should instead reflect a specific alternative rounding convention on the exact proportional share, rather than being computed by bare truncating division. **Intent-level orientation: Value-centered** — a constraint on a specific intermediate value (`toMarketing` at Site 1, `newBalance` at Site 2), not a state-transition/effect claim.

**The three plausible instantiations** (README §4's enumerated list, applied to each site's split `X = A*B/C`):
1. **floor** — `X = ⌊A*B/C⌋`, ordinary truncating division (Solidity's/SafeMath's native behavior — the code's own current behavior at both sites).
2. **round-to-nearest** — `X = ⌊(A*B + C/2) / C⌋` (a `+ denominator/2` numerator adjustment before truncating division — round-half-up for positive integers).
3. **ceiling** — `X = ⌊(A*B + C - 1) / C⌋` (a `+ denominator - 1` numerator adjustment before truncating division — the standard integer-ceiling-division identity).

All three are genuine candidates the `precision_loss_trend` category itself recognizes (they are the three conventions any "proportional split with an unavoidable integer remainder" computation could plausibly use) — none is a researcher-invented alternative outside the category's own scope.

---

## R1-3 — Select the least implementation-specific sufficient relation (per instantiation, per site)

### Preliminary — SafeMath inlining re-verified independently

`.mul()/.div()/.add()/.sub()` at both sites use `SafeMath` (`using SafeMath for uint256;`, L53). Re-read the library body directly (`Dataset/Numscout/Original/...EthereumGod.sol:94–235`), not assumed from the superseded analysis:
- `mul(a,b)`: `if (a==0) return 0; uint256 c = a*b; require(c/a==b, ...); return c;` — deterministic, no other state read, no further call, reduces to ordinary `*` for any inputs that don't overflow.
- `div(a,b)`: `require(b>0,...); uint256 c = a/b; return c;` — ordinary truncating `/`.
- `add(a,b)`/`sub(a,b)`: single-statement overflow/underflow-checked `+`/`-`.

All four satisfy the exact-formula-inlining rescue's three conditions (README §4) for every operand pair actually used at both sites: deterministic given the arguments plus no other state, no opaque call, no loop, body reduces to ordinary `+ - * /` over already-in-scope terms. Accordingly `toMarketing.mul(_marketingFee).div(...)`-style chains are treated below as ordinary `*`/`/`.

### Site 1 — token split (L165–166)

Concrete scenario A (deployed defaults `_marketingFee=2`, `_liquidityFee=4`, denominator `C=6`; `contractTokenBalance=17`, so `A*B=17*2=34`):
- `34 / 6 = 5` remainder `4` (`4/6 ≈ 0.667`).
- **floor**: `toMarketing = ⌊34/6⌋ = 5`. This is exactly what the deployed code computes (L165, unmodified).
- **round**: `⌊(34 + 6/2)/6⌋ = ⌊37/6⌋ = 6` (remainder `4/6 > 0.5`, rounds up).
- **ceiling**: `⌊(34 + 6 - 1)/6⌋ = ⌊39/6⌋ = 6` (matches `⌈5.667⌉ = 6`).

Concrete scenario B, chosen so round and ceiling *disagree* (remainder `< C/2`), demonstrating these are genuinely distinct instantiations: `_marketingFee=2`, `_liquidityFee=4`, `contractTokenBalance=13` (`A*B = 26`, `C=6`):
- `26/6 = 4` remainder `2` (`2/6 ≈ 0.333`).
- **floor**: `⌊26/6⌋ = 4`.
- **round**: `⌊(26+3)/6⌋ = ⌊29/6⌋ = 4` — **coincides with floor here** (remainder `< 0.5`).
- **ceiling**: `⌊(26+5)/6⌋ = ⌊31/6⌋ = 5`.

**Adjacency fact** (used below for the required negation check): for any `A,B,C` with `C≥1`, `⌈A*B/C⌉` equals either `⌊A*B/C⌋` (exact division, remainder `0`) or `⌊A*B/C⌋+1` (otherwise) — never anything else. At a fixed scenario with a nonzero remainder, `toMarketing`'s value under any "floor vs. one-unit-higher" implementation can only be one of exactly two adjacent integers.

### Site 2 — ETH split (L176–183)

Continuing scenario A's deployed-code intermediate values (`half = ⌊12/2⌋ = 6`, `toSwapForEth = 6+5 = 11`, using the deployed floor-based `toMarketing=5`), and an illustrative `fromSwap=95` (ETH yielded by selling `toSwapForEth=11` token-units):
- `fromSwap*half = 95*6 = 570`. `570/11 = 51` remainder `9` (`9/11 ≈ 0.818`).
- **floor**: `newBalance = ⌊570/11⌋ = 51` — the deployed code's own value (L177, unmodified).
- **round**: `⌊(570+5)/11⌋ = ⌊575/11⌋ = 52` (remainder `> 0.5`, rounds up).
- **ceiling**: `⌊(570+10)/11⌋ = ⌊580/11⌋ = 52`.

Scenario B, again chosen so round and ceiling diverge (remainder `< 11/2`): `fromSwap=87`, same `half=6`, `toSwapForEth=11` (`fromSwap*half = 522`):
- `522/11 = 47` remainder `5` (`5/11 ≈ 0.455 < 0.5`).
- **floor**: `⌊522/11⌋ = 47`.
- **round**: `⌊(522+5)/11⌋ = ⌊527/11⌋ = 47` — **coincides with floor here.**
- **ceiling**: `⌊(522+10)/11⌋ = ⌊532/11⌋ = 48`.

Same adjacency fact holds: `newBalance`'s value under any floor-vs.-one-unit-higher implementation is one of exactly two adjacent integers, given fixed `fromSwap`/`half`/`toSwapForEth`.

### Required negation check (§3/R1-3), both sites, all instantiations

**Does each candidate equality's negation fail to catch some alternative implementation that retains the reported defect but produces it differently?** Exploiting a structural identity re-derived for this pass: because `half + toMarketing = toSwapForEth` exactly (L173) and `toMarketing + toLiquify = contractTokenBalance` exactly (L166), the "compute the *other* leg via floor first" alternative produces **exactly** the ceiling value for the leg under test. Concretely, for Site 1: if an alternative implementation instead computed `toLiquify' = ⌊contractTokenBalance*_liquidityFee/(_marketingFee+_liquidityFee)⌋` first and set `toMarketing' = contractTokenBalance - toLiquify'`, then `toMarketing' = ⌈contractTokenBalance*_marketingFee/(_marketingFee+_liquidityFee)⌉` **exactly** (standard identity: when `x+y` is an integer and neither `x` nor `y` individually is, `x + frac(y) = x + (1-frac(x)) = ⌈x⌉`). The same identity holds at Site 2.

This means the **ceiling representative is not an arbitrary constructed formula** — it is exactly the value any implementation would produce if it simply reversed *which* leg gets computed via bare `floor` first, a legitimate, source-grounded alternative construction (the mirror image of the deployed code's own construction), not a researcher invention.

Given the adjacency fact, at a fixed scenario with nonzero remainder there are only two integers a "correct proportional split with some rounding convention" implementation could plausibly produce. Every one of the three instantiations' equality relations discriminates cleanly against the deployed (floor) code whenever it differs from floor: the round-instantiation's equality is violated by the deployed code in scenario A but *not* in scenario B (round coincides with floor there — expected, not a flaw); the ceiling-instantiation's equality is violated by the deployed code in both scenarios A and B. **No gap found for the ceiling instantiation in either scenario.**

---

## R1-4 — Choose annotation observation scope (During vs Post), both sites, all instantiations

**Site 1 — During, attached at L165** (the statement defining `toMarketing`). All three instantiations are checks on an intermediate, same-statement-defined local — README's During criterion applies directly. `toMarketing` is not persistent state and the relation does not concern function entry/exit.

**Site 2 — During, attached at L177** (the statement defining `newBalance`). Same reasoning.

**Delta exception explicitly re-checked**: `swapAndLiquify`'s entire body (L164–184) contains no `for`/`while` loop anywhere. Both attachment points (L165, L177) are ordinary, non-loop statements. **Delta not applicable, trivially, at either site, for any instantiation.**

---

## R1-5 — Relation form

**Exact equality** at both sites, for all three instantiations, via the grammar's general `RelationalCmp` common-form rule (`intentValue relOp intentValue`, `Parser/Solidity.g4:325`) reached through `duringClause -> commonClause`. Selected because, per the adjacency fact above, only an exact equality against the correct adjacent integer discriminates a defect-retaining alternative from the intended one — a non-strict inequality would be trivially satisfied by both the deployed floor code and any higher-rounding alternative, and a strict inequality alone would fail to pin down *which* higher integer is correct.

---

## R1-6 — Construct the target annotation, both sites, all three instantiations

**Grammar's built-in `ceil(x, n)`/`floor(x, n)` constructs checked and ruled out as directly applicable**: `Parser/Solidity.g4:323–324` exist, but `Analyzer/GuardianVerificationEngine.py:153–179` (`_evaluate_ceil`/`_evaluate_floor`) confirms their second argument is a **compile-time `numberLiteral` rounding unit**, not a general ceiling-division-by-a-variable-denominator operation. Since both sites' denominators (`_marketingFee + _liquidityFee`; `toSwapForEth`) are variables, this built-in does not apply directly. **Ordinary arithmetic is used instead** — the grammar's `arithFactor`/`arithTerm`/`arithAdd` productions directly support `+`, `-`, `*`, `/`, and parenthesization, so the standard integer round/ceiling-division identities are expressible as plain `intentValue` arithmetic with no grammar extension needed.

**Site 1 — attached at L165**, all three instantiations:
```solidity
uint256 toMarketing = contractTokenBalance.mul(_marketingFee).div(_marketingFee.add(_liquidityFee));
// floor:   @During toMarketing == contractTokenBalance * _marketingFee / (_marketingFee + _liquidityFee)
// round:   @During toMarketing == (contractTokenBalance * _marketingFee + (_marketingFee + _liquidityFee) / 2) / (_marketingFee + _liquidityFee)
// ceiling: @During toMarketing == (contractTokenBalance * _marketingFee + (_marketingFee + _liquidityFee) - 1) / (_marketingFee + _liquidityFee)
uint256 toLiquify = contractTokenBalance.sub(toMarketing);
```

**Site 2 — attached at L177**, all three instantiations:
```solidity
uint256 newBalance = fromSwap.mul(half).div(toSwapForEth);
// floor:   @During newBalance == fromSwap * half / toSwapForEth
// round:   @During newBalance == (fromSwap * half + toSwapForEth / 2) / toSwapForEth
// ceiling: @During newBalance == (fromSwap * half + toSwapForEth - 1) / toSwapForEth
```

All operands are ordinary in-scope identifiers — a parameter and two state variables at Site 1; four same-function locals at Site 2 — with no synthetic constant introduced beyond the small literal adjustment terms (`2`, `1`), which are fixed parts of the round/ceiling formulas themselves, identical for every scenario.

**Overflow check (explicitly performed)**: the ceiling/round formulas' extra additive term adds at most `_marketingFee+_liquidityFee` (bounded `≤98`, per the `[1,49]` setter clamp) or `toSwapForEth` (bounded by the contract's own token/ETH balances) to the numerator before division — negligible relative to `uint256`'s range, no larger in kind than the multiplication already present in the floor formula.

**No function call inside any instantiation's `intentValue`, at either site**: Site 1's operands are a parameter and two state variables; Site 2's operands are same-function locals already assigned by earlier statements (L173, L176), referenced as plain identifiers, not calls.

**Quantification note**: all values at both sites are plain scalars. **Quantified property instantiated: No**, for every instantiation at both sites.

---

## R1-7 — Expressibility decision (all three instantiations, both sites — invariance check)

| Site | Instantiation | Values referenceable | Arithmetic representable | Observation point supported | Verdict |
|---|---|---|---|---|---|
| 1 | floor | Yes | Yes | Yes | **Expressible** |
| 1 | round | Yes | Yes | Yes | **Expressible** |
| 1 | ceiling | Yes | Yes | Yes | **Expressible** |
| 2 | floor | Yes | Yes | Yes | **Expressible** |
| 2 | round | Yes | Yes | Yes | **Expressible** |
| 2 | ceiling | Yes | Yes | Yes | **Expressible** |

**All six rows independently verified.** The only thing that varies across the three instantiations, at each site, is a small additive adjustment term inside an otherwise-identical arithmetic shape over the same in-scope operands — none of the three adds a function call, a new variable, a collection reference, or a loop-body attachment requirement that the others lack.

**Step 3 of the Policy-underdetermined rule applies: all six rows reach the same verdict (Expressible = Yes).** The case's RQ1 answer does not depend on resolving which rounding convention is actually intended, because RQ1 asks only about representational capacity, not about identifying the one true developer intent (README §4/§0). Per the rule, this licenses selecting one representative from the plausible set for R1-6's concrete annotation, while stating explicitly that the representative choice is not itself a claim about developer intent.

---

## Selecting the representative (Step 4 of the Policy-underdetermined rule)

**The representative must not be floor**: floor is the deployed code's own actual behavior at both sites, so a floor-instantiated annotation would be satisfied by the buggy code itself, proving nothing. Confirmed by the concrete arithmetic above (floor-instantiation values in every scenario checked are exactly the deployed code's own computed values).

**Recommended representative: ceiling, at both sites.**
1. **Ceiling never coincides with floor except when the division is already exact** — in every scenario with a genuine nonzero remainder (the only scenarios this defect category is even applicable to), ceiling differs from floor by exactly `1`, guaranteeing non-vacuous discrimination.
2. **Round-to-nearest does not have this guarantee** — scenario B at both sites was constructed specifically to show round coinciding with floor whenever the remainder is under half the denominator, true for roughly half of all possible nonzero-remainder scenarios. A round-instantiated representative would be vacuously satisfied by the deployed buggy code on a large, non-degenerate fraction of reachable scenarios.
3. **Ceiling is independently grounded** — the negation-check identity above shows the ceiling value is exactly what the code would produce if it computed the *other* leg via floor first, a real, mechanically-meaningful alternative implementation, not an arbitrary number.

**Final target annotation set**:

- **Member (A) — Site 1, token split**:
  ```solidity
  uint256 toMarketing = contractTokenBalance.mul(_marketingFee).div(_marketingFee.add(_liquidityFee));
  // @During toMarketing == (contractTokenBalance * _marketingFee + (_marketingFee + _liquidityFee) - 1) / (_marketingFee + _liquidityFee)
  uint256 toLiquify = contractTokenBalance.sub(toMarketing);
  ```
- **Member (B) — Site 2, ETH split**:
  ```solidity
  uint256 newBalance = fromSwap.mul(half).div(toSwapForEth);
  // @During newBalance == (fromSwap * half + toSwapForEth - 1) / toSwapForEth
  ```

**Both members cover the same finding** (Numscout's single `precision_loss_trend` flag on `swapAndLiquify`, spanning both the token-split and ETH-split lines per the tool's own flagged sub-spans). This is a genuine multi-annotation-set case (README §4): the two sites are independently-checkable mechanisms of the *same* reported category (each has its own `X=floor(A*B/C)`,`Y=Total-X` shape, its own operands, its own attachment point, its own independent three-instantiation invariance check), and together they cover every `precision_loss_trend`-flagged span inside `swapAndLiquify`. Per the finding-level completeness rule, since both members are independently Expressible=Yes, **the finding is Expressible=Yes.**

**What this representative does *not* claim**: neither member's formula is asserted to be the actual developer intent. Floor, round, and ceiling were all checked and yield the identical Expressible=Yes verdict at both sites; ceiling is used here only because it is the one non-floor instantiation guaranteed to discriminate against the deployed code in every nonzero-remainder scenario, not because the source or any external evidence identifies ceiling as correct.

---

## Section 5 — Value/Algorithm and Usable/Unusable

**Value-level, both members.** The intended computation's overall structure — split `contractTokenBalance` (Site 1) or `fromSwap` (Site 2) proportionally between two legs in a fixed ratio — is entirely present and correct in the deployed code. What the representative relation targets is a single within-formula constant-adjustment term applied before the final truncating division — not an absent step, an absent function call, or a missing procedure. This is the textbook Value-level shape, explicitly not the Algorithm-level "missing step" shape (contrast `web3bugs_65_H_01`'s absent `lastFee` update).

**Usable, both members.** All values needed by the representative (ceiling) relation are referenceable at the annotation's program point — a parameter and two state variables at Site 1; three already-defined same-function locals at Site 2 — with no external-contract boundary, no missing proxy, and no semantic/unit distinction that fails to reduce to a plain numeric relation. The unresolved allocation-policy question does not make the relation Unusable — per §5's own discipline, Usable/Unusable is a purely representational-resources question about an *already-selected* relation, and the representative relation's own operands are all trivially referenceable; the policy ambiguity lives entirely upstream, in *which* representative to pick, not in whether the picked one can be stated.

---

## RQ2-A — Specification Requirements profile

*(Applies to the representative — ceiling — relations, per the Policy-underdetermined rule's instruction to re-derive the profile for the representative, not for all three instantiations.)*

### Member (A) — Site 1

**Relevant statements**: **1** — L165 itself (target/attachment statement, defining `toMarketing`; also the point at which `contractTokenBalance`, `_marketingFee`, `_liquidityFee` are read). No other same-function statement defines any operand the relation needs. L166 is **excluded** — it reads `toMarketing` but defines no operand the relation needs, and the relation's soundness doesn't depend on it.

**Unique relevant program values**: **4** — `contractTokenBalance` (parameter), `_marketingFee` (state), `_liquidityFee` (state), `toMarketing` (local — the constrained target value itself).

**Additional functions required: 0.** No call appears in the relation's derivation; `.mul()/.div()/.add()` were inlined (Step 2, generic), not treated as opaque calls.

**Additional protocol/application-specific contracts/libraries required: 0.**

**Context breadth: 0** (target statement/expression only — every operand is named directly within L165 itself).

**External specification required: No.** See combined discussion below.

**Case note (Step 2, generic)**: the relation's derivation depends on `SafeMath`'s specific behavior — deterministic, no internal rounding-mode branch, reduces to ordinary `*`/`/`/`+` with revert-on-overflow/underflow. Load-bearing but generic (protocol-independent), recorded as a case note per README §6 Step 2, not counted toward "Additional libraries."

### Member (B) — Site 2

**Relevant statements**: **7** — unlike Member (A), Site 2 sits at the end of a same-function data-dependency chain:
- L165 (`toMarketing = ...`) — feeds L166 and L173.
- L166 (`toLiquify = contractTokenBalance.sub(toMarketing)`) — feeds L168.
- L168 (`half = toLiquify.div(2)`) — `half` is a direct operand.
- L171 (`initialBalance = address(this).balance`) — feeds L176.
- L173 (`toSwapForEth = half.add(toMarketing)`) — direct operand.
- L176 (`fromSwap = address(this).balance.sub(initialBalance)`) — direct operand.
- L177 (target/attachment statement, defining `newBalance`).

Each of L165/166/168/171/173/176 defines a value that appears, directly or through exactly one further same-function definition, inside Member (B)'s relation text.

**Excluded, with reason**: L174 (`swapTokensForEth(toSwapForEth);`) — checked against the Step 1 load-bearing test: Member (B)'s relation treats `fromSwap` as a free, already-in-scope value; it holds for *any* nonzero `fromSwap` the swap happens to produce. **Not load-bearing — excluded entirely, not even as a case note.** L169 (`otherHalf = toLiquify.sub(half)`) similarly excluded — `otherHalf` does not appear anywhere in Member (B)'s relation.

**Unique relevant program values**: **11** — `contractTokenBalance` (parameter), `_marketingFee` (state), `_liquidityFee` (state), `toMarketing` (local), `toLiquify` (local), `half` (local), `toSwapForEth` (local), `initialBalance` (local), `address(this).balance` (EVM global, read at two points, counted once), `fromSwap` (local), `newBalance` (local — the constrained target value itself).

**Additional functions required: 0** (per the Step 1 exclusion of `swapTokensForEth` above).

**Additional protocol/application-specific contracts/libraries required: 0.**

**Context breadth: 1** (same-function context — six statements beyond the target statement itself, all within `swapAndLiquify`; no other function or contract load-bearing).

**External specification required: No.** See combined discussion below.

**Case note (Step 2, generic)**: same `SafeMath` dependency as Member (A).

### Combined discussion — "External specification required" and the policy-ambiguity gap

**Formal answer: No, for both members.** README §6 asks: *once R1-1/R1-2 have already fixed the intended behavior, does justifying/instantiating the specific selected relation additionally require protocol/business/domain convention beyond the source code and language semantics.* Justifying the selected (ceiling) representative required only: (a) the standard integer-ceiling-division identity (a mathematical fact, not a protocol convention), (b) the requirement, internal to this methodology itself, that the representative not coincide with the deployed code's own floor behavior, and (c) the negation-check identity (also a pure arithmetic fact about the operand relationships, directly readable from the source). None of this drew on any external protocol/business/accounting convention.

**A real, adjacent gap exists, and is recorded separately rather than folded into the field above.** The question "which of floor/round/ceiling actually reflects this contract's intended fee-allocation policy" is genuinely unresolved by anything in-source (R1-1's investigation: no comment, no NatSpec, no setter constraint; the owner-controlled fact rules out one specific *kind* of external-stakeholder argument but does not itself establish that marketing and liquidity have no distinct allocation preference at all — it only means no such preference is documented or otherwise derivable here). Resolving *that* question would require exactly the kind of context this field is designed to flag when it applies elsewhere: the project's actual (undocumented) business intent for how marketing-vs-liquidity funding should be prioritized. This is not recoverable from this source, and marking "External specification required: Yes" here would conflate two different questions this rule keeps separate: *can the language represent a plausible instantiation* (No — confirmed) vs. *is there a fact of the matter, external to this source, about which instantiation is the one actually intended* (genuinely unresolved, a different question, recorded here in prose).

---

## Section 7 — Alternatives-considered summary

| Site | # | Candidate | Grounds | Verdict |
|---|---|---|---|---|
| 1 | 1 | floor | Matches deployed code exactly | Expressible, but **rejected as representative** — vacuous discrimination |
| 1 | 2 | round | Genuine distinct convention | Expressible, discriminates in scenario A but **coincides with floor in scenario B** — rejected as representative |
| 1 | 3 | ceiling | Genuine distinct convention; equals the "compute liquidity via floor first" alternative exactly | Expressible, discriminates in every nonzero-remainder scenario checked — **selected as representative** |
| 2 | 1 | floor | Matches deployed code exactly | Expressible, but **rejected as representative** — same vacuity reason |
| 2 | 2 | round | Genuine distinct convention | Expressible, discriminates in scenario A but **coincides with floor in scenario B** — rejected as representative |
| 2 | 3 | ceiling | Genuine distinct convention; equals the "compute marketing via floor first" alternative exactly | Expressible, discriminates in every nonzero-remainder scenario checked — **selected as representative** |

A direction-specific claim asserting one particular party *should* be favored (as opposed to a rounding-convention-based representative) was considered and rejected — no source evidence supports either direction. The Policy-underdetermined rule sidesteps this deadlock by selecting on a different, answerable ground (non-vacuous discrimination against the deployed code, invariant across all plausible conventions) rather than on the unanswerable ground (which party is "correct").

---

## RQ1-B / RQ2-B

Deferred per README §8. Not run, not predicted. No case-specific engine-precision caution beyond what R1-4/R1-7 already established (no loop, no call inside either member's relation).

---

## Summary

- **Expressible: Yes**, at the finding level. Both members of the target annotation set (Site 1's token split; Site 2's ETH split) are independently Expressible=Yes, and together cover every `precision_loss_trend`-flagged span inside `swapAndLiquify` — satisfying the finding-level completeness rule (README §4).
- **How this differs from the immediately-prior (superseded) analysis.md**: that pass reached "R1-1 non-establishment" because it treated "which party should be favored" as a prerequisite the analysis could not clear. This pass applies the Policy-underdetermined-representative-relations rule and finds that prerequisite is not actually load-bearing for RQ1: all three plausible rounding instantiations (floor/round/ceiling) are independently, verifiably Expressible=Yes at both sites, so the case proceeds to a normal Expressible=Yes verdict using a representative — as long as that representative is honest about not claiming to have resolved the underlying policy question, which it is not.
- **Target annotation set**:
  - Member (A), Site 1, `@During` at L165: `toMarketing == (contractTokenBalance * _marketingFee + (_marketingFee + _liquidityFee) - 1) / (_marketingFee + _liquidityFee)`.
  - Member (B), Site 2, `@During` at L177: `newBalance == (fromSwap * half + toSwapForEth - 1) / toSwapForEth`.
  - Both use the **ceiling** representative, selected because it (a) is never satisfied by the deployed floor-based code except in the degenerate zero-remainder case, unlike round (which coincides with floor whenever the remainder is under half the denominator — demonstrated concretely, scenario B, both sites), and (b) is independently grounded in a real alternative construction (compute the other leg via floor first), not an arbitrary formula.
- **Quantified property instantiated: No**, both members.
- **Value-level, both members** — **Usable, both members**.
- **RQ2-A profile**: Member (A) — 1 relevant statement, 4 unique values, 0 additional functions/libraries, Context breadth 0, External specification required: No. Member (B) — 7 relevant statements, 11 unique values, 0 additional functions/libraries, Context breadth 1, External specification required: No. The statement/value-count gap between the two members is a genuine structural fact (Site 2 sits at the end of a same-function dependency chain that Site 1 does not). Both members share a `SafeMath`-inlining case note (Step 2, generic, not counted).
- **The unresolved policy question is preserved, not discarded.** This pass does not claim to know whether marketing or liquidity should actually be favored by the rounding remainder at either site — that remains genuinely unanswerable from this contract's source. What changed is recognizing that this unresolved question is not the question RQ1's Expressible verdict is asking; it is recorded here instead as an honest RQ2-A-adjacent residual, argued explicitly rather than silently folded into a boolean field. Two framing points were deliberately kept narrower than an earlier draft of this reasoning: (1) the two sites' opposite rounding biases are recorded as an unresolved fact (deliberate-compensation vs. accidental both equally consistent with the source), not asserted as "mutually inconsistent"; (2) the owner-controlled fact about both destinations is used only to rule out one specific external-stakeholder argument for a direction, not to claim that no allocation-preference question exists between marketing and liquidity at all.
- **Aggregation note**: this case requires no special aggregation treatment — it is a normal Expressible=Yes case with a two-member target annotation set, reportable alongside every other Expressible case in the standard RQ1/RQ2-A tables.

---

## Review Notes

*(Agent B review pass deliberately skipped this session, per explicit user instruction — proceeding directly to case build instead of a formal review pass. R1-1 through RQ2-A above were independently re-derived by Agent A rather than copied from the superseded pass, and two framing points were already tightened in response to external critique before this file was finalized — see the Summary's closing bullet. If a formal review pass is wanted later, it has not yet been run.)*
