pragma solidity 0.6.12;

library SwapUtils {
    using SafeERC20 for IERC20;
    using SafeMath for uint256;
    using MathUtils for uint256;

    event TokenSwap(
        address indexed buyer,
        uint256 tokensSold,
        uint256 tokensBought,
        uint128 soldId,
        uint128 boughtId
    );
    event AddLiquidity(
        address indexed provider,
        uint256[] tokenAmounts,
        uint256[] fees,
        uint256 invariant,
        uint256 lpTokenSupply
    );
    event RemoveLiquidity(
        address indexed provider,
        uint256[] tokenAmounts,
        uint256 lpTokenSupply
    );
    event RemoveLiquidityOne(
        address indexed provider,
        uint256 lpTokenAmount,
        uint256 lpTokenSupply,
        uint256 boughtId,
        uint256 tokensBought
    );
    event RemoveLiquidityImbalance(
        address indexed provider,
        uint256[] tokenAmounts,
        uint256[] fees,
        uint256 invariant,
        uint256 lpTokenSupply
    );
    event NewAdminFee(uint256 newAdminFee);
    event NewSwapFee(uint256 newSwapFee);
    event NewWithdrawFee(uint256 newWithdrawFee);
    event RampTargetPrice(
        uint256 oldTargetPrice,
        uint256 newTargetPrice,
        uint256 initialTime,
        uint256 futureTime
    );
    event RampA(
        uint256 oldA,
        uint256 newA,
        uint256 initialTime,
        uint256 futureTime
    );
    event RampA2(
        uint256 oldA2,
        uint256 newA2,
        uint256 initialA2Time,
        uint256 futureA2Time
    );
    event StopRampTargetPrice(uint256 currentTargetPrice, uint256 time);
    event StopRampA(uint256 currentA, uint256 time);
    event StopRampA2(uint256 currentA2, uint256 time);

    struct Swap {
        uint256 initialA;
        uint256 futureA;
        uint256 initialATime;
        uint256 futureATime;
        uint256 initialA2;
        uint256 futureA2;
        uint256 initialA2Time;
        uint256 futureA2Time;
        uint256 swapFee;
        uint256 adminFee;
        uint256 defaultWithdrawFee;
        LPToken lpToken;
        IERC20[] pooledTokens;
        uint256[] tokenPrecisionMultipliers;
        uint256[] balances;
        mapping(address => uint256) depositTimestamp;
        mapping(address => uint256) withdrawFeeMultiplier;
    }

    struct TargetPrice {
        uint256 initialTargetPrice;
        uint256 futureTargetPrice;
        uint256 initialTargetPriceTime;
        uint256 futureTargetPriceTime;

        uint256[2] originalPrecisionMultipliers;
    }

    struct CalculateWithdrawOneTokenDYInfo {
        uint256 d0;
        uint256 d1;
        uint256 newY;
        uint256 feePerToken;
        uint256 preciseA;
    }

    struct AddLiquidityInfo {
        uint256 d0;
        uint256 d1;
        uint256 d2;
        uint256 preciseA;
    }

    struct RemoveLiquidityImbalanceInfo {
        uint256 d0;
        uint256 d1;
        uint256 d2;
        uint256 preciseA;
    }

    uint256 private constant WEI_UNIT = 10**18;

    uint8 public constant POOL_PRECISION_DECIMALS = 18;

    uint256 private constant FEE_DENOMINATOR = 10**10;

    uint256 public constant MAX_SWAP_FEE = 10**8;

    uint256 public constant MAX_ADMIN_FEE = 10**10;

    uint256 public constant MAX_WITHDRAW_FEE = 10**8;

    uint256 private constant MAX_LOOP_LIMIT = 256;

    uint256 public constant TARGET_PRICE_PRECISION = 1;
    uint256 public constant A_PRECISION = 100;
    uint256 public constant MAX_A = 10**6;
    uint256 private constant MAX_A_CHANGE = 2;
    uint256 private constant MAX_RELATIVE_PRICE_CHANGE = 10**16;
    uint256 private constant MIN_RAMP_TIME = 14 days;

    function getA(Swap storage self) external view returns (uint256) {
        return _getA(self);
    }

    function _getA(Swap storage self) internal view returns (uint256) {
        return _getAPrecise(self).div(A_PRECISION);
    }

    function getAPrecise(Swap storage self) external view returns (uint256) {
        return _getAPrecise(self);
    }

    function _getAPrecise(Swap storage self) internal view returns (uint256) {
        uint256 t1 = self.futureATime;
        uint256 a1 = self.futureA;

        if (block.timestamp < t1) {
            uint256 t0 = self.initialATime;
            uint256 a0 = self.initialA;
            if (a1 > a0) {
                return
                    a0.add(
                        a1.sub(a0).mul(block.timestamp.sub(t0)).div(t1.sub(t0))
                    );
            } else {
                return
                    a0.sub(
                        a0.sub(a1).mul(block.timestamp.sub(t0)).div(t1.sub(t0))
                    );
            }
        } else {
            return a1;
        }
    }

    function _getTargetPricePrecise(TargetPrice storage self) internal view returns (uint256) {
        uint256 t1 = self.futureTargetPriceTime;
        uint256 a1 = self.futureTargetPrice;
        uint256 newTargetPrice;

        if (block.timestamp < t1) {
            uint256 t0 = self.initialTargetPriceTime;
            uint256 a0 = self.initialTargetPrice;
            if (a1 > a0) {
                newTargetPrice = a0.add(
                        a1.sub(a0).mul(block.timestamp.sub(t0)).div(t1.sub(t0))
                    );
            } else {
                newTargetPrice = a0.sub(
                        a0.sub(a1).mul(block.timestamp.sub(t0)).div(t1.sub(t0))
                    );
            }

        } else {
            newTargetPrice = a1;
        }

        return newTargetPrice;
    }

    function getA2(Swap storage self) external view returns (uint256) {
        return _getA2(self);
    }

    function _getA2(Swap storage self) internal view returns (uint256) {
        return _getA2Precise(self).div(A_PRECISION);
    }

    function getA2Precise(Swap storage self) external view returns (uint256) {
        return _getA2Precise(self);
    }

    function _getA2Precise(Swap storage self) internal view returns (uint256) {
        uint256 t1 = self.futureA2Time;
        uint256 a1 = self.futureA2;

        if (block.timestamp < t1) {
            uint256 t0 = self.initialA2Time;
            uint256 a0 = self.initialA2;
            if (a1 > a0) {
                return
                    a0.add(
                        a1.sub(a0).mul(block.timestamp.sub(t0)).div(t1.sub(t0))
                    );
            } else {
                return
                    a0.sub(
                        a0.sub(a1).mul(block.timestamp.sub(t0)).div(t1.sub(t0))
                    );
            }
        } else {
            return a1;
        }
    }

    function getDepositTimestamp(Swap storage self, address user)
        external
        view
        returns (uint256)
    {
        return self.depositTimestamp[user];
    }

    function calculateWithdrawOneToken(
        Swap storage self,
        address account,
        uint256 tokenAmount,
        uint8 tokenIndex
    ) public view returns (uint256, uint256) {
        uint256 dy;
        uint256 newY;

        (dy, newY) = calculateWithdrawOneTokenDY(self, tokenIndex, tokenAmount);

        uint256 dySwapFee =
            _xp(self)[tokenIndex]
                .sub(newY)
                .div(self.tokenPrecisionMultipliers[tokenIndex])
                .sub(dy);

        dy = dy
            .mul(
            FEE_DENOMINATOR.sub(calculateCurrentWithdrawFee(self, account))
        )
            .div(FEE_DENOMINATOR);

        return (dy, dySwapFee);
    }

    function calculateWithdrawOneTokenDY(
        Swap storage self,
        uint8 tokenIndex,
        uint256 tokenAmount
    ) internal view returns (uint256, uint256) {
        require(
            tokenIndex < self.pooledTokens.length,
            "Token index out of range"
        );

        uint256[] memory xp = _xp(self);
        CalculateWithdrawOneTokenDYInfo memory v =
            CalculateWithdrawOneTokenDYInfo(0, 0, 0, 0, 0);
        v.preciseA = determineA(self, xp);
        v.d0 = getD(xp, v.preciseA);
        v.d1 = v.d0.sub(tokenAmount.mul(v.d0).div(self.lpToken.totalSupply()));

        require(tokenAmount <= xp[tokenIndex], "Withdraw exceeds available");

        v.newY = getYDC(self, v.preciseA, tokenIndex, xp, v.d1);

        uint256[] memory xpReduced = new uint256[](xp.length);

        v.feePerToken = _feePerToken(self);
        for (uint256 i = 0; i < self.pooledTokens.length; i++) {
            uint256 xpi = xp[i];
            xpReduced[i] = xpi.sub(
                (
                    (i == tokenIndex)
                        ? xpi.mul(v.d1).div(v.d0).sub(v.newY)
                        : xpi.sub(xpi.mul(v.d1).div(v.d0))
                )
                    .mul(v.feePerToken)
                    .div(FEE_DENOMINATOR)
            );
        }

        uint256 dy =
            xpReduced[tokenIndex].sub(
                getYDC(self, determineA(self, xpReduced), tokenIndex, xpReduced, v.d1)
            );
        dy = dy.sub(1).div(self.tokenPrecisionMultipliers[tokenIndex]);

        return (dy, v.newY);
    }

    function getYDC(
        Swap storage self,
        uint256 a,
        uint8 tokenIndex,
        uint256[] memory xp,
        uint256 d
    ) internal view returns (uint256) {
        uint256 numTokens = xp.length;
        require(tokenIndex < numTokens, "Token not found");

        uint256 y = getYD(a, tokenIndex, xp, d);

        uint256 aNew = _xpCalc(self, 1-tokenIndex, tokenIndex, xp[1-tokenIndex], y);

        if (aNew == a){
            return y;
        } else {
            return getYD(aNew, tokenIndex, xp, d);
        }

    }

    function getYD(
        uint256 a,
        uint8 tokenIndex,
        uint256[] memory xp,
        uint256 d
    ) internal pure returns (uint256) {
        uint256 numTokens = xp.length;
        require(tokenIndex < numTokens, "Token not found");

        uint256 c = d;
        uint256 s;
        uint256 nA = a.mul(numTokens);

        for (uint256 i = 0; i < numTokens; i++) {
            if (i != tokenIndex) {
                s = s.add(xp[i]);
                c = c.mul(d).div(xp[i].mul(numTokens));
            }
        }
        c = c.mul(d).mul(A_PRECISION).div(nA.mul(numTokens));

        uint256 b = s.add(d.mul(A_PRECISION).div(nA));
        uint256 yPrev;
        uint256 y = d;
        for (uint256 i = 0; i < MAX_LOOP_LIMIT; i++) {
            yPrev = y;
            y = y.mul(y).add(c).div(y.mul(2).add(b).sub(d));
            if (y.within1(yPrev)) {
                return y;
            }
        }
        revert("Approximation did not converge");
    }

    function getD(uint256[] memory xp, uint256 a)
        internal
        pure
        returns (uint256)
    {
        uint256 numTokens = xp.length;
        uint256 s;
        for (uint256 i = 0; i < numTokens; i++) {
            s = s.add(xp[i]);
        }
        if (s == 0) {
            return 0;
        }

        uint256 prevD;
        uint256 d = s;
        uint256 nA = a.mul(numTokens);

        for (uint256 i = 0; i < MAX_LOOP_LIMIT; i++) {
            uint256 dP = d;
            for (uint256 j = 0; j < numTokens; j++) {
                dP = dP.mul(d).div(xp[j].mul(numTokens));
            }
            prevD = d;

            d = nA.mul(s).div(A_PRECISION).add(dP.mul(numTokens)).mul(d).div(
                nA.mul(d).div(A_PRECISION).add(
                    numTokens.add(1).mul(dP)).sub(d)
            );
            if (d.within1(prevD)) {
                return d;
            }
        }

        revert("D does not converge");
    }

    function getD(Swap storage self) internal view returns (uint256) {
        uint256 a = determineA(self, _xp(self));
        return getD(_xp(self), a);
    }

    function _xp(
        uint256[] memory balances,
        uint256[] memory precisionMultipliers
    ) internal pure returns (uint256[] memory) {
        uint256 numTokens = balances.length;
        require(
            numTokens == precisionMultipliers.length,
            "Balances must match multipliers"
        );
        uint256[] memory xp = new uint256[](numTokens);
        for (uint256 i = 0; i < numTokens; i++) {
            xp[i] = balances[i].mul(precisionMultipliers[i]);
        }
        return xp;
    }

    function _xp(Swap storage self, uint256[] memory balances)
        internal
        view
        returns (uint256[] memory)
    {
        return _xp(balances, self.tokenPrecisionMultipliers);
    }

    function _xp(Swap storage self) internal view returns (uint256[] memory) {
        return _xp(self.balances, self.tokenPrecisionMultipliers);
    }

    function determineA(
        Swap storage self,
        uint256[] memory xp)
        internal
        view
        returns(uint256)
    {
        if( xp[0] < xp[1] ) {
            return _getAPrecise(self);
        } else {
            return _getA2Precise(self);
        }
    }

    function getVirtualPrice(Swap storage self)
        external
        view
        returns (uint256)
    {
        uint256 a = determineA(self, _xp(self));

        uint256 d = getD(_xp(self), a);
        uint256 supply = self.lpToken.totalSupply();
        if (supply > 0) {
            return
                d.mul(10**uint256(ERC20(self.lpToken).decimals())).div(supply);
        }
        return 0;
    }

    function getYC(
        Swap storage self,
        uint8 tokenIndexFrom,
        uint8 tokenIndexTo,
        uint256 x,
        uint256[] memory xp
    ) internal view returns (uint256) {
        uint256 numTokens = self.pooledTokens.length;
        require(
            tokenIndexFrom != tokenIndexTo,
            "Can't compare token to itself"
        );
        require(
            tokenIndexFrom < numTokens && tokenIndexTo < numTokens,
            "Tokens must be in pool"
        );

        uint256 a = determineA(self, xp);

        uint256 d = getD(xp, a);

        uint256 y = getY(self, tokenIndexFrom, tokenIndexTo, x, xp, a, d);

        uint256 aNew = _xpCalc(self, tokenIndexFrom, tokenIndexTo, x, y);

        if (aNew == a){
            return y;
        } else {
            return getY(self, tokenIndexFrom, tokenIndexTo, x, xp, aNew, d);
        }

    }

    function _xpCalc(
        Swap storage self,
        uint8 tokenIndexFrom,
        uint8 tokenIndexTo,
        uint256 x,
        uint256 y
        ) internal view returns (uint256)
    {
        uint256 xpNew0;
        uint256 xpNew1;

        if( tokenIndexFrom == 0 && tokenIndexTo == 1) {
            xpNew0 = x;
            xpNew1 = y;
        }
        else if( tokenIndexFrom == 1 && tokenIndexTo == 0) {
            xpNew0 = y;
            xpNew1 = x;
        }

        if (xpNew0 < xpNew1) {
            return _getAPrecise(self);
        } else {
            return _getA2Precise(self);
        }
    }

    function getY(
        Swap storage self,
        uint8 tokenIndexFrom,
        uint8 tokenIndexTo,
        uint256 x,
        uint256[] memory xp,
        uint256 a,
        uint256 d
    ) internal view returns (uint256) {
        uint256 numTokens = self.pooledTokens.length;
        require(
            tokenIndexFrom != tokenIndexTo,
            "Can't compare token to itself"
        );
        require(
            tokenIndexFrom < numTokens && tokenIndexTo < numTokens,
            "Tokens must be in pool"
        );

        uint256 c = d;
        uint256 s;
        uint256 nA = numTokens.mul(a);

        uint256 _x;
        for (uint256 i = 0; i < numTokens; i++) {
            if (i == tokenIndexFrom) {
                _x = x;
            } else if (i != tokenIndexTo) {
                _x = xp[i];
            } else {
                continue;
            }
            s = s.add(_x);
            c = c.mul(d).div(_x.mul(numTokens));
        }
        c = c.mul(d).mul(A_PRECISION).div(nA.mul(numTokens));
        uint256 b = s.add(d.mul(A_PRECISION).div(nA));
        uint256 yPrev;
        uint256 y = d;

        for (uint256 i = 0; i < MAX_LOOP_LIMIT; i++) {
            yPrev = y;
            y = y.mul(y).add(c).div(y.mul(2).add(b).sub(d));
            if (y.within1(yPrev)) {
                return y;
            }
        }
        revert("Approximation did not converge");
    }

    function calculateSwap(
        Swap storage self,
        uint8 tokenIndexFrom,
        uint8 tokenIndexTo,
        uint256 dx
    ) external view returns (uint256 dy) {
        (dy, ) = _calculateSwap(self, tokenIndexFrom, tokenIndexTo, dx);
    }

    function _calculateSwap(
        Swap storage self,
        uint8 tokenIndexFrom,
        uint8 tokenIndexTo,
        uint256 dx
    ) internal view returns (uint256 dy, uint256 dyFee) {
        uint256[] memory xp = _xp(self);
        require(
            tokenIndexFrom < xp.length && tokenIndexTo < xp.length,
            "Token index out of range"
        );
        uint256 x =
            dx.mul(self.tokenPrecisionMultipliers[tokenIndexFrom]).add(
                xp[tokenIndexFrom]
            );
        uint256 y = getYC(self, tokenIndexFrom, tokenIndexTo, x, xp);
        dy = xp[tokenIndexTo].sub(y).sub(1);
        dyFee = dy.mul(self.swapFee).div(FEE_DENOMINATOR);
        dy = dy.sub(dyFee).div(self.tokenPrecisionMultipliers[tokenIndexTo]);
    }

    function calculateRemoveLiquidity(
        Swap storage self,
        address account,
        uint256 amount
    ) external view returns (uint256[] memory) {
        return _calculateRemoveLiquidity(self, account, amount);
    }

    function _calculateRemoveLiquidity(
        Swap storage self,
        address account,
        uint256 amount
    ) internal view returns (uint256[] memory) {
        uint256 totalSupply = self.lpToken.totalSupply();
        require(amount <= totalSupply, "Cannot exceed total supply");

        uint256 feeAdjustedAmount =
            amount
                .mul(
                FEE_DENOMINATOR.sub(calculateCurrentWithdrawFee(self, account))
            )
                .div(FEE_DENOMINATOR);

        uint256[] memory amounts = new uint256[](self.pooledTokens.length);

        for (uint256 i = 0; i < self.pooledTokens.length; i++) {
            amounts[i] = self.balances[i].mul(feeAdjustedAmount).div(
                totalSupply
            );
        }
        return amounts;
    }

    function calculateCurrentWithdrawFee(Swap storage self, address user)
        public
        view
        returns (uint256)
    {
        uint256 endTime = self.depositTimestamp[user].add(4 weeks);
        if (endTime > block.timestamp) {
            uint256 timeLeftover = endTime.sub(block.timestamp);
            return
                self
                    .defaultWithdrawFee
                    .mul(self.withdrawFeeMultiplier[user])
                    .mul(timeLeftover)
                    .div(4 weeks)
                    .div(FEE_DENOMINATOR);
        }
        return 0;
    }

    function calculateTokenAmount(
        Swap storage self,
        address account,
        uint256[] calldata amounts,
        bool deposit
    ) external view returns (uint256) {
        uint256 numTokens = self.pooledTokens.length;
        uint256 d0 = getD(_xp(self, self.balances), determineA(self, _xp(self, self.balances)));
        uint256[] memory balances1 = self.balances;
        for (uint256 i = 0; i < numTokens; i++) {
            if (deposit) {
                balances1[i] = balances1[i].add(amounts[i]);
            } else {
                balances1[i] = balances1[i].sub(
                    amounts[i],
                    "Cannot withdraw more than available"
                );
            }
        }
        uint256 d1 = getD(_xp(self, balances1), determineA(self, _xp(self, balances1)));
        uint256 totalSupply = self.lpToken.totalSupply();

        if (deposit) {
            return d1.sub(d0).mul(totalSupply).div(d0);
        } else {
            return
                d0.sub(d1).mul(totalSupply).div(d0).mul(FEE_DENOMINATOR).div(
                    FEE_DENOMINATOR.sub(
                        calculateCurrentWithdrawFee(self, account)
                    )
                );
        }
    }

    function getAdminBalance(Swap storage self, uint256 index)
        external
        view
        returns (uint256)
    {
        require(index < self.pooledTokens.length, "Token index out of range");
        return
            self.pooledTokens[index].balanceOf(address(this)).sub(
                self.balances[index]
            );
    }

    function _feePerToken(Swap storage self) internal view returns (uint256) {
        return
            self.swapFee.mul(self.pooledTokens.length).div(
                self.pooledTokens.length.sub(1).mul(4)
            );
    }

    function swap(
        Swap storage self,
        uint8 tokenIndexFrom,
        uint8 tokenIndexTo,
        uint256 dx,
        uint256 minDy
    ) external returns (uint256) {
        require(
            dx <= self.pooledTokens[tokenIndexFrom].balanceOf(msg.sender),
            "Cannot swap more than you own"
        );

        uint256 beforeBalance =
            self.pooledTokens[tokenIndexFrom].balanceOf(address(this));
        self.pooledTokens[tokenIndexFrom].safeTransferFrom(
            msg.sender,
            address(this),
            dx
        );

        uint256 transferredDx =
            self.pooledTokens[tokenIndexFrom].balanceOf(address(this)).sub(
                beforeBalance
            );

        (uint256 dy, uint256 dyFee) =
            _calculateSwap(self, tokenIndexFrom, tokenIndexTo, transferredDx);
        require(dy >= minDy, "Swap didn't result in min tokens");

        uint256 dyAdminFee =
            dyFee.mul(self.adminFee).div(FEE_DENOMINATOR).div(
                self.tokenPrecisionMultipliers[tokenIndexTo]
            );

        self.balances[tokenIndexFrom] = self.balances[tokenIndexFrom].add(
            transferredDx
        );
        self.balances[tokenIndexTo] = self.balances[tokenIndexTo].sub(dy).sub(
            dyAdminFee
        );

        self.pooledTokens[tokenIndexTo].safeTransfer(msg.sender, dy);

        emit TokenSwap(
            msg.sender,
            transferredDx,
            dy,
            tokenIndexFrom,
            tokenIndexTo
        );

        return dy;
    }

    function addLiquidity(
        Swap storage self,
        uint256[] memory amounts,
        uint256 minToMint
    ) external returns (uint256) {
        require(
            amounts.length == self.pooledTokens.length,
            "Amounts must match pooled tokens"
        );

        uint256[] memory fees = new uint256[](self.pooledTokens.length);

        AddLiquidityInfo memory v = AddLiquidityInfo(0, 0, 0, 0);

        if (self.lpToken.totalSupply() != 0) {
            v.d0 = getD(self);
        }

        uint256[] memory newBalances = self.balances;

        for (uint256 i = 0; i < self.pooledTokens.length; i++) {
            require(
                self.lpToken.totalSupply() != 0 || amounts[i] > 0,
                "Must supply all tokens in pool"
            );

            if (amounts[i] != 0) {
                uint256 beforeBalance =
                    self.pooledTokens[i].balanceOf(address(this));
                self.pooledTokens[i].safeTransferFrom(
                    msg.sender,
                    address(this),
                    amounts[i]
                );

                amounts[i] = self.pooledTokens[i].balanceOf(address(this)).sub(
                    beforeBalance
                );
            }

            newBalances[i] = self.balances[i].add(amounts[i]);
        }

        v.preciseA = determineA(self, _xp(self, newBalances));
        v.d1 = getD(_xp(self, newBalances), v.preciseA);
        require(v.d1 > v.d0, "D should increase");

        v.d2 = v.d1;
        if (self.lpToken.totalSupply() != 0) {
            uint256 feePerToken = _feePerToken(self);
            for (uint256 i = 0; i < self.pooledTokens.length; i++) {
                uint256 idealBalance = v.d1.mul(self.balances[i]).div(v.d0);
                fees[i] = feePerToken
                    .mul(idealBalance.difference(newBalances[i]))
                    .div(FEE_DENOMINATOR);
                self.balances[i] = newBalances[i].sub(
                    fees[i].mul(self.adminFee).div(FEE_DENOMINATOR)
                );
                newBalances[i] = newBalances[i].sub(fees[i]);
            }
            v.d2 = getD(_xp(self, newBalances), determineA(self, _xp(self, newBalances)));
        } else {
            self.balances = newBalances;
        }

        uint256 toMint;
        if (self.lpToken.totalSupply() == 0) {
            toMint = v.d1;
        } else {
            toMint = v.d2.sub(v.d0).mul(self.lpToken.totalSupply()).div(v.d0);
        }

        require(toMint >= minToMint, "Couldn't mint min requested");

        self.lpToken.mint(msg.sender, toMint);

        emit AddLiquidity(
            msg.sender,
            amounts,
            fees,
            v.d1,
            self.lpToken.totalSupply()
        );

        return toMint;
    }

    function updateUserWithdrawFee(
        Swap storage self,
        address user,
        uint256 toMint
    ) external {
        _updateUserWithdrawFee(self, user, toMint);
    }

    function _updateUserWithdrawFee(
        Swap storage self,
        address user,
        uint256 toMint
    ) internal {
        if (user == address(0)) {
            return;
        }
        if (self.defaultWithdrawFee == 0) {
            self.withdrawFeeMultiplier[user] = FEE_DENOMINATOR;
        } else {
            uint256 currentFee = calculateCurrentWithdrawFee(self, user);
            uint256 currentBalance = self.lpToken.balanceOf(user);

            self.withdrawFeeMultiplier[user] = currentBalance
                .mul(currentFee)
                .add(toMint.mul(self.defaultWithdrawFee))
                .mul(FEE_DENOMINATOR)
                .div(toMint.add(currentBalance).mul(self.defaultWithdrawFee));
        }
        self.depositTimestamp[user] = block.timestamp;
    }

    function removeLiquidity(
        Swap storage self,
        uint256 amount,
        uint256[] calldata minAmounts
    ) external returns (uint256[] memory) {
        require(amount <= self.lpToken.balanceOf(msg.sender), ">LP.balanceOf");
        require(
            minAmounts.length == self.pooledTokens.length,
            "minAmounts must match poolTokens"
        );

        uint256[] memory amounts =
            _calculateRemoveLiquidity(self, msg.sender, amount);

        for (uint256 i = 0; i < amounts.length; i++) {
            require(amounts[i] >= minAmounts[i], "amounts[i] < minAmounts[i]");
            self.balances[i] = self.balances[i].sub(amounts[i]);
            self.pooledTokens[i].safeTransfer(msg.sender, amounts[i]);
        }

        self.lpToken.burnFrom(msg.sender, amount);

        emit RemoveLiquidity(msg.sender, amounts, self.lpToken.totalSupply());

        return amounts;
    }

    function removeLiquidityOneToken(
        Swap storage self,
        uint256 tokenAmount,
        uint8 tokenIndex,
        uint256 minAmount
    ) external returns (uint256) {
        uint256 totalSupply = self.lpToken.totalSupply();
        uint256 numTokens = self.pooledTokens.length;
        require(
            tokenAmount <= self.lpToken.balanceOf(msg.sender),
            ">LP.balanceOf"
        );
        require(tokenIndex < numTokens, "Token not found");

        uint256 dyFee;
        uint256 dy;

        (dy, dyFee) = calculateWithdrawOneToken(
            self,
            msg.sender,
            tokenAmount,
            tokenIndex
        );

        require(dy >= minAmount, "dy < minAmount");

        self.balances[tokenIndex] = self.balances[tokenIndex].sub(
            dy.add(dyFee.mul(self.adminFee).div(FEE_DENOMINATOR))
        );
        self.lpToken.burnFrom(msg.sender, tokenAmount);
        self.pooledTokens[tokenIndex].safeTransfer(msg.sender, dy);

        emit RemoveLiquidityOne(
            msg.sender,
            tokenAmount,
            totalSupply,
            tokenIndex,
            dy
        );

        return dy;
    }

    function removeLiquidityImbalance(
        Swap storage self,
        uint256[] memory amounts,
        uint256 maxBurnAmount
    ) public returns (uint256) {
        require(
            amounts.length == self.pooledTokens.length,
            "Amounts should match pool tokens"
        );
        require(
            maxBurnAmount <= self.lpToken.balanceOf(msg.sender) &&
                maxBurnAmount != 0,
            ">LP.balanceOf"
        );

        RemoveLiquidityImbalanceInfo memory v =
            RemoveLiquidityImbalanceInfo(0, 0, 0, 0);

        uint256 tokenSupply = self.lpToken.totalSupply();
        uint256 feePerToken = _feePerToken(self);

        uint256[] memory balances1 = self.balances;

        v.preciseA = determineA(self, _xp(self));
        v.d0 = getD(_xp(self), v.preciseA);
        for (uint256 i = 0; i < self.pooledTokens.length; i++) {
            balances1[i] = balances1[i].sub(
                amounts[i],
                "Cannot withdraw more than available"
            );
        }
        v.d1 = getD(_xp(self, balances1), determineA(self, _xp(self, balances1)));
        uint256[] memory fees = new uint256[](self.pooledTokens.length);

        for (uint256 i = 0; i < self.pooledTokens.length; i++) {
            uint256 idealBalance = v.d1.mul(self.balances[i]).div(v.d0);
            uint256 difference = idealBalance.difference(balances1[i]);
            fees[i] = feePerToken.mul(difference).div(FEE_DENOMINATOR);
            self.balances[i] = balances1[i].sub(
                fees[i].mul(self.adminFee).div(FEE_DENOMINATOR)
            );
            balances1[i] = balances1[i].sub(fees[i]);
        }

        v.d2 = getD(_xp(self, balances1), determineA(self, _xp(self, balances1)));

        uint256 tokenAmount = v.d0.sub(v.d2).mul(tokenSupply).div(v.d0);
        require(tokenAmount != 0, "Burnt amount cannot be zero");
        tokenAmount = tokenAmount.add(1).mul(FEE_DENOMINATOR).div(
            FEE_DENOMINATOR.sub(calculateCurrentWithdrawFee(self, msg.sender))
        );

        require(tokenAmount <= maxBurnAmount, "tokenAmount > maxBurnAmount");

        self.lpToken.burnFrom(msg.sender, tokenAmount);

        for (uint256 i = 0; i < self.pooledTokens.length; i++) {
            self.pooledTokens[i].safeTransfer(msg.sender, amounts[i]);
        }

        emit RemoveLiquidityImbalance(
            msg.sender,
            amounts,
            fees,
            v.d1,
            tokenSupply.sub(tokenAmount)
        );

        return tokenAmount;
    }

    function withdrawAdminFees(Swap storage self, address to) external {
        for (uint256 i = 0; i < self.pooledTokens.length; i++) {
            IERC20 token = self.pooledTokens[i];
            uint256 balance =
                token.balanceOf(address(this)).sub(self.balances[i]);
            if (balance != 0) {
                token.safeTransfer(to, balance);
            }
        }
    }

    function setAdminFee(Swap storage self, uint256 newAdminFee) external {
        require(newAdminFee <= MAX_ADMIN_FEE, "Fee is too high");
        self.adminFee = newAdminFee;

        emit NewAdminFee(newAdminFee);
    }

    function setSwapFee(Swap storage self, uint256 newSwapFee) external {
        require(newSwapFee <= MAX_SWAP_FEE, "Fee is too high");
        self.swapFee = newSwapFee;

        emit NewSwapFee(newSwapFee);
    }

    function setDefaultWithdrawFee(Swap storage self, uint256 newWithdrawFee)
        external
    {
        require(newWithdrawFee <= MAX_WITHDRAW_FEE, "Fee is too high");
        self.defaultWithdrawFee = newWithdrawFee;

        emit NewWithdrawFee(newWithdrawFee);
    }

    function rampTargetPrice(
        TargetPrice storage self,
        uint256 futureTargetPrice_,
        uint256 futureTime_
    ) external returns (uint256) {
        require(
            block.timestamp >= self.initialTargetPriceTime.add(1 days),
            "Wait 1 day before starting ramp"
        );
        require(
            futureTime_ >= block.timestamp.add(MIN_RAMP_TIME),
            "Insufficient ramp time"
        );
        require(
            futureTargetPrice_ >= 0,
            "futureTargetPrice_ must be >= 0"
        );

        uint256 initialTargetPricePrecise = _getTargetPricePrecise(self);
        uint256 futureTargetPricePrecise = futureTargetPrice_.mul(TARGET_PRICE_PRECISION);

        if (futureTargetPricePrecise < initialTargetPricePrecise) {
            require(
                futureTargetPricePrecise.mul(MAX_RELATIVE_PRICE_CHANGE).div(WEI_UNIT) >= initialTargetPricePrecise,
                "futureTargetPrice_ is too small"
            );
        } else {
            require(
                futureTargetPricePrecise <= initialTargetPricePrecise.mul(MAX_RELATIVE_PRICE_CHANGE).div(WEI_UNIT),
                "futureTargetPrice_ is too large"
            );
        }

        self.initialTargetPrice = initialTargetPricePrecise;
        self.futureTargetPrice = futureTargetPricePrecise;
        self.initialTargetPriceTime = block.timestamp;
        self.futureTargetPriceTime = futureTime_;

        emit RampTargetPrice(
            initialTargetPricePrecise,
            futureTargetPricePrecise,
            block.timestamp,
            futureTime_
        );

        return self.originalPrecisionMultipliers[0].mul(initialTargetPricePrecise).div(WEI_UNIT);
    }

    function rampA(
        Swap storage self,
        uint256 futureA_,
        uint256 futureTime_
    ) external {
        require(
            block.timestamp >= self.initialATime.add(1 days),
            "Wait 1 day before starting ramp"
        );
        require(
            futureTime_ >= block.timestamp.add(MIN_RAMP_TIME),
            "Insufficient ramp time"
        );
        require(
            futureA_ >= 0 && futureA_ <= MAX_A,
            "futureA_ must be >= 0 and <= MAX_A"
        );

        uint256 initialAPrecise = _getAPrecise(self);
        uint256 futureAPrecise = futureA_.mul(A_PRECISION);

        if (futureAPrecise < initialAPrecise) {
            require(
                futureAPrecise.mul(MAX_A_CHANGE) >= initialAPrecise,
                "futureA_ is too small"
            );
        } else {
            require(
                futureAPrecise <= initialAPrecise.mul(MAX_A_CHANGE),
                "futureA_ is too large"
            );
        }

        self.initialA = initialAPrecise;
        self.futureA = futureAPrecise;
        self.initialATime = block.timestamp;
        self.futureATime = futureTime_;

        emit RampA(
            initialAPrecise,
            futureAPrecise,
            block.timestamp,
            futureTime_
        );
    }

    function rampA2(
        Swap storage self,
        uint256 futureA2_,
        uint256 futureTime_
    ) external {
        require(
            block.timestamp >= self.initialA2Time.add(1 days),
            "Wait 1 day before starting ramp"
        );
        require(
            futureTime_ >= block.timestamp.add(MIN_RAMP_TIME),
            "Insufficient ramp time"
        );
        require(
            futureA2_ >= 0 && futureA2_ <= MAX_A,
            "futureA2_ must be >= 0 and <= MAX_A"
        );

        uint256 initialA2Precise = _getA2Precise(self);
        uint256 futureA2Precise = futureA2_.mul(A_PRECISION);

        if (futureA2Precise < initialA2Precise) {
            require(
                futureA2Precise.mul(MAX_A_CHANGE) >= initialA2Precise,
                "futureA2_ is too small"
            );
        } else {
            require(
                futureA2Precise <= initialA2Precise.mul(MAX_A_CHANGE),
                "futureA2_ is too large"
            );
        }

        self.initialA2 = initialA2Precise;
        self.futureA2 = futureA2Precise;
        self.initialA2Time = block.timestamp;
        self.futureA2Time = futureTime_;

        emit RampA2(
            initialA2Precise,
            futureA2Precise,
            block.timestamp,
            futureTime_
        );
    }

    function stopRampTargetPrice(TargetPrice storage self) external returns (uint256) {
        require(self.futureTargetPriceTime > block.timestamp, "Ramp is already stopped");
        uint256 currentTargetPrice = _getTargetPricePrecise(self);

        self.initialTargetPrice = currentTargetPrice;
        self.futureTargetPrice = currentTargetPrice;
        self.initialTargetPriceTime = block.timestamp;
        self.futureTargetPriceTime = block.timestamp;

        emit StopRampTargetPrice(currentTargetPrice, block.timestamp);

        return self.originalPrecisionMultipliers[0].mul(currentTargetPrice).div(WEI_UNIT);
    }

    function stopRampA(Swap storage self) external {
        require(self.futureATime > block.timestamp, "Ramp is already stopped");
        uint256 currentA = _getAPrecise(self);

        self.initialA = currentA;
        self.futureA = currentA;
        self.initialATime = block.timestamp;
        self.futureATime = block.timestamp;

        emit StopRampA(currentA, block.timestamp);
    }

    function stopRampA2(Swap storage self) external {
        require(self.futureA2Time > block.timestamp, "Ramp is already stopped");
        uint256 currentA2 = _getA2Precise(self);

        self.initialA2 = currentA2;
        self.futureA2 = currentA2;
        self.initialA2Time = block.timestamp;
        self.futureA2Time = block.timestamp;

        emit StopRampA2(currentA2, block.timestamp);
    }
}
