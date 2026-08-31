# web3bugs_45_H_02 — Agent A Analysis (R1-1 → R1-7, RQ2-A)

Methodology: `First Revision/phase_reviews/README.md` (current, non-superseded version).

## Case metadata

- **Case ID**: `web3bugs_45_H_02`
- **Contract**: `CreditLimitByMedian` (Union Finance, contest 45)
- **Function**: `getLockedAmount(LockedInfo[] memory array, address account, uint256 amount, bool isIncrease)` — `public pure`
- **Source read**: `evaluation/RQ1/target_contracts_original/web3bugs_45_H_02.sol` (verbatim, lines 27–78 for `getLockedAmount`); `LockedInfo` struct definition read from `evaluation/RQ1/target_contracts_original/dependencies/ICreditLimitModel.sol` lines 9–14 (`staker`, `vouchingAmount`, `lockedAmount`, `availableStakingAmount`, in that field order).
- **Audit report**: `C:\Users\isjeon\Web3Bugs\reports\45.md`, H-02, "Wrong implementation of `CreditLimitByMedian.sol#getLockedAmount()` makes it unable to unlock `lockedAmount` in `CreditLimitByMedian` model" (line 109 in that file). Read in full per README §0.5; this finding's section contains only the buggy snippet, a one-line stated defect, and a one-line Recommendation — no separate PoC section exists for this finding (verified by reading the full H-02 section, lines 109–159).
- **Existing prior-pipeline label** (historical, retired methodology, recorded for continuity only): `evaluation/RQ1/annotation_plans.md`'s entry for this case records `Status: not_detectable (L1b: loop-body-granularity)`, with the stated reason: *"IntentChecker does not analyze loops on a per-statement basis... Annotations on the final return value outside the loop are possible, but since the fixed-point result is already imprecise, meaningful detection is difficult."* This reasoning is explicitly an **imprecision** claim (the joined/widened loop state being too coarse), not an "observation point never evaluated" architectural claim — the same category of reasoning already rejected on its merits in `02_web3bugs_71_H_11`'s case history (its first refinement pass) as out of scope for R1-7. Per the task brief, this old label is **not** assumed to predict this case's R1-7 outcome; the delta exception is checked below directly against this case's own facts.

---

## R1-1 — Reported Behavior Reconstruction

**Contract role** (brief — clarifies the semantics of the values involved, not needed at more depth): `CreditLimitByMedian` is a pluggable `ICreditLimitModel` implementation used by Union Finance's `UserManager` to compute how much of a staker's stake is "locked" (held as collateral backing a borrower's credit line) as vouching relationships change.

**Function role**: `getLockedAmount()` is a `pure` helper, called by `UserManager.updateLockedData()` (confirmed via `Dataset/Web3Bugs/S6_1/contest_45_H_02/user_UserManager.sol` L594: `members[lockedInfoList[i].staker].creditLine.lockedAmount[borrower] = creditLimitModel.getLockedAmount(...)`), that recomputes one staker's new locked amount given the full `LockedInfo[]` list for a borrower, the staker (`account`), the amount of principal change (`amount`), and a direction flag (`isIncrease` — true when the borrower's debt grew, requiring more stake to be locked; false when debt shrank, allowing stake to be unlocked). **The caller (`UserManager.updateLockedData`) is not load-bearing for the selected relation** (see RQ2-A "Additional functions" below) — it is described here only for contract/function-role context, per R1-1's "only to the depth actually needed" instruction.

**Relevant locals/parameters** (only the ones the bug touches — the `isIncrease == true` branch, L37–62, is a separate, untouched code path, not read further except to note its existence):
- `array` (parameter, `LockedInfo[] memory`) — the list of vouching relationships for the current borrower; each element has `.staker`, `.vouchingAmount`, `.lockedAmount`, `.availableStakingAmount`.
- `account` (parameter, `address`) — the staker whose new locked amount is being computed.
- `amount` (parameter, `uint256`) — the magnitude of the borrower's principal change (here, a decrease, since we're in the `isIncrease == false` branch).
- `newLockedAmount` (local, declared L35, assigned inside the loop L66/L68) — the value that becomes the function's return value once a matching staker is found.
- The buggy statement (**L66**): `newLockedAmount = array[i].lockedAmount - 1;`, reached when `array[i].lockedAmount > amount` (L65) inside the `isIncrease == false` branch's loop (L64–74).

**Variable-value intent (L66).** When unlocking (`isIncrease == false`) and the staker's current `lockedAmount` exceeds the amount being unlocked, `newLockedAmount` should be reduced by exactly `amount` — i.e., `array[i].lockedAmount - amount` — not by the constant `1`.

**Statement/line-level intent.** The `isIncrease == false` branch is trying to uphold: "unlocking `amount` from a staker's position reduces their locked amount by exactly `amount` (floored at 0 when `amount` would exceed the current locked amount, which the untouched `else` branch at L68 already handles correctly)." The bug breaks only the first half of this (the `> amount` regime); the `<= amount` regime (L68, `newLockedAmount = 0`) is untouched, correct in both buggy and patched code, and not part of the reported defect.

**Reported erroneous behavior** (H-02, verbatim): *"Based on the context, at L66, `newLockedAmount = array[i].lockedAmount - 1;` should be `newLockedAmount = array[i].lockedAmount - amount;`. The current implementation is wrong and makes it impossible to unlock `lockedAmount` in `CreditLimitByMedian` model."* Sponsor (`kingjacob`) acknowledged; judge (`GalloDaSballo`) commented: *"The warden identified a mistake in the accounting that would make it impossible to unlock funds, mitigation seems to be straightforward."*

**Expected/intended behavior**: for the branch `array[i].lockedAmount > amount` (inside `isIncrease == false`), `newLockedAmount = array[i].lockedAmount - amount`.

**Patch intent**: the report's Recommendation is the literal one-line substitution `newLockedAmount = array[i].lockedAmount - amount;`, replacing the hard-coded `- 1`. Used as corroborating evidence per README §2, not transcribed mechanically — see R1-2/R1-3 for why the selected relation, though it ends up numerically identical to this substitution, is derived from the branch's own already-correct sibling structure (the untouched `else` at L68), not copied from the patch.

**Related but out-of-scope finding**: the same report also lists **M-01** ("`getLockedAmount()` will lock a much bigger total amount of staked tokens than expected"), which concerns the *other* branch of the same function (`isIncrease == true`, L37–62) — a different code path, a different (Medium) severity finding with its own issue number. Per README §4's multi-relation-set rule ("the report itself identifies the additional mechanism as part of the *same* finding — not a different, separately-numbered finding"), M-01 is **not** folded into this case's target relation; it is a distinct case if/when it is separately analyzed.

**Concrete scenario (constructed, not from the report — the report gives no PoC beyond the one-line fix)**: `isIncrease = false`; `array` has one entry (index 0, chosen as the representative matching element — see R1-6's quantification note) with `array[0].staker == account` and `array[0].lockedAmount = 100`; `amount = 50` (chosen `≠ 1` deliberately — see the boundary caveat below).
- Trace: `array.length != 0` (skip L33's early return); `isIncrease == false` → loop `i = 0`: `array[0].lockedAmount (100) > amount (50)` → true (L65) → **buggy**: `newLockedAmount = 100 - 1 = 99`; `account == array[0].staker` → true → `return 99`.
- **Intended** (report's own formula): `newLockedAmount = 100 - 50 = 50` → `return 50`.
- Buggy (99) vs. intended (50): confirms "impossible to unlock" — the buggy code returns a locked amount far closer to the original 100 than the correct 50, i.e., barely unlocks anything regardless of how large `amount` is (as long as `amount < lockedAmount`), matching the reported symptom exactly.

**Boundary caveat (found while constructing the scenario, recorded per the same discipline as `71_H_11`'s ceiling-collapse note)**: if `amount == 1`, buggy (`lockedAmount - 1`) and intended (`lockedAmount - amount`) coincide — the bug has zero effect on the returned value for that specific input. This is a scenario-selection caveat, not a defect in the relation's form: any `amount ∉ {1}` (with `lockedAmount > amount`) exposes the bug; the constructed scenario above uses `amount = 50` specifically to avoid this collapse.

---

## R1-2 — Intent Abstraction

Governing question: for a staker whose position is being unlocked (`isIncrease == false`) and whose current `lockedAmount` exceeds the unlock `amount`, the new locked amount must be reduced by exactly `amount` — the value the code already receives as a parameter — not by an unrelated hard-coded constant.

**Orientation: value-centered** — a constraint on `newLockedAmount` (which, in the matching branch, becomes the function's return value) in terms of two other already-in-scope values (`array[i].lockedAmount`, `amount`). Not a state-transition claim (the function is `pure`, has no persistent-state side effects of its own).

---

## R1-3 — Select the least implementation-specific sufficient relation

1. **Directional/monotonicity relation**: e.g. "the returned value decreases as `array[0].lockedAmount` decreases." **Rejected — not discriminating.** Both the buggy (`lockedAmount - 1`) and intended (`lockedAmount - amount`) formulas are strictly increasing in `lockedAmount` for any fixed `amount`; this says nothing about which constant/parameter is subtracted, so it cannot distinguish buggy from intended on any scenario.
2. **Trivial range bound**: `returnExpression <= array[0].lockedAmount`. **Rejected — not discriminating.** True under both buggy (99 <= 100) and intended (50 <= 100) arithmetic whenever `amount >= 1` — a property of "you can't unlock more than what's locked," which the bug doesn't violate at all; says nothing about the actual defect.
3. **Inequality tied to the correct subtrahend**: `returnExpression <= array[0].lockedAmount - amount`. **Discriminates.** Buggy: `99 <= 50` → false (violated, correctly flags the bug). Intended: `50 <= 50` → true (holds with equality). Because the buggy code always subtracts the smaller constant `1` (whenever `amount > 1`), the buggy value is always `>=` the intended value, so this upper bound is violated exactly when the bug manifests. **Viable candidate.**
4. **Exact equality (SELECTED)**: `returnExpression == array[0].lockedAmount - amount`. Discriminates identically to (3) — same RHS, comparator differs. Per README's explicit caution (echoed in `10_web3bugs_59_H_04`'s R1-3), operator strength alone doesn't establish implementation-specificity, and since (3) and (4) share the exact same RHS, `==` buys no less independence from the patch than `>=` already has. What tips the choice to `==`: the report's own recommendation is not "don't over-retain the locked amount" (a bound) but a fully deterministic substitution — "should be `array[i].lockedAmount - amount`" — i.e. the intended value is a precise, uniquely-determined arithmetic quantity given `array[0].lockedAmount` and `amount`, not merely a ceiling the actual value must clear. Equality is the semantically accurate claim; there is no rounding-mode or multi-valued ambiguity being arbitrarily pinned (plain integer subtraction, no division).
5. **Known-bound/call rescue (Nokon-style, README R1-3)**: **not applicable.** `getLockedAmount` is `pure` and makes no function calls anywhere in its body (confirmed by reading the full function, L27–78) — no `alpha`-style blocker exists to rescue in the first place.
6. **Snapshot-qualified `varRef(Entry/Exit/...)` extension (README R1-3)**: **not needed.** `array`, `amount` are function parameters never reassigned anywhere in the function body (the loop only reads them); there is no before/after or entry/exit pairing of the *same* identifier in this relation (unlike `05_web3bugs_42_H_01`'s `debts == debts(Entry) + increasingDebt`). A plain, ordinary `@Post` equality over already-in-scope values suffices.

**Winner: Alternative 4** — `returnExpression == array[0].lockedAmount - amount`.

**Discrimination check (explicit arithmetic, per §9 checklist item 1)** — see R1-1's worked scenario: `array[0].lockedAmount = 100, amount = 50`. Buggy: `99`. Intended: `50`. Relation false on buggy (`99 == 50` is false), true (equality) on intended (`50 == 50`). A second scenario confirms the relation doesn't wrongly flag the *untouched* `<= amount` regime: `array[0].lockedAmount = 30, amount = 50` → `30 > 50` is false → **both** buggy and (already-correct) code take the `else` branch, `newLockedAmount = 0` — this regime is outside the relation's stated scenario precondition (`lockedAmount > amount`, see R1-6) and is correctly not claimed to be covered by it (see the precondition note below), avoiding a false claim of generality.

**Required R1-3 sufficiency/negation check (§3/R1-3)**: does this relation's negation fail to catch some alternative implementation that retains the reported defect but produces it differently? The reported defect is entirely a "wrong subtrahend used at L66" defect, and the selected relation is an *exact* equality pinning the correct subtrahend directly — any implementation using a wrong subtrahend (this one, or any other wrong constant/formula) at this line, *for the instantiated array position (index 0)*, would violate it; any implementation using the right subtrahend satisfies it. **One genuine gap, not a depth gap but a breadth gap**: because the relation is instantiated on one concrete representative array position (index 0 — see R1-6), it says nothing about whether the *same* subtrahend bug is present or absent for a different staker at a different array index; an alternative (hypothetical) implementation that is correct at index 0 but still buggy at index 1 would escape this instantiated check. This is the collection-quantification gap the methodology requires flagging via **Quantified property instantiated: Yes** (below), not a claim that the relation's *depth* of coverage for the instance it does check is incomplete — see "Intent coverage" below, judged **Full** on that separate axis.

---

## R1-4 — During vs Post (and the mandatory delta-exception check)

*(Revised on a later methodological review — see "Revision note" after both candidates below. R1-4's original two-candidate analysis is kept in full, since both candidates were correctly characterized; what changed is which of them the case's verdict actually rests on.)*

**Two candidate scopes considered:**

**(a) During, attached directly at L66** — the textually most direct choice, mirroring the patch's own line: `@During newLockedAmount == array[i].lockedAmount - amount`, placed immediately after L66 (or replacing it as the checked value). This relation's *content* is simple and every value it needs (`array[i].lockedAmount`, `amount`) is referenceable — but its **only viable attachment point is L66, which is textually and structurally inside the `for` loop body** (`for (uint256 i = 0; i < array.length; i++) { if (...) { L66 } else {...} } `, L64–74). This is precisely the confirmed `delta` exception (README §4/R1-7): reading `Interpreter/Engine.py` directly (as documented already for `02_web3bugs_71_H_11`/`04_web3bugs_34_H_01`, and re-confirmed here rather than assumed by analogy) — `reinterpret_from()`'s worklist, on reaching a loop head, calls `fixpoint()` and only pushes the loop's designated exit node's successors back onto the outer worklist (`Interpreter/Engine.py` L1071–1087); `_process_during_annotations` (L1108) is only ever reached for nodes processed by that outer worklist, never for a node swept into `fixpoint()`'s internal loop-body processing (L409–644, specifically its own separate node-iteration loop at L476–598, which never calls any intent-checking entry point). A `@During` at L66 would therefore never be evaluated, under any circumstances. **Confirmed: alternative (a) hits `delta`.**

**(b) Post, attached at function exit, using `returnExpression`** — originally selected in this pass, **now also found to hit `delta` under README §4's expanded scope for the tag (added after this case was re-examined); see Revision note below.** `@Post returnExpression == array[0].lockedAmount - amount`. The actual `return` statement that produces this value (L72, `return newLockedAmount;`) is *itself* textually nested inside the same `for` loop (inside the `if (account == array[i].staker)` block, L71–73, which is inside the loop body, L64–74) — a materially different shape from `10_web3bugs_59_H_04`'s and `08_web3bugs_52_H_04`'s precedents, where the relevant `return` statement sits textually *after* the loop closes.

**Distinguishing this case from `71_H_11`, explicitly (kept for record — this distinction is still correct as far as it goes, it just turns out not to be sufficient on its own)**: `71_H_11`'s R1-4 explicitly considered and *rejected* a Post-based rescue, because the buggy value (`_redeemAmount`) was consumed as a call **argument** mid-loop and never itself became a return value — the only Post-adjacent candidate (`_actualDeduction`) was contaminated by a separate external contract's independent logic (`IndexTemplate.compensate()`'s insolvency fallback). **Here, by contrast, the buggy value *is*, verbatim, the function's own return value** in the matching-staker case (`return newLockedAmount;`, L72) — no external call, no separate consuming function, no arithmetic contamination. This remains true, and is exactly why the original pass judged Post viable. What it does not settle — see below — is whether the *CFG node* that carries out that return is itself inside the engine's suppressed loop-interior processing, independent of contamination.

---

**Revision note (methodological, not case-specific — added after direct engine-source verification prompted by user questioning of the original Post-rescue reasoning).**

Direct inspection of `Interpreter/Engine.py` (undertaken specifically to check whether `returnExpression` at σ_exit could be contaminated by this function's *other* `return` statements, L33/L77) established two facts that change how alternative (b) must be read:

1. **The `return` statement at L72 is itself a member of `loop_nodes`.** It is reached mid-iteration, before the loop's back-edge — its CFG node is swept into `fixpoint()`'s internal traversal (`transfer_function`, called from inside `fixpoint()`, `Engine.py` L267–277), never the outer worklist's per-node processing (`_run_worklist`, L795–955). Concretely: `transfer_function` calls `update_statement_with_variables` **without** passing the outer `ret_acc` (`return_values`) list — so `_interpret_return` (L203–221) only ever writes this return's value into the function's exit node via a **per-line side-channel**, `exit_node.return_vals[stmt.src_line] = r_val` (L218), which is read back later by `_extract_return_value` (L957–999). This value never passes through `_process_during_annotations` or the outer worklist's ordinary node handling at all — the same suppressed-processing regime `delta` was defined to describe, just reached via `@Post`'s aggregation machinery instead of `@During`'s per-node hook.
2. **This side-channel is not a designed, robust escape route — it is fragile, and its correctness for this specific case is incidental.** Tracing whether L77's (and L33's) `return 0;` could dilute the σ_exit value via `_extract_return_value`'s join-over-`return_vals` (L979–987) surfaced a genuine, separate engine gap (logged in `engine_code_changes.md`, Open issue "infeasible loop-exit produces an *empty* env, not a bottom-flagged one"): an infeasible loop-exit path produces a *literally empty* `{}` environment, which `_is_bottom_env` does **not** recognize as unreachable (it only iterates existing keys, so an empty dict returns `False`). In this specific function, L77 is correctly excluded from `return_vals` only because the *sibling* `isIncrease==true` branch (an ordinary `if`/`else` infeasibility, handled the normal way via `_set_bottom_env`) happens to supply a properly key-bearing bottom environment at the merge point before L77, and `Utils/Helper.py`'s `_merge_by_mode` treats the empty dict as an identity element that gets absorbed into that real bottom environment. Had this function lacked that sibling branch (e.g. a bare loop immediately followed by `return 0;`, with no `if`/`else` to supply a "real" bottom env at the join), the same mechanism would have let the unreachable `return 0;` execute and contaminate `returnExpression` with `0`. **The correctness of alternative (b) for this case is not a fact about the relation or the engine's architecture — it is a fact about this function's particular CFG shape happening to route around a confirmed representational gap.**

**Conclusion**: per README §4's revised delta scope (a case is delta-blocked when the reported defect's own value is only ever computed at a `loop_nodes` CFG node, with no escape that routes through the engine's ordinary per-node/per-statement checking machinery — not merely "is the `@During` keyword inside the loop"), alternative (b) **also hits delta**. The buggy value (`newLockedAmount`) is assigned at L66 (inside `loop_nodes`) and consumed at L72 (also inside `loop_nodes`) — it never reaches a CFG node the outer worklist processes normally. That the value happens to surface at σ_exit via the `return_vals` side-channel, and that this specific function's sibling-branch shape happens to keep that side-channel uncontaminated, does not change where the value is *actually computed and read* — which is the test the expanded delta definition asks. Compare `10_web3bugs_59_H_04`/`08_web3bugs_52_H_04`/`09_web3bugs_52_H_34`/`12_web3bugs_70_H_04`/`14_web3bugs_3_H_04`, all re-surveyed against this same question (see `README.md` §4's worked-example note and `case_progress.md`'s Open threads) and confirmed **unaffected**: in every one of those cases, the reported defect's own statement is a separate, post-loop (or entirely loop-external) statement — the loop's role there is producing an already-correct intermediate value, not the defect's own location.

---

## R1-5 — Relation form

**Exact equality**, via the grammar's dedicated return-value form: `commonClause -> returnExpression relOp intentValue` (`C_ret`, `paper/first_revision/main.tex` line 493), reached through `postClause -> commonClause`. Not forced to equality by the assignment-shaped patch (R1-5's explicit caution) — equality was selected in R1-3 on independent discrimination-vs-implementation-specificity grounds. Direct in-repo precedent for this exact construction: `@Post returnExpression == _balance - mapToken_tokenAmount[_token]` (`main.tex` line 1438, `Pools.getAddedAmount`), and `10_web3bugs_59_H_04`'s own `@Post returnExpression == total * 10000 / (count - initialIndex)`.

---

## R1-6 — Construct the target annotation

**Attachment point**: `@Post` on function `getLockedAmount()` (placed after the function's closing brace, evaluated against σ_exit — same convention as `10_web3bugs_59_H_04`/`08_web3bugs_52_H_04`). `array`, `amount` are function parameters, in scope throughout the entire function body including σ_exit (`varRef -> identifier subAccess*`, `Parser/Solidity.g4` L379–386, supports both `.identifier` member access and `[expression]` index access — confirmed this syntax is legal by direct grammar read, and has a direct precedent in `03_web3bugs_83_H_01`'s `poolInfo[1].accConcurPerShare`).

**Quantification note (README R1-6, required)**: the reported property — "unlocking works correctly for a staker in the array" — is naturally quantified over the array (any position where `array[i].staker == account`). The grammar has no quantifier (confirmed against `Parser/Solidity.g4`'s `varRef`/`arithFactor` productions — no `∀`/`∃` construct exists for an annotation to range over an array). The target annotation therefore **instantiates on one concrete representative element, index 0** (`array[0]`) — i.e., the scenario is constructed so the matching staker is the array's first entry. This is stated explicitly per R1-6's requirement; see R1-7 for how this narrows the Expressible claim.

**Target annotation:**
```solidity
function getLockedAmount(
    LockedInfo[] memory array,
    address account,
    uint256 amount,
    bool isIncrease
) public pure override returns (uint256) {
    if (array.length == 0) return 0;

    uint256 newLockedAmount;
    if (isIncrease) {
        ...
    } else {
        for (uint256 i = 0; i < array.length; i++) {
            if (array[i].lockedAmount > amount) {
                newLockedAmount = array[i].lockedAmount - 1;
            } else {
                newLockedAmount = 0;
            }

            if (account == array[i].staker) {
                return newLockedAmount;
            }
        }
    }

    return 0;
}
// @Post returnExpression == array[0].lockedAmount - amount
```

No concrete numeric constant needed beyond `array[0].lockedAmount` and `amount` themselves — the annotation introduces no new externally-derived number (unlike, e.g., `02_web3bugs_71_H_11`'s `1e12` scaling constant).

**Preconditions, stated explicitly (R1-7's "scenario-conditioned, not unconditional invariant" requirement)**:
1. `isIncrease == false` (the annotation only concerns the unlock branch; the `isIncrease == true` branch, L37–62, is untouched and unrelated — see M-01 above).
2. `array[0].staker == account` (index 0 is the instantiated representative matching element — R1-6's quantification note).
3. `array[0].lockedAmount > amount` (the branch the bug is actually in; the sibling `<= amount` branch, L68, returns `0` correctly in both buggy and patched code and is not covered by this relation).
4. `amount ≠ 1` (the boundary case flagged in R1-1 — at `amount == 1` the buggy and intended formulas coincide, so the relation, while still technically true, would not have exercised any discriminating power for that specific input; this is a scenario-construction caveat, not a defect in the relation's form, matching `02_web3bugs_71_H_11`'s ceiling-collapse precedent).

---

## R1-7 — Expressibility decision

*(Revised — see R1-4's Revision note. The original pass's reasoning below is kept for record, marked superseded, followed by the current verdict.)*

**Superseded reasoning (original pass, Post-scope alternative (b) treated as the selected relation):**
- Values referenceable at a legal program point: Yes. `array[0].lockedAmount`, `amount` are directly referenceable via ordinary `varRef` + `subAccess` (`Parser/Solidity.g4` L379–386) at σ_exit; `returnExpression` is the grammar's `C_ret` reference to the function's actual return value.
- Arithmetic/logical relation representable: Yes. `array[0].lockedAmount - amount` is an ordinary `arithAdd` (subtraction), directly supported by the grammar.
- Observation point supported: originally judged Yes, on the reasoning that the confirmed delta exception was scoped narrowly to `@During` inside a loop body and did not extend to `@Post` at σ_exit "regardless of whether the specific statement that produces the exit-time value is textually inside a loop." **This premise is exactly what the Revision note in R1-4 corrects**: the relevant question is not the annotation keyword or the textual/σ_exit framing, but whether the value's own defining/consuming CFG nodes are ever visited by the engine's ordinary per-node checking machinery — and here they are not.

**Current verdict**: **Observation point supported: No.** Both viable candidates — During at L66 (alternative (a)) and Post reading `returnExpression` sourced from the L72 return (alternative (b)) — depend on CFG nodes that are members of `loop_nodes`, processed only by `fixpoint()`'s internal, suppressed traversal, never by the outer worklist's per-node intent-checking machinery. Alternative (b)'s apparent σ_exit availability is a side-channel artifact (`exit_node.return_vals`, written directly by `_interpret_return` independent of `_process_post_annotations`), not evidence that the observation point is architecturally supported — see R1-4's Revision note for the full trace, including why this side-channel's correctness for *this* function is incidental (rests on a sibling-branch coincidence, not a designed guarantee) rather than something R1-7 should treat as "supported."

**Quantification caveat (per R1-6/R1-7's required note, kept for record)**: had this case been Expressible, the verdict would have been scoped to the concrete instantiation on `array[0]` (R1-6) — moot given the Inexpressible outcome below, but kept for continuity with the rest of this batch's convention.

**Outcome: Expressible = NO — delta.** The reported defect's own value (`newLockedAmount`, assigned at L66) is only ever computed and consumed at CFG nodes inside the `for` loop body (`loop_nodes`) — L66 (the assignment) and L72 (the consuming `return`) are both members. Per README §4's expanded delta scope (added after this case prompted the clarification — see README §4's worked-example note, which uses this exact case), this blocks not only the directly patch-mirroring `@During` at L66 but also the `@Post`-on-`returnExpression` alternative that was originally selected: the value never passes through the engine's ordinary per-node/per-statement checking machinery at any point, regardless of which annotation keyword or program point is used to try to read it.

---

## §5 — Value/Algorithm and Usable/Unusable

- **Value-level** *(unchanged)*: per the paper's own definition (`main.tex` L239–240 — Value-level = "a wrong operator, a swapped identifier, or truncation that produces a numerically incorrect result"; Algorithm-level = "operation ordering, an absent state update, or a missing procedure call"), the reported defect is exactly a **wrong-operand** case: L66 subtracts the literal constant `1` where it should subtract the in-scope parameter `amount`. This classification does not depend on the Expressible verdict — §5 characterizes the *reported defect itself*, not the relation's representability, and nothing about the delta reclassification changes what kind of defect this is.
- **Usable** *(unchanged despite the Inexpressible verdict — see README §4's explicit note: "a delta case can legitimately still be Usable... don't default to Unusable out of habit," and the established `71_H_11` precedent, which is Usable/delta for the identical reason)*: every value the relation needs — `array[i].lockedAmount`/`array[0].lockedAmount`, `amount`, `newLockedAmount` — is referenceable in the grammar at some legal program point (L66 itself, or σ_exit via the side-channel). The blocker is not that any value is unrepresentable or unreferenceable; it's specifically that the *program point* where the relation would need to be checked (or the CFG path the value's computation is confined to) is never visited by the engine's per-node/per-statement intent-checking machinery. This is a textbook Usable/delta case, matching `71_H_11`'s own §5 call exactly.

---

## RQ2-A — Specification Requirements profile

**Not applicable.** Per README §6, RQ2-A applies only to Expressible cases. This case is Expressible: No (delta, revised pass). No structural profile is recorded here. (A profile was computed in the original pass, when this case was classified Expressible=Yes via the Post-scope rescue — 5 relevant statements, 7 unique relevant program values, 0 additional functions, context breadth 1, external specification required: No — superseded, not reproduced as an active part of the record; see git history / the original pass if needed for reference.)

---

## §7 — Alternatives-considered summary

| # | Relation | Tier | Expressible? | Discriminates? | Verdict |
|---|----------|------|---------------|-----------------|---------|
| 1 | Monotonicity of `returnExpression` in `array[0].lockedAmount` | Directional | Yes | No | Rejected — holds identically under buggy and intended arithmetic |
| 2 | `returnExpression <= array[0].lockedAmount` | Trivial bound | Yes | No | Rejected — holds under both, says nothing about the subtrahend |
| 3 | `returnExpression <= array[0].lockedAmount - amount` | Inequality, correct subtrahend | Yes (content) | Yes | Not selected; same observation-point blocker as (4) below would apply if pursued |
| 4 | `returnExpression == array[0].lockedAmount - amount` | Exact equality | Yes (content) | Yes | Content viable, but see (b) below — the only observation points available for this content are delta-blocked |
| — | Known-bound/call rescue (alpha-style) | — | N/A | — | Not applicable — `getLockedAmount` is `pure`, makes no calls |
| — | Snapshot-qualified `varRef(Entry/...)` extension | — | N/A | — | Not needed — `array`/`amount` never reassigned, no before/after pairing required |
| (a) | `@During newLockedAmount == array[i].lockedAmount - amount` at L66 | During, direct/patch-mirroring | **No — delta** | Would, if evaluated | Rejected — only viable attachment is inside the `for` loop body; confirmed never evaluated by `fixpoint()`/`reinterpret_from()` |
| (b) | `@Post returnExpression == array[0].lockedAmount - amount` | Post, return-value | **No — delta** *(revised — originally Yes; see R1-4 Revision note)* | Would, if evaluated | Rejected on further review — the consuming `return` (L72) is itself a `loop_nodes` member; the value only reaches σ_exit via a side-channel that never routes through the engine's per-node checking machinery, and whose correctness here is a CFG-shape coincidence, not an architectural guarantee |

## RQ1-B / RQ2-B

Not applicable — this case is Inexpressible; RQ1-B/RQ2-B apply only to Expressible cases (README §8).

---

## Summary

**Revised — see R1-4's Revision note and README §4's expanded delta scope for the full reasoning; supersedes the original pass's Expressible=Yes verdict.**

- **Expressible: No — delta.** Both candidate observation points for the reported defect — `@During` at L66 (the buggy assignment itself) and `@Post` reading `returnExpression` (sourced from the L72 `return`, which is nested inside the same loop) — depend on CFG nodes inside `loop_nodes`, which this engine's `fixpoint()`-internal traversal processes without ever calling the per-node intent-checking machinery (`_process_during_annotations`/the ordinary `_process_post_annotations` node path). The apparent Post-scope rescue in the original pass relied on a `return_vals` side-channel (`_interpret_return` writing directly onto the function's exit node) that bypasses this machinery entirely, and whose non-contamination for this specific function is a coincidence of its CFG shape (a sibling `if`/`else` branch happening to supply a properly bottom-flagged environment at the merge point before the function's other `return 0;` statements) rather than a general, reliable escape route — see the newly-logged engine gap in `engine_code_changes.md` (infeasible loop-exit producing an empty, not bottom-flagged, environment).
- **Delta scope note**: this case is the motivating example for README §4's expanded delta definition (added this session) — a case is delta-blocked when the reported defect's own value is only ever computed/consumed at `loop_nodes` CFG nodes, regardless of which annotation keyword or apparent program point (including σ_exit) is used to try to read it. Distinguished explicitly from `10_web3bugs_59_H_04`/`08_web3bugs_52_H_04`/`09_web3bugs_52_H_34`/`12_web3bugs_70_H_04`/`14_web3bugs_3_H_04` — all re-surveyed against this same question and confirmed unaffected, since each of those cases' reported defect is a separate, post-loop (or entirely loop-external) statement, not a value confined to `loop_nodes`.
- **Value-level/Algorithm-level**: **Value-level** (unchanged — §5 characterizes the defect itself, not the relation's representability). A single wrong-operand substitution (`1` instead of `amount`).
- **Usable/Unusable**: **Usable** (unchanged in substance, now the operative field given Expressible=No — see README §4's explicit note that delta cases can remain Usable, and the `71_H_11` precedent). Every value the relation needs is referenceable in the grammar; the blocker is observation-point support, not value-referenceability.
- **Quantified property instantiated**: not applicable — an Expressible-case field (README §10); this case does not reach it.
- **Tag**: **delta.**
- **RQ2-A profile**: not applicable (Expressible-case field only) — see RQ2-A section above for the superseded original-pass numbers, kept for reference only.
- **RQ1-B/RQ2-B**: not applicable — Expressible-case fields only.
