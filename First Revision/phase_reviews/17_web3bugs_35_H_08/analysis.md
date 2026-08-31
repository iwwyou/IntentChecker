# web3bugs_35_H_08 — Agent A (Analyst) Case Analysis

Case ID: `web3bugs_35_H_08` | Contract: `ConcentratedLiquidityPool` (Sushi Trident) | Functions: `mint(bytes calldata data)` and `burn(bytes calldata data)`
Existing label: H-08, "Wrong inequality when adding/removing liquidity in current price range" (Code4rena contest 35, submitted by cmichel; initially disputed by the sponsor, then confirmed after the sponsor re-checked and produced a PoC — sponsor recommended bumping severity, judge agreed)
Source: `evaluation/RQ1/target_contracts_original/web3bugs_35_H_08.sol`; Report: `C:\Users\isjeon\Web3Bugs\reports\35.md`, finding `[H-08]`, lines 287–309 of that file (§0.5 — primary/authoritative source; no separate scattered `Dataset/Web3Bugs/.../README.md` excerpt was consulted as a starting point per §0.5's discipline, only the primary report).
Reported bug lines (local numbering in `target_contracts_original/web3bugs_35_H_08.sol`): 176 (`mint`), 242 (`burn`).

**Old classification (retired methodology, background only, not a starting assumption per the task framing):** `not_detectable (L3: unsupported-construct-top)`, per `evaluation/RQ1/annotation_plans.md`'s entry for this case. Read in full below (R1-7) — its *actual stated reason* turns out to be an engine abstract-interpretation concern (`abi.decode` results modeled as ⊤), not a grammar-expressibility gap, and is re-examined fresh against the current grammar rather than assumed to predict this case's outcome, per the task brief's explicit instruction.

---

## R1-1 — Reported Behavior Reconstruction

**Contract role.** `ConcentratedLiquidityPool` is Trident's concentrated-liquidity AMM pool (Uniswap-V3-style: liquidity is provided over a `[lower, upper]` tick range rather than across the whole price curve). `liquidity` (state, `uint128 public liquidity`, L47) is the pool's **currently active aggregate liquidity** — the sum of every position's liquidity whose range currently contains the pool's price — and it is exactly the quantity `swap()` reads (`cache.currentLiquidity = uint256(liquidity)`, L307) to size every swap step inside the active range. Positions outside the active range do not contribute to `liquidity`; they only start/stop contributing when the price crosses their tick boundary (handled separately, via `Ticks.cross` inside `swap()`).

**Function roles.**
- `mint(bytes calldata data)` (L141–228): opens/adds to a position. Computes the position's `_liquidity` (named return, `uint256 _liquidity`) from the desired token amounts via `DyDxMath.getLiquidityForAmounts`, then — **only if the position's range currently contains the pool's price** — folds `_liquidity` into the pool-wide `liquidity` counter (L176).
- `burn(bytes calldata data)` (L231–272): closes/reduces a position by `amount`. Symmetrically — **only if the position's range currently contains the pool's price** — subtracts `amount` from the pool-wide `liquidity` counter (L242).

**Relevant locals/state, `mint()` (L141–176):**
- `mintParams` (local struct, L142) = `abi.decode(data, (MintParams))` — supplies `mintParams.lower`/`mintParams.upper`, the position's tick bounds.
- `priceLower` (local, L144) = `uint256(TickMath.getSqrtRatioAtTick(mintParams.lower))` — the position's lower-bound price, in Q64.96 sqrt-price form.
- `priceUpper` (local, L145) — same, for `mintParams.upper`.
- `currentPrice` (local, L146) = `uint256(price)` — the pool's *current* price, read from state.
- `_liquidity` (named return, defined L148–154 via `DyDxMath.getLiquidityForAmounts(priceLower, priceUpper, currentPrice, mintParams.amount1Desired, mintParams.amount0Desired)`) — the position's own liquidity amount, derived from the caller's desired token amounts. Its exact numeric derivation is not load-bearing to this case's target relation (see RQ2-A) — the relation only needs it as an already-materialized, in-scope value.
- `require(_liquidity <= MAX_TICK_LIQUIDITY, "LIQUIDITY_OVERFLOW");` (L157) — bounds `_liquidity` to `MAX_TICK_LIQUIDITY`, itself typed `uint128`; this is the fact that makes the later `uint128(_liquidity)` cast (L176) numerically lossless on every execution that reaches L176 without reverting (see R1-6).

**The buggy statement (`mint`, L175–177, inside `unchecked`):**
```solidity
unchecked {
  if (priceLower < currentPrice && currentPrice < priceUpper) liquidity += uint128(_liquidity);
}
```

**Relevant locals/state, `burn()` (L231–242):**
- `(lower, upper, amount, recipient, unwrapBento)` (locals, L232–235) = `abi.decode(data, (int24, int24, uint128, address, bool))`.
- `priceLower` (local, L237) = `TickMath.getSqrtRatioAtTick(lower)` (returns `uint160` directly here, no explicit `uint256(...)` wrapper — a cosmetic difference from `mint`'s locals, not semantically relevant).
- `priceUpper` (local, L238) — same, for `upper`.
- `currentPrice` (local, L239) = `price` (state, read directly — no cast needed, since `price` is already `uint160`).
- `amount` (local, uint128, from the decode above) — the amount of liquidity being withdrawn from this position; **already the same type as `liquidity`**, no cast involved at L242 (unlike `mint`'s `uint128(_liquidity)`).

**The buggy statement (`burn`, L241–243, inside `unchecked`):**
```solidity
unchecked {
  if (priceLower < currentPrice && currentPrice < priceUpper) liquidity -= amount;
}
```

**Variable-value / statement-level intent (both statements).** The statement is trying to uphold: *"the pool-wide `liquidity` counter includes exactly the positions whose `[lower, upper]` range currently contains the pool's price."* A position's range is `[priceLower, priceUpper)` — **closed on the lower end, open on the upper end** — the standard half-open tick-range convention used by Uniswap-V3-style concentrated-liquidity AMMs (general domain convention, matching the report's own recommended fix; not independently verified here against the `Ticks` library's own `cross`/`nextTick` boundary handling, since `Ticks.sol` is not part of this case's `target_contracts_original` source scope — only `ConcentratedLiquidityPool.sol` is provided). The current code instead tests the *open* interval `(priceLower, priceUpper)` on both ends, via `priceLower < currentPrice` — silently excluding the case `priceLower == currentPrice`.

**Candidate in-file corroboration checked and not used (correction, Agent B review).** `_getAmountsForLiquidity` (L472–489), a separate helper used later in the *same* `mint()` call (L194), was considered as independent, in-file support for a closed-lower-bound convention, via its `else if (currentPrice <= priceLower)` branch:
```solidity
} else if (currentPrice <= priceLower) {
    /// @dev Only supply `token0` (`token0` is X).
    token0amount = uint128(DyDxMath.getDx(liquidityAmount, priceLower, priceUpper, true));
}
```
On inspection this does **not** actually corroborate the claim, for two independent reasons: (1) `DyDxMath.getDx`/`getDy` are continuous in `currentPrice`, so at exactly `currentPrice == priceLower` this "only token0" branch and the "both tokens" `else` branch compute the identical numeric result (`token1amount` degenerates to `0` in the "both tokens" branch too) — the `<=` placement here is an arbitrary tie-break for a continuous function, not a meaningful range-membership decision, and carries no information either way. (2) Even taken at face value, routing the tie into the *only-token0, priced-below-range* branch (rather than into the *both-tokens, in-range* `else` branch) groups `currentPrice == priceLower` with "out of range," the opposite grouping from what H-08's fix wants for the *active-liquidity* counter. This candidate corroboration is dropped rather than corrected into a positive argument, since it doesn't support either direction cleanly. R1-1's reading of intended behavior rests on the report's own text (quoted verbatim below) and the sponsor's confirmation, which are independently sufficient without this supplementary argument.

**Reported erroneous behavior** (H-08, verbatim): *"The `ConcentratedLiquidityPool.mint/burn` functions add/remove `liquidity` when `(priceLower < currentPrice && currentPrice < priceUpper)`. Shouldn't it also be changed if `priceLower == currentPrice`?"* Impact (verbatim): *"Pools that mint/burn liquidity at a time where the `currentPrice` is right at the lower price range do not work correctly and will lead to wrong swap amounts."* Sponsor initially disputed ("can you produce a POC?"), then confirmed after checking: *"I confused this with another similar issue... this a valid issue, we should probably even bump the severity."* Recommended Mitigation Steps (verbatim): *"Change the inequalities to `if (priceLower <= currentPrice && currentPrice < priceUpper)`."*

**Expected/intended behavior.** At `priceLower == currentPrice && currentPrice < priceUpper`: `mint()` must still fold the new position's `_liquidity` into the pool-wide `liquidity` counter; `burn()` must still subtract the closed position's `amount` from it. The current code leaves `liquidity` completely unchanged in this scenario in both functions.

**Patch intent.** The report supplies an exact one-operator fix (`<` → `<=` on the lower-bound comparison), applied identically to both `mint` and `burn`. Used here as R1-1 evidence only (§2) — R1-2/R1-3 below derive the target relation from the resulting *state-transition* consequence (does `liquidity` change by the right amount), not by asserting the boundary condition itself as part of the annotation (the grammar has no way to state a relational antecedent like `priceLower == currentPrice` inside an `@Post`/`@During` clause at all — see R1-3's Implication check).

**Concrete illustrative scenario (constructed — the report gives no numeric PoC, only the qualitative confirmation quoted above; independently constructed here, in the spirit of `web3bugs_59_H_04`'s and `70_H_04`'s constructed scenarios).** Real Q64.96 sqrt-price values from `TickMath.getSqrtRatioAtTick` are not computed here (the exact tick-math formula is not load-bearing to this case's target relation — see RQ2-A); the scenario instead uses representative round numbers that satisfy the reported boundary condition and typical position sizes:
- `priceLower = currentPrice = 79228162514264337593543950336` (an illustrative Q64.96 value — the reported boundary tie).
- `priceUpper = 87150978765690771352898345369` (illustrative, `> currentPrice`).
- Mint scenario: `liquidity(Entry) = 5,000,000`, `_liquidity = 1,000,000` (`≤ MAX_TICK_LIQUIDITY`, satisfying L157's require).
- Burn scenario (continuing the same pool state after the mint above, illustratively): `liquidity(Entry) = 6,000,000`, `amount = 1,000,000`.

**Bug-relevant intended numeric behavior:**
- (A) For `mint()`: whenever `priceLower == currentPrice && currentPrice < priceUpper`, `liquidity` at function exit must equal `liquidity` at function entry plus `_liquidity`. The current code leaves it unchanged instead.
- (B) For `burn()`: whenever `priceLower == currentPrice && currentPrice < priceUpper`, `liquidity` at function exit must equal `liquidity` at function entry minus `amount`. The current code leaves it unchanged instead.

These are two independently-reported consequences of the *same* finding (the report names both `mint` and `burn` together, one wrong-inequality pattern, one recommended fix applied identically to both) — treated as a two-member target annotation set below, per README §4's multi-annotation note (the same structure used for `web3bugs_70_H_04`'s persisted-total/returned-array pair).

---

## R1-2 — Intent Abstraction

Distinguishing property (patch's literal `<` → `<=` operator swap not transcribed into the annotation — the grammar cannot state a relational antecedent like `priceLower == currentPrice` at all, see R1-3): whether the pool-wide `liquidity` counter's *change* correctly reflects a position crossing into (mint) or out of (burn) the active range at the closed lower boundary.

**Intent-level orientation: Effect/state-transition-centered**, for both members. Neither relation is a bound on one isolated computed value (contrast `web3bugs_59_H_04`/`70_H_05`, value-centered) — the property is about what *effect* the statement must have on the persistent state variable `liquidity`, i.e., README R1-2's own example category (`weiRaised(Entry > Exit)`) applies directly here, not by analogy but because `liquidity`'s pre/post relationship is exactly what's disputed.

---

## R1-3 — Select the least implementation-specific sufficient relation

**Preliminary check — Implication form.** The grammar has a dedicated `Implication` production (`intentValue '=>' intentValue`, `Parser/Solidity.g4` L326), which looks like the natural fit for "if the boundary condition holds, then liquidity changes accordingly." **Checked and found not usable for this case's antecedent**: per `Analyzer/EnhancedSolidityVisitor.py` (L995–1002), both sides of `=>` are evaluated as a bare **nonzero** check on an `intentValue` (pure arithmetic, no `relOp` inside) — there is no way to express a *relational* antecedent like `priceLower == currentPrice` this way (an arithmetic expression being nonzero is not the same test as an equality holding). The relation is therefore constructed the way most During/Post relations in this benchmark already are (README §4/R1-7's general note): as a relation that holds **given a stated scenario precondition**, not as a literal in-grammar implication.

**Preliminary check — known-bound/call rescue (alpha-style).** Not applicable: the selected relations below reference only `liquidity`, `_liquidity`/`amount` — no function call is needed inside either relation (`TickMath.getSqrtRatioAtTick`/`DyDxMath.getLiquidityForAmounts` are consulted only to construct the illustrative scenario, never referenced live inside the annotation text itself — see RQ2-A for why neither is load-bearing).

**Preliminary check — snapshot-qualified `varRef(Entry/Exit/...)` extension.** **Needed, and used.** The target relation must compare `liquidity`'s *post*-call value against a formula combining its *pre*-call value with a third, independent quantity (`_liquidity`/`amount`) — exactly the "can't compare old value to a formula with a third term" situation README's R1-3 caution addresses. `liquidity(Entry)` (this session's extension) closes it directly; no fallback to a weaker directional relation is needed on this ground.

### Member (A) — `mint()`

1. **Directional/state-change relation**: `changed(liquidity, true)`, scenario-conditioned on the boundary. **Rejected.** It does discriminate on the constructed scenario (buggy: `liquidity` stays `5,000,000`, unchanged → `changed(liquidity, true)` false → Violated; intended: becomes `6,000,000` → true → Satisfied) — but it is **strictly weaker than needed**: an alternative implementation that changes `liquidity` by *any* nonzero amount on this boundary (e.g., off-by-a-constant, or even subtracting instead of adding) would also satisfy `changed(liquidity, true)` while retaining a real, differently-shaped value-level defect. Per README's explicit caution ("don't weaken past the point of losing discriminating power" when a stronger form is available at no extra implementation-specificity cost), this is rejected in favor of the exact form below.
2. **Inequality (non-decrease bound)**: `liquidity >= liquidity(Entry)`, scenario-conditioned. **Rejected**, same reasoning as `web3bugs_70_H_04`'s Alternative 1: the true intended behavior at this boundary is an *exact* increase by `_liquidity`, not merely "no decrease" — a `>=` bound would silently accept an implementation that adds the wrong amount (too much or too little, so long as it isn't negative), which is itself a different, unreported defect this weaker relation would fail to catch.
3. **Exact equality with Entry snapshot (SELECTED)**: `liquidity == liquidity(Entry) + _liquidity`. Ties the claim to the one already-meaningful, in-scope value the mint statement is actually supposed to fold in (`_liquidity`), via the snapshot-qualified reference extension, with no synthetic constant and no mapping/cast expression needed.

### Member (B) — `burn()`

1. **Directional**: `changed(liquidity, true)`. **Rejected**, same reasoning as (A)-1 — accepts a wrong-magnitude fix.
2. **Inequality (non-increase bound)**: `liquidity <= liquidity(Entry)`. **Rejected**, same reasoning as (A)-2 — the true intended behavior is an exact decrease by `amount`, not merely "no increase."
3. **Exact equality with Entry snapshot (SELECTED)**: `liquidity == liquidity(Entry) - amount`.

**Winner: Alternative 3 for each member — the target annotation is the set {(A), (B)}**, per README §4's multi-annotation note: both are independently derivable, independently `Expressible` (confirmed below), and both are named together by the same H-08 finding (not a separately-numbered finding) — exactly the structural situation the multi-annotation note is written for.

**Discrimination check (explicit arithmetic, per §9 checklist item 1), using R1-1's constructed scenario.**
- **(A), buggy**: condition `priceLower < currentPrice` → `79228162514264337593543950336 < 79228162514264337593543950336` → **false** (equal values, strict `<`) → the `&&` is false regardless of the (true) upper-bound check → `liquidity` untouched → `liquidity(Exit) = 5,000,000`. Check: `5,000,000 == liquidity(Entry) + _liquidity = 5,000,000 + 1,000,000 = 6,000,000` → **false → Violated.** Matches the reported defect.
- **(A), intended** (patched `<=`): condition now **true** (equal values, `<=`) and `currentPrice < priceUpper` true → `liquidity += uint128(_liquidity)` → `liquidity(Exit) = 5,000,000 + 1,000,000 = 6,000,000`. Check: `6,000,000 == 6,000,000` → **true → Satisfied.**
- **(B), buggy**: same condition, same falsity → `liquidity` untouched → `liquidity(Exit) = 6,000,000`. Check: `6,000,000 == liquidity(Entry) - amount = 6,000,000 - 1,000,000 = 5,000,000` → **false → Violated.**
- **(B), intended**: condition true → `liquidity -= amount` → `liquidity(Exit) = 6,000,000 - 1,000,000 = 5,000,000`. Check: `5,000,000 == 5,000,000` → **true → Satisfied.**

Both members discriminate correctly on the constructed scenario. (Degenerate-scenario note: at `_liquidity = 0` (A) or `amount = 0` (B), buggy and intended coincide trivially — same caveat as `web3bugs_3_H_04`'s `bond.amount == 0` note; the scenario above uses nonzero values, matching the report's own framing of a real position.)

**Required R1-3 negation check (§3/§4), run against the combined set, per README's mandatory instruction — mirrors `web3bugs_70_H_04`'s structure:**
- An implementation that fixes `mint`'s boundary (satisfying (A)) but leaves `burn`'s untouched: **caught** by (B), independently violated on the burn side. Neither member alone would catch this; the set does.
- Symmetric case (fixes `burn`, not `mint`): **caught** by (A).
- An implementation that "fixes" the boundary by *also* treating the **upper** boundary as closed (`priceLower <= currentPrice && currentPrice <= priceUpper`, an over-inclusive variant not what H-08 reports) is **not** distinguished from the correctly-scoped fix by either member, because the constructed scenario never has `currentPrice == priceUpper` — this is expected and not a coverage gap for *this* reported mechanism: H-08 is specifically and only about the lower boundary; the upper-boundary treatment is a separate, unreported question, out of scope for this finding (same discipline as `web3bugs_70_H_05`'s explicit separation from the co-located `70_H_03` finding).
- An implementation that changes `liquidity` by the wrong magnitude at the boundary (e.g., adds `_liquidity / 2`): **caught**, since both members are exact equalities.

**No defect-retaining alternative the report describes escapes the combined set.** `Intent coverage: Full` for the set (see §10 field below) — the "fixes one function, not the other" gap that a single-member selection would leave open is exactly what the second member closes, the same structural argument as `70_H_04`.

---

## R1-4 — During vs Post

**Both members — selected scope: Post.** `liquidity` is persistent state; the relation concerns its entry-vs-exit relationship across the *whole* call, not an intermediate statement-time value — README's own precedent for this exact shape (§4/R1-4: `SwordCrowdsale`'s `weiRaised -= amount` and `CDP.update`'s `totalCredit += delta`, both single-assignment-inside-conditional patches, both correctly Post with a directional Entry/Exit relation, not During-equality) applies here essentially verbatim — `liquidity += uint128(_liquidity)` (mint, L176) and `liquidity -= amount` (burn, L242) are the same "one conditional assignment statement" shape. Not chosen merely because the report describes a function-level consequence (R1-4's explicit caution): chosen because `liquidity`'s settled pre-call and post-call values are exactly what the reported "does the counter get updated" property needs, and nothing after L176/L242 in either function ever touches `liquidity` again (confirmed by reading the rest of both function bodies, L178–228 and L244–272 — only `reserve0`/`reserve1` are modified downstream, never `liquidity`).

**Required explicit delta-exception check (README §4/R1-7, per the task's mandatory instruction — performed on this case's own facts, not by analogy to any sibling case).** The confirmed exception: a `@During` whose *only viable attachment point* is inside a `for`/`while` loop body is never evaluated by this engine. **Neither `mint()` nor `burn()` contains any loop at all** — scanning both function bodies in full (L141–228, L231–272), there is no `for`/`while` construct anywhere in either function (the contract's only loop, the `while (cache.input != 0)` swap-stepping loop, lives in the unrelated `swap()` function, L321–414, never touched by this bug). The selected relations' attachment point (immediately after the disputed conditional, well before either function's exit) is not merely *outside* a loop — there is no loop present in the relevant scope to begin with. **Confirmed: delta does not apply to either member**, more unambiguously than in any of the loop-adjacent sibling cases (`59_H_04`, `70_H_05`, `3_H_04`), which at least had a loop somewhere in the same function or a same-call callee.

---

## R1-5 — Relation form

**Both members: exact equality, Entry-Exit family**, expressed as an ordinary `(C_cmp)` `RelationalCmp` comparison (`intentValue relOp intentValue`, `Parser/Solidity.g4` L325) with one operand snapshot-qualified via `(Entry)` (`varRef '(' ENTRY ')'`, L369, legal only under `@Post` per the grammar's semantic predicate `{not self.inDuring}?`). Per README §4's grammar note, the old dedicated `(entry relOp exit)` clause form no longer exists as a separate rule — this is "already an ordinary comparison," not a special form requiring justification beyond R1-3's discrimination argument. Not forced to equality by the assignment-shaped source statements (R1-5's explicit caution, and the same point R1-4 already made): equality was selected on independent discriminating-power grounds in R1-3 (a `>=`/`<=` bound would admit a wrong-magnitude fix).

---

## R1-6 — Construct the target annotation

**Target annotation is a set of two `@Post` clauses, attached in two different functions** (unlike `web3bugs_70_H_04`'s two members, which shared one function and one attachment point — here (A) and (B) are genuinely separate functions, so each gets its own attachment point within its own function body).

**Attachment point (A):** immediately after the `unchecked` block containing the disputed conditional (L175–177), inside `mint()`. `liquidity` (state) and `_liquidity` (named return, settled since L148–154 and never reassigned afterward) are both in scope.

**Attachment point (B):** immediately after the `unchecked` block containing the disputed conditional (L241–243), inside `burn()`. `liquidity` (state) and `amount` (local, settled since the L232–235 decode and never reassigned afterward) are both in scope.

**Cast-safety note for (A) (documented, not asserted from nowhere — README's constant-derivation discipline applied to a cast rather than a numeric literal).** The actual code writes `liquidity += uint128(_liquidity)`, but the grammar's `intentValue` has no cast syntax, so the annotation references the un-cast `_liquidity` directly. This is numerically sound — not merely convenient — because of L157's `require(_liquidity <= MAX_TICK_LIQUIDITY, "LIQUIDITY_OVERFLOW")`: `MAX_TICK_LIQUIDITY` is itself declared `uint128 internal immutable`, so `_liquidity <= MAX_TICK_LIQUIDITY` implies `_liquidity <= type(uint128).max` on every execution that reaches L176 (any execution that violates this has already reverted at L157). Per README's non-negativity/cast-scoping discipline (§4/R1-3): this equivalence (`uint128(_liquidity) == _liquidity` as numeric values) is guaranteed on any execution that completes without reverting past L157 — an unconditional fact for this function once that require is passed, not a scenario-specific assumption. (B)'s `amount` needs no such note: it is declared `uint128` at the `abi.decode` site and is never cast before use at L242.

**Target annotation:**
```solidity
// mint(), inside ConcentratedLiquidityPool
unchecked {
  if (priceLower < currentPrice && currentPrice < priceUpper) liquidity += uint128(_liquidity);
}
// @Post liquidity == liquidity(Entry) + _liquidity
```
```solidity
// burn(), inside ConcentratedLiquidityPool
unchecked {
  if (priceLower < currentPrice && currentPrice < priceUpper) liquidity -= amount;
}
// @Post liquidity == liquidity(Entry) - amount
```

**Scenario precondition, stated explicitly for both members (README §4/R1-7's general scenario-conditioning note — this is not a claim that either relation is a function-wide invariant over every reachable call).** Both relations hold specifically for a call in which `priceLower == currentPrice && currentPrice < priceUpper` — the reported boundary tie — and in which the position's own magnitude (`_liquidity` for (A), `amount` for (B)) is nonzero. For any other price relationship (`priceLower < currentPrice < priceUpper`, or `currentPrice` outside `[priceLower, priceUpper)` entirely), the *correctly patched* code's behavior differs (either the same equality still holds under the strict-`<` sub-case, or `liquidity` is correctly left unchanged when the range doesn't contain the price at all) — the annotation as written characterizes the specific boundary-tie instance the report identifies, consistent with how `web3bugs_3_H_04`/`70_H_05` scope their own Post relations to the reported branch/scenario rather than asserting unconditional generality.

---

## R1-7 — Expressibility decision

**Member (A) — `mint()`:**
- **Values referenceable at a legal program point**: Yes. `liquidity` (state) is referenceable both at its ambient (exit) value and, via `(Entry)`, at its pre-call snapshot; `_liquidity` is the function's own named return, settled and unmutated from L154 through function exit. No function call inside `intentValue`.
- **Arithmetic/logical relation representable**: Yes. `liquidity(Entry) + _liquidity` is ordinary `arithAdd`/`arithTerm` arithmetic; the whole clause is a first-class `(C_cmp)` `RelationalCmp`.
- **Observation point supported**: Yes — `@Post`, evaluated at `mint()`'s exit. Explicitly checked against the delta exception in R1-4: no loop exists anywhere in `mint()`'s body. Not applicable, unambiguously.

**Member (B) — `burn()`:** same three checks, same outcomes — `liquidity`/`liquidity(Entry)`/`amount` all in-scope, `liquidity(Entry) - amount` ordinary arithmetic, `@Post` at `burn()`'s exit with no loop anywhere in the function.

**Outcome: Expressible = YES, for both members of the set.**

**Old-label reclassification, checked directly against this case's own recorded old-pipeline reasoning (not assumed from the task brief's general warning alone).** `evaluation/RQ1/annotation_plans.md`'s entry for this case states the old blocker explicitly: *"Primary blocker: `abi.decode` → TOP (L3)... `priceLower = TickMath.getSqrtRatioAtTick(TOP)` → TOP... Condition `TOP < concrete` → both branches explored → boundary edge case indistinguishable... Even without `abi.decode`: setting the exact boundary value `priceLower == currentPrice` via debug annotation is required."* This is entirely an **engine abstract-interpretation / debug-scenario-construction concern** — `abi.decode`'s return being modeled as an unconstrained interval (⊤) under the old engine, and the practical difficulty of driving a debug/batch annotation to the exact boundary value — not a claim that the *relation itself* cannot be written in the grammar. Per README §4/R1-7's explicit instruction, "whether abstract interpretation would produce ⊤" and "whether the engine can validate it" are excluded from the Expressibility question by design; this old label is a textbook instance of the conflation the current methodology's restructuring (README §0) exists to undo, re-examined here on this case's own recorded reasoning rather than by generic analogy.

**A second, independent point (not the historically recorded reason for this case, but a genuine structural fact worth stating): even setting the `abi.decode`/⊤ engine question aside, the *exact-equality* form selected in R1-3 specifically needed this session's snapshot-qualified `varRef(Entry)` extension.** Before that extension, the grammar's only entry/exit construct was a dedicated, clause-level `(entry relOp exit)` form (README §4) that could express a bare `liquidity(Entry) < liquidity(Exit)` directional claim but **could not** mix an entry-snapshotted reference with a third, independent quantity (`_liquidity`/`amount`) inside one arithmetic comparison. R1-3's Alternative 1 (`changed(liquidity, true)`) and a bare directional `liquidity(Entry) < liquidity(Exit)` *would* have been constructible even under the pre-extension grammar — but both were rejected in R1-3 for being too weak to fully discriminate a wrong-magnitude fix. The relation this analysis actually needs (an *exact* pre/post difference pinned to a specific third-party value) is exactly the class of relation the extension was built for (README §4, citing `42_H_01`/`35_H_11`'s worked derivations as the precedent) — this case is a fresh, independent confirmation of that same gap-closing, on a case the extension's own documentation did not originally cite.

**Caution for the later, deferred RQ1-B track (not part of this Expressible verdict, recorded only as a forward-looking note, per the same discipline `3_H_04`/`59_H_04`/`70_H_05` used):** the old label's `abi.decode` → ⊤ concern may still be a real RQ1-B (Engine Validatability) risk — if the current engine's abstract interpretation still widens `abi.decode`-derived locals (`mintParams`, `lower`/`upper`/`amount`) to an unconstrained interval, a `Warning` rather than a clean `Violated` is plausible when this case is actually run, and driving the interpreter to the exact `priceLower == currentPrice` boundary will likely require a concrete debug/batch scenario (matching the old note's own "setting the exact boundary value... is required" observation) rather than relying on general-range settings. This is explicitly not evaluated here.

---

## §5 — Value/Algorithm and Usable/Unusable

- **Value-level**, both members. Per the paper's own definition (`main.tex` L239–240: Value-level = "a wrong operator, a swapped identifier, or truncation that produces a numerically incorrect result"; Algorithm-level = "operation ordering, an absent state update, or a missing procedure call"): the reported defect is, almost verbatim, the textbook Value-level example — a single wrong comparison operator (`<` where `<=` is intended) on one boundary of an otherwise-correct condition. Nothing about *which* statements execute in what order, and no procedure call or state update is missing outright — the same statement runs either way; only its *guard* is one comparison operator too strict. No revision needed here (unlike `59_H_04`/`70_H_05`, which required correcting an initial Algorithm-level call) — this case's defect maps directly onto the paper's own "wrong operator" phrase.
- **Usable**, both members. Every value either relation needs (`liquidity`, `liquidity(Entry)`, `_liquidity`, `amount`) is directly referenceable, in-scope, unmutated between the disputed statement and function exit. No representational gap of any kind.

---

## RQ2-A — Specification Requirements profile

Reported per member, since (A) and (B) are two separate functions with disjoint local scopes — unlike `web3bugs_70_H_04`'s two members (which shared one function and were merged into a single unioned profile), a union does not apply here.

### Member (A) — `mint()`

**Relevant statements:**
1. `MintParams memory mintParams = abi.decode(data, (MintParams));` (L142) — defines the struct whose `.lower`/`.upper` fields feed (2)/(3).
2. `uint256 priceLower = uint256(TickMath.getSqrtRatioAtTick(mintParams.lower));` (L144) — (b)-type: defines a term of the control condition gating whether the target statement's `liquidity`-incrementing branch executes at all.
3. `uint256 priceUpper = uint256(TickMath.getSqrtRatioAtTick(mintParams.upper));` (L145) — same reason.
4. `uint256 currentPrice = uint256(price);` (L146) — same reason; also the value whose equality to `priceLower` defines the reported boundary scenario.
5. `_liquidity = DyDxMath.getLiquidityForAmounts(priceLower, priceUpper, currentPrice, mintParams.amount1Desired, mintParams.amount0Desired);` (L148–154) — defines `_liquidity`, the target relation's addend operand. The callee is excluded from "Additional functions required" below (Step 1, not load-bearing); the statement itself is counted as the context that defines the value.
6. `require(_liquidity <= MAX_TICK_LIQUIDITY, "LIQUIDITY_OVERFLOW");` (L157) — (c)-type: establishes the non-truncation fact the annotation's un-cast `_liquidity` reference depends on (R1-6's cast-safety note).
7. `if (priceLower < currentPrice && currentPrice < priceUpper) liquidity += uint128(_liquidity);` (L176, inside `unchecked`) — the disputed/target statement itself, counted as context establishing the annotation's attachment point and subject (its own algebra is not used as self-justifying evidence, per README §6's self-substitution rule).

**Total: 7 relevant statements.**

**Unique relevant program values (8):** `mintParams` (struct local; its `.lower`/`.upper` fields are consumed directly inline at (2)/(3) with no separate extracted-value local, so — per README §6's container/extracted-value counting rule — only the struct itself is counted, not its fields separately), `priceLower`, `priceUpper`, `currentPrice`, `price` (state, read into `currentPrice`), `_liquidity` (named return), `MAX_TICK_LIQUIDITY` (immutable state), `liquidity` (state, the relation's target — both `(Entry)` and ambient/exit references count as the one value `liquidity`, per how other cases in this batch treat a single state variable read at two snapshots, e.g. `59_H_04`'s `count`).

**Additional functions required: 0.** Both `TickMath.getSqrtRatioAtTick` (L144/145) and `DyDxMath.getLiquidityForAmounts` (L148–154) fail README §6's Step 1 load-bearing test: would the selected relation's derivation or validity change if either callee's specific formula changed (while remaining internally consistent — e.g., a different but still well-defined tick-to-sqrt-price mapping, or a different but still well-defined liquidity-from-amounts formula)? **No.** The relation `liquidity == liquidity(Entry) + _liquidity` treats `priceLower`/`priceUpper`/`currentPrice` only as inputs to the *scenario's* boundary-tie precondition (established outside the annotation text, per R1-6), and treats `_liquidity` as an opaque, already-materialized operand — exactly the same exclusion pattern as `web3bugs_59_H_04`'s `_getIndexOfObservation` and `web3bugs_3_H_04`'s `calcCumulativeYieldFP`. Excluded entirely, not even as a case note.

**Additional protocol/application-specific contracts/libraries required: 0.** (Both `TickMath`/`DyDxMath` already excluded above.)

**Context breadth: 1** (same-function — every load-bearing value the relation needs is defined within `mint()` itself).

**External specification required: No** *(justification corrected on review — the original wording cited the `_getAmountsForLiquidity` in-file corroboration as supporting evidence, but R1-1 already retracted that corroboration as unsound; citing it here was a stale leftover, not a live justification)*. The relation is derivable from the source's own control/data flow (which statement gates `liquidity`'s update, and what the update statement's own operands are) plus the report's own explicit statement of intended behavior — sponsor-confirmed after initial dispute (R1-1) — that the lower boundary must be closed. Per README §6, the audit report itself never counts as an "external specification" for this field (R1-1 reads it for every case by design; the same convention already applied in `09_web3bugs_52_H_34`'s RQ2-A). No independent, protocol-level convention beyond what the report/sponsor already establish (e.g. cross-checking `Ticks.sol`'s own `cross`/`nextTick` boundary handling, out of this case's provided source scope per R1-1) is needed to justify the *selected relation's own validity* — only to further corroborate R1-1's reading, which the report/sponsor's own text already does independently.

### Member (B) — `burn()`

**Relevant statements:**
1. `(int24 lower, int24 upper, uint128 amount, address recipient, bool unwrapBento) = abi.decode(data, (int24, int24, uint128, address, bool));` (L232–235) — defines `lower`, `upper` (feeding (2)/(3)) and `amount`, the target relation's subtrahend operand.
2. `uint160 priceLower = TickMath.getSqrtRatioAtTick(lower);` (L237) — (b)-type control-condition term, same role as (A)'s statement 2.
3. `uint160 priceUpper = TickMath.getSqrtRatioAtTick(upper);` (L238) — same reason.
4. `uint160 currentPrice = price;` (L239) — same reason.
5. `if (priceLower < currentPrice && currentPrice < priceUpper) liquidity -= amount;` (L242, inside `unchecked`) — the disputed/target statement itself.

**Total: 5 relevant statements** (2 fewer than (A) — `burn()` needs no analogue of (A)'s statements 5/6, since `amount` arrives pre-typed as `uint128` directly from the decode, with no intervening formula-derived value and no cast-safety `require` to rely on; a genuine structural asymmetry between the two members, not an oversight — see R1-6's cast-safety note).

**Unique relevant program values (8):** `lower`, `upper` (locals, each with their own declaration site via the tuple-destructuring decode — unlike (A)'s `mintParams.lower`/`.upper`, these get their own local identifiers and are counted separately, per the same container/extracted-value rule applied the other way: an access assigned to its own local *is* counted), `amount` (the relation's target operand), `priceLower`, `priceUpper`, `currentPrice`, `price` (state), `liquidity` (state, the relation's target, both snapshots).

**Additional functions required: 0.** `TickMath.getSqrtRatioAtTick` fails Step 1 for the same reason as in (A) — excluded entirely.

**Additional protocol/application-specific contracts/libraries required: 0.**

**Context breadth: 1** (same-function).

**External specification required: No.**

---

## §7 — Alternatives-considered summary

| # | Relation | Tier | Target mechanism | Expressible? | Discriminates (constructed scenario)? | Verdict |
|---|----------|------|-------------------|---------------|-----------------|---------|
| 1 | `changed(liquidity, true)` | Directional/state-change | (A) and (B), separately | Yes | Yes | Rejected — admits a wrong-magnitude fix as passing |
| 2 | `liquidity >= liquidity(Entry)` (A) / `liquidity <= liquidity(Entry)` (B) | Inequality (non-decrease / non-increase bound) | (A) / (B) | Yes | Yes | Rejected — true intended behavior is an exact, known-magnitude change, not merely a directional bound |
| 3 | `liquidity == liquidity(Entry) + _liquidity` (A) / `liquidity == liquidity(Entry) - amount` (B) | Exact equality, Entry-Exit family | (A) / (B) | Yes | Yes | **Selected — both, as a target annotation set** |
| — | Implication (`priceLower == currentPrice => ...`) | — | — | No | — | Not usable — grammar's `Implication` antecedent is a bare nonzero-check on arithmetic, not a relational (`==`) test; handled instead via explicit scenario-conditioning (R1-3/R1-6) |
| — | Known-bound/call rescue (alpha-style) | — | — | N/A | — | Not applicable — no function call in either selected relation |

---

## RQ1-B / RQ2-B

Deferred per README §8. Not run, not predicted. One caution carried forward from R1-7: the old pipeline's own recorded concern (`abi.decode`-derived locals modeled as ⊤, and the practical need for an exact-boundary debug/batch scenario) is a plausible source of `Warning` rather than clean `Violated` at RQ1-B time, and should be checked empirically rather than assumed either way when that track runs for this case.

---

## Summary

- **Expressible: Yes, for both members of the target set.** No blocking grammar/scope gap in either — all referenced values (`liquidity`, `liquidity(Entry)`, `_liquidity`, `amount`) are ordinary, in-scope, unmutated references at each function's exit; both attach as `@Post` immediately after their respective disputed conditional, with **no loop present anywhere in either function** (the most unambiguous delta-exception check performed in this batch, per R1-4/R1-7 above).
- **Target annotation (a set of two `@Post` clauses, one per function)**:
  - (A) `mint()`: `@Post liquidity == liquidity(Entry) + _liquidity`
  - (B) `burn()`: `@Post liquidity == liquidity(Entry) - amount`
  Both scenario-conditioned on the reported boundary tie, `priceLower == currentPrice && currentPrice < priceUpper`, with the position's own magnitude (`_liquidity`/`amount`) nonzero.
- **Quantified property instantiated: No, for both members.** `liquidity` is a single pool-wide scalar, not an element drawn from a collection of co-existing positions/pools — the boundary-price condition is ordinary scenario-conditioning (which call inputs make the relation checkable), not a collection-element instantiation (contrast `web3bugs_83_H_01`'s representative-pool pattern).
- **Value-level** (both members) — a single wrong comparison operator, the paper's own textbook Value-level example; **Usable** (both members).
- **Old-label reclassification, checked against this case's own recorded reasoning (not a generic analogy).** The old `L3: unsupported-construct-top` label's actual stated blocker (`evaluation/RQ1/annotation_plans.md`) is `abi.decode`-derived locals being modeled as ⊤ under the old engine's abstract interpretation, plus the practical difficulty of debug-scenario construction at the exact boundary — both are engine-precision/RQ1-B-shaped concerns, explicitly out of scope for R1-7 (README §4). Independently, the *exact* relation this analysis selects (rather than a weaker directional alternative) does genuinely rely on this session's snapshot-qualified `varRef(Entry)` extension, since the pre-extension grammar's entry/exit support was a bare, third-term-free dedicated clause — a second, independent reason the old label no longer predicts this case's outcome.
- RQ2-A specification profile: (A) `mint()` — 7 relevant statements, 8 unique relevant program values, 0 additional functions required (`TickMath.getSqrtRatioAtTick`/`DyDxMath.getLiquidityForAmounts` both excluded, Step 1), Context breadth 1, External specification required: No. (B) `burn()` — 5 relevant statements, 8 unique relevant program values, 0 additional functions required, Context breadth 1, External specification required: No.
- RQ1-B/RQ2-B: deferred, not run in this pass. One forward-looking caution recorded (§ RQ1-B/RQ2-B above): the old label's `abi.decode`-as-⊤ concern may still translate into an RQ1-B `Warning` risk, untested here.
