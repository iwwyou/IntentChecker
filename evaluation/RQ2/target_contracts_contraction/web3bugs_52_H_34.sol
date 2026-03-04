pragma solidity =0.8.9;

contract TwapOracle is Ownable {

    using FixedPoint for *;

    struct PairData {
        address pair;
        address token0;
        address token1;
        uint256 price0CumulativeLast;
        uint256 price1CumulativeLast;
        uint32 blockTimestampLast;
        FixedPoint.uq112x112 price0Average;
        FixedPoint.uq112x112 price1Average;
    }

    address public VADER;

    address public USDV;

    bool private _usdvEnabled;

    mapping(address => address) private _aggregators;

    IVaderPoolV2 private _vaderPool;

    uint256 private _updatePeriod;

    PairData[] private _pairs;

    mapping(bytes32 => bool) private _pairExists;

    modifier initialized() {
        require(
            VADER != address(0) && USDV != address(0),
            "TwapOracle::initialized: not initialized"
        );
        _;
    }

    function pairExists(address token0, address token1)
        public
        view
        returns (bool)
    {
        bytes32 pairHash0 = keccak256(abi.encodePacked(token0, token1));
        bytes32 pairHash1 = keccak256(abi.encodePacked(token1, token0));
        return _pairExists[pairHash0] || _pairExists[pairHash1];
    }

    function consult(address token) public view returns (uint256 result) {
        uint256 pairCount = _pairs.length;
        uint256 sumNative = 0;
        uint256 sumUSD = 0;

        for (uint256 i = 0; i < pairCount; i++) {
            PairData memory pairData = _pairs[i];

            if (token == pairData.token0) {

                sumNative += pairData.price1Average.mul(1).decode144();
                if (pairData.price1Average._x != 0) {
                    require(sumNative != 0);
                }

                (
                    uint80 roundID,
                    int256 price,
                    ,
                    ,
                    uint80 answeredInRound
                ) = AggregatorV3Interface(_aggregators[pairData.token1])
                        .latestRoundData();

                require(
                    answeredInRound >= roundID,
                    "TwapOracle::consult: stale chainlink price"
                );
                require(
                    price != 0,
                    "TwapOracle::consult: chainlink malfunction"
                );

                sumUSD += uint256(price) * (10**10);
            }
        }
        require(sumNative != 0, "TwapOracle::consult: Sum of native is zero");
        result = ((sumUSD * IERC20Metadata(token).decimals()) / sumNative);
    }

    function getRate() public view returns (uint256 result) {
        uint256 tUSDInUSDV = consult(USDV);
        uint256 tUSDInVader = consult(VADER);

        result = tUSDInUSDV / tUSDInVader;
    }

    function usdvtoVader(uint256 usdvAmount) external view returns (uint256) {
        return usdvAmount * getRate();
    }

    function vaderToUsdv(uint256 vaderAmount) external view returns (uint256) {
        if (!_usdvEnabled) {
            return consult(VADER) * vaderAmount;
        }

        return vaderAmount / getRate();
    }

    function initialize(address _usdv, address _vader) external onlyOwner {
        require(
            VADER == address(0),
            "TwapOracle::initialize: Vader already set"
        );
        require(USDV == address(0), "TwapOracle::initialize: USDV already set");
        require(
            _usdv != address(0),
            "TwapOracle::initialize: can not set to a zero address"
        );
        require(
            _vader != address(0),
            "TwapOracle::initialize: can not set to a zero address"
        );

        VADER = _vader;
        USDV = _usdv;
    }

    function enableUSDV() external onlyOwner {
        _usdvEnabled = true;
    }

    function registerAggregator(address asset, address aggregator)
        external
        onlyOwner
        initialized
    {
        require(
            asset != address(0),
            "TwapOracle::registerAggregator: asset zero address provided"
        );
        require(
            aggregator != address(0),
            "TwapOracle::registerAggregator: aggregator zero address provided"
        );
        require(
            _aggregators[asset] == address(0),
            "TwapOracle::registerAggregator: aggregator already exists"
        );

        _aggregators[asset] = aggregator;
    }

    function registerPair(
        address factory,
        address token0,
        address token1
    ) external onlyOwner initialized {
        require(
            token0 == VADER || token0 == USDV,
            "TwapOracle::registerPair: Invalid token0 address"
        );
        require(
            token0 != token1,
            "TwapOracle::registerPair: Same token address"
        );
        require(
            !pairExists(token0, token1),
            "TwapOracle::registerPair: Pair exists"
        );

        address pairAddr;
        uint256 price0CumulativeLast;
        uint256 price1CumulativeLast;
        uint112 reserve0;
        uint112 reserve1;
        uint32 blockTimestampLast;

        if (token0 == VADER) {
            IUniswapV2Pair pair = IUniswapV2Pair(
                IUniswapV2Factory(factory).getPair(token0, token1)
            );
            pairAddr = address(pair);
            price0CumulativeLast = pair.price0CumulativeLast();
            price1CumulativeLast = pair.price1CumulativeLast();
            (reserve0, reserve1, blockTimestampLast) = pair.getReserves();
        } else {
            pairAddr = address(_vaderPool);
            (price0CumulativeLast, price1CumulativeLast, ) = _vaderPool
                .cumulativePrices(IERC20(token1));
            (reserve0, reserve1, blockTimestampLast) = _vaderPool.getReserves(
                IERC20(token1)
            );
        }

        require(
            reserve0 != 0 && reserve1 != 0,
            "TwapOracle::registerPair: No reserves"
        );

        _pairExists[keccak256(abi.encodePacked(token0, token1))] = true;

        _pairs.push(
            PairData({
                pair: pairAddr,
                token0: token0,
                token1: token1,
                price0CumulativeLast: price0CumulativeLast,
                price1CumulativeLast: price1CumulativeLast,
                blockTimestampLast: blockTimestampLast,
                price0Average: FixedPoint.uq112x112({_x: 0}),
                price1Average: FixedPoint.uq112x112({_x: 0})
            })
        );
    }

    function update() external onlyOwner initialized {
        uint256 pairCount = _pairs.length;

        for (uint256 i = 0; i < pairCount; i++) {
            PairData storage pairData = _pairs[i];

            (
                uint256 price0Cumulative,
                uint256 price1Cumulative,
                uint32 blockTimestamp
            ) = (pairData.token0 == VADER)
                    ? UniswapV2OracleLibrary.currentCumulativePrices(
                        pairData.pair
                    )
                    : _vaderPool.cumulativePrices(IERC20(pairData.token1));

            unchecked {
                uint32 timeElapsed = blockTimestamp -
                    pairData.blockTimestampLast;
                require(
                    timeElapsed >= _updatePeriod,
                    "TwapOracle::update: Period not elapsed"
                );

                pairData.price0Average = FixedPoint.uq112x112(
                    uint224(
                        (price0Cumulative - pairData.price0CumulativeLast) /
                            timeElapsed
                    )
                );
                pairData.price1Average = FixedPoint.uq112x112(
                    uint224(
                        (price1Cumulative - pairData.price1CumulativeLast) /
                            timeElapsed
                    )
                );
            }

            pairData.price0CumulativeLast = price0Cumulative;
            pairData.price1CumulativeLast = price1Cumulative;
            pairData.blockTimestampLast = blockTimestamp;
        }
    }
}
