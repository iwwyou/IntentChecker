# DomainNotes

target_contracts (RQ1 등) 데이터셋의 컨트랙트를 이해하는 데 필요한 **도메인 배경지식**을 정리하는 공간.
Web3Bugs/Numscout 등은 "버그가 있는 컨트랙트 데이터셋"이고, 여기는 그 컨트랙트를 읽기 위해 필요한
"금융/프로토콜 개념 설명"을 모아둔다.

## 구조

```
DomainNotes/
  <Topic>/
    README.md              해당 토픽의 개념 정리 (일반 배경지식, 특정 파일에 종속되지 않음)
    contracts/
      <파일명>.md           그 토픽에 속하는 개별 컨트랙트의 함수/변수별 설명
```

## 토픽 목록

- [Perpetual_Futures](Perpetual_Futures/README.md) — 퍼페추얼 스왑(무기한 선물), Tracer Protocol
  - contracts: [web3bugs_16_H_04_Balances.md](Perpetual_Futures/contracts/web3bugs_16_H_04_Balances.md)
- [Yield_Farming](Yield_Farming/README.md) — 스테이킹 보상 분배(MasterChef 패턴)
  - contracts: [web3bugs_83_H_01_MasterChef.md](Yield_Farming/contracts/web3bugs_83_H_01_MasterChef.md)
- [CDP_Stablecoin_Vault](CDP_Stablecoin_Vault/README.md) — 담보 기반 스테이블코인 발행(CDP), Mochi.Fi
  - contracts: [web3bugs_42_H_01_MochiVault.md](CDP_Stablecoin_Vault/contracts/web3bugs_42_H_01_MochiVault.md)
- [Cross_Margin_Trading](Cross_Margin_Trading/README.md) — 크로스 마진 거래/대출, Marginswap
  - contracts: [web3bugs_3_H_05_CrossMarginAccounts.md](Cross_Margin_Trading/contracts/web3bugs_3_H_05_CrossMarginAccounts.md)
- [Concentrated_Liquidity_AMM](Concentrated_Liquidity_AMM/README.md) — 집중 유동성 AMM(틱 관리), SushiSwap Trident
  - contracts: [web3bugs_35_H_11_Ticks.md](Concentrated_Liquidity_AMM/contracts/web3bugs_35_H_11_Ticks.md)
