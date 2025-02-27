    
[AloeBlend.sol]

    // @testing _earmarkSomeForMaintenance earned0 10
    // @testing 
    function _earmarkSomeForMaintenance(uint256 earned0, uint256 earned1) private returns (uint256, uint256) {
        uint256 toMaintenance;

        unchecked {
            // Accrue token0
            toMaintenance = earned0 / MAINTENANCE_FEE;
            earned0 -= toMaintenance;
            maintenanceBudget0 += toMaintenance; //@before maintenanceBudget0 < @after maintenenanceBudget0
            // Accrue token1
            toMaintenance = earned1 / MAINTENANCE_FEE;
            earned1 -= toMaintenance;
            maintenanceBudget1 += toMaintenance;
        }

        return (earned0, earned1); 
    }

    function pushRewardPerGas0(uint224 rewardPerGas0) private {
        unchecked {
            rewardPerGas0 /= 10;
            rewardPerGas0Accumulator = rewardPerGas0Accumulator + rewardPerGas0 - rewardPerGas0Array[rebalanceCount % 10];
            rewardPerGas0Array[rebalanceCount % 10] = rewardPerGas0;
        }
    }

[Amoss.sol]

    function _approve(
        address owner,
        address spender,
        uint256 amount
    ) internal virtual {
        require(owner != address(0), "ERC20: approve from the zero address");
        require(spender != address(0), "ERC20: approve to the zero address");

        _allowances[owner][spender] = amount;
        emit Approval(owner, spender, amount);
    }

    function _burn(address account, uint256 amount) internal virtual {
        require(account != address(0), "ERC20: burn from the zero address");

        _beforeTokenTransfer(account, address(0), amount);

        uint256 accountBalance = _balances[account];
        require(accountBalance >= amount, "ERC20: burn amount exceeds balance");
        unchecked {
            _balances[account] = accountBalance - amount;
        }
        _totalSupply -= amount;

        emit Transfer(account, address(0), amount);

        _afterTokenTransfer(account, address(0), amount);
    }

[AOC_BEP.sol]
    function excludedFromLTAF(address account) external onlyOwner whenNotPaused {
        require(includedInLTAF[account], "User is already excluded");
        includedInLTAF[account] = false;
        emit ExcludedFromLTAF(account);
	}

    function updateLtafPercentage(uint256 percentage) external onlyOwner whenNotPaused {
        require(percentage > 0, "Percentage must be greater than zero");
        ltafPercentage = percentage;
        emit LtafPercentageUpdated(ltafPercentage);
    }

    // @
    function updateUserInfo(address account, uint256 year, uint256 month) internal {
        userInfo[account].balance = _balances[account];
        userInfo[account].year = year;
        userInfo[account].month = month;
        for(uint256 i = 1; i <= 4; i++) {
            if(i == 4) {
                userInfo[account].level = i;
                break;
            }
            if(block.timestamp >= levels[i].start && block.timestamp <= levels[i].end) {
                userInfo[account].level = i;
                break;
            }
        }
    }

[ATIDStaking.sol]
    function _insertLockedStake(address _stakerAddress, uint _ATIDamount, uint _stakeWeight, uint _lockedUntil) internal returns (uint newLockedStakeID) {
        // Get (or init) next ID and increment.
        if (nextLockedStakeIDMap[_stakerAddress] == 0) {
            nextLockedStakeIDMap[_stakerAddress] = 1;
        }
        uint nextLockedStateID = nextLockedStakeIDMap[_stakerAddress];
        nextLockedStakeIDMap[_stakerAddress]++;

        // Create and insert the new stakes into the map.
        LockedStake memory newLockedStake = LockedStake({
            active: true,

            ID: nextLockedStateID,
            prevID: tailLockedStakeIDMap[_stakerAddress],  // Can be 0.
            nextID: 0,  // New tail.

            amount: _ATIDamount,
            lockedUntil: _lockedUntil,
            stakeWeight: _stakeWeight
        });
        lockedStakeMap[_stakerAddress][newLockedStake.ID] = newLockedStake;

        // Insert new stakes into the linked list for easier lookup of existing stakes.
        if (headLockedStakeIDMap[_stakerAddress] == 0) {
            // First element in the linked list. Set it also as head.
            headLockedStakeIDMap[_stakerAddress] = newLockedStake.ID;
        } else {
            // Connect with its previous locked stakes, and set it as the new tail.
            lockedStakeMap[_stakerAddress][newLockedStake.prevID].nextID = newLockedStake.ID;
        }
        // The inserted locked stake is the new tail.
        tailLockedStakeIDMap[_stakerAddress] = newLockedStake.ID;

        // Add the weighted stakes to total accounting.
        uint newWeightedStake = newLockedStake.amount * newLockedStake.stakeWeight;
        weightedStakes[_stakerAddress] += newWeightedStake;
        totalWeightedATIDStaked += newWeightedStake;

        emit WeightedStakeAdded(msg.sender, newLockedStake.ID, _ATIDamount, newWeightedStake, weightedStakes[_stakerAddress], _lockedUntil);
        emit TotalWeightedATIDStakedUpdated(totalWeightedATIDStaked);
        // For querying purposes, record unweighted stakes.
        unweightedStakes[_stakerAddress] += _ATIDamount;
        totalUnweightedATIDStaked += _ATIDamount;

        return newLockedStake.ID;
    }

    function _removeLockedStake(address _stakerAddress, uint _lockedStakeID) internal returns (uint atidAmountWithdrawn, uint stakeWeight) {
        require(lockedStakeMap[_stakerAddress][_lockedStakeID].active, "ATIDStaking: invalid locked stakes");
        require(lockedStakeMap[_stakerAddress][_lockedStakeID].lockedUntil < block.timestamp, "ATIDStaking: unlock timestamp not reached");

        LockedStake memory lockedStake = lockedStakeMap[_stakerAddress][_lockedStakeID];
        atidAmountWithdrawn = lockedStake.amount;
        stakeWeight = lockedStake.stakeWeight;

        // Update linked list structures.
        if (headLockedStakeIDMap[_stakerAddress] == lockedStake.ID) {
            // Is linked list head.
            headLockedStakeIDMap[_stakerAddress] = lockedStake.nextID;  // Can be 0.
        } else {
            // Not linked list head.
            lockedStakeMap[_stakerAddress][lockedStake.prevID].nextID = lockedStake.nextID;  // Can be 0.
        }
        if (tailLockedStakeIDMap[_stakerAddress] == lockedStake.ID) {
            // Is linked list tail.
            tailLockedStakeIDMap[_stakerAddress] = lockedStake.prevID;  // Can be 0.
        } else {
            // Not linked list tail.
            lockedStakeMap[_stakerAddress][lockedStake.nextID].prevID = lockedStake.prevID;  // Can be 0.
        }

        // Remove the stakes from total accounting.
        uint removedWeightedStake = lockedStake.amount * lockedStake.stakeWeight;
        weightedStakes[_stakerAddress] -= removedWeightedStake;
        totalWeightedATIDStaked -= removedWeightedStake;

        emit WeightedStakeRemoved(msg.sender, _lockedStakeID, lockedStake.amount, removedWeightedStake, weightedStakes[_stakerAddress]);
        emit TotalWeightedATIDStakedUpdated(totalWeightedATIDStaked);
        // For querying purposes, record unweighted stakes.
        unweightedStakes[_stakerAddress] -= lockedStake.amount;
        totalUnweightedATIDStaked -= lockedStake.amount;

        delete lockedStakeMap[_stakerAddress][_lockedStakeID];

        return (atidAmountWithdrawn, stakeWeight);
    }

    function _getStakeWeight(uint _lockedUntil) internal view returns (uint stakeWeight) {
        uint yearsToStake = 0;
        if (_lockedUntil > block.timestamp) {
            yearsToStake = (_lockedUntil - block.timestamp) / SECONDS_IN_ONE_YEAR;
            // Max allowed locking years timeframe is 3, last index of WEIGHT_MULTIPLIERS.
            if (yearsToStake > 3) {
                yearsToStake = 3;
            }
        }
        stakeWeight = WEIGHT_MULTIPLIERS[yearsToStake];
    }

    function _requireCallerIsVaultManager() internal view {
        require(msg.sender == vaultManagerAddress, "ATIDStaking: caller is not VaultM");
    }

    function _requireUserHasStake(uint currentStake) internal pure {  
        require(currentStake > 0, "ATIDStaking: User must have a non-zero stake");  
    }

[Balancer.sol] - 보류
    address[] public actionBuilders;
    
    function _addActionBuilderAt(address actionBuilder, uint256 index) internal {
        uint256 currentLength = actionBuilders.length;
        // expand array id needed
        if (currentLength == 0 || currentLength - 1 < index) {
            uint256 additionalCount = index - currentLength + 1;
            for (uint8 i = 0; i < additionalCount; i++) {
                actionBuilders.push();
                emit ActionBuilderUpdated(address(0), i);
            }
        }
        actionBuilders[index] = actionBuilder; 
        emit ActionBuilderUpdated(actionBuilder, index);
    }

[BaseCurveConvex4.sol]

    function updateZunamiLpInStrat(uint256 _amount, bool _isMint) external onlyZunami {
        _isMint ? (zunamiLpInStrat += _amount) :  (zunamiLpInStrat -= _amount);
    }

[CGUToken.sol]

    struct AccountLock {
        uint256 amount;
        uint256 timestamp;
    }

    mapping(address => AccountLock) public locks;

    bool private initialized;

    function getLockedAmount(address account) public view returns (uint256) {
        return locks[account].timestamp > block.timestamp ? locks[account].amount : 0;
    }

[CEther.sol]
    // underflow 같은경우에는 0.8이라 실행시간에 다 잡긴 잡는데, 가스비문제제
    function getCashPrior() override internal view returns (uint) {
        return address(this).balance - msg.value;
    }

    function doTransferIn(address from, uint amount) override internal returns (uint) {
        // Sanity checks
        require(msg.sender == from, "sender mismatch");
        require(msg.value == amount, "value mismatch");
        return amount;
    }

[Core.sol]
    /// @notice Map to track the addresses with a `GOVERNOR_ROLE` within Angle protocol
    mapping(address => bool) public governorMap;

    /// @notice Map to track the addresses of the `stableMaster` contracts that have already been deployed
    /// This is used to avoid deploying a revoked `stableMaster` contract again and hence potentially creating
    /// inconsistencies in the `GOVERNOR_ROLE` and `GUARDIAN_ROLE` of this `stableMaster`
    mapping(address => bool) public deployedStableMasterMap;

    /// @notice Address of the guardian, it can be revoked by Angle's governance
    /// The protocol has only one guardian address
    address public override guardian;

    /// @notice List of the addresses of the `StableMaster` contracts accepted by the system
    address[] internal _stablecoinList;

    // List of all the governor addresses of Angle's protocol
    // Initially only the timelock will be appointed governor but new addresses can be added along the way
    address[] internal _governorList;

    /// @notice Revokes a `StableMaster` contract
    /// @param stableMaster Address of  the `StableMaster` to revoke
    /// @dev This function just removes a `StableMaster` contract from the `_stablecoinList`
    /// @dev The consequence is that the `StableMaster` contract will no longer be affected by changes in
    /// governor or guardian occuring from the protocol
    /// @dev This function is mostly here to clean the mappings and save some storage space
    function revokeStableMaster(address stableMaster) external override onlyGovernor {
        uint256 stablecoinListLength = _stablecoinList.length;
        // Checking if `stableMaster` is correct and removing the stablecoin from the `_stablecoinList`
        require(stablecoinListLength >= 1, "45");
        uint256 indexMet;
        for (uint256 i = 0; i < stablecoinListLength - 1; i++) {
            if (_stablecoinList[i] == stableMaster) {
                indexMet = 1;
                _stablecoinList[i] = _stablecoinList[stablecoinListLength - 1];
                break;
            }
        }
        require(indexMet == 1 || _stablecoinList[stablecoinListLength - 1] == stableMaster, "45");
        _stablecoinList.pop();
        // Deleting the stablecoin from the list
        emit StableMasterRevoked(stableMaster);
    }   

[CitrusToken.sol] 
    function transfer(address _to, uint256 _amount) public returns (bool success) {
        require (balances[msg.sender]>=_amount&&_amount>0&&balances[_to]+_amount>balances[_to]);
        balances[msg.sender]-=_amount;
        balances[_to]+=_amount;
        emit Transfer(msg.sender,_to,_amount);
        return true;
    }

    function lockedAccountDetails(address user) public view returns (uint[] memory, uint[] memory, uint[] memory, uint[] memory, uint) {
        uint lockedLength = lock[user].locked.length;
        uint[] memory lockedAmounts = new uint[](lockedLength);
        uint[] memory lockTimes = new uint[](lockedLength);
        uint[] memory lockedAt = new uint[](lockedLength);
        uint[] memory totalLockTime = new uint[](lockedLength);
        uint currentTime = block.timestamp;
        
        
        for(uint i = 0; i < lockedLength; i++) {
            lockedAmounts[i] = lock[user].locked[i].amount;
            lockTimes[i] = lock[user].locked[i].time;
            lockedAt[i] = lock[user].locked[i].lockedAt;
            totalLockTime[i] = lock[user].locked[i].time + lock[user].locked[i].lockedAt;
        }
        return(lockedAmounts, lockTimes, lockedAt, totalLockTime, currentTime);
    }

[CoreVoting.sol]
    /// @notice Override of the getter for the 'quorums' mapping which returns the default
    ///         quorum when the quorum is not set.
    /// @param target the contract for which the quorum is set
    /// @param functionSelector the function which is callable
    /// @return The quorum needed to pass the function at this point in time
    function quorums(address target, bytes4 functionSelector)
        public
        view
        returns (uint256)
    {
        uint256 storedQuorum = _quorums[target][functionSelector];

        if (storedQuorum == 0) {
            return baseQuorum;
        } else {
            return storedQuorum;
        }
    }

[Dai.sol]
    function add(uint x, uint y) internal pure returns (uint z) {
        require((z = x + y) >= x);
    }

    function transfer(address dst, uint wad) external returns (bool) {
        return transferFrom(msg.sender, dst, wad);
    }

    function transferFrom(address src, address dst, uint wad)
        public returns (bool)
    {
        require(balanceOf[src] >= wad, "Dai/insufficient-balance");
        if (src != msg.sender && allowance[src][msg.sender] != uint(-1)) {
            require(allowance[src][msg.sender] >= wad, "Dai/insufficient-allowance");
            allowance[src][msg.sender] = sub(allowance[src][msg.sender], wad);
        }
        balanceOf[src] = sub(balanceOf[src], wad);
        balanceOf[dst] = add(balanceOf[dst], wad);
        emit Transfer(src, dst, wad);
        return true;
    }

[DapiServer.sol]
    /// @notice Called privately to calculate the update magnitude in
    /// percentages where 100% is represented as `HUNDRED_PERCENT`
    /// @dev The percentage changes will be more pronounced when the first
    /// value is almost zero, which may trigger updates more frequently than
    /// wanted. To avoid this, Beacons should be defined in a way that the
    /// expected values are not small numbers floating around zero, i.e.,
    /// offset and scale.
    /// @param initialValue Initial value
    /// @param updatedValue Updated value
    /// @return updateInPercentage Update in percentage
    function calculateUpdateInPercentage(
        int224 initialValue,
        int224 updatedValue
    ) private pure returns (uint256 updateInPercentage) {
        int256 delta = int256(updatedValue) - int256(initialValue);
        uint256 absoluteDelta = delta > 0 ? uint256(delta) : uint256(-delta);
        uint256 absoluteInitialValue = initialValue > 0
            ? uint256(int256(initialValue))
            : uint256(-int256(initialValue));
        // Avoid division by 0
        if (absoluteInitialValue == 0) {
            absoluteInitialValue = 1;
        }
        updateInPercentage =
            (absoluteDelta * HUNDRED_PERCENT) /
            absoluteInitialValue;
    }

[Define.sol]
    
    function updateGasForProcessing(uint256 newValue) public onlyOwner {
        require(newValue >= 200000 && newValue <= 500000, "Define: gasForProcessing must be between 200,000 and 500,000");
        require(newValue != gasForProcessing, "Define: Cannot update gasForProcessing to same value");
        emit GasForProcessingUpdated(newValue, gasForProcessing);
        gasForProcessing = newValue;
    }

[DeltaNeutralPancakeWorker02]
    
    function setReinvestConfig(
    uint256 _reinvestBountyBps,
    uint256 _reinvestThreshold,
    address[] calldata _reinvestPath
  ) external onlyOwner {
    if (_reinvestBountyBps > maxReinvestBountyBps) revert ExceedReinvestBounty();

    if (_reinvestPath.length < 2) revert InvalidReinvestPathLength();

    if (_reinvestPath[0] != cake || _reinvestPath[_reinvestPath.length - 1] != baseToken) revert InvalidReinvestPath();

    reinvestBountyBps = _reinvestBountyBps;
    reinvestThreshold = _reinvestThreshold;
    reinvestPath = _reinvestPath;
    emit SetReinvestConfig(msg.sender, _reinvestBountyBps, _reinvestThreshold, _reinvestPath);
  }

  /// @dev Set the given strategies' approval status.
  /// @param strats - The strategy addresses.
  /// @param isOk - Whether to approve or unapprove the given strategies.
  function setStrategyOk(address[] calldata strats, bool isOk) external override onlyOwner {
    uint256 len = strats.length;
    for (uint256 idx = 0; idx < len; idx++) {
      okStrats[strats[idx]] = isOk;

      emit SetStrategyOK(msg.sender, strats[idx], isOk);
    }
  }

  /// @dev Set treasury configurations.
  /// @param _treasuryAccount - The treasury address to update
  /// @param _treasuryBountyBps - The treasury bounty to update
  function setTreasuryConfig(address _treasuryAccount, uint256 _treasuryBountyBps) external onlyOwner {
    if (_treasuryBountyBps > maxReinvestBountyBps) revert ExceedReinvestBounty();

    treasuryAccount = _treasuryAccount;
    treasuryBountyBps = _treasuryBountyBps;

    emit SetTreasuryConfig(msg.sender, treasuryAccount, treasuryBountyBps);
  }

[FixedFeeSwap.sol]
    function getReturn(uint256 inputAmount) public view returns(uint256 outputAmount) {
        outputAmount = inputAmount * amountMultiplier / _FEE_SCALE;
    }

[FraxCrossChainLiquidityTracker.sol]

    uint256[] public chain_ids_array;
    mapping(uint256 => uint256) public frax_minted; // chain id -> frax minted amount
    mapping(uint256 => uint256) public fxs_minted; // chain id -> fxs minted amount
    mapping(uint256 => uint256) public collat_bridged; // chain id -> collat bridged amount

    function totalsAcrossChains() public view returns (uint256 frax_tally, uint256 fxs_tally, uint256 collat_tally) {
        for (uint256 i = 0; i < chain_ids_array.length; i++){
            uint256 chain_id = chain_ids_array[i];
            frax_tally += frax_minted[chain_id];
            fxs_tally += fxs_minted[chain_id];
            collat_tally += collat_bridged[chain_id];
        }
    }

[GovStakingStorage.sol]

    function getUserInfoByIndex(uint256 from, uint256 to)
        external
        view
        returns (UserInfo[] memory)
    {
        uint256 to_ = to > userList.length ? userList.length : to;
        UserInfo[] memory result = new UserInfo[](to - from);
        for (uint256 i = 0; i < to_ - from; i++) {
            result[i] = userInfo[userList[i + from]];
        }
        return result;
    }

[GreenHouse.sol]

    function bonusRewardPoolCountdown() public view returns(uint256) {
        // SWC-120-Weak Sources of Randomness from Chain Attributes: L209
        uint256 timeSinceLastDistributed = block.timestamp - _bonusPoolLastDistributedAt;
        if (timeSinceLastDistributed >= _bonusPoolTimer) return 0;
        return _bonusPoolTimer - timeSinceLastDistributed;
    }

    function _calculateFees(uint256 amount)
    internal pure
    returns(
        uint256 allUsers,
        uint256 bonusPool,
        uint256 partner,
        uint256 referral,
        uint256 platform,
        uint256 net
    ) {
        allUsers = (amount * FEE_ALL_USERS_STAKED_PERMILLE) / 10000;
        bonusPool = (amount * FEE_BONUS_POOL_PERMILLE) / 10000;
        partner = (amount * FEE_PARTNER_WALLET_PERMILLE) / 10000;
        referral = (amount * FEE_REFERRAL_PERMILLE) / 10000;
        platform = (amount * FEE_PLATFORM_WALLET_PERMILLE) / 10000;
        net = amount - allUsers - bonusPool - partner - referral - platform;
    }

[Lock.sol]

    struct LockedData {
        uint256 total;
        uint256 pending;
        uint256 estUnlock;
        uint256 unlockedAmounts;
    }

    mapping(address => LockedData) public data;
    uint256 public startLock;
    uint256 public unlockDuration = 30 days;
    uint256 public lockedTime = 6 * 30 days;

    function pending(address _account) public view returns(uint256 _pending) {
        LockedData memory _data = data[_account];
        uint256 _totalLockRemain =  _data.total - _data.unlockedAmounts - _data.pending;
        if (_totalLockRemain > 0) {
            if (block.timestamp >= startLock + lockedTime) {
                _pending = _totalLockRemain;
            } else {
                uint256 _nUnlock = (lockedTime - (block.timestamp - startLock) - 1) / unlockDuration + 1;
                _pending = _totalLockRemain - _data.estUnlock * _nUnlock;
            }
        }
        if (_data.pending > 0) {
            _pending += _data.pending;
        }
    }

[MockChainlinkOracle.sol]

    uint80 public roundId = 0;
    uint8 public keyDecimals = 0;

    struct Entry {
        uint80 roundId;
        int256 answer;
        uint256 startedAt;
        uint256 updatedAt;
        uint80 answeredInRound;
    }

    mapping(uint256 => Entry) public entries;

    bool public latestRoundDataShouldRevert;

    string public desc;

    function latestRoundData()
        external
        view
        override
        returns (
            uint80,
            int256,
            uint256,
            uint256,
            uint80
        )
    {
        if (latestRoundDataShouldRevert) {
            revert("latestRoundData reverted");
        }
        return getRoundData(uint80(roundId));
    }

    function getRoundData(uint80 _roundId)
        public
        view
        override
        returns (
            uint80,
            int256,
            uint256,
            uint256,
            uint80
        )
    {
        Entry memory entry = entries[_roundId];
        // Emulate a Chainlink aggregator
        require(entry.updatedAt > 0, "No data present");
        return (entry.roundId, entry.answer, entry.startedAt, entry.updatedAt, entry.answeredInRound);
    }

[PrivateSale.sol]

    struct Round {
        mapping(address => bool) whiteList;
        mapping(address => uint256) sums;
        mapping(address => address) depositToken;
        mapping(address => uint256) tokenReserve;
        uint256 totalReserve;
        uint256 tokensSold;
        uint256 tokenRate;
        uint256 maxMoney;
        uint256 sumTokens;
        uint256 minimumSaleAmount;
        uint256 maximumSaleAmount;
        uint256 startTimestamp;
        uint256 endTimestamp;
        uint256 duration;
        uint256 durationCount;
        uint256 lockup;
        TokenVestingGroup vestingContract;
        uint8 percentOnInvestorWallet;
        uint8 typeRound;
        bool finished;
        bool open;
        bool burnable;
    }

    struct InputNewRound {
        uint256 _tokenRate;
        uint256 _maxMoney;
        uint256 _sumTokens;
        uint256 _startTimestamp;
        uint256 _endTimestamp;
        uint256 _minimumSaleAmount;
        uint256 _maximumSaleAmount;
        uint256 _duration;
        uint256 _durationCount;
        uint256 _lockup;
        uint8 _typeRound;
        uint8 _percentOnInvestorWallet;
        bool _burnable;
        bool _open;
    }

    //*** Variable ***//
    mapping(uint256 => Round) rounds;
    address investorWallet;
    uint256 countRound;
    uint256 countTokens;
    mapping(uint256 => address) tokens;
    mapping(address => address) oracles;
    mapping(address => bool) tokensAdd;

    address BLID;
    address expenseAddress;

    function getLockedTokens(uint256 id) public view returns (uint256) {
        if (rounds[id].tokenRate == 0) return 0;
        return ((rounds[id].totalReserve * (1 ether)) / rounds[id].tokenRate);
    }

    /**
     * @param id Number of round
     * @return  Returns (all deposited money, sold tokens, open or close round)
     */
    function getRoundDynamicInfromation(uint256 id)
        public
        view
        returns (
            uint256,
            uint256,
            bool
        )
    {
        if (rounds[id].typeRound == 1) {
            return (rounds[id].totalReserve, rounds[id].totalReserve / rounds[id].tokenRate, rounds[id].open);
        } else {
            return (rounds[id].totalReserve, rounds[id].sumTokens, rounds[id].open);
        }
    }

[PoolKeeper.sol]

    /* Constants */
    uint256 public constant BASE_TIP = 5; // 5% base tip
    uint256 public constant TIP_DELTA_PER_BLOCK = 5; // 5% increase per block
    uint256 public constant BLOCK_TIME = 13; /* in seconds */
    uint256 public constant MAX_DECIMALS = 18;
    uint256 public constant MAX_TIP = 100; /* maximum keeper tip */

    // #### Global variables
    /**
     * @notice Format: Pool address => last executionPrice
     */
    mapping(address => int256) public executionPrice;

    IPoolFactory public factory;
    bytes16 constant fixedPoint = 0x403abc16d674ec800000000000000000; // 1 ether

    uint256 public gasPrice = 10 gwei;
    address public observer = address(0);

    function keeperTip(uint256 _savedPreviousUpdatedTimestamp, uint256 _poolInterval) public view returns (uint256) {
        /* the number of blocks that have elapsed since the given pool's updateInterval passed */
        uint256 elapsedBlocksNumerator = (block.timestamp - (_savedPreviousUpdatedTimestamp + _poolInterval));

        uint256 keeperTip = BASE_TIP + (TIP_DELTA_PER_BLOCK * elapsedBlocksNumerator) / BLOCK_TIME;

        // In case of network outages or otherwise, we want to cap the tip so that the keeper cost isn't unbounded
        if (keeperTip > MAX_TIP) {
            return MAX_TIP;
        } else {
            return keeperTip;
        }
    }

[QANX.sol]

    function unlockableBalanceOf(address account) public view virtual returns (uint256) {

        // IF THE HARDLOCK HAS NOT PASSED YET, THERE ARE NO UNLOCKABLE TOKENS
        if(block.timestamp < _locks[account].hardLockUntil) {
            return 0;
        }

        // IF THE SOFTLOCK PERIOD PASSED, ALL CURRENTLY TOKENS ARE UNLOCKABLE
        if(block.timestamp > _locks[account].softLockUntil) {
            return _locks[account].tokenAmount;
        }

        // OTHERWISE THE PROPORTIONAL AMOUNT IS UNLOCKABLE
        return (block.timestamp - _locks[account].lastUnlock) * _locks[account].unlockPerSec;
    }

    function unlock(address account) external returns (bool) {

        // CALCULATE UNLOCKABLE BALANCE
        uint256 unlockable = unlockableBalanceOf(account);

        // ONLY ADDRESSES OWNING LOCKED TOKENS AND BYPASSED HARDLOCK TIME ARE UNLOCKABLE
        require(unlockable > 0 && _locks[account].tokenAmount > 0 && block.timestamp > _locks[account].hardLockUntil, "No unlockable tokens!");

        // SET LAST UNLOCK TIME, DEDUCT FROM LOCKED BALANCE & CREDIT TO REGULAR BALANCE
        _locks[account].lastUnlock = uint32(block.timestamp);
        _locks[account].tokenAmount = _locks[account].tokenAmount - unlockable;
        _balances[account] = _balances[account] + unlockable;

        // IF NO MORE LOCKED TOKENS LEFT, REMOVE LOCK OBJECT FROM ADDRESS
        if(_locks[account].tokenAmount == 0){
            delete _locks[account];
            emit LockRemoved(account);
        }

        // UNLOCK SUCCESSFUL
        emit Transfer(account, account, unlockable);
        return true;
    }

[Staking_PSR_PAN.sol]

    /// @notice View function to see pending reward on frontend.
    /// @param _user Address of user.
    /// @return pending reward for a given user.
    function pendingReward(address _user) external view returns (uint256 pending) {
        UserInfo storage user = userInfo[_user];
        uint256 supply = PSR.balanceOf(address(this));
        uint256 _accRewardPerShare = accRewardPerShare;
        if (block.number > lastRewardBlock && supply != 0) {
            uint256 rewardAmount = (block.number - lastRewardBlock) * rewardPerBlock;
            _accRewardPerShare += (rewardAmount * ACC_REWARD_PRECISION) / supply;
        }
        pending = uint256(int256(user.amount * _accRewardPerShare / ACC_REWARD_PRECISION) - user.rewardDebt);
    }

[Vat.sol]
    function flux(bytes32 ilk, address src, address dst, uint256 wad) external note {
        require(wish(src, msg.sender), "Vat/not-allowed");
        gem[ilk][src] = sub(gem[ilk][src], wad);
        gem[ilk][dst] = add(gem[ilk][dst], wad);
    }