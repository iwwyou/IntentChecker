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

    event IssuingTokenDeposited(address indexed token, uint256 amount);

    event UserParticipated(
        address indexed user,
        uint256 avaxAmount,
        uint256 rJoeAmount
    );

    event UserWithdrawn(address indexed user, uint256 avaxAmount);

    event LiquidityPoolCreated(
        address indexed pair,
        address indexed token0,
        address indexed token1,
        uint256 amount0,
        uint256 amount1
    );

    event UserLiquidityWithdrawn(
        address indexed user,
        address indexed pair,
        uint256 amount
    );

    event IssuerLiquidityWithdrawn(
        address indexed issuer,
        address indexed pair,
        uint256 amount
    );

    event Stopped();

    event AvaxEmergencyWithdraw(address indexed user, uint256 amount);

    event TokenEmergencyWithdraw(address indexed user, uint256 amount);

    receive() external payable {
        require(
            msg.sender == address(WAVAX),
            "LaunchEvent: you can't send AVAX directly to this contract"
        );
    }

    modifier atPhase(Phase _phase) {
        _atPhase(_phase);
        _;
    }

    modifier timelockElapsed() {
        uint256 phase3Start = auctionStart +
            PHASE_ONE_DURATION +
            PHASE_TWO_DURATION;
        if (msg.sender == issuer) {
            require(
                block.timestamp > phase3Start + issuerTimelock,
                "LaunchEvent: can't withdraw before issuer's timelock"
            );
        } else {
            require(
                block.timestamp > phase3Start + userTimelock,
                "LaunchEvent: can't withdraw before user's timelock"
            );
        }
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

    function initialize(
        address _issuer,
        uint256 _auctionStart,
        address _token,
        uint256 _tokenIncentivesPercent,
        uint256 _floorPrice,
        uint256 _maxWithdrawPenalty,
        uint256 _fixedWithdrawPenalty,
        uint256 _maxAllocation,
        uint256 _userTimelock,
        uint256 _issuerTimelock
    ) external atPhase(Phase.NotStarted) {
        require(!initialized, "LaunchEvent: already initialized");

        rocketJoeFactory = IRocketJoeFactory(msg.sender);
        WAVAX = IWAVAX(rocketJoeFactory.wavax());
        router = IJoeRouter02(rocketJoeFactory.router());
        factory = IJoeFactory(rocketJoeFactory.factory());
        rJoe = IRocketJoeToken(rocketJoeFactory.rJoe());
        rJoePerAvax = rocketJoeFactory.rJoePerAvax();

        require(
            _maxWithdrawPenalty <= 5e17,
            "LaunchEvent: maxWithdrawPenalty too big"
        );
        require(
            _fixedWithdrawPenalty <= 5e17,
            "LaunchEvent: fixedWithdrawPenalty too big"
        );
        require(
            _userTimelock <= 7 days,
            "LaunchEvent: can't lock user LP for more than 7 days"
        );
        require(
            _issuerTimelock > _userTimelock,
            "LaunchEvent: issuer can't withdraw before users"
        );
        require(
            _auctionStart > block.timestamp,
            "LaunchEvent: start of phase 1 cannot be in the past"
        );

        issuer = _issuer;

        auctionStart = _auctionStart;
        PHASE_ONE_DURATION = rocketJoeFactory.PHASE_ONE_DURATION();
        PHASE_ONE_NO_FEE_DURATION = rocketJoeFactory.PHASE_ONE_NO_FEE_DURATION();
        PHASE_TWO_DURATION = rocketJoeFactory.PHASE_TWO_DURATION();

        token = IERC20Metadata(_token);
        uint256 balance = token.balanceOf(address(this));

        tokenIncentivesPercent = _tokenIncentivesPercent;

        tokenReserve = (balance * 1e18) / (1e18 + _tokenIncentivesPercent);
        tokenIncentivesForUsers = balance - tokenReserve;
        tokenIncentivesBalance = tokenIncentivesForUsers;

        floorPrice = _floorPrice;

        maxWithdrawPenalty = _maxWithdrawPenalty;
        fixedWithdrawPenalty = _fixedWithdrawPenalty;

        maxAllocation = _maxAllocation;

        userTimelock = _userTimelock;
        issuerTimelock = _issuerTimelock;
        initialized = true;
    }

    function currentPhase() public view returns (Phase) {
        if (block.timestamp < auctionStart || auctionStart == 0) {
            return Phase.NotStarted;
        } else if (block.timestamp < auctionStart + PHASE_ONE_DURATION) {
            return Phase.PhaseOne;
        } else if (
            block.timestamp <
            auctionStart + PHASE_ONE_DURATION + PHASE_TWO_DURATION
        ) {
            return Phase.PhaseTwo;
        }
        return Phase.PhaseThree;
    }

    function depositAVAX()
        external
        payable
        isStopped(false)
        atPhase(Phase.PhaseOne)
    {
        require(msg.sender != issuer, "LaunchEvent: issuer cannot participate");
        require(
            msg.value > 0,
            "LaunchEvent: expected non-zero AVAX to deposit"
        );

        UserInfo storage user = getUserInfo[msg.sender];
        uint256 newAllocation = user.balance + msg.value;
        require(
            newAllocation <= maxAllocation,
            "LaunchEvent: amount exceeds max allocation"
        );

        uint256 rJoeNeeded;
        if (newAllocation > user.allocation) {
            rJoeNeeded = getRJoeAmount(newAllocation - user.allocation);
            user.allocation = newAllocation;
        }

        user.balance = newAllocation;
        wavaxReserve += msg.value;

        if (rJoeNeeded > 0) {
            rJoe.burnFrom(msg.sender, rJoeNeeded);
        }

        WAVAX.deposit{value: msg.value}();

        emit UserParticipated(msg.sender, msg.value, rJoeNeeded);
    }

    function withdrawAVAX(uint256 _amount) public isStopped(false) {
        Phase _currentPhase = currentPhase();
        require(
            _currentPhase == Phase.PhaseOne || _currentPhase == Phase.PhaseTwo,
            "LaunchEvent: unable to withdraw"
        );
        require(_amount > 0, "LaunchEvent: invalid withdraw amount");
        UserInfo storage user = getUserInfo[msg.sender];
        require(
            user.balance >= _amount,
            "LaunchEvent: withdrawn amount exceeds balance"
        );
        user.balance -= _amount;

        uint256 feeAmount = (_amount * getPenalty()) / 1e18;
        uint256 amountMinusFee = _amount - feeAmount;

        wavaxReserve -= _amount;

        WAVAX.withdraw(_amount);
        _safeTransferAVAX(msg.sender, amountMinusFee);
        if (feeAmount > 0) {
            _safeTransferAVAX(rocketJoeFactory.penaltyCollector(), feeAmount);
        }
    }

    function createPair() external isStopped(false) atPhase(Phase.PhaseThree) {
        (address wavaxAddress, address tokenAddress) = (
            address(WAVAX),
            address(token)
        );
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

        if (
            floorPrice > (wavaxReserve * 10**token.decimals()) / tokenAllocated
        ) {
            tokenAllocated = (wavaxReserve * 10**token.decimals()) / floorPrice;
            tokenIncentivesForUsers =
                (tokenIncentivesForUsers * tokenAllocated) /
                tokenReserve;
            tokenIncentiveIssuerRefund =
                tokenIncentivesBalance -
                tokenIncentivesForUsers;
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

        emit LiquidityPoolCreated(
            address(pair),
            tokenAddress,
            wavaxAddress,
            tokenAllocated,
            wavaxAllocated
        );
    }

    function withdrawLiquidity() external isStopped(false) timelockElapsed {
        require(address(pair) != address(0), "LaunchEvent: pair not created");

        UserInfo storage user = getUserInfo[msg.sender];
        require(
            !user.hasWithdrawnPair,
            "LaunchEvent: liquidity already withdrawn"
        );

        uint256 balance = pairBalance(msg.sender);
        user.hasWithdrawnPair = true;

        if (msg.sender == issuer) {
            balance = lpSupply / 2;

            emit IssuerLiquidityWithdrawn(msg.sender, address(pair), balance);

            if (tokenReserve > 0) {
                uint256 amount = tokenReserve;
                tokenReserve = 0;
                token.transfer(msg.sender, amount);
            }
        } else {
            emit UserLiquidityWithdrawn(msg.sender, address(pair), balance);
        }

        pair.transfer(msg.sender, balance);
    }

    function withdrawIncentives() external isStopped(false) {
        require(address(pair) != address(0), "LaunchEvent: pair not created");

        UserInfo storage user = getUserInfo[msg.sender];
        require(
            !user.hasWithdrawnIncentives,
            "LaunchEvent: incentives already withdrawn"
        );

        user.hasWithdrawnIncentives = true;
        uint256 amount;

        if (msg.sender == issuer) {
            amount = tokenIncentiveIssuerRefund;
        } else {
            amount = (user.balance * tokenIncentivesForUsers) / wavaxAllocated;
        }

        require(amount > 0, "LaunchEvent: caller has no incentive to claim");

        tokenIncentivesBalance -= amount;

        token.transfer(msg.sender, amount);
    }

    function emergencyWithdraw() external isStopped(true) {
        if (msg.sender != issuer) {
            UserInfo storage user = getUserInfo[msg.sender];
            require(
                user.balance > 0,
                "LaunchEvent: expected user to have non-zero balance to perform emergency withdraw"
            );

            uint256 balance = user.balance;
            user.balance = 0;
            wavaxReserve -= balance;
            WAVAX.withdraw(balance);

            _safeTransferAVAX(msg.sender, balance);

            emit AvaxEmergencyWithdraw(msg.sender, balance);
        } else {
            uint256 balance = tokenReserve + tokenIncentivesBalance;
            tokenReserve = 0;
            tokenIncentivesBalance = 0;
            token.transfer(issuer, balance);
            emit TokenEmergencyWithdraw(msg.sender, balance);
        }
    }

    function allowEmergencyWithdraw() external {
        require(
            msg.sender == Ownable(address(rocketJoeFactory)).owner(),
            "LaunchEvent: caller is not RocketJoeFactory owner"
        );
        stopped = true;
        emit Stopped();
    }

    function skim() external {
        address penaltyCollector = rocketJoeFactory.penaltyCollector();

        uint256 excessToken = token.balanceOf(address(this)) -
            tokenReserve -
            tokenIncentivesBalance;
        if (excessToken > 0) {
            token.transfer(penaltyCollector, excessToken);
        }

        uint256 excessWavax = WAVAX.balanceOf(address(this)) - wavaxReserve;
        if (excessWavax > 0) {
            WAVAX.transfer(penaltyCollector, excessWavax);
        }

        uint256 excessAvax = address(this).balance;
        if (excessAvax > 0) {
            _safeTransferAVAX(penaltyCollector, excessAvax);
        }
    }

    function getPenalty() public view returns (uint256) {
        uint256 timeElapsed = block.timestamp - auctionStart;
        if (timeElapsed < PHASE_ONE_NO_FEE_DURATION) {
            return 0;
        } else if (timeElapsed < PHASE_ONE_DURATION) {
            return
                ((timeElapsed - PHASE_ONE_NO_FEE_DURATION) *
                    maxWithdrawPenalty) /
                uint256(PHASE_ONE_DURATION - PHASE_ONE_NO_FEE_DURATION);
        }
        return fixedWithdrawPenalty;
    }

    function getReserves() external view returns (uint256, uint256) {
        return (wavaxReserve, tokenReserve + tokenIncentivesBalance);
    }

    function getRJoeAmount(uint256 _avaxAmount) public view returns (uint256) {
        return _avaxAmount * rJoePerAvax;
    }

    function pairBalance(address _user) public view returns (uint256) {
        UserInfo memory user = getUserInfo[_user];
        if (wavaxAllocated == 0 || user.hasWithdrawnPair) {
            return 0;
        }
        return (user.balance * lpSupply) / wavaxAllocated / 2;
    }

    function _atPhase(Phase _phase) internal view {
        if (_phase == Phase.NotStarted) {
            require(
                currentPhase() == Phase.NotStarted,
                "LaunchEvent: not in not started"
            );
        } else if (_phase == Phase.PhaseOne) {
            require(
                currentPhase() == Phase.PhaseOne,
                "LaunchEvent: not in phase one"
            );
        } else if (_phase == Phase.PhaseTwo) {
            require(
                currentPhase() == Phase.PhaseTwo,
                "LaunchEvent: not in phase two"
            );
        } else if (_phase == Phase.PhaseThree) {
            require(
                currentPhase() == Phase.PhaseThree,
                "LaunchEvent: not in phase three"
            );
        } else {
            revert("LaunchEvent: unknown state");
        }
    }

    function _safeTransferAVAX(address _to, uint256 _value) internal {
        (bool success, ) = _to.call{value: _value}(new bytes(0));
        require(success, "LaunchEvent: avax transfer failed");
    }
}
