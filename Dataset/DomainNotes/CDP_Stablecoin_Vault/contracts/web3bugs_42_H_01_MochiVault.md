# web3bugs_42_H_01.sol — `MochiVault`

원본 경로: `evaluation/RQ1/target_contracts_original/web3bugs_42_H_01.sol`
Mochi.Fi의 CDP 볼트 + ERC-3156 플래시론 제공자. 개념 배경은 [../README.md](../README.md) 참고.

## 상태 변수

| 변수 | 의미 |
|---|---|
| `CALLBACK_SUCCESS` | ERC-3156 플래시론 콜백 성공 매직값 |
| `engine` (immutable) | 오라클(`cssr`), 설정(`mochiProfile`), NFT, minter, liquidator, treasury 등을 모은 허브 컨트랙트 |
| `asset` | 이 볼트가 받는 담보 토큰 |
| `debtIndex` | 전역 이자 누적 지수 (1e18 시작) |
| `lastAccrued` | 마지막 전역 이자 정산 시각 |
| `deposits` | 볼트 전체 예치 담보 총량 |
| `debts` | 볼트 전체 미상환 부채(USDM 기준) |
| `claimable` | 프로토콜이 아직 회수 안 한 수수료 누적치 |
| `details[id]` | 포지션(NFT id)별 담보량/부채량/개인 debtIndex/상태/추천인 (`Detail` 구조체는 인터페이스에 정의) |
| `lastDeposit[id]` | 포지션별 마지막 예치 시각 (인출 대기시간 계산용) |

## Modifier

- `updateDebt(_id)`: 실행 전 `accrueDebt(_id)` 호출
- `wait(_id)`: `lastDeposit[_id] + delay <= now`여야 통과 — 예치 직후 인출 방지(플래시론/오라클 조작 방지)

## 함수별 설명

### `initialize(_asset)`
업그레이더블 초기화. 담보 자산 지정, `debtIndex=1e18`, `lastAccrued=now`.

### `liveDebtIndex()` / `currentDebt(_id)` (view)
저장 없이 "지금 정산한다면"의 지수/부채를 미리 계산.

### `accrueDebt(_id)`
1. 전역 정산: `debts`, `claimable`을 `currentIndex`로 갱신
2. 개별 정산 (`_id != type(uint256).max`이고 갱신 안 됐으면): 늘어난 부채 계산 후
   `engine.discountProfile().discount(ownerOf(_id))`로 일부 할인 적용, 할인분은 전역 `debts`/`claimable`에서 제외.

### `mint(_recipient, _referrer)`
새 포지션(NFT) 발행, `debtIndex` 초기화, 상태=`Idle`, 추천인 기록.

### `deposit(_id, _amount)`
담보 추가. **소유자 체크 없음**(누구나 남의 포지션에 담보 대신 예치 가능, 주석에 명시). `lastDeposit` 갱신, 담보량 증가.

### `withdraw(_id, _amount, _data)`
담보 인출. 소유자만 가능, `wait` modifier, 오라클 갱신 후 청산 안전선/최대대출한도 재확인 후 실행.

### `borrow(_id, _amount, _data)`
USDM 대출:
- 담보가치×`collateralFactor`로 최대 대출액 계산, 초과분은 잘라냄
- 자산별 전체 대출 한도(`creditCap`)도 재조정
- `increasingDebt = amount * 1005 / 1000` → **0.5% 발행 수수료**를 빚에 가산
- 최소 대출액 확인, 청산 안전선 재확인
- 수수료는 `mintFeeToPool`로 추천인 풀/트레저리에 발행
- 개인 `debtIndex`를 원금 변화에 맞춰 재조정(정규화)하는 트릭 적용
- USDM을 사용자에게 민팅

### `repay(_id, _amount)`
초과 상환분은 실제 빚만큼 잘림, USDM을 받아 **소각**, 완전 상환 시 상태를 `Collaterized`로 되돌림.

### `liquidate(_id, _collateral, _usdm)` / `_liquidatable` / `liquidatable(_id)`
지정된 liquidator만 청산 가능. `담보가치×liquidationFactor < 빚`이면 청산 가능.

### `claim()` / `mintFeeToPool(_amount, _referrer)`
`claimable`의 75%만 회수(25%는 리스크 대비 유보). 추천인 있으면 추천인 풀, 없으면 트레저리로 USDM 발행.

### 플래시론 (`maxFlashLoan`, `flashFee`, `flashLoan`)
ERC-3156 표준. 수수료 0.1337% 고정. 콜백이 `CALLBACK_SUCCESS`를 반환하고 원금+수수료를 갚지 않으면 전체 revert.
