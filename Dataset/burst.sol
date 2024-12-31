pragma solidity ^0.5.0;

contract BURST {
    string public name;
    string public symbol;
    uint8 public decimals; // 18 decimals is the strongly suggested default, avoid changing it

    uint256 public _totalSupply;

    mapping(address => uint) balances;
    mapping(address => mapping(address => uint)) allowed;

    constructor() public {
        name = "BURST";
        symbol = "BURST";
        decimals = 18;
        _totalSupply = 31000000000000000000000000;

        balances[msg.sender] = _totalSupply;
        emit Transfer(address(0), msg.sender, _totalSupply);
    }
//SWC-101-Integer Overflow and Underflow: L60
    function totalSupply() public view returns (uint) {
        return _totalSupply  - balances[address(0)];
    }
}