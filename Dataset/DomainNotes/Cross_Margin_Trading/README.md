# 크로스 마진(Cross-Margin) 거래/대출 개념 정리

대상 프로토콜: **Marginswap** — 여러 토큰을 하나의 포트폴리오로 묶어 담보/대출을 관리하는 마진 거래 프로토콜.
관련 컨트랙트: [contracts/web3bugs_3_H_05_CrossMarginAccounts.md](contracts/web3bugs_3_H_05_CrossMarginAccounts.md) (`CrossMarginAccounts`)

## 1. 개념: 크로스 마진이란?

- 포지션 1개당 담보를 따로 관리하는 [Perpetual_Futures](../Perpetual_Futures/README.md)의 "isolated margin" 방식과 달리,
  **한 계좌 안의 여러 토큰(보유 + 대출)을 통째로 하나의 포트폴리오로 묶어서 건전성을 판단**한다.
- 사용자는 여러 종류의 토큰을 보유(holding)하면서 동시에 여러 종류의 토큰을 대출(borrow)할 수 있고,
  이를 모두 기준통화(`peg`)로 환산해 "전체 보유가치 vs 전체 빚"을 비교한다.
- 대출받은 토큰은 곧바로 계좌의 holdings에도 추가된다 — 빌린 돈이 포트폴리오의 일부가 되어 트레이딩에 쓰임.

## 2. 핵심 개념: `borrowedYieldQuotientsFP` (이자 스냅샷)

[CDP_Stablecoin_Vault](../CDP_Stablecoin_Vault/README.md)의 `debtIndex`와 동일한 원리.

- `Lending` 컨트랙트가 토큰별 전역 이자 지수를 관리
- 대출 시점의 지수를 스냅샷으로 저장
- 실제 빚 = `저장된 borrowed × (현재 전역 지수 / 스냅샷 지수)`로 계산, 건드릴 때만 정산

## 3. 흐름

1. `borrow`로 토큰 대출 → 대출액이 `holdings`에도 추가 → `positiveBalance`로 레버리지 한도 체크
2. `adjustAmounts`로 포트폴리오 내 토큰 교환(트레이드) 결과를 장부에 반영
3. `extinguishDebt`로 빚 상환
4. 청산 시 `deleteAccount`로 계좌 전체 초기화

## 4. 청산 판정

`loanInPeg` / `holdingsInPeg`로 전체 빚/보유자산을 peg 통화로 환산 후 비교.

## ⚠️ 관찰된 이슈 (web3bugs H-05와 연결)

`belowMaintenanceThreshold` 함수의 **이름과 실제 반환값이 반대로 보임**:

```solidity
// holdings / loan >= 1.1 (건전) 이면 true 반환
return 100 * holdings >= liquidationThresholdPercent * loan;
```

이름은 "유지증거금 아래(=청산 대상)"를 뜻해야 하는데, 실제로는 **건전할 때 true**를 반환한다.
호출부에서 이름 그대로 믿고 사용했다면 건전한 계좌를 청산하고 부실 계좌를 방치하는 정반대 결과가
날 수 있음. 자세한 내용은 [contracts/web3bugs_3_H_05_CrossMarginAccounts.md](contracts/web3bugs_3_H_05_CrossMarginAccounts.md) 참고.
