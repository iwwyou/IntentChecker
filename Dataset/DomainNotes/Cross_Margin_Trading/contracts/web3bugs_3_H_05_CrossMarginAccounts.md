# web3bugs_3_H_05.sol — `CrossMarginAccounts`

원본 경로: `evaluation/RQ1/target_contracts_original/web3bugs_3_H_05.sol`
Marginswap의 크로스 마진 회계 로직 (abstract contract, 상위 `MarginRouter` 등이 상속). 개념 배경은 [../README.md](../README.md) 참고.

## 구조체

```solidity
struct CrossMarginAccount {
    uint256 lastDepositBlock;
    address[] borrowTokens;
    mapping(address => uint256) borrowed;                 // 토큰별 대출량
    mapping(address => uint256) borrowedYieldQuotientsFP;  // 토큰별 이자 스냅샷
    address[] holdingTokens;
    mapping(address => uint256) holdings;                  // 토큰별 보유량
    mapping(address => bool) holdsToken;
}
```

## 상태 변수

| 변수 | 의미 |
|---|---|
| `leveragePercent` | 대출 한도 계산 기준 레버리지 |
| `liquidationThresholdPercent` | 청산 기준 (대출 대비 보유자산 비율) |
| `marginAccounts[address]` | 사용자별 계좌 |
| `tokenCaps[token]` | 토큰별 총 한도 |
| `totalShort[token]` / `totalLong[token]` | 토큰별 전체 대출합/보유합 |
| `coolingOffPeriod` | 입금 후 인출 대기 기간 |

## 함수별 설명

### `addHolding(account, token, amount)`
보유 토큰 목록에 없으면 추가, 보유량 증가.

### `borrow(account, borrowToken, borrowAmount)`
1. 기존 대출 있으면 이자 먼저 반영(`applyBorrowInterest`)
2. 이자 스냅샷을 현재 지수로 갱신
3. `borrowed` 증가, 대출액을 `holdings`에도 추가
4. `positiveBalance` 체크 실패 시 revert

### `positiveBalance(account)`
새 대출 시점 건전성 체크: `holdings×(leveragePercent-100) >= loan×leveragePercent`.

### `extinguishDebt(account, debtToken, extinguishAmount)`
이자 반영 후 `borrowed`/`holdings` 차감. 완전 상환 시 이자 스냅샷 삭제 + `borrowTokens` 배열에서
해당 토큰 제거(원소를 앞으로 당기고 `pop`하는 패턴).

### `hasHoldingToken` / `hasBorrowedToken`
조회 헬퍼.

### `loanInPeg` / `holdingsInPeg`
계좌의 전체 빚/보유자산을 기준통화(peg)로 환산한 합계 (내부에서 `sumTokensInPeg*` 순회).

### `belowMaintenanceThreshold(account)` — ⚠️ 이름-로직 불일치 의심
```solidity
uint256 loan = loanInPeg(account, true);
uint256 holdings = holdingsInPeg(account, true);
// holdings / loan >= 1.1 이면 (건전)
return 100 * holdings >= liquidationThresholdPercent * loan;
```
함수명은 "유지증거금 아래(청산 대상)"를 뜻해야 하는데, 실제로는 **건전할 때 true**를 반환.
이름을 믿고 호출하는 코드가 있다면 청산 로직이 반대로 동작할 수 있음. web3bugs `H-05`(High)
항목이라는 점을 볼 때 이 부분이 실제 취약점 핵심일 가능성이 높음.

### `sumTokensInPeg` / `viewTokensInPeg` / `sumTokensInPegWithYield` / `viewTokensInPegWithYield`
토큰 목록을 순회하며 각 토큰을 peg 가치로 환산해 합산. `WithYield` 버전은 대출 이자까지 반영.
`sum*`은 상태를 변경할 수 있는(오라클 갱신 등) 버전, `view*`는 순수 조회 버전.

### `yieldTokenInPeg` / `viewYieldTokenInPeg`
개별 토큰의 실제 빚 = `저장량 × (현재 이자지수/스냅샷 지수)` 계산 후 peg 가치로 환산.

### `adjustAmounts(account, fromToken, toToken, soldAmount, boughtAmount)`
포트폴리오 내 트레이드 결과 반영 — 판 토큰 차감, 산 토큰 추가.

### `deleteAccount(account)`
청산 시 계좌 초기화: 모든 토큰에 대해 전역 `totalShort`/`totalLong` 차감, 개별 잔고 0, 배열 삭제.

### `min(a, b)`
단순 헬퍼.
