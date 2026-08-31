pragma solidity ^0.8.0;

contract Stream {
    using SafeTransferLib for ERC20;

    bool public immutable isSale;

    uint32 private immutable endStream;

    address public immutable depositToken;

    address public immutable streamCreator;

    uint112 private depositTokenAmount;
    uint112 private redeemedDepositTokens;

    bool private claimedDepositTokens;

    uint8 private unlocked = 1;

    event SoldTokensClaimed(address indexed who, uint256 amount);

    function lockInternal() internal {
        require(unlocked == 1, "re");
        unlocked = 2;
    }
    modifier lock {
        lockInternal();
        _;
        unlocked = 1;
    }

    /**
     *  @dev Allows a creator to claim sold tokens if the stream has ended & this contract is a sale
    */
    function creatorClaimSoldTokens(address destination) public lock {
        // can only claim when its a sale
        require(isSale, "!sale");

        // only can claim once
        require(!claimedDepositTokens, "claimed");
        // creator is claiming
        require(msg.sender == streamCreator, "!creator");
        // stream ended
        require(block.timestamp >= endStream, "stream");

        uint112 amount = depositTokenAmount;
        claimedDepositTokens = true;

        ERC20(depositToken).safeTransfer(destination, amount);

        emit SoldTokensClaimed(destination, amount);
    }
}
