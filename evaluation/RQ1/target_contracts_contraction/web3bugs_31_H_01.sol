pragma solidity ^0.6.11;
pragma experimental ABIEncoderV2;

interface IERC20Upgradeable {
    function balanceOf(address account) external view returns (uint256);
}

interface ICvxLocker {
    function maximumBoostPayment() external returns (uint256);

    function lock(
        address _account,
        uint256 _amount,
        uint256 _spendRatio
    ) external;

    function balanceOf(address _user) external view returns (uint256 amount);

    function processExpiredLocks(bool _relock) external;
}

interface ISettV3 {
    function deposit(uint256 _amount) external;

    function getPricePerFullShare() external view returns (uint256);
}

contract MyStrategy {
    using SafeMathUpgradeable for uint256;

    address public governance;
    bool private _paused;

    modifier whenNotPaused() {
        require(!_paused, "Pausable: paused");
        _;
    }

    function _onlyGovernance() internal view {
        require(msg.sender == governance, "onlyGovernance");
    }

    uint256 MAX_BPS = 10_000;

    address public want;
    address public constant CVX = 0x4e3FBD56CD56c3e72c1403e103b45Db9da5B9D2B;

    ICvxLocker public LOCKER;

    ISettV3 public CVX_VAULT;

    bool public harvestOnRebalance = true;
    bool public processLocksOnRebalance = true;

    function wantToCVX(uint256 want_) public view returns (uint256) {
        uint256 bCVXToCVX = CVX_VAULT.getPricePerFullShare();
        return want_.mul(bCVXToCVX).div(10**18);
    }

    function harvest() public whenNotPaused returns (uint256 harvested) {
        return 0;
    }

    function manualRebalance(uint256 toLock) external whenNotPaused {
        _onlyGovernance();
        require(toLock <= MAX_BPS, "Max is 100%");

        if (processLocksOnRebalance) {
            LOCKER.processExpiredLocks(false);
        }

        if (harvestOnRebalance) {
            harvest();
        }

        uint256 balanceOfWant =
            IERC20Upgradeable(want).balanceOf(address(this));
        uint256 balanceOfCVX = IERC20Upgradeable(CVX).balanceOf(address(this));
        uint256 balanceInLock = LOCKER.balanceOf(address(this));
        uint256 totalCVXBalance =
            balanceOfCVX.add(balanceInLock).add(wantToCVX(balanceOfWant));

        uint256 currentLockRatio =
            balanceInLock.mul(10**18).div(totalCVXBalance);
        uint256 newLockRatio = totalCVXBalance.mul(toLock).div(MAX_BPS);
        uint256 toWantRatio =
            totalCVXBalance.mul(MAX_BPS.sub(toLock)).div(MAX_BPS);

        if (newLockRatio <= currentLockRatio) {
            uint256 toDeposit = IERC20Upgradeable(CVX).balanceOf(address(this));
            if (toDeposit > 0) {
                CVX_VAULT.deposit(toDeposit);
            }

            return;
        }

        uint256 cvxToLock = newLockRatio.sub(currentLockRatio);

        uint256 maxCVX = IERC20Upgradeable(CVX).balanceOf(address(this));
        if (cvxToLock > maxCVX) {
            LOCKER.lock(address(this), maxCVX, LOCKER.maximumBoostPayment());
        } else {
            LOCKER.lock(address(this), cvxToLock, LOCKER.maximumBoostPayment());
        }

        uint256 cvxLeft = IERC20Upgradeable(CVX).balanceOf(address(this));
        if (cvxLeft > 0) {
            CVX_VAULT.deposit(cvxLeft);
        }
    }
}
