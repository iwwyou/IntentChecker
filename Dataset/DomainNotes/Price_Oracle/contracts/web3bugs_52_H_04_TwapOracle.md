# web3bugs_52_H_04.sol — `TwapOracle`

원본 경로: `evaluation/RQ1/target_contracts_original/web3bugs_52_H_04.sol`
Vader Protocol의 TWAP+Chainlink 하이브리드 오라클. 개념 배경은 [../README.md](../README.md) 참고.

## 상태 변수

| 변수 | 의미 |
|---|---|
| `VADER`, `USDV` | 추적 대상 두 토큰 |
| `_usdvEnabled` | USDV 가격 산정 모드 on/off |
| `_aggregators[asset]` | 페어링 자산 → Chainlink 가격 피드 |
| `_vaderPool` | Vader 자체 AMM 풀 (USDV 페어에 사용) |
| `_updatePeriod` | TWAP 갱신 최소 경과 시간 |
| `_pairs` | 추적 중인 페어 목록 |
| `_pairExists` | 중복 등록 방지 해시맵 |

## `PairData` 구조체

```solidity
struct PairData {
    address pair; address token0; address token1;
    uint256 price0CumulativeLast; uint256 price1CumulativeLast;
    uint32 blockTimestampLast;
    FixedPoint.uq112x112 price0Average; FixedPoint.uq112x112 price1Average;
}
```

## 함수별 설명

- `pairExists(token0, token1)`: 두 순서 모두 해시 검사로 중복 확인
- `consult(token)`: `_pairs`에서 `token0==token`인 페어만 골라 TWAP 기반 자산량(`sumNative`) +
  Chainlink USD가(`sumUSD`)를 누적, 최종 USD 환산값 반환 — **버그 위치 (아래 참고)**
- `getRate()`: `consult(USDV) / consult(VADER)` → VADER↔USDV 환율
- `usdvtoVader` / `vaderToUsdv`: 환율 기반 상호 환산
- `initialize(_usdv, _vader)`: VADER/USDV 주소 최초 설정 (onlyOwner)
- `enableUSDV()`: `_usdvEnabled` on
- `registerAggregator(asset, aggregator)`: 자산별 Chainlink 피드 등록 (onlyOwner)
- `registerPair(factory, token0, token1)`: 새 페어 등록. `token0==VADER`면 Uniswap V2 팩토리,
  `token0==USDV`면 `_vaderPool` 사용 (onlyOwner)
- `update()`: 모든 페어의 TWAP 평균가 갱신, `_updatePeriod` 이상 경과 확인 (onlyOwner)

## ✅ 확인된 취약점 — `consult()` 156번째 줄 (Code4rena #52 H-04, sponsor-confirmed)

```solidity
result = ((sumUSD * IERC20Metadata(token).decimals()) / sumNative);
```

- 의도: `sumUSD × 10^decimals / sumNative` (USD 환산치를 토큰 소수점 단위로 스케일업)
- 실제: `10^decimals` 대신 **decimals 원시값**(예: 18)을 곱함
- VADER/USDV 모두 OpenZeppelin 기본 `decimals()=18`을 사용하므로, 의도한 `10^18`배 대신
  `18`배만 곱해져 **약 10^16~10^17배 축소된 완전히 틀린 결과**
- 올바른 코드:
  ```solidity
  uint256 scalingFactor = 10 ** IERC20Metadata(token).decimals();
  result = (sumUSD * scalingFactor) / sumNative;
  ```
- 영향: `getRate()` → `usdvtoVader`/`vaderToUsdv` → `Vader.sol` 민팅 로직까지 전파되어 High 등급.
  프로토콜팀 응답: "TWAP 오라클 모듈을 처음부터 다시 설계함" (부분 패치가 아니라 전면 재작성).
