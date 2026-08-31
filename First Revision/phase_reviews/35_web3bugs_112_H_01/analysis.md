# web3bugs_112_H_01 — Agent A (Analyst) Case Analysis

Case ID: `web3bugs_112_H_01` | Contract: `StakerVault` (contest 112, Backd Protocol) | Function: `transfer(address account, uint256 amount) external`
Existing label: H-01, "User can steal all rewards due to checkpoint after transfer" (submitted by `0xDjango`, also found by `unforgiven`; sponsor `chase-manning` (Backd) confirmed and resolved).
Source: `evaluation/RQ1/target_contracts_original/web3bugs_112_H_01.sol`; Report: `C:\Users\isjeon\Web3Bugs\reports\112.md`, finding `[H-01]` (§0.5 primary/authoritative source, lines 118–166).
**Cross-checked against the scattered `Dataset/Web3Bugs/S6_1/contest_112_H_01/README.md` per §0.5's mandatory caution: confirmed truncated.** The scattered file reproduces only the finding's title, byline, source-line link, and the two opening paragraphs (its own lines 1–17) — it is missing the entire `### Proof of Concept` section (the concrete A→B→C exploit walkthrough with the `perUserShare` snippet), the `### Recommended Mitigation Steps` section, and the sponsor-confirmation line, all present in the primary source (`Web3Bugs/reports/112.md` lines 129–162). This matches the exact truncation pattern §0.5 warns about (`71_H_11`/`83_H_01`/`65_H_01`); the primary source is used throughout below.
Reported bug lines (local numbering in `target_contracts_original/web3bugs_112_H_01.sol`): 112–113 (the `balances` mutations) and 117–118 (the `userCheckpoint` calls, which occur *after* the mutations instead of before).

**Note on the retired old-methodology background supplied in the task**: a previously-drafted (never finalized) sketch exists at `evaluation/RQ1/annotation_plans.md` (`## web3bugs_112_H_01`, line 1164), labeled `not_detectable (L5b: wrong-code — operation ordering)` and rejecting `@During Unchanged(balances[msg.sender])` on the grounds that "writing 'must be unchanged' on a variable already visibly modified 5 lines above presupposes bug-awareness of the correct ordering." Per this session's task instructions and README §0/§3, that rejection reasoning is not a valid concept under the current methodology (Expressibility asks only whether the grammar can represent the relation, never whether a bug-unaware developer would have written it) and is disregarded entirely below. The old draft is used only as a cross-reference for dependency names and a rough debug-value sketch, re-derived independently, not assumed correct. **One concrete correction found while re-deriving it**: the old draft's proposed syntax, `Unchanged(balances[msg.sender])`, uses a grammar token (`UNCHANGED : 'Unchanged'`, `Parser/Solidity.g4` line 654) that is defined in the lexer but never referenced by any parser rule (not `duringClause`, not `commonClause`) — it is dead/vestigial, not currently parseable as a clause. The grammar-current, correct construct for this exact need is `changed(intentValue, 'true'|'false')` (`VarChangedEval`, `commonClause` alternative, `Solidity.g4` line 327), backed end-to-end by `GuardianVerificationEngine.verify_during_changed` (confirmed by direct source read, see R1-3). This correction is applied throughout below.

---

## R1-1 — Reported Behavior Reconstruction

**Contract role**: `StakerVault` holds staked LP tokens on behalf of Backd pool depositors. It is explicitly *not* ERC-20-compliant (per its own NatSpec, L29–34) — `balances[account]` is purely internal bookkeeping; the underlying tokens never leave the contract on an internal `transfer`/`transferFrom`. Every balance-mutating entry point (`transfer`, `transferFrom`, `stakeFor` via `increaseActionLockedBalance`, `unstake`) is expected to keep an external `LpGauge` contract's own reward-accrual bookkeeping (`perUserShare`, `perUserStakedIntegral`) synchronized with `StakerVault`'s balances by calling `ILpGauge(lpGauge).userCheckpoint(user)` for each affected account.

**Function role**: `transfer(address account, uint256 amount)` (L105–123) moves `amount` of a user's internal staked-token bookkeeping balance from `msg.sender` to `account`, with no real ERC-20 asset movement. Its body, in source order:

```solidity
function transfer(address account, uint256 amount) external override notPaused returns (bool) {
    require(msg.sender != account, Error.SELF_TRANSFER_NOT_ALLOWED);              // L106
    require(balances[msg.sender] >= amount, Error.INSUFFICIENT_BALANCE);          // L107

    ILiquidityPool pool = controller.addressProvider().getPoolForToken(token);    // L109
    pool.handleLpTokenTransfer(msg.sender, account, amount);                      // L110

    balances[msg.sender] -= amount;                                              // L112 — BUGGY position
    balances[account] += amount;                                                 // L113 — BUGGY position

    address lpGauge = currentAddresses[_LP_GAUGE];                                // L115
    if (lpGauge != address(0)) {                                                 // L116
        ILpGauge(lpGauge).userCheckpoint(msg.sender);                            // L117
        ILpGauge(lpGauge).userCheckpoint(account);                               // L118
    }

    emit Transfer(msg.sender, account, amount);                                  // L121
    return true;                                                                 // L122
}
```

**Relevant locals/state**:
- `balances` (state, `mapping(address => uint256) public balances`) — each account's internal staked-token bookkeeping balance; this is the value `LpGauge.userCheckpoint` reads (via `StakerVault.stakedAndActionLockedBalanceOf(user)`, L289: `return balances[account] + actionLockedBalances[account];`) to compute newly-accrued reward share since the user's last checkpoint.
- `lpGauge` (local, L115) — the currently-configured `ILpGauge` address; `address(0)` if unset, in which case the checkpoint block is skipped entirely (L116 guard).
- `msg.sender` / `account` — the two accounts whose balances and reward checkpoints this call must keep consistent with each other.

**The disputed statements (L112–113 vs L117–118)**: the balance mutations (L112–113) execute, then the checkpoint calls (L117–118) execute — the reverse of the order every other balance-mutating entry point in this contract uses. Confirmed directly from source: `increaseActionLockedBalance` (L198–211) checkpoints at L207 *before* mutating `actionLockedBalances` at L209; `decreaseActionLockedBalance` (L219–236) checkpoints at L228 before mutating at L230–233; `unstake` (checked further in the file, checkpoint at L374 before the balance mutation at L390); and — the most directly comparable sibling — `transferFrom` (L133–177) checkpoints both `src` and `dst` at L157–158 *before* mutating `balances[src]`/`balances[dst]` at L168–169. `transfer()` is the sole exception, with checkpoint-after-mutation ordering.

**Variable-value intent (at the moment of each `userCheckpoint` call)**: at the program point where `ILpGauge(lpGauge).userCheckpoint(msg.sender)` executes, `balances[msg.sender]` must still equal its function-entry value — the transfer's own decrement must not yet have applied — and symmetrically for `ILpGauge(lpGauge).userCheckpoint(account)` and `balances[account]`. This is not a claim about `transfer()`'s *final* balances (those end up correct either way — the bug is purely about what an intermediate external call observes, not about what state the function leaves behind).

**Statement/line-level intent**: `transfer()` is trying to uphold the same invariant every other actionable function in this contract already upholds: "a user's reward-accrual checkpoint, for any function that changes their balance, must be taken against their *pre-mutation* balance" — so that `LpGauge`'s `perUserShare[user] += stakedAndActionLockedBalanceOf(user).scaledMul(poolStakedIntegral_ - perUserStakedIntegral[user])` formula (quoted verbatim in the report's PoC, `Web3Bugs/reports/112.md` L142–147) attributes reward accrual *up to now* to the balance the user actually held *up to now*, not to a balance they only just received (or just gave away) in this very call.

**Reported erroneous behavior** (H-01, verbatim, primary source): *"In `StakerVault.sol`, the user checkpoints occur AFTER the balances are updated in the `transfer()` function. The user checkpoints update the amount of rewards claimable by the user. Since their rewards will be updated after transfer, a user can send funds between their own accounts and repeatedly claim maximum rewards since the pool's inception. In every actionable function except `transfer()` of `StakerVault.sol`, a call to `ILpGauge(lpGauge).userCheckpoint()` is correctly made BEFORE the action effects."*

**Proof of Concept** (verbatim scenario, primary source): *"Assume a certain period of time has passed since the pool's inception. ... Account A stakes 1000 LP tokens. `balances[A] += 1000`. ... Account A can immediately send all balance to Account B via `transfer()`. Since the checkpoint occurs after the transfer, B's balance will increase and then `perUserShare[B]` will be updated. ... Assuming Account B is new to the protocol, their `perUserStakedIntegral[user]` will default to `0`. `perUserShare[B] += 1000 * (1 - 0) = 1000`. B is able to call `claimRewards()` and mint all 1000 reward tokens. B then calls `transfer()` and sends all 1000 staked tokens to Account C. Same calculation occurs, and C can claim all 1000 reward tokens. This process can be repeated until the contract is drained of reward tokens."*

**Recommended Mitigation Steps** (verbatim, primary source): *"In `StakerVault.transfer()`, move the call to `ILpGauge(lpGauge).userCheckpoint()` to before the balances are updated."*

**Sponsor disposition**: *"chase-manning (Backd) confirmed and resolved."* No separate judge commentary is present in this contest's report beyond the sponsor line.

**Expected/intended behavior**: for both `msg.sender` and `account`, the corresponding `userCheckpoint` call must fire while `balances[...]` still holds its function-entry value — i.e., the entire checkpoint block (L117–118) must execute *before* the entire balance-mutation block (L112–113), mirroring `transferFrom`'s own already-correct ordering.

**Patch intent**: the recommendation is a statement-block reordering (move L117–118 above L112–113), not a formula change — used below as evidence for *which* two values (`balances[msg.sender]`, `balances[account]`) must not yet have changed at the checkpoint calls, not transcribed as annotation syntax (§2/§3 — matching the patch's target state is not itself a problem, it is used only as evidence of the correct specification).

**Bug-relevant intended numeric behavior**: at the program point of each `userCheckpoint` call in `transfer()`, the corresponding account's `balances[...]` entry must still equal its value at function entry; the current code instead has already applied both mutations by that point, causing `LpGauge`'s checkpoint formula to attribute the *recipient's* full new balance to the *entire* elapsed-reward period since their last checkpoint (defaulting to the pool's inception for a fresh account), enabling repeated self-directed transfers to drain the reward pool.

---

## R1-2 — Intent Abstraction

Distinguishing property (patch's reordering used only as evidence for *which* two values must be unchanged at *which* two program points, not transcribed as annotation syntax): at the moment each `userCheckpoint` call fires, the corresponding `balances[...]` entry must equal its function-entry value, not its already-mutated value. **Intent-level orientation: Effect/state-transition-centered** — a claim about what a specific call observes at a specific point in execution (has this value changed by the time we get here), not a bound on a computed intermediate expression and not a claim about final persisted state (final `balances` are correct under both the buggy and the intended code — only the *intermediate* observation an external call makes differs).

---

## R1-3 — Select the least implementation-specific sufficient relation

**Preliminary check — does this relation need a function call inside `intentValue`?** No. The relation only ever needs to reference `balances[msg.sender]` / `balances[account]`, both ordinary mapping-entry `varRef`s, at two plain program points. `ILpGauge(lpGauge).userCheckpoint(...)` is the statement the relation is checked *next to* (it anchors the attachment point, R1-4/R1-6), never a term *inside* the relation itself — the relation never needs `userCheckpoint`'s return value or any expression built from it. No alpha-style blocker arises at all.

**Which grammar construct compares "current" against "function entry"?** This case turns out to have essentially one viable answer, not a genuine multi-way tradeoff, and it is worth recording explicitly why the more obvious-looking alternatives don't apply:
- `varRef(Entry)` / `varRef(Exit)` — grammar-restricted to `@Post` only (`{not self.inDuring}?` predicate guards, `Solidity.g4` L369–370). Not usable inside a `@During` clause at all.
- `varRef(Before)` / `varRef(After)` — legal under `@During`, but (per their only worked usage in this project, `07_web3bugs_35_H_11`'s `feeGrowthOutside1 == feeGrowthGlobal - feeGrowthOutside1(Before)`) these snapshot a variable's value immediately before/after *the specific assignment statement the `@During` is attached to*. `transfer()`'s checkpoint calls (L117–118) are not assignments to `balances` at all — there is no assignment statement here to hang a Before/After snapshot off of; `balances[msg.sender]`'s "before this statement" value at L117 is trivially identical to its "current" value (nothing between L113 and L117 touches `balances`), which is not the comparison this relation needs (function-entry, not immediately-prior-statement).
- `changed(intentValue, 'true'|'false')` (`VarChangedEval`, `commonClause`, `Solidity.g4` L327) — the grammar's dedicated construct for exactly "has this value changed since function entry, evaluated at an arbitrary program point." Confirmed by direct source read of `Analyzer/GuardianVerificationEngine.py::verify_during_changed` (L955–994): it reads `entry_env` (`fcfg.entry_env`) for the function-entry value and `cur_vars`/`cfg_node.variables` for the value at the annotation's own program point, then compares them — precisely the "Entry vs Current, at this specific point" semantics this relation needs, with no dependency on the target statement being an assignment.

This means the relation-tier ladder (R1-3's §4 ordering: directional → inequality/bound → relational invariant → exact equality) collapses to a single grammar-forced choice here, not a free selection among four tiers — `changed(x, false)` **is** the directional/state-change tier (tier 1, the weakest), and it is simultaneously the *only* available way to state an Entry-vs-Current comparison under `@During` at a non-assignment statement. There is no tier-2/3/4 alternative to weigh against it for *this* specific need (an inequality or exact-equality form would require referencing the entry value as an operand inside an ordinary comparison, which needs `varRef(Entry)` — unavailable under `@During` — so those tiers are not merely "not selected," they are grammatically unavailable for this exact relation shape).

**Rejected non-tier alternative — `DuringFunctionArg`** (`identifier '.' 'arg' '[' numberLiteral ']' relOp intentValue`, `Solidity.g4` L306): this grammar form checks a call's own *argument* value, e.g. `userCheckpoint.arg[0] == ...`. Not applicable here — `userCheckpoint`'s argument (`msg.sender`/`account`) is an address, not the balance; this construct cannot express "what internal state does the callee observe," only "what literal value was passed as an argument." Confirms this case has no alpha-style "need to peek inside the call" problem in the first place — the relation never needs anything about `userCheckpoint`'s internals, only about `StakerVault`'s own state immediately before the call is made.

**Selected relation, as a set of two independently-derived members (README §4's multi-annotation-set provision)**:
- **(A)** `changed(balances[msg.sender], false)` — attached `@During`, immediately before the checkpoint block (L117).
- **(B)** `changed(balances[account], false)` — attached `@During`, at the same point.

**Why a set, not a single relation — required negation check (§3/R1-3)**: does a single member's negation fail to catch an alternative implementation that retains the *reported* defect but produces it differently? Checked against two partial-fix shapes:
- **Reorder only `userCheckpoint(account)` to before L112–113, leave `userCheckpoint(msg.sender)` in place**: Member B (`account`) would report Satisfied (correctly reordered), but Member A (`msg.sender`) would still report Violated — **caught by the set**, but a lone Member B (chosen because it is the report's own headline "steal" mechanism) would have missed this partial defect on the `msg.sender` side entirely.
- **Reorder only `userCheckpoint(msg.sender)`, leave `userCheckpoint(account)` in place**: symmetric — Member A alone would miss it; the set catches it via Member B.
- **The actual buggy code** (neither reordered): both members Violated — caught by either member alone, and by the set.
No alternative implementation that leaves either checkpoint call observing an already-mutated balance for its own account escapes the two-member set's combined negation. This matches the report's and the recommendation's own framing exactly — both are phrased generally about "the user checkpoints" (plural) and "userCheckpoint()" (unqualified, covering both call sites), not about one account specifically — so this is one finding with one mechanism (checkpoint-block-after-mutation-block) applied symmetrically to two accounts, not two separately-reported mechanisms; both members pass their own full R1-1–R1-7 independently below and are recorded as a set per §4's three conditions.

**Discrimination check (explicit arithmetic, per §9 checklist item 1).** Scenario constructed directly from the report's own PoC narrative ("Account A stakes 1000 LP tokens... sends all balance to Account B"): `balances[msg.sender](Entry) = 1000` (Account A's staked balance before this call), `balances[account](Entry) = 0` (Account B, a fresh account), `amount = 1000` (a full-balance transfer, matching the PoC).

- **Buggy** (current code, mutations at L112–113 execute before the checkpoint block): at the program point immediately before L117, `balances[msg.sender] = 1000 - 1000 = 0` (current) vs. `1000` (entry) → Member A: `entry == current` → `1000 == 0` → **false ⟹ Violated.** `balances[account] = 0 + 1000 = 1000` (current) vs. `0` (entry) → Member B: `0 == 1000` → **false ⟹ Violated.**
- **Intended** (per the recommended fix, checkpoint block moved above the mutation block): at the relocated point immediately before the checkpoint calls — now preceding L112–113 entirely — neither mutation has executed yet: `balances[msg.sender] = 1000` (current) `== 1000` (entry) → Member A: **true ⟹ Satisfied.** `balances[account] = 0` (current) `== 0` (entry) → Member B: **true ⟹ Satisfied.**

**Winner: the two-member `changed(..., false)` set** — both members discriminate the actual buggy code, and together (not individually) they close the partial-fix gap identified above.

---

## R1-4 — During vs Post

**Chosen: During, for both members.** README's own During criterion applies directly and unusually cleanly here: "the relation concerns... a call argument, a statement-time value" — this relation is *literally* about what value an external call observes at the moment it fires, the textbook During use case. **Post is not viable for this relation at all** (not merely "less natural"): `transfer()`'s *final* `balances[msg.sender]`/`balances[account]` are numerically identical under the buggy and the intended code (both end at `0`/`1000` in the scenario above) — the reported defect changes nothing about `transfer()`'s own exit-time state, only what an intermediate call observes mid-execution. A `@Post` Entry/Exit relation on `balances` would be **vacuously true on both the buggy and the intended code** and would not discriminate at all; this is a sharper version of README's `SwordCrowdsale`/`CDP.update` caution (don't default to Post just because a value is a persistent state variable) — here Post isn't merely the wrong *default*, it is provably non-discriminating for this specific defect.

**Required explicit delta-exception check (README §4/R1-7).** `transfer()` contains **no loop of any kind** — confirmed by reading its entire body (L105–123: two `require`s, two external-call statements, two assignment statements, one local declaration, one `if` with no loop inside it, one `emit`, one `return`). (`StakerVault.sol` does contain `for` loops elsewhere — e.g. around L261's `total += balances[actions[i]]` — but that statement belongs to a different function entirely, unconnected to `transfer()`'s own CFG.) **Delta confirmed not applicable, trivially**, for both members.

---

## R1-5 — Relation form

**Changed-unchanged**, via the grammar's `VarChangedEval` `commonClause` alternative (`'changed' '(' intentValue ',' ('true'|'false') ')'`, `Solidity.g4` L327), reached through `duringClause -> commonClause` for both members. Not forced by the patch's syntax (R1-5's explicit caution) — the patch is a pure statement reordering with no assignment shape to mechanically inherit; the relation form was selected in R1-3 on independent grounds (it is the only grammar construct that can state "unchanged relative to function entry" at a non-assignment `@During` point, per the `varRef(Before)`/`varRef(Entry)` inapplicability argument above).

---

## R1-6 — Construct the target annotation

**Target annotation is a set of two `@During` clauses, both attached at the same point** (mirroring `20_web3bugs_29_H_08`'s within-one-function two-member `@Post` pattern, adapted to `@During`, since both members here live in the same function and the same program point).

**Attachment point (both members)**: `@During` on `transfer()`, placed immediately before `ILpGauge(lpGauge).userCheckpoint(msg.sender);` (L117) — i.e., inside the `if (lpGauge != address(0))` block, before the first checkpoint call. Both members are evaluated at this same CFG node's `cur_vars`; nothing between L117 and L118 touches `balances`, so evaluating Member B at this same point (rather than specifically before L118) gives an identical result — the shared placement matches the report's own framing ("the user checkpoints occur AFTER the balances are updated," referring to the whole checkpoint block as a unit against the whole mutation block).

**Scenario precondition this instantiation relies on (README's scenario-conditioning note, §4/R1-7)**: `currentAddresses[_LP_GAUGE] != address(0)` (an `LpGauge` is configured — the L116 guard's own condition, already present in the source, needed for the checkpoint block, and hence the attachment point, to execute at all) and `amount != 0` (a zero-amount transfer would leave both `balances` entries unchanged even under the buggy ordering, producing a vacuous Satisfied on both members with no bug present to detect — the report's own PoC uses a full nonzero-amount transfer). Neither condition is written into the relation text itself — both are properties of the concrete debug/batch scenario that would be used at RQ1-B time (deferred), matching this project's established convention (e.g. `65_H_01`'s `lastFee(Entry) != 0` precondition) for stating reachability/non-degeneracy preconditions in prose rather than inside the relation.

**Target annotation**:
```solidity
function transfer(address account, uint256 amount) external override notPaused returns (bool) {
    require(msg.sender != account, Error.SELF_TRANSFER_NOT_ALLOWED);
    require(balances[msg.sender] >= amount, Error.INSUFFICIENT_BALANCE);

    ILiquidityPool pool = controller.addressProvider().getPoolForToken(token);
    pool.handleLpTokenTransfer(msg.sender, account, amount);

    balances[msg.sender] -= amount;
    balances[account] += amount;

    address lpGauge = currentAddresses[_LP_GAUGE];
    if (lpGauge != address(0)) {
        // @During changed(balances[msg.sender], false)
        // @During changed(balances[account], false)
        ILpGauge(lpGauge).userCheckpoint(msg.sender);
        ILpGauge(lpGauge).userCheckpoint(account);
    }

    emit Transfer(msg.sender, account, amount);
    return true;
}
```
Both referenced identifiers (`balances[msg.sender]`, `balances[account]`) are ordinary in-scope mapping entries at this program point — plain state, no synthetic constant introduced (contrast README's `900`-style derived-constant guidance, inapplicable here since neither operand is a scenario-specific literal).

**Quantification note**: each member's subject is one specific, concretely-identified mapping entry (`balances[msg.sender]`, `balances[account]`) — `msg.sender` and `account` are the two actual, named parties to this one execution, not a representative element standing in for "every user's balance." Contrast `web3bugs_83_H_01`'s genuine representative-pool instantiation (`poolInfo[1]` standing in for "every pool"); this is not that — no universal-quantification gap applies to either member.

---

## R1-7 — Expressibility decision

**Member A — `changed(balances[msg.sender], false)`**:

**Values referenceable at a legal program point**: Yes. `balances[msg.sender]` is an ordinary mapping-entry `varRef`, in scope throughout `transfer()`, referenced at an ordinary `@During` program point (immediately before L117) — no external-contract boundary, no missing proxy.

**Arithmetic/logical relation representable**: Yes. `changed(balances[msg.sender], false)` is a single `VarChangedEval` clause, no arithmetic beyond the built-in Entry-vs-Current comparison the construct itself performs.

**No function call inside `intentValue`**: confirmed not an issue (R1-3's preliminary check) — `balances[msg.sender]` is a plain mapping access, not a call.

**Observation point supported — explicit delta check.** `transfer()` contains no loop anywhere (R1-4); the attachment point (immediately before L117) is an ordinary, non-loop `@During` node. **Delta confirmed not applicable, trivially.**

**Outcome: Expressible = YES.**

**Member B — `changed(balances[account], false)`**: identical reasoning, symmetric to Member A — `balances[account]` in scope, same `VarChangedEval` form, same attachment point, delta confirmed not applicable.

**Outcome: Expressible = YES.**

**Set-level outcome: Expressible = YES** (both members independently Expressible, per §4's multi-annotation-set discipline).

---

## Section 5 — Value/Algorithm and Usable/Unusable

- **Algorithm-level** — per the paper's own classification ("operation ordering, an absent state update, or a missing procedure call"), this is a direct, unambiguous instance of the "operation ordering" pattern: the intended computation for `transfer()` requires the checkpoint block (L117–118) and the balance-mutation block (L112–113) to execute in the order [checkpoint, then mutate] — exactly the order `transferFrom` (L157–158 then L168–169) and every other actionable function in this contract already use — but `transfer()` has both blocks present and both individually correct in isolation, only sequenced in the wrong relative order. Nothing inside either block's own arithmetic is wrong (`balances[msg.sender] -= amount` and `balances[account] += amount` are themselves correct; `userCheckpoint(msg.sender)`/`userCheckpoint(account)` are themselves the correct calls with the correct arguments) — the defect is purely in the statement-block ordering, the textbook shape the paper's own definition names directly, with no need for the more careful "what's missing from the computation's own steps vs. an incidental implementation detail" analysis `web3bugs_16_H_06` required (there, a spare unused helper's existence was a tempting but non-decisive signal; here there is no missing statement or spare unused helper at all — every needed statement already exists, only in the wrong relative order).
- **Usable** — both values each member's relation needs (`balances[msg.sender]`, `balances[account]`) are referenceable, as ordinary in-scope mapping entries, at the annotation's program point; nothing behind an external-contract boundary is needed *inside* the relation itself (§5, purely a representational-resources question) — `LpGauge`'s own reward-accrual formula matters for *understanding why* this ordering is the correct spec (R1-1, and RQ2-A's Additional-functions/External-specification fields below), but the relation's own operands never need to reach across that boundary.

---

## RQ2-A — Specification Requirements profile

*(One profile for the set; both members share the same relevant-statement/value footprint since they are evaluated at the same program point over symmetric operands.)*

**Relevant statements** (within `transfer` itself):
1. `balances[msg.sender] -= amount;` (L112) — the statement whose execution is what actually flips Member A from Satisfied to Violated; defines the "Current" value Member A observes at the checkpoint point.
2. `balances[account] += amount;` (L113) — symmetric, for Member B.
3. `ILpGauge(lpGauge).userCheckpoint(msg.sender);` (L117) — Member A's attachment-point/subject statement, needed as context for what is being guarded (the call whose observed value the relation constrains), even though the call's own internal behavior is captured separately under "Additional functions required," not expanded here (§6).
4. `ILpGauge(lpGauge).userCheckpoint(account);` (L118) — Member B's attachment-point/subject statement, symmetric to (3).

Total: **4 relevant statements** (revised on review — see below).

**Excluded, with reason (Step 1, README §6)**:
- `require(msg.sender != account, Error.SELF_TRANSFER_NOT_ALLOWED);` (L106) — pure reachability gate; does not redefine `balances` or any other relation operand, and the selected relation's own validity does not depend on where this specific guard is drawn (the relation would hold/fail identically for any two distinct accounts). Excluded, matching the `require(...)` exclusion precedent (`62_H_10`).
- `require(balances[msg.sender] >= amount, Error.INSUFFICIENT_BALANCE);` (L107) — pure reachability gate (read-only check, prevents underflow/revert on L112); does not redefine `balances`. Excluded, same reasoning.
- **`address lpGauge = currentAddresses[_LP_GAUGE]; if (lpGauge != address(0)) { ... }` (L115–116) — excluded (revised on review, was counted as a combined unit in an earlier draft).** Re-examined directly against the Step 1 test: does the guard's own condition affect how either relation's operands (`balances[msg.sender]`, `balances[account]`) get *defined*? No — both mutations (L112–113) execute unconditionally, regardless of this guard's outcome; the guard only determines whether the *attachment point* (the checkpoint calls) is *reached* at all — the same reachability/observation-point role a `require(...)` gate plays, just spelled as an `if` rather than a revert. The earlier draft's citation of `65_H_01` as precedent for counting a containing branch does not actually support counting this one: `65_H_01`'s own "1 relevant statement" was not a separate branch layered on top of an already-counted target statement — that case's defect is a *missing* statement, so the branch condition and the (absent) target coincide at the same attachment point, with nothing to count in addition. Here, by contrast, the target statements (L112/113/117/118) are already fully separate and enumerable, and the guard adds nothing to their derivation — only to reachability, which is already captured in prose as this case's own scenario precondition (R1-6). Excluded, matching the `require(...)`-gate treatment, not counted even as a case note.
- `ILiquidityPool pool = controller.addressProvider().getPoolForToken(token); pool.handleLpTokenTransfer(msg.sender, account, amount);` (L109–110) — an external call to a *different* contract (`LiquidityPool`), affecting that contract's own pool-level accounting, not `StakerVault.balances`. Step 1 test: would changing `handleLpTokenTransfer`'s specific behavior change either member's derivation or validity? No — both members only concern `StakerVault`'s own `balances` mapping at a later program point, untouched by this call. Not load-bearing; excluded entirely, not even as a case note.
- `emit Transfer(msg.sender, account, amount);` (L121), `return true;` (L122) — textually after both attachment points; no effect on either relation. Excluded (trivially outside the relevant window).
- `transferFrom`'s own checkpoint-before-mutation ordering (L157–158, L168–169) and the other actionable functions' analogous ordering (`increaseActionLockedBalance` L207/209, `decreaseActionLockedBalance` L228/230–233, `unstake` L374/390) — inspected in R1-1 only to discover/corroborate the codebase's own "checkpoint before mutation" convention (the source of the intended-behavior reconstruction and of the report's own "every actionable function except `transfer()`" framing). Neither selected relation's own validity depends on any of these siblings' specific implementations — changing `transferFrom`'s internals, for instance, would not change whether `changed(balances[msg.sender], false)` holds inside `transfer()`. Excluded per the "alternative-rejection/corroboration inspection doesn't count" corollary (§6), matching `65_H_01`'s treatment of its own sibling branches.

**Unique relevant program values**:
- State (2): `balances[msg.sender]` (Member A's subject), `balances[account]` (Member B's subject) — listed as two distinct entries rather than one generic `balances` container entry, since the two-member set's entire point is that they are two independently-checkable observables of the same mapping at two (here, coincident) program points, not one generic "some element" access.
- Global (1): `msg.sender`.
- Parameter (2): `account` (the mapping key for Member B, and the value a reader must trace to know who the recipient is), `amount` (the RHS operand of both counted assignments L112–113; its nonzero-ness is the scenario precondition that makes the buggy and intended executions actually diverge, per R1-6).
- Local (1): `lpGauge` (revised justification on review — counted not for reachability-tracing, but as the *call-receiver* of the two counted `userCheckpoint` statements, L117/L118: `ILpGauge(lpGauge).userCheckpoint(...)` — the same "defining statement excluded, but the value is counted because it's a call-receiver/argument of an otherwise-counted statement" treatment `web3bugs_101_H_02`'s RQ2-A already established for `_strategy`/`_borrowAsset`. `lpGauge`'s own defining statement, L115, is excluded above as pure reachability — that exclusion is about the *statement*, not about whether the *value* it produces still needs to appear here, and it does, since L117/L118 remain counted statements that reference it.)

Total: **6 unique relevant program values** (2 state / 1 global / 2 parameter / 1 local).

**Additional functions required (1)**: `ILpGauge.userCheckpoint(address user)` — semantic-dependency note (mandatory, §6): per the report's own PoC snippet (quoted verbatim in R1-1, `Web3Bugs/reports/112.md` L142–147), this cross-contract call internally executes `perUserShare[user] += stakedAndActionLockedBalanceOf(user).scaledMul(poolStakedIntegral_ - perUserStakedIntegral[user])` — i.e. it reads the *calling* `StakerVault`'s current `balances[user]` (via `stakedAndActionLockedBalanceOf`, itself `balances[account] + actionLockedBalances[account]`, `StakerVault.sol` L289) to compute newly-accrued reward share since `user`'s last checkpoint. This is precisely the fact that makes the selected relation's derivation meaningful at all: if `userCheckpoint` did not read the vault's balance internally, the ordering of L112–113 relative to L117–118 would have no observable consequence and there would be no defect to specify. **Step 1: load-bearing** (changing this specific guarantee — "reads the caller's current balance to compute reward accrual" — would directly change whether the relation's derivation is sound). **Step 2: protocol-specific** (Backd's own `LpGauge` reward-accrual accounting, not a generic language/library primitive like SafeMath or a fixed-point library) — counts normally toward the metrics below, not a case-note-only entry. `userCheckpoint`'s own internal statements are not expanded/counted here, per §6's no-recursive-counting rule — it is counted once, atomically, as this one entry.

**Additional protocol/application-specific contracts/libraries required (1)**: `LpGauge` (the concrete implementation behind the `ILpGauge` interface) — its `perUserShare`/`poolStakedIntegral`/`perUserStakedIntegral` accrual formula is Backd-specific business/accounting logic, not derivable from `ILpGauge`'s bare interface signature (`Dependencies/interfaces/ILpGauge.sol`: `function userCheckpoint(address user) external returns (bool);` — a return-type-only signature that says nothing about what state it reads). **`LpGauge.sol`'s own implementation is not present anywhere in this project's `Dependencies/` or `evaluation/RQ1/target_contracts_original/dependencies/` trees** (confirmed by directory search — only the interface file exists); the accrual formula used above was sourced from the audit report's own PoC code snippet, not from locally available source.

**Context breadth: 3** (cross-contract/library) — not 2, because the relation's justification (why "unchanged at the checkpoint call" is the bug-relevant question) depends on `LpGauge`'s *specific accrual formula*, not merely on knowing that `userCheckpoint` is "some external call that must be made" (which would be Context breadth 2, same-contract-adjacent reasoning). Reading and citing `LpGauge`'s own accounting mechanism, sourced from outside `StakerVault.sol`'s own file, is what breadth 3 is for.

**External specification required: Yes.** `LpGauge`'s specific reward-accrual convention — `perUserShare[user] += stakedAndActionLockedBalanceOf(user) * (poolStakedIntegral - perUserStakedIntegral[user])`, with `perUserStakedIntegral[user]` defaulting to `0` for a fresh account — is Backd protocol-specific business/accounting logic needed to justify *why* the selected relation is the correct specification, beyond what `StakerVault.sol`'s own source or general Solidity/language semantics provide. This is the narrower, later question §6 asks (not "was the report read," which is always Yes and uninformative) — R1-1/R1-2 had already fixed the intended behavior ("checkpoint before mutation, symmetric to `transferFrom`") from `StakerVault.sol`'s own internal consistency alone; it is *justifying why that ordering matters numerically* (the over-claim mechanism) that additionally required this protocol-specific accrual formula, sourced from the report's PoC rather than from locally available `LpGauge.sol` source.

---

## Section 7 — Alternatives-considered summary

| # | Relation | Tier | Expressible? | Discriminates? | Verdict |
|---|----------|------|------|------|------|
| 1 | `@Post` Entry/Exit equality on final `balances[msg.sender]`/`balances[account]` | Entry-Exit | Yes (grammar-wise) | **No** | Rejected — final balances are numerically identical under buggy and intended code (the bug changes only what an intermediate call observes, not final state); a `@Post` relation on final balances is vacuously true on both and cannot discriminate this defect at all (sharper than README's usual During/Post caution — here Post is provably non-discriminating, not merely a wrong default) |
| 2 | `@During changed(balances[msg.sender], false)` alone (Member A only) | Directional/state-change | Yes | Yes for the actual buggy code, but incomplete | Considered, not selected alone — the required negation check finds a concrete partial-fix (reorder only the `account`-side checkpoint) it would miss; promoted into a two-member set with #3 (README §4) |
| 3 | `@During changed(balances[account], false)` alone (Member B only) | Directional/state-change | Yes | Yes for the actual buggy code (and specifically the report's own headline "recipient over-claims" mechanism), but incomplete | Considered, not selected alone — symmetric gap (misses a partial-fix reordering only the `msg.sender`-side checkpoint); promoted into the set with #2 |
| 4 | **Two-member set: (A) `changed(balances[msg.sender], false)` + (B) `changed(balances[account], false)`, both `@During`, same attachment point** | Directional/state-change ×2 | Yes | Yes — jointly catches the actual buggy code and both partial-fix variants | **Selected** |
| 5 | `DuringFunctionArg`: `userCheckpoint.arg[0] == ...` | Call-argument relation | N/A | N/A | Rejected — not applicable; `userCheckpoint`'s argument is an address (`msg.sender`/`account`), not the balance value; this construct checks a call's literal passed argument, not internal callee-observed state |
| 6 | `balances[msg.sender] == balances[msg.sender](Before)` (or `(Entry)`) as an explicit equality | Exact equality | Not well-formed for this use | — | Rejected — `Before`/`After` are tied to a specific *assignment* statement's own pre/post state (no such assignment exists at the checkpoint-call attachment point); `Entry`/`Exit` are grammar-restricted to `@Post` only. `changed(x, bool)` is the grammar's only construct for "current vs. function-entry, at an arbitrary `@During` point" |

---

## RQ1-B / RQ2-B

Deferred per README §8. Not run, not predicted. One forward-looking observation for whoever runs RQ1-B: both members reference a plain mapping entry (`balances[msg.sender]`/`balances[account]`) with no arithmetic, no loop, and no call inside the relation itself — structurally about as simple as this project's `@During` targets get (comparable to `65_H_01`'s single-comparison `@Post`) — the only engine-specific novelty is that it is a *set* of two `changed(...)` clauses at one shared attachment point rather than a single relation, which RQ1-B would need to instantiate and run as two separate checks (matching `20_web3bugs_29_H_08`'s established two-`@Post`-member precedent, adapted here to `@During`). No loop-propagation or `abi.decode`-style caution applies (contrast `3_H_04`/`29_H_11`).

---

## Summary

- **Expressible: Yes**, for both members of the set. Values referenceable (`balances[msg.sender]`, `balances[account]`, both ordinary in-scope mapping entries), relation representable (`changed(x, false)`, the grammar's `VarChangedEval` construct — confirmed the only viable form for an Entry-vs-Current comparison at a non-assignment `@During` point, since `varRef(Entry)`/`varRef(Exit)` are `@Post`-only and `varRef(Before)`/`varRef(After)` are tied to a specific assignment this attachment point doesn't have), observation point supported (no loop anywhere in `transfer()`, delta confirmed not applicable).
- **Target relation (a set, per README §4)**: (A) `@During changed(balances[msg.sender], false)` and (B) `@During changed(balances[account], false)`, both attached immediately before the `if (lpGauge != address(0))` block's first statement (L117) in `transfer()`. Scenario-conditioned on `currentAddresses[_LP_GAUGE] != address(0)` (checkpoint block reachable) and `amount != 0` (a degenerate zero-amount transfer would leave both members vacuously Satisfied under either ordering).
- **This differs from the old L5b conclusion**: the retired draft (`evaluation/RQ1/annotation_plans.md` line 1164) reached essentially the same *relation content* (an unchanged-balance check immediately before the checkpoint call, for both `msg.sender` and `account`) but labeled the case `not_detectable` on the grounds that writing "must be unchanged" on a variable visibly modified five lines above presupposes bug-awareness of the correct ordering. Under the current methodology that reasoning is not a valid Expressibility consideration at all (README §0/§3/R1-7 — Expressibility asks only whether the grammar can represent the relation, never whether a developer would have known to write it), so it plays no role in the verdict here. **A genuine, independent correction was also found while re-deriving this case**: the old draft's proposed syntax, `Unchanged(balances[msg.sender])`, is not actually valid under the current grammar — `UNCHANGED` is a lexer token with no parser-rule usage (`Solidity.g4` L654, dead/vestigial) — while `changed(balances[msg.sender], false)` (`VarChangedEval`) is the grammar-current, engine-backed (`verify_during_changed`) construct for this exact need.
- **Quantified property instantiated: No**, for both members — each targets one specific, named account's mapping entry in this one execution (`msg.sender`, `account`), not a representative element standing in for "every user."
- **Algorithm-level** (operation ordering — the paper's own canonical Algorithm-level pattern: two correct, individually-unmodified statement blocks in the wrong relative order, not a wrong operand within an existing formula and not an absent statement), **Usable** (all values each relation needs are directly referenceable in-scope; the external `LpGauge` boundary matters for *justifying* the relation via RQ2-A, never for the relation's own operands), `@During` (During is not merely preferred but the only discriminating scope — a `@Post` on final balances is provably vacuous for this defect, per Section 7 alternative #1), changed-unchanged relation form (`VarChangedEval`) ×2.
- **RQ2-A profile** *(relevant-statement count revised on review — see Review Notes)*: 4 relevant statements (the two disputed mutation assignments L112/L113, and the two checkpoint-call attachment-point statements L117/L118 — the `lpGauge`-lookup-and-guard, L115–116, is excluded as a pure reachability gate, matching this project's `require(...)`-gate exclusion pattern rather than being counted as a containing-branch unit), 6 unique relevant program values (2 state / 1 global / 2 parameter / 1 local — `lpGauge` is still counted, not for reachability but as the call-receiver of the two counted `userCheckpoint` statements, the same treatment `web3bugs_101_H_02` gives `_strategy`/`_borrowAsset`), 1 additional function required (`ILpGauge.userCheckpoint`, semantic-dependency note: reads the caller's current balance via `stakedAndActionLockedBalanceOf` to compute reward accrual — this is *why* the relation's ordering requirement is bug-relevant at all), 1 additional protocol-specific contract required (`LpGauge`'s own accrual formula, sourced from the report's PoC since `LpGauge.sol`'s implementation is not present in this project's dependency set), Context breadth 3 (cross-contract/library — the specific accrual *formula*, not just the interface signature, is load-bearing), External specification required: Yes (Backd-specific reward-accrual convention — not merely "the report was read," but a protocol-specific implementation fact, namely that this particular `userCheckpoint` reads the caller's balance at all, that is not recoverable from any locally-available source: neither `stakedAndActionLockedBalanceOf`'s own NatSpec nor `ILpGauge`'s bare interface signature document it).
- **Methodological judgment calls made in this pass**: (1) selected a two-member `changed(...)` set rather than a single relation, specifically because the required negation check found a concrete partial-fix gap for either member alone (reordering only one of the two checkpoint calls) — recorded in §7, not asserted from habit, and justified under README §4's three multi-annotation-set conditions (each member independently R1-1–R1-7'd below; the report itself frames both checkpoint calls as one symmetric mechanism of one finding; Intent coverage judged against the set's combined negation); (2) determined that `@Post` is not merely non-preferred but *provably non-discriminating* for this defect (final balances are identical under buggy and intended code), a stronger version of README's usual During/Post caution; (3) determined that the `varRef(Entry)`/`varRef(Before)`-based snapshot extension (README §4, the `35_H_11`/`42_H_01` rescue) does *not* apply to this relation's specific shape, because the attachment point is not an assignment statement — `changed(x, bool)` remains the only grammar-legal way to state this comparison, which happens to also be the weakest/directional tier, so R1-3's usual "try weaker tiers first" ladder collapses to one forced option rather than a genuine multi-tier selection; (4) corrected the old draft's proposed `Unchanged(...)` syntax to the grammar-current `changed(...)` form, verified against both the grammar file and the engine's `verify_during_changed` implementation, independent of and unrelated to the retired bug-awareness objection.
- **RQ1-B/RQ2-B**: deferred, not run in this pass. No case-specific engine-precision caution identified beyond the two-member-set instantiation mechanics noted in the RQ1-B/RQ2-B section above — both relations are plain mapping-entry `changed()` checks with no loop, no arithmetic, and no call inside the relation itself.

---

## Review Notes

Prompted by a fresh external-LLM critique this session, four points were checked; one correction applied.

**1. Two-member set — approved, no change.** Checked against this project's own `web3bugs_29_H_08` precedent (a single defect pattern applied symmetrically across two subjects, token0/token1, recorded as a two-member set) — `112_H_01`'s shape (one checkpoint-ordering defect, applied symmetrically to `msg.sender`/`account`) is structurally the same, and the analysis already frames it correctly ("one mechanism... applied symmetrically to two accounts, not two separately-reported mechanisms," R1-3) rather than claiming two distinct mechanisms. The required negation check's partial-fix finding (reordering only one checkpoint call escapes a single-member relation) independently confirms the set is not padding.

**2. Algorithm-level / Usable — approved, no change.**

**3. RQ2-A relevant statements: 5 → 4, corrected.** The original count treated `address lpGauge = currentAddresses[_LP_GAUGE]; if (lpGauge != address(0)) { ... }` (L115–116) as a combined containing-branch unit, citing `web3bugs_65_H_01` as precedent. Re-examined: `65_H_01`'s own "1 relevant statement" was not a containing branch counted *in addition to* a separately-identified target statement — that case's defect is a *missing* statement, so its branch condition and its (absent) target statement coincide at the same attachment point, leaving nothing to count beyond the branch itself. Here, the target statements (L112/L113/L117/L118) are already fully separate and enumerable, and the `lpGauge` guard's own condition does not affect how either relation's operands are *defined* — both mutations execute unconditionally regardless of the guard, and the guard only gates whether the *attachment point* is reached, the same reachability role a `require(...)` gate plays elsewhere in this project (already excluded, `62_H_10`/`65_H_01` precedent). Excluded. `lpGauge` itself remains a counted *value* (6 unique values, unchanged), on different grounds: it is the call-receiver of the two still-counted `userCheckpoint` statements (L117/L118), matching how `web3bugs_101_H_02`'s RQ2-A counts `_strategy`/`_borrowAsset` as values despite excluding their own defining statement.

**4. External specification required: Yes — approved, no change, but the justification is sharpened.** A candidate revision to "No" was considered on the ground that the audit report is R1-1's normal ground truth for every case and reading it shouldn't itself trigger "Yes." Rejected: README §6's "the audit report itself never counts here" excludes the *act* of reading the report (true for every case, hence uninformative if it triggered Yes), not every *fact* the report happens to convey. The operative test is whether the load-bearing fact is a protocol-specific implementation detail unrecoverable from local source — and here it is: neither `StakerVault.stakedAndActionLockedBalanceOf`'s own NatSpec nor `ILpGauge`'s bare interface signature (`function userCheckpoint(address user) external returns (bool);`) documents that this particular `userCheckpoint` reads the caller's balance at all (confirmed by direct re-read of both). A generic "checkpoint-before-mutate is a common DeFi idiom" argument was considered and rejected as insufficient — knowing the idiom exists doesn't establish that *this specific* `userCheckpoint` implementation follows it, absent evidence. This verdict is also consistent with `web3bugs_113_H_05`'s own External-spec=Yes determination this session, reached on the same "protocol-specific fact, not recoverable from local source, sourced via the report" ground.
