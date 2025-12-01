contract HippoHotel is ERC721, Ownable {
    using SafeMath for uint256;

    uint256 public mintPrice;
    uint256 public maxToMint;
    uint256 public maxNftSupply;
    address private wallet1;
    address private wallet2;
    bool public saleIsActive;

    // Note: The following modifiers are not defined in this contract: onlyOwner

    function withdraw() external onlyOwner {
        uint256 balance = address(this).balance;
        uint256 balance2 = balance.mul(25).div(100);
        payable(wallet2).transfer(balance2);   
        payable(wallet1).transfer(balance.sub(balance2));        
    }

}