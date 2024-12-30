// SPDX-License-Identifier: MIT
pragma solidity 0.6.12;

contract AllocationStaking {
    // Info of each user.
    struct UserInfo {
        uint256 amount;     // How many LP tokens the user has provided.
        uint256 rewardDebt; // Reward debt. Current reward debt when user joined farm.
        uint256 tokensUnlockTime; // If user registered for sale, returns when tokens are getting unlocked
        address [] salesRegistered;
    }

    // Info of each pool.
    struct PoolInfo {
        //IERC20 lpToken;             // Address of LP token contract.
        uint256 allocPoint;         // How many allocation points assigned to this pool. ERC20s to distribute per block.
        uint256 lastRewardTimestamp;    // Last timstamp that ERC20s distribution occurs.
        uint256 accERC20PerShare;   // Accumulated ERC20s per share, times 1e36.
        uint256 totalDeposits; // Total amount of tokens deposited at the moment (staked)
    }

    // Address of the ERC20 Token contract.
    //IERC20 public erc20;
    // The total amount of ERC20 that's paid out as reward.
    uint256 public paidOut;
    // ERC20 tokens rewarded per second.
    uint256 public rewardPerSecond;
    // Total rewards added to farm
    uint256 public totalRewards;
    // Precision of deposit fee
    uint256 public depositFeePrecision;
    // Percent of deposit fee, must be >= depositFeePrecision.div(100) and less than depositFeePrecision
    uint256 public depositFeePercent;
    // Total XAVA redistributed between people staking
    uint256 public totalXavaRedistributed;
    // Address of sales factory contract
    //ISalesFactory public salesFactory;
    // Info of each pool.
    PoolInfo[] public poolInfo;
    // Info of each user that stakes LP tokens.
    mapping (uint256 => mapping (address => UserInfo)) public userInfo;
    // Total allocation points. Must be the sum of all allocation points in all pools.
    uint256 public totalAllocPoint;
    // The timestamp when farming starts.
    uint256 public startTimestamp;
    // The timestamp when farming ends.
    uint256 public endTimestamp;
    // Total amount of tokens burned from the wallet
    mapping (address => uint256) public totalBurnedFromUser;
    // Time penalty is active
    uint256 public postSaleWithdrawPenaltyLength;
    // Post sale penalty withdraw percent, which is linearly dropping for postSaleWithdrawPenaltyLength period
    uint256 public postSaleWithdrawPenaltyPercent;
    // Post sale withdraw penalty precision
    uint256 public postSaleWithdrawPenaltyPrecision;
    // Nonce usage mapping
    mapping (bytes32 => bool) public isNonceUsed;
    // Signature usage mapping
    mapping (bytes => bool) public isSignatureUsed;
    // Admin contract
    //IAdmin public admin;
    // Stake ownership transfer approvals per pool
    mapping (uint256 => mapping (address => address)) stakeOwnershipTransferApprovals;

    // Events
    //event Deposit(address indexed user, uint256 indexed pid, uint256 amount);
    //event Withdraw(address indexed user, uint256 indexed pid, uint256 amount);
    //event DepositFeeSet(uint256 depositFeePercent, uint256 depositFeePrecision);
    //event CompoundedEarnings(address indexed user, uint256 indexed pid, uint256 amountAdded, uint256 totalDeposited);
    //event FeeTaken(address indexed user, uint256 indexed pid, uint256 amount);
    //event PostSaleWithdrawFeeCharged(address user, uint256 amountStake, uint256 amountRewards);
    //event StakeOwnershipTransferred(address indexed from, address indexed to, uint256 pid);


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

    // Fund the farm, increase the end block
    // SWC-101-Integer Overflow and Underflow: L129-134
    function fund(uint256 _amount) public {
        require(block.timestamp < endTimestamp, "fund: too late, the farm is closed");
        //erc20.safeTransferFrom(address(msg.sender), address(this), _amount);
        //endTimestamp += _amount.div(rewardPerSecond);
        endTimestamp += div(_amount, rewardPerSecond); //@intent endTimestamp < 2^^256-1
        //totalRewards = totalRewards.add(_amount);
        totalRewards = add(totalRewards, _amount);
    }

    // Transfer ERC20 and update the required ERC20 to payout all rewards
    // SWC-101-Integer Overflow and Underflow: L472-475
    function erc20Transfer(address _to, uint256 _amount) internal {
        //erc20.transfer(_to, _amount);
        paidOut += _amount; //@intent endTimestamp < 2^^256-1
    }
}