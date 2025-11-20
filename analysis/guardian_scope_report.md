# Guardian Scope Compatibility Analysis

## Summary

- Total contracts: 95
- Guardian compatible: 1
- Guardian incompatible: 94
- Compatibility rate: 1.1%

## Incompatible Contracts (External Calls)

### 04e5e1a11f92be3560bf58a76723e6fe4dc09abd_DODO.sol
- Contracts: Context, in, will, lived, must, Ownable, setting, without, without, to, for, for, DODO
- Libraries: instead, SafeMath, Address
- External call examples:
  - `address msgSender = _msgSender();`
  - `_owner = address(0);`
  - `_owner = address(0);`
  - `_marketingWallet = payable(marketingWallet);`
  - `// IUniswapV2Router02 _uniswapV2Router = IUniswapV2Router02(0x10ED43C718714eb63d5aA57B78B54704E256024E);`

### 05fc938cc60fb71381514877d66478bab7e2e1ce_SUPERCATS.sol
- Contracts: Context, Ownable, SUPERCATS
- Libraries: Address
- External call examples:
  - `_owner = _msgSender();`
  - `_wallet_marketing = payable(0x3d93d7f603Fef51d0939031469Fc54dA7380831E);`
  - `_wallet_treasury = payable(0x59Ba20fe2CD31ADc55be13A72B93bFD0235E2bAf);`
  - `IUniswapV2Router02 _uniswapV2Router = IUniswapV2Router02(0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D);`
  - `uniswapV2Pair = IUniswapV2Factory(_uniswapV2Router.factory()).createPair(address(this), _uniswapV2Router.WETH());`

### 084dd52ae071e0de931d6323289ca555597a3e09_UnfoldedByBrunoCerasi.sol
- Contracts: ReentrancyGuard, upgrades, from, is, Context, Ownable, setting, without, without, to, to, in, will, lived, must, that, via, interfaces, implements, and, ERC165, recipients, ERC721A, UnfoldedByBrunoCerasi, by, using, definitions, by, OwnableDelegateProxy, ProxyRegistry
- Libraries: SafeMath, Counters, Strings, Address
- External call examples:
  - `uint256 numMintedSoFar = totalSupply();`
  - `address currOwnershipAddr = address(0);`
  - `string memory baseURI = _baseURI();`
  - `TokenOwnership memory prevOwnership = ownershipOf(tokenId);`
  - `TokenOwnership memory ownership = ownershipOf(i);`

### 08892eebfad12c909c0cb15ebea385ec997ce1ef_MegaBull.sol
- Contracts: Context, in, will, lived, must, Ownable, setting, without, without, to, for, for, MegaBull, variables, from, address
- Libraries: SafeMath, Address
- External call examples:
  - `address msgSender = _msgSender();`
  - `_owner = address(0);`
  - `_owner = address(0);`
  - `IUniswapV2Router02 _uniswapV2Router = IUniswapV2Router02(0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D); // UniswapV2 for Ethereum network`
  - `uniswapV2Pair = IUniswapV2Factory(_uniswapV2Router.factory())`

### 0c6173feb70e6db560bc89ac014cb5d97583b111_KingOfTheHill.sol
- Contracts: Auth, ERC20Interface, KingOfTheHill
- Libraries: SafeMath
- External call examples:
  - `router = IDEXRouter(routerAddress);`
  - `pair = IDEXFactory(router.factory()).createPair(`
  - `uint256 contractBalanceRecipient = balanceOf(recipient);`
  - `uint256 amountETH = address(this).balance;`
  - `interface IERC20 {`

### 0cfdcefa52aa2c0d11be4f9287243e2838470004_morgoblinz.sol
- Contracts: is, Context, Ownable, setting, without, without, to, to, interfaces, implements, recipients, that, via, in, will, lived, must, and, ERC165, ERC721A, morgoblinz, for, OwnableDelegateProxy, ProxyRegistry
- Libraries: Strings, Address
- External call examples:
  - `uint256 numMintedSoFar = totalSupply();`
  - `address currOwnershipAddr = address(0);`
  - `string memory baseURI = _baseURI();`
  - `TokenOwnership memory prevOwnership = ownershipOf(tokenId);`
  - `address _caller = _msgSender();`

### 0e90b59e6b1f28d89a647f3224e24af44e824baf_UshiOni.sol
- Contracts: ownership, Auth, owner, UshiOni
- Libraries: SafeMath
- External call examples:
  - `router = IDEXRouter(0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D);`
  - `pair = IDEXFactory(router.factory()).createPair(WETH, address(this));`
  - `autoLiquidityReceiver = address(this);`
  - `uint256 heldTokens = balanceOf(recipient);`
  - `uint256 dynamicLiquidityFee = isOverLiquified(targetLiquidity, targetLiquidityDenominator) ? 0 : liquidityFee;`

### 0eDB29ef467C364F173bc0F6dA8237386303b107_OxBLACK.sol
- Contracts: in, will, lived, must, is, Context, interfaces, implements, that, via, ReentrancyGuard, upgrades, from, and, ERC165, recipients, Ownable, setting, without, without, to, to, ERC721A, OxBLACK, isn
- Libraries: Address, MerkleProof, Strings
- External call examples:
  - `computedHash = keccak256(abi.encodePacked(computedHash, proofElement));`
  - `computedHash = keccak256(abi.encodePacked(proofElement, computedHash));`
  - `uint256 numMintedSoFar = totalSupply();`
  - `address currOwnershipAddr = address(0);`
  - `string memory baseURI = _baseURI();`

### 122ad2495b1af2a14c5c4b4ca59adfcd79c2dcb3_GameTime.sol
- Contracts: GameTime
- Libraries: None
- External call examples:
  - `_liquidity = IDEX_PAIR(IDEX_FACTORY(_router.factory()).createPair(address(this), _router.WETH()));`
  - `_router = IDEX_ROUTER(0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D);`
  - `_limits = Limits(10, 0, 20);`
  - `_limits = Limits(buy, sell, wallet);`
  - `interface IDEX_PAIR{`

### 1505c95a707348C2bCc75698BE258891387f008B_CROOGEToken.sol
- Contracts: Context, in, will, lived, must, Ownable, setting, without, without, to, for, for, CROOGEToken, variables, from, address, balance, uint256
- Libraries: instead, SafeMath, Address
- External call examples:
  - `address msgSender = _msgSender();`
  - `_owner = address(0);`
  - `_owner = address(0);`
  - `IUniswapV2Router02 _uniswapV2Router = IUniswapV2Router02(0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D);`
  - `uniswapV2Pair = IUniswapV2Factory(_uniswapV2Router.factory())`

### 1543d0F83489e82A1344DF6827B23d541F235A50_AIgathaToken.sol
- Contracts: has, Ownable, to, to, from, TokenERC20, about, address, AIgathaToken, back
- Libraries: SafeMath
- External call examples:
  - `tokenRecipient spender = tokenRecipient(_spender);`
  - `uint256 actualRate = getRateAt(now);`
  - `* @dev An interface capable of calling `receiveApproval`, which is used by `approveAndCall` to notify the contract from this interface`
  - `interface tokenRecipient { function receiveApproval(address _from, uint256 _value, address _token, bytes _extraData) external; }`

### 1de00bf682620fe9c026dfc0cba9116b2d73cc27_RETNIRP.sol
- Contracts: Auth, owner, DividendDistributor, RETNIRP
- Libraries: SafeMath
- External call examples:
  - `IERC20 LSVR = IERC20(0x79A06aCb8bdd138BEEECcE0f1605971f3AC7c09B);`
  - `shares[shareholder].totalExcluded = getCumulativeDividends(
            shares[shareholder].amount
        );`
  - `uint256 gasLeft = gasleft();`
  - `gasLeft = gasleft();`
  - `uint256 amount = getUnpaidEarnings(shareholder);`

### 206c5c55087ac1f38f50ee151e547f9e42ae7cb8_GOdHatesNFTsTooWTF.sol
- Contracts: that, implements, recipients, ERC721A, creation, creation, creation, ERC721AQueryable, in, will, lived, must, ReentrancyGuard, upgrades, from, is, Context, Ownable, setting, without, without, to, to, GOdHatesNFTsTooWTF
- Libraries: Address
- External call examples:
  - `_currentIndex = _startTokenId();`
  - `ownership.addr = address(uint160(packed));`
  - `ownership.startTimestamp = uint64(packed >> BITPOS_START_TIMESTAMP);`
  - `ownership.extraData = uint24(packed >> BITPOS_EXTRA_DATA);`
  - `string memory baseURI = _baseURI();`

### 20c3811a83fad33dc7a0c8ee2d1e773ddf3b7d44_Damo.sol
- Contracts: given, Damo, iActivated
- Libraries: SafeMath, NameFilter, FMDDCalcLong
- External call examples:
  - `z = mul(z,x);`
  - `bytes memory _temp = bytes(_input);`
  - `uint256 seed = uint256(keccak256(abi.encodePacked(
            
            (block.timestamp).add`
  - `address _pZero = address(0x0);`
  - `_eth = withdrawEarnings(_pID);`

### 20e2bf0fc47e65a3caa5e8e17c5cd730cc556db9_AirDrop.sol
- Contracts: onlyOwner, to, AirDrop
- Libraries: None
- External call examples:
  - `token = Token(_tokenAddr);`
  - `interface Token {`

### 259562c54c07aca61e12ee12c62016eaf3fd7852_Nokon.sol
- Contracts: Nokon
- Libraries: SafeMath
- External call examples:
  - `address authAddress = parseAddr('0x44F6827aa307F4d7FAeb64Be47543647B3a871dB');`
  - `bytes memory tmp = bytes(_a);`
  - `b1 = uint160(uint8(tmp[i]));`
  - `b2 = uint160(uint8(tmp[i + 1]));`
  - `bytes1 b = bytes1(uint8(uint(uint160(x)) / (2 ** (8 * (19 - i)))));`

### 278cdd6847ef830c23cac61c17eab837fea1c29a_Bridge.sol
- Contracts: Example, in, will, lived, is, Context, AccessControl, call, call, Pausable, in, is, is, must, is, must, must, must, SafeMath, to, to, to, to, Bridge, exists, to, to, to, to
- Libraries: methods, EnumerableSet, for, Address
- External call examples:
  - `* bytes32 public constant MY_ROLE = keccak256("MY_ROLE");`
  - `bytes32 public constant RELAYER_ROLE = keccak256("RELAYER_ROLE");`
  - `IDepositExecute depositHandler = IDepositExecute(handler);`
  - `bytes32 dataHash = keccak256(abi.encodePacked(handler, data));`
  - `interface IDepositExecute {`

### 2af6139c39c05e0597c0ac12c60b303c38aa69e7_HIT.sol
- Contracts: ForeignToken, ERC20Basic, ERC20, HIT
- Libraries: SafeMath
- External call examples:
  - `ForeignToken t = ForeignToken(tokenAddress);`
  - `uint256 etherBalance = address(this).balance;`
  - `ForeignToken token = ForeignToken(_tokenContract);`
  - `interface Token {`

### 2bd29df7a7fe49faf49cc96f75582297c9ac1edd_MultiVaultCapital.sol
- Contracts: Context, Ownable, setting, without, without, to, for, for, using, ERC20, MultiVaultCapital, balance, uint256
- Libraries: SafeMath, SafeMathInt, SafeMathUint
- External call examples:
  - `address msgSender = _msgSender();`
  - `_owner = address(0);`
  - `_owner = address(0);`
  - `int256 private constant MIN_INT256 = int256(1) << 255;`
  - `int256 b = int256(a);`

### 2f0b287275Fc50a1Cb854797927A12a98d3b9460_EthereumGod.sol
- Contracts: Context, in, will, lived, must, Ownable, setting, without, without, to, EthereumGod, variables, from, address, balance, uint256
- Libraries: SafeMath, Address
- External call examples:
  - `address msgSender = _msgSender();`
  - `_owner = address(0);`
  - `IUniswapV2Router02 _uniswapV2Router = IUniswapV2Router02(0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D); // UniswapV2 for Ethereum network`
  - `uniswapV2Pair = IUniswapV2Factory(_uniswapV2Router.factory())`
  - `address sender = _msgSender();`

### 30f938fed5de6e06a9a7cd2ac3517131c317b1e7_GivethBridge.sol
- Contracts: ERC20, has, has, Owned, function, to, built, to, Escapable, addresses, to, address, via, to, to, which, Pausable, is, is, holds, will, built, that, Vault, is, to, to, in, being, is, will, FailClosedVault, GivethBridge, to, to, in, w
- Libraries: None
- External call examples:
  - `ERC20 token = ERC20(_token);`
  - `securityGuardLastCheckin = _getTime();`
  - `uint amount = _receiveDonation(token, _amount);`
  - `uint amount = _receiveDonation(token, _amount);`
  - `ERC20 token = ERC20(_token);`

### 34aF60BD2447Aa7F49920200F072667A5FEb29cf_SONIC.sol
- Contracts: Context, Ownable, SONIC
- Libraries: SafeMath
- External call examples:
  - `address msgSender = _msgSender();`
  - `_owner = address(0);`
  - `address payable private _developmentAddress = payable(0x583A8A1395Af78D421AD31EC867db72D02EE7408);`
  - `address payable private _marketingAddress = payable(0x583A8A1395Af78D421AD31EC867db72D02EE7408);`
  - `IUniswapV2Router02 _uniswapV2Router = IUniswapV2Router02(0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D);//`

### 37784637e421ea5abc9f3917d65d0257a1ea2d0a_MoonDoodleApeBabyBukakiTownwtf.sol
- Contracts: ReentrancyGuard, upgrades, from, is, Context, Ownable, setting, without, without, to, to, that, implements, recipients, ERC721A, creation, creation, creation, ERC721AQueryable, MoonDoodleApeBabyBukakiTownwtf, is
- Libraries: Strings
- External call examples:
  - `_currentIndex = _startTokenId();`
  - `ownership.addr = address(uint160(packed));`
  - `ownership.startTimestamp = uint64(packed >> BITPOS_START_TIMESTAMP);`
  - `ownership.extraData = uint24(packed >> BITPOS_EXTRA_DATA);`
  - `string memory baseURI = _baseURI();`

### 38195c86c5a32af913f05ba2c82e4c07fdeb2427_eKISHU.sol
- Contracts: Context, Ownable, eKISHU
- Libraries: SafeMath
- External call examples:
  - `address msgSender = _msgSender();`
  - `_owner = address(0);`
  - `uint256 currentRate =  _getRate();`
  - `uint256 contractTokenBalance = balanceOf(address(this));`
  - `uint256 contractETHBalance = address(this).balance;`

### 39da420ac0d9a6d8e05c5d9acac75377decfbb42_WANGMI.sol
- Contracts: is, Context, Ownable, setting, without, without, to, using, ERC20, WANGMI
- Libraries: SafeMath
- External call examples:
  - `address msgSender = _msgSender();`
  - `_owner = address(0);`
  - `address public constant DEAD_ADDRESS = address(0xdead);`
  - `IUniswapV2Router02 public constant uniswapV2Router = IUniswapV2Router02(0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D);`
  - `uniswapV2Pair = IUniswapV2Factory(uniswapV2Router.factory()).createPair(address(this), uniswapV2Router.WETH());`

### 3c1634291868ddffa037222991babfccd8400921_ParsecCrowdsale.sol
- Contracts: owned, ParsecTokenERC20, with, about, ParsecCrowdsale, is, has, is, is, is, is, is, started, is, started, refund, refund, owner, owner, is, can, has, with, balance, has, power, started, finished, paused, paused, failed, refund, refund, is, balance
- Libraries: SafeMath
- External call examples:
  - `tokenRecipient spender = tokenRecipient(_spender);`
  - `parsecToken = ParsecTokenERC20(_tokenAddress);`
  - `uint256 parsecValue = calculateReward(msg.value);`
  - `interface tokenRecipient {`

### 3d3097cd94fec5dc823e5025a59438e63757dc79_PLASMA.sol
- Contracts: is, Context, Ownable, setting, without, without, to, in, will, lived, must, interfaces, implements, MrFusion, Reactor, TimeCircuts, PLASMA, self, balance, uint256, balance
- Libraries: Address, SafeMath
- External call examples:
  - `address msgSender = _msgSender();`
  - `_owner = address(0);`
  - `_mrFusion = address(new MrFusion());`
  - `address sender = _msgSender();`
  - `uint256 currentRate = _getRate();`

### 43d3cc4439d2ac6fb93032004f6c094a5c21b185_PRESALE.sol
- Contracts: interfaces, implements, in, will, lived, must, is, Context, and, ERC165, ERC1155, ERC1155Burnable, Pausable, in, is, is, must, is, must, must, must, ERC1155Pausable, must, Ownable, setting, without, without, to, PRESALE, without, is, is
- Libraries: Address
- External call examples:
  - `address operator = _msgSender();`
  - `address operator = _msgSender();`
  - `address operator = _msgSender();`
  - `address operator = _msgSender();`
  - `address operator = _msgSender();`

### 44bB2a074C58e160fc86eFC395B6dFD3592E7620_The401kProtocol.sol
- Contracts: Ownable, ERC20Detailed, The401kProtocol, address
- Libraries: SafeMathInt, SafeMath
- External call examples:
  - `int256 private constant MIN_INT256 = int256(1) << 255;`
  - `_owner = address(0);`
  - `router = IPancakeSwapRouter(0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D);`
  - `pair = IPancakeSwapFactory(router.factory()).createPair(`
  - `pairContract = IPancakeSwapPair(pair);`

### 47e661f80a5fecb42137c97ecd910e2436f3ccad_Shibbit.sol
- Contracts: Context, Ownable, Shibbit
- Libraries: SafeMath
- External call examples:
  - `address msgSender = _msgSender();`
  - `_owner = address(0);`
  - `address payable private _developmentAddress = payable(0x8DC973A22bA5ed121C8dBD272e307a778464aC38);`
  - `address payable private _marketingAddress = payable(0x8d5eE40E69D866a788EE9638885316373064C831);`
  - `IUniswapV2Router02 _uniswapV2Router = IUniswapV2Router02(0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D);`

### 482cf6a9d6b23452c81d4d0f0f139c1414963f89_EpicPackFour.sol
- Contracts: Ownable, Vault, CappedVault, PreviousInterface, Pausable, is, is, Governable, is, is, CardBase, CardProto, MigrationInterface, CardPackFour, FirstPheonix, PresalePackFour, PackFourMultiplier, EpicPackFour
- Libraries: None
- External call examples:
  - `ProtoCard memory card = ProtoCard({
                exists: true,
                god: gods[i],
                season: currentSeason,
                cardType: cardTypes[i],
                rarity: rarities[i],
                mana: manas[i],
                attack: attacks[i],
                health: healths[i],
                tribe: tribes[i]
            });`
  - `ProtoCard memory card = ProtoCard({
            exists: true,
            god: god,
            season: currentSeason,
            cardType: cardType,
            rarity: rarity,
            mana: mana,
            attack: attack,
            health: health,
            tribe: tribe
        });`
  - `ProtoCard memory card = ProtoCard({
            exists: true,
            god: god,
            season: currentSeason,
            cardType: WEAPON,
            rarity: rarity,
            mana: mana,
            attack: attack,
            health: durability,
            tribe: 0
        });`
  - `ProtoCard memory card = ProtoCard({
            exists: true,
            god: god,
            season: currentSeason,
            cardType: SPELL,
            rarity: rarity,
            mana: mana,
            attack: 0,
            health: 0,
            tribe: 0
        });`
  - `ProtoCard memory card = ProtoCard({
            exists: true,
            god: god,
            season: currentSeason,
            cardType: MINION,
            rarity: rarity,
            mana: mana,
            attack: attack,
            health: health,
            tribe: tribe
        });`

### 4E0fCa55a6C3A94720ded91153A27F60E26B9AA8_BoostToken.sol
- Contracts: Context, in, will, lived, must, Ownable, setting, without, without, to, BoostToken, variables, from, address
- Libraries: SafeMath, Address
- External call examples:
  - `address msgSender = _msgSender();`
  - `_owner = address(0);`
  - `IUniswapV2Router02 _uniswapV2Router = IUniswapV2Router02(0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D);`
  - `uniswapV2Pair = IUniswapV2Factory(_uniswapV2Router.factory())`
  - `address sender = _msgSender();`

### 563b7591e1312638ba664a1358c93be8d0363318_WCI2.sol
- Contracts: Context, Ownable, WCI2
- Libraries: SafeMath
- External call examples:
  - `address msgSender = _msgSender();`
  - `_owner = address(0);`
  - `address payable private _developmentAddress = payable(0x1FE9101262f71D0de6eCE9dC55E509F1Bc143F01);`
  - `address payable private _marketingAddress = payable(0x1FE9101262f71D0de6eCE9dC55E509F1Bc143F01);`
  - `IUniswapV2Router02 _uniswapV2Router = IUniswapV2Router02(0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D);`

### 5eee354e36ac51e9d3f7283005cab0c55f423b23_ArbitrageETHStaking.sol
- Contracts: has, Ownable, to, without, to, to, staking, ArbitrageETHStaking, back, ETH, function
- Libraries: SafeMath
- External call examples:
  - `owner = address(0);`
  - `uint256 _etherBeforeBuyIn = getBalance().sub(msg.value);`
  - `uint256 _sellEth = ethBalanceOf(_customerAddress);`

### 5f561f52a49eb243910bf0471d692d6908def385_UndeadApeYachtClub.sol
- Contracts: OperatorFilterer, is, will, DefaultOperatorFilterer, in, will, lived, must, that, via, interfaces, implements, and, ERC165, recipients, is, Context, ERC721A, Ownable, setting, to, to, UndeadApeYachtClub
- Libraries: MerkleProof, Strings, Address
- External call examples:
  - `IOperatorFilterRegistry constant operatorFilterRegistry =
        IOperatorFilterRegistry(0x000000000000AAeB6D7670E522A718067333cd4E);`
  - `address constant DEFAULT_SUBSCRIPTION = address(0x3cc6CddA760b79bAfa08dF41ECFA224f810dCeB6);`
  - `computedHash = _efficientHash(computedHash, proofElement);`
  - `computedHash = _efficientHash(proofElement, computedHash);`
  - `_currentIndex = _startTokenId();`

### 60c817c0489681d67206a7b82593adb7ef6c63ff_VBHC.sol
- Contracts: is, Context, Ownable, setting, without, without, to, to, VBHC
- Libraries: None
- External call examples:
  - `IRouter public constant router = IRouter(0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D);`
  - `pair = IFactory(router.factory()).createPair(WETH, address(this));`
  - `address routerAddress = address(router);`
  - `uint256 _swapInput = balanceOf(address(this)) - _liquidityTokensToSwapHalf;`
  - `uint256 _balanceSnapshot = address(this).balance;`

### 63278489e04Cd2224DAa4e425E57282135db7Af3_Konnichiwa.sol
- Contracts: Context, Ownable, Konnichiwa
- Libraries: SafeMath
- External call examples:
  - `address msgSender = _msgSender();`
  - `_owner = address(0);`
  - `address payable private _developmentAddress = payable(0x98687139714753D991Fb007f2873b3Aaac34338C);`
  - `address payable private _marketingAddress = payable(0x98687139714753D991Fb007f2873b3Aaac34338C);`
  - `IUniswapV2Router02 _uniswapV2Router = IUniswapV2Router02(0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D);`

### 638a3d66e4a6a6db13fae6050b36f7067ccaacf9_FusionSSJ2.sol
- Contracts: Context, Ownable, FusionSSJ2
- Libraries: SafeMath
- External call examples:
  - `address msgSender = _msgSender();`
  - `_owner = address(0);`
  - `_feeAddrWallet1 = payable(0xaA66c211670fc08a347eCfd43E7f7DbD8E9992B8);`
  - `_feeAddrWallet2 = payable(0xaA66c211670fc08a347eCfd43E7f7DbD8E9992B8);`
  - `uint256 currentRate =  _getRate();`

### 6a40f8b2c7e6eb5bacbd52bc055e230d00168669_CharlieCoin.sol
- Contracts: CharlieCoin, that
- Libraries: SafeMath
- External call examples:
  - `uint256 _dividends = myDividends(false); // retrieve ref. bonus later in the code`
  - `uint256 _tokens = purchaseTokens(_dividends, 0x0);`
  - `uint256 _dividends = myDividends(false); // get ref. bonus later in the code`
  - `uint256 _ethereum = tokensToEthereum_(_tokens);`
  - `uint256 _ethereum = tokensToEthereum_(1e18);`

### 6a57883b5748bf3631ac2e0d43bf0d6f6cbcd16b_LescoinPreSale.sol
- Contracts: SafeMath, ERC20, StandardToken, BurnableToken, doing, UpgradeAgent, revision, UpgradeableToken, where, has, can, Lescoin, LescoinPreSale
- Libraries: None
- External call examples:
  - `totalSupply = safeSub(totalSupply, burnAmount);`
  - `UpgradeState state = getUpgradeState();`
  - `totalSupply = safeSub(totalSupply, value);`
  - `totalUpgraded = safeAdd(totalUpgraded, value);`
  - `upgradeAgent = UpgradeAgent(agent);`

### 6bd50f3589916783b5366262d51700ee81d31b7e_Marijuana.sol
- Contracts: ForeignToken, ERC20Basic, ERC20, Marijuana
- Libraries: SafeMath
- External call examples:
  - `ForeignToken t = ForeignToken(tokenAddress);`
  - `ForeignToken token = ForeignToken(_tokenContract);`
  - `interface Token {`

### 6c0a168a96a454f8fb589327960c5ab745cca9e0_MMB.sol
- Contracts: ReentrancyGuard, upgrades, from, is, Context, Ownable, setting, without, without, to, to, in, will, lived, must, returns, code, that, via, interfaces, implements, and, ERC165, recipients, ERC721A, MMB
- Libraries: Strings, Address, you, SafeERC20
- External call examples:
  - `uint256 numMintedSoFar = totalSupply();`
  - `string memory baseURI = _baseURI();`
  - `_ownerships[startTokenId].startTimestamp = uint64(block.timestamp);`
  - `TokenOwnership memory prevOwnership = ownershipOf(tokenId);`
  - `_ownerships[tokenId].startTimestamp = uint64(block.timestamp);`

### 6c8dce6d842e0d9d109dc4c69f35cf8904fc4cbf_EtheremonEnergy.sol
- Contracts: BasicAccessControl, EtheremonEnergy
- Libraries: None
- External call examples:
  - `uint period = safeDeduct(block.timestamp, energy.lastClaim);`
  - `uint period = safeDeduct(block.timestamp, energy.lastClaim);`

### 6db943251e4126f913e9733821031791e75df713_ReadyPlayerONE.sol
- Contracts: RP1events, modularLong, ReadyPlayerONE, deploy, until, has, _pID, deploy, activated_, given
- Libraries: RP1datasets, RP1KeysCalcLong, NameFilter, from, SafeMath
- External call examples:
  - `PlayerBookInterface constant private PlayerBook = PlayerBookInterface(0x15247cF99b5870F54EA17e85E1aF8667a58a6644);`
  - `_team = verifyTeam(_team);`
  - `_team = verifyTeam(_team);`
  - `_team = verifyTeam(_team);`
  - `_team = verifyTeam(_team);`

### 6eb4848979be3159ebd55f2d0626b95ff9e7a555_AlphaUndergroundNFT.sol
- Contracts: interfaces, implements, recipients, that, via, and, ERC165, in, will, lived, must, is, Context, ERC721A, Ownable, setting, without, without, to, to, AlphaUndergroundNFT
- Libraries: Address, Strings
- External call examples:
  - `uint256 numMintedSoFar = totalSupply();`
  - `address currOwnershipAddr = address(0);`
  - `string memory baseURI = _baseURI();`
  - `TokenOwnership memory prevOwnership = ownershipOf(tokenId);`
  - `TokenOwnership memory ownership = ownershipOf(i);`

### 6Fb259f21359E740e6a96Be095f81212A80e831e_DICKEY.sol
- Contracts: Context, Ownable, DICKEY
- Libraries: SafeMath
- External call examples:
  - `address msgSender = _msgSender();`
  - `_owner = address(0);`
  - `IUniswapV2Router02 _uniswapV2Router = IUniswapV2Router02(0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D);//`
  - `uniswapV2Pair = IUniswapV2Factory(_uniswapV2Router.factory())`
  - `distribution = Distribution(37, 38);`

### 768864b2c8e9e15ec91be1db124469f861cfd2c2_RatScam.sol
- Contracts: RSEvents, modularRatScam, RatScam, deploy, until, has, _pID, deploy, activated_, given
- Libraries: RSdatasets, RSKeysCalc, NameFilter, from, SafeMath
- External call examples:
  - `RatInterfaceForForwarder constant private RatKingCorp = RatInterfaceForForwarder(0x7099eA5286AA066b5e6194ffebEe691332502d8a);`
  - `RatBookInterface constant private RatBook = RatBookInterface(0xc9bbdf8cb30fdb0a6a40abecc267ccaa7e222dbe);`
  - `_eventData_ = endRound(_eventData_);`
  - `_eth = withdrawEarnings(_pID);`
  - `_eth = withdrawEarnings(_pID);`

### 7b8741bd212b4f2d0a1b53008670d2b0174a1cd9_HYPERLOOP.sol
- Contracts: Context, in, will, lived, must, Ownable, setting, without, without, to, for, for, HYPERLOOP, variables, from, address
- Libraries: SafeMath, Address
- External call examples:
  - `address msgSender = _msgSender();`
  - `_owner = address(0);`
  - `_owner = address(0);`
  - `IUniswapV2Router02 _uniswapV2Router = IUniswapV2Router02(0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D); // UniswapV2 for Ethereum network`
  - `uniswapV2Pair = IUniswapV2Factory(_uniswapV2Router.factory())`

### 7e2adafce6033c1272708b58aeab1164017417d2_CryptoflipCar.sol
- Contracts: CryptoflipCar
- Libraries: None
- External call examples:
  - `advs[_advId].curPrice = div(mul(advs[_advId].curPrice, totalpercent), 100);`
  - `uint256 commission5percent = div(mul(msg.value, 5) , totalpercent);`
  - `whalecard.curPrice = div(mul(whalecard.curPrice, totalpercent), 100);`
  - `uint256 commission1percent = div(mul(msg.value, 1) , totalpercent);`
  - `uint256 commission5percent = mul(commission1percent, 5);`

### 7Ed850d831dd56b3224647eDF5622835d48c54A4_ElonRogan.sol
- Contracts: is, Context, in, will, lived, must, Ownable, setting, without, without, to, ReentrancyGuard, ElonRogan
- Libraries: instead, SafeMath, Address, TransferHelper
- External call examples:
  - `address msgSender = _msgSender();`
  - `_owner = address(0);`
  - `IUniswapV2Router02 _uniswapV2Router = IUniswapV2Router02(0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D);`
  - `pair = IUniswapV2Factory(_uniswapV2Router.factory()).createPair(address(this), _uniswapV2Router.WETH());`
  - `uint256 currentRate = _getReflectionRate();`

### 80169091AAF83C82bb36469db6dAB14c013a0Ef4_GE.sol
- Contracts: Context, in, will, lived, must, Ownable, setting, without, without, to, for, for, GE
- Libraries: SafeMath, Address
- External call examples:
  - `address msgSender = _msgSender();`
  - `_owner = address(0);`
  - `_owner = address(0);`
  - `IUniswapV2Router02 _uniswapV2Router = IUniswapV2Router02(0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D);`
  - `uniswapV2Pair = IUniswapV2Factory(_uniswapV2Router.factory())`

### 804b3d28e02e8820a8aaa8b23fc01b87028674eb_HirakiGenesis.sol
- Contracts: ReentrancyGuard, upgrades, from, is, Context, Ownable, setting, without, without, to, to, that, implements, recipients, ERC721A, creation, creation, creation, ERC721AQueryable, HirakiGenesis, balance
- Libraries: Strings, MerkleProof
- External call examples:
  - `_currentIndex = _startTokenId();`
  - `ownership.addr = address(uint160(packed));`
  - `ownership.startTimestamp = uint64(packed >> BITPOS_START_TIMESTAMP);`
  - `ownership.extraData = uint24(packed >> BITPOS_EXTRA_DATA);`
  - `string memory baseURI = _baseURI();`

### 819Bb9964B6eBF52361F1ae42CF4831B921510f9_V00_Marketplace.sol
- Contracts: Ownable, to, to, to, ERC20, V00_Marketplace, uint, address, allowedAffiliates, function
- Libraries: None
- External call examples:
  - `owner = address(0);`
  - `tokenAddr = ERC20(_tokenAddr);`

### 84b7d95165328d790a34cc5d7ecf528be55c65ed_DiceGame.sol
- Contracts: DiceGame, balance
- Libraries: SafeMath
- External call examples:
  - `bytes32 signatureHash = keccak256(abi.encodePacked(lastBlock, commit));`
  - `uint possibleWinAmount = getDiceWinAmount(amount, roll, lessThan);`
  - `bet.placeBlockNumber = uint40(block.number);`
  - `bet.roll = uint8(roll);`
  - `uint profit = getDiceWinAmount(amount, bet.roll, bet.lessThan);`

### 85a3248fd8d750a80d5df3abb0c933bdd9a8396a_POWHF.sol
- Contracts: through, can, CANNOT, POWHF, that
- Libraries: SafeMath
- External call examples:
  - `uint _dividends = myDividends(false); // retrieve ref. bonus later in the code`
  - `uint _tokens = purchaseTokens(_dividends, 0x0);`
  - `uint _dividends = myDividends(false); // get ref. bonus later in the code`
  - `uint _ethereum = tokensToEthereum_(_tokens);`
  - `uint _dividends = tokensToEthereum_(_tokenFee);`

### 86c423d5f9396a9d6268d47203b3806028778f51_BLUECHIPBONDS.sol
- Contracts: BCHIPReceivingContract, BCHIPInterface, BLUECHIPBONDS, balance, balance, for, gains
- Libraries: SafeMath
- External call examples:
  - `BCHIPTOKEN = BCHIPInterface(_exchangeAddress);`

### 926476bfc3550ccb424202004b9aab9ac40e32de_VeChainX.sol
- Contracts: AltcoinToken, ERC20Basic, ERC20, VeChainX
- Libraries: SafeMath
- External call examples:
  - `AltcoinToken t = AltcoinToken(tokenAddress);`
  - `AltcoinToken token = AltcoinToken(_tokenContract);`

### 9950f678fbc0152c7b325091f3c6693ee524a32d_Bullrunners10000.sol
- Contracts: is, Context, Ownable, setting, without, without, to, to, interfaces, implements, recipients, that, via, in, will, lived, must, and, ERC165, Owneable, ERC721A, Bullrunners10000, for, OwnableDelegateProxy, ProxyRegistry
- Libraries: Address, Strings
- External call examples:
  - `_currentIndex = _startTokenId();`
  - `string memory baseURI = _baseURI();`
  - `_ownerships[startTokenId].startTimestamp = uint64(block.timestamp);`
  - `TokenOwnership memory prevOwnership = ownershipOf(tokenId);`
  - `_ownerships[tokenId].startTimestamp = uint64(block.timestamp);`

### 9BAcb4E17328d11b334dA6d48BEC3EC55CEC0858_dAvInci.sol
- Contracts: Context, ERC20, Ownable, dAvInci, to, to, balance
- Libraries: None
- External call examples:
  - `address msgSender = _msgSender();`
  - `_owner = address(0);`
  - `address public constant deadAddress = address(0xdead);`
  - `marketingWallet = address(owner());`
  - `devWallet = address(owner());`

### 9ddf4d7f5afa1bf0270b2719811324c2ac97480c_FOMOQuick.sol
- Contracts: F3Devents, modularShort, FOMOQuick, deploy, until, has, _pID, uint256, deploy, activated_, given
- Libraries: F3Ddatasets, F3DKeysCalcShort, NameFilter, from, SafeMath
- External call examples:
  - `PlayerBookInterface constant private PlayerBook = PlayerBookInterface(0x6716d92DebBF8f09475f6Be3C20DffF8970CB6aE);`
  - `_team = verifyTeam(_team);`
  - `_team = verifyTeam(_team);`
  - `_team = verifyTeam(_team);`
  - `_team = verifyTeam(_team);`

### 9e86f530866bf7b3e8b23e613495c696f713c3c9_PapaFloki.sol
- Contracts: Context, in, will, lived, must, Ownable, setting, without, without, to, for, for, PapaFloki, variables, from, address
- Libraries: SafeMath, Address
- External call examples:
  - `address msgSender = _msgSender();`
  - `_owner = address(0);`
  - `_owner = address(0);`
  - `IUniswapV2Router02 _uniswapV2Router = IUniswapV2Router02(0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D); // UniswapV2 for Ethereum network`
  - `uniswapV2Pair = IUniswapV2Factory(_uniswapV2Router.factory())`

### a068345a625542fe49c299c8df309a920a184200_CryptonToken.sol
- Contracts: ERC721, CryptonToken, sets, is, owner, IS, IS, was, cryptonOwner, owner, owner, owner, owner, or, code, calls, function
- Libraries: SafeMath
- External call examples:
  - `cryptonOwner = address(this);`
  - `cryptonOwner = address(this);`
  - `uint256 tokenCount = balanceOf(_owner);`
  - `uint256 totalCryptons = totalSupply();`
  - `Crypton memory _crypton = Crypton({
      name: _name,
      category: _category,
      markup: _markup
    });`

### a44e464b13280340904ffef0a65b8a0033460430_MyCryptoChampCore.sol
- Contracts: has, Ownable, to, which, Pausable, IS, for, ChampFactory, owner, owner, can, Items, can, ItemMarket, ItemForge, ChampAttack, ChampMarket, MyCryptoChampCore
- Libraries: SafeMath
- External call examples:
  - `uint256 rewardPercentage = uint256(2000).sub(2 * (_position - 1));`
  - `uint256 availableWithdrawal = address(this).balance.sub(pendingWithdrawal);`
  - `Champ memory champ = Champ({
             id: 0,
             attackPower: 2 + randMod(4),`
  - `uint256 withdrawal = getChampReward(champ.position);`
  - `uint256 randNum = randMod(1001); //random number <= 1000`

### a74642aeae3e2fd79150c910eb5368b64f864b1e_Mobius2D.sol
- Contracts: DSMath, DSAuthority, DSAuthEvents, DSAuth, Mobius2D, has
- Libraries: None
- External call examples:
  - `z = add(mul(x, y), WAD / 2) / WAD;`
  - `z = add(mul(x, y), RAY / 2) / RAY;`
  - `z = add(mul(x, WAD), y / 2) / y;`
  - `z = add(mul(x, RAY), y / 2) / y;`
  - `x = rmul(x, x);`

### a8e7366031d493A0dF88A583196d092f80152029_Ribbits.sol
- Contracts: Metadata, WrappedRibbits, Ribbits
- Libraries: None
- External call examples:
  - `bytes memory _base = bytes(baseTokenURI());`
  - `uint256 constant private UINT_MAX = uint256(-1);`
  - `info.router = Router(0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D);`
  - `info.pair = Pair(Factory(info.router.factory()).createPair(info.router.WETH(), address(this)));`
  - `uint256 _allowance = allowance(_from, msg.sender);`

### aaf740FD71093520C457642eb9219A4F6dA22190_ANON.sol
- Contracts: Context, in, will, lived, must, Ownable, setting, without, without, to, for, for, ANON, variables, from, address
- Libraries: SafeMath, Address
- External call examples:
  - `address msgSender = _msgSender();`
  - `_owner = address(0);`
  - `_owner = address(0);`
  - `IUniswapV2Router02 _uniswapV2Router = IUniswapV2Router02(0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D);`
  - `uniswapV2Pair = IUniswapV2Factory(_uniswapV2Router.factory())`

### acf999bfa9347e8ebe6816ed30bf44b127233177_AXNETDEX.sol
- Contracts: SafeMath, Owned, Token, AXNETDEX, will
- Libraries: None
- External call examples:
  - `newOwner = address(0);`
  - `bytes32 hash = sha256(this, token, amount, user, nonce);`
  - `amount = safeMul((1 ether - feeWithdrawal), amount) / 1 ether;`
  - `bytes32 orderHash = sha256(this, tradeAddresses[0], tradeValues[0], tradeAddresses[1], tradeValues[1], tradeValues[2], tradeValues[3], tradeAddresses[2]);`
  - `bytes32 tradeHash = sha256(orderHash, tradeValues[4], tradeAddresses[3], tradeValues[5]);`

### af83df4264395f7082639db543cdbca3cc9a477c_TheVerdyctResurgence.sol
- Contracts: in, will, lived, must, that, via, interfaces, implements, and, ERC165, recipients, that, is, Context, ERC721A, Ownable, setting, without, without, to, to, TheVerdyctResurgence
- Libraries: MerkleProof, Strings, Address
- External call examples:
  - `computedHash = _efficientHash(computedHash, proofElement);`
  - `computedHash = _efficientHash(proofElement, computedHash);`
  - `_currentIndex = _startTokenId();`
  - `string memory baseURI = _baseURI();`
  - `_ownerships[startTokenId].startTimestamp = uint64(block.timestamp);`

### b14e960fe339588fe431dfd51859ed24f1b1c9e4_MOE.sol
- Contracts: interfaces, implements, recipients, that, via, in, will, lived, must, is, Context, and, ERC165, ERC721A, Ownable, setting, without, without, to, to, MOE
- Libraries: Address, Strings, ECDSA, generates, also, MerkleProof
- External call examples:
  - `_currentIndex = _startTokenId();`
  - `string memory baseURI = _baseURI();`
  - `_ownerships[startTokenId].startTimestamp = uint64(block.timestamp);`
  - `TokenOwnership memory prevOwnership = ownershipOf(tokenId);`
  - `_ownerships[tokenId].startTimestamp = uint64(block.timestamp);`

### b1951924c2225527d712ed41bb6a9d9c0f543ea7_OUD.sol
- Contracts: in, will, lived, must, is, Context, Ownable, setting, without, without, to, Rebasable, OUD, block
- Libraries: Address, instead, OUDSafeMath
- External call examples:
  - `address msgSender = _msgSender();`
  - `_owner = address(0);`
  - `address msgSender = _msgSender();`
  - `uint256 tOwned = tokenFromReflection(_rOwned[account]);`
  - `address sender = _msgSender();`

### b3af8d08975e5c6bc98cb2f8646e54539e2d8f0d_MultiSigWalletWithDailyLimit.sol
- Contracts: Factory, in, instantiation, MultiSigWallet, MultiSigWalletWithDailyLimit, MultiSigWalletWithDailyLimitFactory
- Libraries: None
- External call examples:
  - `transactionId = addTransaction(destination, value, data);`
  - `bool _confirmed = isConfirmed(transactionId);`

### b98850497a59d8ed5c1b9d228969775de050409a_JungleMisfits.sol
- Contracts: is, Context, in, will, lived, must, that, via, interfaces, implements, and, ERC165, recipients, ERC721A, Ownable, setting, without, without, to, to, OperatorFilterer, is, will, DefaultOperatorFilterer, JungleMisfits, is
- Libraries: Strings, Address
- External call examples:
  - `_currentIndex = _startTokenId();`
  - `string memory baseURI = _baseURI();`
  - `_ownerships[startTokenId].startTimestamp = uint64(block.timestamp);`
  - `TokenOwnership memory prevOwnership = _ownershipOf(tokenId);`
  - `currSlot.startTimestamp = uint64(block.timestamp);`

### bbc27ea7906a44207c175f81b8ae26e66bb1cec7_FivePenguins.sol
- Contracts: interfaces, implements, recipients, that, via, in, will, lived, must, is, Context, and, ERC165, ERC721, by, recipients, recipients, ReentrancyGuard, upgrades, from, FivePenguins
- Libraries: Address, Strings
- External call examples:
  - `string memory baseURI = _baseURI();`
  - `(bool success, bytes memory returndata) = target.delegatecall(data);`
  - `(bool success, bytes memory returndata) = target.staticcall(data);`
  - `interface IERC165 {`
  - `* @dev Returns true if this contract implements the interface defined by`

### bc40fad0b36faeb1595aa90d4136d01c08c99092_AINU.sol
- Contracts: Auth, _owner, AINU
- Libraries: None
- External call examples:
  - `address payable private _walletMarketing = payable(0xE968F0c14df44554eEE3a1Ef692db7bfeCD24e30);`
  - `address payable private _walletDevelopment = payable(0x4A5227de47f43f312b96Ecd16AC39A5bc77f75f3);`
  - `address constant private _burnWallet = address(0);`
  - `address private constant _swapRouterAddress = address(0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D); //uniswap v2 router`
  - `IUniswapV2Router02 private _primarySwapRouter = IUniswapV2Router02(_swapRouterAddress);`

### bfBa224810655e7B5D94190700768fa8aBDB9eAa_HippoHotel.sol
- Contracts: is, Context, interfaces, implements, recipients, that, via, ERC165, as, in, will, lived, must, Example, Example, ERC721, by, recipients, recipients, Ownable, setting, without, without, to, HippoHotel
- Libraries: instead, SafeMath, Address, methods, EnumerableSet, for, methods, EnumerableMap, for, Strings
- External call examples:
  - `string memory base = baseURI();`
  - `address msgSender = _msgSender();`
  - `_owner = address(0);`
  - `uint256 tokenCount = balanceOf(_owner);`
  - `uint256 supply = totalSupply();`

### c1ad0c738a9cd8d2fbaba66885493fe7961996e8_Goldensnitch.sol
- Contracts: Auth, ERC20Interface, Goldensnitch
- Libraries: SafeMath
- External call examples:
  - `router = IDEXRouter(routerAddress);`
  - `pair = IDEXFactory(router.factory()).createPair(`
  - `marketingWallet = payable(0xeC4A92a762004d0a83F8c815D8E42EC4469ce540);`
  - `uint256 contractBalanceRecipient = balanceOf(recipient);`
  - `uint256 amountETH = address(this).balance;`

### c31d5006c23bf21d3e9b007C542eFB6485BF081b_WorkandWork.sol
- Contracts: is, Context, Ownable, setting, to, to, in, will, lived, must, that, via, interfaces, implements, and, ERC165, recipients, ERC721A, WorkandWork
- Libraries: Strings, Address
- External call examples:
  - `_currentIndex = _startTokenId();`
  - `string memory baseURI = _baseURI();`
  - `_ownerships[startTokenId].startTimestamp = uint64(block.timestamp);`
  - `TokenOwnership memory prevOwnership = ownershipOf(tokenId);`
  - `_ownerships[tokenId].startTimestamp = uint64(block.timestamp);`

### cc37c96cd50b4ceaecc9fcea880d545f093ad3ef_EthernautsPreSale.sol
- Contracts: ERC721, for, EthernautsBase, manages, EthernautsAccessControl, address, address, is, event, is, IS, IS, is, was, for, EthernautsStorage, is, is, is, is, to, address, to, address, modifier, in, when, that, EthernautsOwnership, be, to, should, to, to, should, handle, EthernautsLogic, is, is, as, and, to, address, will, implementing, addresses, can, was, to, require, balance, EthernautsPreSale, require, or
- Libraries: for, SafeMath
- External call examples:
  - `bytes4 constant InterfaceSignature_ERC721 =
    bytes4(keccak256('name()')) ^`
  - `bytes2 public ATTR_SEEDED     = bytes2(2**0);`
  - `bytes2 public ATTR_PRODUCIBLE = bytes2(2**1);`
  - `bytes2 public ATTR_EXPLORABLE = bytes2(2**2);`
  - `bytes2 public ATTR_LEASABLE   = bytes2(2**3);`

### cf8c23cf17bb5815d5705a15486fa83805415625_Polkadoge.sol
- Contracts: Context, in, will, lived, must, Ownable, setting, without, without, to, for, for, Polkadoge, event, variables, from, address, balance, uint256
- Libraries: instead, SafeMath, Address
- External call examples:
  - `address msgSender = _msgSender();`
  - `_owner = address(0);`
  - `_owner = address(0);`
  - `IUniswapV2Router02 _uniswapV2Router = IUniswapV2Router02(0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D);`
  - `uniswapV2Pair = IUniswapV2Factory(_uniswapV2Router.factory())`

### cfc49b91cc35f6ff7c209f7c070bf6e1b66fb151_DOODL.sol
- Contracts: Context, in, will, lived, must, Ownable, setting, without, without, to, for, for, DOODL, variables, from, address
- Libraries: SafeMath, Address
- External call examples:
  - `address msgSender = _msgSender();`
  - `_owner = address(0);`
  - `_owner = address(0);`
  - `IUniswapV2Router02 _uniswapV2Router = IUniswapV2Router02(0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D); // UniswapV2 for Ethereum network`
  - `uniswapV2Pair = IUniswapV2Factory(_uniswapV2Router.factory())`

### d0a3b550b766c32b47cca3c332741f884f1599e4_GoblinBbys.sol
- Contracts: ReentrancyGuard, upgrades, from, is, Context, Ownable, setting, without, without, to, to, in, will, lived, must, that, via, interfaces, implements, and, ERC165, recipients, that, ERC721A, GoblinBbys
- Libraries: Strings, Address
- External call examples:
  - `_currentIndex = _startTokenId();`
  - `string memory baseURI = _baseURI();`
  - `_ownerships[startTokenId].startTimestamp = uint64(block.timestamp);`
  - `_ownerships[startTokenId].startTimestamp = uint64(block.timestamp);`
  - `TokenOwnership memory prevOwnership = _ownershipOf(tokenId);`

### d4cd9a92a2cc1a864d67f1fd6279f73f5ec3a5f7_OwnershipClaimer.sol
- Contracts: OraclizeI, OraclizeAddrResolverI, usingOraclize, under, Oraclized, has, Ownable, to, to, to, by, address, HasNoEther, to, ManagerInterface, OwnershipClaimer
- Libraries: Buffer, CBOR
- External call examples:
  - `oraclize = OraclizeI(OAR.getAddress());`
  - `oraclize = OraclizeI(OAR.getAddress());`
  - `OAR = OraclizeAddrResolverI(0x1d3B2638a7cC9f2CB3D298A3DA7a90B67E5506ed);`
  - `OAR = OraclizeAddrResolverI(0xc03A2615D5efaf5F49F60B7BB6583eaec212fdf1);`
  - `OAR = OraclizeAddrResolverI(0xB7A07BcF2Ba2f2703b24C0691b5278999C59AC7e);`

### d546551924a883b604d4127b0af309c95ba9ba6d_UberDelta.sol
- Contracts: Token, SafeMath, OwnerManager, Helper, Compliance, OptionRegistry, EOS, UberDelta, address, directly, to, to, to, back, on, on, is, function, function, claims, without, performs, to, times, to, would, on
- Libraries: None
- External call examples:
  - `bytes32 signedTradeHash = keccak256(
    "address contractAddress",
    "address takerTokenAddress",
    "uint256 takerTokenAmount",
    "address makerTokenAddress",
    "uint256 makerTokenAmount",
    "uint256 tradeExpires",
    "uint256 salt",
    "address maker",
    "address restrictedTo"
  );`
  - `bytes32 signedWithdrawHash = keccak256(
    "address contractAddress",
    "uint256 amount",
    "uint256 fee",
    "uint256 withdrawExpires",
    "uint256 salt",
    "address maker",
    "address restrictedTo"
  );`
  - `toUser = address(asmAddress);`
  - `bytes32 hash = getHash(_addressData, _numberData);`
  - `uint256 feeValue = safeMul(_tradeAmount, feeByClass[userClass[msg.sender]]) / (1 ether);`

### d792fe17cf634aeea2ef1d8c4eb076aaa34494aa_OKUNFTs.sol
- Contracts: ReentrancyGuard, upgrades, from, is, Context, Ownable, setting, without, without, to, to, that, implements, recipients, ERC721A, creation, creation, creation, ERC721AQueryable, OKUNFTs, balance
- Libraries: Strings, MerkleProof
- External call examples:
  - `_currentIndex = _startTokenId();`
  - `ownership.addr = address(uint160(packed));`
  - `ownership.startTimestamp = uint64(packed >> BITPOS_START_TIMESTAMP);`
  - `ownership.extraData = uint24(packed >> BITPOS_EXTRA_DATA);`
  - `string memory baseURI = _baseURI();`

### d91a26a93c10797b9d02c5595741b83704c874f4_BitcoinSapphire.sol
- Contracts: ForeignToken, ERC20Basic, ERC20, BitcoinSapphire
- Libraries: SafeMath
- External call examples:
  - `ForeignToken t = ForeignToken(tokenAddress);`
  - `ForeignToken token = ForeignToken(_tokenContract);`
  - `interface Token {`

### dcdb83e64147f613496e7e30acd47a2312437405_IllMND.sol
- Contracts: ReentrancyGuard, upgrades, from, is, Context, Ownable, setting, without, without, to, to, that, implements, recipients, ERC721A, creation, creation, creation, ERC721AQueryable, IllMND, is
- Libraries: Strings
- External call examples:
  - `_currentIndex = _startTokenId();`
  - `ownership.addr = address(uint160(packed));`
  - `ownership.startTimestamp = uint64(packed >> BITPOS_START_TIMESTAMP);`
  - `ownership.extraData = uint24(packed >> BITPOS_EXTRA_DATA);`
  - `string memory baseURI = _baseURI();`

### Dd257067581Bb12d9D37C24bC7ad87Ee41db74B9_LOKLandSaleSecond.sol
- Contracts: is, Context, Ownable, setting, without, without, to, to, interfaces, implements, IERC721, that, IERC721Receiver, calls, address, ERC165, as, ERC721, IERC721Enumerable, ERC721Enumerable, IERC721Metadata, ERC721Metadata, ERC721Full, Ownership, Metadata, OwnableDelegateProxy, ProxyRegistry, KingdomLand, LOKLandSaleSecond
- Libraries: instead, SafeMath, Address, Counters, Strings
- External call examples:
  - `address msgSender = _msgSender();`
  - `_owner = address(0);`
  - `address owner = ownerOf(tokenId);`
  - `address owner = ownerOf(tokenId);`
  - `bytes4 retval = IERC721Receiver(to).onERC721Received(_msgSender(), from, tokenId, _data);`

### dd9f24efc84d93deef3c8745c837ab63e80abd27_GovernanceLeftoverExchanger.sol
- Contracts: is, Context, Ownable, setting, without, without, to, GovernanceLeftoverExchanger
- Libraries: instead, SafeMath, UniERC20
- External call examples:
  - `address msgSender = _msgSender();`
  - `_owner = address(0);`
  - `IERC20 private constant _ETH_ADDRESS = IERC20(0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE);`
  - `IERC20 private constant _ZERO_ADDRESS = IERC20(0);`
  - `uint256 startGas = gasleft();`

### df56130421afc85431af6b3451a9336377e5fb0c_BountyClaim.sol
- Contracts: has, Ownable, to, without, to, to, ERC20, BountyClaim
- Libraries: None
- External call examples:
  - `owner = address(0);`

### e50b077ecaf6105a70f992fa83b0fdc6a062a349_BabyDogeDoo.sol
- Contracts: Context, Ownable, BabyDogeDoo
- Libraries: SafeMath, Address
- External call examples:
  - `address msgSender = _msgSender();`
  - `_owner = address(0);`
  - `uint256 currentRate =  _getRate();`
  - `uint256 contractTokenBalance = balanceOf(address(this));`
  - `uint256 contractETHBalance = address(this).balance;`

### e77e59e5d9db886b54ec609d0e0add13fe358fba_x00ts.sol
- Contracts: is, Context, Ownable, setting, without, without, to, to, interfaces, implements, recipients, that, via, in, will, lived, must, and, ERC165, Owneable, ERC721A, x00ts, for, OwnableDelegateProxy, ProxyRegistry
- Libraries: Address, Strings
- External call examples:
  - `_currentIndex = _startTokenId();`
  - `string memory baseURI = _baseURI();`
  - `_ownerships[startTokenId].startTimestamp = uint64(block.timestamp);`
  - `TokenOwnership memory prevOwnership = ownershipOf(tokenId);`
  - `_ownerships[tokenId].startTimestamp = uint64(block.timestamp);`

### ed2f35867a1afc19eeff7f0fbd7cd30c0c8c288a_Etheropoly.sol
- Contracts: accepting, to, AcceptsEtheropoly, Etheropoly, will, uint256, approved, if, function, is, that
- Libraries: SafeMath
- External call examples:
  - `tokenContract = Etheropoly(_tokenContract);`
  - `uint256 _dividends = myDividends(false); // retrieve ref. bonus later in the code`
  - `uint256 _tokens = purchaseTokens(_dividends, 0x0);`
  - `uint256 _dividends = myDividends(false); // get ref. bonus later in the code`
  - `uint256 _ethereum = tokensToEthereum_(_tokens);`

### f441b73b0a196aa67d32aee230aab5e54eef4765_RegionsToken.sol
- Contracts: ERC721, RegionsToken, owner, if, code, calls, function
- Libraries: SafeMath
- External call examples:
  - `uint256 tokenCount = balanceOf(_owner);`
  - `uint256 totalRegions = totalSupply();`
  - `Region memory _region = Region({
      name: _name
    });`

### fed8dfb896ff7081851c56a2652240568d2c513f_PreICO.sol
- Contracts: has, Ownable, to, to, PreICO, and, but
- Libraries: SafeMath
- External call examples:
  - `token = Token(_tokenAddr);`
  - `* @dev API interface for interacting with the WILD Token contract`
  - `interface Token {`

## Compatible Contracts

| No | File | Contracts | Libraries |
|-----|------|-----------|------------|
| 1 | 4bdde1e9fbaef2579dd63e2abbf0be445ab93f10_CityMayor | CityMayor | SafeMath |
