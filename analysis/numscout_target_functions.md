# NumScout 95개 데이터셋 타겟 함수 분석

## 전체 통계

- 총 Contract 수: 95
- 취약점 발견된 Contract 수: 34

## 취약점 유형별 통계

### indivisible_amount
- 발견 횟수: 19
- 영향받은 Contract:
  - **04e5e1a11f92be3560bf58a76723e6fe4dc09abd_DODO.solDODO** (04e5e1a11f92be3560bf58a76723e6fe4dc09abd_DODO.solDODO)
    - 타겟 함수: require, payable
  - **05fc938cc60fb71381514877d66478bab7e2e1ce_SUPERCATS.solSUPERCATS** (05fc938cc60fb71381514877d66478bab7e2e1ce_SUPERCATS.solSUPERCATS)
    - 타겟 함수: require, payable
  - **08892eebfad12c909c0cb15ebea385ec997ce1ef_MegaBull.solMegaBull** (08892eebfad12c909c0cb15ebea385ec997ce1ef_MegaBull.solMegaBull)
    - 타겟 함수: sendETHToTeam, if, div, swapTokensForEth, _transfer, tokenFromReflection, balanceOf, _getCurrentSupply, _approve, transfer, _getRate, swapExactTokensForETHSupportingFeeOnTransferTokens
  - **0e90b59e6b1f28d89a647f3224e24af44e824baf_UshiOni.solUshiOni** (0e90b59e6b1f28d89a647f3224e24af44e824baf_UshiOni.solUshiOni)
    - 타겟 함수: if, address, swapExactTokensForETHSupportingFeeOnTransferTokens, checkTxLimit, mul, payable, sub, getLiquidityBacking, isOverLiquified, _transferFrom
  - **38195c86c5a32af913f05ba2c82e4c07fdeb2427_eKISHU.soleKISHU** (38195c86c5a32af913f05ba2c82e4c07fdeb2427_eKISHU.soleKISHU)
    - 타겟 함수: require, sendETHToFee, transfer
  - **3c1634291868ddffa037222991babfccd8400921_ParsecCrowdsale.solParsecCrowdsale** (3c1634291868ddffa037222991babfccd8400921_ParsecCrowdsale.solParsecCrowdsale)
    - 타겟 함수: div, calculateReward, mul, addAcceptedContribution, sub, add, transfer
  - **47e661f80a5fecb42137c97ecd910e2436f3ccad_Shibbit.solShibbit** (47e661f80a5fecb42137c97ecd910e2436f3ccad_Shibbit.solShibbit)
    - 타겟 함수: require, sendETHToFee, transfer
  - **4bdde1e9fbaef2579dd63e2abbf0be445ab93f10_CityMayor.solCityMayor** (4bdde1e9fbaef2579dd63e2abbf0be445ab93f10_CityMayor.solCityMayor)
    - 타겟 함수: sub, address
  - **4E0fCa55a6C3A94720ded91153A27F60E26B9AA8_BoostToken.solBoostToken** (4E0fCa55a6C3A94720ded91153A27F60E26B9AA8_BoostToken.solBoostToken)
    - 타겟 함수: sendETHToTeam, if, div, swapTokensForEth, _transfer, tokenFromReflection, balanceOf, _getCurrentSupply, _approve, sub, transfer, _getRate, swapExactTokensForETHSupportingFeeOnTransferTokens
  - **63278489e04Cd2224DAa4e425E57282135db7Af3_Konnichiwa.solKonnichiwa** (63278489e04Cd2224DAa4e425E57282135db7Af3_Konnichiwa.solKonnichiwa)
    - 타겟 함수: require, sendETHToFee, transfer
  - **638a3d66e4a6a6db13fae6050b36f7067ccaacf9_FusionSSJ2.solFusionSSJ2** (638a3d66e4a6a6db13fae6050b36f7067ccaacf9_FusionSSJ2.solFusionSSJ2)
    - 타겟 함수: require, sendETHToFee, transfer
  - **6Fb259f21359E740e6a96Be095f81212A80e831e_DICKEY.solDICKEY** (6Fb259f21359E740e6a96Be095f81212A80e831e_DICKEY.solDICKEY)
    - 타겟 함수: require, sendETHToFee, mul, payable
  - **7b8741bd212b4f2d0a1b53008670d2b0174a1cd9_HYPERLOOP.solHYPERLOOP** (7b8741bd212b4f2d0a1b53008670d2b0174a1cd9_HYPERLOOP.solHYPERLOOP)
    - 타겟 함수: sendETHToTeam, if, div, swapTokensForEth, _transfer, tokenFromReflection, balanceOf, _getCurrentSupply, _approve, transfer, _getRate, swapExactTokensForETHSupportingFeeOnTransferTokens
  - **84b7d95165328d790a34cc5d7ecf528be55c65ed_DiceGame.solDiceGame** (84b7d95165328d790a34cc5d7ecf528be55c65ed_DiceGame.solDiceGame)
    - 타겟 함수: safeSendFunds, sub, getDiceWinAmount, if
  - **9e86f530866bf7b3e8b23e613495c696f713c3c9_PapaFloki.solPapaFloki** (9e86f530866bf7b3e8b23e613495c696f713c3c9_PapaFloki.solPapaFloki)
    - 타겟 함수: sendETHToTeam, if, div, swapTokensForEth, _transfer, tokenFromReflection, balanceOf, _getCurrentSupply, _approve, transfer, _getRate, swapExactTokensForETHSupportingFeeOnTransferTokens
  - **acf999bfa9347e8ebe6816ed30bf44b127233177_AXNETDEX.solAXNETDEX** (acf999bfa9347e8ebe6816ed30bf44b127233177_AXNETDEX.solAXNETDEX)
    - 타겟 함수: safeSub, assert, safeMul, safeAdd
  - **af83df4264395f7082639db543cdbca3cc9a477c_TheVerdyctResurgence.solTheVerdyctResurgence** (af83df4264395f7082639db543cdbca3cc9a477c_TheVerdyctResurgence.solTheVerdyctResurgence)
    - 타겟 함수: payable
  - **cfc49b91cc35f6ff7c209f7c070bf6e1b66fb151_DOODL.solDOODL** (cfc49b91cc35f6ff7c209f7c070bf6e1b66fb151_DOODL.solDOODL)
    - 타겟 함수: if, div, swapTokensForEth, _transfer, tokenFromReflection, balanceOf, _getCurrentSupply, _approve, sendETHToCharity, transfer, _getRate, swapExactTokensForETHSupportingFeeOnTransferTokens
  - **e50b077ecaf6105a70f992fa83b0fdc6a062a349_BabyDogeDoo.solBabyDogeDoo** (e50b077ecaf6105a70f992fa83b0fdc6a062a349_BabyDogeDoo.solBabyDogeDoo)
    - 타겟 함수: if, div, swapTokensForEth, _transfer, tokenFromReflection, balanceOf, _getCurrentSupply, _approve, sub, transfer, sendETHToFee, _getRate, swapExactTokensForETHSupportingFeeOnTransferTokens

### operator_order_issue
- 발견 횟수: 7
- 영향받은 Contract:
  - **0e90b59e6b1f28d89a647f3224e24af44e824baf_UshiOni.solUshiOni** (0e90b59e6b1f28d89a647f3224e24af44e824baf_UshiOni.solUshiOni)
    - 타겟 함수: if, div, address, add, checkTxLimit, sub, Transfer, shouldTakeFee, _transferFrom
  - **259562c54c07aca61e12ee12c62016eaf3fd7852_Nokon.solNokon** (259562c54c07aca61e12ee12c62016eaf3fd7852_Nokon.solNokon)
    - 타겟 함수: calculateRate, balanceOf, buy, Transfer
  - **4E0fCa55a6C3A94720ded91153A27F60E26B9AA8_BoostToken.solBoostToken** (4E0fCa55a6C3A94720ded91153A27F60E26B9AA8_BoostToken.solBoostToken)
    - 타겟 함수: sendETHToTeam, if, div, swapTokensForEth, _transfer, tokenFromReflection, balanceOf, _getCurrentSupply, _approve, sub, transfer, _getRate, swapExactTokensForETHSupportingFeeOnTransferTokens
  - **6a40f8b2c7e6eb5bacbd52bc055e230d00168669_CharlieCoin.solCharlieCoin** (6a40f8b2c7e6eb5bacbd52bc055e230d00168669_CharlieCoin.solCharlieCoin)
    - 타겟 함수: if, div, myDividends, transfer, dividendsOf, tokensToEthereum_, balanceOf, sub, add, require, withdraw
  - **6a57883b5748bf3631ac2e0d43bf0d6f6cbcd16b_LescoinPreSale.solLescoinPreSale** (6a57883b5748bf3631ac2e0d43bf0d6f6cbcd16b_LescoinPreSale.solLescoinPreSale)
    - 타겟 함수: transfer
  - **7e2adafce6033c1272708b58aeab1164017417d2_CryptoflipCar.solCryptoflipCar** (7e2adafce6033c1272708b58aeab1164017417d2_CryptoflipCar.solCryptoflipCar)
    - 타겟 함수: transfer, div, mul
  - **85a3248fd8d750a80d5df3abb0c933bdd9a8396a_POWHF.solPOWHF** (85a3248fd8d750a80d5df3abb0c933bdd9a8396a_POWHF.solPOWHF)
    - 타겟 함수: if, div, myDividends, transfer, dividendsOf, tokensToEthereum_, balanceOf, sub, add, require, withdraw

### div_in_path
- 발견 횟수: 7
- 영향받은 Contract:
  - **122ad2495b1af2a14c5c4b4ca59adfcd79c2dcb3_GameTime.solGameTime** (122ad2495b1af2a14c5c4b4ca59adfcd79c2dcb3_GameTime.solGameTime)
    - 타겟 함수: _transferTaxes, if, _transfer, _update, Transfer
  - **39da420ac0d9a6d8e05c5d9acac75377decfbb42_WANGMI.solWANGMI** (39da420ac0d9a6d8e05c5d9acac75377decfbb42_WANGMI.solWANGMI)
    - 타겟 함수: if, _setBlacklist, mul, add, require
  - **926476bfc3550ccb424202004b9aab9ac40e32de_VeChainX.solVeChainX** (926476bfc3550ccb424202004b9aab9ac40e32de_VeChainX.solVeChainX)
    - 타겟 함수: if, mul, getTokens
  - **9BAcb4E17328d11b334dA6d48BEC3EC55CEC0858_dAvInci.soldAvInci** (9BAcb4E17328d11b334dA6d48BEC3EC55CEC0858_dAvInci.soldAvInci)
    - 타겟 함수: owner, balanceOf, if
  - **a74642aeae3e2fd79150c910eb5368b64f864b1e_Mobius2D.solMobius2D** (a74642aeae3e2fd79150c910eb5368b64f864b1e_Mobius2D.solMobius2D)
    - 타겟 함수: if, _updateReturns, _purchase, buyShares, mul, _disburseReturns, _outstandingReturns, sub, add, _splitRevenue, _airDrop, wmul
  - **bc40fad0b36faeb1595aa90d4136d01c08c99092_AINU.solAINU** (bc40fad0b36faeb1595aa90d4136d01c08c99092_AINU.solAINU)
    - 타겟 함수: if, _calculateTax, balanceOf, require, _transferFrom
  - **d546551924a883b604d4127b0af309c95ba9ba6d_UberDelta.solUberDelta** (d546551924a883b604d4127b0af309c95ba9ba6d_UberDelta.solUberDelta)
    - 타겟 함수: if, getHash, safeSub, safeDiv, safeMul

### exchange_problem
- 발견 횟수: 3
- 영향받은 Contract:
  - **259562c54c07aca61e12ee12c62016eaf3fd7852_Nokon.solNokon** (259562c54c07aca61e12ee12c62016eaf3fd7852_Nokon.solNokon)
    - 타겟 함수: calculateRate, balanceOf, buy, Transfer
  - **2af6139c39c05e0597c0ac12c60b303c38aa69e7_HIT.solHIT** (2af6139c39c05e0597c0ac12c60b303c38aa69e7_HIT.solHIT)
    - 타겟 함수: distr, Transfer, sub, add, getTokens
  - **6a57883b5748bf3631ac2e0d43bf0d6f6cbcd16b_LescoinPreSale.solLescoinPreSale** (6a57883b5748bf3631ac2e0d43bf0d6f6cbcd16b_LescoinPreSale.solLescoinPreSale)
    - 타겟 함수: transfer

### exchange_rounding
- 발견 횟수: 3
- 영향받은 Contract:
  - **259562c54c07aca61e12ee12c62016eaf3fd7852_Nokon.solNokon** (259562c54c07aca61e12ee12c62016eaf3fd7852_Nokon.solNokon)
    - 타겟 함수: calculateRate, balanceOf, buy, Transfer
  - **2af6139c39c05e0597c0ac12c60b303c38aa69e7_HIT.solHIT** (2af6139c39c05e0597c0ac12c60b303c38aa69e7_HIT.solHIT)
    - 타겟 함수: distr, Transfer, sub, add, getTokens
  - **6a57883b5748bf3631ac2e0d43bf0d6f6cbcd16b_LescoinPreSale.solLescoinPreSale** (6a57883b5748bf3631ac2e0d43bf0d6f6cbcd16b_LescoinPreSale.solLescoinPreSale)
    - 타겟 함수: transfer

### profit_opportunity
- 발견 횟수: 1
- 영향받은 Contract:
  - **2af6139c39c05e0597c0ac12c60b303c38aa69e7_HIT.solHIT** (2af6139c39c05e0597c0ac12c60b303c38aa69e7_HIT.solHIT)
    - 타겟 함수: distr, Transfer, sub, add, getTokens

### precision_loss_trend
- 발견 횟수: 3
- 영향받은 Contract:
  - **2f0b287275Fc50a1Cb854797927A12a98d3b9460_EthereumGod.solEthereumGod** (2f0b287275Fc50a1Cb854797927A12a98d3b9460_EthereumGod.solEthereumGod)
    - 타겟 함수: if, div, addLiquidity, balanceOf, _approve, swapAndLiquify, add, _getRate, _transfer, sendETHToMarketing, mul, tokenFromReflection, sub, transfer, swapTokensForEth, address, owner, _getCurrentSupply, swapExactTokensForETHSupportingFeeOnTransferTokens
  - **7e2adafce6033c1272708b58aeab1164017417d2_CryptoflipCar.solCryptoflipCar** (7e2adafce6033c1272708b58aeab1164017417d2_CryptoflipCar.solCryptoflipCar)
    - 타겟 함수: transfer
  - **bfBa224810655e7B5D94190700768fa8aBDB9eAa_HippoHotel.solHippoHotel** (bfBa224810655e7B5D94190700768fa8aBDB9eAa_HippoHotel.solHippoHotel)
    - 타겟 함수: payable, mul

## 전체 Contract 목록

| No | Contract | File | Defect Types | Target Functions | Public Functions |
|-----|----------|------|--------------|------------------|------------------|
| 1 | 04e5e1a11f92be3560bf58a76723e6fe4dc09abd_DODO.solDODO | 04e5e1a11f92be3560bf58a76723e6... | indivisible_amount | payable, require... | 45 |
| 2 | 05fc938cc60fb71381514877d66478bab7e2e1ce_SUPERCATS.solSUPERCATS | 05fc938cc60fb71381514877d66478... | indivisible_amount | payable, require... | 68 |
| 3 | 084dd52ae071e0de931d6323289ca555597a3e09_UnfoldedByBrunoCerasi.solUnfoldedByBrunoCerasi | 084dd52ae071e0de931d6323289ca5... | None | N/A... | 36 |
| 4 | 08892eebfad12c909c0cb15ebea385ec997ce1ef_MegaBull.solMegaBull | 08892eebfad12c909c0cb15ebea385... | indivisible_amount | _approve, _getCurrentSupply, _getRate, _transfer, ... | 39 |
| 5 | 0c6173feb70e6db560bc89ac014cb5d97583b111_KingOfTheHill.solKingOfTheHill | 0c6173feb70e6db560bc89ac014cb5... | None | N/A... | 47 |
| 6 | 0cfdcefa52aa2c0d11be4f9287243e2838470004_morgoblinz.solmorgoblinz | 0cfdcefa52aa2c0d11be4f9287243e... | None | N/A... | 34 |
| 7 | 0e90b59e6b1f28d89a647f3224e24af44e824baf_UshiOni.solUshiOni | 0e90b59e6b1f28d89a647f3224e24a... | operator_order_issue, indivisible_amount | Transfer, _transferFrom, add, address, checkTxLimi... | 40 |
| 8 | 0eDB29ef467C364F173bc0F6dA8237386303b107_OxBLACK.solOxBLACK | 0eDB29ef467C364F173bc0F6dA8237... | None | N/A... | 42 |
| 9 | 122ad2495b1af2a14c5c4b4ca59adfcd79c2dcb3_GameTime.solGameTime | 122ad2495b1af2a14c5c4b4ca59adf... | div_in_path | Transfer, _transfer, _transferTaxes, _update, if... | 19 |
| 10 | 1505c95a707348C2bCc75698BE258891387f008B_CROOGEToken.solCROOGEToken | 1505c95a707348C2bCc75698BE2588... | None | N/A... | 40 |
| 11 | 1543d0F83489e82A1344DF6827B23d541F235A50_AIgathaToken.solAIgathaToken | 1543d0F83489e82A1344DF6827B23d... | None | N/A... | 30 |
| 12 | 1de00bf682620fe9c026dfc0cba9116b2d73cc27_RETNIRP.solRETNIRP | 1de00bf682620fe9c026dfc0cba911... | None | N/A... | 55 |
| 13 | 206c5c55087ac1f38f50ee151e547f9e42ae7cb8_GOdHatesNFTsTooWTF.solGOdHatesNFTsTooWTF | 206c5c55087ac1f38f50ee151e547f... | None | N/A... | 43 |
| 14 | 20c3811a83fad33dc7a0c8ee2d1e773ddf3b7d44_Damo.solDamo | 20c3811a83fad33dc7a0c8ee2d1e77... | None | N/A... | 26 |
| 15 | 20e2bf0fc47e65a3caa5e8e17c5cd730cc556db9_AirDrop.solAirDrop | 20e2bf0fc47e65a3caa5e8e17c5cd7... | None | N/A... | 3 |
| 16 | 259562c54c07aca61e12ee12c62016eaf3fd7852_Nokon.solNokon | 259562c54c07aca61e12ee12c62016... | operator_order_issue, exchange_problem, exchange_rounding | Transfer, balanceOf, buy, calculateRate... | 19 |
| 17 | 278cdd6847ef830c23cac61c17eab837fea1c29a_Bridge.solBridge | 278cdd6847ef830c23cac61c17eab8... | None | N/A... | 39 |
| 18 | 2af6139c39c05e0597c0ac12c60b303c38aa69e7_HIT.solHIT | 2af6139c39c05e0597c0ac12c60b30... | exchange_problem, exchange_rounding, profit_opportunity | Transfer, add, distr, getTokens, sub... | 21 |
| 19 | 2bd29df7a7fe49faf49cc96f75582297c9ac1edd_MultiVaultCapital.solMultiVaultCapital | 2bd29df7a7fe49faf49cc96f755822... | None | N/A... | 58 |
| 20 | 2f0b287275Fc50a1Cb854797927A12a98d3b9460_EthereumGod.solEthereumGod | 2f0b287275Fc50a1Cb854797927A12... | precision_loss_trend | _approve, _getCurrentSupply, _getRate, _transfer, ... | 38 |
| 21 | 30f938fed5de6e06a9a7cd2ac3517131c317b1e7_GivethBridge.solGivethBridge | 30f938fed5de6e06a9a7cd2ac35171... | None | N/A... | 41 |
| 22 | 34aF60BD2447Aa7F49920200F072667A5FEb29cf_SONIC.solSONIC | 34aF60BD2447Aa7F49920200F07266... | None | N/A... | 28 |
| 23 | 37784637e421ea5abc9f3917d65d0257a1ea2d0a_MoonDoodleApeBabyBukakiTownwtf.solMoonDoodleApeBabyBukakiTownwtf | 37784637e421ea5abc9f3917d65d02... | None | N/A... | 38 |
| 24 | 38195c86c5a32af913f05ba2c82e4c07fdeb2427_eKISHU.soleKISHU | 38195c86c5a32af913f05ba2c82e4c... | indivisible_amount | require, sendETHToFee, transfer... | 18 |
| 25 | 39da420ac0d9a6d8e05c5d9acac75377decfbb42_WANGMI.solWANGMI | 39da420ac0d9a6d8e05c5d9acac753... | div_in_path | _setBlacklist, add, if, mul, require... | 47 |
| 26 | 3c1634291868ddffa037222991babfccd8400921_ParsecCrowdsale.solParsecCrowdsale | 3c1634291868ddffa037222991babf... | indivisible_amount | add, addAcceptedContribution, calculateReward, div... | 51 |
| 27 | 3d3097cd94fec5dc823e5025a59438e63757dc79_PLASMA.solPLASMA | 3d3097cd94fec5dc823e5025a59438... | None | N/A... | 74 |
| 28 | 43d3cc4439d2ac6fb93032004f6c094a5c21b185_PRESALE.solPRESALE | 43d3cc4439d2ac6fb93032004f6c09... | None | N/A... | 44 |
| 29 | 44bB2a074C58e160fc86eFC395B6dFD3592E7620_The401kProtocol.solThe401kProtocol | 44bB2a074C58e160fc86eFC395B6dF... | None | N/A... | 57 |
| 30 | 47e661f80a5fecb42137c97ecd910e2436f3ccad_Shibbit.solShibbit | 47e661f80a5fecb42137c97ecd910e... | indivisible_amount | require, sendETHToFee, transfer... | 28 |
| 31 | 482cf6a9d6b23452c81d4d0f0f139c1414963f89_EpicPackFour.solEpicPackFour | 482cf6a9d6b23452c81d4d0f0f139c... | None | N/A... | 32 |
| 32 | 4E0fCa55a6C3A94720ded91153A27F60E26B9AA8_BoostToken.solBoostToken | 4E0fCa55a6C3A94720ded91153A27F... | operator_order_issue, indivisible_amount | _approve, _getCurrentSupply, _getRate, _transfer, ... | 48 |
| 33 | 4bdde1e9fbaef2579dd63e2abbf0be445ab93f10_CityMayor.solCityMayor | 4bdde1e9fbaef2579dd63e2abbf0be... | indivisible_amount | address, sub... | 39 |
| 34 | 563b7591e1312638ba664a1358c93be8d0363318_WCI2.solWCI2 | 563b7591e1312638ba664a1358c93b... | None | N/A... | 29 |
| 35 | 5eee354e36ac51e9d3f7283005cab0c55f423b23_ArbitrageETHStaking.solArbitrageETHStaking | 5eee354e36ac51e9d3f7283005cab0... | None | N/A... | 8 |
| 36 | 5f561f52a49eb243910bf0471d692d6908def385_UndeadApeYachtClub.solUndeadApeYachtClub | 5f561f52a49eb243910bf0471d692d... | None | N/A... | 48 |
| 37 | 60c817c0489681d67206a7b82593adb7ef6c63ff_VBHC.solVBHC | 60c817c0489681d67206a7b82593ad... | None | N/A... | 72 |
| 38 | 63278489e04Cd2224DAa4e425E57282135db7Af3_Konnichiwa.solKonnichiwa | 63278489e04Cd2224DAa4e425E5728... | indivisible_amount | require, sendETHToFee, transfer... | 31 |
| 39 | 638a3d66e4a6a6db13fae6050b36f7067ccaacf9_FusionSSJ2.solFusionSSJ2 | 638a3d66e4a6a6db13fae6050b36f7... | indivisible_amount | require, sendETHToFee, transfer... | 17 |
| 40 | 6Fb259f21359E740e6a96Be095f81212A80e831e_DICKEY.solDICKEY | 6Fb259f21359E740e6a96Be095f812... | indivisible_amount | mul, payable, require, sendETHToFee... | 35 |
| 41 | 6a40f8b2c7e6eb5bacbd52bc055e230d00168669_CharlieCoin.solCharlieCoin | 6a40f8b2c7e6eb5bacbd52bc055e23... | operator_order_issue | add, balanceOf, div, dividendsOf, if, myDividends,... | 28 |
| 42 | 6a57883b5748bf3631ac2e0d43bf0d6f6cbcd16b_LescoinPreSale.solLescoinPreSale | 6a57883b5748bf3631ac2e0d43bf0d... | operator_order_issue, exchange_problem, exchange_rounding | transfer... | 13 |
| 43 | 6bd50f3589916783b5366262d51700ee81d31b7e_Marijuana.solMarijuana | 6bd50f3589916783b5366262d51700... | None | N/A... | 26 |
| 44 | 6c0a168a96a454f8fb589327960c5ab745cca9e0_MMB.solMMB | 6c0a168a96a454f8fb589327960c5a... | None | N/A... | 41 |
| 45 | 6c8dce6d842e0d9d109dc4c69f35cf8904fc4cbf_EtheremonEnergy.solEtheremonEnergy | 6c8dce6d842e0d9d109dc4c69f35cf... | None | N/A... | 21 |
| 46 | 6db943251e4126f913e9733821031791e75df713_ReadyPlayerONE.solReadyPlayerONE | 6db943251e4126f913e97338210317... | None | N/A... | 36 |
| 47 | 6eb4848979be3159ebd55f2d0626b95ff9e7a555_AlphaUndergroundNFT.solAlphaUndergroundNFT | 6eb4848979be3159ebd55f2d0626b9... | None | N/A... | 33 |
| 48 | 768864b2c8e9e15ec91be1db124469f861cfd2c2_RatScam.solRatScam | 768864b2c8e9e15ec91be1db124469... | None | N/A... | 33 |
| 49 | 7Ed850d831dd56b3224647eDF5622835d48c54A4_ElonRogan.solElonRogan | 7Ed850d831dd56b3224647eDF56228... | None | N/A... | 56 |
| 50 | 7b8741bd212b4f2d0a1b53008670d2b0174a1cd9_HYPERLOOP.solHYPERLOOP | 7b8741bd212b4f2d0a1b53008670d2... | indivisible_amount | _approve, _getCurrentSupply, _getRate, _transfer, ... | 39 |
| 51 | 7e2adafce6033c1272708b58aeab1164017417d2_CryptoflipCar.solCryptoflipCar | 7e2adafce6033c1272708b58aeab11... | operator_order_issue, precision_loss_trend | div, mul, transfer... | 24 |
| 52 | 80169091AAF83C82bb36469db6dAB14c013a0Ef4_GE.solGE | 80169091AAF83C82bb36469db6dAB1... | None | N/A... | 40 |
| 53 | 804b3d28e02e8820a8aaa8b23fc01b87028674eb_HirakiGenesis.solHirakiGenesis | 804b3d28e02e8820a8aaa8b23fc01b... | None | N/A... | 42 |
| 54 | 819Bb9964B6eBF52361F1ae42CF4831B921510f9_V00_Marketplace.solV00_Marketplace | 819Bb9964B6eBF52361F1ae42CF483... | None | N/A... | 30 |
| 55 | 84b7d95165328d790a34cc5d7ecf528be55c65ed_DiceGame.solDiceGame | 84b7d95165328d790a34cc5d7ecf52... | indivisible_amount | getDiceWinAmount, if, safeSendFunds, sub... | 24 |
| 56 | 85a3248fd8d750a80d5df3abb0c933bdd9a8396a_POWHF.solPOWHF | 85a3248fd8d750a80d5df3abb0c933... | operator_order_issue | add, balanceOf, div, dividendsOf, if, myDividends,... | 20 |
| 57 | 86c423d5f9396a9d6268d47203b3806028778f51_BLUECHIPBONDS.solBLUECHIPBONDS | 86c423d5f9396a9d6268d47203b380... | None | N/A... | 61 |
| 58 | 926476bfc3550ccb424202004b9aab9ac40e32de_VeChainX.solVeChainX | 926476bfc3550ccb424202004b9aab... | div_in_path | getTokens, if, mul... | 23 |
| 59 | 9950f678fbc0152c7b325091f3c6693ee524a32d_Bullrunners10000.solBullrunners10000 | 9950f678fbc0152c7b325091f3c669... | None | N/A... | 36 |
| 60 | 9BAcb4E17328d11b334dA6d48BEC3EC55CEC0858_dAvInci.soldAvInci | 9BAcb4E17328d11b334dA6d48BEC3E... | div_in_path | balanceOf, if, owner... | 73 |
| 61 | 9ddf4d7f5afa1bf0270b2719811324c2ac97480c_FOMOQuick.solFOMOQuick | 9ddf4d7f5afa1bf0270b2719811324... | None | N/A... | 36 |
| 62 | 9e86f530866bf7b3e8b23e613495c696f713c3c9_PapaFloki.solPapaFloki | 9e86f530866bf7b3e8b23e613495c6... | indivisible_amount | _approve, _getCurrentSupply, _getRate, _transfer, ... | 39 |
| 63 | Dd257067581Bb12d9D37C24bC7ad87Ee41db74B9_LOKLandSaleSecond.solLOKLandSaleSecond | Dd257067581Bb12d9D37C24bC7ad87... | None | N/A... | 37 |
| 64 | a068345a625542fe49c299c8df309a920a184200_CryptonToken.solCryptonToken | a068345a625542fe49c299c8df309a... | None | N/A... | 42 |
| 65 | a44e464b13280340904ffef0a65b8a0033460430_MyCryptoChampCore.solMyCryptoChampCore | a44e464b13280340904ffef0a65b8a... | None | N/A... | 38 |
| 66 | a74642aeae3e2fd79150c910eb5368b64f864b1e_Mobius2D.solMobius2D | a74642aeae3e2fd79150c910eb5368... | div_in_path | _airDrop, _disburseReturns, _outstandingReturns, _... | 48 |
| 67 | a8e7366031d493A0dF88A583196d092f80152029_Ribbits.solRibbits | a8e7366031d493A0dF88A583196d09... | None | N/A... | 36 |
| 68 | aaf740FD71093520C457642eb9219A4F6dA22190_ANON.solANON | aaf740FD71093520C457642eb9219A... | None | N/A... | 47 |
| 69 | acf999bfa9347e8ebe6816ed30bf44b127233177_AXNETDEX.solAXNETDEX | acf999bfa9347e8ebe6816ed30bf44... | indivisible_amount | assert, safeAdd, safeMul, safeSub... | 18 |
| 70 | af83df4264395f7082639db543cdbca3cc9a477c_TheVerdyctResurgence.solTheVerdyctResurgence | af83df4264395f7082639db543cdbc... | indivisible_amount | payable... | 43 |
| 71 | b14e960fe339588fe431dfd51859ed24f1b1c9e4_MOE.solMOE | b14e960fe339588fe431dfd51859ed... | None | N/A... | 51 |
| 72 | b1951924c2225527d712ed41bb6a9d9c0f543ea7_OUD.solOUD | b1951924c2225527d712ed41bb6a9d... | None | N/A... | 48 |
| 73 | b3af8d08975e5c6bc98cb2f8646e54539e2d8f0d_MultiSigWalletWithDailyLimit.solMultiSigWalletWithDailyLimit | b3af8d08975e5c6bc98cb2f8646e54... | None | N/A... | 26 |
| 74 | b98850497a59d8ed5c1b9d228969775de050409a_JungleMisfits.solJungleMisfits | b98850497a59d8ed5c1b9d22896977... | None | N/A... | 37 |
| 75 | bbc27ea7906a44207c175f81b8ae26e66bb1cec7_FivePenguins.solFivePenguins | bbc27ea7906a44207c175f81b8ae26... | None | N/A... | 36 |
| 76 | bc40fad0b36faeb1595aa90d4136d01c08c99092_AINU.solAINU | bc40fad0b36faeb1595aa90d4136d0... | div_in_path | _calculateTax, _transferFrom, balanceOf, if, requi... | 27 |
| 77 | bfBa224810655e7B5D94190700768fa8aBDB9eAa_HippoHotel.solHippoHotel | bfBa224810655e7B5D94190700768f... | precision_loss_trend | mul, payable... | 34 |
| 78 | c1ad0c738a9cd8d2fbaba66885493fe7961996e8_Goldensnitch.solGoldensnitch | c1ad0c738a9cd8d2fbaba66885493f... | None | N/A... | 46 |
| 79 | c31d5006c23bf21d3e9b007C542eFB6485BF081b_WorkandWork.solWorkandWork | c31d5006c23bf21d3e9b007C542eFB... | None | N/A... | 24 |
| 80 | cc37c96cd50b4ceaecc9fcea880d545f093ad3ef_EthernautsPreSale.solEthernautsPreSale | cc37c96cd50b4ceaecc9fcea880d54... | None | N/A... | 54 |
| 81 | cf8c23cf17bb5815d5705a15486fa83805415625_Polkadoge.solPolkadoge | cf8c23cf17bb5815d5705a15486fa8... | None | N/A... | 41 |
| 82 | cfc49b91cc35f6ff7c209f7c070bf6e1b66fb151_DOODL.solDOODL | cfc49b91cc35f6ff7c209f7c070bf6... | indivisible_amount | _approve, _getCurrentSupply, _getRate, _transfer, ... | 38 |
| 83 | d0a3b550b766c32b47cca3c332741f884f1599e4_GoblinBbys.solGoblinBbys | d0a3b550b766c32b47cca3c332741f... | None | N/A... | 35 |
| 84 | d4cd9a92a2cc1a864d67f1fd6279f73f5ec3a5f7_OwnershipClaimer.solOwnershipClaimer | d4cd9a92a2cc1a864d67f1fd6279f7... | None | N/A... | 14 |
| 85 | d546551924a883b604d4127b0af309c95ba9ba6d_UberDelta.solUberDelta | d546551924a883b604d4127b0af309... | div_in_path | getHash, if, safeDiv, safeMul, safeSub... | 70 |
| 86 | d792fe17cf634aeea2ef1d8c4eb076aaa34494aa_OKUNFTs.solOKUNFTs | d792fe17cf634aeea2ef1d8c4eb076... | None | N/A... | 42 |
| 87 | d91a26a93c10797b9d02c5595741b83704c874f4_BitcoinSapphire.solBitcoinSapphire | d91a26a93c10797b9d02c5595741b8... | None | N/A... | 26 |
| 88 | dcdb83e64147f613496e7e30acd47a2312437405_IllMND.solIllMND | dcdb83e64147f613496e7e30acd47a... | None | N/A... | 40 |
| 89 | dd9f24efc84d93deef3c8745c837ab63e80abd27_GovernanceLeftoverExchanger.solGovernanceLeftoverExchanger | dd9f24efc84d93deef3c8745c837ab... | None | N/A... | 6 |
| 90 | df56130421afc85431af6b3451a9336377e5fb0c_BountyClaim.solBountyClaim | df56130421afc85431af6b3451a933... | None | N/A... | 6 |
| 91 | e50b077ecaf6105a70f992fa83b0fdc6a062a349_BabyDogeDoo.solBabyDogeDoo | e50b077ecaf6105a70f992fa83b0fd... | indivisible_amount | _approve, _getCurrentSupply, _getRate, _transfer, ... | 20 |
| 92 | e77e59e5d9db886b54ec609d0e0add13fe358fba_x00ts.solx00ts | e77e59e5d9db886b54ec609d0e0add... | None | N/A... | 38 |
| 93 | ed2f35867a1afc19eeff7f0fbd7cd30c0c8c288a_Etheropoly.solEtheropoly | ed2f35867a1afc19eeff7f0fbd7cd3... | None | N/A... | 35 |
| 94 | f441b73b0a196aa67d32aee230aab5e54eef4765_RegionsToken.solRegionsToken | f441b73b0a196aa67d32aee230aab5... | None | N/A... | 26 |
| 95 | fed8dfb896ff7081851c56a2652240568d2c513f_PreICO.solPreICO | fed8dfb896ff7081851c56a2652240... | None | N/A... | 15 |
