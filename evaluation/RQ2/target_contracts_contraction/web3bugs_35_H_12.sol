pragma solidity >=0.8.0;

contract ConcentratedLiquidityPool is IPool {
    using Ticks for mapping(int24 => Ticks.Tick);

    event Mint(address indexed sender, uint256 amount0, uint256 amount1, address indexed recipient);
    event Burn(address indexed sender, uint256 amount0, uint256 amount1, address indexed recipient);
    event Collect(address indexed sender, uint256 amount0, uint256 amount1);
    event Sync(uint256 reserveShares0, uint256 reserveShares1);

    bytes32 public constant override poolIdentifier = "Trident:ConcentratedLiquidity";

    uint24 internal constant MAX_FEE = 100000;

    uint128 internal immutable MAX_TICK_LIQUIDITY;
    uint24 internal immutable tickSpacing;
    uint24 internal immutable swapFee;

    address internal immutable barFeeTo;
    IBentoBoxMinimal internal immutable bento;
    IMasterDeployer internal immutable masterDeployer;

    address internal immutable token0;
    address internal immutable token1;

    uint128 public liquidity;

    uint160 internal secondsPerLiquidity;
    uint32 internal lastObservation;

    uint256 public feeGrowthGlobal0;
    uint256 public feeGrowthGlobal1;

    uint256 public barFee;

    uint128 internal token0ProtocolFee;
    uint128 internal token1ProtocolFee;

    uint128 internal reserve0;
    uint128 internal reserve1;

    uint160 internal price;
    int24 internal nearestTick;

    uint256 internal unlocked;
    modifier lock() {
        require(unlocked == 1, "LOCKED");
        unlocked = 2;
        _;
        unlocked = 1;
    }

    mapping(int24 => Ticks.Tick) public ticks;
    mapping(address => mapping(int24 => mapping(int24 => Position))) public positions;

    struct Position {
        uint128 liquidity;
        uint256 feeGrowthInside0Last;
        uint256 feeGrowthInside1Last;
    }

    struct SwapCache {
        uint256 feeAmount;
        uint256 totalFeeAmount;
        uint256 protocolFee;
        uint256 feeGrowthGlobal;
        uint256 currentPrice;
        uint256 currentLiquidity;
        uint256 input;
        int24 nextTickToCross;
    }

    struct MintParams {
        int24 lowerOld;
        int24 lower;
        int24 upperOld;
        int24 upper;
        uint256 amount0Desired;
        uint256 amount1Desired;
        bool token0native;
        bool token1native;
        address positionOwner;
        address positionRecipient;
    }

    function rangeFeeGrowth(int24 lowerTick, int24 upperTick) public view returns (uint256 feeGrowthInside0, uint256 feeGrowthInside1) {
        int24 currentTick = nearestTick;

        Ticks.Tick storage lower = ticks[lowerTick];
        Ticks.Tick storage upper = ticks[upperTick];

        uint256 _feeGrowthGlobal0 = feeGrowthGlobal0;
        uint256 _feeGrowthGlobal1 = feeGrowthGlobal1;
        uint256 feeGrowthBelow0;
        uint256 feeGrowthBelow1;
        uint256 feeGrowthAbove0;
        uint256 feeGrowthAbove1;

        if (lowerTick <= currentTick) {
            feeGrowthBelow0 = lower.feeGrowthOutside0;
            feeGrowthBelow1 = lower.feeGrowthOutside1;
        } else {
            feeGrowthBelow0 = _feeGrowthGlobal0 - lower.feeGrowthOutside0;
            feeGrowthBelow1 = _feeGrowthGlobal1 - lower.feeGrowthOutside1;
        }

        if (currentTick < upperTick) {
            feeGrowthAbove0 = upper.feeGrowthOutside0;
            feeGrowthAbove1 = upper.feeGrowthOutside1;
        } else {
            feeGrowthAbove0 = _feeGrowthGlobal0 - upper.feeGrowthOutside0;
            feeGrowthAbove1 = _feeGrowthGlobal1 - upper.feeGrowthOutside1;
        }

        feeGrowthInside0 = _feeGrowthGlobal0 - feeGrowthBelow0 - feeGrowthAbove0;
        feeGrowthInside1 = _feeGrowthGlobal1 - feeGrowthBelow1 - feeGrowthAbove1;
    }

    function _updatePosition(
        address owner,
        int24 lower,
        int24 upper,
        int128 amount
    ) internal returns (uint256 amount0fees, uint256 amount1fees) {
        Position storage position = positions[owner][lower][upper];

        (uint256 growth0current, uint256 growth1current) = rangeFeeGrowth(lower, upper);
        amount0fees = FullMath.mulDiv(
            growth0current - position.feeGrowthInside0Last,
            position.liquidity,
            0x100000000000000000000000000000000
        );

        amount1fees = FullMath.mulDiv(
            growth1current - position.feeGrowthInside1Last,
            position.liquidity,
            0x100000000000000000000000000000000
        );

        if (amount < 0) {
            position.liquidity -= uint128(-amount);
        }
        if (amount > 0) {
            position.liquidity += uint128(amount);
        }

        require(position.liquidity < MAX_TICK_LIQUIDITY, "MAX_TICK_LIQUIDITY");

        position.feeGrowthInside0Last = growth0current;
        position.feeGrowthInside1Last = growth1current;
    }

    function _transfer(
        address token,
        uint256 shares,
        address to,
        bool unwrapBento
    ) internal {
        if (unwrapBento) {
            bento.withdraw(token, address(this), to, 0, shares);
        } else {
            bento.transfer(token, address(this), to, shares);
        }
    }

    function _ensureTickSpacing(int24 lower, int24 upper) internal view {
        require(lower % int24(tickSpacing) == 0, "INVALID_TICK");
        require((lower / int24(tickSpacing)) % 2 == 0, "LOWER_EVEN");

        require(upper % int24(tickSpacing) == 0, "INVALID_TICK");
        require((upper / int24(tickSpacing)) % 2 != 0, "UPPER_ODD");
    }

    function _getAmountsForLiquidity(
        uint256 priceLower,
        uint256 priceUpper,
        uint256 currentPrice,
        uint256 liquidityAmount
    ) internal pure returns (uint128 token0amount, uint128 token1amount) {
        if (priceUpper <= currentPrice) {
            token1amount = uint128(DyDxMath.getDy(liquidityAmount, priceLower, priceUpper, true));
        } else if (currentPrice <= priceLower) {
            token0amount = uint128(DyDxMath.getDx(liquidityAmount, priceLower, priceUpper, true));
        } else {
            token0amount = uint128(DyDxMath.getDx(liquidityAmount, currentPrice, priceUpper, true));
            token1amount = uint128(DyDxMath.getDy(liquidityAmount, priceLower, currentPrice, true));
        }
    }

    function mint(bytes calldata data) public override lock returns (uint256 _liquidity) {
        MintParams memory mintParams = abi.decode(data, (MintParams));

        uint256 priceLower = uint256(TickMath.getSqrtRatioAtTick(mintParams.lower));
        uint256 priceUpper = uint256(TickMath.getSqrtRatioAtTick(mintParams.upper));
        uint256 currentPrice = uint256(price);

        _liquidity = DyDxMath.getLiquidityForAmounts(
            priceLower,
            priceUpper,
            currentPrice,
            mintParams.amount1Desired,
            mintParams.amount0Desired
        );

        require(_liquidity <= MAX_TICK_LIQUIDITY, "LIQUIDITY_OVERFLOW");

        (uint256 amount0fees, uint256 amount1fees) = _updatePosition(
            mintParams.positionOwner,
            mintParams.lower,
            mintParams.upper,
            int128(uint128(_liquidity))
        );
        if (amount0fees > 0) {
            _transfer(token0, amount0fees, mintParams.positionOwner, false);
            reserve0 -= uint128(amount0fees);
        }
        if (amount1fees > 0) {
            _transfer(token1, amount1fees, mintParams.positionOwner, false);
            reserve1 -= uint128(amount1fees);
        }

        unchecked {
            if (priceLower < currentPrice && currentPrice < priceUpper) {
                liquidity += uint128(_liquidity);
            }
        }

        _ensureTickSpacing(mintParams.lower, mintParams.upper);
        nearestTick = Ticks.insert(
            ticks,
            feeGrowthGlobal0,
            feeGrowthGlobal1,
            secondsPerLiquidity,
            mintParams.lowerOld,
            mintParams.lower,
            mintParams.upperOld,
            mintParams.upper,
            uint128(_liquidity),
            nearestTick,
            uint160(currentPrice)
        );

        (uint128 amount0Actual, uint128 amount1Actual) = _getAmountsForLiquidity(priceLower, priceUpper, currentPrice, _liquidity);

        ITridentRouter.TokenInput[] memory callbackData = new ITridentRouter.TokenInput[](2);
        callbackData[0] = ITridentRouter.TokenInput(token0, mintParams.token0native, amount0Actual);
        callbackData[1] = ITridentRouter.TokenInput(token1, mintParams.token1native, amount1Actual);

        ITridentCallee(msg.sender).tridentMintCallback(abi.encode(callbackData));

        unchecked {
            if (amount0Actual != 0) {
                require(amount0Actual + reserve0 <= _balance(token0), "TOKEN0_MISSING");
                reserve0 += amount0Actual;
            }

            if (amount1Actual != 0) {
                require(amount1Actual + reserve1 <= _balance(token1), "TOKEN1_MISSING");
                reserve1 += amount1Actual;
            }
        }

        (uint256 feeGrowth0, uint256 feeGrowth1) = rangeFeeGrowth(mintParams.lower, mintParams.upper);

        if (mintParams.positionRecipient != address(0)) {
            IPositionManager(mintParams.positionOwner).positionMintCallback(
                mintParams.positionRecipient,
                mintParams.lower,
                mintParams.upper,
                uint128(_liquidity),
                feeGrowth0,
                feeGrowth1
            );
        }

        emit Mint(mintParams.positionOwner, amount0Actual, amount1Actual, mintParams.positionRecipient);
    }   
}
