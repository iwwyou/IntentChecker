# Yield Farming / Staking Rewards (MasterChef 패턴) 개념 정리

대상 프로토콜: SushiSwap의 "MasterChef"를 복제한 스테이킹 보상 분배 컨트랙트 (Concur 계열로 추정).
관련 컨트랙트: [contracts/web3bugs_83_H_01_MasterChef.md](contracts/web3bugs_83_H_01_MasterChef.md) (`MasterChef` 컨트랙트)

## 1. 개념: 유동성 채굴(liquidity mining)

- 사용자가 특정 토큰(주로 LP 토큰)을 컨트랙트에 **예치(deposit)**하면, 시간(블록)이 지날수록
  보상 토큰을 블록당 일정량씩 지급받는다.
- 여러 개의 **풀(pool)**이 있고, 각 풀은 `allocPoint`(배정 비중)만큼 전체 보상 중 몫을 가져간다.
  - `이 풀 몫 = 전체 블록당 보상 × (이 풀의 allocPoint / 모든 풀의 allocPoint 합)`
- 인출(withdraw) 시 그동안 쌓인 보상을 정산받는다.

파생상품(Perpetual_Futures)의 "포지션/담보"와는 다른 개념이다 — 여기서는 담보 개념이 아니라
"예치한 토큰 비율에 비례해 시간이 지날수록 보상을 나눠 갖는" 구조.

## 2. accRewardPerShare 패턴 (핵심 트릭)

MasterChef류 컨트랙트의 핵심은 **모든 사용자를 순회하지 않고 O(1)로 보상을 계산**하는 것이다.

- `accConcurPerShare`: "지금까지 예치된 토큰 1개당 누적된 보상량". 풀 전체에 대해 한 번만 계산.
- `user.rewardDebt`: "이 사용자는 이 시점까지의 보상은 이미 받은 것으로 친다"는 기준선.
  - `pending reward = user.amount * accConcurPerShare - user.rewardDebt`
  - 사용자가 예치/인출할 때마다 `rewardDebt`를 현재 `amount * accConcurPerShare`로 재설정해서,
    그 이후에 새로 쌓이는 보상만 카운트되게 만든다.
  - 뒤늦게 들어온 사람이 이전 사람들 몫까지 가로채는 것을 막는 장치.

## 3. 구조체

```solidity
struct UserInfo {
    uint128 amount;      // 예치량
    uint128 rewardDebt;  // 보상 기준선
}
struct PoolInfo {
    IERC20 depositToken;
    uint allocPoint;         // 이 풀의 보상 배정 비중
    uint lastRewardBlock;    // 마지막 정산 블록
    uint accConcurPerShare;  // 토큰 1개당 누적 보상
    uint16 depositFeeBP;     // 예치 수수료
}
```

## 4. 풀 등록 (`add` 함수)

관리자(`onlyOwner`)만 새 풀을 등록할 수 있다. 등록 시:
- 토큰 주소, 배정 비중(`allocPoint`), 예치수수료, 보상 시작 블록을 지정
- `totalAllocPoint`(전체 배정 비중 합)에 새 풀 비중을 더함 — 이게 각 풀 몫 계산의 분모
- `pid[token] == 0`으로 중복 등록 여부 체크 (pid 0은 생성자에서 만든 더미 풀이 차지하고 있어서
  "0 = 미등록"으로 판별 가능)
- 등록 이전 과거분에 보상이 소급되지 않도록 `lastRewardBlock`을 현재/미래 블록으로 설정

## 5. 예치/인출 흐름

1. `updatePool`로 해당 풀의 `accConcurPerShare`를 최신 블록까지 갱신
2. 기존 예치분이 있으면 쌓인 보상(pending)을 먼저 지급
3. 예치량 증감 반영 (예치 시 수수료 차감)
4. `rewardDebt`를 새 기준으로 재설정

## ⚠️ 관찰된 이슈 (web3bugs H-01과 연결)

`depositFeeBP`라는 이름은 "basis point"(1bp=0.01%, 분모 10000) 관례를 암시하지만,
실제 계산은 `_perMille = 1000`(퍼밀, 분모 1000)으로 나눈다.
→ 관리자가 "4%(400bp)"를 의도해도 실제로는 `400/1000 = 40%`가 부과됨 — **의도한 것보다 10배 큰 수수료**.
단위 관례(BP)와 실제 나눗셈 분모(퍼밀)가 어긋난 전형적인 유닛 불일치 버그로 보인다.
자세한 내용은 [contracts/web3bugs_83_H_01_MasterChef.md](contracts/web3bugs_83_H_01_MasterChef.md) 참고.
