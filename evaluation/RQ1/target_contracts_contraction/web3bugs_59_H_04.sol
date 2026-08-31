pragma solidity >=0.6.6;

contract AuctionBurnReserveSkew {
  uint256[] public pegObservations;
  uint256 public auctionAverageLookback = 10;
  uint256 public count;

  function _getIndexOfObservation(uint _index) internal view returns (uint index) {
    return _index % auctionAverageLookback;
  }

  function getPegDeltaFrequency() public view returns (uint256) {
    uint256 initialIndex = 0;
    uint256 index;

    if (count > auctionAverageLookback) {
      initialIndex = count - auctionAverageLookback;
    }

    uint256 total = 0;

    for (uint256 i = initialIndex; i < count; ++i) {
      index = _getIndexOfObservation(i);
      total = total + pegObservations[index];
    }

    return total * 10000 / auctionAverageLookback;
  }
}
