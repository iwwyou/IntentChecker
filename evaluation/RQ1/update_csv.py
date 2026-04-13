import csv

csv_path = "evaluation/RQ1/dataset.csv"

# Data from agents: id -> (contract, function, bug_line)
updates = {
    # S6_1
    "web3bugs_18_H_01": ("LendingPair", "accrueAccount", "188;189"),
    "web3bugs_35_H_12": ("ConcentratedLiquidityPool", "mint", "176;184"),
    "web3bugs_43_H_02": ("DelegatedStaking", "unstake", "223;224;226"),
    "web3bugs_45_H_01": ("UToken", "borrow", "403;409;413"),
    "web3bugs_45_H_02": ("CreditLimitByMedian", "getLockedAmount", "66"),
    "web3bugs_83_H_02": ("MasterChef", "deposit", "170;171;172"),
    "web3bugs_102_H_01": ("ScalingPriceOracle", "requestCPIData", "136;198"),
    "web3bugs_112_H_01": ("StakerVault", "transfer", "112;113;117;118"),
    # S6_2
    "web3bugs_3_H_04": ("HourlyBondSubscriptionLending", "viewHourlyBondAmount", "96;97"),
    "web3bugs_61_H_02": ("SavingsAccountUtil", "savingsAccountTransfer", "75;77;79"),
    "web3bugs_101_H_01": ("LenderPool", "_calculatePrincipalWithdrawable", "678;679;680"),
    "web3bugs_110_H_01": ("StakedCitadel", "balance", "293;294"),
    # S6_3
    "web3bugs_5_H_15": ("Router", "swapWithSynthsWithLimit", "170"),
    "web3bugs_14_H_01": ("IdleYieldSource", "redeemToken", "131"),
    "web3bugs_14_H_03": ("BadgerYieldSource", "balanceOfToken", "36"),
    "web3bugs_16_H_02": ("Pricing", "updateFundingRate", "155;159"),
    "web3bugs_29_H_11": ("ConstantProductPool", "burnSingle", "175;183"),
    "web3bugs_32_H_01": ("LendingPair", "_supplyCreditUni", "673"),
    "web3bugs_35_H_10": ("ConcentratedLiquidityPool", "burn", "264;265"),
    "web3bugs_42_H_01": ("MochiVault", "borrow", "248"),
    "web3bugs_47_H_02": ("WrappedIbbtcEth", "transferFrom", "111"),
    "web3bugs_49_H_01": ("OverlayV1UniswapV3Market", "fetchPricePoint", "119;120;121"),
    "web3bugs_51_H_06": ("SwapUtils", "addLiquidity", "1231"),
    "web3bugs_52_H_16": ("VaderRouter", "calculateOutGivenIn", "488;489;490;491"),
    "web3bugs_62_H_10": ("Stream", "recoverTokens", "654"),
    "web3bugs_66_H_02": ("sYETIToken", "rebase", "297"),
    "web3bugs_78_H_02": ("RebaseProxy", "mint", "36"),
    "web3bugs_101_H_02": ("LenderPool", "terminate", "389;400"),
    # S6_4 first 28
    "web3bugs_3_H_05": ("CrossMarginAccounts", "belowMaintenanceThreshold", "203"),
    "web3bugs_5_H_07": ("Utils", "calcAsymmetricShare", "273"),
    "web3bugs_5_H_08": ("Utils", "calcLiquidityUnits", "239"),
    "web3bugs_5_H_12": ("Pools", "getAddedAmount", "201"),
    "web3bugs_8_H_03": ("NFTXVaultUpgradeable", "getRandomTokenIdFromFund", "414"),
    "web3bugs_16_H_04": ("Balances", "applyTrade", "187"),
    "web3bugs_16_H_06": ("GasOracle", "latestAnswer", "32;33;35"),
    "web3bugs_17_H_02": ("Buoy3Pool", "safetyCheck", "88"),
    "web3bugs_25_H_01": ("CompositeMultiOracle", "_peek;_get", "116;126"),
    "web3bugs_25_H_03": ("ERC20Rewards", "setRewards", "85"),
    "web3bugs_25_H_05": ("CTokenMultiOracle", "_setSource", "110"),
    "web3bugs_29_H_05": ("HybridPool", "_nonOptimalMintFee", "433"),
    "web3bugs_29_H_08": ("HybridPool", "_getReserves", "255;256"),
    "web3bugs_29_H_14": ("IndexPool", "_computeSingleOutGivenPoolIn", "279"),
    "web3bugs_29_H_15": ("IndexPool", "_computeSingleOutGivenPoolIn", "282"),
    "web3bugs_30_H_07": ("Vault", "balance", "309"),
    "web3bugs_30_H_08": ("Vault", "withdraw", "248;249"),
    "web3bugs_31_H_01": ("MyStrategy", "manualRebalance", "469;471;477"),
    "web3bugs_34_H_01": ("DrawCalculator", "_numberOfPrizesForIndex", "422;423;424"),
    "web3bugs_35_H_08": ("ConcentratedLiquidityPool", "mint;burn", "176;242"),
    "web3bugs_35_H_11": ("Ticks", "cross", "40;49"),
    "web3bugs_39_H_02": ("Swivel", "exitVaultFillingVaultInitiate", "280"),
    "web3bugs_42_H_05": ("MochiVault", "borrow", "248"),
    "web3bugs_44_H_02": ("Swap", "fillZrxQuote", "210;215"),
    "web3bugs_51_H_02": ("SwapUtils", "rampTargetPrice", "1573;1578"),
    "web3bugs_51_H_04": ("SwapUtils", "getYC", "765;767;768"),
    "web3bugs_52_H_04": ("TwapOracle", "consult", "156"),
    # S6_4 last 28
    "web3bugs_52_H_09": ("VaderReserve", "reimburseImpermanentLoss", "85"),
    "web3bugs_52_H_15": ("VaderRouter", "_swap", "326"),
    "web3bugs_52_H_23": ("VaderPoolV2", "mintSynth", "161"),
    "web3bugs_52_H_25": ("VaderMath", "calculateSwap", "105"),
    "web3bugs_52_H_28": ("TwapOracle", "consult", "156"),
    "web3bugs_52_H_34": ("TwapOracle", "consult", "129;152"),
    "web3bugs_56_H_02": ("CDP", "update", "39"),
    "web3bugs_58_H_02": ("LpIssuer", "_chargeFees", "270"),
    "web3bugs_59_H_04": ("AuctionBurnReserveSkew", "getPegDeltaFrequency", "131"),
    "web3bugs_59_H_05": ("AuctionEscapeHatch", "exitEarly", "83;87"),
    "web3bugs_60_H_01": ("OptimisticLedgerLib", "settleAccount", "68;73"),
    "web3bugs_61_H_01": ("CreditLine", "_borrowTokensToLiquidate", "1050"),
    "web3bugs_61_H_04": ("YearnYield", "getTokensForShares", "180"),
    "web3bugs_62_H_01": ("Stream", "recoverTokens", "654"),
    "web3bugs_62_H_03": ("Stream", "recoverTokens", "672"),
    "web3bugs_70_H_03": ("LiquidityBasedTWAP", "_calculateUSDVPrice", "399;403"),
    "web3bugs_70_H_04": ("LiquidityBasedTWAP", "syncVaderPrice", "131;140;144;147"),
    "web3bugs_70_H_05": ("LiquidityBasedTWAP", "_calculateUSDVPrice", "412"),
    "web3bugs_70_H_08": ("VaderReserve", "reimburseImpermanentLoss", "98;102"),
    "web3bugs_70_H_09": ("USDV", "mint", "76;109"),
    "web3bugs_71_H_11": ("PoolTemplate", "resume", "709;710;711"),
    "web3bugs_77_H_01": ("MathLib", "calculateLiquidityTokenQtyForSingleAssetEntry", "174;175;176;177;178;179;180;181;182;183;184;185"),
    "web3bugs_79_H_02": ("LaunchEvent", "createPair", "398"),
    "web3bugs_97_H_03": ("LiquidityPool", "getAmountToTransfer", "319;320;321;322"),
    "web3bugs_113_H_05": ("NFTPairWithOracle", "_lend", "316"),
    "web3bugs_192_H_06": ("Trading", "addToPosition", "295"),
    "web3bugs_192_H_09": ("Trading", "_closePosition", "625"),
    "web3bugs_192_H_11": ("Trading", "addToPosition", "274;278"),
    # S3_1
    "web3bugs_18_H_02": ("LendingPair", "liquidateAccount", "260"),
    "web3bugs_24_H_03": ("SwappableYieldSource", "setYieldSource", "258;268;269"),
    "web3bugs_25_H_02": ("ERC20Rewards", "_updateRewardsPerToken", "107"),
    "web3bugs_36_H_02": ("Basket", "auctionBurn", "105"),
    "web3bugs_51_H_03": ("SwapUtils", "_xp", "666;676"),
    "web3bugs_58_H_04": ("AaveVault", "tvl", "47"),
    "web3bugs_62_H_08": ("Stream", "updateStreamInternal", "226;229;230"),
    "web3bugs_65_H_01": ("Basket", "handleFees", "136;137"),
    "web3bugs_70_H_10": ("LiquidityBasedTWAP", "syncVaderPrice", "187"),
    "web3bugs_83_H_01": ("MasterChef", "add", "89"),
    "web3bugs_192_H_01": ("Lock", "extendLock", "90;91"),
}

# IDs to exclude
exclude_ids = {
    # Previous exclusions (external lib bug, patched source, excessive bug lines)
    "web3bugs_92_H_01", "web3bugs_30_H_01", "web3bugs_12_H_03",
    # Assembly in target contract itself
    "web3bugs_102_H_01",  # ScalingPriceOracle: assembly in constructor (chainid)
    # Target contract imports/inherits from local files with inline assembly
    "web3bugs_18_H_01",   # LendingPair (S6-1): imports Address.sol, Clones.sol
    "web3bugs_18_H_02",   # LendingPair (S3-1): imports Address.sol, Clones.sol
    "web3bugs_32_H_01",   # LendingPair (S6-3): imports Address.sol, Clones.sol
    "web3bugs_49_H_01",   # OverlayV1UniswapV3Market: imports TickMath.sol, FullMath.sol
    "web3bugs_192_H_06",  # Trading: inherits MetaContext (assembly in _msgSender)
    "web3bugs_192_H_09",  # Trading: inherits MetaContext (assembly in _msgSender)
    "web3bugs_192_H_11",  # Trading: inherits MetaContext (assembly in _msgSender)
    "web3bugs_97_H_03",   # LiquidityPool: inherits ERC2771ContextUpgradeable (assembly)
    "web3bugs_25_H_03",   # ERC20Rewards (S6-4): inherits ERC20Permit (assembly)
    "web3bugs_25_H_02",   # ERC20Rewards (S3-1): inherits ERC20Permit (assembly)
    "web3bugs_30_H_07",   # Vault: inherits VaultToken -> ERC677Token (assembly)
    "web3bugs_30_H_08",   # Vault: inherits VaultToken -> ERC677Token (assembly)
}

# Read current CSV
rows = []
with open(csv_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    for row in reader:
        if row["id"] in exclude_ids:
            continue
        if row["id"] in updates:
            contract, function, bug_line = updates[row["id"]]
            row["contract"] = contract
            row["function"] = function
            row["bug_line"] = bug_line
        rows.append(row)

# Write updated CSV
with open(csv_path, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

# Summary
total = len(rows)
numscout = sum(1 for r in rows if r["source"] == "numscout")
web3bugs = sum(1 for r in rows if r["source"] == "web3bugs")
filled = sum(1 for r in rows if r["contract"] and r["source"] == "web3bugs")
empty = sum(1 for r in rows if not r["contract"] and r["source"] == "web3bugs")
print(f"Total entries: {total}")
print(f"  Numscout: {numscout}")
print(f"  Web3Bugs: {web3bugs} ({filled} filled, {empty} still empty)")
print(f"  Excluded: {len(exclude_ids)}")
