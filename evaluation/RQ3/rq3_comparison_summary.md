# RQ3: Comparison Analysis Summary

## Overview

Comparison of **IntentChecker** against **GPTScan** and **ScType** on **20 annotated cases**
containing numeric logic errors (erroneous accounting, inconsistent state updates, etc.)
in Solidity smart contracts.

- **IntentChecker**: Symbolic abstract interpretation with Z3 solver, guided by developer-specified intent annotations (pre/post-conditions).
- **ScType**: Static type-checking for financial type consistency, requiring per-contract type annotation files.
- **GPTScan**: LLM-based multi-step analysis pipeline targeting DeFi-specific vulnerability patterns (price manipulation, slippage, etc.).
- **NumScout**: _(Results pending; placeholder included for future update.)_

---

## 1. Detection Rates

| Tool | Detected | Total Evaluated | Rate |
|------|----------|----------------|------|
| IntentChecker | 20 | 20 | 100.0% |
| ScType | 4 | 7 | 57.1% |
| GPTScan (strict) | 0 | 20 | 0.0% |
| GPTScan (loose) | 11 | 20 | 55.0% |
| NumScout | TBD | TBD | TBD |

**Definitions:**
- **Strict detection**: The tool identifies the same *type* of bug as the ground truth
  (erroneous accounting / numeric logic error). GPTScan has no rules for this category,
  so strict detection is 0%.
- **Loose detection**: The tool produces *any* finding on the target .sol file, regardless
  of whether the finding matches the actual bug type.
- **ScType applicability**: Only 7 of 20 cases have ScType type annotation files.
  The remaining 13 cases are marked N/A.

---

## 2. Detection Matrix (all 20 annotated cases)

| Case | Contract.Function | IC | ScType | GPTScan (strict) | GPTScan (loose) | NumScout |
|------|-------------------|-----|--------|-------------------|-----------------|----------|
| BoostToken_ind | BoostToken.sendETHToTeam | Y | N/A | N | N | TBD |
| BoostToken_op | BoostToken.sendETHToTeam | Y | N/A | N | N | TBD |
| HIT | HIT.getTokens | Y | N/A | N | N | TBD |
| Nokon | Nokon.buy | Y | N/A | N | N | TBD |
| SwordCrowdsale | SwordCrowdsale.refundMoney | Y | N/A | N | N | TBD |
| WANGMI | WANGMI._transfer | Y | N/A | N | Y | TBD |
| 101_H_01 | LenderPool._calculatePrincipalWithdrawable | Y | N | N | Y | TBD |
| 45_H_01 | UToken.borrow | Y | N/A | N | Y | TBD |
| 47_H_02 | WrappedIbbtcEth.transferFrom | Y | Y | N | N | TBD |
| 51_H_02 | SwapUtils.rampTargetPrice | Y | N/A | N | Y | TBD |
| 56_H_02 | CDP.update | Y | N | N | N | TBD |
| 58_H_02 | LpIssuer._chargeFees | Y | N/A | N | Y | TBD |
| 5_H_07 | Utils.calcAsymmetricShare | Y | Y | N | Y | TBD |
| 5_H_08 | Utils.calcLiquidityUnits | Y | Y | N | Y | TBD |
| 5_H_12 | Pools.getAddedAmount | Y | N/A | N | Y | TBD |
| 60_H_01 | OptimisticLedgerLib.settleAccount | Y | Y | N | N | TBD |
| 62_H_08 | Stream.updateStreamInternal | Y | N/A | N | N | TBD |
| 70_H_10 | LiquidityBasedTWAP.syncVaderPrice | Y | N | N | Y | TBD |
| 77_H_01 | MathLib.calculateLiquidityTokenQtyForSingleAssetEntry | Y | N/A | N | Y | TBD |
| 78_H_02 | RebaseProxy.mint | Y | N/A | N | Y | TBD |

---

## 3. Analysis Time

| Metric | IntentChecker | ScType | GPTScan |
|--------|---------------|--------|---------|
| Mean | 4.5s | 13.9s | 267s |
| Median | 2.9s | 11.5s | 153s |
| Min | 0.4s | 3.0s | 1s |
| Max | 18.4s | 25.8s | 750s |
| Samples | 20 | 21 (3 runs x 7 cases) | 20 |

GPTScan is ~59x slower than IntentChecker on average.
IntentChecker and ScType are both local analysis tools that complete in seconds.

---

## 4. GPTScan Detail (per annotated case)

GPTScan detects *price-manipulation*, *no-slippage-limit-check*, *first-deposit*, etc.
These are fundamentally **different bug types** from the numeric logic errors targeted
in this study. Even when GPTScan produces a finding on the target file (loose match),
it is identifying a different vulnerability.

| Case | Loose Match | Patterns on Target File | Time |
|------|-------------|------------------------|------|
| BoostToken_ind | No match | - | 69s |
| BoostToken_op | No match | - | 66s |
| HIT | No match | - | 9s |
| Nokon | No match | - | 26s |
| SwordCrowdsale | No match | - | 1s |
| WANGMI | File match | no-slippage-limit-check | 36s |
| 101_H_01 | File match | price-manipulation; wrong-order-interest | 750s |
| 45_H_01 | File match | price-manipulation | 271s |
| 47_H_02 | No match | - | 12s |
| 51_H_02 | File match | no-slippage-limit-check; price-manipulation | 129s |
| 56_H_02 | No match | - | 621s |
| 58_H_02 | File match | price-manipulation | 390s |
| 5_H_07 | File match | price-manipulation | 543s |
| 5_H_08 | File match | price-manipulation | 514s |
| 5_H_12 | File match | no-slippage-limit-check; price-manipulation | 529s |
| 60_H_01 | No match | - | 25s |
| 62_H_08 | No match | - | 96s |
| 70_H_10 | File match | price-manipulation | 499s |
| 77_H_01 | File match | price-manipulation | 177s |
| 78_H_02 | File match | price-manipulation | 573s |

---

## 5. ScType Detail (per annotated case)

ScType checks financial type consistency. It can only be applied to contracts where
type annotation files exist (7/20 cases overlap). Times reported are averages
over 3 runs (stdev in parentheses where available).

| Case | Result | Avg Time (stdev) |
|------|--------|-----------------|
| BoostToken_ind | N/A (no type file) | - |
| BoostToken_op | N/A (no type file) | - |
| HIT | N/A (no type file) | - |
| Nokon | N/A (no type file) | - |
| SwordCrowdsale | N/A (no type file) | - |
| WANGMI | N/A (no type file) | - |
| 101_H_01 | Not detected | 22.8s (1.19) |
| 45_H_01 | N/A (no type file) | - |
| 47_H_02 | Detected | 3.2s (0.24) |
| 51_H_02 | N/A (no type file) | - |
| 56_H_02 | Not detected | 22.9s (2.51) |
| 58_H_02 | N/A (no type file) | - |
| 5_H_07 | Detected | 8.6s (0.06) |
| 5_H_08 | Detected | 8.7s (0.09) |
| 5_H_12 | N/A (no type file) | - |
| 60_H_01 | Detected | 12.0s (1.96) |
| 62_H_08 | N/A (no type file) | - |
| 70_H_10 | Not detected | 19.1s (1.32) |
| 77_H_01 | N/A (no type file) | - |
| 78_H_02 | N/A (no type file) | - |

---

## 6. Key Findings

### 6.1 Coverage Gap
GPTScan has **no detection rules** for numeric logic errors (erroneous accounting,
operator order issues, precision loss, etc.). Its rule set targets price manipulation,
slippage, and related DeFi-specific patterns. This means GPTScan **structurally cannot
detect** the class of bugs IntentChecker targets, resulting in 0% strict detection rate.

Even in the loose comparison, GPTScan's 11/20 file-level matches all correspond
to *different* vulnerability types (e.g., price-manipulation on the same file), not the
actual numeric logic error.

### 6.2 Complementarity with ScType
- **Detection overlap**: ScType detected **4/7** of the overlapping cases.
  IntentChecker detected all 7/7 of the same cases.
- **Different properties checked**: ScType verifies *financial type consistency*
  (e.g., mixing token types in arithmetic), while IntentChecker verifies
  *developer intent* (pre/post-conditions on numeric values).
- ScType requires type annotation files per contract; IntentChecker requires
  intent annotations (pre/post-conditions). Both need manual specification,
  but check **orthogonal properties**.
- **Non-overlapping cases**: 13 annotated cases cannot be evaluated by ScType
  (no type files), but are all detected by IntentChecker.
- **False negatives in ScType**: 3 cases where ScType has type files
  but fails to detect the bug (e.g., the bug is not a type inconsistency).

### 6.3 Speed Comparison
- IntentChecker (4.5s avg) and ScType (13.9s avg)
  are **local analysis tools** that complete in seconds.
- GPTScan (267s avg, ~59x slower) is significantly
  slower due to its multi-step LLM-based pipeline.
- IntentChecker's speed makes it suitable for CI/CD integration and interactive developer
  workflows.

### 6.4 Annotation Nature
| Aspect | IntentChecker | ScType | GPTScan |
|--------|---------------|--------|---------|
| Annotation needed | Developer intent (pre/post) | Financial types | None |
| Bug types detected | Numeric logic errors | Type inconsistency | Price manipulation, slippage |
| Analysis approach | Abstract interpretation + Z3 | Type inference | LLM + static analysis |
| Avg. time | 4.5s | 13.9s | 267s |
| Coverage | 20/20 (100%) | 4/7 (57%) | 0/20 (strict: 0%) |

---

## 7. Implications for Paper

1. **IntentChecker fills a detection gap**: No existing tool specifically targets
   numeric logic errors via developer intent verification. GPTScan's rule set does
   not cover this category at all.
2. **Complementary to ScType**: The two tools check different semantic properties
   and could be combined for broader coverage. IntentChecker catches all 3
   cases that ScType misses among the overlapping set.
3. **Speed advantage over LLM-based tools**: IntentChecker's symbolic approach
   provides fast (~59x faster than GPTScan), deterministic analysis
   suitable for CI/CD integration.
4. **Annotation trade-off**: While IntentChecker requires intent annotations,
   this is analogous to type annotations for ScType. The annotations serve as
   both specification and documentation of developer intent.
5. **Broader applicability**: IntentChecker works on all 20 cases regardless of
   contract structure, while ScType is limited to the 7 cases with available
   type annotation files.

---

## 8. Threats to Validity

1. **Internal validity -- annotation bias**: IntentChecker's 100% detection rate is
   by design: the 20 cases were annotated with intent specifications that, when
   violated, confirm the known bug. This reflects the tool's purpose (checking
   developer-specified properties) but does not measure the effort or correctness
   of writing annotations.
2. **Construct validity -- strict vs. loose**: The strict/loose distinction for GPTScan
   is important. GPTScan was not designed for numeric logic errors, so its 0% strict
   rate reflects a scope mismatch rather than a quality deficiency.
3. **External validity -- limited ScType overlap**: Only 7/20 cases could be
   evaluated with ScType due to the availability of type annotation files. Results
   may differ with a larger overlap set.
4. **Generalizability**: The 20 annotated cases are drawn from Web3Bugs and NumScout
   datasets. Results may not generalize to all Solidity codebases or vulnerability types.
5. **Single-run GPTScan**: GPTScan was executed once (run1). LLM-based tools may
   produce non-deterministic results across runs, though GPTScan's pipeline includes
   deterministic static analysis steps.

---

## 9. NumScout (Pending)

NumScout results will be added in a future update. The comparison table, heatmap, and
detection rate chart include placeholder columns for NumScout. Once NumScout data is
available, the script can be re-run to produce updated outputs.

---

*Generated by `rq3_comparison.py`*
