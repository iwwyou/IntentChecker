pragma solidity ^0.8.0;

interface IWAVAX {
    function approve(address spender, uint256 amount) external returns (bool);
}

interface IJoeFactory {
    function getPair(address tokenA, address tokenB) external view returns (address pair);
}

interface IJoePair {
    function totalSupply() external view returns (uint256);
}

interface IJoeRouter02 {
    function addLiquidity(
        address tokenA,
        address tokenB,
        uint256 amountADesired,
        uint256 amountBDesired,
        uint256 amountAMin,
        uint256 amountBMin,
        address to,
        uint256 deadline
    )
        external
        returns (
            uint256 amountA,
            uint256 amountB,
            uint256 liquidity
        );
}

interface IERC20Metadata {
    function decimals() external view returns (uint8);

    function approve(address spender, uint256 amount) external returns (bool);
}

contract LaunchEvent {
    uint8 constant PHASE_NOT_STARTED = 0;
    uint8 constant PHASE_ONE = 1;
    uint8 constant PHASE_TWO = 2;
    uint8 constant PHASE_THREE = 3;

    uint256 public auctionStart;

    uint256 public PHASE_ONE_DURATION;
    uint256 public PHASE_TWO_DURATION;

    uint256 public floorPrice;

    IWAVAX private WAVAX;
    IERC20Metadata public token;

    IJoeRouter02 private router;
    IJoeFactory private factory;

    bool public stopped;

    IJoePair public pair;

    uint256 private wavaxAllocated;

    uint256 private lpSupply;

    uint256 private tokenReserve;

    uint256 private tokenIncentivesBalance;
    uint256 private tokenIncentivesForUsers;
    uint256 private tokenIncentiveIssuerRefund;

    uint256 private wavaxReserve;

    event LiquidityPoolCreated(
        address indexed pair,
        address indexed token0,
        address indexed token1,
        uint256 amount0,
        uint256 amount1
    );

    function currentPhase() public view returns (uint8) {
        if (block.timestamp < auctionStart || auctionStart == 0) {
            return PHASE_NOT_STARTED;
        } else if (block.timestamp < auctionStart + PHASE_ONE_DURATION) {
            return PHASE_ONE;
        } else if (
            block.timestamp <
            auctionStart + PHASE_ONE_DURATION + PHASE_TWO_DURATION
        ) {
            return PHASE_TWO;
        }
        return PHASE_THREE;
    }

    function _atPhase(uint8 _phase) internal view {
        if (_phase == PHASE_NOT_STARTED) {
            require(
                currentPhase() == PHASE_NOT_STARTED,
                "LaunchEvent: not in not started"
            );
        } else if (_phase == PHASE_ONE) {
            require(
                currentPhase() == PHASE_ONE,
                "LaunchEvent: not in phase one"
            );
        } else if (_phase == PHASE_TWO) {
            require(
                currentPhase() == PHASE_TWO,
                "LaunchEvent: not in phase two"
            );
        } else if (_phase == PHASE_THREE) {
            require(
                currentPhase() == PHASE_THREE,
                "LaunchEvent: not in phase three"
            );
        } else {
            revert("LaunchEvent: unknown state");
        }
    }

    modifier atPhase(uint8 _phase) {
        _atPhase(_phase);
        _;
    }

    modifier isStopped(bool _stopped) {
        if (_stopped) {
            require(stopped, "LaunchEvent: is still running");
        } else {
            require(!stopped, "LaunchEvent: stopped");
        }
        _;
    }

    function createPair() external isStopped(false) atPhase(PHASE_THREE) {
        (address wavaxAddress, address tokenAddress) = (
            address(WAVAX),
            address(token)
        );
        require(
            factory.getPair(wavaxAddress, tokenAddress) == address(0) ||
                IJoePair(
                    IJoeFactory(factory).getPair(wavaxAddress, tokenAddress)
                ).totalSupply() ==
                0,
            "LaunchEvent: liquid pair already exists"
        );
        require(wavaxReserve > 0, "LaunchEvent: no wavax balance");

        uint256 tokenAllocated = tokenReserve;

        if (
            floorPrice > (wavaxReserve * 10**token.decimals()) / tokenAllocated
        ) {
            tokenAllocated = (wavaxReserve * 10**token.decimals()) / floorPrice;
            tokenIncentivesForUsers =
                (tokenIncentivesForUsers * tokenAllocated) /
                tokenReserve;
            tokenIncentiveIssuerRefund =
                tokenIncentivesBalance -
                tokenIncentivesForUsers;
        }

        WAVAX.approve(address(router), wavaxReserve);
        token.approve(address(router), tokenAllocated);

        (, , lpSupply) = router.addLiquidity(
            wavaxAddress,
            tokenAddress,
            wavaxReserve,
            tokenAllocated,
            wavaxReserve,
            tokenAllocated,
            address(this),
            block.timestamp
        );

        pair = IJoePair(factory.getPair(tokenAddress, wavaxAddress));
        wavaxAllocated = wavaxReserve;
        wavaxReserve = 0;

        tokenReserve -= tokenAllocated;

        emit LiquidityPoolCreated(
            address(pair),
            tokenAddress,
            wavaxAddress,
            tokenAllocated,
            wavaxAllocated
        );
    }
}
