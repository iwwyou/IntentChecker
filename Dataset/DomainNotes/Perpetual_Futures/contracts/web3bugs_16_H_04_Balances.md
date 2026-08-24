# web3bugs_16_H_04.sol — `Balances` 라이브러리

원본 경로: `evaluation/RQ1/target_contracts_original/web3bugs_16_H_04.sol`
소속 프로토콜: Tracer Protocol (퍼페추얼 스왑). 개념 배경은 [../README.md](../README.md) 참고.

storage를 갖는 컨트랙트가 아니라, 트레이더의 포지션·마진·수수료를 계산하는 **순수 계산 로직 모음**
(`internal pure` 함수들). 상위 컨트랙트(예: `TracerPerpetualSwaps.sol`, 이 데이터셋에는 미포함)가
`using Balances for ...` 형태로 가져다 쓴다.

## 구조체

```solidity
struct Position { int256 quote; int256 base; }        // 계정의 담보(quote)와 노출량(base)
struct Trade { uint256 price; uint256 amount; Perpetuals.Side side; }  // 체결된 거래 1건
struct Account {
    Position position;
    uint256 totalLeveragedValue;
    uint256 lastUpdatedIndex;
    uint256 lastUpdatedGasPrice;
}
```

## 함수별 설명

### `notionalValue(position, price) → uint256`
`|base| * price`. 포지션의 현재 시세 기준 명목가치.

### `margin(position, price) → int256`
`quote + base * price`. 실제 자기자본(순자산). 저장값이 아니라 호출 시점마다 재계산.
주석에 "price를 캐스팅하는 이유"가 설명돼 있음 — quote/base는 음수가 허용되어 캐스팅 불가하므로
소거법상 price(uint256)를 int256으로 캐스팅. `price >= type(int256).max()`면 revert.

### `leveragedNotionalValue(position, price) → uint256`
`notionalValue - margin`, 단 음수면 0. 레버리지로 인해 노출된 만큼(자기자본을 초과하는 부분)을 나타냄.

### `minimumMargin(position, price, liquidationGasCost, maximumLeverage) → uint256`
```
minimumMargin = notionalValue / maximumLeverage + 6 * liquidationGasCost
```
- `position.base == 0`이면 0 반환 (포지션 없으면 최소마진도 없음).
- **처음 낸 담보와 무관**하게, 현재 포지션 크기와 현재 가격 기준으로 매 호출마다 재계산됨.
- `6 * liquidationGasCost`: 청산 실행자에게 가스비를 보상하기 위한 버퍼.

### `marginIsValid(position, liquidationGasCost, price, trueMaxLeverage) → bool`
`margin < 0`이면 무조건 false (과다 인출 등으로 마진이 음수인 경우). 그 외엔
`margin >= minimumMargin`인지 검사. 청산 여부 판정의 핵심 함수 — 같은 시점의 같은 price로
margin과 minimumMargin을 동시에 비교.

### `fillAmount(orderA, fillA, orderB, fillB) → uint256`
`min(orderA.amount - fillA, orderB.amount - fillB)`. 반대 방향 주문 두 개를 매칭할 때
체결 가능한 수량(둘 중 잔여수량이 작은 쪽) 계산.

### `applyTrade(position, trade, feeRate) → Position`
체결된 거래 1건을 기존 포지션에 반영해 새 포지션을 계산.

```solidity
quoteChange = amount * price   // 이 거래에 오가야 할 현금(quote) 액수
fee = getFee(amount, price, feeRate)   // 항상 양수

Long:  newBase = base + amount   newQuote = quote - quoteChange + fee
Short: newBase = base - amount   newQuote = quote + quoteChange - fee
```
- Long = "base를 사는 것" → quote 지불(감소), base 취득(증가)
- Short = "base를 파는 것" → quote 수취(증가), base 처분(감소)

**⚠️ 주목할 점 (이 파일이 web3bugs `H-04`, High severity 항목이라는 점과 연결지어 볼 것):**
Short은 `- fee`(수수료만큼 quote 차감, 정상적으로 수수료를 내는 방향)인데, Long은 `+ fee`
(수수료만큼 quote가 오히려 **증가**)로 부호가 다르다. `getFee`는 항상 양수를 반환하므로,
Long 쪽에서는 수수료를 내는 게 아니라 담보가 늘어나는 셈이 된다. 이 비대칭이 실제 취약점의
핵심 지점일 가능성이 높음 — 상위 컨트랙트나 감사 리포트 원문 확인 시 우선적으로 검증할 부분.

### `getFee(amount, executionPrice, feeRate) → int256`
`amount * executionPrice * feeRate`. 항상 양수 반환.

### `tokenToWad` / `wadToToken`
담보로 쓰는 토큰이 18 decimals가 아닐 수 있어서(예: USDC는 6 decimals), 내부 계산 표준 단위인
WAD(18 decimals)로 상호 변환.

## 담보 입출금은 이 파일에 없음

`applyTrade`는 `Trade{price, amount, side}`를 필수로 받으므로 실제 매매 체결에만 쓰이고,
"포지션은 그대로 두고 담보만 추가/인출"하는 로직은 표현할 수 없다. 그런 deposit/withdraw는
상위 컨트랙트에 별도로 있을 것으로 추정되며, 출금 시 `marginIsValid`로 사후 검증할 것으로 보임
(이 데이터셋에는 해당 상위 컨트랙트 파일이 포함되어 있지 않아 실제 구현은 미확인).
