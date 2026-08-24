# web3bugs_83_H_01.sol — `MasterChef`

원본 경로: `evaluation/RQ1/target_contracts_original/web3bugs_83_H_01.sol`
SushiSwap의 MasterChef 패턴을 복제한 스테이킹 보상 분배 컨트랙트. 개념 배경은 [../README.md](../README.md) 참고.

## 상태 변수

| 변수 | 의미 |
|---|---|
| `poolInfo` (배열) | 등록된 각 풀의 정보. index = `pid` |
| `userInfo[pid][address]` | 특정 풀에서 특정 사용자의 예치량/보상 정산 상태 |
| `isDepositor[address]` | 예치를 대신 실행할 수 있는 권한을 가진 주소 화이트리스트 |
| `pid[token]` | 토큰 → pool id 역매핑 (중복 등록 방지) |
| `concurPerBlock` | 블록당 전체 풀에 분배되는 concur 보상량 |
| `totalAllocPoint` | 모든 풀의 `allocPoint` 합계 (풀 몫 계산의 분모) |
| `startBlock` / `endBlock` | 보상 지급 시작/종료 블록 |
| `concur` | 보상 토큰 |
| `_concurShareMultiplier` (1e18) | 정밀도 보정 배수 |
| `_perMille` (1000) | 퍼밀 단위 상수. `depositFeeBP` 이름과 단위가 어긋남 (아래 참고) |

## 구조체

```solidity
struct UserInfo { uint128 amount; uint128 rewardDebt; }
struct PoolInfo {
    IERC20 depositToken; uint allocPoint; uint lastRewardBlock;
    uint accConcurPerShare; uint16 depositFeeBP;
}
```

## 함수별 설명

### `addDepositor` / `removeDepositor` (onlyOwner)
`isDepositor` 화이트리스트 관리. `deposit`/`withdraw`는 `onlyDepositor`만 호출 가능 —
일반 유저가 직접 부르지 않고 별도 프록시/라우터를 통해서만 예치·인출 가능한 구조로 보임.

### `add(_token, _allocationPoints, _depositFee, _startBlock)` (onlyOwner)
새 풀 등록. `totalAllocPoint`에 비중 추가, `pid[_token]==0`으로 중복 등록 방지
(pid 0은 생성자의 더미 풀이 차지), 등록 이전 과거분 보상 소급 방지를 위해
`lastRewardBlock = max(block.number, _startBlock)`.

### `poolLength` / `getMultiplier(from, to)`
조회용. `getMultiplier`는 단순히 `to - from`(경과 블록 수).

### `pendingConcur(_pid, _user)` (view)
상태 변경 없이 `updatePool`과 동일한 계산을 시뮬레이션해서, 지금 클레임하면 받을 보상을 미리 계산.

### `massUpdatePools` / `updatePool(_pid)`
- `updatePool`: 해당 풀의 `accConcurPerShare`(토큰 1개당 누적 보상)를 최신 블록까지 갱신.
  - `lpSupply==0` 또는 `allocPoint==0`이면 계산 없이 `lastRewardBlock`만 갱신
  - `endBlock` 지났으면 더 이상 보상 안 쌓이게 스냅
  - 정상: `보상 = 경과블록 × concurPerBlock × (allocPoint/totalAllocPoint)`를 `accConcurPerShare`에 누적
- `massUpdatePools`: 모든 풀에 대해 `updatePool` 반복 (가스비 주의 주석 있음)

### `deposit(_recipient, _pid, _amount)` (onlyDepositor)
1. `updatePool`로 정산
2. 기존 예치분 있으면 쌓인 보상을 `_recipient`에게 지급
3. `_amount`만큼 예치량 증가 (수수료 있으면 차감)
4. `rewardDebt` 재설정 (이후 보상만 카운트되게)

### `withdraw(_recipient, _pid, _amount)` (onlyDepositor)
정산 → 보상 지급 → 예치량 감소 → `rewardDebt` 재설정. 인출량이 예치량 초과 시 revert.

### `safeConcurTransfer(_to, _amount)` (private)
반올림 오차로 컨트랙트에 보상 토큰이 부족할 경우, 있는 만큼만 전송하는 안전장치.

## ⚠️ 주목할 부분 — `depositFeeBP` vs `_perMille` 단위 불일치

```solidity
uint depositFee = _amount.mul(pool.depositFeeBP).div(_perMille);  // _perMille = 1000
```

- `depositFeeBP`의 "BP"는 관례적으로 basis point(1bp=0.01%, 분모 10000)를 의미
  (SushiSwap 원본 MasterChef도 `/10000` 사용).
- 실제로는 `_perMille = 1000`(퍼밀, 분모 1000)으로 나눔.
- 결과: 관리자가 "4%(400bp)"를 의도해도 실제 수수료는 `400/1000 = 40%` — **의도보다 10배**.
- 이 파일이 web3bugs `H-01`(High)이라는 점을 볼 때, 이 단위 불일치가 실제 신고된 취약점일 가능성이 높음.
