pragma solidity ^0.8.0;

contract Lock {
    IBondNFT public immutable bondNFT;
    IGovNFT public immutable govNFT;

    mapping(address => uint) public totalLocked;

    /**
     * @notice Claim rewards from gov nfts and distribute them to bonds
     */
    function claimGovFees() public {
        address[] memory assets = bondNFT.getAssets();

        for (uint i=0; i < assets.length; i++) {
            uint balanceBefore = IERC20(assets[i]).balanceOf(address(this));
            IGovNFT(govNFT).claim(assets[i]);
            uint balanceAfter = IERC20(assets[i]).balanceOf(address(this));
            IERC20(assets[i]).approve(address(bondNFT), type(uint256).max);
            bondNFT.distribute(assets[i], balanceAfter - balanceBefore);
        }
    }

    function claim(
        uint256 _id
    ) public returns (address) {
        claimGovFees();
        (uint _amount, address _tigAsset) = bondNFT.claim(_id, msg.sender);
        IERC20(_tigAsset).transfer(msg.sender, _amount);
        return _tigAsset;
    }

    /**
     * @notice Reset the lock time and extend the period and/or token amount
     * @param _id Bond id being extended
     * @param _amount tigAsset amount being added
     * @param _period number of days being added
     */
    function extendLock(
        uint _id,
        uint _amount,
        uint _period
    ) public {
        address _asset = claim(_id);
        IERC20(_asset).transferFrom(msg.sender, address(this), _amount);
        bondNFT.extendLock(_id, _asset, _amount, _period, msg.sender);
    }
}
