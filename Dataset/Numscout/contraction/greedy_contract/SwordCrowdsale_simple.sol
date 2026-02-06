pragma solidity ^0.6.12;

contract SwordCrowdsale {
    struct Contributor {
        uint256 contributionAmount;
        uint256 tokensIssued;
    }

    mapping(address => Contributor) public contributorList;

    uint256 public weiRaised;
    address payable public wallet;

    constructor(address payable _wallet) public {
        wallet = _wallet;
    }

    function contribute() external payable {
        contributorList[msg.sender].contributionAmount += msg.value;
        weiRaised += msg.value;
    }

    function forwardAllRaisedFunds() internal {
        wallet.transfer(weiRaised);
    }

    function refundMoney(address payable _address) public {
        uint256 amount = contributorList[_address].contributionAmount;
        if (amount > 0 && _address.send(amount)) {
            contributorList[_address].contributionAmount = 0;
            contributorList[_address].tokensIssued = 0;
        }
        // @Post weiRaised(Entry > Exit)
    }
}
