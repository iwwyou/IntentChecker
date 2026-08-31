# web3bugs_65_H_01 — Agent A (Analyst) Case Analysis

Case ID: `web3bugs_65_H_01` | Contract: `Basket` (contest 65, DeFi Protocol) | Function: `handleFees(uint256 startSupply) private`
Existing label: H-01, "Wrong fee calculation after `totalSupply` was 0" (submitted by kenzo; sponsor `frank-beard` (Kuiper) confirmed; judge `0xleastwood` commented and kept the finding — this is the report's sole High-severity finding, contest 65).
Source: `evaluation/RQ1/target_contracts_original/web3bugs_65_H_01.sol`; Report: `C:\Users\isjeon\Web3Bugs\reports\65.md`, finding `[H-01]` (§0.5 primary/authoritative source).
**Cross-checked against the scattered `Dataset/Web3Bugs/S3_1/contest_65_H_01/README.md` per §0.5's mandatory caution: confirmed truncated.** The scattered file reproduces only the finding's title, byline, and the two-sentence opening summary (its own lines 1–14) — it is missing the entire `### Impact`, `### Proof of Concept`, `### Recommended Mitigation Steps` sections, and the sponsor-confirmation/judge-comment exchange, all present in the primary source (`Web3Bugs/reports/65.md` lines 86–141). This matches the exact truncation pattern §0.5 warns about (`71_H_11`/`83_H_01`); the primary source is used throughout below, and the missing PoC/Recommendation sections are load-bearing to R1-1's reconstruction (the recommended fix is exactly what anchors R1-3's target relation).
Reported bug lines (local numbering in `target_contracts_original/web3bugs_65_H_01.sol`): 136–137 (the `else if (startSupply == 0) { return; }` branch of `handleFees`).

---

## R1-1 — Reported Behavior Reconstruction

**Contract role**: `Basket` is an index-fund-style ERC20 wrapper token — depositors mint basket tokens by supplying a weighted set of underlying `tokens` (per `weights`/`ibRatio` accounting) and burn them to redeem the underlying. The contract charges a continuous "license fee" to the `publisher` (and a split to the factory owner) proportional to elapsed time and current `totalSupply`, funded by minting new basket tokens (diluting existing holders) rather than by transferring underlying out.

**Function role**: `handleFees(uint256 startSupply)` is a `private` helper invoked at the top of every state-mutating entry point that changes `totalSupply` — `mintTo` (L97), `burn` (L113), and `auctionBurn` (L123) — each of which snapshots `startSupply = totalSupply()` *before* its own mint/burn effect and passes that snapshot in. `handleFees`'s job is twofold: (1) mint the publisher/owner their accrued time-based fee since the last time `handleFees` ran, and (2) advance the bookkeeping timestamp `lastFee` to `block.timestamp` so the *next* call only charges for the time elapsed since *this* call. It is a three-way branch on `lastFee`/`startSupply`:

```solidity
function handleFees(uint256 startSupply) private {
    if (lastFee == 0) {
        lastFee = block.timestamp;                              // L134-135: first-ever call, no fee owed yet
    } else if (startSupply == 0) {
        return;                                                  // L136-137: BUGGY — basket currently empty
    } else {
        uint256 timeDiff = (block.timestamp - lastFee);          // L139
        uint256 feePct = timeDiff * licenseFee / ONE_YEAR;       // L140
        uint256 fee = startSupply * feePct / (BASE - feePct);    // L141

        _mint(publisher, fee * (BASE - factory.ownerSplit()) / BASE);   // L144
        _mint(Ownable(address(factory)).owner(), fee * factory.ownerSplit() / BASE); // L145
        lastFee = block.timestamp;                               // L146: normal path also re-touches lastFee

        uint256 newIbRatio = ibRatio * startSupply / totalSupply();
        ibRatio = newIbRatio;
        emit NewIBRatio(ibRatio);
    }
}
```

**Relevant locals/state**:
- `lastFee` (state, `uint256 public override lastFee`) — the timestamp of the most recent point up to which fees have been "settled." Every branch of `handleFees` is, by design, supposed to leave `lastFee` at `block.timestamp` when it returns — branch 1 (L135) and branch 3 (L146) both do this explicitly.
- `startSupply` (parameter) — the caller's pre-effect `totalSupply()` snapshot; gates which branch executes.
- `block.timestamp` (global) — the current block time; both the value branches 1/3 assign to `lastFee` and the reference point `timeDiff` is measured against on the *next* call.

**The disputed statement (L136–137)**: `else if (startSupply == 0) { return; }` — the one branch, out of three, that does **not** update `lastFee` before returning. This is not a value miscomputation inside an existing formula; it is the complete absence of the `lastFee = block.timestamp;` statement that the other two branches both carry.

**Variable-value intent (L137)**: on any execution that reaches this branch (i.e., `lastFee` has already been initialized at least once, but the basket currently holds zero outstanding tokens), `lastFee`'s value at function exit must still equal `block.timestamp` — the same "touch" convention branches 1 and 3 uphold — not remain at whatever stale value it held on entry.

**Statement/line-level intent**: `handleFees` is trying to uphold the invariant that `lastFee` always marks "the last point in time this function was told there was nothing (more) to charge, or charged everything owed up to now" — so that the *next* invocation's `timeDiff = block.timestamp - lastFee` only ever measures time during which the basket held tokens. The `startSupply == 0` branch exists precisely to skip fee *computation* (there is nothing to charge a fee on when supply is zero — `fee` would need a `startSupply` multiplicand, and `ibRatio`'s update divides by `totalSupply()`, both degenerate at zero), but skipping the computation is not a license to also skip the bookkeeping timestamp.

**Reported erroneous behavior** (H-01, verbatim, primary source `Web3Bugs/reports/65.md`): *"`handleFees` does not update `lastFee` if `startSupply == 0`. This means that wrongly, extra fee tokens would be minted once the basket is resupplied and `handleFees` is called again."*

**Proof of Concept** (verbatim scenario, primary source only — **absent from the scattered excerpt**, §0.5): *"All basket token holders are burning their tokens. The last burn would set totalSupply to 0. After 1 day, somebody mints basket tokens. `handleFees` would be called upon mint, and would just return since totalSupply == 0. Note: It does not update `lastFee`. ... The next block, somebody else mints a token. Now `handleFees` will calculate the fees according to the current supply and the time diff between now and `lastFee`. ... But `lastFee` wasn't updated in the previous step. `lastFee` is still the time of 1 day before ... So now the basket will mint fees as if a whole day has passed since the last calculation, but actually it only needs to calculate the fees for the last block."*

**Impact** (verbatim, primary source only, **absent from the scattered excerpt**): *"Loss of user funds. The extra minting of fee tokens comes on the expense of the regular basket token owners, which upon withdrawal would get less underlying than their true share, due to the dilution of their tokens' value."* Judge's own restatement (`0xleastwood`): *"fees are charged on the user's deposit for the entire time that the basket was inactive for... Malicious publishers can setup baskets as a sort of honeypot to abuse this behaviour."*

**Recommended Mitigation Steps** (verbatim, primary source only, **absent from the scattered excerpt**): *"Set `lastFee = block.timestamp` if `startSupply == 0`."*

**Expected/intended behavior**: on any call to `handleFees` where `lastFee != 0` (already initialized) and `startSupply == 0`, `lastFee` must be advanced to `block.timestamp` before the function returns — exactly mirroring what branches 1 and 3 already do, matching the literal one-line recommended fix.

**Patch intent**: the recommendation is a literal one-line insertion (`lastFee = block.timestamp;` before the `return;`) scoped to exactly this branch. Used below as evidence that the intended target value is `block.timestamp` (an exactly-determined quantity, not a bound) — R1-3 constructs the relation from this and from the other two branches' own already-present convention, not by mechanically copying the patch as annotation prose (the annotation ends up textually identical to the patch's target state only because that literal value genuinely *is* the correct specification here — §2/§3 note this is not itself a problem).

**Bug-relevant intended numeric behavior**: for any call to `handleFees` reaching the `lastFee != 0 && startSupply == 0` branch, `lastFee` at function exit must equal `block.timestamp`; the current code instead leaves it unchanged from function entry, causing the *next* fee-charging call's `timeDiff` to over-count by exactly the dead interval during which the basket held no tokens.

---

## R1-2 — Intent Abstraction

Distinguishing property (patch's literal one-line insertion used only as evidence for *which* value is correct, not transcribed as annotation syntax beyond that): in the `startSupply == 0` branch, `lastFee`'s value at function exit must equal `block.timestamp`, not remain at its entry value. **Intent-level orientation: Effect/state-transition-centered** — a claim about how a single piece of persistent state (`lastFee`) must move as a result of the call (or, on this specific path, must move but currently doesn't), not a bound on an intermediate computed value.

---

## R1-3 — Select the least implementation-specific sufficient relation

**Preliminary check — does this relation need a function call inside `intentValue`?** No. `block.timestamp` is an ordinary global reference (`varRef`, same treatment as `web3bugs_3_H_04`'s/`web3bugs_16_H_06`'s use of `block.timestamp` as a plain in-scope operand), not a call. No alpha-style blocker to check at all — the cleanest case in this respect of the three template cases read for calibration.

1. **Directional (weakest tier), non-strict**: `lastFee(Exit) >= lastFee(Entry)`. **Rejected — does not discriminate.** The buggy code leaves `lastFee` *unchanged* (`lastFee(Exit) == lastFee(Entry)`), which already satisfies `>=`; a non-strict directional relation is trivially true on both the buggy and the intended code and catches nothing.
2. **Directional, strict**: `lastFee(Exit) > lastFee(Entry)`. **Expressible, and discriminates** for any scenario where time has genuinely elapsed since `lastFee` was last set (buggy: `lastFee(Exit) == lastFee(Entry)`, so `>` is false → Violated; intended: `lastFee(Exit) == block.timestamp > lastFee(Entry)` → true → Satisfied, given `block.timestamp` has advanced past the stored `lastFee`). **Considered, not selected**: the intended value here is not naturally a bound — the recommendation names an *exact* target (`block.timestamp`), and a strict-inequality relation would pass on a plausible defect-retaining "partial fix" that advances `lastFee` to some value other than the true current time (e.g., an off-by-some-amount touch that still leaves the next call's `timeDiff` wrong, just by a smaller margin) — see the required negation check below for the concrete instance this would miss.
3. **Exact equality (SELECTED)**: `lastFee == block.timestamp`. Matches the value R1-1 establishes as correct exactly (the same convention branches 1 and 3 already implement, and the literal recommended fix's target state), and is strictly more discriminating than either directional alternative above.

**Required check (§3/R1-3)**: does this equality's negation fail to catch some alternative implementation that retains the *reported* defect — a `lastFee` that isn't properly re-touched when `startSupply == 0` — but produces it differently? Checked against two distinct alternative shapes:
- **No update at all (the actual buggy code)**: `lastFee(Exit) = lastFee(Entry)`. Caught (Violated), as shown below.
- **A near-miss "partial fix"** — e.g., an implementation that sets `lastFee = block.timestamp - 1;` (an off-by-one, or any similarly near-but-wrong touch) instead of the exact current time: `lastFee(Exit) = block.timestamp - 1 ≠ block.timestamp`. **Caught by the exact equality** (Violated) — this is exactly the alternative the weaker strict-inequality candidate (#2) would have *missed* (`block.timestamp - 1 > lastFee(Entry)` is still true whenever meaningful time has elapsed, so `#2` would report Satisfied on this still-defective variant). This is the concrete instance motivating equality's selection over #2, not a hypothetical aside.
- No alternative implementation that still leaves `lastFee` un-advanced-to-`block.timestamp` on this branch escapes the exact equality's negation. **No gap found**; this case does not need an `Intent coverage: Partial` flag on this ground.

**Winner: Alternative 3 (exact equality).**

**Discrimination check (explicit arithmetic, per §9 checklist item 1).** Scenario constructed directly from the report's own PoC narrative ("After 1 day, somebody mints..."): `lastFee(Entry) = 1,000,000` (the timestamp set by the last *normal* fee-charging call, branch 3, before the basket was fully drained), `startSupply = 0` (the basket has since been fully burned), `block.timestamp = 1,086,400` (exactly 1 day / 86,400 seconds later, matching the report's own "after 1 day" framing).
- **Buggy** (current code, `return;` with no update): `lastFee(Exit) = 1,000,000` (unchanged). Check: `1,000,000 == 1,086,400` → **false ⟹ Violated.**
- **Intended** (per the recommended fix, `lastFee = block.timestamp;` inserted before the `return;`): `lastFee(Exit) = 1,086,400`. Check: `1,086,400 == 1,086,400` → **true ⟹ Satisfied.**

**A structural observation not present in the calibration cases (worth recording explicitly, per §7's transparency requirement)**: because branches 1 and 3 both *already* leave `lastFee == block.timestamp` at exit, the selected relation is not merely scenario-locally true on the intended code — it is a genuine **function-wide invariant of the fixed implementation across all three branches simultaneously** (branch 1: sets it directly; branch 3: sets it directly; branch 2 with the fix: also sets it directly). The relation only needs a scenario at all to guarantee that the specific *buggy* execution path (branch 2) is the one exercised — not to make the relation itself sound, unlike several other cases in this batch where the relation's validity itself depends on a narrow precondition (contrast `web3bugs_16_H_06`'s non-enforced decimals pair). This is recorded as a corroborating strength of the selected relation, not used to weaken the scenario-conditioning discipline below (a concrete reachability scenario is still required, and still documented, per README §4's general note).

---

## R1-4 — During vs Post

**Chosen: Post.** The relation concerns a persistent state variable's value at function exit — README's own Post criterion ("the relation concerns... final state... a persistent state transition") applies directly. This is a clearer case for Post than `web3bugs_29_H_11`'s `amount0`/`amount1` (which needed `@During`+`(Before)` precisely because those locals don't exist at function entry): `lastFee` is ordinary persistent state, present at both entry and exit, and — critically — **there is no statement in the buggy branch to attach a `@During` to at all**: the branch's entire body is a bare `return;`, with no assignment whose before/after effect a During could check. What the intended behavior requires is an entirely absent statement, not a wrong effect of an existing one; the only coherent way to state "the exit-time value of this persistent variable must be X" when the buggy branch performs no relevant assignment is a `@Post` at the function's own exit (mirroring README's `SwordCrowdsale`/`CDP.update` precedent: an assignment-shaped patch that still resolves to `@Post`, not because the patch is single-statement-shaped, but because the relation's own nature — final persisted state — calls for it).

**No Entry/Exit snapshot syntax is actually needed inside the relation itself.** Although the scenario's *reachability* depends on `lastFee(Entry) != 0` (the precondition that routes execution into the `else if` rather than the `if (lastFee == 0)` branch), the relation being checked (`lastFee == block.timestamp`) references only the exit-time (default, unqualified) value of `lastFee` under `@Post` — `lastFee(Entry)` is not itself compared against anything in the annotation text, only used in prose (here and in R1-6) to describe which concrete scenario reaches the buggy branch, the same way `web3bugs_3_H_04`'s `yieldQuotientFP > 0` scenario-precondition was stated in prose rather than embedded in the annotation.

**Required explicit delta-exception check (README §4/R1-7, per task instructions).** `handleFees` contains **no loop of any kind** — confirmed by reading its entire body (lines 133–153, a plain three-way `if`/`else if`/`else`, no `for`/`while` anywhere). This is a more clear-cut "not applicable" outcome than `web3bugs_29_H_11`'s if/else-inside-a-loopless-function case (itself already a clean negative) — there is no candidate loop-body attachment point to even consider, and the confirmed engine fact (`fixpoint()`'s `transfer_function` never reaching `_process_during_annotations` for a loop-interior node) has nothing to apply to. **Delta confirmed not applicable, trivially.** (For completeness: `Basket.sol` does contain `for` loops elsewhere — `validateWeights`, `approveUnderlying`, `pushUnderlying`, `pullUnderlying` — but none of them calls or is called by `handleFees`; they are unrelated to this case's defect and its own CFG.)

---

## R1-5 — Relation form

**Exact equality** via the grammar's general `RelationalCmp` common-form rule (`intentValue relOp intentValue`, `Parser/Solidity.g4` line 325), reached through `postClause -> commonClause`. Classified as an **Entry/Exit-adjacent relation targeting a single exit-time value** — it is not literally a `(varRef(Entry) relOp varRef(Exit))` pairing of the *same* identifier (contrast `web3bugs_42_H_01`'s `debts == debts(Entry) + increasingDebt`, which genuinely mixes an entry-snapshotted and an exit-time reference of the same variable in one expression); here the LHS (`lastFee`, implicitly exit-time under `@Post`) is compared against an independent global (`block.timestamp`), which is itself already exit-scoped (there being no meaningful "entry-time `block.timestamp`" distinct from exit-time within one function call — the EVM's `block.timestamp` is constant for the duration of a single transaction). Not forced to equality by the patch's assignment shape (R1-5's explicit caution) — equality was selected in R1-3 on an independent, concretely-demonstrated discrimination ground (the near-miss "partial fix" that a weaker strict inequality would have missed).

---

## R1-6 — Construct the target annotation

**Attachment point**: inside the `else if (startSupply == 0)` branch (lines 136–137), immediately after the disputed `return;` statement — the textual-placement convention used elsewhere in this project's `@Post` write-ups (e.g. `web3bugs_3_H_04`, `web3bugs_42_H_01`) even though `@Post`'s semantics evaluate at the function's own exit state, not at this specific textual line.

**Scenario precondition this instantiation relies on (README's scenario-conditioning note, §4/R1-7)**: the relation as written is only exercised (i.e., only reaches the buggy branch at all) given `lastFee(Entry) != 0` (the basket has already had at least one prior fee-settling call — the negation of branch 1's own guard) and `startSupply == 0` (the basket currently holds zero outstanding tokens — the branch's own explicit condition, already present in the source). Neither condition needs to be written into the annotation itself (see R1-4) — they are properties of the concrete debug/batch scenario that would be used at RQ1-B time (deferred) to route execution into this specific branch, matching this batch's `web3bugs_3_H_04`/`web3bugs_29_H_11` precedent for stating reachability preconditions in prose rather than inside the relation.

**Target annotation**:
```solidity
function handleFees(uint256 startSupply) private {
    if (lastFee == 0) {
        lastFee = block.timestamp;
    } else if (startSupply == 0) {
        return;
        // @Post lastFee == block.timestamp
    } else {
        uint256 timeDiff = (block.timestamp - lastFee);
        uint256 feePct = timeDiff * licenseFee / ONE_YEAR;
        uint256 fee = startSupply * feePct / (BASE - feePct);

        _mint(publisher, fee * (BASE - factory.ownerSplit()) / BASE);
        _mint(Ownable(address(factory)).owner(), fee * factory.ownerSplit() / BASE);
        lastFee = block.timestamp;

        uint256 newIbRatio = ibRatio * startSupply / totalSupply();
        ibRatio = newIbRatio;

        emit NewIBRatio(ibRatio);
    }
}
```
Both referenced identifiers (`lastFee`, `block.timestamp`) are ordinary in-scope values at the function's exit — a state variable and an EVM global, respectively. No synthetic constant is introduced (contrast README's `900`-style derived-constant guidance, which does not apply here since the relation's RHS is a live global, not a scenario-specific literal).

**Quantification note**: the property is a plain, unindexed state-variable check (`lastFee` is a single scalar, not an array/mapping element) — not a claim quantified over a stored collection of co-existing elements (contrast `web3bugs_83_H_01`'s "every pool" case or `web3bugs_42_H_01`'s single-`_id`-out-of-a-mapping instantiation). No representative-element instantiation issue applies.

---

## R1-7 — Expressibility decision

**Values referenceable at a legal program point**: Yes. `lastFee` (state variable, `varRef`, defaulting to exit-time value under `@Post`) and `block.timestamp` (EVM global, `varRef` with member access, the same construct already relied on in `web3bugs_3_H_04`/`web3bugs_16_H_06`) are both ordinary in-scope identifiers at `handleFees`'s exit — nothing needed here is behind an external-contract boundary or missing a proxy.

**Arithmetic/logical relation representable**: Yes. `lastFee == block.timestamp` is a single `intentValue relOp intentValue` (`RelationalCmp`) with no arithmetic beyond the bare comparison — the simplest relation form encountered across this calibration batch.

**No function call inside `intentValue`**: confirmed not an issue (R1-3's preliminary check) — neither operand is a call.

**Observation point supported — explicit check against the confirmed `delta` (loop-body-`@During`) exception, per task instructions.** As established in R1-4: `handleFees` contains no loop anywhere in its body, and the relation is a `@Post` (not a `@During`) in any case, evaluated at the function's ordinary, non-loop exit. **Delta confirmed not applicable, trivially** — there is no candidate loop-body attachment point at all, a cleaner negative than `web3bugs_29_H_11`'s (which had to rule out conditional-vs-loop conflation) or `web3bugs_16_H_06`'s (which had to confirm the whole contract, not just the one function, is loop-free).

**Outcome: Expressible = YES.**

---

## Section 5 — Value/Algorithm and Usable/Unusable

- **Algorithm-level** — per the paper's own classification (Algorithm-level = "operation ordering, an absent state update, or a missing procedure call"), this is a direct, unambiguous instance of the "absent state update" pattern: the intended computation for `handleFees` is "on every invocation, once this function has decided how (or whether) to charge a fee, leave `lastFee` at `block.timestamp`" — a step every other branch performs. The `startSupply == 0` branch is missing exactly that one state-mutating statement; nothing inside an existing formula is wrong (there is no formula at all on this path — the entire "fee computation" is correctly and intentionally skipped when `startSupply == 0`, since `fee`'s own formula and `newIbRatio`'s division by `totalSupply()` would both be degenerate at zero supply). This is the textbook shape the paper's own definition names directly, and does not require the more careful "what's missing from the computation's own steps, not an incidental implementation detail" analysis that `web3bugs_16_H_06` needed (there, an unused helper function's presence was a tempting but ultimately non-decisive signal) — here there is no computation, spare helper, or intermediate formula to weigh at all: a single required assignment statement is present on two of three branches and absent on the third.
- **Usable** — both values the relation needs (`lastFee`, `block.timestamp`) are referenceable, as ordinary in-scope identifiers, at the annotation's program point (the function's exit); nothing is behind an external-contract boundary or otherwise unreachable (§5, purely a representational-resources question).

---

## RQ2-A — Specification Requirements profile

**Relevant statements** (within `handleFees` itself; **recount on review — see Review Notes**):
1. `else if (startSupply == 0) { return; }` (L136–137) — the target control-flow branch, counted as **one** unit (condition + body, not split into two separate entries): this is the branch in which the required `lastFee` update is absent, and is recorded as the annotation's attachment-point/subject context. `startSupply` (the condition's own operand) is read here, which is why it stays a counted unique value below. This is *not* counted because the relation's own truth-value soundness depends on this specific branch-selection threshold — per R1-3's own structural observation, `lastFee == block.timestamp` is a function-wide invariant that would hold identically under a differently-thresholded branch split, as long as *some* branch still leaves `lastFee` untouched and is the one under test — it is counted because a reader needs it to know *which* concrete scenario the `@Post` is being exercised under, the same role a genuinely-buggy assignment statement plays as an "attachment point" elsewhere in this batch (e.g. `44_H_02`'s L210), even though here — being an absence, not a wrong assignment — there is no operand-defining role to it either.

Total: **1 relevant statement.** *(Corrected on review from 3 — see Review Notes.)*

**Excluded, with reason (Step 1, README §6)**:
- `if (lastFee == 0) { lastFee = block.timestamp; }` (L134–135) — **excluded on review (was counted as statement 1)**. This is a pure reachability/branch-selection gate, structurally identical to the `require(...)` gates already excluded in `web3bugs_62_H_10`'s RQ2-A (e.g. `require(isSale, "!sale")`): its condition determines which of three mutually-exclusive scenarios is under test, but does not redefine any value the selected relation reads, and the relation's own validity (per R1-3's function-wide-invariant observation) does not depend on where this specific threshold is drawn. Excluded entirely, matching the same reachability-gate rule applied elsewhere in this batch, not merely "not separately counted."
- `lastFee = block.timestamp;` (L135, branch 1's body) and the entirety of branch 3 (L139–152, the normal fee-charging path) — both are on execution paths mutually exclusive with the target branch. They were read in R1-1 purely to *discover* the intended "touch" convention (the same role `web3bugs_3_H_04`'s `updateHourlyBondAmount` played for its case) and to establish the structural observation in R1-3 that the fixed relation is a function-wide invariant — but the selected relation's own validity does not depend on either branch's specific computation (changing branch 3's fee formula, for instance, would not change whether `lastFee == block.timestamp` holds on the target branch). Excluded entirely, not even as a case note, per the same corollary `web3bugs_29_H_11` applied to its rejected-alternative code (§6's "alternative-rejection inspection doesn't count").

**Unique relevant program values**:
- State (1): `lastFee`.
- Parameter (1): `startSupply` (the branch-gating value, read within the one counted statement; not itself an operand of the relation's RHS, but a value a reader must trace to understand why this branch executes).
- Global (1): `block.timestamp`.

Total: **3 unique relevant program values** (unchanged by the statement-count correction — `startSupply` was already, and remains, drawn from the still-counted `else if` branch). This is markedly smaller than every calibration case read for this pass (`web3bugs_3_H_04`: 9; `web3bugs_16_H_06`: 5; `web3bugs_29_H_11`: 11) — a direct consequence of the defect being a single missing same-function statement with no computed intermediate values at all, not an artifact of under-counting (no cross-function or cross-statement dependency was excluded on a technicality; there genuinely is none for this relation).

**Additional functions required: 0.** Neither the relation nor the counted branch involves a function call — `lastFee`, `startSupply`, and `block.timestamp` are all directly-referenced identifiers.

**Additional protocol/application-specific contracts/libraries required: 0.**

**Context breadth: 1** (same-function context — unchanged by the statement-count correction: the relation's own two operands, `lastFee`/`block.timestamp`, need no same-function context to evaluate, but understanding *which scenario* the `@Post` is exercised under still requires the one counted same-function branch; not 0, since that scenario-identifying context is still same-function material beyond the bare relation text itself).

**External specification required: No.** Everything the selected relation depends on — the "touch `lastFee` on every branch" convention and the exact target value `block.timestamp` — is derivable directly from `handleFees`'s own other two branches and the report's literal one-line recommendation; no protocol-external accounting/business convention had to be separately looked up.

---

## Section 7 — Alternatives-considered summary

| # | Relation | Tier | Expressible? | Discriminates? | Verdict |
|---|----------|------|---------------|-----------------|---------|
| 1 | `lastFee(Exit) >= lastFee(Entry)` | Directional, non-strict | Yes | No | Rejected — trivially true on the buggy code (unchanged value already satisfies `>=`) |
| 2 | `lastFee(Exit) > lastFee(Entry)` | Directional, strict | Yes | Yes, but incompletely | Rejected — discriminates the actual buggy code, but the required negation check finds a concrete near-miss "partial fix" (`lastFee = block.timestamp - 1`) it would fail to catch |
| 3 | `lastFee == block.timestamp` | Exact equality | Yes | Yes | **Selected** — catches both the actual buggy code and the near-miss alternative #2 would have missed |

---

## RQ1-B / RQ2-B

Deferred per README §8. Not run, not predicted. No caution comparable to `web3bugs_3_H_04`'s loop-propagation concern or `web3bugs_29_H_11`'s confirmed `abi.decode` crash applies here — `handleFees` involves no external call, no `staticcall`/`abi.decode` pattern, and no loop; the values the relation needs (`lastFee`, `block.timestamp`) are about as structurally simple as this project's `@Post` targets get. This is a forward-looking observation for whoever runs RQ1-B, not a substitute for actually running it.

---

## Summary

- **Expressible: Yes.** Values referenceable (`lastFee`, `block.timestamp`, both ordinary in-scope identifiers), arithmetic representable (a single equality comparison, no arithmetic operators needed at all), observation point (`@Post` at `handleFees`'s exit) supported — explicitly checked against, and trivially not blocked by, the confirmed `delta` loop-body-`@During` exception (README §4): `handleFees` contains no loop anywhere in its body, and the relation is a `@Post`, not a `@During`, in any case.
- **Target relation**: `lastFee == block.timestamp`, attached `@Post` on `handleFees`, immediately after the disputed `return;` in the `else if (startSupply == 0)` branch. Scenario-conditioned on `lastFee(Entry) != 0` (basket previously initialized) and `startSupply == 0` (basket currently empty) — both conditions are the source's own existing branch gates, not additions.
- **Quantified property instantiated: No** — `lastFee` is a plain scalar state variable, not an element of a collection the annotation would need to range over.
- **Algorithm-level** (an absent state update on one of three mutually-exclusive branches — the paper's own canonical Algorithm-level pattern, no ambiguity with the Value-level "wrong operand within an existing formula" shape since no formula exists on the buggy path at all), **Usable** (both needed values directly referenceable, no representational gap), `@Post`, exact-equality common-form (`RelationalCmp`).
- **RQ2-A profile** *(corrected on review — see Review Notes)*: 1 relevant statement (the `else if (startSupply == 0) { return; }` branch, counted as one unit; `if (lastFee == 0)` excluded as a pure reachability gate, matching `web3bugs_62_H_10`'s treatment of its own `require(...)` gates), 3 unique relevant program values (1 state / 1 parameter / 1 global — unchanged), 0 additional functions required, 0 additional protocol contracts/libraries, Context breadth 1 (same-function), External specification required: No. The smallest specification-requirements footprint among this pass's calibration cases (`3_H_04`: 5 statements/9 values; `16_H_06`: 4/5; `29_H_11`: 7/11) — a genuine structural feature of this defect (a single missing same-function statement with no computed intermediates, and no soundness-load-bearing branch-selection logic either), not an under-counting artifact.
- **Methodological judgment calls made in this pass**: (1) chose exact equality over a strict directional inequality specifically because the required negation check surfaced a concrete near-miss "partial fix" the weaker form would miss — recorded in §7, not asserted from habit; (2) determined Post (not During) is the only coherent scope, since there is no existing `lastFee`-updating statement whose effect can be checked at a `During` observation point on the buggy branch — the defect is the *absence* of a statement, not the wrong effect of an existing one; (3) explicitly excluded branches 1 and 3's own bodies, and (on review) `if (lastFee == 0)`'s own condition, from the RQ2-A count as non-load-bearing-but-informative (discovery/corroboration/reachability only), applying the same "alternative-rejection inspection doesn't count" corollary `web3bugs_29_H_11` used for its rejected reserve-based alternative and the same reachability-gate exclusion `web3bugs_62_H_10` applied to its own `require(...)` statements; (4) considered and rejected treating the report's "extra fee minted on the next call" consequence as a second README §4 multi-annotation-set member, since it is a two-transaction-spanning symptom of the same single-statement root cause rather than an independently-reported mechanism, and checking the root cause directly gives Full coverage without needing a second relation.
- **RQ1-B/RQ2-B**: deferred, not run in this pass; no case-specific engine-precision caution identified (contrast `3_H_04`'s loop-propagation note or `29_H_11`'s confirmed `abi.decode` crash) — this case's values are simple state/global reads with no call or loop involved anywhere in the relevant path.

---

## Review Notes

Independent re-verification prompted by an external-LLM critique of the RQ2-A section (this case predates the `## Review Notes` convention adopted from folder `22` onward, so this is the first review pass recorded here).

**Confirmed correct, no change**: R1-1 bug reconstruction, R1-3's selected relation and negation check (re-derived with the same numbers, `lastFee(Entry)=1,000,000`, `block.timestamp=1,086,400`), R1-4/R1-7's Post/exact-equality/delta-exception reasoning, §5's Algorithm-level/Usable classification, Intent coverage: Full. None of these were questioned or found in error.

**RQ2-A "Relevant statements" was overcounted at 3 — corrected to 1.** The original count included `if (lastFee == 0)` (statement 1) and split `else if (startSupply == 0)`/`return;` into two separate entries (statements 2–3). Re-checked against README §6 Step 1 and, specifically, against `web3bugs_62_H_10`'s own already-established precedent (reviewed earlier this session) for excluding pure reachability `require(...)` gates entirely: `if (lastFee == 0)` is structurally the same kind of fact as `62_H_10`'s `require(isSale, "!sale")` — it determines which of several mutually-exclusive scenarios is under test, but does not redefine any operand the selected relation reads, and (per R1-3's own already-recorded observation that `lastFee == block.timestamp` is a function-wide invariant across all three branches of the fixed implementation) the relation's own soundness does not depend on exactly where this threshold is drawn. Excluded. The `else if (startSupply == 0) { return; }` branch is kept, but as **one** combined unit rather than two separate statements — `return;` itself defines no operand (unlike every other "disputed/target statement" counted elsewhere in this batch, which are assignments defining the relation's own constrained value, e.g. `44_H_02`'s L210) and is control-flow-vestigial (removing it would not change the branch's behavior, since it is already the branch's last statement); it earns its place in the count only as part of the branch that identifies which scenario is under test, not as an independent operand-definer or a separately-load-bearing fact. **Relevant statements corrected 3 → 1.** Unique relevant program values, Additional functions, and Context breadth are unaffected (`startSupply` was already, and remains, drawn from the still-counted branch; Context breadth stays 1, same-function, since identifying the scenario still requires this one same-function branch beyond the bare relation text).

**Wording fix**: the Summary's "(2)" methodological-judgment-call bullet previously read "the buggy branch contains no statement at all for a `During` to attach to" — imprecise, since `return;` *is* a statement. Corrected to "there is no existing `lastFee`-updating statement whose effect can be checked at a `During` observation point," matching R1-4's own (already-precise) phrasing.

No change to Expressible/Usable/Algorithm-level/Intent coverage/attachment point, or to the target relation itself — this pass corrected RQ2-A's statement count and one imprecise sentence, nothing else.
