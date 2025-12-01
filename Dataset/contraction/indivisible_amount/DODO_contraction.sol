contract DODO is Context, IERC20, Ownable {
    using SafeMath for uint256;
    using Address for address;

    event ToMarketing(uint256 bnbSent);

    event SwapAndLiquifyEnabledUpdated(bool enabled);

    event SwapAndLiquify(
        uint256 tokensSwapped,
        uint256 ethReceived,
        uint256 tokensIntoLiqudity
    );

    address deadAddress = 0x000000000000000000000000000000000000dEaD;
    string private _name = "DODO";
    string private _symbol = "DODO";
    uint8 private _decimals = 9;    
    uint256 private initialsupply = 1_000_000_000;
    uint256 private _tTotal = initialsupply * 10 ** _decimals;
    address payable private _marketingWallet;
    mapping (address => uint256) private _rOwned;
    mapping (address => uint256) private _tOwned;
    mapping(address => uint256) private buycooldown;
    mapping (address => mapping (address => uint256)) private _allowances;
    mapping (address => bool) private _isExcludedFromFee;
    mapping (address => bool) private _isExcluded;
    mapping (address => bool) private _isBlacklisted;
    address[] private _excluded;
    bool private cooldownEnabled = true;
    uint256 public cooldown = 30 seconds;
    uint256 private constant MAX = ~uint256(0);
    uint256 private _rTotal = (MAX - (MAX % _tTotal));
    uint256 private _tFeeTotal;
    uint256 public _taxFee = 0;
    uint256 private _previousTaxFee = _taxFee;
    uint256 public _liquidityFee = 0;
    uint256 private _previousLiquidityFee = _liquidityFee;
    uint256 public _marketingFee = 0;
    uint256 private _previousMarketingFee = _marketingFee;
    uint256 _sellLiquidityFee;
    uint256 _sellMarketingFee;
    uint256 _sellTaxFee;
    uint256 _buyLiquidtyFee;
    uint256 _buyMarketingFee;
    uint256 _buytaxFee;
    uint256 _transferTaxFee;
    uint256 _transferMarketingFee;
    uint256 _transferLiquidityFee;
    uint256 private maxBuyPercent = 1;
    uint256 private maxBuyDivisor = 100;
    uint256 private _maxBuyAmount = (_tTotal * maxBuyPercent) / maxBuyDivisor;
    IUniswapV2Router02 public uniswapV2Router;
    address public uniswapV2Pair;
    bool inSwapAndLiquify;
    bool public swapAndLiquifyEnabled = true;
    uint256 private numTokensSellToAddToLiquidity = _tTotal / 100; // 1%

    // Note: The following modifiers are not defined in this contract: onlyOwner

    function clearStuckBalance(uint256 amountPercentage) external onlyOwner {
        require(amountPercentage <= 100);
        uint256 amountBNB = address(this).balance;
        payable(_marketingWallet).transfer(amountBNB.mul(amountPercentage).div(100));
    }

}