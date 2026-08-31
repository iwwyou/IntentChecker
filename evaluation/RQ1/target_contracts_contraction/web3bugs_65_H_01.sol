pragma solidity =0.8.7;

contract Basket is ERC20Upgradeable {
    uint256 public constant ONE_YEAR = 365.25 days;
    uint256 private constant BASE = 1e18;

    address public publisher;
    uint256 public licenseFee;

    IFactory public factory;

    uint256 public ibRatio;

    uint256 public lastFee;

    event NewIBRatio(uint256 ibRatio);

    function handleFees(uint256 startSupply) private {
        if (lastFee == 0) {
            lastFee = block.timestamp;
        } else if (startSupply == 0) {
            return;
        } else {
            uint256 timeDiff = (block.timestamp - lastFee);
            uint256 feePct = timeDiff * licenseFee / ONE_YEAR;
            uint256 fee = startSupply * feePct / (BASE - feePct);

            _mint(publisher, fee * (BASE - factory.ownerSplit()) / BASE);
            _mint(Ownable(address(factory)).owner(), fee * factory.ownerSplit() / BASE);
            lastFee = block.timestamp;

            uint256 newIbRatio = ibRatio * startSupply / totalSupply();
            ibRatio = newIbRatio;

            emit NewIBRatio(ibRatio);
        }
    }
}
