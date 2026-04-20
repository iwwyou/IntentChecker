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
    # L5-specific
    bug_awareness: str = ""                        # "consistency" | "domain" | "mixed" | ""


CASES: list[CaseClassification] = [
    # ---------------------------------------------------------------- L4a ---
    CaseClassification(
        id="web3bugs_25_H_01",
        contract="CompositeMultiOracle",
        function="_peek;_get",
        bug_lines="116;126",
        original_class="L4a",
        final_class="L4a",
        reclass_reason="A_candidate_resolved_to_B_proxy_unreliable_depends_on_setSource_invariant_not_code_enforced",
        bug_category="value",
        proxy_type="B",
        l4a_axis="alpha",
        primary_G=["G1", "G3"],
        silent_sanction=True,
        aux_injection_viable="Y",
        intent_level_blocker=True,
        secondary_concerns="latent_invariant_dependent_proxy_source_decimals_equals_oracle_decimals_by_setSource_construction_only",
        notes="runtime_equivalent_in_alcueca_reading_but_audit_accepts_as_bug_under_cmichel_framing_Type_B_proxy_unreliable",
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
    CaseClassification(
        id="web3bugs_52_H_15",
        contract="VaderRouter",
        function="_swap",
        bug_lines="326",
        original_class="L4b",
        final_class="L4b",
        reclass_reason="limitation_types_md_self_inconsistent_L4b_list_and_L5b_examples_both_contain_this_case_I9_principle_picks_L4b",
        bug_category="value",
        proxy_type="B",
        l4a_axis="",
        primary_G=["G1", "G3", "G4", "G8"],
        silent_sanction=True,
        aux_injection_viable="N",
        intent_level_blocker=True,
        secondary_concerns="arg_n_lint_level_excluded_per_I9_router_wrapper_no_state",
        notes="pool_swap_arg_order_reversal_3_path_revert_all_cases_router_wrapper_L4b_archetype",
    ),
    # ------------------------------------------------------------ L4c ---
    CaseClassification(
        id="web3bugs_35_H_10",
        contract="ConcentratedLiquidityPool",
        function="burn",
        bug_lines="264;265",
        original_class="L4c",
        final_class="L4c",
        bug_category="value",
        proxy_type="A",
        l4a_axis="",
        primary_G=["G5"],
        silent_sanction=False,
        aux_injection_viable="Y",
        intent_level_blocker=True,
        secondary_concerns="grammar_postClause_only_qualitative_entry_exit_relOp_no_magnitude_arithmetic",
        notes="only_L4c_case_magnitude_only_diff_Type_A_proxy_in_scope_but_grammar_limit_snapshot_injection_enables_L5_transit",
    ),
    # ------------------------------------------------------------ L4d ---
    CaseClassification(
        id="web3bugs_36_H_02",
        contract="Basket",
        function="auctionBurn",
        bug_lines="102;103;105",
        original_class="L4d",
        final_class="L4d",
        bug_category="algorithm",
        proxy_type="A",
        l4a_axis="",
        primary_G=["G6"],
        silent_sanction=True,
        aux_injection_viable="Y",
        general_specific_boundary=True,
        intent_level_blocker=True,
        secondary_concerns="handleFees_masks_changed_annotation_in_scenario_A_product_invariant_needs_arithmetic_postEntryExit",
        notes="only_L4d_case_multi_var_product_invariant_ibRatio_totalSupply_preservation_merger_candidate_with_L4c_both_grammar_limit",
    ),
    # ------------------------------------------------------------ L4b batch ---
    CaseClassification(
        id="web3bugs_52_H_16",
        contract="VaderRouter",
        function="calculateOutGivenIn",
        bug_lines="488;489;490;491",
        original_class="L4b",
        final_class="L4b",
        reclass_reason="annotation_plans_L5b_but_view_function_no_state_I9_principle_L4b",
        bug_category="value",
        proxy_type="B",
        primary_G=["G1", "G3", "G4"],
        silent_sanction=True,
        aux_injection_viable="N",
        intent_level_blocker=True,
        notes="Case12_52H15_twin_view_version_pool0_pool1_reserve_order_swap",
    ),
    CaseClassification(
        id="web3bugs_58_H_04",
        contract="AaveVault",
        function="tvl;_push",
        bug_lines="47",
        original_class="L4b",
        final_class="L4b",
        reclass_reason="annotation_plans_L5a_but_ordering_problem_not_expressible_L4b_per_function_type",
        bug_category="algorithm",
        proxy_type="B",
        primary_G=["G1", "G3", "G4"],
        silent_sanction=True,
        aux_injection_viable="Y_hard",
        intent_level_blocker=True,
        notes="stale_cache_tvl_ordering_bug_updateTvls_before_deposit_missing_missing_check_family_Case11_twin",
    ),
    CaseClassification(
        id="web3bugs_62_H_01",
        contract="Stream",
        function="recoverTokens",
        bug_lines="654",
        original_class="L4b",
        final_class="L4b",
        reclass_reason="annotation_plans_L5a_but_wrapper_no_state_balanceOf_inline_chain_I9_principle",
        bug_category="algorithm",
        proxy_type="B",
        primary_G=["G1", "G3", "G4"],
        silent_sanction=True,
        aux_injection_viable="Y",
        intent_level_blocker=True,
        notes="missing_formula_term_flashloan_fee_deduction_balanceOf_inline_unbound_Case9_wrapper_family",
    ),
    CaseClassification(
        id="web3bugs_70_H_08",
        contract="VaderReserve",
        function="reimburseImpermanentLoss",
        bug_lines="98;102",
        original_class="L4b",
        final_class="L4b",
        reclass_reason="annotation_plans_L5a_but_wrapper_no_state_parameter_overwrite_original_lost",
        bug_category="value",
        proxy_type="B",
        primary_G=["G1", "G3", "G4"],
        silent_sanction=True,
        aux_injection_viable="Y",
        intent_level_blocker=True,
        notes="scaling_factor_missing_1e18_parameter_overwrite_loses_original_Case1_Case10_wrapper_version",
    ),
    CaseClassification(
        id="web3bugs_83_H_02",
        contract="MasterChef",
        function="deposit",
        bug_lines="170;171;172",
        original_class="L4b",
        final_class="L4b",
        bug_category="algorithm",
        proxy_type="B",
        primary_G=["G3", "G4"],
        silent_sanction=True,
        aux_injection_viable="N",
        intent_level_blocker=True,
        secondary_concerns="fee_recipient_state_slot_absent_from_data_model",
        notes="missing_state_update_fee_recipient_data_model_absence_Case11_twin",
    ),
    CaseClassification(
        id="web3bugs_110_H_01",
        contract="StakedCitadel",
        function="balance",
        bug_lines="293;294",
        original_class="L4b",
        final_class="L4b",
        reclass_reason="annotation_plans_L5a_but_view_function_missing_call_site_G3_I9_L4b",
        bug_category="algorithm",
        proxy_type="B",
        primary_G=["G1", "G3", "G4"],
        silent_sanction=True,
        aux_injection_viable="Y",
        intent_level_blocker=True,
        notes="missing_strategy_balance_call_NatSpec_mentions_vault_plus_strategy_Case11_Case16_Case20_family",
    ),
    # ------------------------------------------------------------ L5a batch ---
    CaseClassification(
        id="web3bugs_35_H_12",
        contract="ConcentratedLiquidityPool",
        function="mint",
        bug_lines="176;184",
        original_class="L5a",
        final_class="L5a",
        bug_category="value",
        proxy_type="A",
        silent_sanction=False,
        aux_injection_viable="",
        intent_level_blocker=False,
        bug_awareness="consistency",
        secondary_concerns="abi_decode_param_L3_partial_debug_annotation_limit",
        notes="secondsPerLiquidity_missing_update_swap_sibling_consistency",
    ),
    CaseClassification(
        id="web3bugs_52_H_23",
        contract="VaderPoolV2",
        function="mintSynth",
        bug_lines="161",
        original_class="L5a",
        final_class="L5a",
        bug_category="value",
        proxy_type="A",
        silent_sanction=False,
        aux_injection_viable="",
        intent_level_blocker=False,
        bug_awareness="domain",
        notes="reserveForeign_missing_deduction_synth_minting_economics_domain_required",
    ),
    CaseClassification(
        id="web3bugs_62_H_03",
        contract="Stream",
        function="claimReward",
        bug_lines="575",
        original_class="L5a",
        final_class="L5a",
        bug_category="value",
        proxy_type="A",
        silent_sanction=False,
        aux_injection_viable="",
        intent_level_blocker=False,
        bug_awareness="consistency",
        notes="rewardTokenAmount_missing_decrement_token_transfer_tracking_pattern",
    ),
    CaseClassification(
        id="web3bugs_62_H_10",
        contract="Stream",
        function="creatorClaimSoldTokens",
        bug_lines="597",
        original_class="L5a",
        final_class="L5a",
        bug_category="value",
        proxy_type="A",
        silent_sanction=False,
        aux_injection_viable="",
        intent_level_blocker=False,
        bug_awareness="consistency",
        notes="Case23_twin_deposit_token_transfer_tracking_missing_update",
    ),
    CaseClassification(
        id="web3bugs_65_H_01",
        contract="Basket",
        function="handleFees",
        bug_lines="136;137",
        original_class="L5a",
        final_class="L5a",
        bug_category="value",
        proxy_type="A",
        silent_sanction=False,
        aux_injection_viable="",
        intent_level_blocker=False,
        bug_awareness="consistency",
        notes="lastFee_missing_update_in_startSupply_zero_branch_inter_branch_inconsistency",
    ),
    CaseClassification(
        id="web3bugs_83_H_01",
        contract="MasterChef",
        function="add",
        bug_lines="89",
        original_class="L5a",
        final_class="L5a",
        bug_category="algorithm",
        proxy_type="A",
        silent_sanction=False,
        aux_injection_viable="",
        intent_level_blocker=False,
        bug_awareness="mixed",
        notes="massUpdatePools_missing_call_before_totalAllocPoint_change_existing_pools_accConcurPerShare_invariant",
    ),
    CaseClassification(
        id="web3bugs_192_H_01",
        contract="Lock",
        function="extendLock",
        bug_lines="90;91",
        original_class="L5a",
        final_class="L5a",
        bug_category="value",
        proxy_type="A",
        silent_sanction=False,
        aux_injection_viable="",
        intent_level_blocker=False,
        bug_awareness="consistency",
        notes="totalLocked_missing_update_lock_sibling_consistency_leads_to_release_underflow",
    ),
    # ------------------------------------------------------------ L5b batch ---
    CaseClassification(
        id="web3bugs_31_H_01",
        contract="MyStrategy",
        function="manualRebalance",
        bug_lines="469;471;477",
        original_class="L5b",
        final_class="L5b",
        bug_category="value",
        proxy_type="A",
        silent_sanction=False,
        aux_injection_viable="",
        intent_level_blocker=False,
        bug_awareness="domain",
        notes="currentLockRatio_dimensional_mismatch_ratio_vs_amount_downstream_usage_analysis_domain",
    ),
    CaseClassification(
        id="web3bugs_35_H_11",
        contract="Ticks",
        function="cross",
        bug_lines="40;49",
        original_class="L5b",
        final_class="L5b",
        bug_category="value",
        proxy_type="A",
        silent_sanction=False,
        aux_injection_viable="",
        intent_level_blocker=False,
        bug_awareness="domain",
        notes="wrong_struct_field_feeGrowthOutside0_vs_1_zeroForOne_token1_outside1_mapping",
    ),
    CaseClassification(
        id="web3bugs_70_H_09",
        contract="USDV",
        function="mint;burn",
        bug_lines="76;109",
        original_class="L5b",
        final_class="L5b",
        bug_category="value",
        proxy_type="A",
        silent_sanction=False,
        aux_injection_viable="",
        intent_level_blocker=False,
        bug_awareness="domain",
        notes="wrong_price_conversion_direction_oracle_spec_dependent",
    ),
    CaseClassification(
        id="web3bugs_79_H_02",
        contract="LaunchEvent",
        function="createPair",
        bug_lines="398",
        original_class="L5b",
        final_class="L5b",
        bug_category="value",
        proxy_type="A",
        silent_sanction=False,
        aux_injection_viable="",
        intent_level_blocker=False,
        bug_awareness="domain",
        notes="wrong_scaling_factor_token_decimals_vs_1e18_natspec_partial_hint",
    ),
    CaseClassification(
        id="web3bugs_101_H_02",
        contract="LenderPool",
        function="terminate",
        bug_lines="389;400",
        original_class="L5b",
        final_class="L5b",
        bug_category="value",
        proxy_type="A",
        silent_sanction=False,
        aux_injection_viable="",
        intent_level_blocker=False,
        bug_awareness="domain",
        notes="token_share_mixing_should_use_sharesHeld_directly_terminate_semantic",
    ),
    CaseClassification(
        id="web3bugs_112_H_01",
        contract="StakerVault",
        function="transfer",
        bug_lines="112;113;117;118",
        original_class="L5b",
        final_class="L5b",
        bug_category="algorithm",
        proxy_type="A",
        silent_sanction=False,
        aux_injection_viable="",
        intent_level_blocker=False,
        bug_awareness="consistency",
        notes="operation_ordering_balance_before_checkpoint_transferFrom_sibling_correct",
    ),
    CaseClassification(
        id="web3bugs_113_H_05",
        contract="NFTPairWithOracle",
        function="_lend",
        bug_lines="316",
        original_class="L5b",
        final_class="L5b",
        bug_category="value",
        proxy_type="A",
        silent_sanction=False,
        aux_injection_viable="",
        intent_level_blocker=False,
        bug_awareness="domain",
        notes="wrong_require_operator_GE_should_be_LE_lender_favorable_direction",
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
    awareness = Counter(c.bug_awareness for c in CASES if c.bug_awareness)
    if awareness:
        print(f"  L5 bug awareness  : {dict(awareness)}")


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
