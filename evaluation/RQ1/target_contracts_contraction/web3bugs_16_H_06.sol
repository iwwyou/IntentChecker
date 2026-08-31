pragma solidity ^0.8.0;

contract GasOracle {
    IChainlinkOracle public gasOracle;
    IChainlinkOracle public priceOracle;

    function latestAnswer() external view returns (uint256) {
        uint256 gasPrice = uint256(gasOracle.latestAnswer());
        uint256 ethPrice = uint256(priceOracle.latestAnswer());

        uint256 result = PRBMathUD60x18.mul(gasPrice, ethPrice);
        return result;
    }
}
