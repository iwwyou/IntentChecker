pragma solidity 0.8.1;

contract CTokenMultiOracle is IOracle, AccessControl, Constants {
    using CastBytes32Bytes6 for bytes32;

    uint8 public constant override decimals = 18;

    event SourceSet(bytes6 indexed baseId, bytes6 indexed quoteId, address indexed source);

    struct Source {
        address source;
        uint8 decimals;
        bool inverse;
    }

    mapping(bytes6 => mapping(bytes6 => Source)) public sources;

    function setSource(bytes6 cTokenId, bytes6 underlying, address cToken) external auth {
        _setSource(cTokenId, underlying, cToken);
    }

    function setSources(bytes6[] memory cTokenIds, bytes6[] memory underlyings, address[] memory cTokens) external auth {
        require(
            cTokenIds.length == underlyings.length &&
            cTokenIds.length == cTokens.length,
            "Mismatched inputs"
        );
        for (uint256 i = 0; i < cTokenIds.length; i++) {
            _setSource(cTokenIds[i], underlyings[i], cTokens[i]);
        }
    }

    function peek(bytes32 base, bytes32 quote, uint256 amount)
        external view virtual override
        returns (uint256 value, uint256 updateTime)
    {
        uint256 price;
        (price, updateTime) = _peek(base.b6(), quote.b6());
        value = price * amount / 1e18;
    }

    function get(bytes32 base, bytes32 quote, uint256 amount)
        external virtual override
        returns (uint256 value, uint256 updateTime)
    {
        uint256 price;
        (price, updateTime) = _get(base.b6(), quote.b6());
        value = price * amount / 1e18;
    }

    function _peek(bytes6 base, bytes6 quote) private view returns (uint price, uint updateTime) {
        uint256 rawPrice;
        Source memory source = sources[base][quote];
        require (source.source != address(0), "Source not found");

        rawPrice = CTokenInterface(source.source).exchangeRateStored();

        require(rawPrice > 0, "Compound price is zero");

        if (source.inverse == true) {
            price = 10 ** (source.decimals + 18) / uint(rawPrice);
        } else {
            price = uint(rawPrice) * 10 ** (18 - source.decimals);
        }

        updateTime = block.timestamp;
    }

    function _get(bytes6 base, bytes6 quote) private returns (uint price, uint updateTime) {
        uint256 rawPrice;
        Source memory source = sources[base][quote];
        require (source.source != address(0), "Source not found");

        rawPrice = CTokenInterface(source.source).exchangeRateCurrent();

        require(rawPrice > 0, "Compound price is zero");

        if (source.inverse == true) {
            price = 10 ** (source.decimals + 18) / uint(rawPrice);
        } else {
            price = uint(rawPrice) * 10 ** (18 - source.decimals);
        }

        updateTime = block.timestamp;
    }

    function _setSource(bytes6 cTokenId, bytes6 underlying, address source) internal {
        uint8 decimals_ = 18;
        require (decimals_ <= 18, "Unsupported decimals");
        sources[cTokenId][underlying] = Source({
            source: source,
            decimals: decimals_,
            inverse: false
        });
        sources[underlying][cTokenId] = Source({
            source: source,
            decimals: decimals_,
            inverse: true
        });
        emit SourceSet(cTokenId, underlying, source);
        emit SourceSet(underlying, cTokenId, source);
    }
}
