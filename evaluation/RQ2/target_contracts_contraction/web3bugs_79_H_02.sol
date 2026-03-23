pragma solidity ^0.8.0;

contract LaunchEvent is Ownable {
    enum Phase {
        NotStarted,
        PhaseOne,
        PhaseTwo,
        PhaseThree
    }

    struct UserInfo {
        uint256 allocation;
        uint256 balance;
        bool hasWithdrawnPair;
        bool hasWithdrawnIncentives;
    }

    address public issuer;

    uint256 public auctionStart;

    uint256 public PHASE_ONE_DURATION;
    uint256 public PHASE_ONE_NO_FEE_DURATION;
    uint256 public PHASE_TWO_DURATION;

    uint256 public tokenIncentivesPercent;

    uint256 public floorPrice;

    uint256 public userTimelock;

    uint256 public issuerTimelock;

    uint256 public maxWithdrawPenalty;

    uint256 public fixedWithdrawPenalty;

    IRocketJoeToken public rJoe;
    uint256 public rJoePerAvax;
    IWAVAX private WAVAX;
    IERC20Metadata public token;

    IJoeRouter02 private router;
    IJoeFactory private factory;
    IRocketJoeFactory public rocketJoeFactory;

    bool private initialized;
    bool public stopped;

    uint256 public maxAllocation;

    mapping(address => UserInfo) public getUserInfo;

    IJoePair public pair;

    uint256 private wavaxAllocated;

    uint256 private lpSupply;

    uint256 private tokenReserve;

    uint256 private tokenIncentivesBalance;
    uint256 private tokenIncentivesForUsers;
    uint256 private tokenIncentiveIssuerRefund;

    uint256 private wavaxReserve;

    modifier atPhase(Phase _phase) {
        _atPhase(_phase);
        _;
    }

    modifier isStopped(bool _stopped) {
        if (_stopped) {
            require(stopped, "LaunchEvent: is still running");
        } else {
            require(!stopped, "LaunchEvent: stopped");
        }
        _;
    }

    function createPair() external isStopped(false) atPhase(Phase.PhaseThree) {
        (address wavaxAddress, address tokenAddress) = (address(WAVAX), address(token));
        require(
            factory.getPair(wavaxAddress, tokenAddress) == address(0) ||
                IJoePair(
                    IJoeFactory(factory).getPair(wavaxAddress, tokenAddress)
                ).totalSupply() ==
                0,
            "LaunchEvent: liquid pair already exists"
        );
        require(wavaxReserve > 0, "LaunchEvent: no wavax balance");

        uint256 tokenAllocated = tokenReserve;

        if (floorPrice > (wavaxReserve * 10**token.decimals()) / tokenAllocated) {
            tokenAllocated = (wavaxReserve * 10**token.decimals()) / floorPrice;
            tokenIncentivesForUsers = (tokenIncentivesForUsers * tokenAllocated) / tokenReserve;
            tokenIncentiveIssuerRefund = tokenIncentivesBalance - tokenIncentivesForUsers;
        }

        WAVAX.approve(address(router), wavaxReserve);
        token.approve(address(router), tokenAllocated);

        (, , lpSupply) = router.addLiquidity(
            wavaxAddress,
            tokenAddress,
            wavaxReserve,
            tokenAllocated,
            wavaxReserve,
            tokenAllocated,
            address(this),
            block.timestamp
        );

        pair = IJoePair(factory.getPair(tokenAddress, wavaxAddress));
        wavaxAllocated = wavaxReserve;
        wavaxReserve = 0;

        tokenReserve -= tokenAllocated;
    }    
}
