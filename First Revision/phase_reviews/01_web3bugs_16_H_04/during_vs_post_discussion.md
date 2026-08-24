# Discussion — During vs. Post for `web3bugs_16_H_04`

Not part of Agent A/B's pipeline. A design-choice discussion between the user and Claude, conducted after `analysis.md`/`review.md` were finalized, while the user was independently reviewing this case. Recorded here for traceability since it touches a general methodological question (R1-4, and the retired L5 classification) that may recur in other cases.

## The question

Current selected form (R1-4 in `analysis.md`): `@During newQuote <= position.quote - quoteChange`, attached immediately after `newQuote = position.quote - quoteChange + fee;` inside the `Long` branch only.

User's proposal: attach the *same relation* as `@Post` instead, at the function's return point, and neutralize the `Long`/`Short` branch ambiguity by pinning `trade.side == Perpetuals.Side.Long` via a debug annotation — reasoning that a function-exit postcondition is closer to how a developer would naturally think about debugging this function's contract than a check buried mid-function inside one branch.

## Round 1 — Claude's initial technical objections

1. **σ_exit is formally a joined state.** `paper/first_revision/main.tex` (~line 448) defines `σ_exit` as "joined state at normal function exit." If `newQuote` is evaluated there without conditioning, the value merges the `Long` and `Short` branch outcomes. Concretely: the `Short` branch's own correct value is `position.quote + quoteChange - fee`, which generally does **not** satisfy `<= position.quote - quoteChange` (reduces to `2*quoteChange <= fee`, false whenever `quoteChange > fee`, the common case). So checking the relation at the unconditioned join point isn't just "less natural placement" — the claim is actually false there.
2. **Enum-typed debug annotation for `trade.side` is not evidenced in the grammar.** Every debug-annotation example in `main.tex` (§ "Examples of Intent Annotation Usage") supplies a bounded numeric/boolean interval (`@GlobalVar msg.value = [...]`, `@StateVar presell = true`, `@LocalVar amount = [500e18, 500e18]`). No example shows a cross-contract (or same-contract) enum-qualified literal like `Perpetuals.Side.Long`. Whether the grammar/engine supports this at all was unconfirmed.
3. Even granting (2), whether pinning `trade.side` actually **removes** the `Short` branch from the join (versus merely narrowing an interval that still gets joined) was an open engine-behavior question — and running the engine is explicitly out of scope for this pass (RQ1-B deferred).
4. Given (1)–(3), Claude's initial recommendation was to keep `@During` as-is: it already achieves the same effective scoping "for free," since attaching to a specific line inside a specific branch means the `Short` branch is never even reached at that program point — no join, no pinning apparatus needed.

## Round 2 — User's corrections

1. **Bottom-branch join is confirmed engine behavior, not a maybe.** The engine already implements infeasible-branch pruning via the interval domain's bottom element: if a branch is proven infeasible under the pinned value (e.g. `trade.side` fixed to `Long` makes the `Short` guard evaluate to false), that branch's contribution to any join becomes ⊥, and `⊥ ⊔ x = x` — so the joined `σ_exit` at the return point reduces to exactly the live branch's value. This directly resolves objection (1)/(3): Claude's concern about the join was valid in the abstract but factually wrong about this engine's actual join semantics.
2. **Enum debug-annotation support is a legitimate, case-independent capability gap.** The user's point: whether `trade.side`'s enum type happens to live in another contract (`Perpetuals`) here is incidental — the identical gap (no way to pin an enum-typed local/state var to a specific named value via debug annotation) would exist even if the enum were declared in the same contract as the analyzed function. So this isn't a `16_H_04`-specific workaround; it's a general tool capability that arguably *should* exist, independent of whether it's exercised on this particular case.

## Round 3 — the L5-adjacent worry, and Claude's counter-argument

The user then reconsidered their own motivation for preferring Post here, and flagged it as possibly re-introducing the retired "bug-awareness required" (old L5) concern: does attaching `@During` *immediately after the exact buggy line, inside the exact branch that contains the bug* implicitly encode "I already know precisely where this bug lives" in a way that's illegitimate for a retrospective study?

Claude's counter-argument (not yet re-confirmed by the user as of this writing):

- **This isn't specific to the During/Post choice.** R1-1 (Reported Behavior Reconstruction) is, by explicit design, built by reading the audit report first — for *every* case in the dataset, During or Post alike. "The annotator already knows where the bug is" is a precondition of the entire pipeline, not something newly introduced by placing `@During` at the buggy line. This is exactly why old L5 ("would a bug-unaware developer have written this?") was judged undecidable and retired outright, not narrowed to apply selectively to During-attached annotations. If During's placement here were disqualifying on these grounds, the same argument would disqualify nearly every target annotation in the benchmark.
- **If anything, the argument points the other way.** The During relation's content is independently motivated by a general domain invariant already stated in R1-1 ("fee must always reduce the trader's quote balance regardless of side — a cost, never a credit") — the kind of check a developer might plausibly write as routine post-assignment sanity-checking, independent of knowing this specific bug exists. The Post+pinning alternative, by contrast, requires *deliberately* forcing execution down the `Long` path specifically because one knows that's where the bug lives — arguably a more bug-targeted construction than During's simple "assert right after I compute this" pattern.

## Status

Not fully re-confirmed by the user (marked "애매하네" / undecided at time of writing). No files under this case were changed as a result of this discussion — `analysis.md`'s R1-4 (`@During`, selected) stands as-is. Two follow-up items were identified, neither acted on yet:

1. **Tool capability gap**: no grammar/engine support demonstrated for enum-typed debug annotations (same-contract or cross-contract). Worth tracking separately as a discovered limitation, not as part of this case's RQ1/RQ2 classification, and not something to build this pass (engine changes are out of scope for now).
2. **General methodology note (candidate for README)**: whether "annotation attached at/near the reported buggy line" should ever be treated as evidence against a case, given R1-1's report-first construction applies uniformly — current answer is no, but this hasn't been promoted to a README rule since it's not yet clear another case will need it.
