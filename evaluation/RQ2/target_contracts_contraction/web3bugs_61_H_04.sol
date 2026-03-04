pragma solidity 0.7.6;

contract YearnYield is IYield, Initializable, OwnableUpgradeable, ReentrancyGuard {
    using SafeERC20 for IERC20;
    using SafeMath for uint256;

    address payable public savingsAccount;

    mapping(address => address) public override liquidityToken;

    event ProtocolAddressesUpdated(address indexed asset, address indexed protocolToken);

    modifier onlySavingsAccount() {
        require(_msgSender() == savingsAccount, 'Invest: Only savings account can invoke');
        _;
    }

    function initialize(address _owner, address payable _savingsAccount) external initializer {
        __Ownable_init();
        super.transferOwnership(_owner);

        _updateSavingsAccount(_savingsAccount);
    }

    function updateSavingsAccount(address payable _savingsAccount) external onlyOwner {
        _updateSavingsAccount(_savingsAccount);
    }

    function _updateSavingsAccount(address payable _savingsAccount) internal {
        require(_savingsAccount != address(0), 'Invest: zero address');
        savingsAccount = _savingsAccount;
        emit SavingsAccountUpdated(_savingsAccount);
    }

    function updateProtocolAddresses(address _asset, address _liquidityToken) external onlyOwner {
        liquidityToken[_asset] = _liquidityToken;
        emit ProtocolAddressesUpdated(_asset, _liquidityToken);
    }

    function emergencyWithdraw(address _asset, address payable _wallet) external onlyOwner nonReentrant returns (uint256 received) {
        require(_wallet != address(0), 'cant burn');
        address investedTo = liquidityToken[_asset];
        uint256 amount = IERC20(investedTo).balanceOf(address(this));

        if (_asset == address(0)) {
            received = _withdrawETH(investedTo, amount);
            (bool success, ) = _wallet.call{value: received}('');
            require(success, 'Transfer failed');
        } else {
            received = _withdrawERC(_asset, investedTo, amount);
            IERC20(_asset).safeTransfer(_wallet, received);
        }
    }

    function lockTokens(
        address user,
        address asset,
        uint256 amount
    ) external payable override onlySavingsAccount nonReentrant returns (uint256 sharesReceived) {
        require(amount != 0, 'Invest: amount');

        address investedTo = liquidityToken[asset];
        if (asset == address(0)) {
            require(msg.value == amount, 'Invest: ETH amount');
            sharesReceived = _depositETH(investedTo, amount);
        } else {
            IERC20(asset).safeTransferFrom(user, address(this), amount);
            sharesReceived = _depositERC20(asset, investedTo, amount);
        }

        emit LockedTokens(user, investedTo, sharesReceived);
    }

    function unlockTokens(address asset, uint256 amount) external override onlySavingsAccount nonReentrant returns (uint256 received) {
        require(amount != 0, 'Invest: amount');
        address investedTo = liquidityToken[asset];

        if (asset == address(0)) {
            received = _withdrawETH(investedTo, amount);
            (bool success, ) = savingsAccount.call{value: received}('');
            require(success, 'Transfer failed');
        } else {
            received = _withdrawERC(asset, investedTo, amount);
            IERC20(asset).safeTransfer(savingsAccount, received);
        }

        emit UnlockedTokens(asset, received);
    }

    function unlockShares(address asset, uint256 amount) external override onlySavingsAccount nonReentrant returns (uint256) {
        if (amount == 0) {
            return 0;
        }

        require(asset != address(0), 'Asset address cannot be address(0)');
        IERC20(asset).safeTransfer(savingsAccount, amount);

        emit UnlockedShares(asset, amount);
        return amount;
    }

    function getTokensForShares(uint256 shares, address asset) public view override returns (uint256 amount) {
        if (shares == 0) {
            return 0;
        }
        amount = IyVault(liquidityToken[asset]).getPricePerFullShare().mul(shares).div(1e18);
    }

    function getSharesForTokens(uint256 amount, address asset) external view override returns (uint256 shares) {
        shares = (amount.mul(1e18)).div(getTokensForShares(1e18, asset));
    }

    function _depositETH(address vault, uint256 amount) internal returns (uint256 sharesReceived) {
        uint256 initialTokenBalance = IERC20(vault).balanceOf(address(this));

        IyVault(vault).depositETH{value: amount}();

        sharesReceived = IERC20(vault).balanceOf(address(this)).sub(initialTokenBalance);
    }

    function _depositERC20(
        address asset,
        address vault,
        uint256 amount
    ) internal returns (uint256 sharesReceived) {
        uint256 sharesBefore = IERC20(vault).balanceOf(address(this));

        IERC20(asset).approve(vault, 0);
        IERC20(asset).approve(vault, amount);
        IyVault(vault).deposit(amount);

        sharesReceived = IERC20(vault).balanceOf(address(this)).sub(sharesBefore);
    }

    function _withdrawETH(address vault, uint256 amount) internal returns (uint256 received) {
        uint256 ethBalance = address(this).balance;

        IyVault(vault).withdrawETH(amount);

        received = address(this).balance.sub(ethBalance);
    }

    function _withdrawERC(
        address asset,
        address vault,
        uint256 amount
    ) internal returns (uint256 tokensReceived) {
        uint256 initialAssetBalance = IERC20(asset).balanceOf(address(this));

        IyVault(vault).withdraw(amount);

        tokensReceived = IERC20(asset).balanceOf(address(this)).sub(initialAssetBalance);
    }

    receive() external payable {}
}
