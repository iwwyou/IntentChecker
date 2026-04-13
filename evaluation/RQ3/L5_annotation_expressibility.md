# L5 Annotation Expressibility Analysis

Bug-awareness-required (L5) 케이스 14건에 대해, **버그를 인지한 상태에서** IntentChecker의 annotation 모델로 *awareness signal*(Violated 또는 Warning)을 제공할 수 있는지를 분석한 문서.

**중요**: IntentChecker의 목표는 detection(버그를 정확히 잡음)이 아니라 awareness(개발자가 이상함을 인지하도록 신호 제공). 따라서 annotation이 fix와 1:1로 대응할 필요는 없으며, 문제가 발생했을 때 Violated 또는 Warning을 발생시키는 것으로 충분.

## 분류 기준

| 분류 | 정의 | Annotation 유형 |
|------|------|----------------|
| **Strong** (Direct) | Annotation이 올바른 값/관계를 직접 명시하여 buggy code에서 명확한 Violated 발생. Awareness signal이 강함. | `@During var relOp expr`, `@Post var relOp expr` (CommonClause: RelationalCmp) |
| **Weak** (Indirect) | 변수의 변경 여부 또는 변경 방향만 감지. 정확한 값은 명시하지 않으나 buggy 케이스에서 Violated 또는 partial signal 발생. | `changed(var, true/false)` (VarChangedEval), `var(Entry relOp Exit)` (PostEntryExit) |

이전에 "Not possible"로 분류되었던 11건은 `evaluation/RQ1/limitation_types.md`의 L4 (annotation-inexpressible)로 이동되었다. 해당 케이스들은 bug awareness가 있어도 annotation 모델로 어떤 형태의 signal도 제공할 수 없는 구조적 한계 케이스이다.

### Strong vs Weak 구분

- **Strong**: CommonClause의 `var relOp expr` -- **올바른 값 자체 또는 명시적 관계를 표현**. Buggy면 확실히 Violated.
- **Weak**: `changed(var, true/false)` 또는 `var(Entry relOp Exit)` -- **변경 여부/방향만 감지**. Buggy 중 일부 경로에서만 Violated (변화가 아예 없는 경우 등).

### 문법 참조 (Solidity.g4)

```
postClause
    : intentValue '(' ENTRY relOp EXIT ')'    // PostEntryExit
    | commonClause                             // PostCommon
    ;

duringClause
    : intentValue '(' BEFORE relOp AFTER ')'   // DuringBeforeAfter
    | intentValue '(' ASSIGN relOp CURRENT ')' // DuringAssignCurrent
    | identifier '.' 'arg' '[' N ']' relOp intentValue  // DuringFunctionArg
    | commonClause                             // DuringCommon
    ;

commonClause
    : intentValue relOp intentValue            // RelationalCmp
    | 'changed' '(' intentValue ',' ('true'|'false') ')'  // VarChangedEval
    | 'returnExpression' relOp intentValue     // ReturnExprCmp
    | ...
    ;

intentValue : arithExpr ;  // 산술(+,-,*,/,%) + varRef(var.field, var[expr])
```

**제약**: `entry(var)`를 CommonClause의 intentValue에서 참조할 수 없음. Entry/Exit 비교는 PostEntryExit에서만 가능. PostEntryExit에서 산술 표현(예: `ibRatio * totalSupply(Entry == Exit)`)은 도구에서 미지원.

---

## 요약

| | L5a (missing-code) | L5b (wrong-code) | 합계 |
|---|---|---|---|
| **Strong** (Direct) | 2 | 5 | **7** (50%) |
| **Weak** (Indirect) | 5 | 2 | **7** (50%) |
| **합계** | 7 | 7 | **14** |

**핵심 결과**: 14/14 expressible. Bug awareness가 전제될 경우 모든 L5 케이스에서 IntentChecker가 awareness signal을 제공할 수 있다.

---

## Strong (Direct) -- 7건

---

### 1. web3bugs_62_H_10 (L5a: missing-code)

- **Contract**: Stream
- **Function**: creatorClaimSoldTokens
- **Bug**: `ERC20(depositToken).safeTransfer(destination, amount)` 이후 `redeemedDepositTokens` 갱신 누락. 이후 `recoverTokens()`에서 `depositTokenAmount - redeemedDepositTokens`가 여전히 원래 값이라 excess 계산 오류.
- **Bug report**: 62.md H-10
- **Bug report 권장 fix**: `redeemedDepositTokens = depositTokenAmount` 추가

**Annotation**:
```
// @Post redeemedDepositTokens == depositTokenAmount
```

**문법**: CommonClause (RelationalCmp). 두 state variable 비교.

**왜 Strong인가**:
- Buggy (`creatorClaimSoldTokens` 종료 후): `redeemedDepositTokens`가 갱신되지 않아 < `depositTokenAmount` → annotation **violated**
- Correct: `redeemedDepositTokens = depositTokenAmount` 추가 → 두 값 동일 → **satisfied**
- "creatorClaimSoldTokens가 모든 deposit token을 claim했다면 redeemed가 deposit과 같아야 한다"는 함수 불변식을 직접 명시.

**참고**: 이전 버전에서는 `@Post depositTokenAmount == 0`을 제안했으나, 이는 fix(`redeemedDepositTokens = depositTokenAmount`) 후에도 성립하지 않아 buggy/correct 구분 불가. 위 annotation으로 교체.

---

### 2. web3bugs_65_H_01 (L5a: missing-code)

- **Contract**: Basket
- **Function**: handleFees
- **Bug**: `startSupply == 0` 분기(line 136-137)에서 `lastFee = block.timestamp` 누락. 3개 분기 중 2개는 `lastFee`를 갱신하지만 supply=0 분기만 누락. 이후 supply가 복원되면 stale `lastFee`로 인해 과도한 fee 부과.
- **Bug report**: 65.md H-01

**Annotation**:
```
// @Post lastFee == block.timestamp
```

**문법**: CommonClause (RelationalCmp). `block.timestamp`은 varRef(`block.timestamp`)로 파싱 가능.

**왜 Strong인가**:
- Buggy (supply=0 경로): `lastFee` 미갱신 -> `lastFee != block.timestamp` -> **violated**
- Correct: 모든 경로에서 `lastFee = block.timestamp` -> **satisfied**
- "handleFees 실행 후 lastFee는 항상 현재 timestamp"라는 함수 불변식을 직접 명시. 이는 fee 함수의 자연스러운 spec.

---

### 3. web3bugs_113_H_05 (L5b: wrong-code)

- **Contract**: NFTPairWithOracle
- **Function**: _lend
- **Bug**: Line 316의 require에서 `params.ltvBPS >= accepted.ltvBPS` 사용. Lender에게 낮은 LTV가 더 안전하므로 올바른 조건은 `params.ltvBPS <= accepted.ltvBPS`. 현재 코드는 borrower가 lender의 허용치보다 높은 LTV를 요청해도 통과시킴.
- **Bug report**: 113.md H-05

**Annotation**:
```
// @During params.ltvBPS <= accepted.ltvBPS
```

**문법**: DuringCommon -> CommonClause (RelationalCmp). 두 varRef 간 비교.

**왜 Strong인가**:
- Buggy: require가 `>=`를 허용 -> `params.ltvBPS > accepted.ltvBPS`인 경우 함수 진입 -> annotation `<=` **violated**
- Correct: require가 `<=`로 변경 -> 항상 `params.ltvBPS <= accepted.ltvBPS` -> **satisfied**
- Annotation이 올바른 require 조건 자체를 명시. Fix와 동일.

---

### 4. web3bugs_31_H_01 (L5b: wrong-code)

- **Contract**: MyStrategy
- **Function**: manualRebalance
- **Bug**: `currentLockRatio = balanceInLock.mul(10**18).div(totalCVXBalance)` (percentage, max 1e18)로 계산하지만, `newLockRatio = totalCVXBalance.mul(toLock).div(MAX_BPS)` (absolute CVX amount)로 계산. 이후 둘을 직접 비교/뺄셈하여 차원 불일치. Fix: `currentLockRatio = balanceInLock`.
- **Bug report**: 31.md H-01

**Annotation**:
```
// @During currentLockRatio == balanceInLock
```

**문법**: DuringCommon -> CommonClause (RelationalCmp). 두 local variable 비교.

**왜 Strong인가**:
- Buggy: `currentLockRatio = balanceInLock * 1e18 / totalCVXBalance` != `balanceInLock` (totalCVXBalance != 1e18일 때) -> **violated**
- Correct: `currentLockRatio = balanceInLock` -> **satisfied**
- Annotation이 올바른 계산 결과를 직접 명시. Fix 공식과 동일.

---

### 5. web3bugs_79_H_02 (L5b: wrong-code)

- **Contract**: LaunchEvent
- **Function**: createPair
- **Bug**: Floor price 미달 시 `tokenAllocated = (wavaxReserve * 10**token.decimals()) / floorPrice` 사용. `floorPrice`는 1e18 스케일이므로 올바른 공식은 `wavaxReserve * 1e18 / floorPrice`. `token.decimals() != 18`이면 잘못된 allocation.
- **Bug report**: 79.md H-02

**Annotation**:
```
// @During tokenAllocated == wavaxReserve * 1e18 / floorPrice
```
**배치**: `tokenAllocated`가 floor price 분기에서 재할당되는 statement (line 398) 직후. 함수 시작점이나 floor price 조건이 false인 경로에서 부착하면 correct code에서도 위반.

**문법**: DuringCommon -> CommonClause (RelationalCmp). intentValue에 산술 표현(`wavaxReserve * 1e18 / floorPrice`) 사용.

**왜 Strong인가**:
- Buggy: `tokenAllocated = wavaxReserve * 10**decimals / floorPrice` -> decimals != 18이면 다른 값 -> **violated**
- Correct: `tokenAllocated = wavaxReserve * 1e18 / floorPrice` -> **satisfied**
- Annotation이 올바른 수식을 직접 명시. Fix와 동일.

---

### 6. web3bugs_101_H_02 (L5b: wrong-code)

- **Contract**: LenderPool
- **Function**: terminate
- **Bug**: 실제 소스 코드에서 `_totalBorrowAsset`(local 변수, 일부 audit report에서는 `_principalWithdrawable`로 호칭)가 token amount 단위로 계산되지만 `withdrawShares()`에 share amount로 전달됨 (단위 혼동). 올바른 값은 단순히 `_sharesHeld` (전체 share 인출).
- **Bug report**: 101.md H-02
- **변수명 매핑**: `_principalWithdrawable` (audit report) ↔ `_totalBorrowAsset` (실제 .sol 변수명)

**Annotation**:
```
// @During _totalBorrowAsset == _sharesHeld
```

**문법**: DuringCommon -> CommonClause (RelationalCmp). 두 local variable 비교.

**왜 Strong인가**:
- Buggy: `_totalBorrowAsset`이 복잡한 token/share 혼합 계산으로 산출 -> `_sharesHeld`와 다름 -> **violated**
- Correct: `_totalBorrowAsset = _sharesHeld` (단순 전체 인출) -> **satisfied**
- Annotation이 "terminate 시 전체 shares를 인출해야 한다"는 의도를 직접 명시.

---

### 7. web3bugs_70_H_09 (L5b: wrong-code)

- **Contract**: USDV
- **Function**: mint
- **Bug**: `uAmount = (vPrice * vAmount) / 1e18` (곱셈)이지만, oracle 가격 의미상 올바른 공식은 `uAmount = vAmount * 1e18 / vPrice` (나눗셈). 가격 방향 오류로 민팅량 왜곡.
- **Bug report**: 70.md H-09. **History**: Sponsor가 처음에 dispute(report line 481-488)했으나 최종 final report에서 High Risk Findings로 유지됨.

**Annotation**:
```
// @During uAmount == vAmount * 1e18 / vPrice
```
**배치**: `uAmount`가 처음 할당되는 statement (line 76: `uAmount = (vPrice * vAmount) / 1e18`) 직후. line 91 (`uAmount = uAmount - fee`)에 후 부착하면 fee 차감 때문에 correct code에서도 위반.

**문법**: DuringCommon -> CommonClause (RelationalCmp). 산술 표현.

**왜 Strong인가**:
- Buggy: `uAmount = vPrice * vAmount / 1e18` -> `vPrice != 1e18`이면 다른 값 -> **violated**
- Correct: `uAmount = vAmount * 1e18 / vPrice` -> **satisfied**
- Annotation이 올바른 변환 공식을 직접 명시.

**Caveat**: Sponsor dispute history 있음. 논문에서 dispute → 최종 confirm 흐름 명시 권장.

---

## Weak (Indirect) -- 7건

---

### 1. web3bugs_192_H_01 (L5a: missing-code)

- **Contract**: Lock
- **Function**: extendLock
- **Bug**: `IERC20(_asset).transferFrom(msg.sender, address(this), _amount)` 이후 `totalLocked[_asset] += _amount` 누락. 토큰은 유입되지만 내부 장부가 갱신되지 않아, 이후 `release()`에서 `totalLocked -= lockAmount` 시 underflow 발생.
- **Bug report**: 192.md H-01

**Annotation**:
```
// @Post totalLocked[_asset](Entry < Exit)
```

**문법**: PostEntryExit. `totalLocked[_asset]`은 mapping state variable.

**왜 Weak인가**:
- Buggy: `totalLocked[_asset]`이 함수 내에서 수정되지 않음 -> Entry == Exit -> `Entry < Exit` **violated**
- Correct: `totalLocked[_asset] += _amount` -> Entry < Exit -> **satisfied**
- "totalLocked는 증가해야 한다"는 방향만 명시. 정확한 증가량(`_amount`)은 표현하지 않음.
- 문법 제약: `@Post totalLocked == entry(totalLocked) + _amount` 형태는 지원되지 않음 (entry 값을 CommonClause에서 참조 불가)

**대안 annotation**: `@Post changed(totalLocked[_asset], true)` -- 방향도 미명시, 더 약한 형태.

---

### 2. web3bugs_62_H_03 (L5a: missing-code)

- **Contract**: Stream
- **Function**: claimReward
- **Bug**: `ERC20(rewardToken).safeTransfer(msg.sender, rewardAmt)` 이후 `rewardTokenAmount -= rewardAmt` 누락. 내부 장부가 감소하지 않아 이후 `recoverTokens()`에서 excess 계산이 잘못됨.
- **Bug report**: 62.md H-03

**Annotation**:
```
// @Post rewardTokenAmount(Entry > Exit)
```

**문법**: PostEntryExit. `rewardTokenAmount`은 `uint112` state variable.

**왜 Weak인가**:
- Buggy: `rewardTokenAmount` 불변 -> Entry == Exit -> `Entry > Exit` **violated**
- Correct: `rewardTokenAmount -= rewardAmt` -> Entry > Exit -> **satisfied**
- "rewardTokenAmount는 감소해야 한다"는 방향만 명시. 정확한 감소량(`rewardAmt`)은 표현하지 않음.

---

### 3. web3bugs_52_H_23 (L5a: missing-code)

- **Contract**: VaderPoolV2
- **Function**: mintSynth
- **Bug**: `mintSynth` 내부에서 `(uint112 reserveNative, uint112 reserveForeign, ) = getReserves(foreignAsset)`로 reserve를 읽고, 이후 `_update(foreignAsset, reserveNative + nativeDeposit, reserveForeign, ...)` 호출. 이때 `reserveForeign`(local)이 감소 없이 그대로 전달됨. Synth 민팅은 경제적으로 foreign reserve를 소비하는 것이므로 `reserveForeign - amountSynth`이어야 함.
- **Bug report**: 52.md H-23

**Annotation**:
```
// @Post pairInfo[foreignAsset].reserveForeign(Entry > Exit)
```

**문법**: PostEntryExit. `pairInfo[foreignAsset].reserveForeign`은 mapping → struct field로 접근되는 state variable. `_update()`에서 storage에 기록됨.

**왜 Weak인가**:
- Buggy: `_update`가 원래 `reserveForeign` 값을 기록 → Entry == Exit → `Entry > Exit` **violated**
- Correct: `_update`가 `reserveForeign - amountSynth`를 기록 → Entry > Exit → **satisfied**
- "synth 민팅 후 foreign reserve는 감소해야 한다"는 방향만 명시. 정확한 감소량(`amountSynth`)은 표현하지 않음.

**주의**: `_update`의 storage write는 `BasePoolV2`(import)에 정의되어 있어 IntentChecker가 dependency 사전분석으로 해당 함수의 동작을 알아야 함. 이 점에서 `limitation_types.md`에서는 한때 E5(missing-dependency)로도 분류된 적 있으나, dependency 분석이 가능하다는 전제 하에 L5 Weak로 유지.

---

### 4. web3bugs_35_H_12 (L5a: missing-code)

- **Contract**: ConcentratedLiquidityPool
- **Function**: mint
- **Bug**: `liquidity` 변경(line 176) 시 `secondsPerLiquidity` 업데이트 누락. `swap()`에서는 `secondsPerLiquidity += (diff << 128) / liquidity`로 갱신하지만 `mint()`에서 동일 갱신이 빠짐.
- **Bug report**: 35.md H-12

**Annotation**:
```
// @Post changed(secondsPerLiquidity, true)
```

**문법**: CommonClause (VarChangedEval). `secondsPerLiquidity`는 `uint160` state variable.

**왜 Weak인가**:
- Buggy: `secondsPerLiquidity` 불변 -> `changed(..., true)` **violated**
- Correct: 업데이트 추가 -> **satisfied**
- 변경 여부만 감지하며, 정확한 갱신 값(`(diff << 128) / liquidity`)이나 방향을 명시하지 않음.

**PostEntryExit 대안이 아닌 이유**: `secondsPerLiquidity`는 시간 경과에 따라 증가하므로 `lastObservation == block.timestamp` (같은 블록)이면 증가하지 않아야 함. 방향이 조건부이므로 `changed`가 더 안전.

**부가 blocker**: `abi.decode`로 mint 파라미터 전달 -> debugging annotation으로 concrete 값 설정 불가. 실제 IntentChecker 실행에는 추가 제약 존재.

---

### 5. web3bugs_83_H_01 (L5a: missing-code)

- **Contract**: MasterChef
- **Function**: add
- **Bug**: `totalAllocPoint` 증가 전 `massUpdatePools()` 호출 누락. 기존 풀의 `accConcurPerShare`가 이전 `totalAllocPoint`로 갱신되지 않은 채 새로운 값이 적용되어 기존 staker reward 소급 희석.
- **Bug report**: 83.md H-01

**Annotation**:
```
// @Post changed(poolInfo[0].accConcurPerShare, true)
```

**문법**: CommonClause (VarChangedEval). `poolInfo[0].accConcurPerShare`는 varRef(`poolInfo` `[0]` `.accConcurPerShare`).

**왜 Weak인가**:
- Buggy: `massUpdatePools()` 미호출 -> 기존 풀의 `accConcurPerShare` 불변 -> **violated**
- Correct: `massUpdatePools()` 호출 -> `accConcurPerShare` 갱신 -> **satisfied**
- 변경 여부만 감지.

**왜 Strong이 아닌가**: `accConcurPerShare`의 올바른 값은 `concurPerBlock`, `totalAllocPoint`, `block.number` 등 여러 변수의 복합 계산에 의존. 이를 intentValue의 산술 표현으로 구성하기 어려움.

**주의**: 기존 풀이 없는 상태(첫 `add()` 호출)에서는 `poolInfo[0]`이 존재하지 않아 annotation 무의미. 기존 풀 + active staker가 있을 때만 유효.

---

### 6. web3bugs_35_H_11 (L5b: wrong-code)

- **Contract**: Ticks (library)
- **Function**: cross
- **Bug**: `zeroForOne` 분기에서 `feeGrowthOutside0`를 업데이트(line 40)하지만, swap 방향에 따른 fee 회계 규칙상 `feeGrowthOutside1`을 업데이트해야 함. 권장 fix(report line 430-440)는 field 0/1만 swap.
- **Bug report**: 35.md H-11

**Annotation**:
```
// @Post changed(ticks[nextTickToCross].feeGrowthOutside1, true)
```

**문법**: CommonClause (VarChangedEval). `ticks[nextTickToCross].feeGrowthOutside1`은 mapping struct field. `nextTickToCross`는 함수 파라미터로, `@Post`에서 Entry 시점의 값으로 바인딩.

**왜 Weak인가**:
- Buggy (`zeroForOne`): 원래 tick의 `feeGrowthOutside1`이 아닌 새 tick의 `feeGrowthOutside0`이 업데이트됨 -> 원래 tick의 `feeGrowthOutside1` 불변 -> **violated**
- Correct: 원래 tick의 `feeGrowthOutside1`이 `feeGrowthGlobal1 - feeGrowthOutside1`로 업데이트됨 -> **satisfied**
- 변경 여부만 감지하며, 어떤 값으로 변해야 하는지는 명시하지 않음.

**왜 Strong이 아닌가**: `feeGrowthOutside1`의 새 값은 `feeGrowthGlobal1 - ticks[nextTickToCross].feeGrowthOutside1`인데, 이 XOR 패턴은 증가/감소 방향이 고정되지 않아 `Entry relOp Exit`로 방향을 명시할 수 없음. `changed`만 가능.

---

### 7. web3bugs_112_H_01 (L5b: wrong-code)

- **Contract**: StakerVault
- **Function**: transfer
- **Bug**: `balances[msg.sender] -= amount` 및 `balances[account] += amount` (lines 112-113)이 `userCheckpoint()` (lines 117-118) **이전에** 실행됨. Checkpoint가 이미 변경된 balance를 기반으로 reward를 계산하여 receiver가 부당 이득. `transferFrom()`은 올바르게 checkpoint를 먼저 호출.
- **Bug report**: 112.md H-01

**Annotation**:
```
// @During changed(balances[msg.sender], false)
```
checkpoint 호출 시점(line 117)에 배치.

**문법**: DuringCommon -> CommonClause (VarChangedEval). `@During` 컨텍스트에서 `changed(var, false)`는 "함수 시작부터 이 지점까지 변수가 변하지 않았어야 한다"를 의미.

**왜 Weak인가**:
- Buggy: line 117 시점에서 `balances[msg.sender]`이 이미 line 112에서 감소됨 -> `changed(..., false)` **violated**
- Correct: checkpoint를 먼저 호출 -> balance 변경 전에 checkpoint 실행 -> `changed(..., false)` **satisfied**
- 실행 순서(ordering) 문제를 변수 변경 여부로 간접 감지.

**왜 Strong이 아닌가**: 근본 문제는 "checkpoint가 balance 변경 전에 실행되어야 한다"는 ordering 제약. `changed(var, false)`는 이 ordering을 간접적으로 표현하는 것이며, 정확한 값이나 관계를 명시하지 않음.

---

## Reclassified to L4 (formerly "Not possible" -- 11 cases)

이전 버전에서 "Not possible"로 분류되었던 11건은 `evaluation/RQ1/limitation_types.md`의 L4 (annotation-inexpressible) 카테고리로 이동되었다. 해당 케이스들은 bug awareness가 있어도 IntentChecker의 annotation 모델로 표현 자체가 불가능한 구조적 한계 케이스이며, L5(bug-awareness-required)의 정의("표현은 가능하나 버그 인지를 전제")에 부합하지 않기 때문이다.

### 재분류 매핑

| 케이스 | 새 분류 | 이동 이유 |
|--------|---------|----------|
| **web3bugs_36_H_02** (Basket.auctionBurn) | **L4d** (invariant-masked, 신규) | `handleFees`가 동일 함수 내에서 이미 `ibRatio`를 갱신하여 `changed()`가 buggy/correct 구분 불가. Product invariant `ibRatio * totalSupply` 표현 필요하나 PostEntryExit에서 산술 미지원 |
| **web3bugs_35_H_10** (ConcentratedLiquidityPool.burn) | **L4c** (magnitude-only, 신규) | `reserve0 -= amount0fees` (buggy) vs `reserve0 -= amount0` (correct). 둘 다 동일 방향으로 감소, 차이는 magnitude뿐 |
| **web3bugs_62_H_01** (Stream.recoverTokens) | **L4b** (no-target-storage) | `recoverTokens`가 자체 state 수정하지 않음 |
| **web3bugs_58_H_04** (AaveVault.tvl) | **L4b** (no-target-storage) | View 함수 |
| **web3bugs_61_H_02** (SavingsAccountUtil) | **L4a** (inexpressible-expected-value) | Library, 폐기된 외부 호출 return value를 담는 변수가 코드에 없음 |
| **web3bugs_70_H_08** (VaderReserve.reimburseImpermanentLoss) | **L4b** (no-target-storage) | 자체 state 수정 없음 |
| **web3bugs_110_H_01** (StakedCitadel.balance) | **L4b** (no-target-storage) | View 함수 |
| **web3bugs_17_H_02** (Buoy3Pool.safetyCheck) | **L4b** (no-target-storage) | View 함수 |
| **web3bugs_52_H_15** (VaderRouter._swap) | **L4b** (no-target-storage) | 자체 state 수정 없음, 외부 pool 호출만 |
| **web3bugs_52_H_16** (VaderRouter.calculateOutGivenIn) | **L4b** (no-target-storage) | View 함수 |
| **web3bugs_59_H_05** (AuctionEscapeHatch.exitEarly) | **L4a** (inexpressible-expected-value) | 올바른 값이 외부 Auction contract state(`userMaltPurchased`, `userCommitment`)에 의존 |

### 재분류 후 카운트

| 분류 | 이전 | 이후 |
|------|------|------|
| L4 (전체) | 9건 | **20건** |
| L5 (전체) | 25건 | **14건** (Strong 7 + Weak 7) |
| L4 + L5 | 34건 | 34건 (불변) |

상세 설명은 `evaluation/RQ1/limitation_types.md` 참조.
