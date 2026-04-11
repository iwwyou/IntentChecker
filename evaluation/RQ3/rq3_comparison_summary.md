# RQ3: Comparison Analysis Summary

## Overview

Comparison of **IntentChecker** against **GPTScan** and **ScType** on **20 annotated cases**
containing numeric logic errors (erroneous accounting, inconsistent state updates, etc.)
in Solidity smart contracts.

---

## 1. Detection Rates

| Tool | Detected | Total | Rate |
|------|----------|-------|------|
| IntentChecker | 20 | 20 | 100% |
| GPTScan (strict) | 0 | 20 | 0% |
| GPTScan (loose) | 11 | 20 | 55% |
| ScType | 4 | 7 | 57% |

**Definitions:**
- **Strict detection**: The tool identifies the same *type* of bug as the ground truth
  (erroneous accounting / numeric logic error).
- **Loose detection**: The tool produces *any* finding on the target file, regardless
  of whether the finding matches the actual bug type.
- **ScType applicability**: Only 7 of 20 cases have ScType type annotation files.
  The remaining 13 cases are marked N/A.

---

## 2. Analysis Time

| Tool | mean=4.4s, median=2.0s, min=0.4s, max=18.4s |
|------|---------------------------------------------|

| Metric | IntentChecker | ScType | GPTScan |
|--------|---------------|--------|---------|
| Mean | 4.4s | 13.9s | 267s |
| Median | 2.0s | 11.5s | 153s |
| Min | 0.4s | 3.0s | 1s |
| Max | 18.4s | 25.8s | 750s |

IntentChecker and ScType are orders of magnitude faster than GPTScan.

---

## 3. GPTScan Detail (per annotated case)

GPTScan detects *price-manipulation*, *no-slippage-limit-check*, *first-deposit*, etc.
These are fundamentally **different bug types** from the numeric logic errors targeted
in this study. Even when GPTScan produces a finding on the target file (loose match),
it is identifying a different vulnerability.

| Case ID | Loose Match | Patterns on Target File | Time |
|---------|-------------|------------------------|------|
| numscout_BoostToken_indivisible | No match | - | 69s |
| numscout_BoostToken_operator | No match | - | 66s |
| numscout_HIT | No match | - | 9s |
| numscout_Nokon | No match | - | 26s |
| numscout_SwordCrowdsale | No match | - | 1s |
| numscout_WANGMI | File match | no-slippage-limit-check | 36s |
| web3bugs_101_H_01 | File match | price-manipulation; wrong-order-interest | 750s |
| web3bugs_45_H_01 | File match | price-manipulation | 271s |
| web3bugs_47_H_02 | No match | - | 12s |
| web3bugs_51_H_02 | File match | no-slippage-limit-check; price-manipulation | 129s |
| web3bugs_56_H_02 | No match | - | 621s |
| web3bugs_58_H_02 | File match | price-manipulation | 390s |
| web3bugs_5_H_07 | File match | price-manipulation | 543s |
| web3bugs_5_H_08 | File match | price-manipulation | 514s |
| web3bugs_5_H_12 | File match | no-slippage-limit-check; price-manipulation | 529s |
| web3bugs_60_H_01 | No match | - | 25s |
| web3bugs_62_H_08 | No match | - | 96s |
| web3bugs_70_H_10 | File match | price-manipulation | 499s |
| web3bugs_77_H_01 | File match | price-manipulation | 177s |
| web3bugs_78_H_02 | File match | price-manipulation | 573s |

---

## 4. ScType Detail (per annotated case)

ScType checks financial type consistency. It can only be applied to contracts where
type annotation files exist (7/20 cases overlap).

| Case ID | Result | Avg Time |
|---------|--------|----------|
| numscout_BoostToken_indivisible | N/A (no type file) | - |
| numscout_BoostToken_operator | N/A (no type file) | - |
| numscout_HIT | N/A (no type file) | - |
| numscout_Nokon | N/A (no type file) | - |
| numscout_SwordCrowdsale | N/A (no type file) | - |
| numscout_WANGMI | N/A (no type file) | - |
| web3bugs_101_H_01 | Not detected | 22.8s |
| web3bugs_45_H_01 | N/A (no type file) | - |
| web3bugs_47_H_02 | Detected | 3.2s |
| web3bugs_51_H_02 | N/A (no type file) | - |
| web3bugs_56_H_02 | Not detected | 22.9s |
| web3bugs_58_H_02 | N/A (no type file) | - |
| web3bugs_5_H_07 | Detected | 8.6s |
| web3bugs_5_H_08 | Detected | 8.7s |
| web3bugs_5_H_12 | N/A (no type file) | - |
| web3bugs_60_H_01 | Detected | 12.0s |
| web3bugs_62_H_08 | N/A (no type file) | - |
| web3bugs_70_H_10 | Not detected | 19.1s |
| web3bugs_77_H_01 | N/A (no type file) | - |
| web3bugs_78_H_02 | N/A (no type file) | - |

---

## 5. Key Findings

### 5.1 Coverage Gap
GPTScan has **no detection rules** for numeric logic errors (erroneous accounting,
operator order issues, precision loss, etc.). Its rule set targets price manipulation,
slippage, and related DeFi-specific patterns. This means GPTScan **structurally cannot
detect** the class of bugs IntentChecker targets, resulting in 0% strict detection.

### 5.2 Complementarity with ScType
- **Overlap**: ScType detected **4/7** of the overlapping cases.
  IntentChecker detected all 7/7 of the same cases.
- **Different properties checked**: ScType verifies *financial type consistency*
  (e.g., mixing token types in arithmetic), while IntentChecker verifies
  *developer intent* (pre/post-conditions on numeric values).
- ScType requires type annotation files per contract; IntentChecker requires
  intent annotations (pre/post-conditions). Both need manual specification,
  but check orthogonal properties.
- **Non-overlapping cases**: 13 annotated cases cannot be evaluated by ScType
  (no type files), but are all detected by IntentChecker.

### 5.3 Speed Comparison
- IntentChecker (4.4s avg) and ScType (13.9s avg)
  are **local analysis tools** that complete in seconds.
- GPTScan (267s avg) is significantly slower due to its
  multi-step LLM-based pipeline.

### 5.4 Annotation Nature
| Aspect | IntentChecker | ScType | GPTScan |
|--------|---------------|--------|---------|
| Annotation needed | Developer intent (pre/post) | Financial types | None |
| Bug types detected | Numeric logic errors | Type inconsistency | Price manipulation, slippage |
| Analysis approach | Symbolic (Z3) | Type inference | LLM + static analysis |
| Avg. time | 4.4s | 13.9s | 267s |

---

## 6. Implications for Paper

1. **IntentChecker fills a detection gap**: No existing tool specifically targets
   numeric logic errors via developer intent verification.
2. **Complementary to ScType**: The two tools check different semantic properties
   and could be combined for broader coverage.
3. **Speed advantage over LLM-based tools**: IntentChecker's symbolic approach
   provides fast, deterministic analysis suitable for CI/CD integration.
4. **Annotation trade-off**: While IntentChecker requires intent annotations,
   this is analogous to type annotations for ScType. The annotations serve as
   both specification and documentation.

---

*Generated by `rq3_comparison.py`*
