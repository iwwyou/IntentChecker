# web3bugs_83_H_01 — R1-1 → R1-7 + RQ2-A (Agent A / Analyst pass)

**Case ID**: `web3bugs_83_H_01`
**Contract**: `MasterChef`
**Function**: `add` (line 86; bug statement at line 89: `totalAllocPoint = totalAllocPoint.add(_allocationPoints);`)
**Prior (superseded) label**: old taxonomy `L5a` (`evaluation/RQ2/l4_l5_classification.py`, `l4_l5_case_review.md` Case 26). That label and its annotation are historical background only, per README §12 — this pass re-derives everything from R1-1 fresh. One part of it (the `poolInfo[0]`-based annotation it recorded as "weak") turns out to be non-discriminating on closer inspection — see R1-3 alternative (1) below. That is flagged as a finding, not assumed.

Source read verbatim from `evaluation/RQ1/target_contracts_original/web3bugs_83_H_01.sol` (confirmed byte-identical to `Dataset/Web3Bugs/S3_1/contest_83_H_01/MasterChef.sol` via diff). **Correction (second refinement pass)**: the original pass read `Dataset/Web3Bugs/S3_1/contest_83_H_01/README.md` and found only a bug description, concluding no patch/recommendation existed. That local copy was **truncated** (same class of problem found in `web3bugs_71_H_11`) — it's since been corrected against the authoritative source, `C:\Users\isjeon\Web3Bugs\reports\83.md` (see README §0.5), which contains the full report including a Proof of Concept and a Recommendation section: *"Update all existing pools before adding new pool. Use the massUpdate() function which is already present ... but unused."* This is used as corroborating evidence in R1-1 below, not transcribed into the annotation.

---

## R1-1 — Reported Behavior Reconstruction

**Contract role**: `MasterChef` is a yield-farming reward distributor. It manages a list of staking pools (`poolInfo[]`), tracks per-user stake and reward debt (`userInfo`), and emits a fixed per-block amount of `concur` tokens (`concurPerBlock`) split across pools in proportion to each pool's `allocPoint` relative to the global `totalAllocPoint`.

**Function role**: `add(address _token, uint _allocationPoints, uint16 _depositFee, uint _startBlock)` is an owner-only administrative function that registers a new pool and assigns it `_allocationPoints`, which become part of the denominator (`totalAllocPoint`) used by every pool's reward-rate formula.

**Relevant variable semantic roles** (only the ones the bug touches):
- `totalAllocPoint` (state, uint): global denominator in `concurReward = multiplier * concurPerBlock * pool.allocPoint / totalAllocPoint` (`updatePool`, line 151; `pendingConcur`, line 120). Any change to it retroactively changes the effective reward rate applied to *every* pool for whatever elapsed-block interval hasn't yet been synced into `accConcurPerShare`.
- `poolInfo[i].accConcurPerShare` (state, uint, per pool): accumulated reward-per-share; monotonically non-decreasing (only ever `.add()`-ed to, in `updatePool` line 152); the value that ultimately determines `pendingConcur`/user payouts (lines 123, 163, 190).
- `poolInfo[i].lastRewardBlock` (state, uint, per pool): last block at which pool `i`'s `accConcurPerShare` was brought up to date; gates whether `updatePool(i)` does any further work (line 137).

**Statement-level behavior** (two sub-questions kept distinct):
- **Variable-value intent** at line 89 (`totalAllocPoint = totalAllocPoint.add(_allocationPoints)`): the new value of `totalAllocPoint` should correctly equal old value + `_allocationPoints`. This arithmetic itself is *not* buggy.
- **Statement/line-level intent**: before `totalAllocPoint` is changed (before the denominator used by *every* pool's reward formula shifts), every existing pool's reward-accrual state must already be synchronized up through the current block *under the old `totalAllocPoint`*, so reward earned during already-elapsed blocks is priced at the weighting that was actually in effect then. `add()` contains no statement upholding this — it never touches any existing `poolInfo[i]` before or after reassigning `totalAllocPoint`.

**Reported erroneous behavior** (audit report, lines 13–21): "All other, already added, pools should be updated but currently they are not. Instead, only totalPoints is updated. Therefore, old (and not updated) pools will lose it's share during the next update. Therefore, user rewards are not computed correctly (will be always smaller)."

**Expected/intended behavior**: when `add()` registers a new pool and increases `totalAllocPoint`, existing pools' reward-accrual state (`accConcurPerShare`, via `lastRewardBlock`) must be synchronized first — i.e., `add()` must behave, with respect to existing pools, the way `deposit()` and `withdraw()` already do: both call `updatePool(_pid)` (lines 160, 188) *before* touching state that depends on the reward rate. `add()` is the outlier that skips this. This "sync before mutating rate-affecting state" pattern is independently visible elsewhere in this same contract, which is the basis for reconstructing intended behavior here.

**Patch intent** *(revised in the second refinement pass, now that the report's real Recommendation section is available — see metadata above)*: the report explicitly recommends updating all existing pools before adding the new pool, and names `massUpdatePools()` as the mechanism ("Use the massUpdate() function which is already present ... but unused"). This is used to corroborate the intended synchronization behavior — existing pools' reward-accrual state must be brought up to date before `totalAllocPoint` changes — not as a guarantee that the suggested implementation is itself correct in all edge cases. It is not, in fact: `massUpdatePools()` loops over every pool including pool 0, and pool 0's `updatePool(0)` reverts once `block.number > _startBlock` (see R1-3, candidate (2), independently confirmed during Agent B review before the real report was known) — so the report's own literally-named fix would make `add()` permanently unusable shortly after deployment. A real working fix would need to skip pool 0 or guard against it; the report doesn't note this. This distinction — using the recommendation as evidence for *what should happen*, while not assuming its *literal mechanism* is bug-free — is exactly the discipline README §2/§3 calls for, and this case is a clean illustration of it: the report's own suggested implementation has a real edge-case bug, discovered independently of and before the report's existence was even confirmed.

---

## R1-2 — Intent Abstraction

Dropping any patch-syntax framing: the numeric property distinguishing buggy from intended behavior is **whether an existing pool's reward-accrual state (`accConcurPerShare`) gets synchronized as a result of calling `add()`**, given that pool has pending, not-yet-synced rewards at that moment.

- Buggy: calling `add()` never changes any existing `poolInfo[i].accConcurPerShare` — invariantly unchanged across the call, for every `i` that existed before it, regardless of preconditions.
- Intended: calling `add()`, for an existing pool `i` with unsynced elapsed blocks and nonzero stake, must change (increase) `poolInfo[i].accConcurPerShare`.

**Orientation**: Effect/state-transition-centered — the relevant property is the effect executing `add()` has on an existing pool's accounting state, not a fixed bound on a single value.

**Intent-coverage narrowing (added in a later pass, per README §3/§4's `Intent coverage` field)**: this R1-2 abstraction, as stated ("must change (increase)"), already drops part of R1-1's reconstructed intent. R1-1 explicitly stated the sync must happen *using the old `totalAllocPoint`*, "so reward earned during already-elapsed blocks is priced at the weighting that was actually in effect then" — a claim about which rate is used, not merely whether some accrual happens. The R1-3-selected relation (below) only ever checks the latter (see the `Intent coverage` discussion at R1-7). Recorded here rather than left implicit, per README's required-check rule.

**Quantification note (added in second refinement pass)**: the reported/intended property above is naturally quantified over *every* existing pool with pending rewards ("for all `i`..."). The grammar has no construct for universal quantification over a collection (`poolInfo[]`) — confirmed against `paper/first_revision/main.tex`: every `∀`/`∃` in the grammar's semantics is internal to the analysis engine's own path-quantification for `changed`/entry-exit evaluation *within one execution*, not something an annotation can write over an array. So the target annotation necessarily instantiates the property on one concrete representative pool (`poolInfo[1]`, chosen because it has pending rewards in the constructed scenario — see R1-6), not the fully general "all pools" claim. This is stated explicitly here rather than left implicit, per README §4's quantification note: **Expressibility here means "expressible under concrete instantiation," not "expressible as the fully general, universally-quantified property the report actually describes."**

---

## R1-3 — Select the least implementation-specific sufficient relation

Candidates, weakest/least-patch-specific to strongest, each with an explicit discrimination check (R1-3 condition (c); README §7):

**(1) `changed(poolInfo[0].accConcurPerShare, true)` / `poolInfo[0].accConcurPerShare (entry != exit)` — REJECTED, fails to discriminate.**
This is essentially the old (superseded) taxonomy's recorded "weak" annotation (`l4_l5_classification.py`: `// @Post changed(poolInfo[0].accConcurPerShare, true)`). `poolInfo[0]` is the placeholder pool pushed in the constructor with `allocPoint: 0` (line 66); nothing ever modifies an existing pool's `allocPoint` after construction. In `updatePool`, the guard `if (lpSupply == 0 || pool.allocPoint == 0) { pool.lastRewardBlock = block.number; return; }` (line 141) means pool 0, *whenever this guard is actually reached without reverting* (see (2) below), takes the early-return branch and *never* has `accConcurPerShare` touched — permanently 0, in both the buggy code and any hypothetical patched code. Entry==exit==0 unconditionally in both worlds — cannot reject buggy since intended doesn't satisfy it either. This is a real, checkable defect in the old annotation, recorded per README §7/§12.

**(2) `poolInfo[0].lastRewardBlock (entry < exit)` — REJECTED (corrected during Agent B review — see `review.md`; originally mislabeled "viable, not selected").**
`poolInfo[0].depositToken` is `IERC20(address(0))` (constructor, line 65). Reaching line 141/142 at all requires first executing line 140, `pool.depositToken.balanceOf(address(this))` — a high-level call through a typed interface. Under Solidity `^0.8.11` (this contract's pragma), such a call **automatically reverts** when the target address has no code (`extcodesize == 0`), which is exactly `address(0)`. So: whenever `block.number > poolInfo[0].lastRewardBlock` (the only case where line 140 would even execute), `updatePool(0)` reverts the entire transaction before line 142 is ever reached. The only window where line 140 isn't reached is when guard 137 (`block.number <= pool.lastRewardBlock`) is true — but then nothing changes either, since `lastRewardBlock` is already at its constructor value. **`poolInfo[0].lastRewardBlock` can therefore never be successfully advanced past `_startBlock` in any transaction that completes without reverting** — this candidate is exactly as non-discriminating as (1), just via a different mechanism (revert rather than silent no-op), not a legitimate "not selected for style reasons" alternative.

**(3) `poolInfo[1].accConcurPerShare (entry <= exit)` — REJECTED, too weak.**
Buggy behavior always produces `entry == exit` exactly (pool 1 untouched), which trivially satisfies `<=`. A non-strict bound is *satisfied by the buggy case too* — useless as a discriminator. Exactly the failure mode R1-3 warns against.

**(4) Exact-equality full reward-accrual formula — REJECTED, over-specific and doesn't fit the grammar's P_ee form cleanly.**
E.g. exit `accConcurPerShare` == entry `accConcurPerShare` + (block.number − entry `lastRewardBlock`) × `concurPerBlock` × entry `allocPoint` / entry `totalAllocPoint` × `_concurShareMultiplier` / lpSupply. Two problems: (a) strictly more specific than needed — relation (6) already fully discriminates, so reproducing the exact formula adds implementation detail without adding discriminating power; (b) doesn't fit `postClause -> intentValue (entry relOp exit)` (P_ee), which evaluates *one* `intentValue` twice (against σ_entry, then σ_exit) and compares with one `relOp` — it cannot mix an entry-only evaluation of one subterm (old `totalAllocPoint`) with an exit-only evaluation of another (new `accConcurPerShare`) in one composite formula. `commonClause`'s `intentValue relOp intentValue` (C_cmp) doesn't rescue this either, since @Post's field supply gives σ_entry/σ_exit as whole-environment snapshots, not a way to pin individual subterms to different snapshots within one comparison.

**(5) Relation solely on `totalAllocPoint` — dismissed immediately, not a real candidate.**
`totalAllocPoint = totalAllocPoint.add(_allocationPoints)` (line 89) executes identically, same arithmetic, in buggy and patched code — not where the defect lives.

**(6) SELECTED — `poolInfo[1].accConcurPerShare (entry < exit)`, Post scope, attached to `add`.**
Directional/state-change relation (strict inequality: since `accConcurPerShare` is only ever `.add()`-ed to, "changed" and "strictly increased" coincide here, so strict inequality is the natural, cost-free strengthening of "changed"). Selected over (1)–(4) because it is the least implementation-specific relation that (a) is supported by the reported intended behavior, (b) is expressible from purely in-scope observables, and (c) actually discriminates buggy from intended, verified with concrete numbers in R1-6. It targets `accConcurPerShare` — the value the report's harm is directly about — on an active pool (index 1), avoiding pitfall (1).

---

## R1-4 — Choose annotation observation scope (During vs Post)

**Post.** The relation concerns a persistent state transition across the whole `add()` call — entry vs exit values of `poolInfo[1].accConcurPerShare` — not an intermediate expression or a single statement's before/after. Driven by the relation's nature (a function-level "was the existing pool synced as a side effect of this call" property), not by where a patch's literal fix would be inserted. Per R1-4's explicit warning, the missing call would in fact belong early in the function body, but that is not the deciding factor — what decides it is that the effect being checked is a whole-function before/after comparison on state outside the (missing) statement itself.

---

## R1-5 — Choose relation form

**Entry-Exit relation with a strict lower-bound inequality operator** (`P_ee`: `intentValue (entry relOp exit)`, `relOp = <`). Classification per the R1-5 list: primarily "Entry-Exit," secondarily a strict inequality/lower bound on exit relative to entry. Not equality (see R1-3(4)). Not merely `changed(...)` — the strict-inequality reading is at least as precise for no extra cost, using the same grammar rule. Since there is no literal patch text available here at all, there is no risk of mechanically inferring relation form from patch syntax; the form follows purely from R1-2/R1-3's reasoning.

---

## R1-6 — Construct the target annotation

**Target annotation**:
```
// @Post poolInfo[1].accConcurPerShare (entry < exit)
```
**Attachment point**: function `add` (evaluated against σ_entry/σ_exit of the call under test).

No numeric literal/constant appears in the relation, so R1-6's constant-derivation documentation requirement doesn't apply — but a concrete scenario is constructed for the discrimination check:

- Deploy with `startBlock = 100`, `endBlock = 1_000_000`. Defaults: `concurPerBlock = 100000 gwei = 1e14`, `_concurShareMultiplier = 1e18`. `totalAllocPoint` starts 0; constructor pushes placeholder `poolInfo[0]` (`allocPoint: 0`).
- At block 100, owner calls `add(tokenA, 100, 0, 100)` (setup call, not under test): `lastRewardBlock = max(100,100) = 100`; pushes `poolInfo[1] = {tokenA, allocPoint:100, lastRewardBlock:100, accConcurPerShare:0, depositFeeBP:0}`; `totalAllocPoint` becomes 100; `pid[tokenA]=1`.
- Assume (external precondition, not part of the annotated relation) that by block 200 `tokenA.balanceOf(MasterChef) = 500e18`, i.e. `lpSupply = 500e18` when `updatePool(1)` is evaluated.
- At block 200 (100 blocks elapsed since pool 1's `lastRewardBlock=100`), owner calls `add(tokenB, 50, 0, 200)` — **the call under test.**
  - **Buggy**: only `totalAllocPoint = totalAllocPoint.add(50) = 150` runs (line 89); `poolInfo[1]` never referenced. Entry=0, exit=0. `0 < 0` ⇒ **false** ⇒ Violated. Correct flag.
  - **Intended** (hypothetical `massUpdatePools()`/`updatePool(1)` before the reassignment): runs while `totalAllocPoint` is still 100 (old): `200 > 100` ✓; `lpSupply(500e18)≠0`, `allocPoint(100)≠0` ✓ (skips early return); `200 < endBlock` ✓. `multiplier = getMultiplier(100,200) = 100`. `concurReward = 100 * 1e14 * 100 / 100 = 1e16`. `accConcurPerShare = 0 + (1e16*1e18)/500e18 = 1e16/500 = 2e13`. Entry=0, exit=2e13. `0 < 2e13` ⇒ **true** ⇒ Satisfied. Correct acceptance.

**Note on `lpSupply`**: comes from `pool.depositToken.balanceOf(address(this))`, an external call, but it does **not** appear inside the annotated `intentValue` — doesn't affect R1-7. Relevant only to how a real engine run (RQ1-B, deferred) would supply that external value (e.g., `@IReturn`), noted for RQ2-A completeness, not decided here.

---

## R1-7 — Expressibility decision

**Expressible: Yes.**

- Required value referenceable at a legal program point? Yes — `poolInfo[1].accConcurPerShare` is public state (`varRef -> identifier subAccess*`, `subAccess -> [expr] | .identifier`), in scope at both entry and exit of `add`.
- Can the arithmetic/logical relation be represented? Yes — direct instance of grammar's `postClause -> intentValue (entry relOp exit)` (P_ee).
- Is the required observation point supported? Yes — @Post's context supplies σ_entry and σ_exit, exactly what P_ee needs.

No function call inside `intentValue` (no alpha concern), value not missing from scope (no beta concern), single P_ee comparison rather than a multi-statement/structural relation (no gamma concern).

**Intent coverage: Partial (added in a later pass — see README §3/§4/§10's `Intent coverage` field).** The required check: does this relation's negation fail to catch at least one alternative implementation that still retains the reported defect but produces it differently? **Yes, it does fail to catch one.** Consider an implementation that calls `updatePool(1)` — but only *after* `totalAllocPoint` has already been mutated to 150 (i.e., right ordering of "call the sync function" but wrong placement relative to the mutation). Using the same R1-6 scenario numbers: `accConcurPerShare` would compute to `1.333e13` (using the wrong, already-increased `totalAllocPoint=150` as the denominator) rather than the correct `2e13` — still strictly less than the fully-correct value, i.e. still exhibiting the exact "always smaller"/underpayment defect the report describes (concretely worked out via the report's own PoC numbers: this is the same mechanism that makes Bob receive `X/2` instead of `X` in the audit's Scenario 1). Yet `entry < exit` (`0 < 1.333e13`) still evaluates **true** — Satisfied. So the selected relation verifies *that* `poolInfo[1].accConcurPerShare` changed, but not *that it changed using the pre-mutation `totalAllocPoint`* — the specific mechanism R1-1 identifies as what "intended" actually requires. This is a genuine grammar limitation, not an R1-3 oversight: R1-3 candidate (4) already established that `P_ee` cannot mix an entry-time evaluation of one subterm (`totalAllocPoint`) with an exit-time evaluation of a different subterm (`accConcurPerShare`) in one relation — there is no stronger relation in this grammar, attached anywhere in `add()`, that would close this gap (the statement that would need to exist for a `@During` check doesn't exist in the buggy code being annotated at all). **Expressible: Yes stands** (per R1-7's scope note) — this relation is still the least-implementation-specific one that discriminates the actual buggy code from the constructed intended scenario, satisfying R1-3's sufficiency condition as written — but it is a *necessary*, not *sufficient*, formalization of R1-1's full reported intent.

**Scenario-conditioning note (added in second refinement pass)**: `poolInfo[1].accConcurPerShare (entry < exit)` is not an unconditional function-level invariant — it only holds given the preconditions established in R1-6's scenario (pool 1 has `lpSupply != 0`, `allocPoint != 0`, elapsed blocks since its `lastRewardBlock`, and `block.number < endBlock`). Under different preconditions (e.g. no elapsed blocks, or `lpSupply == 0`), a correctly-implemented `add()` would *also* produce `entry == exit` for that pool, since there'd be nothing to accrue. The precise claim is: **under a scenario where the existing pool has pending rewards to accrue, `accConcurPerShare` must increase across `add()`** — which is exactly what the debug/batch-annotation scenario instantiation this tool already uses is for (RQ1-B, deferred), not a gap in this record.

---

## §5 — Value/Algorithm and Usable/Unusable

- **Algorithm-level**: the defect is a missing procedural step (the synchronization call that should precede the `totalAllocPoint` mutation), not an incorrect value/formula within an otherwise-correct step — consistent with the old classification's `bug_category="algorithm"`.
- **Usable**: `poolInfo[1].accConcurPerShare` (and alternative `poolInfo[0].lastRewardBlock`) are directly referenceable in-scope state; no external/inaccessible proxy needed.

---

## Required transparency field (README §7) — alternatives summary

| # | Relation | Verdict | Why |
|---|---|---|---|
| 1 | `changed(poolInfo[0].accConcurPerShare, true)` (≈ old taxonomy's "weak" annotation) | Rejected | Pool 0's `allocPoint=0` forever ⇒ `accConcurPerShare` invariantly 0 in both buggy and intended code; no discrimination. |
| 2 | `poolInfo[0].lastRewardBlock (entry < exit)` | Rejected (corrected — see `review.md`) | `updatePool(0)` reverts once `block.number > _startBlock` (calling `balanceOf` on `address(0)`), so `lastRewardBlock` can never actually advance in any completing transaction — non-discriminating for the same underlying reason as (1), not a legitimate style-based rejection. |
| 3 | `poolInfo[1].accConcurPerShare (entry <= exit)` | Rejected | Non-strict bound trivially satisfied by buggy case; loses discriminating power. |
| 4 | Exact-equality full reward-accrual formula | Rejected | More implementation-specific than needed; also doesn't cleanly fit the P_ee grammar form. |
| 5 | Relation solely on `totalAllocPoint` | Not a real candidate | Computed identically in buggy and intended code. |
| 6 | `poolInfo[1].accConcurPerShare (entry < exit)` on `add` | **Selected** | Least implementation-specific relation that still discriminates (verified with concrete arithmetic), closest to reported harm. |

---

## RQ2-A — Specification Requirements profile

(Applies: R1-7 = Expressible.)

*(Recounted a third time, applying README §6's simplified rules. This case is the worked example for those rules' "no missing-call exception" clause: the entire discrimination argument lives inside `updatePool`/`getMultiplier`, which `add()` never calls — that's the bug. Applying the atomic-function rule collapses "Relevant statements"/"Unique relevant program values" sharply (7→1, 9→3) relative to the second-refinement-pass numbers below this note's predecessor used. Per README §6, this is not a loss of information — it means this case's dependency sits almost entirely on the cross-function axis of the profile (`Additional functions required`) rather than the local-statement axis, which the mandatory semantic-dependency notes below now carry explicitly instead of a recursive line count.)*

- **Relevant statements (1, in `add()` itself)**: line 89 (`totalAllocPoint = totalAllocPoint.add(_allocationPoints)`) — bug-site context, needed to know the attachment point and what's buggy. Not operand-defining for the relation's own value (`poolInfo[1].accConcurPerShare` is never touched anywhere in `add()`'s body — that omission *is* the bug), kept as context for the same reason a target/disputed statement is always kept as context in this methodology, even where (as here) it doesn't directly define the constrained value.

- **Unique relevant program values (3, in `add()`'s own scope)**: `poolInfo[1].accConcurPerShare` (the relation's target value — counted regardless of whether any statement in `add()` defines it, per README §6), `totalAllocPoint`, `_allocationPoints` (both from line 89, the one counted relevant statement). Values belonging to `updatePool`/`getMultiplier`'s own internals (`lpSupply`, `multiplier`, `concurReward`, the three guard conditions, `concurPerBlock`, `_concurShareMultiplier`, `block.number`, `endBlock`) are not enumerated here — their existence and role are covered by the "Additional functions required" entries below, per README §6's no-recursive-counting rule.

- **Additional functions required (2)**:
  - `updatePool()` (lines 135–154) — required because its behavior establishes when and how `poolInfo[i].accConcurPerShare` increases for an existing active pool: three early-return guards (137, 141, 145) determine whether it changes at all, and the accrual statements (150–152) determine by how much. This *is* the mechanism the selected relation's discrimination argument runs on (R1-6's scenario).
  - `getMultiplier()` (lines 108–110) — required because its behavior determines positive reward accrual over the elapsed block interval; R1-6's scenario needs this to confirm the intended side actually produces a positive increment (if it returned 0 regardless of elapsed blocks, `entry < exit` would never hold even under correct behavior).
  - (`massUpdatePools`, `deposit`, `withdraw`, and the pool-0/`address(0)`-revert investigation — see "Supporting evidence, not counted" below; excluded from this count.)

- **Supporting evidence, not counted** (informed R1-1's reconstruction or R1-3's alternative-rejection, but not load-bearing for the *selected* relation's own derivation — README §6 Step 1 / corollary):
  - `massUpdatePools()` (127–132) — the report names this as its recommended mechanism (R1-1), and it was read to check whether it would work correctly (finding the pool-0 revert issue, R1-3 candidate (2)) — but the *selected* relation's own construction/verification only needs `updatePool(1)`'s direct behavior.
  - `deposit()` line 160 / `withdraw()` line 188 (`updatePool(_pid);`) — sibling-function evidence for R1-1's reconstruction ("sync before mutating rate-affecting state" is this contract's own pattern), not needed to construct/verify the selected relation itself.
  - Pool 0 / `address(0)`-revert investigation (R1-3, candidates (1)–(2)) — necessary to *reject* those alternatives, not to construct or justify the *selected* one (README §6's corollary).

- **Additional protocol/application-specific contracts/libraries required**: None beyond the target contract. The one external call involved (`IERC20.balanceOf`, feeding `lpSupply`) only needs to be known to "return a token balance"; its implementation isn't inspected. `SafeMath`/`SafeCast` are used only as ordinary arithmetic-safety wrappers (generic, would be a Step-2 case note if load-bearing at all — not load-bearing here beyond ordinary typed arithmetic).

- **Context breadth (ordinal)**: **2** — other function(s) in the same contract (`updatePool`, `getMultiplier`). Not 3 — no other contract's own source had to be read.

- **External specification required**: **No** — every value/predicate the relation depends on is derivable from this one file (`totalAllocPoint`'s role as a shared reward-rate denominator, and that `add()` must sync existing pools before changing it, are both established by the source itself — the guards in `updatePool`, the sibling `deposit`/`withdraw` pattern, and the report's own recommendation). *(Reworded in this pass — the original rationale cited "generic familiarity with the reward-per-share accrual pattern common to MasterChef-family contracts," which risks inviting exactly the "isn't that external domain knowledge?" question this field exists to rule out. The correct grounds are simpler: everything needed is in this file, full stop.)*

---

## RQ1-B / RQ2-B

Deferred, per README §8. No predicted outcome recorded.

---

## Summary (README §10 record)

- Case: `web3bugs_83_H_01`, `MasterChef.add`, prior label `L5a` (superseded).
- Value/Algorithm: **Algorithm-level**.
- Target relation: `poolInfo[1].accConcurPerShare (entry < exit)`, Post scope, Entry-Exit inequality form, attached to `add`.
- Expressible: **Yes** — all referenced values are in-scope state, the relation is a direct instance of the grammar's P_ee production, Post/entry-exit is directly supported.
- Usable: **Usable**.
- **Quantified property instantiated: Yes** — the reported property is "every existing pool," instantiated on the concrete `poolInfo[1]` since the grammar has no quantifier over `poolInfo[]` (grammar has no universal quantification over `poolInfo[]`); relation is scenario-conditioned (pending rewards, nonzero `lpSupply`/`allocPoint`), not an unconditional invariant.
- **Intent coverage: Partial** *(added in a later pass, README §3/§4/§10)* — the selected relation verifies that `poolInfo[1].accConcurPerShare` changed, a *necessary* condition of the reported intent, but not that it changed using the pre-mutation `totalAllocPoint` — the specific mechanism R1-1 identifies as what "intended" requires. A still-buggy alternative (sync called after the mutation, using the wrong rate) also satisfies `entry < exit` (see R1-7 discussion above). This is a confirmed grammar limitation (`P_ee` cannot mix an entry-time value of one subterm with an exit-time value of another), not an R1-3 selection error — Expressible remains Yes per README's scope note, since R1-3's sufficiency condition only requires discriminating the actual buggy code from one constructed intended scenario, which this relation does.
- RQ2-A profile: context breadth 2, 1 relevant statement, 3 unique relevant program values, 2 additional functions required (`updatePool`, `getMultiplier`, each with a mandatory semantic-dependency note — see RQ2-A above), 0 additional protocol/application-specific contracts/libraries required, no external specification required. (`massUpdatePools`/`deposit`/`withdraw`/pool-0 investigation recorded as supporting evidence, excluded from the counted metrics.)
- **Note on this profile's shape**: the small "Relevant statements"/"Unique relevant program values" counts are not a measurement gap — this case's entire dependency sits on the cross-function axis of the profile (its bug *is* a missing call, so almost nothing relevant lives in the annotated function itself), not the local-statement axis. This is a useful illustration of why RQ2-A is reported as a multi-field profile rather than a single combined score: this case and `web3bugs_16_H_04` (dense local arithmetic context, few additional functions) would misleadingly rank as "harder"/"easier" than each other under any single number, when they in fact reflect two different distributions of the same underlying context requirement.

---

**Final short summary**: Expressible = **Yes**, Intent coverage = **Partial**. Target annotation: `// @Post poolInfo[1].accConcurPerShare (entry < exit)` attached to `MasterChef.add`. Notable finding for the reviewer: the old (superseded) taxonomy's recorded annotation for this case, `changed(poolInfo[0].accConcurPerShare, true)`, does not actually discriminate buggy from intended behavior — pool 0 is a permanently-inert placeholder (`allocPoint = 0` forever) — so this pass selected pool 1 instead and documented why, along with three other rejected/alternative relations, per README §7. Second notable finding (later pass): the selected relation verifies *that* the existing pool's reward state changed, not *that it changed using the pre-mutation `totalAllocPoint`* — a still-buggy "sync after the mutation" alternative also passes it (see the `Intent coverage` discussion above) — recorded transparently rather than left implicit in the bare Expressible=Yes verdict.
