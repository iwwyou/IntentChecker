pragma solidity ^0.8.11;

interface IERC20 {
}

contract MasterChef is Ownable {
    using SafeMath for uint;

    struct PoolInfo {
        IERC20 depositToken;
        uint allocPoint;
        uint lastRewardBlock;
        uint accConcurPerShare;
        uint16 depositFeeBP;
    }

    PoolInfo[] public poolInfo;
    mapping(address => uint256) public pid;
    uint public totalAllocPoint = 0;

    function add(address _token, uint _allocationPoints, uint16 _depositFee, uint _startBlock) public onlyOwner {
        require(_token != address(0), "zero address");
        uint lastRewardBlock = block.number > _startBlock ? block.number : _startBlock;
        totalAllocPoint = totalAllocPoint.add(_allocationPoints);
        require(pid[_token] == 0, "already registered");
        poolInfo.push(
            PoolInfo({
                depositToken: IERC20(_token),
                allocPoint: _allocationPoints,
                lastRewardBlock: lastRewardBlock,
                accConcurPerShare: 0,
                depositFeeBP: _depositFee
            })
        );
        pid[_token] = poolInfo.length - 1;
    }
}
