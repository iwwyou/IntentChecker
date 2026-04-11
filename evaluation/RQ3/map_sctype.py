"""Map our 20 annotated cases to ScType benchmark projects."""
import sys
sys.stdout.reconfigure(encoding="utf-8")

# ScType Table 3 projects from paper + test_benchmark_final.sh
sctype_projects = {
    1:  {"name": "MarginSwap", "file": "HourlyBondSubscriptionLending.sol", "contest": "3", "tw": 1, "fp": 0, "tp": 0, "nte": 1, "mte": 0, "time": 8.93},
    2:  {"name": "Vader Protocol p1", "file": "Utils.sol", "contest": "5", "tw": 4, "fp": 1, "tp": 2, "nte": 2, "mte": 0, "time": 28.6},
    3:  {"name": "PoolTogether", "file": "yield-source/", "contest": "45", "tw": 1, "fp": 0, "tp": 1, "nte": 0, "mte": 0, "time": 4.96},
    4:  {"name": "Tracer", "file": "lib/", "contest": "16", "tw": 1, "fp": 0, "tp": 1, "nte": 1, "mte": 1, "time": 110.57},
    5:  {"name": "Yield Micro", "file": "CompositeMultiOracle.sol", "contest": "25", "tw": 2, "fp": 0, "tp": 1, "nte": 1, "mte": 1, "time": 10.39},
    6:  {"name": "Sushi Trident", "file": "HybridPool.sol", "contest": "29", "tw": 0, "fp": 0, "tp": 0, "nte": 4, "mte": 0, "time": 19.64},
    7:  {"name": "yAxis", "file": "Vault.sol", "contest": "56_related", "tw": 4, "fp": 1, "tp": 2, "nte": 1, "mte": 1, "time": 14.81},
    8:  {"name": "BadgerDao", "file": "veCVXStrategy.sol", "contest": "31", "tw": 2, "fp": 0, "tp": 1, "nte": 0, "mte": 0, "time": 14.61},
    10: {"name": "PoolTogether v4", "file": "DrawCalculator.sol", "contest": "34", "tw": 0, "fp": 0, "tp": 0, "nte": 1, "mte": 0, "time": 14.99},
    11: {"name": "Sushi Trident p2", "file": "ConcentratedLiquidityPool.sol", "contest": "35", "tw": 10, "fp": 4, "tp": 2, "nte": 2, "mte": 0, "time": 19.68},
    12: {"name": "Swivel", "file": "Swivel.sol", "contest": "39", "tw": 2, "fp": 0, "tp": 1, "nte": 0, "mte": 0, "time": 15.03},
    14: {"name": "Badger Dao p2", "file": "WrappedIbbtc.sol", "contest": "47", "tw": 2, "fp": 0, "tp": 1, "nte": 0, "mte": 0, "time": 10.31},
    15: {"name": "Vader Protocol p2", "file": "TwapOracle+router", "contest": "52", "tw": 13, "fp": 2, "tp": 6, "nte": 2, "mte": 0, "time": 66.86},
    16: {"name": "yAxis p2", "file": "CDP.sol", "contest": "56", "tw": 0, "fp": 0, "tp": 0, "nte": 1, "mte": 0, "time": 9.58},
    17: {"name": "Malt Finance", "file": "AuctionEscapeHatch+BurnReserveSkew", "contest": "59", "tw": 0, "fp": 0, "tp": 0, "nte": 0, "mte": 0, "time": 21.34},
    18: {"name": "Perennial", "file": "OptimisticLedger.sol", "contest": "60", "tw": 1, "fp": 0, "tp": 1, "nte": 0, "mte": 0, "time": 24.54},
    19: {"name": "Sublime", "file": "CreditLine+YearnYield", "contest": "61", "tw": 5, "fp": 2, "tp": 2, "nte": 0, "mte": 0, "time": 38.17},
    21: {"name": "Vader Protocol p3", "file": "LiquidityBasedTWAP.sol", "contest": "70", "tw": 4, "fp": 0, "tp": 2, "nte": 0, "mte": 0, "time": 14.86},
    22: {"name": "InsureDao", "file": "PoolTemplate.sol", "contest": "71", "tw": 1, "fp": 0, "tp": 0, "nte": 1, "mte": 0, "time": 2.86},
    23: {"name": "Rocket Joe", "file": "LaunchEvent.sol", "contest": "79", "tw": 5, "fp": 1, "tp": 1, "nte": 1, "mte": 0, "time": 2.96},
    24: {"name": "Concur Finance", "file": "MasterChef.sol", "contest": "83", "tw": 0, "fp": 0, "tp": 0, "nte": 0, "mte": 0, "time": 14.66},
    26: {"name": "Sublime p2", "file": "LenderPool.sol", "contest": "101", "tw": 0, "fp": 0, "tp": 0, "nte": 0, "mte": 0, "time": 14.22},
    28: {"name": "Badger Dao p3", "file": "StakedCitadel.sol", "contest": "110", "tw": 0, "fp": 0, "tp": 0, "nte": 0, "mte": 0, "time": 4.0},
}

# Our 20 annotated cases
annotated = [
    ("numscout_WANGMI", "numscout", "", "WANGMI", "_transfer"),
    ("numscout_Nokon", "numscout", "", "Nokon", "buy"),
    ("numscout_SwordCrowdsale", "numscout", "", "SwordCrowdsale", "refundMoney"),
    ("numscout_BoostToken_operator", "numscout", "", "BoostToken", "sendETHToTeam"),
    ("numscout_BoostToken_indivisible", "numscout", "", "BoostToken", "sendETHToTeam"),
    ("numscout_HIT", "numscout", "", "HIT", "getTokens"),
    ("web3bugs_5_H_07", "web3bugs", "5", "Utils", "calcAsymmetricShare"),
    ("web3bugs_5_H_08", "web3bugs", "5", "Utils", "calcLiquidityUnits"),
    ("web3bugs_5_H_12", "web3bugs", "5", "Pools", "getAddedAmount"),
    ("web3bugs_45_H_01", "web3bugs", "45", "UToken", "borrow"),
    ("web3bugs_47_H_02", "web3bugs", "47", "WrappedIbbtcEth", "transferFrom"),
    ("web3bugs_51_H_02", "web3bugs", "51", "SwapUtils", "rampTargetPrice"),
    ("web3bugs_56_H_02", "web3bugs", "56", "CDP", "update"),
    ("web3bugs_58_H_02", "web3bugs", "58", "LpIssuer", "_chargeFees"),
    ("web3bugs_60_H_01", "web3bugs", "60", "OptimisticLedgerLib", "settleAccount"),
    ("web3bugs_62_H_08", "web3bugs", "62", "Stream", "updateStreamInternal"),
    ("web3bugs_70_H_10", "web3bugs", "70", "LiquidityBasedTWAP", "syncVaderPrice"),
    ("web3bugs_77_H_01", "web3bugs", "77", "MathLib", "calculateLiquidityTokenQty"),
    ("web3bugs_78_H_02", "web3bugs", "78", "RebaseProxy", "mint"),
    ("web3bugs_101_H_01", "web3bugs", "101", "LenderPool", "_calculatePrincipalWithdrawable"),
]

# Build contest -> sctype mapping
contest_to_sctype = {}
for idx, proj in sctype_projects.items():
    c = proj["contest"]
    if c and c != "n/a" and "_" not in c:
        contest_to_sctype.setdefault(c, []).append((idx, proj))

print("=== ANNOTATED 20 vs ScType Benchmark ===\n")
header = f"{'case_id':<40} {'contest':<8} {'ScType project':<25} {'ScType file':<30} {'TW':>3} {'FP':>3} {'TP':>3} {'NTE':>4} {'time':>8} {'match'}"
print(header)
print("-" * len(header))

matched_indices = set()
matched_cases = []
unmatched_cases = []

for case_id, src, contest, contract, func in annotated:
    if src == "numscout":
        print(f"{case_id:<40} {'-':<8} {'-':<25} {'-':<30} {'-':>3} {'-':>3} {'-':>3} {'-':>4} {'-':>8} NO (numscout)")
        unmatched_cases.append(case_id)
        continue

    if contest in contest_to_sctype:
        for idx, proj in contest_to_sctype[contest]:
            file_match = (
                contract.lower() in proj["file"].lower()
                or proj["file"].lower().replace(".sol", "") in contract.lower()
            )
            tag = "FILE" if file_match else "CONTEST"
            print(f"{case_id:<40} {contest:<8} {proj['name']:<25} {proj['file']:<30} {proj['tw']:>3} {proj['fp']:>3} {proj['tp']:>3} {proj['nte']:>4} {proj['time']:>7.1f}s {tag}")
            matched_indices.add(idx)
            matched_cases.append((case_id, idx, proj, tag))
    else:
        print(f"{case_id:<40} {contest:<8} {'-':<25} {'-':<30} {'-':>3} {'-':>3} {'-':>3} {'-':>4} {'-':>8} NO")
        unmatched_cases.append(case_id)

print(f"\n=== Summary ===")
print(f"Matched: {len(matched_cases)} case-project pairs")
print(f"Unmatched: {len(unmatched_cases)} cases: {unmatched_cases}")

print(f"\nScType benchmark groups to fetch: {sorted(matched_indices)}")
for idx in sorted(matched_indices):
    p = sctype_projects[idx]
    print(f"  Group {idx}: {p['name']} ({p['file']}) - contest {p['contest']}")
