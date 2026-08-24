# Engine/Script Code Changes — First Revision Session

Tracks actual code changes made to the engine and pipeline scripts during this revision session, as distinct from the RQ1/RQ2 case-analysis methodology work (see `phase_reviews/README.md` for that). Written while preparing `web3bugs_16_H_04`'s dependencies as a first trial of `phase_reviews/case_pipeline_automation_plan.md`.

## Status: 6 open issues, not yet fixed (see bottom) — plus 1 confirmed architectural (non-bug) finding — plus 1 new grammar/engine feature (see below), not yet end-to-end tested

---

## New feature: snapshot-qualified references, `varRef(Entry/Exit/Before/After/Assign)`

**Motivation**: three independently-analyzed cases (`web3bugs_83_H_01`, `web3bugs_42_H_01`, `web3bugs_35_H_11`) each hit the same wall in R1-3: the true reported intent was of the form `new_value == f(old_value, some_independent_third_quantity)`, and the grammar's only cross-state constructs — `(before relOp after)` ($D_{\text{ba}}$), `(assign relOp current)` ($D_{\text{ac}}$) under `@During`, and `(entry relOp exit)` ($P_{\text{ee}}$) under `@Post` — all compare the *same* single expression at two timepoints, with no way to inject a third, independently-scoped term. R1-3 had to fall back to a weaker relation each time (e.g. `debts >= details[_id].debt` instead of the exact `debts == old_debts + increasingDebt`), recorded as `Intent coverage: Partial` after the field was added (see the `web3bugs_83_H_01` RQ2-A-correction entries below in this doc's history / `phase_reviews/README.md` §3/§4/§10).

**Decision**: rather than keep documenting this as a permanent grammar limitation, extend the grammar. User's call, made explicitly aware of the cost (new grammar production, new formal semantics, new engine implementation, re-litigating cases already analyzed under the old grammar) and choosing to do it now, early in the 35-case pass, rather than after all 35 are done.

**Design**: one new `arithFactor` alternative, `varRef '(' snap ')'` where `snap ∈ {Entry, Exit, Before, After, Assign}` — a variable reference tagged to evaluate against a specific state snapshot ($\sigma_{\text{entry}}$/$\sigma_{\text{exit}}$/$\sigma_{\text{before}}$/$\sigma_{\text{pt}}$/$\sigma_{\text{assign}}$, per `main.tex`'s existing $\Gamma$ table) instead of the ambient reference point. Crucially, this is a single new *term*, usable anywhere inside an arithmetic expression (nested under `+`, `-`, `*`, ...), not a new clause-level rule — which is what makes `debts == debts(Entry) + increasingDebt` and `feeGrowthOutside1 == feeGrowthGlobal - feeGrowthOutside1(Before)` expressible as ordinary `(C_cmp)` comparisons. The old $D_{\text{ba}}$/$D_{\text{ac}}$/$P_{\text{ee}}$ clause forms are now strictly subsumed by this (e.g. `x(Before) < x(After)` says the same thing `x(Before < After)` used to) and were **removed from the grammar entirely**, not kept alongside the new form — a deliberate choice (user: "다 고쳐서 하자", "논문에 syntax semantics 적을 때도 더 깔끔할 것 같아") over keeping both for backward compatibility, since keeping both would have meant explaining two ways to say the same thing in the paper.

**Grammar restriction (`Entry`/`Exit` → `@Post`-only, `Before`/`After`/`Assign` → `@During`-only)**: NOT enforced by making `arithFactor` itself take a rule parameter — ANTLR4 doesn't allow parameters on left-recursive rules (`arithExpr`/`arithAdd`/`arithTerm` are all left-recursive; `error(169): rule ... is left recursive but doesn't conform to a pattern ANTLR can handle` when first attempted). Fixed by using a **parser member variable** instead (`@parser::members { inDuring = False }` at the top of `Parser/Solidity.g4`), set by an action at the top of `duringIntent`/`postIntent` (`{self.inDuring = True/False;}`), and read by semantic predicates on `arithFactor`'s new alternatives (`{not self.inDuring}? varRef '(' ENTRY ')'`, etc.) — this avoids parameterizing the left-recursive rules at all. `Entry` was originally going to be legal in *both* kinds (since $\sigma_{\text{entry}}$ is genuinely in `@During`'s $\Gamma$ too, needed internally by `changed()`) but was deliberately restricted to `@Post`-only per the user's design call, keeping `{Entry, Exit}` and `{Before, After, Assign}` as two clean, non-overlapping, self-contained sets rather than an asymmetric one.

**Files changed**:
- `Parser/Solidity.g4` — grammar changes above. User regenerated the ANTLR parser themselves (established pattern this session).
- `Analyzer/EnhancedSolidityVisitor.py` — (a) removed dead/now-crashing references to the deleted `PostEntryExitContext`/`DuringBeforeAfterContext`/`DuringAssignCurrentContext` classes in `_build_post_clause_dict`/`_build_during_clause_dict` (these would otherwise `AttributeError` on *every* `@Post`/`@During` annotation immediately after regeneration, since the classes no longer exist — found and fixed before it could bite); (b) added 5 new visitor methods (`visitVarRefAtEntry`/`Exit`/`Before`/`After`/`Assign`), each wrapping the inner `varRef`'s `Expression` with a context tag (`'VarRefAtEntry'` etc.) for the evaluator to dispatch on.
- `Analyzer/GuardianVerificationEngine.py` — `evaluate_guardian_expression` gained a dispatch branch for the 5 new context tags, delegating to a new `_evaluate_snapshot_var_ref` helper. That helper: for `Exit`/`After`, just re-evaluates the inner varRef against whatever `variables` env was already ambiently passed in (already `sigma_exit`/`sigma_pt` in every calling context checked — `verify_post_direct_comparison` via `_eval_on_exit_value`, `verify_during_direct_comparison` via `cfg_node.variables`); for `Entry`/`Assign`, resolves via a new `self._current_fn_cfg` ambient field (`entry_env`/`fn_cfg.related_variables`, `fn_cfg.assign_env`); for `Before`, resolves via new `self._before_cfg_node`/`self._before_line_no` ambient fields (`cfg_node.before_envs[line_no]`) — this one needed genuinely new ambient-state wiring, since `(cfg_node, line_no)` weren't otherwise reachable from arbitrary depth inside an expression tree.
- `Interpreter/Engine.py` — 4 call sites wire the new ambient state right before dispatching to a verify_* method: `_verify_during_annotation` and `_verify_during_clause_dynamic` set `guardian._before_cfg_node`/`_before_line_no`; `_verify_post_annotation` and the live (non-shadowed) `_verify_post_clause_dynamic` set `guardian._current_fn_cfg`. (Noted in passing: `_verify_post_clause_dynamic` is defined *twice* in this file, at two different line numbers — the second definition silently shadows the first, which is dead code. Not touched/fixed, just observed.)
- `paper/first_revision/main.tex` — grammar figure (`fig:intent-grammar`) and semantics equations updated to match; see the "Snapshot-qualified references" write-up added there for the formal `eval` extension (5 equations replacing what were previously 3 separate $\mathcal{V}\llbracket\cdot\rrbracket$ clause-level rules).

**Migrated to the new syntax** (mechanical, semantics-preserving): `evaluation/RQ1/cases/greedy_contract/SwordCrowdsale_input.json`/`.json`, `evaluation/RQ1/cases/div_in_path/WANGMI_input.json`/`.json`, `evaluation/RQ1/cases/web3bugs_45_H_01/web3bugs_45_H_01.sol` (regenerated its `.json` via `soltotestjson.py` after editing the source) — these are part of the *already-published* 20-case baseline, so old-syntax → new-syntax was done as a literal find/replace (`x(Entry > Exit)` → `x(Entry) > x(Exit)`), not a re-analysis.

**Upgraded to use the new capability**: `web3bugs_42_H_01` (`debts == debts(Entry) + increasingDebt`, was `debts >= details[_id].debt`) and `web3bugs_35_H_11` (`feeGrowthOutside1 == feeGrowthGlobal - feeGrowthOutside1(Before)`, was `(before != after)`) — see their `analysis.md` files and `case_progress.md`. `web3bugs_83_H_01` was deliberately *not* upgraded — its exact formula needs `lpSupply` (an external `IERC20.balanceOf` call), elapsed-block count, and `totalAllocPoint(Entry)` all combined, judged too complex relative to the benefit for now.

**Not yet done**: end-to-end testing. The grammar compiles and the migrated/upgraded case JSONs are syntactically valid, but no case has actually been run through `main.py` with the new syntax yet — neither the migrated baseline cases (to confirm they still behave identically) nor the upgraded cases (`42_H_01`'s build is separately blocked on the chained-interface-struct crash above).

`web3bugs_35_H_11`'s contraction + case JSON were built this session (`evaluation/RQ1/target_contracts_contraction/web3bugs_35_H_11.sol`, `evaluation/RQ1/cases/web3bugs_35_H_11/web3bugs_35_H_11.json`) — the JSON slices cleanly with the new `(Before)` syntax intact. A first run attempt hit an unrelated, pre-existing blocker before reaching the new grammar feature at all:
```
ValueError: Unsupported typeCategory 'mapping'
  at Analyzer/StaticCFGFactory.py:422, in make_param_variable
```
`cross(mapping(int24 => Tick) storage ticks, ...)` — a **mapping-typed function parameter** — isn't handled by `make_param_variable`'s type dispatch (only elementary/array/struct/etc. branches exist there, no `mapping` branch for parameters specifically, as opposed to state variables or struct members, which do support mapping). This is a parse/CFG-construction failure, upstream of anything related to the new snapshot-qualified-reference feature — so this run did **not** actually test `varRef(Before)` at all yet. Not investigated further; user stopped here to wrap up for the day. Next time this case is picked up, either fix `make_param_variable`'s mapping-parameter gap first, or find/construct a different upgraded case (`42_H_01`, once unblocked) to get the first real test of the new feature.

---

## 1. `temp/preprocess_contraction.py` — single-line `if` expansion regex bug

**File**: `temp/preprocess_contraction.py`, function `expand_single_line_blocks` (originally used `RE_SINGLE_IF`).

**Bug**: `RE_SINGLE_IF = re.compile(r"^(\s*)(if\s*\(.*\))\s+(.+;)\s*$")` — the `.*` inside the condition group is greedy and matches through to the *last* `)` on the line. When the statement after the `if` condition itself contains parentheses (e.g. `if (cond) result = (a * b) >> 128;`), the regex misidentifies where the condition ends, producing corrupted output like:
```solidity
if (cond) result = (a * b) {
    >> 128;
}
```
Found while cleaning `PRBMathCommon.sol` for `Dependencies/libraries/` — its `exp2()` function has ~60 single-line `if (bitmask & x > 0) result = (result * K) >> 128;` statements, the first real-world case in this project to hit the pattern.

**Fix**: Replaced regex-based condition matching with a proper balanced-paren scan (`_find_matching_paren`, `_expand_single_line_if`) that walks from the `if`'s opening `(` and tracks depth to find the true matching `)`, instead of guessing via greedy regex.

**Regression check performed**: Wrote a comparison script (scratchpad, not committed) that ran both the old and new logic against every `if (...) ...;`-shaped candidate line across the whole repo corpus (2108 candidate lines: `Dataset/`, `evaluation/RQ1/target_contracts_original/` including `dependencies/`, `evaluation/RQ1/target_contracts_contraction/`, `Dependencies/`). Result: **0 lines differ in already-processed/active locations** (`target_contracts_contraction/`, `Dependencies/`) — all 885 lines where old and new output differ are in raw, never-yet-processed source (`Dataset/`, `target_contracts_original/`). Confirmed the fix cannot have broken any of the 20 already-working cases.

---

## 2. New dependency files for `web3bugs_16_H_04` (Tracer Protocol `Balances.applyTrade`)

**Files added**: `Dependencies/libraries/LibMath.sol`, `LibPerpetuals.sol`, `PRBMathSD59x18.sol`, `PRBMathUD60x18.sol`, `PRBMathCommon.sol`.

**Source**: `evaluation/RQ1/target_contracts_original/dependencies/` (a raw dependency cache that predates this session — discovered mid-session; not previously wired into `Dependencies/`).

**Processing**: Ran through `preprocess_contraction.py`'s `preprocess()` (comment/SPDX/import stripping, single-line-if expansion, enum single-lining) — the same treatment as target-contract contractions. Per established convention (`Dependencies/libraries/SafeMath.sol` already keeps all 20 of its functions rather than only what one case needs, since `Dependencies/` is a shared pool reused across cases), **no functions were trimmed** — each file keeps its full function set, only comments/imports removed.

**Not brought in**: `Types.sol`, `LibPrices.sol` (transitively required only by `Types.sol`) — neither `applyTrade` nor `getFee` reference `Types`, and no other pending case in this dataset appears to need them (contest 16's other two entries, `16_H_02` and `16_H_06`, are `excluded`/unrelated `GasOracle` respectively). Can be added later if a future case needs them.

**`Dependencies/main.py` change**: added `"LibPerpetuals.sol"` to the `_late` library-ordering set (alongside pre-existing `Fixed18.sol`, `FixedPoint.sol`) — `Perpetuals`' functions call `PRBMathUD60x18.mul()`/`.div()`, but alphabetically `LibPerpetuals.sol` sorts before `PRBMathUD60x18.sol`, so it needs to be pushed later in the analysis order for the cross-library call to resolve.

---

## 3. `Domain/Variable.py` — struct member initialization crashed on enum-typed fields

**Symptom**: Analyzing `Perpetuals.Order` (a struct with a field `Side side;`, `Side` being an enum in the same library) crashed 3 of `Perpetuals`' 5 functions (`orderId`, `canMatch`, `getExecutionPrice` — every function taking an `Order`-typed parameter) with:
```
AttributeError: 'NoneType' object has no attribute 'startswith'
  at Domain/Variable.py:540, in _make_var: if et.startswith("int"):
```
(Reproduced with a full traceback via a standalone script bypassing `Dependencies/main.py`'s `except Exception: pass`, which was swallowing this into a one-line `[ERR]` log.)

**Root cause**: `StructVariable.initialize_struct`'s inner helper `_make_var` was a **separate, incomplete reimplementation** of the type-dispatch logic that `VariableEnv.top_from_soltype` (`Utils/Helper.py`) already implements generically (array/mapping/struct/interface/enum/elementary). `_make_var` had branches for array/mapping/struct/interface but **no `enum` branch**, so an enum-typed member fell through to the elementary branch, where `et = sol_t.elementaryTypeName` is `None` for an enum type (only `enumTypeName` is set for enums) — `None.startswith(...)` crashes. `top_from_soltype` already had a correct enum branch; `_make_var` was simply never updated when that support was added elsewhere, which is exactly the kind of drift two independent copies of the same dispatch logic invite.

**Fix (root-cause, not a patch)**: Replaced `_make_var`'s entire body with a delegation to `VariableEnv.top_from_soltype(m_type, struct_defs=struct_defs, enum_defs=enum_defs, identifier=var_id)`, then setting `.scope` on the result (the one thing `top_from_soltype` doesn't set that `_make_var` did). This removes the duplicate dispatch table entirely — any type category `top_from_soltype` supports in the future is automatically supported here too, with no second place to remember to update. Added `enum_defs` as a new keyword parameter to `initialize_struct` (mirroring the existing `struct_defs` parameter), defaulting to `{}` if not supplied so no call site is required to change.

**Local import note**: `VariableEnv` is imported inside the function body (not at module top), because `Utils/Helper.py` imports several classes from `Domain/Variable.py` — a top-level import would be circular.

**Call sites updated to also pass `enum_defs=`** (mechanical, low-risk additions — previously these all passed `struct_defs=` but never `enum_defs=`, so enum-typed struct members would fall back to the empty-default `EnumVariable` instead of crashing, but without the enum's actual member list):
- `Domain/Variable.py` — `ArrayVariable._create_default_value` (struct-typed array element), `MappingVariable`'s equivalent default-value path (this one was also missing `struct_defs=` entirely — nested struct-in-mapping resolution was silently incomplete before; now fixed too).
- `Analyzer/StaticCFGFactory.py:378` (`make_param_variable`) — this is the exact call site in the crash traceback.
- `Analyzer/ContractAnalyzer.py` — 4 call sites (struct default-value initialization, ~lines 786/791, 1158, 1401).
- `Utils/Helper.py:438` — `top_from_soltype`'s own struct branch was missing `struct_defs=`/`enum_defs=` propagation for *nested* structs (a struct field whose type is itself a struct); fixed to pass both through recursively.
- `Interpreter/Semantics/Evaluation.py` — 5 call sites (struct-typed array/mapping element access returning an empty struct, struct constructor calls) — 3 of these were also missing `struct_defs=` entirely, now fixed alongside the `enum_defs=` addition.

**Verification**:
- Isolated re-run of `LibPerpetuals.sol` in the repro script: all 5 functions (`orderId`, `calculateAverageExecutionPrice`, `calculateTrueMaxLeverage`, `canMatch`, `getExecutionPrice`) now register in the CFG; `enumDefs: {'Side': ['Long', 'Short']}` confirmed present.
- Full `Dependencies/main.py --type all` pkl regeneration: no new `NoneType`/`AttributeError` crashes anywhere in the corpus except one pre-existing, unrelated `'NoneType' object has no attribute 'get_exit_node'` in `Preparable.sol` (not struct/enum-related, not touched by this change — not investigated further, out of scope).
- Full 20-case regression (`evaluation/RQ1/run_all.py`): **19/20 still VIOLATED** as before. **1 new failure — see below.**

---

## Open issue: `web3bugs_51_H_02` regressed from VIOLATED to ERROR

Previously part of the 20/20 VIOLATED baseline (per `PROCESS_GUIDE.md`/`PROCESS_GUIDE_v2.md`). After the changes above, it now errors:
```
[LIBRARY CALL ERROR] None: 'str' object has no attribute 'multiply'
...
ValueError: member 'div' is not a recognised global-member.
```
at `Interpreter/Semantics/Evaluation.py:1188` (`evaluate_member_access_context`), reached via a `return` statement evaluating a library call chain in `web3bugs_51_H_02.json`.

**Not yet diagnosed.** Suspected connection: the `struct_defs=`/`enum_defs=` propagation changes in `Interpreter/Semantics/Evaluation.py` may have changed how some value along this call chain resolves (e.g. an alias/struct-typed intermediate that previously fell through to a generic string-symbol path and got picked up by `using`-directive dispatch by accident, now resolves more precisely and no longer matches whatever `div` was being dispatched against). **Deferred per user instruction — pick this up before trusting `web3bugs_51_H_02`'s result again, and before scaling the `Domain/Variable.py`/`Evaluation.py` changes' effects assumption to other cases.**

---

## Open issue: state-level struct-array debug annotations resolve to empty struct members (found while building `web3bugs_83_H_01`)

**Symptom**: `@StateVar poolInfo[1].allocPoint = [100, 100]` (and `poolInfo[1].accConcurPerShare`) silently fail to resolve when `poolInfo` is a public `PoolInfo[]` state array:
```
[WARNING] Cannot resolve LHS expression: VarRefMemberAccess (member: allocPoint) (base: None) (scope: state)
```

**Root cause, confirmed by direct source read**: `Analyzer/ContractAnalyzer.py:1069-1076` (`_create_variable_object`, the "2-A 배열" / array branch) constructs the state variable's `ArrayVariable` **without passing `struct_defs=`/`enum_defs=`** — unlike the very next branch, "2-D 매핑" (mapping, lines 1091-1108), which explicitly builds `all_structs`/`all_enums` (including parent CFGs) and passes them into `MappingVariable`. This is the exact same class of propagation gap already fixed twice this session (`Domain/Variable.py`'s `_make_var`→`top_from_soltype` delegation; several `Evaluation.py`/`ContractAnalyzer.py` call sites missing `struct_defs=`) — just a third, previously-unexercised call site (a *state-level array-of-structs*, as opposed to a struct member or mapping value).

Downstream consequence, traced through `Domain/Variable.py`: `get_or_create_element(idx)` (line 111) auto-grows a dynamic array via `_create_new_array_element` (line 132), which at line 169 checks `if btype.structTypeName in self.struct_defs:` before calling `initialize_struct`. Since `poolInfo`'s `struct_defs` is empty, this check fails silently, and an **empty `StructVariable` with no members at all** is returned instead of raising an error — so any subsequent `.allocPoint`/`.accConcurPerShare` field lookup on `poolInfo[1]` returns `None`, which the debug-annotation resolver (`DebugInitializer.py`) then reports as "cannot resolve LHS expression."

**Scope**: not specific to `poolInfo` — this will reproduce for **any future case that debug-annotates an indexed element of a public/state array-of-structs** (a common pattern; `poolInfo`-like patterns are typical in yield-farming/staking contracts, which appear repeatedly across the remaining 35-case list).

**Not yet fixed** — found while building `web3bugs_83_H_01`'s case JSON; user deferred it ("일단 넘기고 다음거 보자") to keep moving on case review rather than context-switch into a fix immediately. `web3bugs_83_H_01`'s contraction (`target_contracts_contraction/web3bugs_83_H_01.sol`) and a first-draft case JSON (`evaluation/RQ1/cases/web3bugs_83_H_01/web3bugs_83_H_01.json`) already exist but **cannot be verified against the engine until this is fixed** — the debug scenario (`poolInfo[1]`'s pre-existing `allocPoint`/`accConcurPerShare`) silently fails to apply.

**Proposed fix** (not yet applied): mirror the mapping branch — in `_create_variable_object`'s array branch, build `all_structs`/`all_enums` the same way (including `parent_cfgs`) and pass them into `ArrayVariable(...)`.

---

## Separate, non-blocking tool issue found in the same pass: `soltotestjson.py` misparses `array.push(Struct({...}))` spanning multiple lines

`soltotestjson.py`'s block-header heuristic (`_open_blk` regex, matches a trailing `{`) misfires on a multi-line `poolInfo.push(PoolInfo({ ... }));` call — it treats the struct literal's `{` as if it were a control-flow block opener, splitting the statement into a malformed two-record pair that the ANTLR grammar then rejects (`no viable alternative at input 'poolInfo.push('`). Confirmed this exact pattern (`.push(StructName({` spanning multiple lines) does not appear in any existing contraction file, so this is newly-encountered, not a regression.

**Not a code fix — worked around instead**: writing the `.push(...)` call as a single line ending in `;` avoids the multi-line block-header misdetection entirely (matches `soltotestjson.py`'s simple one-liner rule, `_one_liner`). No engine/tool change needed; just a contraction-authoring convention to remember for any future case using a multi-line struct-literal argument to a function call.

---

## Open issue: chained (non-cast) interface calls returning a struct crash on field access — found while building `web3bugs_42_H_01`

**Symptom**: `FloatStruct memory lf = engine.mochiProfile().liquidationFactor(address(asset));` inside `_liquidatable()`, then passed into `Float.divide(a, lf)`, crashes the moment the library function reads `lf.denominator`:
```
ValueError: 'denominator' not in struct 'lf'
```
`lf` materializes as a `StructVariable` with an **empty `.members` dict** — the interface call's return value never went through `initialize_struct`/`top_from_soltype`, so field access has nothing to find.

**Not a new bug — already logged, previously unresolved, in `Dependencies/ISSUES.md`** (a pre-existing engine-debugging log from an earlier, separate session, predating this revision): `56_H_02: 'getEarnedYield' not in struct '_self' — struct member가 interface function call 결과` is the exact same failure signature/class, just a different struct/field name. `ISSUES.md`'s session-3 notes (§3, "Interface struct return 지원") record that this *was* fixed for **explicit-cast style** interface calls (`IERC20(addr).balanceOf()`, routed through `InterfaceFunctionCallContext` → `_lookup_interface_return` → `top_from_soltype`, confirmed in `Interpreter/Semantics/Evaluation.py:208-240` — this path correctly passes `struct_defs`/`enum_defs`). The failure here is on the **other** call shape — a chained, non-cast interface member call (`engine.mochiProfile().liquidationFactor(...)`) — which is evidently a separate code path that never received the same fix. Not yet located precisely which function handles this second shape (didn't get that far before deferring); `56_H_02` itself no longer errors in this session's own 20-case regression checks, so whatever fixed *that* case's specific manifestation either doesn't generalize to this call shape, or this is a third, still-different code path — needs investigation, not assumption, when picked up.

**Scope**: blocks `web3bugs_42_H_01` end-to-end (both `_liquidatable()`'s `lf` and, more fundamentally, `borrow()`'s own `price` from `engine.cssr().update(...)` — a **non-view** call that can never legally receive an `@IReturn` hint at all, per the view/pure restriction — will hit the identical crash the moment any of its struct fields are read, with no debug-annotation workaround possible). Likely affects any future case with a chained (non-cast) interface call returning a struct type.

**Deferred per user instruction** ("괜찮아, 별도로 문서에 정리해 두고 나중에 한꺼번에 고치자") — to be batched together with the other open issues above (`web3bugs_51_H_02` regression, the Update.py if-condition-refine bug, the `poolInfo`-style state-array `struct_defs` propagation gap) rather than fixed piecemeal. `web3bugs_42_H_01`'s case build is blocked on this until then.

---

## 4. Cross-library qualified-enum-type reference (`Library.EnumName`, e.g. `Perpetuals.Side`) — 3 of 4 layers fixed

Surfaced while building `web3bugs_16_H_04`'s contraction: `Balances.Trade.side` is typed `Perpetuals.Side`, and `applyTrade` compares `trade.side == Perpetuals.Side.Long`. Every layer that touches a dot-qualified library-scoped enum reference had the same latent assumption baked in — "a `Library.X` qualified name always resolves to a struct" — because structs were the only qualified-name case exercised before this case.

**Layer 1 — `Analyzer/EnhancedSolidityVisitor.py`, `visitUserDefinedType`'s dot-qualified branch (`elif '.' in type_name:`)**: always treated the resolved symbol as a `StructDefinition`. Fixed by importing `EnumDefinition` (alongside `StructDefinition`) from `Domain/Variable.py` and branching on `isinstance(resolved, EnumDefinition)` vs `isinstance(resolved, StructDefinition)`:
```python
if isinstance(resolved, EnumDefinition):
    type_obj.typeCategory = "enum"
    type_obj.enumTypeName = type_name
    if contract_cfg and type_name not in contract_cfg.enumDefs:
        contract_cfg.enumDefs[type_name] = resolved
elif isinstance(resolved, StructDefinition):
    ... # existing struct logic, unchanged
```

**Layer 2 — `Interpreter/Semantics/Evaluation.py`, `evaluate_member_access_context`'s `isLibrary` dict-handling branch (~line 1014-1022)**: `Library.EnumName` fell through to a generic `f"symbolic({lib_name}.{member})"` string fallback (meant for genuinely-opaque library members), which then broke the subsequent `.Member` access on the enum value. Fixed by checking `lib_cfg.enumDefs` before falling back:
```python
if lib_cfg and member in getattr(lib_cfg, 'enumDefs', {}):
    return lib_cfg.enumDefs[member]
if lib_cfg and member in getattr(lib_cfg, 'globals', {}):
    return lib_cfg.globals[member].value
```
**Note**: this is the same error signature/site (`ValueError: member 'X' is not a recognised global-member.`) as the still-open `web3bugs_51_H_02` regression above (§ Open issue). Strongly suspected shared root cause, but not chased further — both remain in the deferred batch.

**Layer 3 — `Interpreter/Semantics/Update.py`'s identifier-resolution logic**: had no library-marker handling at all for a bare `Perpetuals` identifier appearing in a condition-refinement context (e.g. narrowing `trade.side == Perpetuals.Side.Long` inside an `if`), producing `Identifier 'Perpetuals' not declared.`. Fixed by adding the same `{"isLibrary": True, "libraryName": ident}` marker pattern Evaluation.py already used.

**Layer 4 — deferred**: fixing Layer 3 exposed a deeper error in the same condition-refine continuation logic (`'dict' object has no attribute 'identifier'`) when actually narrowing on the qualified-enum comparison. **This is the layer explicitly deferred by the user** ("에러난건 나중에 한꺼번에 고치자"), to be batched together with the `web3bugs_51_H_02` regression later. Until fixed, `if (trade.side == Perpetuals.Side.Long)`-shaped branches cannot be condition-refined by the engine, though the comparison's *evaluation* (non-branch-refining contexts) is unaffected by this specific layer.

---

## 5. Enum-valued `@LocalVar`/`@StateVar` debug annotations — new feature, implemented and verified

Motivated by `web3bugs_16_H_04`'s need to debug-annotate `trade.side` (an enum-typed struct field) with a value like `Perpetuals.Side.Long`. Previously, debug annotations only supported numeric/boolean/array literal values — no enum support existed end-to-end.

**Grammar**: the user themselves changed `Parser/Solidity.g4`'s `DebugEnumLiteral` production from `identifier ('.' identifier)?` to `identifier ('.' identifier)*` (arbitrary-depth qualified enum literals, e.g. `Long`, `Side.Long`, or `Perpetuals.Side.Long`) and regenerated the ANTLR parser themselves — not done by the assistant.

**`Analyzer/EnhancedSolidityVisitor.py`, `_parse_debug_value`'s `DebugEnumLiteralContext` branch (~line 2892)**: previously only joined the first 1-2 identifier tokens (written for the old `?`-cardinality grammar); fixed to join *all* identifier tokens to match the new `*` grammar:
```python
if isinstance(iv_ctx, SolidityParser.DebugEnumLiteralContext):
    return ".".join(ident.getText() for ident in iv_ctx.identifier())
```

**`Interpreter/Semantics/DebugInitializer.py`, `_patch_var_with_new_value_for_debug`**: had no enum-specific branch at all — a debug value string for an enum target fell through to a generic `isinstance(target_var, VarClass)` path that doesn't know how to set an enum's `valueIndex`. Added a new explicit branch, checked before the generic fallback:
```python
if isinstance(target_var, EnumVariable) and isinstance(new_value, str):
    member_name = new_value.rsplit(".", 1)[-1]
    if member_name not in target_var.members:
        raise ValueError(f"Debug annotation value '{new_value}' for enum '{target_var.typeInfo.enumTypeName}': "
            f"member '{member_name}' not found (known members: {list(target_var.members.keys())}). ...")
    target_var.valueIndex = target_var.members[member_name]
    target_var.value = member_name
    return
```
Accepts any qualification depth (`Long`, `Side.Long`, `Perpetuals.Side.Long`) by taking only the last dot-segment as the member name, so it works regardless of how fully-qualified the user's annotation happens to be.

**Verification**: (a) unit test directly against `_patch_var_with_new_value_for_debug` — `Long`, `Side.Long`, `Perpetuals.Side.Long` all correctly produced `valueIndex=0, value='Long'`; `Short` produced `valueIndex=1`; an invalid member name raised the clear `ValueError` above. (b) full-pipeline test through the real grammar/visitor/`ContractAnalyzer`, using a throwaway scratchpad `.sol` file (`debug_enum_test.sol`, **not** the real `web3bugs_16_H_04` contraction — contraction files stay annotation-free per convention, debug annotations belong only in the case JSON) with `// @LocalVar trade.side = Long` and friends inside a `// @Debugging BEGIN/END` block matching `applyTrade`'s real signature — confirmed working end-to-end through the actual parser, not just the isolated unit.

---

## 6. Confirmed architectural finding: loop-body `@During` is never evaluated by the engine

Not a bug fix — a confirmed fact about existing engine behavior, established by direct source inspection while investigating an external critique of `web3bugs_71_H_11`'s classification (see `phase_reviews/README.md` §4/R1-7's new exception paragraph and `phase_reviews/02_web3bugs_71_H_11/analysis.md` for the case-level consequences).

**Finding**: `Interpreter/Engine.py`'s `fixpoint()` (line 409) computes a loop's fixpoint using `transfer_function` (lines 267-277) internally — `transfer_function` never calls `_process_node_intents`. Separately, `reinterpret_from()` (line 1006) treats loop-head nodes specially: it calls `self.fixpoint(n)` and then `continue`s directly to the loop-exit's successors, entirely skipping the `_process_during_annotations` call (line 1108) that normal (non-loop) nodes go through. The net effect: a `@During` annotation textually placed on a statement inside a loop body is **never evaluated by the engine, in any iteration** — not evaluated once per iteration, not evaluated imprecisely via join — simply never invoked. This is an architectural/control-flow fact, verifiable from the source without running any case, independent of any question about join-over-iterations precision or ⊤-widening (a separate, genuinely engine-precision concern that remains correctly out of scope for R1-7's Expressibility decision).

**Consequence for the methodology**: led to the new `delta` tag (README §4/R1-7) — a case where a relation's content and referenced values are otherwise fine, but the only viable attachment point is a location this specific engine's architecture never evaluates. Two confirmed instances so far: `web3bugs_71_H_11` (this is the case's primary/first blocker) and `web3bugs_34_H_01` (checked as a secondary alternative, found to be equally blocked, but not the case's primary blocker — that case is independently blocked by `beta` first).

---

## Dependencies pipeline gap found: `Dependencies/main.py`'s "contracts" phase uses a hardcoded file list, not a directory scan — found while building `web3bugs_3_H_05`

**Symptom**: three new files added to `Dependencies/contracts/` (`Roles.sol`, `RoleAware.sol`, `PriceAware.sol`) were silently never analyzed/pkl'd by `python Dependencies/main.py --type all` — no error, no log entry, just absent from the output.

**Root cause**: unlike the interfaces phase (`IFC_DIR.rglob("*.sol")`, recursive, auto-discovers everything) and the libraries phase (`LIB_DIR.glob("*.sol")`, auto-discovers top-level files), the **contracts phase** (`Dependencies/main.py:515-563`) iterates a manually-maintained Python list, `_con_order` — a hardcoded sequence of `(relative_path, mode)` tuples reflecting a hand-picked library→parent→child dependency order. Any `.sol` file placed in `Dependencies/contracts/` (or a numbered subfolder) that isn't explicitly added to this list is never processed, with no warning.

**Fixed for this session's 3 new files**: added `("Roles.sol", "contract")`, `("RoleAware.sol", "contract")`, `("PriceAware.sol", "contract")` to `_con_order` (`Dependencies/main.py`, right after the `ReentrancyGuardUpgradeable.sol` entry), in that dependency order (`RoleAware` uses `Roles`; `PriceAware is RoleAware`). Confirmed all 3 now produce fresh `con_*.pkl` files.

**Not fixed, just documented — a process trap for future cases**: any future case that adds a new contract (not interface, not library) to `Dependencies/contracts/` must remember to also add it to `_con_order`, in correct dependency order, or it will be silently skipped with zero error output. Worth eventually replacing with an automatic topological sort or at least a loud warning for `.sol` files present on disk but absent from `_con_order`, but that's a larger change — noted here, not attempted.

---

## Open issue: two new pre-analysis warnings found while pkl'ing `RoleAware.sol`/`PriceAware.sol` for `web3bugs_3_H_05` — not yet chased

Found during the (isolated, single-file) `Dependencies/main.py` pre-analysis pass, both **pre-existing classes of issue already seen this session, reproducing in new files**, not chased further — deferred to the same later batch as the other open issues:

1. **`RoleAware.sol`**: `[ERR] L25 ctx=constantVariableDeclaration: Type 'Roles' is not defined as struct, enum, or type alias in contract 'RoleAware'` (plus three follow-on "`roles` not declared" errors) — `Roles` is a contract-typed state variable (`Roles public immutable roles;`), and `Roles.sol` is processed earlier in `_con_order`, but this isolated per-file pass apparently doesn't see it. Same class as the `ICSSRRouter`/`FloatStruct` warning found earlier this session (§ ICSSRRouter/IMochiNFT work) — that one turned out to be a single-file-pre-analysis-only artifact, harmless once `--type all` cross-references everything. Not independently confirmed harmless here; treat as unconfirmed, not as "known fine," until actually tested.
2. **`PriceAware.sol`**: `[ERR] L27 ctx=if: 'blockLastUpdated' not in struct 'tokenPrice'` and a follow-on `else: target join not found`. `tokenPrice` is `TokenPrice storage tokenPrice = tokenPrices[token];` — a mapping-to-struct access, and `TokenPrice` is declared file-level in the *same* file, so this isn't a cross-file resolution question the way the `ICSSRRouter` one was. This looks more like it could be a genuine instance of the same "struct member fields empty at this call path" family as the `poolInfo`/`lf` bugs already logged above — **not confirmed**, just flagged; whether it actually blocks `web3bugs_3_H_05`'s real analysis run is exactly the kind of thing the deferred execution pass (user: "실제 실행은 차후에") will surface.

`web3bugs_3_H_05`'s contraction, dependencies, and case JSON (`evaluation/RQ1/cases/web3bugs_3_H_05/web3bugs_3_H_05.json`) are all built and ready; actually running it through `main.py` — which would confirm or refute both warnings above, and confirm/refute the predicted Warning outcome from the `@LocalVar`-parameter-only constraint (see `phase_reviews/06_web3bugs_3_H_05/analysis.md`, R1-6) — is deferred per user instruction.
