# web3bugs_35_H_11.sol — `Ticks` 라이브러리

원본 경로: `evaluation/RQ1/target_contracts_original/web3bugs_35_H_11.sol`
SushiSwap Trident의 집중 유동성 풀에서 틱(가격 범위) 연결리스트를 관리하는 라이브러리.
개념 배경은 [../README.md](../README.md) 참고.

## `Tick` 구조체

```solidity
struct Tick {
    int24 previousTick;
    int24 nextTick;
    uint128 liquidity;
    uint256 feeGrowthOutside0;   // 토큰0 기준, 이 틱 바깥쪽 누적 수수료
    uint256 feeGrowthOutside1;   // 토큰1 기준, 이 틱 바깥쪽 누적 수수료
    uint160 secondsPerLiquidityOutside;
}
```

## 함수별 설명

### `getMaxLiquidity(_tickSpacing) → uint128`
`type(uint128).max / (MAX_TICK / tickSpacing)`. 틱 개수(`MAX_TICK/tickSpacing`)로 나눠서, 한 틱에
모든 포지션의 유동성이 몰려도 오버플로우 나지 않을 최대 허용치를 계산.

### `cross(ticks, nextTickToCross, secondsPerLiquidity, currentLiquidity, feeGrowthGlobal, zeroForOne) → (uint256, int24)`
스왑 도중 가격이 실제로 틱을 넘을 때 호출.
1. `secondsPerLiquidityOutside`를 flip: `outside = 전역값 - 기존 outside값`
2. `zeroForOne`(토큰0→토큰1, 가격 하락 방향)이면 `previousTick`으로, 아니면 `nextTick`으로 연결리스트를 이동
3. 이동하면서 `currentLiquidity`(활성 유동성)를 갱신하고, `feeGrowthOutside0`(또는 1)도 flip

```solidity
if (zeroForOne) {
    if (nextTickToCross % 2 == 0) {
        currentLiquidity -= ticks[nextTickToCross].liquidity;
    } else {
        currentLiquidity += ticks[nextTickToCross].liquidity;
    }
    nextTickToCross = ticks[nextTickToCross].previousTick;
    ticks[nextTickToCross].feeGrowthOutside0 = feeGrowthGlobal - ticks[nextTickToCross].feeGrowthOutside0;
} else {
    // 반대 방향, nextTick으로 이동, feeGrowthOutside1 갱신
}
```

**⚠️ `nextTickToCross % 2 == 0` 분기가 의심스러운 지점.** 정상 설계라면 이 틱이 어떤 포지션의
lower/upper 경계인지(보통 부호 있는 `liquidityNet`으로 인코딩)에 따라 방향이 결정돼야 하는데,
틱 번호의 홀짝은 그것과 무관한 임의의 값이다. 같은 틱이 서로 다른 포지션에서 lower/upper로 혼용될
수 있으므로, 이 판단 방식은 활성 유동성 계산을 틀리게 만들 수 있다. web3bugs `H-11`(High)로
분류된 것과 부합.

### `insert(ticks, feeGrowthGlobal0, feeGrowthGlobal1, secondsPerLiquidity, lowerOld, lower, upperOld, upper, amount, nearestTick, currentPrice) → int24`
새 LP 포지션 `[lower, upper]`를 등록.
- `lower < upper`, `MIN_TICK <= lower`, `upper <= MAX_TICK` 검증
- lower/upper 각각: 이미 존재하는 틱(`liquidity != 0`)이거나 경계값(MIN/MAX_TICK)이면 유동성만 가산.
  아니면 `lowerOld`/`upperOld` 힌트를 이용해 연결리스트의 올바른 위치에 새 노드 삽입 (순서가 안 맞으면
  `"LOWER_ORDER"`/`"UPPER_ORDER"`로 revert)
- 새로 삽입된 틱이 현재가(`nearestTick`) 안쪽인지 바깥쪽인지에 따라 `feeGrowthOutside` 초기값을
  전역값 또는 0으로 설정
- `TickMath.getTickAtSqrtRatio(currentPrice)`로 실제 현재 틱을 구해서, 새로 삽입된 lower/upper가
  더 가까우면 `nearestTick` 포인터를 갱신

### `remove(ticks, lower, upper, amount, nearestTick) → int24`
유동성 `amount`만큼 제거.
- lower/upper 각각: 제거 후 유동성이 정확히 0이 되면(`liquidity == amount`, 경계값이 아닐 때)
  연결리스트에서 그 틱 노드를 완전히 제거(이전/다음 노드 재연결), `nearestTick`이 그 틱을 가리키고
  있었으면 `previousTick`으로 갱신
- 아니면 `unchecked { current.liquidity -= amount; }`로 단순 차감 (오버플로우 체크를 개발자가
  수동으로 보장한다고 가정한 부분 — 언더플로우가 실제로 가능하다면 별도 위험 지점)

## 기타 코드 품질 관찰

- `import "hardhat/console.sol"`이 남아있음 — 프로덕션 배포용 코드에 디버그용 콘솔 임포트가 남은 것으로,
  버그는 아니지만 배포 전 정리가 필요한 잔재.
