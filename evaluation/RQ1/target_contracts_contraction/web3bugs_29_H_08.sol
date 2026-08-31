pragma solidity >=0.8.0;

contract HybridPool {
    address public immutable bento;
    address public immutable token0;
    address public immutable token1;

    uint128 internal reserve0;
    uint128 internal reserve1;

    function _toAmount(address token, uint256 input) internal view returns (uint256 output) {
        (, bytes memory _output) = bento.staticcall(abi.encodeWithSelector(IBentoBoxMinimal.toAmount.selector,
            token, input, false));
        output = abi.decode(_output, (uint256));
    }

    function _getReserves() internal view returns (uint256 _reserve0, uint256 _reserve1) {
        (_reserve0, _reserve1) = (reserve0, reserve1);
        _reserve0 = _toAmount(token0, _reserve0);
        _reserve1 = _toAmount(token1, _reserve1);
    }
}
