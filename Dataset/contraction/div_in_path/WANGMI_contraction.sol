contract WANGMI {
    using SafeMath for uint256;

    address public constant DEAD_ADDRESS = address(0xdead);
    IUniswapV2Router02 public constant uniswapV2Router = IUniswapV2Router02(0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D);
    uint256 public buyLiquidityFee = 3;
    uint256 public sellLiquidityFee = 3;
    uint256 public buyTxFee = 9;
    uint256 public sellTxFee = 9;
    uint256 public tokensForLiquidity;
    uint256 public tokensForTax;
    uint256 public _tTotal = 10**9 * 10**9;                         // 1 billion
    uint256 public swapAtAmount = _tTotal.mul(10).div(10000);       // 0.10% of total supply
    uint256 public maxTxLimit = _tTotal.mul(75).div(10000);         // 0.75% of total supply
    uint256 public maxWalletLimit = _tTotal.mul(150).div(10000);    // 1.50% of total supply
    address public dev;
    address public deployer;
    address public uniswapV2Pair;
    uint256 private launchBlock;
    bool private swapping;
    bool public isLaunched;
    mapping (address => bool) public isExcludedFromFees;
    mapping (address => bool) public isExcludedFromTxLimit;
    mapping (address => bool) public isExcludedFromWalletLimit;
    mapping (address => bool) public isBlacklisted;

    function swapBack(uint256 totalTokensForFee) private {
        uint256 toSwap = swapAtAmount;
   
        uint256 liquidityTokens = toSwap.mul(tokensForLiquidity).div(totalTokensForFee).div(2);
        uint256 taxTokens = toSwap.sub(liquidityTokens).sub(liquidityTokens);
        uint256 amountToSwapForETH = toSwap.sub(liquidityTokens);

        _swapTokensForETH(amountToSwapForETH);

        uint256 ethBalance = address(this).balance;
        uint256 ethForTax = ethBalance.mul(taxTokens).div(amountToSwapForETH);
        uint256 ethForLiquidity = ethBalance.sub(ethForTax);

        tokensForLiquidity = tokensForLiquidity.sub(liquidityTokens.mul(2));
        tokensForTax = tokensForTax.sub(toSwap.sub(liquidityTokens.mul(2)));

        payable(address(dev)).transfer(ethForTax);
        _addLiquidity(liquidityTokens, ethForLiquidity);
    }

    function _addLiquidity(uint256 tokenAmount, uint256 ethAmount) private {

        uniswapV2Router.addLiquidityETH{value: ethAmount}(
            address(this),
            tokenAmount,
            0,
            0,
            deployer,
            block.timestamp
        );
    }

    function _swapTokensForETH(uint256 tokenAmount) private {

        address[] memory path = new address[](2);
        path[0] = address(this);
        path[1] = uniswapV2Router.WETH();

        uniswapV2Router.swapExactTokensForETHSupportingFeeOnTransferTokens(
            tokenAmount,
            0,
            path,
            address(this),
            block.timestamp
        );
    }

    function _setBlacklist(address account, bool value) internal {
        isBlacklisted[account] = value;
    }

    function _transfer(address from, address to, uint256 amount) internal override {
        require(from != address(0), "transfer from the zero address");
        require(to != address(0), "transfer to the zero address");
        require(amount <= maxTxLimit || isExcludedFromTxLimit[from] || isExcludedFromTxLimit[to], "Tx Amount too large");
        require(balanceOf(to).add(amount) <= maxWalletLimit || isExcludedFromWalletLimit[to], "Transfer will exceed wallet limit");
        require(isLaunched || isExcludedFromFees[from] || isExcludedFromFees[to], "Waiting to go live");
        require(!isBlacklisted[from], "Sender is blacklisted");

        if(amount == 0) {
            super._transfer(from, to, 0);
            return;
        }

        uint256 totalTokensForFee = tokensForLiquidity + tokensForTax;
        bool canSwap = totalTokensForFee >= swapAtAmount;

        if(
            from != uniswapV2Pair &&
            canSwap &&
            !swapping
        ) {
            swapping = true;
            swapBack(totalTokensForFee);
            swapping = false;
        } else if(
            from == uniswapV2Pair &&
            to != uniswapV2Pair &&
            block.number < launchBlock + 2 &&
            !isExcludedFromFees[to]
        ) {
            _setBlacklist(to, true);
        }

        bool takeFee = !swapping;

        if(isExcludedFromFees[from] || isExcludedFromFees[to]) {
            takeFee = false;
        }

        if(takeFee) {
            uint256 fees;
           
            if (to == uniswapV2Pair) {
                uint256 sellTotalFees = sellLiquidityFee.add(sellTxFee);
                fees = amount.mul(sellTotalFees).div(100);
                tokensForLiquidity = tokensForLiquidity.add(fees.mul(sellLiquidityFee).div(sellTotalFees));
                tokensForTax = tokensForTax.add(fees.mul(sellTxFee).div(sellTotalFees));
            }          
            else {
                uint256 buyTotalFees = buyLiquidityFee.add(buyTxFee);
                fees = amount.mul(buyTotalFees).div(100);
                tokensForLiquidity = tokensForLiquidity.add(fees.mul(buyLiquidityFee).div(buyTotalFees));
                tokensForTax = tokensForTax.add(fees.mul(buyTxFee).div(buyTotalFees));
            }

            if(fees > 0){
                super._transfer(from, address(this), fees);
                amount = amount.sub(fees);
            }
        }

        super._transfer(from, to, amount);
    }
}