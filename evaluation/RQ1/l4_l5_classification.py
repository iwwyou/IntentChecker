"""L4/L5 case classification — source of truth.

Each case reviewed in `l4_l5_case_review.md` is recorded as a structured entry in
CASES. Run this module to regenerate `l4_l5_classification.csv` and print summary
statistics. Downstream scripts can import CASES directly for plotting or cross-tab.

Workflow per case:
  1. Deep-review the case in `l4_l5_case_review.md` (§1–§6).
  2. Append a CaseClassification to CASES below with the verdict.
  3. Run `python l4_l5_classification.py` to regenerate the CSV.

Axes recap (see I8 in review markdown):
  - bug_category : "value" | "algorithm"         (축 1 — bug nature)
  - proxy_type   : "A" | "B" | "A_candidate"     (축 2 — scope proxy presence)
  - l4a_axis     : "alpha" | "beta" | "gamma" | "alpha_and_gamma" | ""
                   alpha = function-call-in-relation
                   beta  = no variable to form relation
                   gamma = multi-point accounting / multi-step
"""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass, asdict, field
from pathlib import Path


@dataclass
class CaseClassification:
    id: str
    contract: str
    function: str
    bug_lines: str                                 # semicolon-separated
    original_class: str                            # L4a / L4b / ... / L5b
    final_class: str
    reclass_reason: str = ""                       # "" if no change
    bug_category: str = ""                         # "value" | "algorithm"
    proxy_type: str = ""                           # "A" | "B" | "A_candidate"
    l4a_axis: str = ""                             # "alpha"|"beta"|"gamma"|"alpha_and_gamma"|""
    primary_G: list[str] = field(default_factory=list)
    silent_sanction: bool = False                  # I5
    aux_injection_viable: str = ""                 # "Y" | "N" | "Y_hard"
    general_specific_boundary: bool = False        # I6
    intent_level_blocker: bool = False             # I7
    secondary_concerns: str = ""                   # L1-L3 etc. notes
    notes: str = ""


CASES: list[CaseClassification] = [
    # ---------------------------------------------------------------- L4a ---
    CaseClassification(
        id="web3bugs_25_H_01",
        contract="CompositeMultiOracle",
        function="_peek;_get",
        bug_lines="116;126",
        original_class="L4a",
        final_class="L4a",
        bug_category="value",
        proxy_type="A_candidate",
        l4a_axis="alpha",
        primary_G=["G1", "G3"],
        silent_sanction=True,
        aux_injection_viable="Y",
        intent_level_blocker=True,
        secondary_concerns="grammar_revision_adds_star_star_so_G2_no_longer_blocker",
        notes="struct_field_proxy_ambiguity_alcueca_vs_cmichel_reading",
    ),
    CaseClassification(
        id="web3bugs_25_H_05",
        contract="CTokenMultiOracle",
        function="_setSource",
        bug_lines="110",
        original_class="L4a",
        final_class="L4a",
        bug_category="value",
        proxy_type="B",
        l4a_axis="beta",
        primary_G=["G1", "G3"],
        silent_sanction=False,
        aux_injection_viable="Y",
        general_specific_boundary=True,
        intent_level_blocker=True,
        notes="purest_Type_B_example_hardcoded_18",
    ),
    CaseClassification(
        id="web3bugs_29_H_05",
        contract="HybridPool",
        function="_nonOptimalMintFee",
        bug_lines="433",
        original_class="L4a",
        final_class="L4a",
        bug_category="algorithm",
        proxy_type="B",
        l4a_axis="alpha",
        primary_G=["G1", "G3"],
        silent_sanction=True,
        aux_injection_viable="Y",
        intent_level_blocker=True,
        notes="grammar_algebraic_coincidence_with_CP_buggy_formula",
    ),
    CaseClassification(
        id="web3bugs_39_H_02",
        contract="Swivel",
        function="exitVaultFillingVaultInitiate",
        bug_lines="280",
        original_class="L4a",
        final_class="L4a",
        reclass_reason="L5b_trial_withdrawn_arg_n_proxy_is_not_intent_level",
        bug_category="algorithm",
        proxy_type="B",
        l4a_axis="gamma",
        primary_G=["G3", "G8"],
        silent_sanction=True,
        aux_injection_viable="N",
        intent_level_blocker=True,
        secondary_concerns="natspec_drives_silent_sanction",
        notes="cross_line_fee_flow_composition_external_ERC20_state",
    ),
    CaseClassification(
        id="web3bugs_51_H_04",
        contract="SwapUtils",
        function="getYC",
        bug_lines="765;767;768",
        original_class="L4a",
        final_class="L4a",
        bug_category="algorithm",
        proxy_type="B",
        l4a_axis="alpha_and_gamma",
        primary_G=["G1", "G3"],
        silent_sanction=True,
        aux_injection_viable="Y_hard",
        intent_level_blocker=True,
        secondary_concerns="nonlinear_boundary_equation_multi_step",
        notes="missing_split_decomposition_dual_A_curve",
    ),
    CaseClassification(
        id="web3bugs_51_H_06",
        contract="SwapUtils",
        function="addLiquidity",
        bug_lines="1231",
        original_class="L4a",
        final_class="L4a",
        bug_category="algorithm",
        proxy_type="B",
        l4a_axis="alpha",
        primary_G=["G1", "G3"],
        silent_sanction=True,
        aux_injection_viable="Y",
        intent_level_blocker=True,
        secondary_concerns="potential_L1a_unverified_unlikely",
        notes="Case5_twin_consistent_A_D_absence",
    ),
    CaseClassification(
        id="web3bugs_59_H_05",
        contract="AuctionEscapeHatch",
        function="exitEarly",
        bug_lines="83;87",
        original_class="L4a",
        final_class="L4a",
        reclass_reason="annotation_plans_md_says_L5b_but_limitation_types_md_says_L4a_objective_judgment_L4a",
        bug_category="algorithm",
        proxy_type="B",
        l4a_axis="alpha",
        primary_G=["G1", "G3", "G8"],
        silent_sanction=True,
        aux_injection_viable="Y",
        intent_level_blocker=True,
        secondary_concerns="annotation_plans_vs_limitation_types_inconsistency_needs_fix",
        notes="Case4_twin_dual_use_value_collapse_pre_vs_post_penalty",
    ),
    CaseClassification(
        id="web3bugs_61_H_01",
        contract="CreditLine",
        function="_borrowTokensToLiquidate",
        bug_lines="1050",
        original_class="L4a",
        final_class="L4a",
        reclass_reason="L5b_trial_withdrawn_arg_n_is_lint_level_I9_principle_semantic_channel_blocked_by_IReturn_arg_indifference",
        bug_category="value",
        proxy_type="B",
        l4a_axis="alpha",
        primary_G=["G1", "G3", "G8"],
        silent_sanction=False,
        aux_injection_viable="N",
        intent_level_blocker=True,
        secondary_concerns="IReturn_arg_indifference_blocks_semantic_distinguishing_same_cell_as_Case2_Case7",
        notes="oracle_arg_order_bug_semantic_channel_L4a_Case2_Case7_twin_Value_TypeB_cell",
    ),
    CaseClassification(
        id="web3bugs_61_H_02",
        contract="SavingsAccountUtil",
        function="savingsAccountTransfer",
        bug_lines="75;77;79",
        original_class="L4a",
        final_class="L4a",
        reclass_reason="annotation_plans_md_said_L5a_but_self_contradictory_limitation_types_md_says_L4a_confirmed",
        bug_category="value",
        proxy_type="B",
        l4a_axis="alpha",
        primary_G=["G1", "G3", "G8"],
        silent_sanction=True,
        aux_injection_viable="Y_hard",
        intent_level_blocker=True,
        secondary_concerns="IReturn_blocked_for_state_modifying_interface_transfer_call",
        notes="Case7_twin_wrapper_return_misrouting_drop_pattern_pps_shares_mismatch",
    ),
    CaseClassification(
        id="web3bugs_61_H_04",
        contract="YearnYield",
        function="getTokensForShares",
        bug_lines="180",
        original_class="L4a",
        final_class="L4a",
        bug_category="value",
        proxy_type="B",
        l4a_axis="alpha",
        primary_G=["G1", "G3"],
        silent_sanction=True,
        aux_injection_viable="Y",
        general_specific_boundary=True,
        intent_level_blocker=True,
        secondary_concerns="grammar_revision_adds_star_star_aux_injection_then_viable_L5_transit",
        notes="Case1_Case2_scaling_trio_decimals_based_L4a_pure_Type_B_version_of_Case1",
    ),
    # ------------------------------------------------------------ L4b ---
    CaseClassification(
        id="web3bugs_17_H_02",
        contract="Buoy3Pool",
        function="safetyCheck",
        bug_lines="88",
        original_class="L4b",
        final_class="L4b",
        reclass_reason="annotation_plans_md_said_L5a_but_post_condition_not_expressible_due_to_missing_scope_vars_limitation_types_L4b_confirmed",
        bug_category="algorithm",
        proxy_type="B",
        l4a_axis="",
        primary_G=["G1", "G3", "G4"],
        silent_sanction=True,
        aux_injection_viable="Y_hard",
        intent_level_blocker=True,
        secondary_concerns="natspec_drives_silent_sanction_incorrect_transitivity_claim_data_model_extension_needed_for_L5_transit",
        notes="view_function_missing_b_c_check_AND_missing_cache_state_var_deepest_L4b_requires_data_model_extension",
    ),
]


def to_csv(path: Path | str = "l4_l5_classification.csv") -> None:
    """Regenerate the classification CSV from CASES."""
    path = Path(path)
    if not CASES:
        return
    fieldnames = list(asdict(CASES[0]).keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for case in CASES:
            row = asdict(case)
            row["primary_G"] = ";".join(row["primary_G"])
            for key in ("silent_sanction", "general_specific_boundary", "intent_level_blocker"):
                row[key] = "Y" if row[key] else "N"
            writer.writerow(row)
    print(f"Wrote {len(CASES)} rows to {path}")


def stats() -> None:
    """Print summary statistics (intermediate — will grow as cases are added)."""
    print(f"\n=== L4/L5 Classification Stats ({len(CASES)}/34 cases reviewed) ===")
    print(f"  Original class    : {dict(Counter(c.original_class for c in CASES))}")
    print(f"  Final class       : {dict(Counter(c.final_class for c in CASES))}")
    reclassified = sum(1 for c in CASES if c.reclass_reason)
    print(f"  Reclassified      : {reclassified}")
    print(f"  Bug category      : {dict(Counter(c.bug_category for c in CASES))}")
    print(f"  Proxy type        : {dict(Counter(c.proxy_type for c in CASES))}")
    axis_counts = Counter(c.l4a_axis for c in CASES if c.l4a_axis)
    print(f"  L4a axis          : {dict(axis_counts)}")
    silent = sum(1 for c in CASES if c.silent_sanction)
    print(f"  Silent sanction   : {silent}")
    aux = Counter(c.aux_injection_viable for c in CASES if c.aux_injection_viable)
    print(f"  Aux injection     : {dict(aux)}")
    g_counter: Counter[str] = Counter()
    for c in CASES:
        g_counter.update(c.primary_G)
    print(f"  Primary G tally   : {dict(g_counter)}")


def matrix_cell(cases: list[CaseClassification]) -> dict[tuple[str, str], list[str]]:
    """Return I8 matrix cell occupancy: (bug_category, proxy_type) -> [case_ids]."""
    cells: dict[tuple[str, str], list[str]] = {}
    for c in cases:
        key = (c.bug_category or "?", c.proxy_type or "?")
        cells.setdefault(key, []).append(c.id)
    return cells


def print_matrix() -> None:
    """Pretty-print the I8 matrix (bug_category × proxy_type)."""
    cells = matrix_cell(CASES)
    print("\n=== I8 Matrix (bug_category × proxy_type) ===")
    for (bc, pt), ids in sorted(cells.items()):
        print(f"  [{bc:>9} | {pt:>13}]  n={len(ids):<2}  {', '.join(ids)}")


if __name__ == "__main__":
    script_dir = Path(__file__).parent
    to_csv(script_dir / "l4_l5_classification.csv")
    stats()
    print_matrix()
