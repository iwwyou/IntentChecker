pragma solidity ^0.8.0;

contract Stream {
    using SafeTransferLib for ERC20;

    struct TokenStream {
        uint256 lastCumulativeRewardPerToken;
        uint256 virtualBalance;
        uint112 rewards;
        uint112 tokens;
        uint32 lastUpdate;
        bool merkleAccess;
    }

    uint32 private immutable streamDuration;
    uint32 private immutable endStream;
    uint32 private immutable endRewardLock;

    address public immutable rewardToken;

    uint112 private immutable depositDecimalsOne;

    uint112 private rewardTokenAmount;

    uint8 private unlocked = 1;

    uint256 private cumulativeRewardPerToken;

    uint256 private totalVirtualBalance;

    uint32 private lastUpdate;

    mapping (address => TokenStream) public tokensNotYetStreamed;

    event RewardsClaimed(address indexed who, uint256 amount);

    function lockInternal() internal {
        require(unlocked == 1, "re");
        unlocked = 2;
    }
    modifier lock {
        lockInternal();
        _;
        unlocked = 1;
    }

    function lastApplicableTime() internal view returns (uint32) {
        return block.timestamp <= endStream ? uint32(block.timestamp) : endStream;
    }

    function rewardPerToken() public view returns (uint256) {
        if (totalVirtualBalance == 0) {
            return cumulativeRewardPerToken;
        } else {
            return cumulativeRewardPerToken + (
                ((uint256(lastApplicableTime()) - lastUpdate) * rewardTokenAmount * depositDecimalsOne/streamDuration)
                / totalVirtualBalance
            );
        }
    }

    function earned(TokenStream storage ts, uint256 currCumRewardPerToken) internal view returns (uint112) {
        return uint112(ts.virtualBalance * (currCumRewardPerToken - ts.lastCumulativeRewardPerToken) / depositDecimalsOne) + ts.rewards;
    }

    function claimReward() public lock {
        require(block.timestamp > endRewardLock, "lock");

        TokenStream storage ts = tokensNotYetStreamed[msg.sender];
        cumulativeRewardPerToken = rewardPerToken();

        ts.rewards = earned(ts, cumulativeRewardPerToken);
        ts.lastCumulativeRewardPerToken = cumulativeRewardPerToken;

        lastUpdate = lastApplicableTime();

        uint256 rewardAmt = ts.rewards;
        ts.rewards = 0;

        require(rewardAmt > 0, "amt");

        ERC20(rewardToken).safeTransfer(msg.sender, rewardAmt);

        emit RewardsClaimed(msg.sender, rewardAmt);
    }
}
