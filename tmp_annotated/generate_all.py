"""
Generate annotated .sol files for all 7 cases, then run soltotestjson.py on each.
Inserts annotation comment lines at specified positions (bottom-to-top to avoid shifting).
"""
import sys, os, json, subprocess

ROOT = r"C:\Users\isjeon\PycharmProjects\pythonProject\SolidityGuardian"
TMP = os.path.join(ROOT, "tmp_annotated")
CASES_DIR = os.path.join(ROOT, "evaluation", "RQ2", "cases")
SOLTOTESTJSON = os.path.join(ROOT, "soltotestjson.py")

def insert_annotations(sol_path, annotations):
    """
    annotations: list of (line_number_1based, annotation_text)
    Inserts BEFORE the specified line number. Sort bottom-to-top.
    """
    with open(sol_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Sort annotations by line number descending (bottom-to-top) to avoid shift issues
    annotations_sorted = sorted(annotations, key=lambda x: x[0], reverse=True)

    for line_num, text in annotations_sorted:
        # Insert BEFORE line_num (0-indexed: line_num - 1)
        idx = line_num - 1
        # Match indentation of the target line
        if idx < len(lines):
            target_line = lines[idx]
            indent = len(target_line) - len(target_line.lstrip())
            indent_str = target_line[:indent]
        else:
            indent_str = "    "
        lines.insert(idx, indent_str + text + "\n")

    return "".join(lines)

def run_soltotestjson(sol_content, tmp_name, output_path):
    """Write temp .sol, run soltotestjson.py, save JSON output."""
    tmp_sol = os.path.join(TMP, tmp_name)
    with open(tmp_sol, 'w', encoding='utf-8') as f:
        f.write(sol_content)

    result = subprocess.run(
        [sys.executable, SOLTOTESTJSON, tmp_sol],
        capture_output=True, text=True, encoding='utf-8'
    )

    if result.returncode != 0:
        print(f"ERROR running soltotestjson on {tmp_name}: {result.stderr}")
        return False

    # Parse and re-format for consistent output
    json_data = json.loads(result.stdout)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)

    print(f"OK: {output_path} ({len(json_data)} chunks)")
    return True

# ============================================================
# Case 1: WANGMI (div_in_path)
# ============================================================
print("\n=== Case 1: WANGMI ===")
sol_path = os.path.join(ROOT, "Dataset", "Numscout", "contraction", "div_in_path", "WANGMI_contraction.sol")

# Debug annotations: insert BEFORE line 384 (before _transfer body starts, after function signature)
# The function header is at line 383: function _transfer(...) internal override {
# Line 384 is the first statement: require(_from != address(0), ...)
# We insert all debug annotations BEFORE line 384
debug_annotations_wangmi = [
    (384, "// @LocalVar _from = symbolicAddress 1"),
    (384, "// @LocalVar to = symbolicAddress 2"),
    (384, "// @LocalVar amount = [33, 33]"),
    (384, "// @StateVar uniswapV2Pair = symbolicAddress 2"),
    (384, "// @StateVar sellLiquidityFee = [3, 3]"),
    (384, "// @StateVar sellTxFee = [9, 9]"),
    (384, "// @StateVar tokensForLiquidity = [100, 100]"),
    (384, "// @StateVar tokensForTax = [50, 50]"),
    (384, "// @StateVar isLaunched = true"),
    (384, "// @StateVar maxTxLimit = [1000, 1000]"),
    (384, "// @StateVar maxWalletLimit = [10000, 10000]"),
    (384, "// @StateVar swapAtAmount = [10000, 10000]"),
    (384, "// @StateVar swapping = false"),
    (384, "// @StateVar isExcludedFromTxLimit[_from] = true"),
    (384, "// @StateVar isExcludedFromTxLimit[to] = true"),
    (384, "// @StateVar isExcludedFromFees[_from] = false"),
    (384, "// @StateVar isExcludedFromFees[to] = false"),
    (384, "// @StateVar isBlacklisted[_from] = false"),
    (384, "// @StateVar isExcludedFromWalletLimit[to] = true"),
    (384, "// @GlobalVar block.number = [10, 10]"),
    (384, "// @StateVar launchBlock = [5, 5]"),
]

# Intent annotation at original line 428 → after inserting 21 debug lines, it shifts to 428+21=449
# But we insert bottom-to-top, so we specify the ORIGINAL line number
# The intent goes BEFORE line 428 (tokensForLiquidity = tokensForLiquidity.add(...))
intent_annotations_wangmi = [
    (428, "// @During tokensForLiquidity(Before < After)"),
]

all_annotations = debug_annotations_wangmi + intent_annotations_wangmi
annotated = insert_annotations(sol_path, all_annotations)
run_soltotestjson(annotated, "WANGMI_annotated.sol",
                  os.path.join(CASES_DIR, "div_in_path", "WANGMI_input.json"))

# ============================================================
# Case 2: Nokon (exchange_problem)
# ============================================================
print("\n=== Case 2: Nokon ===")
sol_path = os.path.join(ROOT, "Dataset", "Numscout", "contraction", "exchange_problem", "Nokon_contraction.sol")

# Debug at line 49 (before require(presell) - first statement of buy())
# buy() function header is at line 48: function buy() public payable {
# Line 49 is: require(presell, "presell is closed");
debug_annotations_nokon = [
    (49, "// @GlobalVar msg.value = [50000000000500000, 50000000000500000]"),
    (49, "// @StateVar presell = true"),
    (49, "// @StateVar balances[1] = [2000000000000, 2000000000000]"),
]

# Intent at line 51 (amountToBuy calculation)
# Original line 51: uint256 amountToBuy = msg.value / ethRateFix * calculateRate();
intent_annotations_nokon = [
    (51, "// @During amountToBuy * ethRateFix >= msg.value * 250000"),
]

all_annotations = debug_annotations_nokon + intent_annotations_nokon
annotated = insert_annotations(sol_path, all_annotations)
run_soltotestjson(annotated, "Nokon_annotated.sol",
                  os.path.join(CASES_DIR, "exchange_problem", "Nokon_input.json"))

# ============================================================
# Case 3: SwordCrowdsale (greedy_contract)
# ============================================================
print("\n=== Case 3: SwordCrowdsale ===")
sol_path = os.path.join(ROOT, "Dataset", "Numscout", "contraction", "greedy_contract", "SwordCrowdsale_contraction.sol")

# Debug at line 76 (before first statement of refundMoney)
# Line 75: function refundMoney(address payable _address) public onlyOwner {
# Line 76: uint256 amount = contributorList[_address].contributionAmount;
debug_annotations_sword = [
    (76, "// @StateVar contributorList[_address].contributionAmount = [100, 100]"),
    (76, "// @StateVar weiRaised = [1000, 1000]"),
]

# Intent at line 81 is already in the .sol file! Let's verify.
# Line 81: // @Post weiRaised(Entry > Exit)
# So no intent insertion needed.
intent_annotations_sword = []

all_annotations = debug_annotations_sword + intent_annotations_sword
annotated = insert_annotations(sol_path, all_annotations)
run_soltotestjson(annotated, "SwordCrowdsale_annotated.sol",
                  os.path.join(CASES_DIR, "greedy_contract", "SwordCrowdsale_input.json"))

# ============================================================
# Case 4: BoostToken operator_order_issue
# ============================================================
print("\n=== Case 4: BoostToken (operator_order_issue) ===")
sol_path = os.path.join(ROOT, "Dataset", "Numscout", "contraction", "operator_order_issue", "BoostToken_contraction.sol")

# Debug at line 140 (before first statement of sendETHToTeam body)
# Line 139: function sendETHToTeam(uint256 amount) private {
# Line 140: _devWalletAddress.transfer(amount.div(4));
debug_annotations_boost_op = [
    (140, "// @LocalVar amount = [68, 68]"),
]

# Intent at line 141 and 142
# Line 141: _marketingWalletAddress.transfer(amount.div(12).mul(5));
# Line 142: _dipWalletAddress.transfer(amount.div(9).mul(2));
intent_annotations_boost_op = [
    (142, "// @During transfer.arg[0] >= amount * 2 / 9"),
    (141, "// @During transfer.arg[0] >= amount * 5 / 12"),
]

all_annotations = debug_annotations_boost_op + intent_annotations_boost_op
annotated = insert_annotations(sol_path, all_annotations)
run_soltotestjson(annotated, "BoostToken_operator_annotated.sol",
                  os.path.join(CASES_DIR, "operator_order_issue", "BoostToken_input.json"))

# ============================================================
# Case 5: BoostToken indivisible_amount
# ============================================================
print("\n=== Case 5: BoostToken (indivisible_amount) ===")
sol_path = os.path.join(ROOT, "Dataset", "Numscout", "contraction", "indivisible_amount", "BoostToken_contraction.sol")

# Debug at line 135 (before first statement of sendETHToTeam body)
# Line 135: function sendETHToTeam(uint256 amount) private {
# Line 136: _devWalletAddress.transfer(amount.div(4));
debug_annotations_boost_ind = [
    (136, "// @LocalVar amount = [3, 3]"),
]

# Intent at lines 136, 137, 138, 139
# Line 136: _devWalletAddress.transfer(amount.div(4));
# Line 137: _marketingWalletAddress.transfer(amount.div(12).mul(5));
# Line 138: _dipWalletAddress.transfer(amount.div(9).mul(2));
# Line 139: _marketingWalletAddress2.transfer(amount.div(9));
intent_annotations_boost_ind = [
    (139, "// @During transfer.arg[0] > 0"),
    (138, "// @During transfer.arg[0] > 0"),
    (137, "// @During transfer.arg[0] > 0"),
    (136, "// @During transfer.arg[0] > 0"),
]

all_annotations = debug_annotations_boost_ind + intent_annotations_boost_ind
annotated = insert_annotations(sol_path, all_annotations)
run_soltotestjson(annotated, "BoostToken_indivisible_annotated.sol",
                  os.path.join(CASES_DIR, "indivisible_amount", "BoostToken_input.json"))

# ============================================================
# Case 6: HIT (profit_opportunity)
# ============================================================
print("\n=== Case 6: HIT ===")
sol_path = os.path.join(ROOT, "Dataset", "Numscout", "contraction", "profit_opportunity", "HIT_contraction.sol")

# Debug at line 54 (inside getTokens, before first statement)
# Line 54: function getTokens() payable canDistr onlyWhitelist public {
# Line 55: if (value > totalRemaining) {
# Insert debug annotations before line 55
debug_annotations_hit = [
    (55, "// @GlobalVar msg.value = [0, 0]"),
    (55, "// @StateVar value = [5000000000000000000000, 5000000000000000000000]"),
    (55, "// @StateVar totalRemaining = [800000000000000000000000000, 800000000000000000000000000]"),
    (55, "// @StateVar totalDistributed = [200000000000000000000000000, 200000000000000000000000000]"),
    (55, "// @StateVar totalSupply = [1000000000000000000000000000, 1000000000000000000000000000]"),
    (55, "// @StateVar distributionFinished = false"),
    (55, "// @StateVar blacklist[msg.sender] = false"),
]

# Intent at line 69 (distr call)
# Line 69: distr(investor, toGive);
intent_annotations_hit = [
    (69, "// @During toGive => msg.value"),
]

all_annotations = debug_annotations_hit + intent_annotations_hit
annotated = insert_annotations(sol_path, all_annotations)
run_soltotestjson(annotated, "HIT_annotated.sol",
                  os.path.join(CASES_DIR, "profit_opportunity", "HIT_input.json"))

# ============================================================
# Summary
# ============================================================
print("\n=== All cases processed ===")
print("Note: Case 7 was not in the spec (only 6 unique cases described).")
print("Output files:")
for subdir, fname in [
    ("div_in_path", "WANGMI_input.json"),
    ("exchange_problem", "Nokon_input.json"),
    ("greedy_contract", "SwordCrowdsale_input.json"),
    ("operator_order_issue", "BoostToken_input.json"),
    ("indivisible_amount", "BoostToken_input.json"),
    ("profit_opportunity", "HIT_input.json"),
]:
    fpath = os.path.join(CASES_DIR, subdir, fname)
    exists = os.path.exists(fpath)
    print(f"  {subdir}/{fname}: {'EXISTS' if exists else 'MISSING'}")
