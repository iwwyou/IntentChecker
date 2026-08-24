# CDP(Collateralized Debt Position) / 스테이블코인 볼트 개념 정리

대상 프로토콜: **Mochi.Fi** — 담보를 맡기고 스테이블코인(USDM)을 발행(대출)받는 볼트. MakerDAO의 DAI 발행 구조와 유사.
관련 컨트랙트: [contracts/web3bugs_42_H_01_MochiVault.md](contracts/web3bugs_42_H_01_MochiVault.md) (`MochiVault`)

## 1. 개념: CDP란?

- 사용자가 담보(`asset`, 예: ETH)를 볼트에 맡기고, 그 담보 가치의 일부만큼 **스테이블코인(USDM)을 새로 발행**받아 가져간다.
- 이건 "빚(debt)"이며, 나중에 USDM을 갚으면(소각) 담보를 되찾는다.
- [Perpetual_Futures](../Perpetual_Futures/README.md)의 "레버리지 베팅"과 다르게, 여기선 **담보 대비 대출 비율(LTV, collateral factor)**을 넘지 않는 선에서 돈을 빌리는 것.
- **포지션이 NFT로 표현됨**: 포지션 id(`_id`)가 곧 NFT tokenId — 대출 포지션 자체를 양도 가능한 자산으로 다룸 (다른 두 도메인엔 없는 특징).

## 2. 핵심 개념: `debtIndex` (복리 이자 누적 지수)

모든 포지션을 순회하지 않고 이자를 반영하기 위한 표준 트릭 (Compound/Aave의 `borrowIndex`와 동일 원리).

- `debtIndex`는 시간이 지날수록 커지는 전역 지수 (1e18에서 시작)
- 개별 포지션의 실제 빚 = `저장된 debt × (전역 debtIndex / 그 포지션이 마지막으로 갱신됐을 때의 debtIndex)`
- 포지션을 건드릴 때(`updateDebt`/`wait` modifier)만 그 시점까지의 이자를 계산해서 반영

## 3. 흐름

1. `mint`로 새 포지션(NFT) 생성
2. `deposit`으로 담보 예치 (누구나 남의 포지션에 담보를 넣어줄 수 있음 — 소유자 체크 없음)
3. `borrow`로 USDM 대출 — 담보가치×collateralFactor를 넘지 않는 선에서, 0.5% 발행 수수료가 빚에 가산됨
4. `repay`로 USDM 상환(소각)
5. `withdraw`로 담보 인출 — 소유자만 가능, 예치 후 `delay`(대기시간) 지나야 함, 청산 안전선 재확인

## 4. 청산

`_liquidatable(collateral, price, debt)`: `담보가치 × liquidationFactor < 빚`이면 청산 가능.
지정된 `liquidator` 컨트랙트만 `liquidate()` 호출 가능.

## 5. 부가 기능: 플래시론 (ERC-3156)

이 볼트는 담보 자산에 대해 플래시론도 제공한다 (`flashLoan`, 수수료 0.1337% 고정).

## 비유 정리 (이전 도메인과 비교)

| 개념 | 이 컨트랙트 | Perpetual_Futures 비교 |
|---|---|---|
| 담보(`asset`) | 맡기는 자산 | quote 담보와 유사한 개념 |
| 빚(`debt`) | 담보 대비 발행받은 스테이블코인 | base 포지션과 다름 — 레버리지 베팅이 아니라 "대출" |
| 청산 판정 | `_liquidatable` | `marginIsValid`와 역할 동일 |
| 포지션 단위 | NFT (양도 가능) | Tracer는 계좌 매핑, NFT 아님 |
