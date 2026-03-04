pragma solidity ^0.8.0;

contract Lock is Ownable{

    uint public constant minPeriod = 7;
    uint public constant maxPeriod = 365;

    IBondNFT public immutable bondNFT;
    IGovNFT public immutable govNFT;

    mapping(address => bool) public allowedAssets;
    mapping(address => uint) public totalLocked;

    function claim(
        uint256 _id
    ) public returns (address) {
        claimGovFees();
        (uint _amount, address _tigAsset) = bondNFT.claim(_id, msg.sender);
        IERC20(_tigAsset).transfer(msg.sender, _amount);
        return _tigAsset;
    }

    function claimDebt(
        address _tigAsset
    ) external {
        claimGovFees();
        uint amount = bondNFT.claimDebt(msg.sender, _tigAsset);
        IERC20(_tigAsset).transfer(msg.sender, amount);
    }

    function lock(
        address _asset,
        uint _amount,
        uint _period
    ) public {
        require(_period <= maxPeriod, "MAX PERIOD");
        require(_period >= minPeriod, "MIN PERIOD");
        require(allowedAssets[_asset], "!asset");

        claimGovFees();

        IERC20(_asset).transferFrom(msg.sender, address(this), _amount);
        totalLocked[_asset] += _amount;

        bondNFT.createLock( _asset, _amount, _period, msg.sender);
    }

    function extendLock(
        uint _id,
        uint _amount,
        uint _period
    ) public {
        address _asset = claim(_id);
        IERC20(_asset).transferFrom(msg.sender, address(this), _amount);
        bondNFT.extendLock(_id, _asset, _amount, _period, msg.sender);
    }

    function release(
        uint _id
    ) public {
        claimGovFees();
        (uint amount, uint lockAmount, address asset, address _owner) = bondNFT.release(_id, msg.sender);
        totalLocked[asset] -= lockAmount;
        IERC20(asset).transfer(_owner, amount);
    }

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

    function editAsset(
        address _tigAsset,
        bool _isAllowed
    ) external onlyOwner() {
        allowedAssets[_tigAsset] = _isAllowed;
    }

    function sendNFTs(
        uint[] memory _ids
    ) external onlyOwner() {
        govNFT.safeTransferMany(msg.sender, _ids);
    }
}
