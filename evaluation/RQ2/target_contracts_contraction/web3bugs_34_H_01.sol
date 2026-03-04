pragma solidity 0.8.6;

contract DrawCalculator is IDrawCalculator, Ownable {

    IDrawBuffer public immutable drawBuffer;

    ITicket public immutable ticket;

    IPrizeDistributionBuffer public immutable prizeDistributionBuffer;

    uint8 public constant TIERS_LENGTH = 16;

    function calculate(
        address _user,
        uint32[] calldata _drawIds,
        bytes calldata _pickIndicesForDraws
    ) external view override returns (uint256[] memory, bytes memory) {
        uint64[][] memory pickIndices = abi.decode(_pickIndicesForDraws, (uint64 [][]));
        require(pickIndices.length == _drawIds.length, "DrawCalc/invalid-pick-indices-length");

        IDrawBeacon.Draw[] memory draws = drawBuffer.getDraws(_drawIds);

        IPrizeDistributionBuffer.PrizeDistribution[] memory _prizeDistributions = prizeDistributionBuffer
            .getPrizeDistributions(_drawIds);

        uint256[] memory userBalances = _getNormalizedBalancesAt(_user, draws, _prizeDistributions);

        bytes32 _userRandomNumber = keccak256(abi.encodePacked(_user));

        return _calculatePrizesAwardable(
                userBalances,
                _userRandomNumber,
                draws,
                pickIndices,
                _prizeDistributions
            );
    }

    function getDrawBuffer() external view override returns (IDrawBuffer) {
        return drawBuffer;
    }

    function getPrizeDistributionBuffer()
        external
        view
        override
        returns (IPrizeDistributionBuffer)
    {
        return prizeDistributionBuffer;
    }

    function getNormalizedBalancesForDrawIds(address _user, uint32[] calldata _drawIds)
        external
        view
        override
        returns (uint256[] memory)
    {
        IDrawBeacon.Draw[] memory _draws = drawBuffer.getDraws(_drawIds);
        IPrizeDistributionBuffer.PrizeDistribution[] memory _prizeDistributions = prizeDistributionBuffer
            .getPrizeDistributions(_drawIds);

        return _getNormalizedBalancesAt(_user, _draws, _prizeDistributions);
    }

    function _calculatePrizesAwardable(
        uint256[] memory _normalizedUserBalances,
        bytes32 _userRandomNumber,
        IDrawBeacon.Draw[] memory _draws,
        uint64[][] memory _pickIndicesForDraws,
        IPrizeDistributionBuffer.PrizeDistribution[] memory _prizeDistributions
    ) internal pure returns (uint256[] memory prizesAwardable, bytes memory prizeCounts) {

        uint256[] memory _prizesAwardable = new uint256[](_normalizedUserBalances.length);
        uint256[][] memory _prizeCounts = new uint256[][](_normalizedUserBalances.length);

        for (uint32 drawIndex = 0; drawIndex < _draws.length; drawIndex++) {
            uint64 totalUserPicks = _calculateNumberOfUserPicks(
                _prizeDistributions[drawIndex],
                _normalizedUserBalances[drawIndex]
            );

            (_prizesAwardable[drawIndex], _prizeCounts[drawIndex]) = _calculate(
                _draws[drawIndex].winningRandomNumber,
                totalUserPicks,
                _userRandomNumber,
                _pickIndicesForDraws[drawIndex],
                _prizeDistributions[drawIndex]
            );
        }
        prizeCounts = abi.encode(_prizeCounts);
        prizesAwardable = _prizesAwardable;
    }

    function _calculateNumberOfUserPicks(
        IPrizeDistributionBuffer.PrizeDistribution memory _prizeDistribution,
        uint256 _normalizedUserBalance
    ) internal pure returns (uint64) {
        return uint64((_normalizedUserBalance * _prizeDistribution.numberOfPicks) / 1 ether);
    }

    function _getNormalizedBalancesAt(
        address _user,
        IDrawBeacon.Draw[] memory _draws,
        IPrizeDistributionBuffer.PrizeDistribution[] memory _prizeDistributions
    ) internal view returns (uint256[] memory) {
        uint64[] memory _timestampsWithStartCutoffTimes = new uint64[](_draws.length);
        uint64[] memory _timestampsWithEndCutoffTimes = new uint64[](_draws.length);

        for (uint32 i = 0; i < _draws.length; i++) {
            unchecked {
                _timestampsWithStartCutoffTimes[i] =
                    _draws[i].timestamp - _prizeDistributions[i].startTimestampOffset;
                _timestampsWithEndCutoffTimes[i] =
                    _draws[i].timestamp - _prizeDistributions[i].endTimestampOffset;
            }
        }

        uint256[] memory balances = ticket.getAverageBalancesBetween(
            _user,
            _timestampsWithStartCutoffTimes,
            _timestampsWithEndCutoffTimes
        );

        uint256[] memory totalSupplies = ticket.getAverageTotalSuppliesBetween(
            _timestampsWithStartCutoffTimes,
            _timestampsWithEndCutoffTimes
        );

        uint256[] memory normalizedBalances = new uint256[](_draws.length);

        for (uint256 i = 0; i < _draws.length; i++) {
            require(totalSupplies[i] > 0, "DrawCalc/total-supply-zero");
            normalizedBalances[i] = (balances[i] * 1 ether) / totalSupplies[i];
        }

        return normalizedBalances;
    }

    function _calculate(
        uint256 _winningRandomNumber,
        uint256 _totalUserPicks,
        bytes32 _userRandomNumber,
        uint64[] memory _picks,
        IPrizeDistributionBuffer.PrizeDistribution memory _prizeDistribution
    ) internal pure returns (uint256 prize, uint256[] memory prizeCounts) {

        uint256[] memory masks = _createBitMasks(_prizeDistribution);
        uint32 picksLength = uint32(_picks.length);
        uint256[] memory _prizeCounts = new uint256[](_prizeDistribution.tiers.length);

        uint8 maxWinningTierIndex = 0;

        require(
            picksLength <= _prizeDistribution.maxPicksPerUser,
            "DrawCalc/exceeds-max-user-picks"
        );

        for (uint32 index = 0; index < picksLength; index++) {
            require(_picks[index] < _totalUserPicks, "DrawCalc/insufficient-user-picks");

            if (index > 0) {
                require(_picks[index] > _picks[index - 1], "DrawCalc/picks-ascending");
            }

            uint256 randomNumberThisPick = uint256(
                keccak256(abi.encode(_userRandomNumber, _picks[index]))
            );

            uint8 tiersIndex = _calculateTierIndex(
                randomNumberThisPick,
                _winningRandomNumber,
                masks
            );

            if (tiersIndex < TIERS_LENGTH) {
                if (tiersIndex > maxWinningTierIndex) {
                    maxWinningTierIndex = tiersIndex;
                }
                _prizeCounts[tiersIndex]++;
            }
        }

        uint256 prizeFraction = 0;
        uint256[] memory prizeTiersFractions = _calculatePrizeTierFractions(
            _prizeDistribution,
            maxWinningTierIndex
        );

        for (
            uint256 prizeCountIndex = 0;
            prizeCountIndex <= maxWinningTierIndex;
            prizeCountIndex++
        ) {
            if (_prizeCounts[prizeCountIndex] > 0) {
                prizeFraction +=
                    prizeTiersFractions[prizeCountIndex] *
                    _prizeCounts[prizeCountIndex];
            }
        }

        prize = (prizeFraction * _prizeDistribution.prize) / 1e9;
        prizeCounts = _prizeCounts;
    }

    function _calculateTierIndex(
        uint256 _randomNumberThisPick,
        uint256 _winningRandomNumber,
        uint256[] memory _masks
    ) internal pure returns (uint8) {
        uint8 numberOfMatches = 0;
        uint8 masksLength = uint8(_masks.length);

        for (uint8 matchIndex = 0; matchIndex < masksLength; matchIndex++) {
            uint256 mask = _masks[matchIndex];

            if ((_randomNumberThisPick & mask) != (_winningRandomNumber & mask)) {
                return masksLength - numberOfMatches;
            }

            numberOfMatches++;
        }

        return masksLength - numberOfMatches;
    }

    function _createBitMasks(IPrizeDistributionBuffer.PrizeDistribution memory _prizeDistribution)
        internal
        pure
        returns (uint256[] memory)
    {
        uint256[] memory masks = new uint256[](_prizeDistribution.matchCardinality);
        uint256 _bitRangeMaskValue = (2**_prizeDistribution.bitRangeSize) - 1;

        for (uint8 maskIndex = 0; maskIndex < _prizeDistribution.matchCardinality; maskIndex++) {
            uint256 _matchIndexOffset = uint256(maskIndex) * uint256(_prizeDistribution.bitRangeSize);
            masks[maskIndex] = _bitRangeMaskValue << _matchIndexOffset;
        }

        return masks;
    }

    function _calculatePrizeTierFraction(
        IPrizeDistributionBuffer.PrizeDistribution memory _prizeDistribution,
        uint256 _prizeTierIndex
    ) internal pure returns (uint256) {
        uint256 prizeFraction = _prizeDistribution.tiers[_prizeTierIndex];

        uint256 numberOfPrizesForIndex = _numberOfPrizesForIndex(
            _prizeDistribution.bitRangeSize,
            _prizeTierIndex
        );

        return prizeFraction / numberOfPrizesForIndex;
    }

    function _calculatePrizeTierFractions(
        IPrizeDistributionBuffer.PrizeDistribution memory _prizeDistribution,
        uint8 maxWinningTierIndex
    ) internal pure returns (uint256[] memory) {
        uint256[] memory prizeDistributionFractions = new uint256[](
            maxWinningTierIndex + 1
        );

        for (uint8 i = 0; i <= maxWinningTierIndex; i++) {
            prizeDistributionFractions[i] = _calculatePrizeTierFraction(
                _prizeDistribution,
                i
            );
        }

        return prizeDistributionFractions;
    }

    function _numberOfPrizesForIndex(uint8 _bitRangeSize, uint256 _prizeTierIndex)
        internal
        pure
        returns (uint256)
    {
        uint256 bitRangeDecimal = 2**uint256(_bitRangeSize);
        uint256 numberOfPrizesForIndex = bitRangeDecimal**_prizeTierIndex;

        while (_prizeTierIndex > 0) {
            numberOfPrizesForIndex -= bitRangeDecimal**(_prizeTierIndex - 1);
            _prizeTierIndex--;
        }

        return numberOfPrizesForIndex;
    }
}
