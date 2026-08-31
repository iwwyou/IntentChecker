pragma solidity ^0.6.12;

struct TokenLoanParams {
    uint128 valuation;
    uint64 duration;
    uint16 annualInterestBPS;
    uint16 ltvBPS;
    INFTOracle oracle;
}

contract NFTPairWithOracle {
    using BoringMath for uint256;

    event LogLend(address indexed lender, uint256 indexed tokenId);

    IBentoBoxV1 public immutable bentoBox;
    IERC20 public asset;

    uint256 public feesEarnedShare;

    mapping(uint256 => TokenLoanParams) public tokenLoanParams;

    uint8 private constant LOAN_INITIAL = 0;
    uint8 private constant LOAN_REQUESTED = 1;
    uint8 private constant LOAN_OUTSTANDING = 2;
    struct TokenLoan {
        address borrower;
        address lender;
        uint64 startTime;
        uint8 status;
    }
    mapping(uint256 => TokenLoan) public tokenLoan;

    uint256 private constant PROTOCOL_FEE_BPS = 1000;
    uint256 private constant OPEN_FEE_BPS = 100;
    uint256 private constant BPS = 10_000;

    constructor(IBentoBoxV1 bentoBox_) public {
        bentoBox = bentoBox_;
    }

    function _lend(
        address lender,
        uint256 tokenId,
        TokenLoanParams memory accepted,
        bool skim
    ) internal {
        TokenLoan memory loan = tokenLoan[tokenId];
        require(loan.status == LOAN_REQUESTED, "NFTPair: not available");
        TokenLoanParams memory params = tokenLoanParams[tokenId];

        require(
            params.valuation == accepted.valuation &&
                params.duration <= accepted.duration &&
                params.annualInterestBPS >= accepted.annualInterestBPS &&
                params.ltvBPS >= accepted.ltvBPS,
            "NFTPair: bad params"
        );

        if (params.oracle != INFTOracle(0)) {
            (, uint256 rate) = params.oracle.get(address(this), tokenId);
            require(rate.mul(uint256(params.ltvBPS)) / BPS >= params.valuation, "Oracle: price too low.");
        }

        uint256 totalShare = bentoBox.toShare(asset, params.valuation, false);
        uint256 openFeeShare = (totalShare * OPEN_FEE_BPS) / BPS;
        uint256 protocolFeeShare = (openFeeShare * PROTOCOL_FEE_BPS) / BPS;

        if (skim) {
            require(
                bentoBox.balanceOf(asset, address(this)) >= (totalShare - openFeeShare + protocolFeeShare + feesEarnedShare),
                "NFTPair: skim too much"
            );
        } else {
            bentoBox.transfer(asset, lender, address(this), totalShare - openFeeShare + protocolFeeShare);
        }
        uint256 borrowerShare = totalShare - openFeeShare;
        bentoBox.transfer(asset, address(this), loan.borrower, borrowerShare);
        feesEarnedShare += protocolFeeShare;

        loan.lender = lender;
        loan.status = LOAN_OUTSTANDING;
        loan.startTime = uint64(block.timestamp);
        tokenLoan[tokenId] = loan;

        emit LogLend(lender, tokenId);
    }
}
