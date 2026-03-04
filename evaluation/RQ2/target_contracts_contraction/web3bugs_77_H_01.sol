pragma solidity 0.8.4;

library MathLib {
    struct InternalBalances {
        uint256 baseTokenReserveQty;
        uint256 quoteTokenReserveQty;
        uint256 kLast;
    }

    struct TokenQtys {
        uint256 baseTokenQty;
        uint256 quoteTokenQty;
        uint256 liquidityTokenQty;
        uint256 liquidityTokenFeeQty;
    }

    uint256 public constant BASIS_POINTS = 10000;
    uint256 public constant WAD = 10**18;

    function wDiv(uint256 a, uint256 b) public pure returns (uint256) {
        return ((a * WAD) + (b / 2)) / b;
    }

    function roundToNearest(uint256 a, uint256 n)
        public
        pure
        returns (uint256)
    {
        return ((a + (n / 2)) / n) * n;
    }

    function wMul(uint256 a, uint256 b) public pure returns (uint256) {
        return ((a * b) + (WAD / 2)) / WAD;
    }

    function diff(uint256 a, uint256 b) public pure returns (uint256) {
        if (a >= b) {
            return a - b;
        }
        return b - a;
    }

    function sqrt(uint256 y) internal pure returns (uint256 z) {
        if (y > 3) {
            z = y;
            uint256 x = y / 2 + 1;
            while (x < z) {
                z = x;
                x = (y / x + x) / 2;
            }
        } else if (y != 0) {
            z = 1;
        }
    }

    function isSufficientDecayPresent(
        uint256 _baseTokenReserveQty,
        InternalBalances memory _internalBalances
    ) public pure returns (bool) {
        return (wDiv(
            diff(_baseTokenReserveQty, _internalBalances.baseTokenReserveQty) *
                WAD,
            wDiv(
                _internalBalances.baseTokenReserveQty,
                _internalBalances.quoteTokenReserveQty
            )
        ) >= WAD);
    }

    function calculateQty(
        uint256 _tokenAQty,
        uint256 _tokenAReserveQty,
        uint256 _tokenBReserveQty
    ) public pure returns (uint256 tokenBQty) {
        require(_tokenAQty > 0, "MathLib: INSUFFICIENT_QTY");
        require(
            _tokenAReserveQty > 0 && _tokenBReserveQty > 0,
            "MathLib: INSUFFICIENT_LIQUIDITY"
        );
        tokenBQty = (_tokenAQty * _tokenBReserveQty) / _tokenAReserveQty;
    }

    function calculateQtyToReturnAfterFees(
        uint256 _tokenASwapQty,
        uint256 _tokenAReserveQty,
        uint256 _tokenBReserveQty,
        uint256 _liquidityFeeInBasisPoints
    ) public pure returns (uint256 qtyToReturn) {
        uint256 tokenASwapQtyLessFee =
            _tokenASwapQty * (BASIS_POINTS - _liquidityFeeInBasisPoints);
        qtyToReturn =
            (tokenASwapQtyLessFee * _tokenBReserveQty) /
            ((_tokenAReserveQty * BASIS_POINTS) + tokenASwapQtyLessFee);
    }

    function calculateLiquidityTokenQtyForSingleAssetEntry(
        uint256 _totalSupplyOfLiquidityTokens,
        uint256 _tokenQtyAToAdd,
        uint256 _internalTokenAReserveQty,
        uint256 _tokenBDecayChange,
        uint256 _tokenBDecay
    ) public pure returns (uint256 liquidityTokenQty) {
        uint256 wGamma =
            wDiv(
                (
                    wMul(
                        wDiv(_tokenQtyAToAdd, _internalTokenAReserveQty),
                        _tokenBDecayChange * WAD
                    )
                ),
                _tokenBDecay
            ) /
                WAD /
                2;

        liquidityTokenQty =
            wDiv(
                wMul(_totalSupplyOfLiquidityTokens * WAD, wGamma),
                WAD - wGamma
            ) /
            WAD;
    }

    function calculateLiquidityTokenQtyForDoubleAssetEntry(
        uint256 _totalSupplyOfLiquidityTokens,
        uint256 _quoteTokenQty,
        uint256 _quoteTokenReserveBalance
    ) public pure returns (uint256 liquidityTokenQty) {
        liquidityTokenQty =
            (_quoteTokenQty * _totalSupplyOfLiquidityTokens) /
            _quoteTokenReserveBalance;
    }

    function calculateAddQuoteTokenLiquidityQuantities(
        uint256 _quoteTokenQtyDesired,
        uint256 _quoteTokenQtyMin,
        uint256 _baseTokenReserveQty,
        uint256 _totalSupplyOfLiquidityTokens,
        InternalBalances storage _internalBalances
    ) public returns (uint256 quoteTokenQty, uint256 liquidityTokenQty) {
        uint256 baseTokenDecay =
            _baseTokenReserveQty - _internalBalances.baseTokenReserveQty;

        uint256 wInternalBaseTokenToQuoteTokenRatio =
            wDiv(
                _internalBalances.baseTokenReserveQty,
                _internalBalances.quoteTokenReserveQty
            );

        uint256 maxQuoteTokenQty =
            wDiv(baseTokenDecay, wInternalBaseTokenToQuoteTokenRatio);

        require(
            _quoteTokenQtyMin < maxQuoteTokenQty,
            "MathLib: INSUFFICIENT_DECAY"
        );

        if (_quoteTokenQtyDesired > maxQuoteTokenQty) {
            quoteTokenQty = maxQuoteTokenQty;
        } else {
            quoteTokenQty = _quoteTokenQtyDesired;
        }

        uint256 baseTokenQtyDecayChange =
            roundToNearest(
                (quoteTokenQty * wInternalBaseTokenToQuoteTokenRatio),
                WAD
            ) / WAD;

        require(
            baseTokenQtyDecayChange > 0,
            "MathLib: INSUFFICIENT_CHANGE_IN_DECAY"
        );
        _internalBalances.baseTokenReserveQty += baseTokenQtyDecayChange;
        _internalBalances.quoteTokenReserveQty += quoteTokenQty;

        liquidityTokenQty = calculateLiquidityTokenQtyForSingleAssetEntry(
            _totalSupplyOfLiquidityTokens,
            quoteTokenQty,
            _internalBalances.quoteTokenReserveQty,
            baseTokenQtyDecayChange,
            baseTokenDecay
        );
        return (quoteTokenQty, liquidityTokenQty);
    }

    function calculateAddBaseTokenLiquidityQuantities(
        uint256 _baseTokenQtyDesired,
        uint256 _baseTokenQtyMin,
        uint256 _baseTokenReserveQty,
        uint256 _totalSupplyOfLiquidityTokens,
        InternalBalances memory _internalBalances
    ) public pure returns (uint256 baseTokenQty, uint256 liquidityTokenQty) {
        uint256 maxBaseTokenQty =
            _internalBalances.baseTokenReserveQty - _baseTokenReserveQty;
        require(
            _baseTokenQtyMin < maxBaseTokenQty,
            "MathLib: INSUFFICIENT_DECAY"
        );

        if (_baseTokenQtyDesired > maxBaseTokenQty) {
            baseTokenQty = maxBaseTokenQty;
        } else {
            baseTokenQty = _baseTokenQtyDesired;
        }

        uint256 wInternalQuoteToBaseTokenRatio =
            wDiv(
                _internalBalances.quoteTokenReserveQty,
                _internalBalances.baseTokenReserveQty
            );

        uint256 quoteTokenQtyDecayChange =
            roundToNearest(
                (baseTokenQty * wInternalQuoteToBaseTokenRatio),
                MathLib.WAD
            ) / WAD;

        require(
            quoteTokenQtyDecayChange > 0,
            "MathLib: INSUFFICIENT_CHANGE_IN_DECAY"
        );

        uint256 quoteTokenDecay =
            (maxBaseTokenQty * wInternalQuoteToBaseTokenRatio) / WAD;

        require(quoteTokenDecay > 0, "MathLib: NO_QUOTE_DECAY");

        liquidityTokenQty = calculateLiquidityTokenQtyForSingleAssetEntry(
            _totalSupplyOfLiquidityTokens,
            baseTokenQty,
            _internalBalances.baseTokenReserveQty,
            quoteTokenQtyDecayChange,
            quoteTokenDecay
        );
        return (baseTokenQty, liquidityTokenQty);
    }

    function calculateAddLiquidityQuantities(
        uint256 _baseTokenQtyDesired,
        uint256 _quoteTokenQtyDesired,
        uint256 _baseTokenQtyMin,
        uint256 _quoteTokenQtyMin,
        uint256 _baseTokenReserveQty,
        uint256 _quoteTokenReserveQty,
        uint256 _totalSupplyOfLiquidityTokens,
        InternalBalances storage _internalBalances
    ) public returns (TokenQtys memory tokenQtys) {
        if (_totalSupplyOfLiquidityTokens > 0) {

            tokenQtys.liquidityTokenFeeQty = calculateLiquidityTokenFees(
                _totalSupplyOfLiquidityTokens,
                _internalBalances
            );

            _totalSupplyOfLiquidityTokens += tokenQtys.liquidityTokenFeeQty;

            if (
                isSufficientDecayPresent(
                    _baseTokenReserveQty,
                    _internalBalances
                )
            ) {

                uint256 baseTokenQtyFromDecay;
                uint256 quoteTokenQtyFromDecay;
                uint256 liquidityTokenQtyFromDecay;

                if (
                    _baseTokenReserveQty > _internalBalances.baseTokenReserveQty
                ) {
                    (
                        quoteTokenQtyFromDecay,
                        liquidityTokenQtyFromDecay
                    ) = calculateAddQuoteTokenLiquidityQuantities(
                        _quoteTokenQtyDesired,
                        0,
                        _baseTokenReserveQty,
                        _totalSupplyOfLiquidityTokens,
                        _internalBalances
                    );
                } else {
                    (
                        baseTokenQtyFromDecay,
                        liquidityTokenQtyFromDecay
                    ) = calculateAddBaseTokenLiquidityQuantities(
                        _baseTokenQtyDesired,
                        0,
                        _baseTokenReserveQty,
                        _totalSupplyOfLiquidityTokens,
                        _internalBalances
                    );
                }

                if (
                    quoteTokenQtyFromDecay < _quoteTokenQtyDesired &&
                    baseTokenQtyFromDecay < _baseTokenQtyDesired
                ) {
                    (
                        tokenQtys.baseTokenQty,
                        tokenQtys.quoteTokenQty,
                        tokenQtys.liquidityTokenQty
                    ) = calculateAddTokenPairLiquidityQuantities(
                        _baseTokenQtyDesired - baseTokenQtyFromDecay,
                        _quoteTokenQtyDesired - quoteTokenQtyFromDecay,
                        0,
                        0,
                        _quoteTokenReserveQty + quoteTokenQtyFromDecay,
                        _totalSupplyOfLiquidityTokens +
                            liquidityTokenQtyFromDecay,
                        _internalBalances
                    );
                }
                tokenQtys.baseTokenQty += baseTokenQtyFromDecay;
                tokenQtys.quoteTokenQty += quoteTokenQtyFromDecay;
                tokenQtys.liquidityTokenQty += liquidityTokenQtyFromDecay;

                require(
                    tokenQtys.baseTokenQty >= _baseTokenQtyMin,
                    "MathLib: INSUFFICIENT_BASE_QTY"
                );

                require(
                    tokenQtys.quoteTokenQty >= _quoteTokenQtyMin,
                    "MathLib: INSUFFICIENT_QUOTE_QTY"
                );
            } else {
                (
                    tokenQtys.baseTokenQty,
                    tokenQtys.quoteTokenQty,
                    tokenQtys.liquidityTokenQty
                ) = calculateAddTokenPairLiquidityQuantities(
                    _baseTokenQtyDesired,
                    _quoteTokenQtyDesired,
                    _baseTokenQtyMin,
                    _quoteTokenQtyMin,
                    _quoteTokenReserveQty,
                    _totalSupplyOfLiquidityTokens,
                    _internalBalances
                );
            }
        } else {
            require(
                _baseTokenQtyDesired > 0,
                "MathLib: INSUFFICIENT_BASE_QTY_DESIRED"
            );
            require(
                _quoteTokenQtyDesired > 0,
                "MathLib: INSUFFICIENT_QUOTE_QTY_DESIRED"
            );

            tokenQtys.baseTokenQty = _baseTokenQtyDesired;
            tokenQtys.quoteTokenQty = _quoteTokenQtyDesired;
            tokenQtys.liquidityTokenQty = sqrt(
                _baseTokenQtyDesired * _quoteTokenQtyDesired
            );

            _internalBalances.baseTokenReserveQty += tokenQtys.baseTokenQty;
            _internalBalances.quoteTokenReserveQty += tokenQtys.quoteTokenQty;
        }
    }

    function calculateAddTokenPairLiquidityQuantities(
        uint256 _baseTokenQtyDesired,
        uint256 _quoteTokenQtyDesired,
        uint256 _baseTokenQtyMin,
        uint256 _quoteTokenQtyMin,
        uint256 _quoteTokenReserveQty,
        uint256 _totalSupplyOfLiquidityTokens,
        InternalBalances storage _internalBalances
    )
        public
        returns (
            uint256 baseTokenQty,
            uint256 quoteTokenQty,
            uint256 liquidityTokenQty
        )
    {
        uint256 requiredQuoteTokenQty =
            calculateQty(
                _baseTokenQtyDesired,
                _internalBalances.baseTokenReserveQty,
                _internalBalances.quoteTokenReserveQty
            );

        if (requiredQuoteTokenQty <= _quoteTokenQtyDesired) {
            require(
                requiredQuoteTokenQty >= _quoteTokenQtyMin,
                "MathLib: INSUFFICIENT_QUOTE_QTY"
            );
            baseTokenQty = _baseTokenQtyDesired;
            quoteTokenQty = requiredQuoteTokenQty;
        } else {
            uint256 requiredBaseTokenQty =
                calculateQty(
                    _quoteTokenQtyDesired,
                    _internalBalances.quoteTokenReserveQty,
                    _internalBalances.baseTokenReserveQty
                );

            require(
                requiredBaseTokenQty >= _baseTokenQtyMin,
                "MathLib: INSUFFICIENT_BASE_QTY"
            );
            baseTokenQty = requiredBaseTokenQty;
            quoteTokenQty = _quoteTokenQtyDesired;
        }

        liquidityTokenQty = calculateLiquidityTokenQtyForDoubleAssetEntry(
            _totalSupplyOfLiquidityTokens,
            quoteTokenQty,
            _quoteTokenReserveQty
        );

        _internalBalances.baseTokenReserveQty += baseTokenQty;
        _internalBalances.quoteTokenReserveQty += quoteTokenQty;
    }

    function calculateBaseTokenQty(
        uint256 _quoteTokenQty,
        uint256 _baseTokenQtyMin,
        uint256 _baseTokenReserveQty,
        uint256 _liquidityFeeInBasisPoints,
        InternalBalances storage _internalBalances
    ) public returns (uint256 baseTokenQty) {
        require(
            _baseTokenReserveQty > 0 &&
                _internalBalances.baseTokenReserveQty > 0,
            "MathLib: INSUFFICIENT_BASE_TOKEN_QTY"
        );

        if (_baseTokenReserveQty < _internalBalances.baseTokenReserveQty) {
            uint256 wPricingRatio =
                wDiv(
                    _internalBalances.baseTokenReserveQty,
                    _internalBalances.quoteTokenReserveQty
                );

            uint256 impliedQuoteTokenQty =
                wDiv(_baseTokenReserveQty, wPricingRatio);

            baseTokenQty = calculateQtyToReturnAfterFees(
                _quoteTokenQty,
                impliedQuoteTokenQty,
                _baseTokenReserveQty,
                _liquidityFeeInBasisPoints
            );
        } else {
            baseTokenQty = calculateQtyToReturnAfterFees(
                _quoteTokenQty,
                _internalBalances.quoteTokenReserveQty,
                _internalBalances.baseTokenReserveQty,
                _liquidityFeeInBasisPoints
            );
        }

        require(
            baseTokenQty > _baseTokenQtyMin,
            "MathLib: INSUFFICIENT_BASE_TOKEN_QTY"
        );

        _internalBalances.baseTokenReserveQty -= baseTokenQty;
        _internalBalances.quoteTokenReserveQty += _quoteTokenQty;
    }

    function calculateQuoteTokenQty(
        uint256 _baseTokenQty,
        uint256 _quoteTokenQtyMin,
        uint256 _liquidityFeeInBasisPoints,
        InternalBalances storage _internalBalances
    ) public returns (uint256 quoteTokenQty) {
        require(
            _baseTokenQty > 0 && _quoteTokenQtyMin > 0,
            "MathLib: INSUFFICIENT_TOKEN_QTY"
        );

        quoteTokenQty = calculateQtyToReturnAfterFees(
            _baseTokenQty,
            _internalBalances.baseTokenReserveQty,
            _internalBalances.quoteTokenReserveQty,
            _liquidityFeeInBasisPoints
        );

        require(
            quoteTokenQty > _quoteTokenQtyMin,
            "MathLib: INSUFFICIENT_QUOTE_TOKEN_QTY"
        );

        _internalBalances.baseTokenReserveQty += _baseTokenQty;
        _internalBalances.quoteTokenReserveQty -= quoteTokenQty;
    }

    function calculateLiquidityTokenFees(
        uint256 _totalSupplyOfLiquidityTokens,
        InternalBalances memory _internalBalances
    ) public pure returns (uint256 liquidityTokenFeeQty) {
        uint256 rootK =
            sqrt(
                _internalBalances.baseTokenReserveQty *
                    _internalBalances.quoteTokenReserveQty
            );
        uint256 rootKLast = sqrt(_internalBalances.kLast);
        if (rootK > rootKLast) {
            uint256 numerator =
                _totalSupplyOfLiquidityTokens * (rootK - rootKLast);
            uint256 denominator = (rootK * 5) + rootKLast;
            liquidityTokenFeeQty = numerator / denominator;
        }
    }
}
