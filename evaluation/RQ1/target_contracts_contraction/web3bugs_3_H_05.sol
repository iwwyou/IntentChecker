pragma solidity ^0.8.0;

interface ILending {
    function viewBorrowingYieldFP(address issuer) external view returns (uint256);
}

struct CrossMarginAccount {
    uint256 lastDepositBlock;
    address[] borrowTokens;
    mapping(address => uint256) borrowed;
    mapping(address => uint256) borrowedYieldQuotientsFP;
    address[] holdingTokens;
    mapping(address => uint256) holdings;
    mapping(address => bool) holdsToken;
}

abstract contract CrossMarginAccounts is RoleAware, PriceAware {
    uint256 public leveragePercent;
    uint256 public liquidationThresholdPercent;
    mapping(address => CrossMarginAccount) internal marginAccounts;

    function yieldTokenInPeg(
        address token,
        uint256 amount,
        mapping(address => uint256) storage yieldQuotientsFP,
        bool forceCurBlock
    ) internal returns (uint256) {
        uint256 yieldFP = ILending(lending()).viewBorrowingYieldFP(token);
        uint256 amountInToken = (amount * yieldFP) / yieldQuotientsFP[token];
        return
            PriceAware.getCurrentPriceInPeg(
                token,
                amountInToken,
                forceCurBlock
            );
    }

    function sumTokensInPeg(
        address[] storage tokens,
        mapping(address => uint256) storage amounts,
        bool forceCurBlock
    ) internal returns (uint256 totalPeg) {
        uint256 len = tokens.length;
        for (uint256 tokenId; tokenId < len; tokenId++) {
            address token = tokens[tokenId];
            totalPeg += PriceAware.getCurrentPriceInPeg(
                token,
                amounts[token],
                forceCurBlock
            );
        }
    }

    function sumTokensInPegWithYield(
        address[] storage tokens,
        mapping(address => uint256) storage amounts,
        mapping(address => uint256) storage yieldQuotientsFP,
        bool forceCurBlock
    ) internal returns (uint256 totalPeg) {
        uint256 len = tokens.length;
        for (uint256 tokenId; tokenId < len; tokenId++) {
            address token = tokens[tokenId];
            totalPeg += yieldTokenInPeg(
                token,
                amounts[token],
                yieldQuotientsFP,
                forceCurBlock
            );
        }
    }

    function loanInPeg(CrossMarginAccount storage account, bool forceCurBlock)
        internal
        returns (uint256)
    {
        return
            sumTokensInPegWithYield(
                account.borrowTokens,
                account.borrowed,
                account.borrowedYieldQuotientsFP,
                forceCurBlock
            );
    }

    function holdingsInPeg(
        CrossMarginAccount storage account,
        bool forceCurBlock
    ) internal returns (uint256) {
        return
            sumTokensInPeg(
                account.holdingTokens,
                account.holdings,
                forceCurBlock
            );
    }

    function belowMaintenanceThreshold(CrossMarginAccount storage account)
        internal
        returns (bool)
    {
        uint256 loan = loanInPeg(account, true);
        uint256 holdings = holdingsInPeg(account, true);
        // The following should hold:
        // holdings / loan >= 1.1
        // => holdings >= loan * 1.1
        return 100 * holdings >= liquidationThresholdPercent * loan;
    }
}
