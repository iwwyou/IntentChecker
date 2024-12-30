// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.6.0 <0.7.0;



contract BaseStrategy {

    struct StrategyParams {
        uint256 performanceFee;
        uint256 activation;
        uint256 debtLimit;
        uint256 rateLimit;
        uint256 lastReport;
        uint256 totalDebt;
        uint256 totalReturns;
    }

    //VaultAPI public vault;
    address public strategist;
    address public rewards;
    address public keeper;

    //IERC20 public want;

    // So indexers can keep track of this
    //event Harvested(uint256 profit);

    // The minimum number of blocks between harvest calls
    // NOTE: Override this value with your own, or set dynamically below
    uint256 public minReportDelay = 6300; // ~ once a day

    // The minimum multiple that `callCost` must be above the credit/profit to be "justifiable"
    // NOTE: Override this value with your own, or set dynamically below
    uint256 public profitFactor = 100;

    // Use this to adjust the threshold at which running a debt causes a harvest trigger
    uint256 public debtThreshold = 0;

    // Adjust this using `setReserve(...)` to keep some of the position in reserve in the strategy,
    // to accomodate larger variations needed to sustain the strategy's core positon(s)
    uint256 private reserve = 0;

    function mul(uint256 a, uint256 b) internal pure returns (uint256 c) {
        if (a == 0) {
          return 0;
        }
        c = a * b;
        assert(c / a == b);
        return c;
    }

    function div(uint256 a, uint256 b) internal pure returns (uint256) {
        assert(b > 0); // Solidity automatically throws when dividing by 0
        uint256 c = a / b;
        assert(a == b * c + a % b); // There is no case in which this doesn't hold
        return a / b;
    }

    function sub(uint256 a, uint256 b) internal pure returns (uint256) {
        assert(b <= a);
        return a - b;
    }

    function add(uint256 a, uint256 b) internal pure returns (uint256 c) {
        c = a + b;
        assert(c >= a);
        return c;
    }

    function creditAvailable() external view returns (uint256) {
        return 100;
    }

    function estimatedTotalAssets() external view returns (uint256) {
        return 100;
    }

    function harvestTrigger(uint256 callCost) public virtual view returns (bool) {
        //StrategyParams memory params = vault.strategies(address(this));
        StrategyParams memory params;

        // Should not trigger if strategy is not activated
        if (params.activation == 0) return false;

        // Should trigger if hadn't been called in a while
        //if (block.number.sub(params.lastReport) >= minReportDelay) return true;
        if (sub(block.number, params.lastReport) >= minReportDelay) {
            return true;
        }

        // If some amount is owed, pay it back
        // NOTE: Since debt is adjusted in step-wise fashion, it is appropiate to always trigger here,
        //       because the resulting change should be large (might not always be the case)
        //uint256 outstanding = vault.debtOutstanding();
        //if (outstanding > 0) return true;

        // Check for profits and losses
        uint256 total = estimatedTotalAssets();
        // Trigger if we have a loss to report
        if (add(total, debtThreshold) < params.totalDebt) return true;

        uint256 profit = 0;
        if (total > params.totalDebt) profit = sub(total, params.totalDebt); // We've earned a profit!

        // Otherwise, only trigger if it "makes sense" economically (gas cost is <N% of value moved)
        uint256 credit = vault.creditAvailable();
        //SWC-101-Integer Overflow and Underflow:L332
        return (profitFactor * callCost < add(credit, profit)); //@intent
    }
}

