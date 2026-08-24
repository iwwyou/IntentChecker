# web3bugs_71_H_11 — Agent A Analysis (R1-1 → R1-7, RQ2-A)

Methodology: `First Revision/phase_reviews/README.md` (current, non-superseded version).

## Case metadata

- **Case ID**: `web3bugs_71_H_11`
- **Contract**: `PoolTemplate` (InsureDAO, contest 71)
- **Function**: `resume()`
- **Source read**: `evaluation/RQ1/target_contracts_original/web3bugs_71_H_11.sol` (verbatim, lines 691–734 for `resume()`; line 146 for `MAGIC_SCALE_1E6`)
- **Audit report**: `Dataset/Web3Bugs/S6_4/contest_71_H_11/README.md` — H-11, "Wrong implementation of `resume()` will compensate overmuch redeem amount from index pools." **Correction (second refinement pass)**: an earlier version of this analysis stated the report had no Recommendation/patch — that was wrong, caused by reading a truncated local copy of the report that was missing its Proof-of-Concept and Recommendation sections. The dataset file has since been corrected to the full report content (verified against the real Code4rena finding). The report **does** include a full worked Proof of Concept and an explicit Recommendation with the exact corrected formula:
  ```solidity
  uint256 _redeemAmount = _divCeil(
      _deductionFromIndex * _shareOfIndex,
      MAGIC_SCALE_1E6 * MAGIC_SCALE_1E6
  );
  ```
  Per README §2, patch access is permitted and this is used as **corroborating evidence** for the intended proportional-allocation behavior in R1-1 below — not mechanically transcribed as the annotation. Notably, R1-2/R1-3's independently-derived target relation (`_redeemAmount <= ceil(_deductionFromIndex * _shareOfIndex, 1e12)`) has the *same* multiplicative structure as this recommendation, arrived at without ever having read it (the original analysis pass genuinely believed no patch existed) — a real instance of the methodology's abstraction discipline converging on the patch's own formula from first principles, then abstracting the exact equality down to an upper bound because the *reported* defect ("overmuch") is specifically an upper-bound property, not an exact-value property.
- **Existing prior-pipeline label** (historical, retired methodology, recorded for continuity only): `evaluation/RQ1/dataset.csv` row 78 and `evaluation/RQ1/annotation_plans.md` mark this `not_detectable (L1b: loop-body-granularity)`. See R1-7 for why this does not carry over.

---

## R1-1 — Reported Behavior Reconstruction

**Function role.** `resume()` closes out the debt (`vault.debts(address(this))`) the pool incurred while paying out insurance claims, splitting that debt between the pool's own liquidity and the index pools that allocated credit to it, via `IIndexTemplate(_index).compensate(_redeemAmount)` for each index in `indexList`.

**Relevant local variables:**
- `_debt` (L698) = `vault.debts(address(this))` — total outstanding debt owed to the vault.
- `_totalCredit` (L699) = `totalCredit` — total credit allocated to this pool by all indices.
- `_deductionFromIndex` (L700–701) = `(_debt * _totalCredit * MAGIC_SCALE_1E6) / totalLiquidity()` — the portion of `_debt` attributable to index-supplied credit, scaled up by `MAGIC_SCALE_1E6` (1e6), matching the contract's own documented fixed-point convention (see the `rewardPerCredit` comment: "Times MAGIC_SCALE_1E6. To avoid reward decimal truncation").
- `_credit` (L705) = `indicies[_index].credit`.
- `_shareOfIndex` (L707–708) = `(_credit * MAGIC_SCALE_1E6) / _totalCredit` — this index's fractional share of `_totalCredit`, scaled by 1e6 (e.g. 30% share → 300000). Name and construction unambiguously identify it as a proportion.
- `_redeemAmount` (L709–712) = `_divCeil(_deductionFromIndex, _shareOfIndex)` — **the buggy statement**, the amount requested from index `_index` via `compensate()`.

**Variable-value intent (L709–712).** `_redeemAmount` for a given index should be that index's proportional share of `_deductionFromIndex` — i.e. `_deductionFromIndex` scaled *down* by `_shareOfIndex`/1e6, not scaled *up* by dividing by `_shareOfIndex`.

**Statement/line-level intent.** The loop should uphold: the sum of what's requested from all indices approximates `_deductionFromIndex/MAGIC_SCALE_1E6` (real, unscaled index-attributable debt), distributed in proportion to each index's credit share — the invariant the surrounding `_deductionFromPool`/`_shortage`/`vault.transferDebt` accounting is built to close out.

**Reported erroneous behavior.** Title: "will compensate overmuch redeem amount from index pools"; body: "Wrong arithmetic," with the buggy snippet highlighted. No corrected formula given.

**Expected/intended behavior (implied, reconstructed).** `_shareOfIndex` is a fraction on a 0..1e6 scale. Applying a fraction means *multiplying* by it (then descaling), not *dividing* by it. Dividing inflates the result instead of scaling it down — exactly "compensate overmuch."

**Concrete scenario / arithmetic — now using the report's own Proof-of-Concept numbers directly (second refinement pass; previously used a synthetic example since the patch/PoC weren't known to exist). Independently re-verified in Python, not just re-typed from the report — see below.**

Report's PoC: `totalLiquidity = 200,000e18`, `totalCredit = 100,000e18`, `debt = 10,000e18`; Index Pool 1 credit `= 20,000e18`, Index Pool 2 credit `= 30,000e18`.

- `_deductionFromIndex = (10,000e18 * 100,000e18 * 1e6) / 200,000e18 = 5,000,000,000e18` (`5e27`). *(Independently recomputed in Python; the report's own inline comment for this line, "`= 10,000 * 10**6 * 10**18`," is an imprecise simplification and does not match `5e27` — but every downstream number in the report is consistent with the correct `5e27` value, confirmed below, so this is a documentation slip in the report's PoC comment, not a discrepancy that affects the analysis.)*
- Index 1: `_shareOfIndex = (20,000e18 * 1e6)/100,000e18 = 200,000`. **Buggy**: `_redeemAmount = ceil(5e27/200,000) = 25,000e18` — matches the report's stated `25,000 * 10**18` exactly.
- Index 2: `_shareOfIndex = (30,000e18 * 1e6)/100,000e18 = 300,000`. **Buggy**: `_redeemAmount = ceil(5e27/300,000) ≈ 16,666.67e18` — matches the report's stated `~16,666 * 10**18` exactly.
- **Intended (recommendation's formula, `ceil(_deductionFromIndex * _shareOfIndex, 1e12)`)**: Index 1 → `ceil(5e27*200,000/1e12) = 1,000e18`; Index 2 → `ceil(5e27*300,000/1e12) = 1,500e18`. The report's own narrative independently confirms the Index 1 figure: "Index Pool 1 should only pay `1,000 * 10**18`, but actually paid `6,000 * 10**18`" (the `6,000` reflects a downstream insolvency-driven CDS shortfall distribution, not the `_redeemAmount` value itself, but the "should only pay 1,000" matches the corrected formula's output precisely).
- Buggy vs. intended: 25× overcompensation for Index 1 (25,000 vs 1,000), ~11× for Index 2 (16,666.67 vs 1,500) — far larger margins than the earlier synthetic example, and now grounded in the report's own verified figures rather than a constructed scenario.

This also shows the bug is *inverted*: as `_credit` for one index grows (`_shareOfIndex → 1e6`), the buggy result *shrinks* relative to what it should be — an index holding *more* credit is charged proportionally less relative to its fair share, the opposite of proportional allocation. General symbolic argument: with `S = _shareOfIndex`, `D = _deductionFromIndex`, buggy `= D/S` (pre-ceiling), intended `= D·S/1e12` (pre-ceiling); `D/S > D·S/1e12 ⟺ S² < 1e12 ⟺ S < 1e6`. Since `_credit ≤ _totalCredit` always, `S ≤ 1e6` with equality only in the degenerate single-index case — so for any multi-index split the buggy *pre-rounding* value exceeds the intended *pre-rounding* value. **Caveat added during second refinement pass**: this is a statement about the real-valued quantities *before* `ceil()` is applied to both sides. After both are ceiled to integers, the two rounded results can coincide when the pre-rounding gap is smaller than 1 — verified with a constructed edge case: `D=1000, S=999,999` gives buggy `ceil(1000/999999)=1` and intended `ceil(1000·999999/1e12)=1`, identical after rounding despite the real-valued gap being nonzero. The correct claim is: **the annotation is violated whenever the bug has a nonzero effect on the rounded `_redeemAmount`** — which the report's own PoC numbers (25× and ~11× gaps) show is the case for realistic magnitudes, not an edge case.

**Patch intent.** The report's Recommendation section gives the exact corrected formula (see metadata above) — used as corroborating evidence that the proportional-allocation reading is correct, not transcribed into the annotation as an exact equality (the annotation is an upper bound instead, since the reported defect is specifically "overmuch," an upper-bound property).

---

## R1-2 — Intent Abstraction

Governing question: `_redeemAmount` for a given index must not exceed that index's proportional share of `_deductionFromIndex`, where the proportion is exactly what the code already computes as `_shareOfIndex`.

**Orientation: value-centered** — a constraint on `_redeemAmount` (lvalue of the buggy statement) in terms of two other in-scope values computed a few lines earlier. Not a state-transition claim.

---

## R1-3 — Select the least implementation-specific sufficient relation

**Alternative 1 — Directional/monotonicity relation (weakest tier).** "`_redeemAmount` should increase monotonically as `_credit` increases across indices" — true of intended behavior, false of buggy (inverted, shown above). Rejected: requires comparing values from *different loop iterations*; none of the grammar's forms (`D_ba`, `D_ac`, `D_arg`, `P_ee`, `C_cmp`, etc., `paper/first_revision/main.tex` fig:intent-grammar) let an `intentValue` reference "this same expression's value in another iteration" — each is evaluated against one program state at one point. Not expressible as stated, and even if it were, only certifies an ordering, not the proportional-cap property "overmuch" actually describes.

**Alternative 2 — Inequality without `_shareOfIndex`.** `_redeemAmount * MAGIC_SCALE_1E6 <= _deductionFromIndex` ("no single index charged more than the entire index-attributable debt"). Expressible, and discriminates against the report's PoC numbers (Index 1 buggy `25,000e18 * 1e6 > 5e27` — violated; intended `1,000e18 * 1e6 <= 5e27` — satisfied). Rejected: doesn't encode proportionality at all — it would equally "pass" many other wrong allocation formulas (e.g. an equal split ignoring credit) as long as no index hits the full total. Understates what the report is about.

**Alternative 3 — Inequality using `_shareOfIndex` (SELECTED).** `_redeemAmount <= ceil(_deductionFromIndex * _shareOfIndex, MAGIC_SCALE_1E6 * MAGIC_SCALE_1E6)`. Ties the cap directly to the one value whose role is unambiguous (a fraction), fully in-scope, matches the report's own Recommendation formula's structure (independently re-derived — see R1-1), rejects the buggy value whenever the bug's effect on the *rounded* result is nonzero (see R1-1's ceiling-collapse caveat for the precise scope of this claim), satisfied with equality by the corrected value. An upper bound, not a full equality — says "don't overcompensate relative to your share," exactly the reported defect ("overmuch").

**Alternative 4 — Exact equality.** `_redeemAmount == ceil(...)`. Also expressible, also discriminates. Rejected: adds no discriminating power over #3 (the buggy formula is wrong by a large structural margin, not an off-by-one rounding difference) while pinning an exact rounding mode unnecessarily — over-specification the methodology warns against.

**Winner: Alternative 3.**

---

## R1-4 — During vs Post

**Relation-driven scope (before the R1-7 blocker below): During.** `_redeemAmount` is a loop-local, statement-time value computed immediately before being passed as a call argument; it doesn't persist to function exit and isn't a return value of `resume()` (which returns nothing). Nothing about this conclusion changes below — During remains the scope the relation's own nature calls for; what changes is whether that scope is actually usable (R1-7).

**Alternative considered and rejected: Post, on `_actualDeduction`/`_shortage`.** Could bound `_actualDeduction` (running sum of what indices actually paid, updated L713–715) relative to `_deductionFromIndex/MAGIC_SCALE_1E6` at function exit. Rejected: `_actualDeduction` is the return value of an external call (`IndexTemplate.compensate()`, `Dataset/Web3Bugs/S6_4/contest_71_H_11/IndexTemplate.sol` L421–450) whose own logic can legitimately return *less* than requested if the index is insolvent and falls back to its CDS pool. A Post bound on `_actualDeduction` would conflate "the pool asked for too much" (the actual `PoolTemplate` bug) with "the index couldn't fully pay" (legitimate `compensate()` behavior) — risking false results unrelated to the reported defect. The During, per-iteration bound on `_redeemAmount` isolates the arithmetic error itself, independent of downstream external-contract state — but see R1-7: this correctly-scoped During cannot actually be placed anywhere the engine will evaluate it, and no Post-based rescue exists (this paragraph already rules out the one candidate), so the case is Inexpressible despite During being the right scope in principle.

---

## R1-5 — Relation form

**Inequality (upper bound), using the grammar's `ceil()` DSL helper** — `commonClause → intentValue relOp ceil(intentValue, d)` (`C_ceil`), reached via `duringClause → commonClause` (`D_com`).

---

## R1-6 — Attempted construction of the target annotation (blocked — see R1-7)

**Attachment point (the annotation that would be correct if the engine evaluated it).** Immediately after `_redeemAmount`'s assignment (lines 709–712) and before the `compensate()` call (line 713), inside `if (_credit > 0)` (line 706) inside the `for` loop (line 703). All referenced identifiers are in scope.

**Constant derivation.** `d = MAGIC_SCALE_1E6 * MAGIC_SCALE_1E6 = 1,000,000,000,000` (1e12) — the product of the *same* scaling constant applied twice: once inside `_deductionFromIndex` (real-debt × 1e6) and once inside `_shareOfIndex` (fraction × 1e6); both factors must be divided out to recover a real token amount for `_redeemAmount`. Written as a literal (not `MAGIC_SCALE_1E6 * MAGIC_SCALE_1E6`) because the grammar notates the `ceil()` divisor as a bare `d`, distinct in kind from `intentValue`-typed arguments, reading as a plain numeric literal.

**Target annotation:**
```solidity
uint256 _redeemAmount = _divCeil(
    _deductionFromIndex,
    _shareOfIndex
);
// @During _redeemAmount <= ceil(_deductionFromIndex * _shareOfIndex, 1000000000000)
_actualDeduction += IIndexTemplate(_index).compensate(
    _redeemAmount
);
```

---

## R1-7 — Expressibility decision

*(Revised — third refinement pass. Earlier passes concluded Expressible = Yes; that conclusion is reversed below after directly reading the engine's loop-handling code, per the new `delta` tag and its confirmed-exception clause added to README §4 this session. This is not a reversal of R1-1–R1-6's reasoning about the bug or the relation — the selected relation and its During scope are still exactly right in content; what changed is a fact about this engine's implementation, discovered by reading `Interpreter/Engine.py` directly.)*

- **Values referenceable at a legal program point**: Yes — `_redeemAmount`, `_deductionFromIndex`, `_shareOfIndex` are locals in scope; `MAGIC_SCALE_1E6` is a public constant. No function call inside `intentValue` — the R1-3 "known-bound rescue" check wasn't even needed since no call was ever required (`_deductionFromIndex`/`_shareOfIndex` are already-materialized locals, not re-derived).
- **Arithmetic/logical relation representable**: Yes — `C_ceil` is a first-class `commonClause` form; multiplication of two `varRef`s is within `arithTerm`; `1000000000000` is a valid `number` literal.
- **Observation point supported**: **No.** This needs explicit justification because two earlier passes (in this same case, and independently in the retired pipeline) concluded otherwise.
  - The retired pipeline's `annotation_plans.md`/`dataset.csv` labeled this `not_detectable (L1b: loop-body-granularity)`, traced to `paper/backup/main_l4_l5_backup.tex` line 1299: *"the analyzer's state inside the loop body is a single summary joined over all iterations, so an @During annotation placed there cannot single out the faulty iteration."* This is a claim about **imprecision** (the joined/widened state being too coarse to distinguish faulty from correct) — and this session's *first* refinement pass correctly rejected that specific claim: imprecision is an RQ1-B/engine-precision question, explicitly out of scope for R1-7 (README §4), and loops are not automatically Unsupported for RQ1-B either (§8). That rejection was right, as far as it went.
  - But a **second, independent fact** — not the L1b imprecision claim, and not considered by either earlier pass — makes the observation point genuinely unsupported: reading `Interpreter/Engine.py` directly (not running the case) shows the fixpoint computation's `transfer_function` (used inside `fixpoint()`, the function that processes every node in a loop body) never calls the intent-checking entry point (`_process_node_intents`) for any node — it only propagates variable values. `reinterpret_from()`'s worklist, on reaching a loop head, calls `fixpoint()` and jumps straight to the loop's exit successors; `_process_during_annotations` is only reached for the ordinary (non-loop) branch of that worklist, never for a statement inside the loop body. **A `@During` whose only viable attachment point is inside a loop body is therefore never evaluated by this engine, under any circumstances** — not "evaluated but imprecise," literally never invoked. This is the confirmed exception documented in README §4 R1-7 and the new `delta` tag definition: a fixed, source-verified architectural fact, not a speculative precision judgment, and therefore usable at the R1-7 stage without running the case.
  - R1-4 already establishes there is no viable Post-based alternative (the only candidate, bounding `_actualDeduction`, is rejected on separate, independent grounds — conflating the pool's bug with `compensate()`'s legitimate insolvency behavior). So the *only* relation-and-scope combination that is faithful to R1-1–R1-3 (During, inside the loop, on `_redeemAmount`) is exactly the one the engine cannot evaluate, and no alternative observation point rescues it.

**Outcome: Expressible = NO.**

**Tag: delta** — the relation's content is simple and every value it needs is referenceable (nothing wrong with the relation itself, unlike alpha/beta/gamma); the blocker is purely that its only viable attachment point (inside the `for` loop over `indexList`) is a location this engine's fixpoint/reinterpret architecture never evaluates a `@During` at. See README §4's delta definition and its loop-body confirmed-exception note.

---

## §5 — Value/Algorithm and Usable/Unusable

- **Algorithm-level**: the relation ties together derived intermediate quantities (`_deductionFromIndex`, `_shareOfIndex`) produced by a multi-step fixed-point computation, via the contract's own proportional-allocation recipe — not a raw threshold on one input.
- **Usable** *(third refinement pass — re-confirmed despite Expressible=No)*: every needed value is still referenceable at the would-be annotation's program point; nothing about R1-7's delta finding is a values problem (README §4's note on delta: it can legitimately remain Usable, since Usable/Unusable is purely about value-referenceability, and the blocker here is the observation point, not any value).

---

## RQ2-A — Specification Requirements profile

**Not applicable.** Per README §6, RQ2-A applies only to Expressible cases. This case is Expressible: No (delta, third refinement pass) — no structural profile is recorded. (A profile was computed in the second refinement pass, when this case was still classified Expressible=Yes; that profile is superseded, not reproduced here, to avoid implying it's still an active part of the record.)

---

## §7 — Alternatives-considered summary

| # | Relation | Tier | Expressible? | Discriminates? | Verdict |
|---|----------|------|---------------|-----------------|---------|
| 1 | Monotonicity of `_redeemAmount` in `_credit` across iterations | Directional | No | Would, if expressible | Rejected — no cross-iteration grammar form |
| 2 | `_redeemAmount * MAGIC_SCALE_1E6 <= _deductionFromIndex` | Inequality, no `_shareOfIndex` | Yes | Yes | Rejected — too weak, ignores proportionality |
| 3 | `_redeemAmount <= ceil(_deductionFromIndex * _shareOfIndex, 1e12)` | Inequality, uses `_shareOfIndex` | Yes | Yes | **Selected** |
| 4 | `_redeemAmount == ceil(_deductionFromIndex * _shareOfIndex, 1e12)` | Exact equality | Yes | Yes | Rejected — no added power over #3, over-specifies rounding |

## RQ1-B / RQ2-B

Deferred per README §8. Not run, not predicted.

---

**Summary**: Expressible = **No — delta** (third refinement pass; reversed from the earlier Expressible=Yes conclusion). The relation R1-1–R1-3 establish is exactly right in content, and During (R1-4) is exactly the right scope for it — but the only place that scope can attach is inside the `for` loop over `indexList`, and this engine's `fixpoint()`/`reinterpret_from()` (`Interpreter/Engine.py`) never evaluate a `@During` placed inside a loop body, confirmed by direct source inspection (not speculation about precision/⊤). The relation that *would* have been the target annotation, had the engine supported this observation point:
```
_redeemAmount <= ceil(_deductionFromIndex * _shareOfIndex, 1000000000000)
```
**This is a different failure mode than the retired pipeline's `not_detectable (L1b: loop-body-granularity)` label**, even though the two land on the same practical outcome (not detectable). L1b's own stated reasoning was about join-over-iterations *imprecision* (a claim about what value the analyzer would compute, requiring the engine to actually run) — that reasoning was explicitly and correctly rejected earlier in this same case's history (see the R1-7 section above) as out of scope for R1-7, and that rejection stands. What actually blocks this case is a categorically different, simpler fact: the validation call is never invoked at all for a loop-interior statement, regardless of what value it would compute if it were. Recorded under the new **delta** tag (README §4), not as a vindication of the old L1b reasoning.

**Quantified property instantiated: No** *(reasoning corrected, third refinement pass)* — earlier text here claimed "the engine evaluates a During annotation once per iteration naturally," which is now known to be factually wrong (see R1-7: the engine evaluates it zero times, not once per iteration). The correct reasoning for why this wasn't a collection-quantification problem, independent of engine behavior: the relation's *content* is about one loop-local index at a time, with no cross-index term — this is a property that is naturally per-instance (unlike `web3bugs_83_H_01`'s `@Post`, which picks one representative pool out of several *co-existing* storage entries checked at a single instant). Whether the engine would have actually visited every index, one index, or none is a separate question from whether the annotation's *meaning* requires referencing more than one index — it doesn't. This distinction is now moot for R1-7's verdict (delta blocks the case regardless), but is kept here since it remains the correct characterization of the relation's content.

**Note on the patch (second refinement pass)**: the report does contain an exact Recommendation formula, `_divCeil(_deductionFromIndex * _shareOfIndex, MAGIC_SCALE_1E6 * MAGIC_SCALE_1E6)`, matching the relation's structure exactly (see R1-1). This was discovered *after* R1-1–R1-7 were originally completed against a truncated local copy of the report that appeared to have no patch — the relation was derived independently of the real patch and only found to match it afterward, which is a stronger validation of the abstraction discipline than if the patch had been consulted from the start. (The RQ2-A recount this note originally referenced no longer applies, now that RQ2-A is N/A for this case — see above.)
