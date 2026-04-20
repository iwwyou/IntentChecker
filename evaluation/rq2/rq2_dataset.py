"""RQ2 dataset — unified view of annotated (VIOLATED) and annotation-limited (L4/L5) cases.

Combines two case populations that together answer RQ2 (annotation effectiveness):
  - 20 VIOLATED cases : detection succeeded because an annotation was written.
                        Each is tagged as direct (@Post/@IReturn-style) or
                        indirect (@During-style) based on the annotation family
                        observed in `evaluation/RQ1/rq2_results.csv`.
  - 34 not_detectable : L4/L5 cases imported from `l4_l5_classification.py`.
                        These are the annotation-level limits analyzed in
                        `l4_l5_case_review.md`.

Run to regenerate `rq2_dataset.csv`:
    .venv/Scripts/python.exe evaluation/rq2/rq2_dataset.py
"""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass, asdict, field
from pathlib import Path

from l4_l5_classification import CASES as L4L5_CASES, CaseClassification


# --------------------------------------------------------------------------- #
# Unified row                                                                 #
# --------------------------------------------------------------------------- #

@dataclass
class RQ2Entry:
    # Identity
    id: str
    source: str                    # "numscout" | "web3bugs"
    contract: str
    function: str
    bug_lines: str

    # RQ2 outcome
    result: str                    # "VIOLATED" | "not_detectable"
    annotation_kind: str = ""      # "direct" | "indirect" | "" (for not_detectable)
    annotation_family: str = ""    # e.g. "post_EntryExit", "during_RelationalCmp"

    # L4/L5 classification (empty for VIOLATED)
    final_class: str = ""          # "L4a" | ... | "L5b"
    bug_category: str = ""         # "value" | "algorithm"
    proxy_type: str = ""           # "A" | "B"
    l4a_axis: str = ""             # "alpha" | "beta" | "gamma" | "alpha_and_gamma"
    bug_awareness: str = ""        # "consistency" | "domain" | "mixed"
    silent_sanction: str = ""      # "Y" | "N"
    aux_injection_viable: str = "" # "Y" | "N" | "Y_hard"

    notes: str = ""


# --------------------------------------------------------------------------- #
# 20 VIOLATED cases — annotation kind derived from rq2_results.csv            #
# --------------------------------------------------------------------------- #
# Mapping rule (column with count >0 in rq2_results.csv):
#   during_*  -> kind="indirect",  family="during_<Subtype>"
#   post_*    -> kind="direct",    family="post_<Subtype>"
#
# Direct  (8): annotation names the expected exit value directly
#              (@Post, @IReturn). Fix-equivalent.
# Indirect(12): annotation monitors an intermediate transition
#              (@During).  Awareness signal rather than exact spec.

VIOLATED_CASES: list[RQ2Entry] = [
    RQ2Entry(
        id="numscout_WANGMI", source="numscout",
        contract="WANGMI", function="_transfer", bug_lines="428",
        result="VIOLATED",
        annotation_kind="indirect", annotation_family="during_BeforeAfter",
        notes="div_in_path: fees.mul(sellLiquidityFee).div(sellTotalFees) precision loss",
    ),
    RQ2Entry(
        id="numscout_Nokon", source="numscout",
        contract="Nokon", function="buy", bug_lines="51",
        result="VIOLATED",
        annotation_kind="indirect", annotation_family="during_RelationalCmp",
        notes="exchange_problem: division-first precision loss",
    ),
    RQ2Entry(
        id="numscout_SwordCrowdsale", source="numscout",
        contract="SwordCrowdsale", function="refundMoney", bug_lines="33",
        result="VIOLATED",
        annotation_kind="direct", annotation_family="post_EntryExit",
        notes="greedy_contract: weiRaised -= amount missing",
    ),
    RQ2Entry(
        id="numscout_BoostToken_operator", source="numscout",
        contract="BoostToken", function="sendETHToTeam", bug_lines="141;142",
        result="VIOLATED",
        annotation_kind="indirect", annotation_family="during_FunctionArg",
        notes="operator_order_issue: div-then-mul precision loss",
    ),
    RQ2Entry(
        id="numscout_BoostToken_indivisible", source="numscout",
        contract="BoostToken", function="sendETHToTeam", bug_lines="933;934;935;936",
        result="VIOLATED",
        annotation_kind="indirect", annotation_family="during_FunctionArg",
        notes="indivisible_amount: divisor too large yields zero",
    ),
    RQ2Entry(
        id="numscout_HIT", source="numscout",
        contract="HIT", function="getTokens", bug_lines="126;144",
        result="VIOLATED",
        annotation_kind="indirect", annotation_family="during_Implication",
        notes="profit_opportunity: rounding favors caller",
    ),
    RQ2Entry(
        id="web3bugs_5_H_07", source="web3bugs",
        contract="Utils", function="calcAsymmetricShare", bug_lines="273",
        result="VIOLATED",
        annotation_kind="indirect", annotation_family="during_RelationalCmp",
        notes="wrong calcAsymmetricShare calculation",
    ),
    RQ2Entry(
        id="web3bugs_5_H_08", source="web3bugs",
        contract="Utils", function="calcLiquidityUnits", bug_lines="239",
        result="VIOLATED",
        annotation_kind="indirect", annotation_family="during_RelationalCmp",
        notes="wrong liquidity units calculation",
    ),
    RQ2Entry(
        id="web3bugs_5_H_12", source="web3bugs",
        contract="Pools", function="getAddedAmount", bug_lines="201",
        result="VIOLATED",
        annotation_kind="direct", annotation_family="post_ReturnExprCmp",
        notes="getAddedAmount may return wrong results",
    ),
    RQ2Entry(
        id="web3bugs_45_H_01", source="web3bugs",
        contract="UToken", function="borrow", bug_lines="403;409;413",
        result="VIOLATED",
        annotation_kind="indirect", annotation_family="during_BeforeAfter",
        notes="borrow must accrueInterest first",
    ),
    RQ2Entry(
        id="web3bugs_47_H_02", source="web3bugs",
        contract="WrappedIbbtcEth", function="transferFrom", bug_lines="111",
        result="VIOLATED",
        annotation_kind="direct", annotation_family="post_RelationalCmp",
        notes="approved spender can spend too many tokens",
    ),
    RQ2Entry(
        id="web3bugs_51_H_02", source="web3bugs",
        contract="SwapUtils", function="rampTargetPrice", bug_lines="1573;1578",
        result="VIOLATED",
        annotation_kind="indirect", annotation_family="during_Feasible",
        notes="cannot update target price",
    ),
    RQ2Entry(
        id="web3bugs_56_H_02", source="web3bugs",
        contract="CDP", function="update", bug_lines="39",
        result="VIOLATED",
        annotation_kind="direct", annotation_family="post_EntryExit",
        notes="CDP.update overwrites user credit on positive increment",
    ),
    RQ2Entry(
        id="web3bugs_58_H_02", source="web3bugs",
        contract="LpIssuer", function="_chargeFees", bug_lines="270",
        result="VIOLATED",
        annotation_kind="indirect", annotation_family="during_RelationalCmp",
        notes="performanceFee wrong implementation",
    ),
    RQ2Entry(
        id="web3bugs_60_H_01", source="web3bugs",
        contract="OptimisticLedgerLib", function="settleAccount", bug_lines="68;73",
        result="VIOLATED",
        annotation_kind="indirect", annotation_family="during_RelationalCmp",
        notes="wrong shortfall calculation",
    ),
    RQ2Entry(
        id="web3bugs_62_H_08", source="web3bugs",
        contract="Stream", function="updateStreamInternal", bug_lines="226;229;230",
        result="VIOLATED",
        annotation_kind="direct", annotation_family="post_RelationalCmp",
        notes="ts.tokens sometimes calculated incorrectly",
    ),
    RQ2Entry(
        id="web3bugs_70_H_10", source="web3bugs",
        contract="LiquidityBasedTWAP", function="syncVaderPrice", bug_lines="187",
        result="VIOLATED",
        annotation_kind="direct", annotation_family="post_VarChanged",
        notes="previousPrices never updated upon syncing token price",
    ),
    RQ2Entry(
        id="web3bugs_77_H_01", source="web3bugs",
        contract="MathLib", function="calculateLiquidityTokenQtyForSingleAssetEntry",
        bug_lines="174;175;176;177;178;179;180;181;182;183;184;185",
        result="VIOLATED",
        annotation_kind="direct", annotation_family="post_ReturnExprCmp",
        notes="single-asset-entry computation flaw",
    ),
    RQ2Entry(
        id="web3bugs_78_H_02", source="web3bugs",
        contract="RebaseProxy", function="mint", bug_lines="36",
        result="VIOLATED",
        annotation_kind="direct", annotation_family="post_EntryExit",
        notes="wrong minting amount",
    ),
    RQ2Entry(
        id="web3bugs_101_H_01", source="web3bugs",
        contract="LenderPool", function="_calculatePrincipalWithdrawable",
        bug_lines="678;679;680",
        result="VIOLATED",
        annotation_kind="indirect", annotation_family="during_RelationalCmp",
        notes="principal withdrawable incorrectly calculated with non-zero start fee",
    ),
]


# --------------------------------------------------------------------------- #
# Bridge 34 L4/L5 cases into the unified row                                  #
# --------------------------------------------------------------------------- #

def from_l4l5(c: CaseClassification) -> RQ2Entry:
    return RQ2Entry(
        id=c.id,
        source="web3bugs",
        contract=c.contract,
        function=c.function,
        bug_lines=c.bug_lines,
        result="not_detectable",
        annotation_kind="",
        annotation_family="",
        final_class=c.final_class,
        bug_category=c.bug_category,
        proxy_type=c.proxy_type,
        l4a_axis=c.l4a_axis,
        bug_awareness=c.bug_awareness,
        silent_sanction="Y" if c.silent_sanction else "N",
        aux_injection_viable=c.aux_injection_viable,
        notes=c.notes,
    )


def all_entries() -> list[RQ2Entry]:
    return list(VIOLATED_CASES) + [from_l4l5(c) for c in L4L5_CASES]


# --------------------------------------------------------------------------- #
# IO                                                                          #
# --------------------------------------------------------------------------- #

def to_csv(path: Path | str = "rq2_dataset.csv") -> None:
    path = Path(path)
    rows = all_entries()
    if not rows:
        return
    fieldnames = list(asdict(rows[0]).keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(asdict(r))
    print(f"Wrote {len(rows)} rows to {path}")


def stats() -> None:
    rows = all_entries()
    print(f"\n=== RQ2 dataset ({len(rows)} rows) ===")
    print(f"  Result         : {dict(Counter(r.result for r in rows))}")
    kinds = Counter(r.annotation_kind for r in rows if r.annotation_kind)
    print(f"  Annotation kind: {dict(kinds)}  (VIOLATED only)")
    fam = Counter(r.annotation_family for r in rows if r.annotation_family)
    print(f"  Annotation fam : {dict(fam)}")
    classes = Counter(r.final_class for r in rows if r.final_class)
    print(f"  L4/L5 class    : {dict(classes)}")


if __name__ == "__main__":
    script_dir = Path(__file__).parent
    to_csv(script_dir / "rq2_dataset.csv")
    stats()
