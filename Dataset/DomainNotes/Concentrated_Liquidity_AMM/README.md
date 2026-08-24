# 집중 유동성 AMM (Concentrated Liquidity) 개념 정리

대상 프로토콜: SushiSwap **Trident**의 Concentrated Liquidity Pool (Uniswap V3 스타일).
관련 컨트랙트: [contracts/web3bugs_35_H_11_Ticks.md](contracts/web3bugs_35_H_11_Ticks.md) (`Ticks` 라이브러리)

## 1. 기존 AMM vs 집중 유동성 AMM

- **기존 AMM (Uniswap V2류, `x*y=k`)**: LP의 유동성이 0~무한대 전체 가격 구간에 고르게 퍼짐 → 자본 효율 낮음
  (실제 거래는 현재가 근처에서만 일어나는데 자본은 극단적 가격대에도 낭비됨)
- **집중 유동성 (Uniswap V3류)**: LP가 유동성을 공급할 가격 범위 `[lower, upper]`를 직접 지정.
  현재가가 그 범위 안에 있을 때만 해당 유동성이 활성화되어 스왑에 쓰임 → 자본 효율 대폭 상승

## 2. 틱(Tick)

- 가격은 연속값이 아니라 이산적인 격자 단위인 **틱**으로 표현 (`price = 1.0001^tick`, 로그 스케일)
- LP 포지션의 가격 범위 경계(lower tick, upper tick)를 지정하는 단위
- 스왑으로 가격이 움직이다 어떤 틱을 "넘으면(cross)", 그 틱에 걸린 포지션들의 유동성이 활성/비활성 전환됨

## 3. Tick 자료구조 (이 구현의 특징: 연결리스트)

```solidity
struct Tick {
    int24 previousTick; int24 nextTick;     // 연결리스트 포인터
    uint128 liquidity;                       // 이 틱에서 증감할 유동성량
    uint256 feeGrowthOutside0/1;             // 이 틱 "바깥쪽"에서 누적된 수수료
    uint160 secondsPerLiquidityOutside;      // TWAP 오라클용 시간가중 지표
}
```

**주의**: 원조 Uniswap V3는 틱을 **비트맵(bitmap)**으로 관리해서 "다음 활성 틱"을 빠르게 찾는데,
이 구현(Trident)은 `previousTick`/`nextTick`으로 **연결리스트**를 만들어 관리한다 — 가스 최적화를 위한
설계 선택이지만, 리스트 삽입/삭제 순서가 꼬이면 버그로 이어지기 쉬운 구조.

## 4. `feeGrowthOutside` 트릭

특정 범위 안에서 LP가 번 수수료를 계산하려면 "전역 누적 수수료 - 범위 바깥쪽 누적 수수료"로 역산해야 한다.
그래서 각 틱은 "이 틱 바깥쪽"의 누적 수수료 스냅샷을 들고 있고, 가격이 그 틱을 넘을 때마다
`바깥쪽 = 전역값 - 기존 바깥쪽값`으로 안/바깥 기준이 뒤집힌다(flip). `secondsPerLiquidityOutside`도 동일한 트릭.

## 5. 핵심 함수 흐름

- `insert`: 새 LP 포지션 `[lower, upper]` 등록 — 기존 틱이면 유동성만 더하고, 없으면 연결리스트에 새 노드 삽입
- `remove`: 유동성 제거 — 남은 유동성이 0이 되면 연결리스트에서 노드 자체를 제거
- `cross`: 스왑 도중 가격이 틱을 실제로 넘을 때, 활성 유동성(`currentLiquidity`)을 갱신하고 fee/시간 지표를 flip

## ⚠️ 관찰된 이슈 (web3bugs H-11과 연결)

`cross()`에서 유동성을 더할지 뺄지를 **틱 번호의 짝/홀(`nextTickToCross % 2`)**로 판단한다:

```solidity
if (nextTickToCross % 2 == 0) {
    currentLiquidity -= ticks[nextTickToCross].liquidity;
} else {
    currentLiquidity += ticks[nextTickToCross].liquidity;
}
```

정상적인 설계라면 "이 틱이 어떤 포지션의 lower인지 upper인지"에 따라 방향이 결정되어야 하는데
(보통 부호 있는 `liquidityNet`으로 인코딩), 틱 번호의 홀짝은 그것과 논리적으로 무관하다.
같은 틱이 어떤 포지션에서는 lower로 다른 포지션에서는 upper로 쓰일 수 있어, 활성 유동성 계산이
틀어지고 스왑 가격 계산 전체가 깨질 수 있는 심각한 버그로 보인다. 자세한 내용은
[contracts/web3bugs_35_H_11_Ticks.md](contracts/web3bugs_35_H_11_Ticks.md) 참고.

(참고: `import "hardhat/console.sol"`이 남아있는 것도 프로덕션에 부적절한 디버그 잔재이지만
이건 별개의 코드 품질 이슈.)
