pragma solidity 0.8.7;

abstract contract AbstractRewards {
    uint256 public pointsPerShare;
    mapping(address => int256) public pointsCorrection;
    mapping(address => uint256) public withdrawnRewards;

    error SafeCastOverflowedUintToInt(uint256 value);

    function _correctPointsForTransfer(address _from, address _to, uint256 _shares) internal {
        require(_from != address(0), "AbstractRewards._correctPointsForTransfer: address cannot be zero address");
        require(_to != address(0), "AbstractRewards._correctPointsForTransfer: address cannot be zero address");
        require(_shares != 0, "AbstractRewards._correctPointsForTransfer: shares cannot be zero");

        //SWC-101-Integer Overflow and Underflow: L107
        int256 _magCorrection = toInt256(pointsPerShare * _shares);
        pointsCorrection[_from] = pointsCorrection[_from] + _magCorrection;
        pointsCorrection[_to] = pointsCorrection[_to] - _magCorrection;

    }

    function toInt256(uint256 value) internal pure returns (int256) {
        // Note: Unsafe cast below is okay because `type(int256).max` is guaranteed to be positive
        if (value > uint256(type(int256).max)) {
            revert SafeCastOverflowedUintToInt(value);
        }
        return int256(value);
    }
}