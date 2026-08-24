# RQ1/RQ2 Case Analysis Methodology

**This supersedes the old L1–L5 taxonomy and the blind-provenance pipeline (Phase 3–8 in earlier drafts of this file).** Those are retained only as historical/superseded material inside individual case folders (marked as such). The reason for the change, and what replaced it, is below.

## 0. Why the old approach was replaced

The original evaluation used a flat framing — 20/75 cases produced `Violated`, the remaining 55 were bucketed into L1–L5 by *why* they failed, with L5 meaning "expressible but requires bug-awareness." That framing conflated three separate questions:

1. Can the intent model **represent** the bug-relevant intended numeric behavior at all?
2. Given a representable specification and the right analysis inputs, can the **engine validate** it?
3. Could a developer **unaware of the bug** have independently formulated the same specification?

Question 3 (the old L5 / "bug-awareness" axis) turned out not to be answerable with the rigor a paper needs. This session tried, seriously, to build a rigorous version of it — a blind multi-agent pipeline with local/cross-code/domain provenance tiers, a self-substitution exclusion rule, and mandatory critique rounds — and even with all of that, two pilot cases (`web3bugs_45_H_02`, `web3bugs_71_H_11`) remained genuinely disputed between the researcher and the reviewing agents. That's not a methodology bug; it's a sign the underlying question is inherently under-determined by a retrospective study. **The evaluation is retrospective**: annotations are constructed after reading the audit report, so it can never establish what a bug-unaware developer would have done. Trying to force a crisp "L5 yes/no" label out of that is asking the data for more than it can support.

**What replaces it**: split questions 1 and 2 into **RQ1** (Expressibility + Validatability), and move the *content* that used to live in question 3 into **RQ2** (Specification Requirements) — but reframed as a **structural characterization** (how much program context and analysis input a specification needs), not a psychological claim about what a developer would or wouldn't have noticed. Nothing is lost — the old L5 cases don't disappear, they get correctly recognized as **Expressible** (they were never representation failures) and get a richer, more defensible structural profile instead of a contested binary label.

## 0.5. Report source path convention — read this before R1-1 on any `web3bugs_*` case

**Primary/authoritative source: `C:\Users\isjeon\Web3Bugs\reports\<contest_number>.md`.** This is the complete, original, per-contest Code4rena report (every severity tier — High/Medium/Low/Non-Critical/Gas — in one file). Get `<contest_number>` from the case ID: `web3bugs_<contest_number>_H_<finding_number>` (all cases in this dataset are High-severity, so always an `H-<finding_number>` heading). Within the file, find the finding's own section by its heading, `## [[H-<finding_number>] ...]`.

**Do not default to `Dataset/Web3Bugs/.../contest_<id>_H_<n>/README.md`** (the scattered, per-finding excerpt files used earlier in this project). They are **not reliable** — confirmed truncated (missing Proof-of-Concept and Recommendation sections entirely) for at least `web3bugs_71_H_11` and `web3bugs_83_H_01`, discovered only because a user manually supplied the real report text and it contradicted what Agent A/B had concluded from the local file. Given 2 of the first 3 pilot cases checked were truncated, treat every one of these scattered files as unverified until cross-checked against `Web3Bugs/reports/<contest_number>.md`. If a discrepancy is found between the two, `Web3Bugs/reports/` wins and the scattered file should be corrected to match (see `web3bugs_71_H_11`'s and `web3bugs_83_H_01`'s `Dataset/Web3Bugs/.../README.md` for the pattern of what a fix looks like).

This convention applies only to `web3bugs_*` cases (Code4rena/Web3Bugs sourced). `numscout_*`/`flyinointment_*` cases keep using their existing dataset sources (`Dataset/Numscout/`, `Dataset/Flyinointment/`) — this truncation issue has not been checked for those and is a separate, lower-priority question if it comes up.

## 1. Dataset scope

- 89 collected instances → 14 excluded → **75 eligible instances**. Do not reintroduce the 14 excluded cases into RQ1 (they fail the paper's Numeric Logic Error definition, are multi-transaction, are duplicates, or are not reproducible — e.g. Solidity ≥0.8 overflow/underflow cases that revert don't qualify, since the NLE definition requires the transaction to complete without a runtime exception).
- Of the 75: **20** already produced `Violated` under existing annotations (treat as Expressible=Yes, RQ1-B=Violated, by construction — no need to re-run Phase R1-1–R1-7 on these, though they still eventually want an RQ2-A structural profile for completeness).
- The remaining **55** break down as: former L1–L3 = 21, L5 = 14, L4 = 20. **L1–L3 (21) and L5 (14), all 35, have no existing usable annotation and must go through Phase R1-1–R1-7 fresh.** Do **not** assume former L1–L3 cases are automatically Expressible just because their old label implied an engine-precision problem rather than a grammar problem — R1-7 must be (re)established for every one of them, same as former L5 cases.
- **The 20 former-L4 cases are a special, mostly-lighter-lift case** — they already have detailed per-case reasoning in `evaluation/RQ2/l4_l5_case_review_(kor).md` and a final verdict in `evaluation/RQ2/l4_l5_classification.py` (`final_class`). Triage instead of blanket re-running:
  - **~9 cases with `proxy_type=B` and no `reclass_reason`** (the value genuinely has no in-scope proxy, e.g. `web3bugs_25_H_05`, `29_H_05`, `51_H_04`, `51_H_06`, `61_H_04`, `83_H_02`, `52_H_15`): safe to carry forward as-is. A weaker/abstracted relation (R1-2/R1-3) can't manufacture an in-scope reference that doesn't exist.
  - **The `l4a_axis="alpha"` subset** (needs a function call inside the relation — most of L4a): re-check specifically for a Nokon-style rescue (§4, R1-3) — a *known bound/constant* on the call's result, rather than the call itself, might still discriminate. Verified once already for `web3bugs_59_H_05` (see below) — the function-call blocker held because the needed values were genuinely external-contract state (Type B), not because no bound existed; don't assume every alpha case resolves the same way, check each.
  - **The ~10 cases with a `reclass_reason` recording an `annotation_plans.md` vs. `limitation_types.md`/case-review disagreement** (`59_H_05`, `61_H_01`, `61_H_02`, `17_H_02`, `52_H_15`, `52_H_16`, `58_H_04`, `62_H_01`, `70_H_08`, `110_H_01`): spot-checked one (`59_H_05`) directly — the existing case-review reasoning already correctly separates "the arg is wrong" (bug-awareness, irrelevant now) from "can the correct value be grammar-expressed from in-scope values" (expressibility, the only relevant question), and lands on L4a for the right reason (Type B — the correct value is another contract's state, unreachable without a call). This is **not** a case of a stale document being blindly trusted — the existing reasoning already matches this session's RQ1/RQ2 discipline. Re-express these ~10 in the new R1-1–R1-7 / alpha-beta-gamma vocabulary (§4) as a verification pass, not a from-scratch Agent A/B run, unless the re-expression surfaces an actual disagreement.
  - **`35_H_10` (L4c) and `36_H_02` (L4d)**, `proxy_type=A`: genuinely in-scope values, pure grammar-form limitation. Carry forward as-is.

## 2. Patch/fix access — allowed, with discipline

Full access to the audit report, including any recommended fix/patch, is permitted in Phase R1-1. This benchmark's ground truth *is* the audit report; refusing to read the patch doesn't produce a purer signal, it just starves the analysis of the only concrete anchor for "intended behavior" that exists for most cases. The discipline that matters is downstream, not access-related: **do not mechanically transcribe the patch's literal syntax into the annotation** — abstract first (R1-2/R1-3), and prefer program-native terms over patch terms only where a genuinely independent, equally-discriminating alternative exists (this is a synthesis-quality question, not a classification gate — see §3 below for why literal patch-matching does not by itself indicate anything).

## 3. What we explicitly do NOT classify anymore

- No "bug-awareness required / not required" label.
- No A/B/C1/C2 knowledge-provenance tiers.
- No blind agent separation between "ground truth" and "provenance" phases — there is no provenance claim left to protect via blindness.
- No inference from **whether the final annotation's syntax happens to match the patch**. This was tested directly against real data during this session: `web3bugs_5_H_07`/`5_H_08` use annotations that are *verbatim identical* to an in-function comment's stated formula, which is about as "literal" as it gets, yet are unambiguously local/non-external in origin (the comment states it directly) — literal-syntax-match tracks nothing reliable about provenance, in either direction.
- No "self-substitution" of a disputed statement into itself, treated as independent support — this specific fallacy is now relevant to **RQ2-A's context-counting metric** (§6), not to a classification decision: don't let a circular derivation inflate or deflate the "relevant statements" count.

## 4. The phases (Agent A performs these, R1-1 → R1-7, in one continuous pass)

### R1-1 — Reported Behavior Reconstruction

Inputs: audit report (full), original buggy source, recommended fix/patch if present, relevant contract context.

Identify, **only to the depth actually needed** for this specific case (never force every item — an irrelevant level, especially contract-level role, should be skipped, not guessed at, to avoid hallucination):
- Contract role (only if relevant)
- Function role
- Relevant state/local variable semantic roles (only the ones the bug touches)
- Statement-level behavior — kept as two distinct sub-questions, not conflated:
  - **Variable-value intent**: the range/value intent of this specific value at this line (usually the lvalue, sometimes a sub-expression of the RHS, sometimes the whole RHS).
  - **Statement/line-level intent**: what function-wide invariant this statement is trying to uphold, independent of the exact arithmetic.
- Reported erroneous behavior
- Expected/intended behavior (as stated or implied by the report)
- Patch intent, if a patch exists — read as evidence of intended behavior, not as annotation source text

Output: **bug-relevant intended numeric behavior**, in prose. Prefer "bug-relevant intended numeric behavior" / "intended numeric relation" over "the developer's actual intent" — audits sometimes have disputed intent (sponsor vs. auditor).

### R1-2 — Intent Abstraction

Drop the patch's literal syntax. Governing question: *what numeric property distinguishes the reported buggy behavior from the intended behavior?*

Decide the intent-level orientation (a synthesis aid, not a taxonomy that needs reporting):
- **Value-centered**: a constraint on a specific value/expression (`returnExpression >= 363`, `transfer.arg[0] > 0`).
- **Effect/state-transition-centered**: the effect executing the statement/function must have on state (`weiRaised(Entry > Exit)`, `changed(previousPrices[0], true)`).

### R1-3 — Select the least implementation-specific sufficient relation

Try, roughly in this order, but **this is not "always pick the weakest"**:
1. Directional/state-change relation
2. Inequality / bound
3. Relational invariant
4. Exact equality

Selection condition: **the least implementation-specific relation that is (a) supported by the reported intended behavior, (b) expressible using program observables, and (c) still sufficient to reject the buggy behavior while accepting the intended one.** If only an exact equality actually discriminates (a looser bound would be satisfied by buggy outputs too), use the equality — don't weaken past the point of losing discriminating power. Record the alternatives considered and why the selected one won — this is required (§7), not optional color, because this freedom is exactly where researcher-degrees-of-freedom risk lives.

**Required check before finalizing the selection: does the candidate's negation fail to catch at least one alternative implementation that still retains the reported defect but produces it differently** (e.g., performs the right-looking side effect at the wrong point in execution, or using the wrong operand/rate)**?** If so, the relation is still a legitimate R1-3 selection — the sufficiency condition above only requires discriminating the *actual observed buggy code* from *one* reconstructed intended scenario, not rejecting every conceivable defect-retaining alternative — but it is **incomplete** relative to the fully reported intent. Record this explicitly as `Intent coverage: Partial` (§10); don't fold it silently into the relation write-up. This is the same category of required, expected-to-recur check as R1-6's collection-quantification note (§4) — not a special case that only applies when something feels off.

**Implementation-specificity is judged by how tightly the relation depends on the exact patched arithmetic or statement structure, not merely by operator strength.** Don't treat "it uses `<=` instead of `==`" as automatically less implementation-specific — a bound built from an oddly-specific intermediate quantity can be just as tied to the patch's particular implementation as an equality would be. Judge each candidate on what it actually depends on, not on its operator.

**Before concluding a relation needs a function call inside it (which would force Inexpressible, since `intentValue` cannot contain calls): check whether a known bound/constant on that call's result — not the call itself — still discriminates.** This is not hypothetical; it's how `numscout_Nokon`'s already-published annotation works (`amountToBuy * ethRateFix >= msg.value * 250000` avoids calling `calculateRate()` by using its known minimum instead). Try this before declaring Inexpressible for that reason. It won't always work — e.g. `web3bugs_59_H_05` was checked for exactly this and still failed, because the needed values (`userMaltPurchased`, `userCommitment`) are another contract's state with no in-scope proxy at all, not just a call result with a known bound — but it must be tried, not skipped.

**When a discrimination argument leans on a non-negativity/bound fact, separate what's unconditionally true by typing from what depends on revert-not-wrap casting semantics — don't blanket-state either way.** A claim like "`fee` is always `>= 0`" is often really two different claims bundled together:
- A value that's still an unsigned type (e.g. the raw result of a `uint256` fixed-point multiplication) is non-negative **unconditionally, by pure type construction** — `uint256` cannot represent a negative number at all, independent of any execution-semantics assumption.
- Once that value is *cast* to a signed type (e.g. `.toInt256()`), whether it stays non-negative additionally depends on the cast reverting (rather than silently wrapping) when the source value exceeds the target type's max — this part is **only true on successful (non-reverting) executions**, not a bare type guarantee.

State each sub-claim at its actual precision level (e.g. "the `uint256` multiplication result is non-negative by construction; the subsequent cast to `int256` preserves this on any execution that completes without reverting"). This isn't pedantry — the successful-execution scoping matches the paper's own Numeric Logic Error definition (§1: the transaction must complete without a runtime exception), so it's the *correct* scope for the cast-dependent half, not a hedge.

### R1-4 — Choose annotation observation scope (During vs Post)

- **During**: the relation concerns an intermediate expression, a call argument, a statement-time value, a before/current/after relation tied to one statement.
- **Post**: the relation concerns function entry vs exit, final state, a return value, a persistent state transition, a function-level invariant.

**Do not choose During merely because the patch modifies one statement, and do not choose Post merely because the report describes a function-level consequence.** Two real cases in this project's already-published set make this concrete: `SwordCrowdsale`'s patch is the single assignment `weiRaised -= amount`, and `CDP.update`'s patch is `totalCredit += delta` — both assignment-shaped, and both ended up as **Post** with a directional Entry/Exit relation, not During-equality. Let the relation's nature (from R1-2/R1-3) drive the choice.

### R1-5 — Choose relation form

Classify explicitly (bookkeeping, feeds into R1-6 and the record, not a separate judgment call): exact equality / inequality (upper or lower bound) / Entry-Exit / Before-After / changed-unchanged / return-value relation / call-argument relation / implication / feasibility property.

**Patch syntax does not determine relation form.** An assignment patch does not imply the annotation must be an equality.

### R1-6 — Construct the target annotation

Express the R1-2/R1-3 relation, at the R1-4 scope, in current grammar (`paper/first_revision/main.tex`, `\label{fig:intent-grammar}`).

- When exact equality is genuinely needed: prefer semantically meaningful in-scope values (state variables, parameters, locals, return values) over mechanically reproducing the patch's exact expression — *unless* that exact expression is genuinely the correct specification, in which case use it (matching the patch is not itself a problem; see §3).
- When a concrete constant is needed (a number that appears nowhere in the source): document how it was derived — which specific scenario/input values, combined with the abstract relation, produced it. E.g. `_allowances[1][101] == 900` is not just syntax; `900` must be traceable to a specific validation scenario, not asserted from nowhere.
- **When the reported/intended property is naturally quantified over a collection** (e.g. "every existing pool," "all users with a position") **but the grammar has no universal-quantification construct** (confirmed against the grammar: the only `∀`/`∃` in `main.tex`'s semantics are internal to the analysis engine's own path-quantification for `changed`/entry-exit evaluation *within one execution* — nothing lets an annotation itself range over an array/mapping) — the target annotation necessarily instantiates the property on one concrete representative element. **State this explicitly** (which element, and why it's representative for the constructed scenario — e.g. "the one with pending unsynced rewards in this scenario") rather than writing the record as if the annotation captured the fully general claim. This affects how R1-7 is phrased, not whether it's Expressible — see R1-7.

Output: **fixed target annotation** (text + attachment point + relation form used).

### R1-7 — Expressibility decision

Question: *can the current grammar represent the R1-2/R1-3 relation, as constructed in R1-6, without changing its semantics?*

**Scope of "Expressible" — read carefully.** This asks whether a relation *sufficient to discriminate the reported buggy behavior from one reconstructed intended scenario* (R1-3's sufficiency condition, §3) can be represented — not whether the annotation fully specifies every semantic condition described in the audit report. A case can be legitimately Expressible=Yes while the selected relation only partially covers the reported intent (e.g., it checks that a required side effect occurred, without checking that the effect used the specific input/ordering the report identifies as the actual mechanism of the defect). When this happens, it must be flagged explicitly via the `Intent coverage` field (§10) — never left implicit inside a bare "Expressible: Yes."

Consider only: can the required values be referenced at a legal program point, can the arithmetic/logical relation be represented, is the required observation point supported. Do **not** consider: whether a developer would know to write it, whether the report was needed to discover it, whether the engine can validate it, whether abstract interpretation would produce ⊤, "would they have avoided the bug if they'd known."

**One narrow, empirically-confirmed exception to "do not consider whether the engine can validate it": loop-body `@During` placement.** This is not a precision/⊤ question (which genuinely requires running the engine to know) — it's a confirmed architectural fact, verified by reading `Interpreter/Engine.py` directly (not by running a case): the fixpoint computation's `transfer_function` (used inside `fixpoint()`) never calls the intent-checking entry point for any node, and `reinterpret_from()`'s worklist explicitly treats a loop head as "call `fixpoint()`, then jump straight to its exit's successors" — `_process_during_annotations` is only reached for nodes outside that jump, i.e. never for a statement inside a loop body. So a `@During` whose only viable attachment point is inside a loop body is never evaluated by this engine, under any circumstances — not "sometimes produces ⊤," never invoked at all. Because this is a fixed, already-known fact rather than something that requires speculating about a specific case's abstract-interpretation behavior, R1-7 may use it directly: if the R1-3-selected relation's only viable observation point is inside a loop body, the required observation point is **not supported**, regardless of how simple the relation's own content is.

**If R1-6 instantiated a collection-quantified property on one concrete element** (per R1-6's quantification note): the Expressible verdict here means *expressible under that concrete instantiation*, not that the fully general, universally-quantified property is expressible — the grammar's lack of a quantifier is a real, permanent gap, just not one that blocks this narrower claim. Say so explicitly rather than letting "Expressible: Yes" imply more than it does.

**Most During/Post relations in this benchmark are implicitly scenario-conditioned, not unconditional invariants** — they hold given the preconditions the R1-6 concrete scenario establishes (e.g. nonzero balances, elapsed time, a particular branch reachable), not for every possible program state. This is expected, not a defect — RQ1-B's debug/batch-annotation instantiation exists precisely to supply such scenarios. State the relation's actual conditioning explicitly in the record (what precondition makes it hold) rather than describing it as a bare "function-level invariant," which overclaims generality.

Outcome: **Expressible** (→ counted toward RQ1's expressibility rate; proceed to RQ2-A profiling and, separately/later, RQ1-B). **Inexpressible** → record the specific grammar/scope fact that blocks it, tagged with one of these (alpha/beta/gamma adopted from the existing, already-battle-tested `evaluation/RQ2/l4_l5_classification.py` axis; delta added this session, see below — do not invent further new tags without the same level of empirical grounding):
- **alpha** — the relation needs a function call inside `intentValue`, which the grammar disallows, and no known-bound rescue (R1-3) closes the gap.
- **beta** — no in-scope variable/expression exists to reference the needed value at all.
- **gamma** — the relation is inherently multi-point/structural (spans multiple statements or an accounting relationship the grammar's single-relation forms can't capture), independent of any single missing value.
- **delta** — the relation's content is simple and single-point, and every value it needs is referenceable — but the only viable attachment point is a location the current engine architecturally never evaluates (currently: inside a loop body, per the confirmed exception above). Unlike alpha/beta/gamma, this is not about the relation's own form or the values it needs — it's specifically about observation-point support. Do not use this tag speculatively ("might not be well-precision-supported") — only for confirmed, source-verified "never evaluated" facts, matching the same bar as the loop-body finding above.
- A case can be `alpha_and_gamma` etc. if more than one applies.

This tag is purely descriptive (why it's currently inexpressible under the existing grammar/engine) — do not speculate about what a future grammar or engine extension would enable; describe the current intent model and, for delta specifically, the current engine only.

**Note on delta and Usable/Unusable (§5)**: unlike alpha/beta/gamma, a delta case can legitimately still be **Usable** — §5's Usable/Unusable axis is purely about whether the needed values are referenceable, and for delta they are (that was never the problem). Don't default to "Unusable" out of habit; assess §5 independently for delta cases.

## 5. RQ1 explanatory axes — Value/Algorithm and Usable/Unusable (retained)

This is the axis pair behind the finding Reviewer 2 explicitly praised, and it survives this restructuring — it just gets applied to the correct (larger) set of Expressible cases instead of being entangled with the retired bug-awareness label.

- **Value-level vs Algorithm-level**: the existing abstraction-level classification already defined in the paper.
- **Usable vs Unusable**: whether the values needed to represent the intended relation are referenceable in a form the intent model can use, *purely a representational-resources question*. **Do not equate** Usable with "developer could discover it" or Unusable with "developer couldn't understand the bug" — that conflation is exactly the mistake this restructuring removes.

Expected shape of the finding, restated without L5: cases that are Usable and still weren't originally counted as successes were never representation failures — they were misclassified as failures by the old flat taxonomy. Cases that are Unusable are inexpressible regardless of anything else.

## 6. RQ2-A — Specification Requirements (replaces the old L5/bug-awareness question)

Applies to every Expressible case. The question is never *"did the developer need to know about the bug"* — it's *"how much program context and analysis input does formulating and validating this specification actually involve."* This is a structural profile, not a difficulty score.

Candidate metrics (pilot on a diverse subset first — §9 — keep only ones that vary meaningfully and are consistently operationalizable):
- **Relevant statements** (a.k.a. specification-relevant statements — the name matters, see below): statements **within the annotated function itself** that (a) define the values appearing in the target relation, (b) determine control conditions affecting those definitions, or (c) establish an independent constraint the relation's *soundness* depends on, even if that constraint's own variables never appear in the annotation text — e.g. a same-function statement establishing a non-negativity fact the bound's validity rests on. Not raw LOC above the bug line. No formal (a)/(b)/(c) labeling is required in the record — where a statement's relevance isn't obvious from the annotation text alone (most often (c)-type entries, or a control-gating statement), add a short inline note saying why, same as the record already does in prose; a rigid two-category taxonomy turned out to add bookkeeping without adding information a plain one-line explanation didn't already carry.
  - **A call to another function — same-contract or cross-contract — is never expanded into that function's own internal statements here.** The call is counted once, as a unit, under "Additional functions required" below, with the specific load-bearing property stated there (Step 1/2). Do not itemize the called function's internal lines into this count. This resolves a real inconsistency found across the pilot cases: `web3bugs_16_H_04`'s original count drilled into `getFee`'s internal lines while `web3bugs_71_H_11`'s did not drill into `IndexTemplate.compensate()`'s — same-contract and cross-contract calls were being treated differently for no principled reason, and unbounded drilling has no natural stopping rule for deeper call chains anyway. (This also means the old motivating example for the retired (a)/(b) vs (c) labeling — `getFee`'s two internal lines — no longer appears in `web3bugs_16_H_04`'s count at all; see that case's updated record.)
  - **No missing-call exception.** A required function is treated as an atomic dependency regardless of whether the buggy implementation actually calls it, or is precisely the function whose *missing* invocation constitutes the defect (e.g. `web3bugs_83_H_01`, where the entire discrimination argument lives inside an un-called `updatePool`/`getMultiplier`). Carving out a bug-pattern-specific exception here would reintroduce, in a different shape, the same inconsistency this rule exists to remove.
  - **No recursive counting.** Statements and values internal to an atomically-represented additional function are excluded from "Relevant statements" and "Unique relevant program values," full stop, independent of how large or small that function is or whether it's actually executed on the buggy path.
  - **Mandatory semantic-dependency note.** Every entry under "Additional functions required" (and "Additional protocol/application-specific contracts/libraries required") must state, in one line, the specific behavioral guarantee the selected relation depends on — not just a bare name and count. This is what carries the information that a recursive statement count used to carry; a bare `Additional functions required: 2` with no accompanying explanation is an incomplete record.
  - **Accordingly, "Relevant statements" and "Unique relevant program values" are not a measure of everything that had to be read or inspected** — they measure the directly-counted local context at the scope being analyzed; program context reached by crossing a function boundary is represented atomically, in a separate part of the profile, not folded into these two counts. A case where these two numbers are small because most of its dependency sits behind other functions' semantics (rather than because little context was needed overall) is showing a real feature of that case's structure, not a measurement gap — see `web3bugs_83_H_01` for a worked example.
  - **A statement inspected "to confirm the scenario is reachable" is not automatically reachability-only — check whether it also redefines a value the relation depends on.** These are two different things that look similar during R1-1/R1-3 exploration (both involve reading code beyond the disputed statement) but must be classified separately: a `require(...)` or other pure boolean gate that doesn't assign anything is reachability-only and correctly excluded; a conditional block that *reassigns* a variable later consumed by the relation's operand chain (e.g. `if (cond) { x = f(...); }` where `x` feeds into a value the relation references) is (a)-type and must be counted, even though it was first noticed while checking reachability. Found and corrected in `web3bugs_42_H_01`: two `if`-blocks that conditionally cap `_amount` before `increasingDebt = (_amount * 1005) / 1000;` were originally lumped in with two unrelated `require(...)` reachability gates under one blanket exclusion — the capping blocks redefine `_amount`, an operand in the relation's derivation chain, and belong in the count; the `require`s genuinely don't redefine anything and stay excluded. Don't let "I only looked at this to check reachability" become an excuse to skip re-checking whether it also happens to be a definition.
  - **Do not count algebraic self-substitution of the disputed buggy formula as a relevant statement** — rewriting a buggy formula into itself reproduces whatever it computes regardless of correctness and adds no real information. **This is not the same question as whether the disputed/target statement itself is counted.** It is — the statement that defines/assigns the constrained value is context you must read to know the annotation's attachment point and subject, and belongs in this count like any other statement in the annotated function. What's barred is treating that statement's *own algebra, substituted into itself*, as independent evidence *for* the relation — the statement counts as context, never as self-justifying evidence. Apply consistently across cases.
- **Unique relevant program values**: all distinct program values, **within the annotated function's own scope**, occurring in the statements counted above — **including the constrained target value itself** (e.g. the lvalue the annotation bounds), not only the values on the relation's other side. Values that only exist inside a called function's own body are not enumerated here (same scoping rule as above) — their existence is covered by "Additional functions required." Optionally split by state variable / parameter / local / return value if that subtyping turns out to vary usefully.
- **Additional functions required** (not "inspected" — see Step 1 below) outside the target function.
- **Additional protocol/application-specific contracts/libraries required** (renamed for consistency with Step 2 below — generic library dependencies are handled there as case notes, not counted here).
- **Context breadth** (ordinal): 0 = target statement/expression only, 1 = same-function context, 2 = other function(s) in same contract/library, 3 = cross-contract/library, 4 = external protocol/domain specification.
- **External specification required** (boolean/categorical) — source alone insufficient, protocol/accounting/unit/business convention needed. This is a description of *information source*, not a claim about bug-awareness. **The audit report itself never counts here.** R1-1 legitimately reads the report for every single case (§2) — if that counted as "external specification," this field would read "Yes" for 100% of cases and carry no information. This field asks a narrower, later question: *once R1-1/R1-2 have already fixed the intended behavior, does justifying/instantiating the specific selected relation additionally require protocol/business/domain convention beyond the source code and language semantics* — not how the intended behavior was originally identified. **Generic language/library semantics handled under Step 2 below do not, by themselves, make this field "Yes."** A case that only needed SafeMath's overflow-check behavior or a fixed-point library's rounding convention (Step 2: generic, case-note-only) still answers "No" here — those facts are protocol-independent, not the protocol/business convention this field is asking about.

**Counting any cross-code entity ("Additional functions/contracts," "Context breadth," or a case note) is a two-step decision — apply in order:**

**Step 1 — load-bearing filter.** Was a function/contract/library actually inspected only in passing, or does the *selected* relation's derivation genuinely depend on its specific behavior? Operational test: ***if the entity's relevant semantic guarantee were changed — while remaining consistent with everything else already known about it from the analysis — would the target relation's derivation or validity change?*** (Not "if it behaved as literally any value consistent with its raw type signature" — that framing is too permissive and would make almost anything touched look load-bearing, since swapping in arbitrary garbage breaks nearly every downstream computation trivially. Test the *specific property actually being relied on* — e.g. "reverts rather than wraps on overflow," "ceiling rather than floor division," "may pay less than requested under insolvency" — not the entity's entire implementation.) If changing that specific guarantee wouldn't move the needle — the entity was read/called/imported along the way but never actually fed into the R1-1–R1-6 argument (e.g. an unrelated modifier on the same function, a helper touched while exploring but not relied on) — **don't count it anywhere, not even as a case note.** It's not part of the record at all. If yes, proceed to Step 2.

**Corollary — alternative-rejection inspection doesn't count.** R1-3 often requires inspecting extra code specifically to *reject* a candidate relation (why alternative X doesn't discriminate, or is itself non-viable for some other reason) — keep that reasoning fully documented in the R1-3/§7 alternatives write-up, but it does not, by itself, make the inspected entity load-bearing for RQ2-A. Apply Step 1 to the *selected* relation only: would rejecting-alternative-X's entity behaving differently change the *selected* relation's own derivation or validity? If the answer is no — the investigation only affected which alternative got picked, not whether the winner is sound — exclude it from the counted metrics, same as any other non-load-bearing entity. (`web3bugs_83_H_01`'s pool-0/`address(0)`-revert investigation is the worked example: essential to reject two candidate relations in R1-3, irrelevant to constructing/verifying the one actually selected.)

**Step 2 — generic vs. protocol-specific bucket** (only for entities that passed Step 1). Distinguish two kinds of load-bearing "had to look elsewhere" facts:
- **Semantic program context** — understanding *this contract's* business/accounting logic (a sibling function's formula, another contract's state layout). Counts normally toward "Additional functions/contracts" and "Context breadth."
- **Language/library-semantics dependency** — a generic, protocol-independent arithmetic/type-safety fact (SafeMath's overflow-checked `.add()`, a fixed-point math library's `.mul()`, a safe-casting helper's revert-on-overflow behavior) that would hold identically regardless of which contract calls it. Record as a **case note** instead — it *is* part of the argument (it passed Step 1), just not counted in the numeric/ordinal metrics. **Being load-bearing and being generic are independent properties, not the same test** — a fact can be both (e.g. a safe-cast helper's revert-not-wrap behavior is often exactly this: the argument really does depend on it, and it's also a completely generic property with nothing protocol-specific about it). Don't write off a load-bearing generic fact as "not load-bearing" just because it belongs in the case-note bucket — say why it's excluded (generic) rather than implying it wasn't needed at all.

The reason the Step 2 split matters: SafeMath-style wrappers and fixed-point libraries (PRBMath, etc.) are near-ubiquitous in this dataset. Counting every one would push "Additional libraries"/"Context breadth" to 2+ for nearly every case, and the metric would stop discriminating between cases that genuinely needed cross-function/cross-contract business understanding and cases that just used an ordinary safety wrapper. The test for which bucket a library fact falls in: would understanding it require knowing anything specific to *this* protocol/contract, or is it a domain-independent primitive that behaves the same in any contract that imports it? A custom AMM library's specific rounding convention, if the bug hinges on it, is protocol-specific — count it. A generic overflow-checked `.add()` is not — note it only (but it still had to pass Step 1 to earn even that).

**Do not combine these into one weighted score** — there is no defensible weighting, and they have different units/meanings. Report as a **specification profile** per case, not a scalar.

## 7. Required transparency field: alternatives considered

For every case, record: the target relation actually selected, the alternatives considered at R1-3 (weaker and/or more patch-specific), and why the selected one won. This exists because R1-2/R1-3's freedom to choose among directional/bound/equality forms is necessary (to avoid patch-copying) but also opens real researcher-degrees-of-freedom risk — without a recorded rationale there's no answer to "why did this case get a convenient inequality and that one an exact equality, other than it worked out."

## 8. Deferred, separate tracks (not part of this pass — do not use the analysis tool yet)

- **RQ1-B — Engine Validatability.** For each Expressible case selected for this track: build a real executable test input (batch/debug annotations, concrete or Z3-derived values) and **actually run it** — do not predict engine behavior by reading `Interpreter/Engine.py`'s source (this was tried once for `web3bugs_45_H_02` and explicitly retired as too weak a form of evidence; see that case folder's `phase7_engine_validatability.md`, kept as historical background only). Outcomes: `Violated` / `Warning` (imprecision — widening, ⊤, unresolved calls) / `Unsupported` (the required observation/granularity genuinely isn't available — note loops are *not* automatically Unsupported; IntentChecker already handles some loop cases, this applies only when the specific required observation can't be evaluated at the engine's available granularity). **Explicitly deferred until after the R1-1–R1-7 pass is done and reviewed on this session's pilot batch.**
- **RQ2-B — Analysis Cost.** Actual measured runtime (multiple repetitions, median + dispersion, not just 3 runs), covering both definite `Violated` paths and executable `Warning` paths (Reviewer 2 specifically flagged that widening/fixpoint-heavy `Warning` paths may have different runtime characteristics than the original 20). Also deferred.

Do not mix predicted outcomes into either of these once they're started — empirical fields only.

## 9. Agent roles and process

Two roles per case, run sequentially. No blindness requirement anymore (there's no provenance claim left to protect) — both agents see everything (report, patch, full contract, `Dependencies/` as needed).

- **Agent A — Analyst.** Performs R1-1 → R1-7 in one pass, records the full reasoning trace (not just final answers — Agent B needs to see *why*, not just *what*), drafts the RQ2-A structural profile for Expressible cases.
- **Agent B — Reviewer.** One review pass (not a multi-round rebuttal chain — most of what a rebuttal chain was protecting against was epistemic-provenance subtlety, which no longer exists as a classification target). Checklist:
  1. **Discrimination check**: does the selected relation, on Agent A's own concrete scenario, actually distinguish buggy from intended? Agent A/B should state the scenario and arithmetic explicitly (not just assert the conclusion) — this project has at least one documented case (`web3bugs_71_H_11`'s early `gate1_reviews` pilot) of an agent-proposed annotation containing a real arithmetic error, so don't take a self-reported "yes it discriminates" at face value. (A plain-arithmetic sanity re-check — not running IntentChecker itself, just verifying the stated numbers — is planned as a later hardening step; not required for this pass.)
  2. **Relation-strength appropriateness**: could a weaker relation have worked (was equality reached for out of habit)? Does the chosen relation actually still discriminate, or was it weakened too far?
  3. **During/Post and relation-form justification**: driven by the relation's nature, not the patch's syntactic shape.
  4. **Expressibility correctness**: are the referenced values genuinely in scope at that program point; no smuggled function calls.
  5. **Self-substitution contamination**: in the target-relation derivation or the RQ2-A backward slice, is anything circularly derived from the disputed statement itself?
  6. **RQ2-A scope sanity**: is the backward slice over- or under-inclusive?
  
  Output: approve, or specific corrections tied to a specific R1-phase.
- **Claude (orchestrator)**: prepares each case's packet (source, report, patch, grammar reference), dispatches Agent A then Agent B, reconciles Agent B's corrections into the final per-case record. Does not itself make the classification calls.

Different cases can run in parallel (independent); within a case, Agent A must finish before Agent B starts.

## 10. Per-case record format

- Case ID, contract, function, existing error-pattern label (if any)
- Value-level / Algorithm-level
- Reported erroneous behavior; bug-relevant intended behavior (R1-1)
- Alternatives considered and why the selected relation won (R1-3, required — see §7)
- Target relation, intent-level orientation, During/Post + why, relation form (R1-2–R1-5)
- Final target annotation + attachment point (R1-6)
- Expressible: Yes/No + rationale (R1-7); if No, alpha/beta/gamma tag(s) (§4, R1-7)
- **Quantified property instantiated: Yes/No** — transparency flag, not a new judged metric: Yes if R1-6 had to instantiate a collection-quantified reported property (e.g. "every existing pool") on one concrete representative element because the grammar has no quantifier (R1-6's quantification note), No otherwise. Exists so the aggregate table can report e.g. "X of Y expressible cases required concrete instantiation" rather than silently folding this into a bare Expressible=Yes.
- **Intent coverage: Full/Partial** — transparency flag, distinct from the quantification flag above (that one is about *breadth* — how many pools/elements; this one is about *depth* — how much of the reported mechanism the relation actually verifies for the one instance it does check). Partial if the selected relation only checks a *necessary* condition of the reported intent (e.g., "some change occurred") without checking that the change reflects the specific mechanism/ordering/value the report identifies as the actual defect (R1-3's required check, §3); Full if the relation's discrimination directly tracks the reported defect's mechanism, not merely a symptom of it. A case being Expressible=Yes and Intent coverage=Partial simultaneously is expected, not a contradiction — see R1-7's scope note (§4).
- Usable/Unusable + rationale (§5)
- RQ2-A specification profile (§6) — for Expressible cases
- RQ1-B / RQ2-B fields — left blank/marked "deferred" until that track starts; never mix a predicted outcome in here

## 11. Threats to Validity (for eventual inclusion in the paper)

> The annotations are constructed retrospectively from reported defects; recommended fixes are consulted when available. Consequently, the evaluation characterizes the representational capacity of the intent model and the behavior of the analyzer given an appropriate intent specification — it does not establish that a developer unaware of the bug would independently formulate the same specification. The program-context and specification-input measures (RQ2-A) characterize structural requirements, not measured human effort, time, or cognitive load; an independent developer study would be required to answer those questions directly.

## 12. Status

- Old per-case files (`web3bugs_45_H_02/phase1_2_ground_truth.md`, `phase3_local_evidence.md`, `phase7_engine_validatability.md`, `phase9_final_record.md`, and the equivalent `web3bugs_71_H_11/` files) are **historical/superseded** — produced under the retired blind-provenance methodology. Not deleted, but not authoritative; both cases need a fresh R1-1–R1-7 + RQ2-A pass under this methodology.
- Nothing has been run under this methodology yet. Next step: select a diverse pilot batch (a handful of cases spanning the old L1/L2/L3/L4/L5 labels) to stress-test R1-1–R1-7 and the Agent A/B process before scaling to all 55.
