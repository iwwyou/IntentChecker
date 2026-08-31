# web3bugs_42_H_01 — Agent A (Analyst) Case Analysis

Case ID: `web3bugs_42_H_01` | Contract: `MochiVault` | Function: `borrow(uint256 _id, uint256 _amount, bytes memory _data) public override updateDebt(_id)`
Existing label: H-01, "Vault fails to track debt correctly that leads to bad debt" (Code4rena contest 42; submitted by jonah1005, also found by WatchPug — no explicit sponsor-confirmation line present in the report text for this finding)
Source: `evaluation/RQ1/target_contracts_original/web3bugs_42_H_01.sol`; Report: `C:\Users\isjeon\Web3Bugs\reports\42.md`, finding `[H-01]`
Struct reference: `Detail{status, collateral, debt, debtIndex, referrer}`, `Dependencies/interfaces/IMochiVault.sol`

## R1-1 — Reported Behavior Reconstruction

**Contract/function role**: `MochiVault` is a CDP-style lending vault — users deposit collateral and borrow the protocol stablecoin (USDM) against it. It tracks debt at two levels: `details[_id].debt` (per-position debt, in the `Detail` struct keyed by NFT id) and `debts` (a single contract-level state variable meant to be the protocol-wide aggregate across all positions). `borrow` increases a position's debt: it computes the new debt including a 0.5% origination premium, enforces collateralization/credit-cap/minimum-debt checks, mints the premium as protocol fee, updates the position's own bookkeeping, and mints USDM to the caller.

**Relevant locals/state**:
- `_amount` (parameter, possibly reduced by the collateral-factor cap at lines 228–230 and the credit-cap at lines 231–233) — the raw borrow request size.
- `increasingDebt` (line 234, `(_amount * 1005) / 1000`) — the amount by which *this position's own debt* increases; includes the 0.5% premium. This is the individual-debt increment.
- `totalDebt` (line 235, `details[_id].debt + increasingDebt`) — the position's new debt.
- `details[_id].debt` (state, `Detail.debt` field) — set to `totalDebt` at line 246. Its increment across this call is exactly `increasingDebt`.
- `debts` (state) — the protocol-wide aggregate. Line 248 (the reported bug line) increments it by `_amount`, not `increasingDebt`.

**The disputed statement**:
```solidity
details[_id].debt = totalDebt;                       // line 246 — position debt increases by increasingDebt
details[_id].status = Status.Active;
debts += _amount;                                      // line 248 — BUGGY: aggregate increases by _amount only
```
- **Variable-value intent (line 248)**: the increment applied to the protocol-wide `debts` aggregate should equal the increment just applied to this position's own debt (`increasingDebt`), not the smaller, premium-free `_amount`.
- **Statement-level invariant**: `debts` must remain consistent with (at least as large as) the sum of every position's individual debt — it exists specifically to track that sum.

**Reported erroneous behavior** (report, verbatim): "when the contract records the total debt it uses `_amount` instead of `increasingDebt`... The contract's debt is inconsistent with the total sum of all users' debt. The bias increases overtime and would break the vault at the end." The report's own worked example (single user, deposits 1.2M collateral, borrows 1M USDM): "The user's debt (`details[_id].debt`) would be 1.005M as there's a .5 percent fee. The contract's debt is 1M" — and later, a liquidation attempting to subtract 1.005M from a `debts`/`details[_id].debt` pair that never matched reverts on underflow.

**Expected/intended behavior**: `debts` should increase by `increasingDebt` (the same quantity added to `details[_id].debt`), not by `_amount`.

**Patch intent** (evidence only, not transcribed): "Recommend to check the contract to make sure `increasingDebt` is used consistently" — i.e., change `debts += _amount;` to `debts += increasingDebt;`. Used only to confirm which quantity is intended, not as annotation source text — R1-3 below shows the direct "delta equals `increasingDebt`" formulation this patch suggests is not actually expressible in the current grammar, and a different (still discriminating) relation is selected instead.

**Bug-relevant intended numeric behavior**: the protocol-wide debt aggregator (`debts`) must stay consistent with the sum of individual position debts; in particular, after any `borrow` call it must be at least as large as the specific position's own debt.

## R1-2 — Intent Abstraction

Distinguishing property (patch syntax dropped): the *increment* applied to `debts` at line 248 must equal the increment separately applied to `details[_id].debt`, not a lesser value. **Intent-level orientation: Effect/state-transition-centered** — a claim about how two related pieces of persistent state must move together as a result of the call, not a bound on one isolated value.

## R1-3 — Select the least implementation-specific sufficient relation (alternatives recorded, §7)

1. **Directional/state-change**: `debts` increases (`entry < exit`, or `before < after` around line 248). **Rejected — not discriminating.** Both the buggy code (`+= _amount`) and the intended code (`+= increasingDebt`) add a strictly positive quantity, so `debts` increases either way; a bare directional check can't see which quantity was added.

2. **Tight delta bound, mirroring the patch, exactly `debts`'s increment `== increasingDebt`** (selected — see correction below): `debts == debts(Entry) + increasingDebt` at `@Post`.
   **Correction (later pass, after the grammar was extended)**: this alternative was originally recorded as *inexpressible*, on the grounds that the grammar's only two cross-state constructs — `(before relOp after)` ($D_{\text{ba}}$) and `(assign relOp current)` ($D_{\text{ac}}$) — compare the *same* expression $e$ at two timepoints, with no way to mix in an independently-scoped third quantity (`increasingDebt`). That blocker is now resolved: the grammar's snapshot-qualified references (`README`/`main.tex`'s $\mathit{varRef}(\mathit{snap})$ extension) let any reference inside an arithmetic expression be pinned to `Entry`/`Exit`/`Before`/`After`/`Assign` independently of the rest of the expression, so `debts(Entry)` and the ordinary (exit-time) `debts`, `increasingDebt` can all appear in one ordinary $C_{\text{cmp}}$ comparison — `debts == debts(Entry) + increasingDebt` — without needing a separate clause-level rule. This is now the *exact*, general form of the reported intent (R1-1/R1-2), not an approximation of it.
   **Discrimination check (same scenario as below, reusing the report's own numbers)**: fresh position `_id`, `debts(Entry) = 0`, `details[_id].debt = 0` at entry (`updateDebt(_id)`'s `accrueDebt` call is a no-op under this zero baseline, as before). `_amount = 1{,}000{,}000`, caps non-binding, `increasingDebt = 1{,}005{,}000` (exact, as computed below).
   - **Buggy** (`debts += _amount`): `debts(Exit) = 0 + 1{,}000{,}000 = 1{,}000{,}000`. Check: `1{,}000{,}000 == 0 + 1{,}005{,}000` → **false ⟹ Violated.**
   - **Intended** (`debts += increasingDebt`): `debts(Exit) = 0 + 1{,}005{,}000 = 1{,}005{,}000`. Check: `1{,}005{,}000 == 0 + 1{,}005{,}000` → **true ⟹ Satisfied.**
   **Correction to an earlier draft of this note**: this relation is *not* unconditionally general — it is still scenario-conditioned the same way alternative 3 was, on `accrueDebt`'s own contribution to `debts` being zero. The fully general fact about the *intended* implementation is `debts(Exit) == debts(Entry) + increased + increasingDebt`, where `increased` is `accrueDebt`'s own accrual term (line 89 of `MochiVault.sol`); under the zero-baseline scenario (`debts(Entry) == 0`) `increased` is provably `0` regardless of `currentIndex`/`debtIndex`, so it drops out and `debts == debts(Entry) + increasingDebt` holds exactly — but this is the *same* precondition-dependence R1-6 already documents, not a new, weaker one. What *does* improve over alternative 3 is depth, not generality: within the same scenario, this relation captures the *exact* increment (matches R1-1/R1-2's reported intent precisely), where alternative 3 only captured a *necessary consequence* of it (see R1-7).
3. **Relational invariant** (considered, not selected — see below): `debts >= details[_id].debt`, evaluated at function exit (`@Post`). This was the relation originally selected, back when alternative 2 was believed inexpressible; it is still valid (compares two *different* state variables at the *same* timepoint, exactly what $C_{\text{cmp}}$ supports) and still discriminates on the same scenario (`1{,}000{,}000 >= 1{,}005{,}000` false vs. `1{,}005{,}000 >= 1{,}005{,}000` true) — but it is **no longer selected**, now that alternative 2 is expressible and is a strictly more direct, exact statement of the reported intent (see R1-7's revised Intent coverage note: alternative 3 only verifies a necessary consequence — that *some* accrual happened — not that the *correct* increment was applied, exactly the gap alternative 2 closes). Kept here, not deleted, as the record of what the case's Expressible verdict rested on before the grammar was extended.
4. **Exact equality on the same-state form**: `debts == details[_id].debt`. Still rejected for the same reason as before: the moment a second position with nonzero debt exists in the vault, `debts` (the sum over all positions) legitimately exceeds any single `details[_id].debt`, so this form is unsound beyond the single-position instantiation — unlike alternative 2, which stays sound in general because it's stated as an increment, not an absolute-value comparison.

**Selected**: `debts == debts(Entry) + increasingDebt` at `@Post` (alternative 2). It is the direct, exact statement of R1-1/R1-2's reported intent, now expressible without any grammar gap, discriminates correctly, and is sound unconditionally (not merely on the constructed scenario) — strictly stronger than alternative 3's aggregate inequality on every count that matters here.

## R1-4 — During vs Post

**Chosen: Post.** The relation is about final, persistent state — `debts` and `details[_id].debt` both being state variables whose *last-written* values (already stable by the time `borrow` returns; nothing after line 248 touches either) must satisfy an accounting relationship. This is exactly the "final state, a persistent state transition, a function-level invariant" category from the README, not a statement-time intermediate value. Per the README's explicit caution, the choice is not driven by the fact that the patch is a single `+=` statement (it is, same shape as `SwordCrowdsale`/`CDP.update`, both of which are also `@Post` in this project's existing set) — it's driven by the relation's own nature: a same-timepoint comparison between two different pieces of persistent state, not something tied to one program point mid-statement. Numerically, attaching this at `@During` immediately after line 248 vs. `@Post` at function exit would evaluate identically here (nothing after line 248 modifies `debts` or `details[_id].debt`), but `@Post` is the semantically appropriate scope for a persistent-state accounting invariant.

## R1-5 — Relation form

Exact equality via the common-form rule `intentValue relOp intentValue` ($C_{\text{cmp}}$), evaluated at `ref(Γ) = σ_{\text{exit}}$` under `@Post`, where the left-hand `intentValue` is the ordinary (exit-time) `debts` and the right-hand `intentValue` is `debts(Entry) + increasingDebt` — an arithmetic expression mixing a snapshot-qualified reference (`debts(Entry)`, reading $\sigma_{\text{entry}}$) with an ordinary exit-time reference (`increasingDebt`), per the grammar's snapshot-qualified-reference extension. This is *not* $(P_{\text{ee}})$/entry-exit in the old, retired sense (that rule compared the *same* expression at both timepoints); here `debts(Entry)` is one *term* inside a larger expression compared against a *different* expression (`debts` at exit), which is exactly what the extension exists to allow. The equality is not a mechanical copy of the patch's `+=` syntax — it states the increment relationship directly, matching R1-2's reported intent, not the assignment operator.

## R1-6 — Target annotation

Attachment point: immediately after `debts += _amount;` (line 248), inside `borrow`. (Per `@Post`'s semantics the relation is actually evaluated at $\sigma_{\text{exit}}$, i.e. the join over the function's return paths — the comment is placed at the disputed statement by the same textual convention used elsewhere in this project's `@Post` examples, e.g. the paper's own `Pools.mint` illustration.)

```solidity
details[_id].debt = totalDebt;
details[_id].status = Status.Active;
debts += _amount;
// @Post debts == debts(Entry) + increasingDebt
engine.minter().mint(msg.sender, _amount);
```

**Scenario preconditions this instantiation relies on** (documented per R1-3/R1-6, not part of the annotation text itself): `_id` is a freshly minted, previously-untouched position (`details[_id].debt == 0` at entry) in a vault where `debts == 0` at entry, so that the `updateDebt(_id)` modifier's `accrueDebt(_id)` call contributes exactly `0` to `debts` regardless of `currentIndex`/`debtIndex` (see R1-3's correction) and doesn't disturb the zero baseline; and `_amount` is large enough, and collateral/credit-cap headroom generous enough, that none of the caps at lines 228–233 or the `minimumDebt`/`!_liquidatable` checks at lines 236–240 bind (so execution reaches line 246/248 unmodified). Unlike the earlier `debts >= details[_id].debt` relation, this scenario isn't only a convenience for clean discrimination numbers — the relation's own *soundness* now genuinely depends on the zero-baseline precondition (see R1-3's correction), so it must be stated as a scenario-conditioned fact, not an unconditional invariant.

**Quantification note**: the fully general reported property — "the vault's aggregate debt must equal the sum of every position's debt" — is quantified over the entire `details` mapping (every existing NFT id), and the grammar has no construct to range an annotation over a mapping/collection. This annotation instantiates that property on **one concrete representative element**: the specific `_id` passed to `borrow`. This narrowing is unchanged from the earlier relation and is orthogonal to the R1-3 upgrade below — the new relation is exact *for this one `_id`*, not a step toward the fully general multi-`_id` claim.

All identifiers are pre-existing, semantically meaningful in-scope values (two state variables plus the already-defined `increasingDebt` local, and one snapshot-qualified reference); no synthetic value, no concrete constant needing derivation, no mechanical transcription of the patch's assignment operator (the relation states an equality because that's what the reported intent actually is, not because the patch uses `+=`).

## R1-7 — Expressibility decision

- Values referenceable at the point: yes — `debts`, `debts(Entry)`, `increasingDebt` are all legal `varRef`/snapshot-qualified-`varRef` references, `debts(Entry)` per the grammar's new snapshot extension (well-formed under `@Post`'s $\Gamma$, which supplies $\sigma_{\text{entry}}$).
- Arithmetic/relation representable: yes — a single `==` comparison via $(C_{\text{cmp}})$ whose right-hand side is an ordinary `arithAdd` of a snapshot-qualified term and an exit-time term.
- Observation point supported: yes — `@Post`'s $\Gamma$ supplies both $\sigma_{\text{entry}}$ (for `debts(Entry)`) and $\sigma_{\text{exit}}$ (for the ambient/left-hand `debts` and `increasingDebt`); nothing after line 248 further mutates either quantity.
- No function call inside `intentValue`: confirmed — same as before, none of `borrow`'s several external interface calls are needed by the selected relation.

**Intent coverage: Full** (revised — see analysis history below). Earlier passes of this case selected `debts >= details[_id].debt`, which only verified a *necessary consequence* of the reported intent (that `debts` increased at all, not that it increased by the *correct* amount) — recorded at the time as `Intent coverage: Partial`, per README §3/§4/§10. That gap is now closed: the grammar's snapshot-qualified-reference extension makes the *exact* reported relation (`debts == debts(Entry) + increasingDebt`) directly expressible, so this case no longer needs the necessary-condition fallback. This is one of the two cases (with `web3bugs_35_H_11`) that motivated adding the extension in the first place.

**Quantified property instantiated: this Expressible verdict is under the R1-6 single-`_id` instantiation** — the fully general, mapping-wide "aggregate equals the sum of all positions" claim is not itself expressible (no quantifier in the grammar), only this one-representative-element narrowing of it is. Unaffected by the R1-3 upgrade (see R1-6's quantification note).

**This relation is scenario-conditioned**, per the README's explicit allowance: it holds given the R1-6 preconditions (fresh position, zero vault-wide baseline, caps non-binding) — and, unlike the earlier relation, the scenario is now load-bearing to the relation's *soundness*, not only to the cleanliness of the discrimination numbers (see R1-3's correction and R1-6).

**Outcome: Expressible — Yes.**

## Usable/Unusable (§5)

**Usable** — both needed values (`debts`, `details[_id].debt`) are directly referenceable, in-grammar, at the annotated point's exit-state; purely a representational-resources fact, no call, no missing in-scope proxy. **Effect/state-transition-level** in R1-2's orientation sense; in the paper's existing Value-level/Algorithm-level axis this is **Value-level** (a direct relational bound between two specific values, not an ordering/algorithm-wide property).

## RQ2-A — Specification profile

*(Recomputed in a later pass — the original count below missed that `_amount`'s value, which `increasingDebt` is built from, is itself conditionally redefined by two statements upstream of line 234. See README §6's new caution bullet, added from this exact correction.)*

- **Relevant statements (9, all in `borrow`)**:
  1. `price = engine.cssr().update(address(asset), _data);` — defines `price`, an input to `maxMinted`'s computation (statement 3).
  2. `cf = engine.mochiProfile().maxCollateralFactor(address(asset));` — defines `cf`, the other input to `maxMinted`.
  3. `maxMinted = details[_id].collateral.multiply(cf).multiply(price);` — defines the cap threshold used by statement 4's condition.
  4. `if (details[_id].debt + _amount > maxMinted) { _amount = maxMinted - details[_id].debt; }` — **first conditional redefinition of `_amount`.** This is the statement the original pass missed: it was inspected during R1-1/R1-3 "to confirm the scenario is reachable," but it also redefines `_amount`, which statement 6 (`increasingDebt`) is built from — squarely (a)-type per README §6, not a reachability-only gate.
  5. `if (engine.mochiProfile().creditCap(address(asset)) < debts + _amount) { _amount = engine.mochiProfile().creditCap(address(asset)) - debts; }` — **second conditional redefinition of `_amount`**, same correction as statement 4.
  6. `increasingDebt = (_amount * 1005) / 1000;` — defines the individual-debt increment, now correctly traced to the `_amount` value *after* statements 4–5's capping, not the raw parameter.
  7. `totalDebt = details[_id].debt + increasingDebt;` — combines the position's prior debt with the increment.
  8. `details[_id].debt = totalDebt;` — directly defines the relation's right-hand value.
  9. `debts += _amount;` — target/disputed statement, defines the relation's left-hand value; counted as context per the self-substitution rule (§6), not as self-justifying evidence.
  - **Still excluded, and correctly so** (genuine reachability-only gates, redefine nothing the relation depends on): `require(engine.nft().ownerOf(_id) == msg.sender, "!approved");`, `require(engine.nft().asset(_id) == address(asset), "!asset");`, `require(details[_id].debt + _amount >= engine.mochiProfile().minimumDebt(), "<minimum");`, `require(!_liquidatable(details[_id].collateral, price, totalDebt), "!healthy");` — all pure boolean gates, no assignment. `mintFeeToPool(increasingDebt - _amount, details[_id].referrer);` — checked directly against its own definition (`mintFeeToPool` decrements `claimable` and calls `engine.minter().mint`/`engine.referralFeePool().addReward`, an unrelated protocol-fee side channel); it does not write `debts` or `details[_id].debt`, so it doesn't feed the relation's operand chain — excluded, not merely unexamined.
  - The `updateDebt(_id)` modifier's `accrueDebt(_id)` call remains excluded as before: under the R1-6 zero-baseline scenario it is a genuine no-op (§6 Step 1: changing its behavior, while keeping it consistent with "no-op when both quantities are already zero," wouldn't move the argument).
- **Unique relevant values (9)**: state variables — `debts`, `details[_id].debt`, `details[_id].collateral` (3); locals — `price`, `cf`, `maxMinted`, `increasingDebt`, `totalDebt` (5); parameters — `_amount` (1). (`_id`/`_data`/`asset` are used only as mapping-index/call-argument roles, not as arithmetic operands the relation's derivation combines — same convention already used for `_id` in the original count, extended consistently to the newly-added statements' arguments.)
- **Additional functions required (3)**: all three are external interface calls whose *specific return values* feed statements 1–5 above, hence the `_amount` the relation's `increasingDebt`/`totalDebt` chain is built from — this is a direct correction of the original "None," which only checked whether the *selected relation's text* named a call (it doesn't), not whether a call fed a value the relation's derivation depends on.
  - `engine.cssr().update(address(asset), _data)` — defines `price`; semantic guarantee needed: returns *some* current-price value for `asset` (the relation's own soundness doesn't depend on which specific price, only that `maxMinted` ends up some finite bound — see below). **Flagged separately for RQ1-B**: this call's interface declares no `view`/`pure` modifier (`evaluation/RQ1/target_contracts_original/dependencies/42_ICSSRRouter.sol:8-10`), so under this project's `@IReturn` restriction (view/pure interface calls only — `paper/first_revision/main.tex:399`) its return value cannot be pinned by a debug annotation at all; the engine must treat it as ⊤. This doesn't affect the R1-7 Expressible verdict (precision/⊤ questions are explicitly out of scope there), but it is now RQ2-A-load-bearing context worth carrying forward into the RQ1-B discussion.
  - `engine.mochiProfile().maxCollateralFactor(address(asset))` — defines `cf`; guarantee needed: returns *some* finite collateral-factor value for `asset`.
  - `engine.mochiProfile().creditCap(address(asset))` (called twice, same value both times) — guarantee needed: returns *some* finite credit-ceiling value for `asset`.
  - **Note on what's *not* load-bearing here**: the relation `debts >= details[_id].debt` doesn't need to know what these three calls specifically compute — only that `_amount`, whatever it settles to after any capping, is what both `increasingDebt` (statement 6) and `debts += _amount` (statement 9, the disputed line) consistently use. This is why "External specification required" (below) stays No even though three external calls are now counted here — being load-bearing to the derivation and requiring protocol-specific domain knowledge to justify are different questions (§6 Step 2).
- **Additional protocol/application-specific contracts/libraries required**: None counted. `Float`/`FloatStruct.multiply()` (used in statement 3, `maxMinted`'s computation) is a generic fixed-point multiplication primitive — passed Step 1 (load-bearing: `maxMinted`'s value depends on it) but sorted into the Step 2 generic bucket, same treatment as SafeMath/PRBMath elsewhere in this project; not separately counted, noted here as a case note.
- **Context breadth (3)** — corrected from 1. Three external interface calls (`engine.cssr()`, `engine.mochiProfile()` ×2) are now load-bearing to the relation's derivation chain, which is exactly README §6's ordinal-3 definition ("cross-contract/library"), not ordinal-2 ("other function(s) in same contract") — these are genuinely external interfaces, not same-contract sibling functions.
- **External specification required**: No — unchanged from the original pass, for the reason stated in the "Additional functions required" note above: the relation's own soundness only needs *some* value out of each external call, not a specific protocol-defined number or convention.

## RQ1-B / RQ2-B

Deferred. Per README §8, engine validatability (RQ1-B) and analysis cost (RQ2-B) are not part of this pass — not attempted, no predicted outcome recorded here.

## Summary

- **Expressible: Yes** (under the R1-6 single-`_id` instantiation of the collection-quantified reported property).
- **Target annotation** *(revised — grammar extended with snapshot-qualified references, see README §3/§4)*: `// @Post debts == debts(Entry) + increasingDebt`, attached immediately after line 248 (`debts += _amount;`) inside `borrow`; the left-hand `debts` and `increasingDebt` evaluate at $\sigma_{\text{exit}}$, `debts(Entry)` at $\sigma_{\text{entry}}$, within one ordinary $(C_{\text{cmp}})$ comparison.
- **Value-level, Usable, Post, exact-equality form** (revised from the earlier relational-invariant/inequality form — see R1-3/R1-5).
- **Quantified property instantiated: Yes** — the fully general "vault-wide aggregate equals the sum of every position's debt" claim is quantified over the `details` mapping; the annotation instantiates it on the one `_id` being borrowed against in this call (the position whose debt increment the bug fails to mirror into `debts`). Unaffected by the Intent-coverage upgrade — a separate (breadth vs. depth) axis.
- Alternatives considered at R1-3: directional (rejected, non-discriminating), **tight delta bound mirroring the patch, `debts == debts(Entry) + increasingDebt` (selected — originally recorded as a grammar-inexpressible cross-state-arithmetic gap; now expressible via the snapshot-qualified-reference extension and re-selected as the exact, direct statement of the reported intent)**, relational invariant `debts >= details[_id].debt` (the case's original selection before the grammar was extended — still valid and still recorded, but superseded, since it only captures a necessary consequence of the intent rather than the intent itself), exact equality on the same-state form `debts == details[_id].debt` (rejected — unsound beyond the single-position instantiation).
- RQ1-B/RQ2-B: deferred, not run in this pass.
