pragma solidity =0.8.9;

contract VaderReserve is IVaderReserve, ProtocolConstants, Ownable {

    using SafeERC20 for IERC20;

    IERC20 public immutable vader;

    address public router;

    uint256 public lastGrant;

    function reserve() public view override returns (uint256) {
        return vader.balanceOf(address(this));
    }

    function grant(address recipient, uint256 amount)
        external
        override
        onlyOwner
        throttle
    {
        amount = _min(
            (reserve() * _MAX_GRANT_BASIS_POINTS) / _MAX_BASIS_POINTS,
            amount
        );
        vader.safeTransfer(recipient, amount);

        emit GrantDistributed(recipient, amount);
    }

    function initialize(address _router, address _dao) external onlyOwner {
         require(
            _router != _ZERO_ADDRESS &&
                _dao != _ZERO_ADDRESS,
            "VaderReserve::initialize: Incorrect Arguments"
        );
        router = _router;
        transferOwnership(_dao);
    }

    function reimburseImpermanentLoss(address recipient, uint256 amount)
        external
        override
    {
        require(
            msg.sender == router,
            "VaderReserve::reimburseImpermanentLoss: Insufficient Priviledges"
        );

        uint256 actualAmount = _min(reserve(), amount);

        vader.safeTransfer(recipient, actualAmount);

        emit LossCovered(recipient, amount, actualAmount);
    }

    function _min(uint256 a, uint256 b) private pure returns (uint256) {
        return a < b ? a : b;
    }

    modifier throttle() {
        require(
            lastGrant + _GRANT_DELAY <= block.timestamp,
            "VaderReserve::throttle: Grant Too Fast"
        );
        lastGrant = block.timestamp;
        _;
    }
}
