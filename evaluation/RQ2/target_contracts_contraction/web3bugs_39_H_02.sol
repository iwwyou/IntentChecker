pragma solidity 0.8.4;

contract Swivel {
  mapping (bytes32 => bool) public cancelled;
  mapping (bytes32 => uint256) public filled;
  mapping (address => uint256) public withdrawals;

  string constant public NAME = 'Swivel Finance';
  string constant public VERSION = '2.0.0';
  uint256 constant public HOLD = 259200;
  bytes32 public immutable domain;
  address public immutable marketPlace;
  address public immutable admin;
  uint16[] public fenominator;

  event Cancel (bytes32 indexed key, bytes32 hash);
  event Initiate(bytes32 indexed key, bytes32 hash, address indexed maker, bool vault, bool exit, address indexed sender, uint256 amount, uint256 filled);
  event Exit(bytes32 indexed key, bytes32 hash, address indexed maker, bool vault, bool exit, address indexed sender, uint256 amount, uint256 filled);
  event WithdrawalScheduled (address indexed token, uint256 hold);

  function initiate(Hash.Order[] calldata o, uint256[] calldata a, Sig.Components[] calldata c) external returns (bool) {
    for (uint256 i=0; i < o.length; i++) {
      if (!o[i].exit) {
        if (!o[i].vault) {
          initiateVaultFillingZcTokenInitiate(o[i], a[i], c[i]);
        } else {
          initiateZcTokenFillingVaultInitiate(o[i], a[i], c[i]);
        }
      } else {
        if (!o[i].vault) {
          initiateZcTokenFillingZcTokenExit(o[i], a[i], c[i]);
        } else {
          initiateVaultFillingVaultExit(o[i], a[i], c[i]);
        }
      }
    }

    return true;
  }

  function initiateVaultFillingZcTokenInitiate(Hash.Order calldata o, uint256 a, Sig.Components calldata c) internal {
    bytes32 hash = validOrderHash(o, c);

    require(a <= (o.premium - filled[hash]), 'taker amount > available volume');

    filled[hash] += a;

    uint256 principalFilled = (((a * 1e18) / o.premium) * o.principal) / 1e18;
    uint256 fee = ((principalFilled * 1e18) / fenominator[2]) / 1e18;

    Erc20 uToken = Erc20(o.underlying);
    uToken.transferFrom(msg.sender, o.maker, a);
    uToken.transferFrom(o.maker, address(this), principalFilled);

    MarketPlace mPlace = MarketPlace(marketPlace);
    address cTokenAddr = mPlace.cTokenAddress(o.underlying, o.maturity);
    uToken.approve(cTokenAddr, principalFilled);
    require(CErc20(cTokenAddr).mint(principalFilled) == 0, 'minting CToken failed');

    require(mPlace.custodialInitiate(o.underlying, o.maturity, o.maker, msg.sender, principalFilled), 'custodial initiate failed');

    require(mPlace.transferVaultNotionalFee(o.underlying, o.maturity, msg.sender, fee), "notional fee transfer failed");

    emit Initiate(o.key, hash, o.maker, o.vault, o.exit, msg.sender, a, principalFilled);
  }

  function initiateZcTokenFillingVaultInitiate(Hash.Order calldata o, uint256 a, Sig.Components calldata c) internal {
    bytes32 hash = validOrderHash(o, c);

    require((a <= o.principal - filled[hash]), 'taker amount > available volume');

    filled[hash] += a;

    uint256 premiumFilled = (((a * 1e18) / o.principal) * o.premium) / 1e18;
    uint256 fee = ((premiumFilled * 1e18) / fenominator[0]) / 1e18;

    Erc20 uToken = Erc20(o.underlying);
    uToken.transferFrom(o.maker, msg.sender, premiumFilled);
    uToken.transferFrom(msg.sender, address(this), (a + fee));

    MarketPlace mPlace = MarketPlace(marketPlace);
    address cTokenAddr = mPlace.cTokenAddress(o.underlying, o.maturity);
    uToken.approve(cTokenAddr, a);
    require(CErc20(cTokenAddr).mint(a) == 0, 'minting CToken Failed');

    require(mPlace.custodialInitiate(o.underlying, o.maturity, msg.sender, o.maker, a), 'custodial initiate failed');

    emit Initiate(o.key, hash, o.maker, o.vault, o.exit, msg.sender, a, premiumFilled);
  }

  function initiateZcTokenFillingZcTokenExit(Hash.Order calldata o, uint256 a, Sig.Components calldata c) internal {
    bytes32 hash = validOrderHash(o, c);

    require(a <= ((o.principal - filled[hash])), 'taker amount > available volume');

    filled[hash] += a;

    uint256 premiumFilled = (((a * 1e18) / o.principal) * o.premium) / 1e18;
    uint256 fee = ((premiumFilled * 1e18) / fenominator[0]) / 1e18;

    Erc20(o.underlying).transferFrom(msg.sender, o.maker, ((a - premiumFilled) + fee));
    require(MarketPlace(marketPlace).p2pZcTokenExchange(o.underlying, o.maturity, o.maker, msg.sender, a), 'zcToken exchange failed');

    emit Initiate(o.key, hash, o.maker, o.vault, o.exit, msg.sender, a, premiumFilled);
  }

  function initiateVaultFillingVaultExit(Hash.Order calldata o, uint256 a, Sig.Components calldata c) internal {
    bytes32 hash = validOrderHash(o, c);

    require(a <= (o.premium - filled[hash]), 'taker amount > available volume');

    filled[hash] += a;

    uint256 principalFilled = (((a * 1e18) / o.premium) * o.principal) / 1e18;
    uint256 fee = ((principalFilled * 1e18) / fenominator[2]) / 1e18;

    Erc20(o.underlying).transferFrom(msg.sender, o.maker, a);

    MarketPlace mPlace = MarketPlace(marketPlace);
    require(mPlace.p2pVaultExchange(o.underlying, o.maturity, o.maker, msg.sender, principalFilled), 'vault exchange failed');

    require(mPlace.transferVaultNotionalFee(o.underlying, o.maturity, msg.sender, fee), "notional fee transfer failed");

    emit Initiate(o.key, hash, o.maker, o.vault, o.exit, msg.sender, a, principalFilled);
  }

  function exit(Hash.Order[] calldata o, uint256[] calldata a, Sig.Components[] calldata c) external returns (bool) {
    for (uint256 i=0; i < o.length; i++) {
      if (!o[i].exit) {
          if (!o[i].vault) {
            exitZcTokenFillingZcTokenInitiate(o[i], a[i], c[i]);
          } else {
            exitVaultFillingVaultInitiate(o[i], a[i], c[i]);
          }
      } else {
        if (!o[i].vault) {
          exitVaultFillingZcTokenExit(o[i], a[i], c[i]);
        } else {
          exitZcTokenFillingVaultExit(o[i], a[i], c[i]);
        }
      }
    }

    return true;
  }

  function exitZcTokenFillingZcTokenInitiate(Hash.Order calldata o, uint256 a, Sig.Components calldata c) internal {
    bytes32 hash = validOrderHash(o, c);

    require(a <= (o.premium - filled[hash]), 'taker amount > available volume');

    filled[hash] += a;

    uint256 principalFilled = (((a * 1e18) / o.premium) * o.principal) / 1e18;
    uint256 fee = ((principalFilled * 1e18) / fenominator[1]) / 1e18;

    Erc20 uToken = Erc20(o.underlying);
    uToken.transferFrom(o.maker, msg.sender, principalFilled - a - fee);
    uToken.transferFrom(o.maker, address(this), fee);

    require(MarketPlace(marketPlace).p2pZcTokenExchange(o.underlying, o.maturity, msg.sender, o.maker, principalFilled), 'zcToken exchange failed');

    emit Exit(o.key, hash, o.maker, o.vault, o.exit, msg.sender, a, principalFilled);
  }

  function exitVaultFillingVaultInitiate(Hash.Order calldata o, uint256 a, Sig.Components calldata c) internal {
    bytes32 hash = validOrderHash(o, c);

    require(a <= (o.principal - filled[hash]), 'taker amount > available volume');

    filled[hash] += a;

    uint256 premiumFilled = (((a * 1e18) / o.principal) * o.premium) / 1e18;
    uint256 fee = ((premiumFilled * 1e18) / fenominator[3]) / 1e18;

    Erc20 uToken = Erc20(o.underlying);
    uToken.transferFrom(o.maker, msg.sender, premiumFilled - fee);

    uToken.transferFrom(msg.sender, address(this), fee);

    require(MarketPlace(marketPlace).p2pVaultExchange(o.underlying, o.maturity, msg.sender, o.maker, a), 'vault exchange failed');

    emit Exit(o.key, hash, o.maker, o.vault, o.exit, msg.sender, a, premiumFilled);
  }

  function exitVaultFillingZcTokenExit(Hash.Order calldata o, uint256 a, Sig.Components calldata c) internal {
    bytes32 hash = validOrderHash(o, c);

    require(a <= (o.principal - filled[hash]), 'taker amount > available volume');

    filled[hash] += a;

    uint256 premiumFilled = (((a * 1e18) / o.principal) * o.premium) / 1e18;
    uint256 fee = ((premiumFilled * 1e18) / fenominator[3]) / 1e18;

    MarketPlace mPlace = MarketPlace(marketPlace);
    address cTokenAddr = mPlace.cTokenAddress(o.underlying, o.maturity);
    require((CErc20(cTokenAddr).redeemUnderlying(a) == 0), "compound redemption error");

    Erc20 uToken = Erc20(o.underlying);
    uToken.transfer(o.maker, a - premiumFilled);
    uToken.transfer(msg.sender, premiumFilled - fee);

    require(mPlace.custodialExit(o.underlying, o.maturity, o.maker, msg.sender, a), 'custodial exit failed');

    emit Exit(o.key, hash, o.maker, o.vault, o.exit, msg.sender, a, premiumFilled);
  }

  function exitZcTokenFillingVaultExit(Hash.Order calldata o, uint256 a, Sig.Components calldata c) internal {
    bytes32 hash = validOrderHash(o, c);

    require(a <= (o.premium - filled[hash]), 'taker amount > available volume');

    filled[hash] += a;

    uint256 principalFilled = (((a * 1e18) / o.premium) * o.principal) / 1e18;
    uint256 fee = ((principalFilled * 1e18) / fenominator[1]) / 1e18;

    MarketPlace mPlace = MarketPlace(marketPlace);
    address cTokenAddr = mPlace.cTokenAddress(o.underlying, o.maturity);
    require((CErc20(cTokenAddr).redeemUnderlying(principalFilled) == 0), "compound redemption error");

    Erc20 uToken = Erc20(o.underlying);
    uToken.transfer(msg.sender, principalFilled - a - fee);
    uToken.transfer(o.maker, a);

    require(mPlace.custodialExit(o.underlying, o.maturity, msg.sender, o.maker, principalFilled), 'custodial exit failed');

    emit Exit(o.key, hash, o.maker, o.vault, o.exit, msg.sender, a, principalFilled);
  }

  function cancel(Hash.Order calldata o, Sig.Components calldata c) external returns (bool) {
    bytes32 hash = validOrderHash(o, c);

    require(msg.sender == o.maker, 'sender must be maker');

    cancelled[hash] = true;

    emit Cancel(o.key, hash);

    return true;
  }

  function scheduleWithdrawal(address e) external onlyAdmin(admin) {
    uint256 when = block.timestamp + HOLD;
    withdrawals[e] = when;
    emit WithdrawalScheduled(e, when);
  }

  function blockWithdrawal(address e) external onlyAdmin(admin) {
      withdrawals[e] = 0;
  }

  function withdraw(address e) external onlyAdmin(admin) {
    uint256 when = withdrawals[e];
    require (when != 0, 'no withdrawal scheduled');
    require (block.timestamp >= when, 'withdrawal still on hold');

    withdrawals[e] = 0;

    Erc20 token = Erc20(e);
    token.transfer(admin, token.balanceOf(address(this)));
  }

  function setFee(uint16 t, uint16 d) external onlyAdmin(admin) returns (bool) {
    fenominator[t] = d;
    return true;
  }

  function splitUnderlying(address u, uint256 m, uint256 a) external returns (bool) {
    Erc20 uToken = Erc20(u);
    uToken.transferFrom(msg.sender, address(this), a);
    MarketPlace mPlace = MarketPlace(marketPlace);
    address cTokenAddr = mPlace.cTokenAddress(u, m);
    uToken.approve(cTokenAddr, a);
    require(CErc20(cTokenAddr).mint(a) == 0, 'minting CToken Failed');
    require(mPlace.mintZcTokenAddingNotional(u, m, msg.sender, a), 'mint ZcToken adding Notional failed');

    return true;
  }

  function combineTokens(address u, uint256 m, uint256 a) external returns (bool) {
    MarketPlace mPlace = MarketPlace(marketPlace);
    require(mPlace.burnZcTokenRemovingNotional(u, m, msg.sender, a), 'burn ZcToken removing Notional failed');
    address cTokenAddr = mPlace.cTokenAddress(u, m);
    require((CErc20(cTokenAddr).redeemUnderlying(a) == 0), "compound redemption error");
    Erc20(u).transfer(msg.sender, a);

    return true;
  }

  function redeemZcToken(address u, uint256 m, uint256 a) external returns (bool) {
    MarketPlace mPlace = MarketPlace(marketPlace);
    uint256 redeemed = mPlace.redeemZcToken(u, m, msg.sender, a);
    require(CErc20(mPlace.cTokenAddress(u, m)).redeemUnderlying(redeemed) == 0, 'compound redemption failed');
    Erc20(u).transfer(msg.sender, redeemed);

    return true;
  }

  function redeemVaultInterest(address u, uint256 m) external returns (bool) {
    MarketPlace mPlace = MarketPlace(marketPlace);
    uint256 redeemed = mPlace.redeemVaultInterest(u, m, msg.sender);
    require(CErc20(mPlace.cTokenAddress(u, m)).redeemUnderlying(redeemed) == 0, 'compound redemption failed');
    Erc20(u).transfer(msg.sender, redeemed);

    return true;
  }

  function validOrderHash(Hash.Order calldata o, Sig.Components calldata c) internal view returns (bytes32) {
    bytes32 hash = Hash.order(o);

    require(!cancelled[hash], 'order cancelled');
    require(o.expiry >= block.timestamp, 'order expired');
    require(o.maker == Sig.recover(Hash.message(domain, hash), c), 'invalid signature');

    return hash;
  }

  modifier onlyAdmin(address a) {
    require(msg.sender == a, 'sender must be admin');
    _;
  }
}
