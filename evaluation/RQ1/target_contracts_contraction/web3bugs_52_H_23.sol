pragma solidity =0.8.9;

contract VaderPoolV2 {
    struct PriceCumulative {
        uint256 nativeLast;
        uint256 foreignLast;
    }

    struct PairInfo {
        uint256 totalSupply;
        uint112 reserveNative;
        uint112 reserveForeign;
        uint32 blockTimestampLast;
        PriceCumulative priceCumulative;
    }

    event Sync(IERC20 foreignAsset, uint256 reserve0, uint256 reserve1);

    IERC20 public immutable nativeAsset;

    mapping(IERC20 => bool) public supported;
    mapping(IERC20 => PairInfo) public pairInfo;

    ISynthFactory public synthFactory;

    function _supportedToken(IERC20 token) private view {
        require(supported[token], "BasePoolV2::_supportedToken: Unsupported Token");
    }
    modifier supportedToken(IERC20 token) {
        _supportedToken(token);
        _;
    }

    function getReserves(IERC20 foreignAsset)
        public
        view
        returns (
            uint112 reserveNative,
            uint112 reserveForeign,
            uint32 blockTimestampLast
        )
    {
        PairInfo storage pair = pairInfo[foreignAsset];
        (reserveNative, reserveForeign, blockTimestampLast) = (
            pair.reserveNative,
            pair.reserveForeign,
            pair.blockTimestampLast
        );
    }

    function _update(
        IERC20 foreignAsset,
        uint256 balanceNative,
        uint256 balanceForeign,
        uint112 reserveNative,
        uint112 reserveForeign
    ) internal {
        require(
            balanceNative <= type(uint112).max &&
                balanceForeign <= type(uint112).max,
            "BasePoolV2::_update: Balance Overflow"
        );
        uint32 blockTimestamp = uint32(block.timestamp % 2**32);
        PairInfo storage pair = pairInfo[foreignAsset];
        unchecked {
            uint32 timeElapsed = blockTimestamp - pair.blockTimestampLast;
            if (timeElapsed > 0 && reserveNative != 0 && reserveForeign != 0) {
                pair.priceCumulative.nativeLast +=
                    uint256(
                        UQ112x112.encode(reserveForeign).uqdiv(reserveNative)
                    ) *
                    timeElapsed;
                pair.priceCumulative.foreignLast +=
                    uint256(
                        UQ112x112.encode(reserveNative).uqdiv(reserveForeign)
                    ) *
                    timeElapsed;
            }
        }
        pair.reserveNative = uint112(balanceNative);
        pair.reserveForeign = uint112(balanceForeign);
        pair.blockTimestampLast = blockTimestamp;
        emit Sync(foreignAsset, balanceNative, balanceForeign);
    }

    function mintSynth(
        IERC20 foreignAsset,
        uint256 nativeDeposit,
        address from,
        address to
    )
        external
        supportedToken(foreignAsset)
        returns (uint256 amountSynth)
    {
        nativeAsset.safeTransferFrom(from, address(this), nativeDeposit);

        ISynth synth = synthFactory.synths(foreignAsset);

        if (synth == ISynth(address(0)))
            synth = synthFactory.createSynth(
                IERC20Extended(address(foreignAsset))
            );

        (uint112 reserveNative, uint112 reserveForeign, ) = getReserves(
            foreignAsset
        ); // gas savings

        amountSynth = VaderMath.calculateSwap(
            nativeDeposit,
            reserveNative,
            reserveForeign
        );

        // TODO: Clarify
        _update(
            foreignAsset,
            reserveNative + nativeDeposit,
            reserveForeign,
            reserveNative,
            reserveForeign
        );

        synth.mint(to, amountSynth);
    }
}
