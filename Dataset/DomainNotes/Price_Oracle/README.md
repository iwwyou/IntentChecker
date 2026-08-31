# 가격 오라클 (Price Oracle) 개념 정리

대상 프로토콜: **Vader Protocol**의 `TwapOracle` — TWAP(시간가중평균가격) + Chainlink 하이브리드 오라클.
관련 컨트랙트: [contracts/web3bugs_52_H_04_TwapOracle.md](contracts/web3bugs_52_H_04_TwapOracle.md) (`TwapOracle`)

## 1. 왜 오라클이 필요하고, TWAP은 뭔가?

- DeFi 프로토콜은 "이 토큰이 지금 USD로 얼마인지" 알아야 함 (담보평가, 스테이블코인 발행 등)
- **단순 스팟 가격의 문제**: AMM 풀의 "지금 이 순간" 가격을 그대로 읽으면, 플래시론으로 순간적으로
  가격을 왜곡시켜 오라클을 속이는 공격(오라클 조작)이 가능
- **TWAP(Time-Weighted Average Price)**: 한 순간이 아니라 **일정 시간 동안의 평균가**를 사용하면
  짧은 순간의 가격 조작으로는 평균을 크게 못 흔들어 훨씬 안전
- Uniswap V2는 블록마다 "누적 가격(cumulative price)"을 계속 더해 저장해두고, 두 시점의 누적값
  차이를 경과 시간으로 나눠 그 구간의 평균가를 계산하는 표준 패턴을 제공

## 2. Chainlink와의 결합

- Chainlink: 탈중앙화된 오프체인 데이터를 온체인으로 가져다주는 외부 오라클 네트워크
- 이 컨트랙트는 **"VADER/USDV 대비 페어링된 자산의 TWAP" × "그 자산의 Chainlink USD 가격"**을
  조합해서 VADER·USDV의 최종 USD 가치를 계산하는 하이브리드 구조

## 3. 핵심 흐름

1. `registerPair`로 추적할 페어 등록 (VADER는 일반 Uniswap V2 팩토리, USDV는 프로토콜 자체 풀 사용)
2. `update`로 주기적으로 누적가격 스냅샷을 갱신하고 TWAP 평균가(`price0Average`/`price1Average`) 계산
   — 최소 `_updatePeriod` 시간이 지나야만 갱신 가능(조작 방지)
3. `consult(token)`으로 등록된 페어들을 순회하며 TWAP 기반 자산량 × Chainlink USD가를 합산해 최종 USD 가치 산출
4. `getRate()`로 VADER↔USDV 환율 계산, `usdvtoVader`/`vaderToUsdv`로 상호 환산

## ✅ 확인된 취약점 (web3bugs H-04, sponsor-confirmed)

`consult()`의 마지막 스케일링 단계에서 `10**decimals()` 대신 **`decimals()` 원시값**을 곱함:

```solidity
result = ((sumUSD * IERC20Metadata(token).decimals()) / sumNative);  // 버그
// 올바름: result = (sumUSD * (10 ** decimals())) / sumNative;
```

VADER/USDV 둘 다 18 decimals이므로 의도한 `10^18`배 대신 `18`배만 곱해져 **~10^16배 축소된 완전히
틀린 결과**가 나옴. `getRate()` → 민팅 로직까지 영향을 미쳐 High로 평가됨. 프로토콜팀은 이 TWAP
오라클 모듈 자체를 전면 재설계함. 자세한 내용은
[contracts/web3bugs_52_H_04_TwapOracle.md](contracts/web3bugs_52_H_04_TwapOracle.md) 참고.
