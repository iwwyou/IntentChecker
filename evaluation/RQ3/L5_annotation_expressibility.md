# L5 Annotation Expressibility Analysis

Bug-awareness-required (L5) 케이스 25건에 대해, **버그를 인지한 상태에서** IntentChecker의 annotation 모델로 표현 가능한지를 분석한 문서.

## 분류 기준

| 분류 | 정의 | Annotation 유형 |
|------|------|----------------|
| **Direct** | Bug를 인지한 상태에서, annotation이 올바른 값/관계를 직접 명시하여 buggy code에서 violation 발생. Annotation = fix | `@During var relOp expr`, `@Post var relOp expr` (CommonClause: RelationalCmp) |
| **Indirect** | 변수의 변경 여부 또는 변경 방향만 감지. 정확한 올바른 값은 명시하지 않음 | `changed(var, true/false)` (VarChangedEval), `var(Entry relOp Exit)` (PostEntryExit) |
| **Not possible** | Bug를 알아도 annotation 문법/구조상 표현 불가. 대상 변수 없음, view 함수, magnitude만 다름 등 | N/A |

### Direct vs Indirect 구분

- **Direct**: CommonClause의 `var relOp expr` -- **올바른 값 자체를 명시** (annotation = fix)
- **Indirect**: `changed(var, true)` 또는 `var(Entry relOp Exit)` -- **변경 여부/방향만 감지** (올바른 값은 미명시)

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
| **Direct** | 2 | 5 | **7** (28%) |
| **Indirect** | 5 | 2 | **7** (28%) |
| **Not possible** | 8 | 3 | **11** (44%) |
| **합계** | 15 | 10 | **25** |

---

## Direct -- 7건

---

### 1. web3bugs_62_H_10 (L5a: missing-code)

- **Contract**: Stream
- **Function**: creatorClaimSoldTokens
- **Bug**: `ERC20(depositToken).safeTransfer(destination, amount)` 이후 `depositTokenAmount` 또는 `redeemedDepositTokens` 갱신 누락. 이후 `recoverTokens()`에서 `depositTokenAmount - redeemedDepositTokens`가 여전히 원래 값이라 excess 계산 오류.
- **Bug report**: 62.md H-10

**Annotation**:
```
// @Post depositTokenAmount == 0
```

**문법**: CommonClause (RelationalCmp). Exit 시점의 `depositTokenAmount`를 0과 비교.

**왜 Direct인가**:
- Buggy: `depositTokenAmount`이 원래 값 유지 (> 0) -> `== 0` **violated**
- Correct: 전체 deposit token을 claim 후 `depositTokenAmount = 0` (또는 `redeemedDepositTokens = depositTokenAmount`) -> **satisfied**
- 함수 완료 후 deposit token 잔여가 0이어야 한다는 의도를 직접 명시.

**참고**: Fix는 `redeemedDepositTokens = depositTokenAmount`이 더 정확하므로 `@Post redeemedDepositTokens == depositTokenAmount`도 가능.

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

**왜 Direct인가**:
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

**왜 Direct인가**:
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

**왜 Direct인가**:
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

**문법**: DuringCommon -> CommonClause (RelationalCmp). intentValue에 산술 표현(`wavaxReserve * 1e18 / floorPrice`) 사용.

**왜 Direct인가**:
- Buggy: `tokenAllocated = wavaxReserve * 10**decimals / floorPrice` -> decimals != 18이면 다른 값 -> **violated**
- Correct: `tokenAllocated = wavaxReserve * 1e18 / floorPrice` -> **satisfied**
- Annotation이 올바른 수식을 직접 명시. Fix와 동일.

---

### 6. web3bugs_101_H_02 (L5b: wrong-code)

- **Contract**: LenderPool
- **Function**: terminate
- **Bug**: `_principalWithdrawable`가 token amount 단위로 계산되지만 `withdrawShares()`에 share amount로 전달됨 (단위 혼동). 올바른 값은 단순히 `_sharesHeld` (전체 share 인출).
- **Bug report**: 101.md H-02

**Annotation**:
```
// @During _totalBorrowAsset == _sharesHeld
```

**문법**: DuringCommon -> CommonClause (RelationalCmp). 두 local variable 비교.

**왜 Direct인가**:
- Buggy: `_totalBorrowAsset`이 복잡한 token/share 혼합 계산으로 산출 -> `_sharesHeld`와 다름 -> **violated**
- Correct: `_totalBorrowAsset = _sharesHeld` (단순 전체 인출) -> **satisfied**
- Annotation이 "terminate 시 전체 shares를 인출해야 한다"는 의도를 직접 명시.

---

### 7. web3bugs_70_H_09 (L5b: wrong-code)

- **Contract**: USDV
- **Function**: mint
- **Bug**: `uAmount = (vPrice * vAmount) / 1e18` (곱셈)이지만, oracle 가격 의미상 올바른 공식은 `uAmount = vAmount * 1e18 / vPrice` (나눗셈). 가격 방향 오류로 민팅량 왜곡.
- **Bug report**: 70.md H-09. **주의**: Sponsor가 dispute했으나 최종 보고서에 유지됨.

**Annotation**:
```
// @During uAmount == vAmount * 1e18 / vPrice
```

**문법**: DuringCommon -> CommonClause (RelationalCmp). 산술 표현.

**왜 Direct인가**:
- Buggy: `uAmount = vPrice * vAmount / 1e18` -> `vPrice != 1e18`이면 다른 값 -> **violated**
- Correct: `uAmount = vAmount * 1e18 / vPrice` -> **satisfied**
- Annotation이 올바른 변환 공식을 직접 명시.

**Caveat**: Sponsor dispute. 논문에서 이 점 언급 필요.

---

## Indirect -- 7건

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

**왜 Indirect인가**:
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

**왜 Indirect인가**:
- Buggy: `rewardTokenAmount` 불변 -> Entry == Exit -> `Entry > Exit` **violated**
- Correct: `rewardTokenAmount -= rewardAmt` -> Entry > Exit -> **satisfied**
- "rewardTokenAmount는 감소해야 한다"는 방향만 명시. 정확한 감소량(`rewardAmt`)은 표현하지 않음.

---

### 3. web3bugs_52_H_23 (L5a: missing-code)

- **Contract**: VaderPoolV2
- **Function**: mintSynth
- **Bug**: `_update(foreignAsset, reserveNative + nativeDeposit, reserveForeign, ...)` 호출 시 `reserveForeign`이 감소 없이 그대로 전달됨. Synth 민팅은 경제적으로 foreign reserve를 소비하는 것이므로 `reserveForeign - amountSynth`이어야 함. 미감소로 인해 synth 과다 발행.
- **Bug report**: 52.md H-23

**Annotation**:
```
// @Post reserveForeign(Entry > Exit)
```

**문법**: PostEntryExit. `reserveForeign`은 `_update()`를 통해 `pairInfo[foreignAsset].reserveForeign`에 기록되는 state variable.

**왜 Indirect인가**:
- Buggy: `_update`가 `reserveForeign`(원래 값)을 기록 -> Entry == Exit -> `Entry > Exit` **violated**
- Correct: `_update`가 `reserveForeign - amountSynth`를 기록 -> Entry > Exit -> **satisfied**
- "synth 민팅 후 foreign reserve는 감소해야 한다"는 방향만 명시. 정확한 감소량(`amountSynth`)은 표현하지 않음.

**이전 분류**: Not possible -> **Indirect로 승격**. `.sol` 파일의 state variable 재검토에서 `reserveForeign`이 `_update()`를 통해 storage에 기록되는 것을 확인.

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

**왜 Indirect인가**:
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

**왜 Indirect인가**:
- Buggy: `massUpdatePools()` 미호출 -> 기존 풀의 `accConcurPerShare` 불변 -> **violated**
- Correct: `massUpdatePools()` 호출 -> `accConcurPerShare` 갱신 -> **satisfied**
- 변경 여부만 감지.

**왜 Direct가 아닌가**: `accConcurPerShare`의 올바른 값은 `concurPerBlock`, `totalAllocPoint`, `block.number` 등 여러 변수의 복합 계산에 의존. 이를 intentValue의 산술 표현으로 구성하기 어려움.

**주의**: 기존 풀이 없는 상태(첫 `add()` 호출)에서는 `poolInfo[0]`이 존재하지 않아 annotation 무의미. 기존 풀 + active staker가 있을 때만 유효.

---

### 6. web3bugs_35_H_11 (L5b: wrong-code)

- **Contract**: Ticks (library)
- **Function**: cross
- **Bug**: `zeroForOne` 분기에서 (1) `nextTickToCross`를 `previousTick`으로 재할당(line 39) 후 (2) `feeGrowthOutside0`를 업데이트(line 40). 두 가지 오류: (a) 포인터 이동 후 잘못된 tick에 적용, (b) `feeGrowthOutside0` 대신 `feeGrowthOutside1`이어야 함.
- **Bug report**: 35.md H-11

**Annotation**:
```
// @Post changed(ticks[nextTickToCross].feeGrowthOutside1, true)
```

**문법**: CommonClause (VarChangedEval). `ticks[nextTickToCross].feeGrowthOutside1`은 mapping struct field. `nextTickToCross`는 함수 파라미터로, `@Post`에서 Entry 시점의 값으로 바인딩.

**왜 Indirect인가**:
- Buggy (`zeroForOne`): 원래 tick의 `feeGrowthOutside1`이 아닌 새 tick의 `feeGrowthOutside0`이 업데이트됨 -> 원래 tick의 `feeGrowthOutside1` 불변 -> **violated**
- Correct: 원래 tick의 `feeGrowthOutside1`이 `feeGrowthGlobal1 - feeGrowthOutside1`로 업데이트됨 -> **satisfied**
- 변경 여부만 감지하며, 어떤 값으로 변해야 하는지는 명시하지 않음.

**왜 Direct가 아닌가**: `feeGrowthOutside1`의 새 값은 `feeGrowthGlobal1 - ticks[nextTickToCross].feeGrowthOutside1`인데, 이 XOR 패턴은 증가/감소 방향이 고정되지 않아 `Entry relOp Exit`로 방향을 명시할 수 없음. `changed`만 가능.

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

**왜 Indirect인가**:
- Buggy: line 117 시점에서 `balances[msg.sender]`이 이미 line 112에서 감소됨 -> `changed(..., false)` **violated**
- Correct: checkpoint를 먼저 호출 -> balance 변경 전에 checkpoint 실행 -> `changed(..., false)` **satisfied**
- 실행 순서(ordering) 문제를 변수 변경 여부로 간접 감지.

**왜 Direct가 아닌가**: 근본 문제는 "checkpoint가 balance 변경 전에 실행되어야 한다"는 ordering 제약. `changed(var, false)`는 이 ordering을 간접적으로 표현하는 것이며, 정확한 값이나 관계를 명시하지 않음.

---

## Not possible -- 11건

---

### 1. web3bugs_36_H_02 (L5a: missing-code)

- **Contract**: Basket
- **Function**: auctionBurn
- **Bug**: `handleFees()` 후 `_burn(msg.sender, amount)` 실행 시 `totalSupply` 감소. 그러나 `ibRatio`가 이에 비례하여 증가하지 않아 product invariant `ibRatio * totalSupply` 붕괴. 기존 holders의 underlying token 가치 희석.
- **Bug report**: 36.md H-02

**왜 Not possible인가**:
1. `changed(ibRatio, true)` -- `handleFees()`가 이미 `ibRatio`를 변경하므로 buggy code에서도 **satisfied**
2. `ibRatio(Entry != Exit)` -- 역시 handleFees에 의해 변경됨 -> buggy에서도 **satisfied**
3. Product invariant `ibRatio * totalSupply(Entry == Exit)`로 감지 가능하나, **PostEntryExit에서 산술 표현은 도구에서 미지원**
4. `ibRatio`의 올바른 최종 값은 handleFees의 중간 결과에 의존하여 CommonClause로도 표현 불가

**확인한 state variables**: ibRatio, lastFee, tokens, weights, publisher, factory, auction 등 + inherited ERC20 (`_totalSupply`, `_balances`) -- 모두 handleFees에 의해 이미 변경되거나 무관.

---

### 2. web3bugs_35_H_10 (L5a: missing-code)

- **Contract**: ConcentratedLiquidityPool
- **Function**: burn
- **Bug**: `reserve0 -= uint128(amount0fees)` (line 264)만 존재. 올바른 코드는 `reserve0 -= uint128(amount0)` (전체 인출량). Fees만 차감되고 원금은 차감되지 않아 reserve 과대 계상.
- **Bug report**: 35.md H-10

**왜 Not possible인가**:
1. `reserve0`는 buggy code에서도 **감소함** (fees만큼) -> `changed(reserve0, true)` **satisfied** (buggy에서도)
2. `reserve0(Entry > Exit)` -- buggy에서도 Entry > Exit (감소 방향 동일) -> **satisfied** (buggy에서도)
3. 차이는 **감소 크기**(magnitude)뿐: buggy = amount0fees, correct = amount0. 문법상 Entry와 Exit의 차이값을 비교하는 구문 없음
4. 부가적으로 `abi.decode`로 파라미터 전달 -> amount0, amount0fees를 debugging annotation으로 설정 불가

**확인한 state variables** (14개): liquidity, secondsPerLiquidity, lastObservation, feeGrowthGlobal0/1, barFee, token0/1ProtocolFee, reserve0/1, price, nearestTick, unlocked, ticks, positions -- 모두 방향이 동일하거나 무관.

---

### 3. web3bugs_62_H_01 (L5a: missing-code)

- **Contract**: Stream
- **Function**: recoverTokens
- **Bug**: Excess 계산에서 `depositTokenFlashloanFeeAmount` 차감 누락. `excess = balanceOf(this) - (depositTokenAmount - redeemedDepositTokens)`이지만, 올바른 공식은 `- depositTokenFlashloanFeeAmount` 추가.
- **Bug report**: 62.md H-01

**왜 Not possible인가**:
1. `recoverTokens()`는 **state variable을 수정하지 않음**. 로컬 `excess` 계산 후 `safeTransfer`만 수행
2. `changed(var, true/false)` 대상이 없음 -- 어떤 state variable도 Entry와 Exit 사이에 변하지 않음 (unlocked lock 제외)
3. `balanceOf(this)`는 함수 호출이므로 intentValue에 사용 불가
4. `returnExpression` -- 함수가 값을 return하지 않음

**확인한 state variables** (12개): rewardTokenAmount, depositTokenAmount, rewardTokenFeeAmount, depositTokenFlashloanFeeAmount, unlocked, claimedDepositTokens, cumulativeRewardPerToken, totalVirtualBalance, unstreamed, redeemedDepositTokens, lastUpdate, tokensNotYetStreamed -- recoverTokens에서 수정되는 것 없음.

---

### 4. web3bugs_58_H_04 (L5a: missing-code)

- **Contract**: AaveVault
- **Function**: tvl (view) / _push
- **Bug**: `tvl()`이 cached `_tvls` 반환. aToken의 rebasing interest가 반영되지 않음. `_push()`에서 deposit 후 `updateTvls()` 호출하지만, 호출 순서가 늦어 stale 값 사용.
- **Bug report**: 58.md H-04

**왜 Not possible인가**:
1. `tvl()`은 **view 함수** -- state 수정 없음
2. `_push()`에서 `_tvls`는 **결국 업데이트됨** (updateTvls 호출). Buggy와 correct 모두 `changed(_tvls, true)` satisfied
3. 문제는 **operation ordering**: 언제 업데이트하느냐 (deposit 전 vs 후). Annotation은 함수 시작/종료 시점의 값만 비교하며, 함수 내부의 실행 순서를 표현할 수 없음
4. `@During` standalone으로 특정 지점에서 `_tvls` 값을 체크할 수 있지만, 올바른 값은 `aToken.balanceOf(address(this))`(함수 호출)이므로 intentValue에 표현 불가

**확인한 state variables**: `_aTokens`, `_tvls` + inherited Vault vars -- ordering 문제로 값 수준 비교 불가.

---

### 5. web3bugs_61_H_02 (L5a: missing-code)

- **Contract**: SavingsAccountUtil (library)
- **Function**: savingsAccountTransfer
- **Bug**: `_savingsAccount.transfer()` / `transferFrom()`의 return value(실제 전송된 shares)를 폐기하고 항상 `_amount`(입력 파라미터)를 return. pps != 1일 때 잘못된 값 반환.
- **Bug report**: 61.md H-02

**왜 Not possible인가**:
1. **Library** -- 자체 state variable 없음
2. 폐기된 return value를 담는 변수가 코드에 존재하지 않음 -> 참조할 대상 없음
3. `returnExpression relOp intentValue` -- 올바른 return 값은 외부 호출의 return value이며, 이를 intentValue로 표현 불가 (함수 호출 미지원)
4. `returnExpression != _amount` -- pps == 1이면 둘이 같으므로 false positive 발생

---

### 6. web3bugs_70_H_08 (L5a: missing-code)

- **Contract**: VaderReserve
- **Function**: reimburseImpermanentLoss
- **Bug**: Fixed-point scaling 오류. `amount / usdvPrice` (missing `* 1e18`)와 `amount * vaderPrice` (missing `/ 1e18`). 두 분기에서 반대 방향 오류 (과소/과다 지급).
- **Bug report**: 70.md H-08

**왜 Not possible인가**:
1. 함수가 **state variable을 수정하지 않음**. `vader.safeTransfer(pool, actualAmount)`만 수행
2. Contract의 state variables: `router`, `lastGrant`, `lbt` -- 모두 이 함수에서 미수정
3. `returnExpression` -- 함수가 값을 return하지 않음
4. 로컬 `amount` 변수에 `@During`을 걸 수 있으나, 올바른 값을 표현하려면 `Before(amount)`를 다른 expression과 결합해야 하며 이는 문법상 불가 (Entry/Exit는 PostEntryExit에서만 사용 가능)

---

### 7. web3bugs_110_H_01 (L5a: missing-code)

- **Contract**: StakedCitadel
- **Function**: balance (view)
- **Bug**: `balance()` = `token.balanceOf(address(this))` 반환. 올바른 값은 `+ IStrategy(strategy).balanceOf()` 추가. Strategy에 배치된 자금이 누락되어 share 가격 왜곡.
- **Bug report**: 110.md H-01

**왜 Not possible인가**:
1. `balance()`는 **view 함수** -- state 수정 없음
2. 올바른 return 값에 `IStrategy(strategy).balanceOf()` (외부 호출)가 포함되어야 하며, 이를 intentValue로 표현 불가
3. Caller `_depositFor()`에서 간접적으로 share가 과다 발행되지만, 과다 발행의 크기(magnitude)만 다르고 방향은 동일 (totalSupply 증가)
4. `returnExpression` -- `balance()` 자체의 return을 annotation할 수 있으나, 올바른 기대값을 표현할 방법 없음

**확인한 state variables** (20+개): strategy, token, guestList, fees, lifeTimeEarned 등 -- `balance()`에서 수정 없음. Caller에서도 magnitude만 차이.

---

### 8. web3bugs_17_H_02 (L5a: missing-code)

- **Contract**: Buoy3Pool
- **Function**: safetyCheck (view)
- **Bug**: a/b와 a/c ratio만 검사하고 b/c ratio를 검사하지 않음. Transitivity에 의해 b/c는 최대 2 * BASIS_POINTS까지 벗어날 수 있음.
- **Bug report**: 17.md H-02

**왜 Not possible인가**:
1. **View 함수** -- state 수정 없음
2. `returnExpression == false` -- 특정 debug 값(b/c가 벗어나지만 a/b, a/c는 통과)에서 가능하나, 올바른 return 값이 조건부이며 그 조건(b/c ratio)을 intentValue로 표현 불가
3. 기존 검증 로직은 모두 올바름 -- 추가 검증이 통째로 누락된 패턴. "존재하지 않는 로직"에 대한 annotation은 구조적으로 불가

**확인한 state variables** (5개): TIME_LIMIT, BASIS_POINTS, lastRatio, tokenRatios -- view 함수에서 수정 없음.

---

### 9. web3bugs_52_H_15 (L5b: wrong-code)

- **Contract**: VaderRouter
- **Function**: _swap
- **Bug**: 3-path swap에서 `pool1.swap(0, pool0.swap(amountIn, 0, addr), to)` -- 인자 순서 뒤바뀜. 올바른 호출은 `pool1.swap(pool0.swap(0, amountIn, addr), 0, to)`.
- **Bug report**: 52.md H-15

**왜 Not possible인가**:
1. VaderRouter의 state variables: `factory` (immutable), `reserve` -- `_swap()`에서 **미수정**
2. `DuringFunctionArg`: `swap.arg[1] == 0` -- 문법상 파싱 가능하나, nested call에서 어느 `swap`을 참조하는지 모호. 또한 swap direction 지식(= bug awareness)이 전제
3. `returnExpression` -- _swap()은 `uint256 amountOut`을 return하지만, 올바른 값은 chained pool.swap 호출 결과이며 intentValue로 표현 불가
4. 외부 pool contract의 reserve가 변경되지만 이는 VaderRouter의 state가 아님

---

### 10. web3bugs_52_H_16 (L5b: wrong-code)

- **Contract**: VaderRouter
- **Function**: calculateOutGivenIn (view)
- **Bug**: 3-path 계산에서 pool0과 pool1의 reserve가 뒤바뀜. `calculateSwap(calculateSwap(amountIn, nativeReserve1, foreignReserve1), foreignReserve0, nativeReserve0)` -> 올바른 순서는 반대.
- **Bug report**: 52.md H-16

**왜 Not possible인가**:
1. **View 함수** -- state 수정 없음
2. State variables: `pool` (immutable), `nativeAsset` (immutable), `reserve` -- 미수정
3. `returnExpression` -- return 값은 있으나, 올바른 기대값은 chained `calculateSwap()` 호출이며 intentValue에 함수 호출 표현 불가
4. reserve 값 자체는 올바르게 읽힘 (interface call support) -- 문제는 순서뿐이며 이는 값 수준 annotation으로 표현 불가

---

### 11. web3bugs_59_H_05 (L5b: wrong-code)

- **Contract**: AuctionEscapeHatch
- **Function**: exitEarly
- **Bug**: `_calculateMaltRequiredForExit`가 penalty-adjusted `maltQuantity`를 반환. 이 값이 `auction.amendAccountParticipation()`의 4번째 인자로 전달되지만, accounting에는 원래(pre-penalty) 값이 사용되어야 함. Ratio `userMaltPurchased/userCommitment` 왜곡.
- **Bug report**: 59.md H-05

**왜 Not possible인가**:
1. `auctionEarlyExits[_auctionId].maltUsed += maltQuantity` -- buggy `maltQuantity`를 **충실히 기록**. State variable 값 자체에 이상 없음 (기록된 값 = 실제 사용된 값)
2. 올바른 값(pre-penalty maltQuantity)은 `userMaltPurchased * amount / userCommitment`이지만, `userMaltPurchased`와 `userCommitment`는 **외부 Auction contract의 state**에서 읽어오므로 intentValue로 표현 불가
3. `DuringFunctionArg`: `amendAccountParticipation.arg[3]`의 올바른 값을 표현하려면 외부 state 참조 필요
4. 자체 contract의 state에서는 buggy와 correct의 **질적 차이가 없음** -- 둘 다 각자의 maltQuantity를 올바르게 기록

**확인한 state variables**: auction, dexHandler, collateralToken, malt, maxEarlyExitBps, cooloffPeriod, auctionEarlyExits -- auctionEarlyExits가 수정되나 buggy 값을 충실히 기록.

---

## Not Possible 패턴 요약

| 패턴 | 해당 케이스 | 설명 |
|------|-----------|------|
| **View 함수** | 17_H_02, 110_H_01, 52_H_16 | State 수정 없음. returnExpression으로도 올바른 기대값 표현 불가 |
| **State 미수정 함수** | 62_H_01, 70_H_08, 52_H_15 | 함수가 state variable을 수정하지 않아 annotation 대상 없음 |
| **Magnitude만 차이** | 35_H_10 | State variable이 buggy에서도 올바른 방향으로 변경됨. 크기만 다르나 문법상 차이 표현 불가 |
| **Ordering 문제** | 58_H_04 | State는 결국 올바르게 업데이트되나 시점이 잘못됨 |
| **외부 state 의존** | 59_H_05 | 올바른 값이 외부 contract state에 의존 |
| **변수 부재** | 61_H_02 | 올바른 값을 담는 변수가 코드에 존재하지 않음 (library) |
| **기존 변경으로 masking** | 36_H_02 | 동일 함수 내 다른 코드가 이미 대상 변수를 변경하여 changed/Entry-Exit 통과 + 도구 미지원 문법 |
