pragma solidity 0.7.6;
pragma abicoder v2;

contract LenderPool is ERC1155Upgradeable, ReentrancyGuardUpgradeable, IPooledCreditLineEnums, ILenderPool {
    using SafeMath for uint256;
    using SafeERC20 for IERC20;

    ISavingsAccount public immutable SAVINGS_ACCOUNT;
    IPooledCreditLine public immutable POOLED_CREDIT_LINE;
    IVerification public immutable VERIFICATION;
    uint256 constant SCALING_FACTOR = 1e18;

    struct LenderInfo {
        uint256 borrowerInterestSharesWithdrawn;
        uint256 yieldInterestWithdrawnShares;
    }

    struct LenderPoolConstants {
        uint256 startTime;
        address borrowAsset;
        address collateralAsset;
        uint256 borrowLimit;
        uint256 minBorrowAmount;
        address lenderVerifier;
        address borrowAssetStrategy;
        bool areTokensTransferable;
    }

    struct LenderPoolVariables {
        mapping(address => LenderInfo) lenders;
        uint256 sharesHeld;
        uint256 borrowerInterestShares;
        uint256 borrowerInterestSharesWithdrawn;
        uint256 yieldInterestWithdrawnShares;
        uint256 collateralHeld;
    }

    mapping(uint256 => LenderPoolConstants) public pooledCLConstants;
    mapping(uint256 => LenderPoolVariables) public pooledCLVariables;
    mapping(uint256 => uint256) public totalSupply;

    modifier onlyPooledCreditLine() {
        require(msg.sender == address(POOLED_CREDIT_LINE), 'LP:OPCL1');
        _;
    }

    event Lend(uint256 indexed id, address indexed user, uint256 amount);
    event WithdrawLiquidity(uint256 indexed id, address indexed user, uint256 shares);
    event WithdrawLiquidityOnCancel(uint256 indexed id, address indexed user, uint256 amount);
    event InterestWithdrawn(uint256 indexed id, address indexed user, uint256 shares);
    event LiquidationWithdrawn(uint256 indexed id, address indexed user, uint256 collateralShare);
    event Liquidated(uint256 indexed id, uint256 collateralLiquidated);

    function initialize() external initializer {
        ReentrancyGuardUpgradeable.__ReentrancyGuard_init();
        __ERC1155_init('URI');
    }

    function create(
        uint256 _id,
        address _lenderVerifier,
        address _borrowAsset,
        address _borrowAssetStrategy,
        uint256 _borrowLimit,
        uint256 _minBorrowAmount,
        uint256 _collectionPeriod,
        bool _areTokensTransferable
    ) external override nonReentrant onlyPooledCreditLine {
        pooledCLConstants[_id].startTime = block.timestamp.add(_collectionPeriod);
        pooledCLConstants[_id].borrowAsset = _borrowAsset;
        pooledCLConstants[_id].borrowLimit = _borrowLimit;
        pooledCLConstants[_id].minBorrowAmount = _minBorrowAmount;
        pooledCLConstants[_id].lenderVerifier = _lenderVerifier;
        pooledCLConstants[_id].borrowAssetStrategy = _borrowAssetStrategy;
        pooledCLConstants[_id].areTokensTransferable = _areTokensTransferable;

        uint256 allowance = SAVINGS_ACCOUNT.allowance(address(this), _borrowAsset, address(POOLED_CREDIT_LINE));
        if (allowance != type(uint256).max) {
            SAVINGS_ACCOUNT.approve(_borrowAsset, address(POOLED_CREDIT_LINE), type(uint256).max);
        }
    }

    function lend(uint256 _id, uint256 _amount) external nonReentrant {
        require(_amount != 0, 'LP:L1');
        require(VERIFICATION.isUser(msg.sender, pooledCLConstants[_id].lenderVerifier), 'LP:L2');
        require(block.timestamp < pooledCLConstants[_id].startTime, 'LP:L3');

        uint256 _totalLent = totalSupply[_id];
        uint256 _maxLent = pooledCLConstants[_id].borrowLimit;
        require(_maxLent > _totalLent, 'LP:L4');

        uint256 _amountToLend = _amount;
        if (_totalLent.add(_amount) > _maxLent) {
            _amountToLend = _maxLent.sub(_totalLent);
        }
        address _borrowAsset = pooledCLConstants[_id].borrowAsset;

        IERC20(_borrowAsset).safeTransferFrom(msg.sender, address(this), _amountToLend);
        _mint(msg.sender, _id, _amountToLend, '');

        emit Lend(_id, msg.sender, _amountToLend);
    }

    function start(uint256 _id) external override nonReentrant {
        uint256 _startTime = pooledCLConstants[_id].startTime;
        require(_startTime != 0, 'LP:S1');
        require(block.timestamp >= _startTime, 'LP:S2');
        require(block.timestamp < POOLED_CREDIT_LINE.getEndsAt(_id), 'LP:S3');

        uint256 _totalLent = totalSupply[_id];
        require(_totalLent >= pooledCLConstants[_id].minBorrowAmount, 'LP:S4');

        _accept(_id, _totalLent);
    }

    function _accept(uint256 _id, uint256 _amount) private {
        address _borrowAsset = pooledCLConstants[_id].borrowAsset;
        address _strategy = pooledCLConstants[_id].borrowAssetStrategy;
        IERC20(_borrowAsset).safeApprove(_strategy, _amount);
        pooledCLVariables[_id].sharesHeld = SAVINGS_ACCOUNT.deposit(_borrowAsset, _strategy, address(this), _amount);

        POOLED_CREDIT_LINE.accept(_id, _amount, msg.sender);

        pooledCLConstants[_id].borrowLimit = _amount;
        delete pooledCLConstants[_id].startTime;
        delete pooledCLConstants[_id].minBorrowAmount;
    }

    function borrowed(uint256 _id, uint256 _sharesBorrowed) external override nonReentrant onlyPooledCreditLine {
        pooledCLVariables[_id].sharesHeld = pooledCLVariables[_id].sharesHeld.sub(_sharesBorrowed);
    }

    function repaid(
        uint256 _id,
        uint256 _sharesRepaid,
        uint256 _interestShares
    ) external override nonReentrant onlyPooledCreditLine {
        pooledCLVariables[_id].sharesHeld = pooledCLVariables[_id].sharesHeld.add(_sharesRepaid);
        pooledCLVariables[_id].borrowerInterestShares = pooledCLVariables[_id].borrowerInterestShares.add(_interestShares);
    }

    function requestCancelled(uint256 _id) external override onlyPooledCreditLine {
        delete pooledCLConstants[_id].startTime;

    }

    function terminate(uint256 _id, address _to) external override nonReentrant onlyPooledCreditLine {
        address _strategy = pooledCLConstants[_id].borrowAssetStrategy;
        address _borrowAsset = pooledCLConstants[_id].borrowAsset;
        uint256 _borrowedTokens = pooledCLConstants[_id].borrowLimit;
        uint256 _notBorrowed = _borrowedTokens.sub(POOLED_CREDIT_LINE.getPrincipal(_id));
        uint256 _notBorrowedInShares = IYield(_strategy).getSharesForTokens(_notBorrowed, _borrowAsset);
        uint256 _sharesHeld = pooledCLVariables[_id].sharesHeld;
        if (_sharesHeld != 0) {
            uint256 _totalInterestInShares = _sharesHeld.sub(_notBorrowedInShares);
            uint256 _actualNotBorrowedInShares = _notBorrowedInShares.mul(totalSupply[_id]).div(_borrowedTokens);
            uint256 _totalBorrowAsset = _actualNotBorrowedInShares.add(_totalInterestInShares);
            if (_totalBorrowAsset != 0) {
                SAVINGS_ACCOUNT.withdrawShares(_borrowAsset, _strategy, _to, _totalBorrowAsset, false);
            }
        }

        uint256 _collateralHeld = pooledCLVariables[_id].collateralHeld;
        if (_collateralHeld != 0) {
            IERC20(pooledCLConstants[_id].collateralAsset).safeTransfer(_to, _collateralHeld);
        }
        delete pooledCLConstants[_id];
        delete pooledCLVariables[_id];
    }

    function withdrawInterest(uint256 _id) external nonReentrant {
        uint256 _interestSharesWithdrawn = _withdrawInterest(_id, msg.sender);
        require(_interestSharesWithdrawn != 0, 'LP:WI1');
    }

    function _withdrawInterest(uint256 _id, address _lender) private returns (uint256 _interestSharesWithdrawn) {
        address _strategy = pooledCLConstants[_id].borrowAssetStrategy;
        address _borrowAsset = pooledCLConstants[_id].borrowAsset;
        require(_strategy != address(0), 'LP:IWI1');

        uint256 _interestSharesToWithdraw = _updateInterestSharesToWithdraw(_id, _lender, _strategy, _borrowAsset);

        if (_interestSharesToWithdraw != 0) {
            pooledCLVariables[_id].sharesHeld = pooledCLVariables[_id].sharesHeld.sub(_interestSharesToWithdraw);
            SAVINGS_ACCOUNT.withdrawShares(_borrowAsset, _strategy, _lender, _interestSharesToWithdraw, false);
            emit InterestWithdrawn(_id, _lender, _interestSharesToWithdraw);
        }

        return _interestSharesToWithdraw;
    }

    function _updateInterestSharesToWithdraw(
        uint256 _id,
        address _lender,
        address _strategy,
        address _borrowAsset
    ) private returns (uint256) {
        uint256 _lenderBalance = balanceOf(_lender, _id);
        if (_lenderBalance == 0) {
            return 0;
        }

        uint256 _borrowLimit = pooledCLConstants[_id].borrowLimit;
        (uint256 _borrowerInterestSharesForLender, uint256 _yieldInterestSharesForLender) = _calculateLenderInterest(
            _id,
            _lender,
            _strategy,
            _borrowAsset,
            _lenderBalance,
            _borrowLimit
        );

        if (_borrowerInterestSharesForLender != 0) {
            pooledCLVariables[_id].lenders[_lender].borrowerInterestSharesWithdrawn = pooledCLVariables[_id]
                .lenders[_lender]
                .borrowerInterestSharesWithdrawn
                .add(_borrowerInterestSharesForLender);
            pooledCLVariables[_id].borrowerInterestSharesWithdrawn = pooledCLVariables[_id].borrowerInterestSharesWithdrawn.add(
                _borrowerInterestSharesForLender
            );
        }

        if (_yieldInterestSharesForLender != 0) {
            pooledCLVariables[_id].lenders[_lender].yieldInterestWithdrawnShares = pooledCLVariables[_id]
                .lenders[_lender]
                .yieldInterestWithdrawnShares
                .add(_yieldInterestSharesForLender);
            pooledCLVariables[_id].yieldInterestWithdrawnShares = pooledCLVariables[_id].yieldInterestWithdrawnShares.add(
                _yieldInterestSharesForLender
            );
        }

        return _yieldInterestSharesForLender.add(_borrowerInterestSharesForLender);
    }

    function getLenderInterestWithdrawable(uint256 _id, address _lender) external returns (uint256) {
        address _strategy = pooledCLConstants[_id].borrowAssetStrategy;
        address _borrowAsset = pooledCLConstants[_id].borrowAsset;
        (uint256 _borrowerInterestShares, uint256 _yieldInterestShares) = _calculateLenderInterest(
            _id,
            _lender,
            _strategy,
            _borrowAsset,
            balanceOf(_lender, _id),
            pooledCLConstants[_id].borrowLimit
        );
        return IYield(_strategy).getTokensForShares(_borrowerInterestShares.add(_yieldInterestShares), _borrowAsset);
    }

    function _calculateLenderInterest(
        uint256 _id,
        address _lender,
        address _strategy,
        address _borrowAsset,
        uint256 _lenderBalance,
        uint256 _borrowLimit
    ) private returns (uint256 _borrowerInterestSharesForLender, uint256 _yieldInterestSharesForLender) {
        uint256 _totalInterestWithdrawableInShares;
        uint256 _sharesHeld = pooledCLVariables[_id].sharesHeld;
        if (_sharesHeld == 0) {
            return (0, 0);
        }
        uint256 _notBorrowed = _borrowLimit.sub(POOLED_CREDIT_LINE.getPrincipal(_id));
        uint256 _notBorrowedInShares = IYield(_strategy).getSharesForTokens(_notBorrowed, _borrowAsset);
        _totalInterestWithdrawableInShares = _sharesHeld.sub(_notBorrowedInShares);
        uint256 _borrowerInterestShares = pooledCLVariables[_id].borrowerInterestShares;
        _borrowerInterestSharesForLender = (_borrowerInterestShares.mul(_lenderBalance).div(_borrowLimit)).sub(
            pooledCLVariables[_id].lenders[_lender].borrowerInterestSharesWithdrawn
        );

        uint256 _borrowerInterestWithdrawableInShares = _borrowerInterestShares.sub(
            pooledCLVariables[_id].borrowerInterestSharesWithdrawn
        );
        _yieldInterestSharesForLender = 0;
        if (_totalInterestWithdrawableInShares > _borrowerInterestWithdrawableInShares) {
            uint256 _totalYieldInterestShares = _totalInterestWithdrawableInShares.sub(_borrowerInterestWithdrawableInShares).add(
                pooledCLVariables[_id].yieldInterestWithdrawnShares
            );
            _yieldInterestSharesForLender = (_totalYieldInterestShares.mul(_lenderBalance).div(_borrowLimit)).sub(
                pooledCLVariables[_id].lenders[_lender].yieldInterestWithdrawnShares
            );
        }
    }

    function withdrawLiquidity(uint256 _id) external nonReentrant {
        _withdrawLiquidity(_id, false);
    }

    function _withdrawLiquidity(uint256 _id, bool _isLiquidationWithdrawn) private {
        uint256 _liquidityProvided = balanceOf(msg.sender, _id);
        require(_liquidityProvided != 0, 'LP:IWL1');

        PooledCreditLineStatus _status = POOLED_CREDIT_LINE.getStatusAndUpdate(_id);

        address _borrowAsset = pooledCLConstants[_id].borrowAsset;

        if (_status == PooledCreditLineStatus.REQUESTED) {
            if (block.timestamp >= pooledCLConstants[_id].startTime && totalSupply[_id] < pooledCLConstants[_id].minBorrowAmount) {
                POOLED_CREDIT_LINE.cancelRequestOnLowCollection(_id);
            } else if (block.timestamp >= POOLED_CREDIT_LINE.getEndsAt(_id)) {
                POOLED_CREDIT_LINE.cancelRequestOnRequestedStateAtEnd(_id);
            } else {
                revert('LP:IWL3');
            }
            _status = PooledCreditLineStatus.CANCELLED;
            delete pooledCLConstants[_id].startTime;
        }

        if (_status == PooledCreditLineStatus.CANCELLED) {

            IERC20(_borrowAsset).safeTransfer(msg.sender, _liquidityProvided);
            emit WithdrawLiquidityOnCancel(_id, msg.sender, _liquidityProvided);
        } else if (_status == PooledCreditLineStatus.CLOSED || _status == PooledCreditLineStatus.LIQUIDATED) {
            if (_status == PooledCreditLineStatus.LIQUIDATED) {
                require(_isLiquidationWithdrawn, 'LP:IWL2');
            }
            address _strategy = pooledCLConstants[_id].borrowAssetStrategy;
            uint256 _principalWithdrawable = _calculatePrincipalWithdrawable(_id, msg.sender);
            uint256 _interestSharesWithdrawable = _updateInterestSharesToWithdraw(_id, msg.sender, _strategy, _borrowAsset);
            uint256 _interestWithdrawable;
            if (_interestSharesWithdrawable != 0) {
                _interestWithdrawable = IYield(_strategy).getTokensForShares(_interestSharesWithdrawable, _borrowAsset);
                pooledCLVariables[_id].sharesHeld = pooledCLVariables[_id].sharesHeld.sub(_interestSharesWithdrawable);
            }
            uint256 _amountToWithdraw = _principalWithdrawable.add(_interestWithdrawable);
            uint256 _sharesToWithdraw = IYield(_strategy).getSharesForTokens(_amountToWithdraw, _borrowAsset);
            if (_sharesToWithdraw != 0) {
                SAVINGS_ACCOUNT.withdrawShares(_borrowAsset, _strategy, msg.sender, _sharesToWithdraw, false);
            }
            emit WithdrawLiquidity(_id, msg.sender, _sharesToWithdraw);
        } else {
            revert('LP:IWL3');
        }

        _burn(msg.sender, _id, _liquidityProvided);
    }

    function calculatePrincipalWithdrawable(uint256 _id, address _lender) external returns (uint256) {
        PooledCreditLineStatus _status = POOLED_CREDIT_LINE.getStatusAndUpdate(_id);
        if (_status == PooledCreditLineStatus.CLOSED || _status == PooledCreditLineStatus.LIQUIDATED) {
            return _calculatePrincipalWithdrawable(_id, _lender);
        } else if (
            _status == PooledCreditLineStatus.CANCELLED ||
            (_status == PooledCreditLineStatus.REQUESTED &&
                ((block.timestamp >= pooledCLConstants[_id].startTime && totalSupply[_id] < pooledCLConstants[_id].minBorrowAmount) ||
                    block.timestamp >= POOLED_CREDIT_LINE.getEndsAt(_id)))
        ) {
            return balanceOf(_lender, _id);
        } else {
            return 0;
        }
    }

    function _calculatePrincipalWithdrawable(uint256 _id, address _lender) private view returns (uint256) {
        uint256 _borrowedTokens = pooledCLConstants[_id].borrowLimit;
        uint256 _totalLiquidityWithdrawable = _borrowedTokens.sub(POOLED_CREDIT_LINE.getPrincipal(_id));
        uint256 _principalWithdrawable = _totalLiquidityWithdrawable.mul(balanceOf(_lender, _id)).div(_borrowedTokens);
        return _principalWithdrawable;
    }

    function liquidate(uint256 _id, bool _withdraw) external nonReentrant {
        uint256 _lendingShare = balanceOf(msg.sender, _id);
        require(_lendingShare != 0, 'LP:LIQ1');
        (address _collateralAsset, uint256 _collateralLiquidated) = POOLED_CREDIT_LINE.liquidate(_id);
        pooledCLConstants[_id].collateralAsset = _collateralAsset;
        pooledCLVariables[_id].collateralHeld = _collateralLiquidated;

        emit Liquidated(_id, _collateralLiquidated);

        if (_withdraw) {
            _withdrawTokensAfterLiquidation(_id, _lendingShare);
        }
    }

    function withdrawTokensAfterLiquidation(uint256 _id) external nonReentrant {
        uint256 _lendingShare = balanceOf(msg.sender, _id);
        require(_lendingShare != 0, 'LP:WLC1');
        _withdrawTokensAfterLiquidation(_id, _lendingShare);
    }

    function _withdrawTokensAfterLiquidation(uint256 _id, uint256 _balance) private {
        address _collateralAsset = pooledCLConstants[_id].collateralAsset;
        require(_collateralAsset != address(0), 'LP:IWLC1');
        uint256 _collateralLiquidated = pooledCLVariables[_id].collateralHeld;
        uint256 _currentSupply = totalSupply[_id];

        uint256 _lenderCollateralShare = _balance.mul(_collateralLiquidated).div(_currentSupply);

        if (_lenderCollateralShare != 0) {
            pooledCLVariables[_id].collateralHeld = pooledCLVariables[_id].collateralHeld.sub(_lenderCollateralShare);

            IERC20(_collateralAsset).safeTransfer(msg.sender, _lenderCollateralShare);
            emit LiquidationWithdrawn(_id, msg.sender, _lenderCollateralShare);
        }
        _withdrawLiquidity(_id, true);
    }

    function _beforeTokenTransfer(
        address,
        address from,
        address to,
        uint256[] memory ids,
        uint256[] memory amounts,
        bytes memory
    ) internal override {
        require(from != to, 'LP:IT1');
        for (uint256 i; i < ids.length; ++i) {
            uint256 id = ids[i];
            if (to != address(0)) {
                require(to != POOLED_CREDIT_LINE.getBorrowerAddress(id), 'LP:IT2');
                require(VERIFICATION.isUser(to, pooledCLConstants[id].lenderVerifier), 'LP:IT3');
            }

            uint256 amount = amounts[i];

            if (from == address(0)) {
                totalSupply[id] = totalSupply[id].add(amount);
            } else if (to == address(0)) {
                uint256 supply = totalSupply[id];
                require(supply >= amount, 'LP:IT4');
                totalSupply[id] = supply - amount;
            } else {
                require(pooledCLConstants[id].areTokensTransferable, 'LP:IT5');
            }

            if (from != address(0)) {
                _rebalanceInterestWithdrawn(id, amount, from, to);
            }
        }
    }

    function _rebalanceInterestWithdrawn(
        uint256 id,
        uint256 amount,
        address from,
        address to
    ) private {
        if (from != address(0) && to != address(0)) {
            _withdrawInterest(id, from);
            _withdrawInterest(id, to);
        }

        uint256 fromBalance = balanceOf(from, id);
        require(fromBalance != 0, 'LP:IRIW1');

        uint256 yieldInterestOnTransferAmount = pooledCLVariables[id].lenders[from].yieldInterestWithdrawnShares.mul(amount).div(
            fromBalance
        );
        uint256 borrowerInterestOnTransferAmount = pooledCLVariables[id].lenders[from].borrowerInterestSharesWithdrawn.mul(amount).div(
            fromBalance
        );

        if (borrowerInterestOnTransferAmount != 0) {
            pooledCLVariables[id].lenders[from].borrowerInterestSharesWithdrawn = pooledCLVariables[id]
                .lenders[from]
                .borrowerInterestSharesWithdrawn
                .sub(borrowerInterestOnTransferAmount);
        }

        if (yieldInterestOnTransferAmount != 0) {
            pooledCLVariables[id].lenders[from].yieldInterestWithdrawnShares = pooledCLVariables[id]
                .lenders[from]
                .yieldInterestWithdrawnShares
                .sub(yieldInterestOnTransferAmount);
        }

        if (to != address(0)) {
            if (borrowerInterestOnTransferAmount != 0) {
                pooledCLVariables[id].lenders[to].borrowerInterestSharesWithdrawn = pooledCLVariables[id]
                    .lenders[to]
                    .borrowerInterestSharesWithdrawn
                    .add(borrowerInterestOnTransferAmount);
            }
            if (yieldInterestOnTransferAmount != 0) {
                pooledCLVariables[id].lenders[to].yieldInterestWithdrawnShares = pooledCLVariables[id]
                    .lenders[to]
                    .yieldInterestWithdrawnShares
                    .add(yieldInterestOnTransferAmount);
            }
        }
    }

    function getLenderInfo(uint256 _id, address _lender) external view returns (LenderInfo memory) {
        return pooledCLVariables[_id].lenders[_lender];
    }

}
