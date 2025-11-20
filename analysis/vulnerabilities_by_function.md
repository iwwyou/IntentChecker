# Vulnerabilities Mapped to Functions (Solidity 0.8+)

## Summary

- Total contracts with vulnerabilities: 11

## 04e5e1a11f92be3560bf58a76723e6fe4dc09abd_DODO.solDODO (04e5e1a11f92be3560bf58a76723e6fe4dc09abd_DODO.sol)

### Function: `clearStuckBalance`

#### indivisible_amount

- Line 1054: `payable(_marketingWallet).transfer(amountBNB.mul(amountPercentage)`
- Line 1054: `payable(_marketingWallet).transfer(amountBNB.mul(amountPercentage).div(100)`
- Line 1054: `payable(_marketingWallet).transfer(amountBNB.mul(amountPercentage).div(100))`

## 05fc938cc60fb71381514877d66478bab7e2e1ce_SUPERCATS.solSUPERCATS (05fc938cc60fb71381514877d66478bab7e2e1ce_SUPERCATS.sol)

### Function: `clearStuckBalance`

#### indivisible_amount

- Line 457: `payable(msg.sender).transfer(amountToClear)`

## 122ad2495b1af2a14c5c4b4ca59adfcd79c2dcb3_GameTime.solGameTime (122ad2495b1af2a14c5c4b4ca59adfcd79c2dcb3_GameTime.sol)

### Function: `_transfer`

#### div_in_path

- Line 272: `_transferTaxes(from, to, amount, 0)`
- Line 272: `_transferTaxes(from, to, amount, 0)`
- Line 272: `_transferTaxes(from, to, amount, 0)`

### Function: `_transferTaxes`

#### div_in_path

- Line 303: `if(pit > 0) _update(from, address(0), pit)`
- Line 304: `_update(from, address(this), tax)`
- Line 316: `if(total <= 0) break`
- Line 304: `_update(from, address(this), tax)`
- Line 318: `if(total > 0) _taxes[direction].tokens[_taxes[direction].percent.length - 1] += total`

### Function: `_update`

#### div_in_path

- Line 259: `emit Transfer(from, to, amount)`
- Line 259: `emit Transfer(from, to, amount)`

### Function: `transferFrom`

#### div_in_path

- Line 197: `_transfer(from, to, amount)`
- Line 197: `_transfer(from, to, amount)`
- Line 197: `_transfer(from, to, amount)`

## 38195c86c5a32af913f05ba2c82e4c07fdeb2427_eKISHU.soleKISHU (38195c86c5a32af913f05ba2c82e4c07fdeb2427_eKISHU.sol)

### Function: `manualsend`

#### indivisible_amount

- Line 411: `require(_msgSender()`
- Line 413: `sendETHToFee(contractETHBalance)`
- Line 411: `require(_msgSender()`
- Line 413: `sendETHToFee(contractETHBalance)`

### Function: `sendETHToFee`

#### indivisible_amount

- Line 346: `_FeeAddress.transfer(amount.div(2)`
- Line 346: `_FeeAddress.transfer(amount.div(2))`
- Line 346: `_FeeAddress.transfer(amount.div(2)`
- Line 347: `_marketingWalletAddress.transfer(amount.div(2)`
- Line 347: `_marketingWalletAddress.transfer(amount.div(2))`

## 47e661f80a5fecb42137c97ecd910e2436f3ccad_Shibbit.solShibbit (47e661f80a5fecb42137c97ecd910e2436f3ccad_Shibbit.sol)

### Function: `manualsend`

#### indivisible_amount

- Line 438: `require(_msgSender()`
- Line 440: `sendETHToFee(contractETHBalance)`
- Line 438: `require(_msgSender()`
- Line 440: `sendETHToFee(contractETHBalance)`
- Line 438: `require(_msgSender()`
- Line 438: `require(_msgSender() == _developmentAddress || _msgSender()`
- Line 440: `sendETHToFee(contractETHBalance)`
- Line 438: `require(_msgSender()`
- Line 438: `require(_msgSender() == _developmentAddress || _msgSender()`
- Line 440: `sendETHToFee(contractETHBalance)`

### Function: `sendETHToFee`

#### indivisible_amount

- Line 423: `_developmentAddress.transfer(amount.div(2)`
- Line 423: `_developmentAddress.transfer(amount.div(2))`
- Line 423: `_developmentAddress.transfer(amount.div(2)`
- Line 424: `_marketingAddress.transfer(amount.div(2)`
- Line 424: `_marketingAddress.transfer(amount.div(2))`
- Line 423: `_developmentAddress.transfer(amount.div(2)`
- Line 423: `_developmentAddress.transfer(amount.div(2))`
- Line 423: `_developmentAddress.transfer(amount.div(2)`
- Line 424: `_marketingAddress.transfer(amount.div(2)`
- Line 424: `_marketingAddress.transfer(amount.div(2))`

## 63278489e04Cd2224DAa4e425E57282135db7Af3_Konnichiwa.solKonnichiwa (63278489e04Cd2224DAa4e425E57282135db7Af3_Konnichiwa.sol)

### Function: `manualsend`

#### indivisible_amount

- Line 421: `require(_msgSender()`
- Line 423: `sendETHToFee(contractETHBalance)`
- Line 421: `require(_msgSender()`
- Line 423: `sendETHToFee(contractETHBalance)`
- Line 421: `require(_msgSender()`
- Line 421: `require(_msgSender() == _developmentAddress || _msgSender()`
- Line 423: `sendETHToFee(contractETHBalance)`
- Line 421: `require(_msgSender()`
- Line 421: `require(_msgSender() == _developmentAddress || _msgSender()`
- Line 423: `sendETHToFee(contractETHBalance)`

### Function: `sendETHToFee`

#### indivisible_amount

- Line 406: `_marketingAddress.transfer(amount.mul(3)`
- Line 406: `_marketingAddress.transfer(amount.mul(3).div(5)`
- Line 406: `_marketingAddress.transfer(amount.mul(3).div(5))`
- Line 406: `_marketingAddress.transfer(amount.mul(3)`
- Line 406: `_marketingAddress.transfer(amount.mul(3).div(5)`
- Line 407: `_developmentAddress.transfer(amount.mul(2)`
- Line 407: `_developmentAddress.transfer(amount.mul(2).div(5)`
- Line 407: `_developmentAddress.transfer(amount.mul(2).div(5))`
- Line 406: `_marketingAddress.transfer(amount.mul(3)`
- Line 406: `_marketingAddress.transfer(amount.mul(3).div(5)`
- Line 406: `_marketingAddress.transfer(amount.mul(3).div(5))`
- Line 406: `_marketingAddress.transfer(amount.mul(3)`
- Line 406: `_marketingAddress.transfer(amount.mul(3).div(5)`
- Line 407: `_developmentAddress.transfer(amount.mul(2)`
- Line 407: `_developmentAddress.transfer(amount.mul(2).div(5)`
- Line 407: `_developmentAddress.transfer(amount.mul(2).div(5))`

## 638a3d66e4a6a6db13fae6050b36f7067ccaacf9_FusionSSJ2.solFusionSSJ2 (638a3d66e4a6a6db13fae6050b36f7067ccaacf9_FusionSSJ2.sol)

### Function: `manualsend`

#### indivisible_amount

- Line 365: `require(_msgSender()`
- Line 367: `sendETHToFee(contractETHBalance)`
- Line 365: `require(_msgSender()`
- Line 367: `sendETHToFee(contractETHBalance)`

### Function: `sendETHToFee`

#### indivisible_amount

- Line 304: `_feeAddrWallet1.transfer(amount.div(2)`
- Line 304: `_feeAddrWallet1.transfer(amount.div(2))`
- Line 304: `_feeAddrWallet1.transfer(amount.div(2)`
- Line 305: `_feeAddrWallet2.transfer(amount.div(2)`
- Line 305: `_feeAddrWallet2.transfer(amount.div(2))`

## 6Fb259f21359E740e6a96Be095f81212A80e831e_DICKEY.solDICKEY (6Fb259f21359E740e6a96Be095f81212A80e831e_DICKEY.sol)

### Function: `manualsend`

#### indivisible_amount

- Line 455: `require(_msgSender()`
- Line 457: `sendETHToFee(contractETHBalance)`
- Line 455: `require(_msgSender()`
- Line 457: `sendETHToFee(contractETHBalance)`
- Line 455: `require(_msgSender()`
- Line 455: `require(_msgSender() == developmentAddress || _msgSender()`
- Line 457: `sendETHToFee(contractETHBalance)`
- Line 455: `require(_msgSender()`
- Line 455: `require(_msgSender() == developmentAddress || _msgSender()`
- Line 457: `sendETHToFee(contractETHBalance)`

### Function: `sendETHToFee`

#### indivisible_amount

- Line 438: `uint256 marketingShare = distributionEth.mul(distribution.marketing)`
- Line 438: `uint256 marketingShare = distributionEth.mul(distribution.marketing).div(100)`
- Line 439: `uint256 developmentShare = distributionEth.mul(distribution.development)`
- Line 439: `uint256 developmentShare = distributionEth.mul(distribution.development).div(100)`
- Line 440: `payable(marketingAddress).transfer(marketingShare)`
- Line 438: `uint256 marketingShare = distributionEth.mul(distribution.marketing)`
- Line 438: `uint256 marketingShare = distributionEth.mul(distribution.marketing).div(100)`
- Line 439: `uint256 developmentShare = distributionEth.mul(distribution.development)`
- Line 439: `uint256 developmentShare = distributionEth.mul(distribution.development).div(100)`
- Line 441: `payable(developmentAddress).transfer(developmentShare)`
- Line 438: `uint256 marketingShare = distributionEth.mul(distribution.marketing)`
- Line 438: `uint256 marketingShare = distributionEth.mul(distribution.marketing).div(100)`
- Line 439: `uint256 developmentShare = distributionEth.mul(distribution.development)`
- Line 439: `uint256 developmentShare = distributionEth.mul(distribution.development).div(100)`
- Line 440: `payable(marketingAddress).transfer(marketingShare)`
- Line 438: `uint256 marketingShare = distributionEth.mul(distribution.marketing)`
- Line 438: `uint256 marketingShare = distributionEth.mul(distribution.marketing).div(100)`
- Line 439: `uint256 developmentShare = distributionEth.mul(distribution.development)`
- Line 439: `uint256 developmentShare = distributionEth.mul(distribution.development).div(100)`
- Line 441: `payable(developmentAddress).transfer(developmentShare)`

## 9BAcb4E17328d11b334dA6d48BEC3EC55CEC0858_dAvInci.soldAvInci (9BAcb4E17328d11b334dA6d48BEC3EC55CEC0858_dAvInci.sol)

### Function: `approve`

#### div_in_path

- Line 394: `from != owner()`

## af83df4264395f7082639db543cdbca3cc9a477c_TheVerdyctResurgence.solTheVerdyctResurgence (af83df4264395f7082639db543cdbca3cc9a477c_TheVerdyctResurgence.sol)

### Function: `withdraw`

#### indivisible_amount

- Line 1527: `payable(_wallet1).transfer(_payable1)`
- Line 1532: `payable(_wallet2).transfer(_payable2)`

## bc40fad0b36faeb1595aa90d4136d01c08c99092_AINU.solAINU (bc40fad0b36faeb1595aa90d4136d01c08c99092_AINU.sol)

### Function: `_transferFrom`

#### div_in_path

- Line 180: `uint256 _taxAmount = _calculateTax(sender, recipient, amount)`
- Line 183: `if ( _taxAmount > 0 ) { _balances[address(this)] = _balances[address(this)] + _taxAmount; }`
- Line 179: `if ( sender != address(this) && recipient != address(this) && sender != _owner ) { require(_checkLimits(sender, recipient, amount)`
- Line 180: `uint256 _taxAmount = _calculateTax(sender, recipient, amount)`
- Line 183: `if ( _taxAmount > 0 ) { _balances[address(this)] = _balances[address(this)] + _taxAmount; }`
- Line 177: `if ( !_inTaxSwap && _isLP[recipient] ) { _swapTaxAndLiquify()`
- Line 180: `uint256 _taxAmount = _calculateTax(sender, recipient, amount)`
- Line 183: `if ( _taxAmount > 0 ) { _balances[address(this)] = _balances[address(this)] + _taxAmount; }`

### Function: `name`

#### div_in_path

- Line 137: `return _transferFrom(sender, recipient, amount)`
- Line 137: `return _transferFrom(sender, recipient, amount)`
- Line 137: `return _transferFrom(sender, recipient, amount)`
- Line 292: `uint256 _taxTokensAvailable = balanceOf(address(this))`

### Function: `symbol`

#### div_in_path

- Line 133: `require(_checkTradingOpen(sender)`
- Line 133: `require(_checkTradingOpen(sender)`
- Line 133: `require(_checkTradingOpen(sender)`

