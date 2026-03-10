# RQ2 Annotation Plans

컨트랙트별 contraction/annotation 계획을 추적하는 문서.
- case JSON 생성 전 단계에서 논의된 내용을 기록
- contraction 완료 후 case JSON으로 옮김

---

## web3bugs_35_H_12

- **Contract**: ConcentratedLiquidityPool
- **Function**: mint
- **Bug lines (original)**: 176; 184
- **Pattern**: erroneous_accounting
- **Status**: contraction 대기

### Dependencies
**Interfaces** (6):
- IPool, IBentoBoxMinimal, IMasterDeployer, IPositionManager, ITridentCallee, ITridentRouter

**Libraries** (6):
- DyDxMath, Ticks, FullMath, TickMath, UnsafeMath, SwapLib

### Debug Annotations
| Type | Variable | Comment |
|------|----------|---------|
| StateVar | secondsPerLiquidity | 유일하게 추적 가능한 상태변수 |

### Debug Annotation 제한 사유
mint 함수의 주요 파라미터가 아래 패턴으로 전달됨:
```solidity
MintParams memory mintParams = abi.decode(data, (MintParams));
```
- `data`는 `bytes calldata` → `abi.decode`로 memory struct에 할당
- IntentChecker는 bytes 레벨 할당(abi.decode)에서 개별 struct 필드를 추적할 수 없음
- 따라서 mintParams.lowerOld, mintParams.lower 등 함수 파라미터에 debug annotation 부여 불가
- 만약 mapping → struct (상태변수)였다면 필드 단위 추적 가능했을 것

### Intent Annotations
| Type | Line | Expression | Expected | Comment |
|------|------|------------|----------|---------|
| During | 229 | Changed(secondsPerLiquidity) | violated | secondsPerLiquidity가 mint 내에서 갱신되어야 하나 실제로 안 됨 |

---

## web3bugs_43_H_02

- **Contract**: DelegatedStaking
- **Function**: unstake
- **Bug lines (original)**: 223; 224; 226
- **Pattern**: erroneous_accounting
- **Status**: excluded_fixed_code

### Notes
- 현재 코드가 이미 수정된 버전 (exchange rate 업데이트가 shares 계산 전에 호출됨)
- 탐지할 버그가 없으므로 데이터셋에서 제외

---

## web3bugs_45_H_01

- **Contract**: UToken
- **Function**: borrow
- **Bug lines (original)**: 403; 409; 413
- **Bug lines (contraction)**: 203; 205; 207; 213
- **Pattern**: erroneous_accounting
- **Status**: contraction 진행중

### Dependencies
**Contracts**:
- Controller, ReentrancyGuardUpgradeable, SafeERC20Upgradeable

**Interfaces**:
- IInterestRateModel, IUErc20, IUserManager, IAssetManager

**Libraries**:
- interestRateModel, assetManagerContract

**구현 필요**:
- `using SafeERC20Upgradeable for IUErc20;`

### Intent Annotations
| Type | Line (contraction) | Expression | Expected | Comment |
|------|-------------------|------------|----------|---------|
| During | 203, 205, 207, 213 | borrowIndex(Before < After) | violated | accrueInterest() 호출 전이므로 borrowIndex 미갱신 → Before == After → 위반 |

※ Z3 solver로 방향 확정: Before < After ✓ (z3_solvers/web3bugs_45_H_01_solver.py)

### Debug Annotations (Z3 생성값)
**LocalVar:**
| # | Variable | Value (interval) | Comment |
|---|----------|-------------------|---------|
| 1 | amount | [1000000000000000001, 1000000000000000001] | ~1e18 (1 token in wei) |
| 2 | account | symbolicAddress 101 | msg.sender와 일치 |

**StateVar:**
| # | Variable | Value (interval) | Comment |
|---|----------|-------------------|---------|
| 1 | minBorrow | [2, 2] | require 통과용 |
| 2 | debtCeiling | [1000000000000000002, 1000000000000000002] | getRemainingLoanSize용 |
| 3 | totalBorrows | [0, 0] | getRemainingLoanSize용 |
| 4 | originationFee | [1000000000000001, 1000000000000001] | ~0.1%, fee 계산용 |
| 5 | WAD | [1000000000000000000, 1000000000000000000] | 1e18 |
| 6 | accountBorrows[101].principal | [1000000000000000001, 1000000000000000001] | ~1e18 |
| 7 | accrualBlockNumber | [1, 1] | blockDelta 계산용 |
| 8 | borrowIndex | [1000000000000000001, 1000000000000000001] | ~1e18, intent 대상 |
| 9 | accountBorrows[101].interest | [1, 1] | calculatingInterest용 |
| 10 | accountBorrows[101].interestIndex | [1000000000000000001, 1000000000000000001] | ~1e18 |
| 11 | accountBorrows[101].lastRepay | [1, 1] | checkIsOverdue 통과용 |
| 12 | maxBorrow | [2001005000000000005, 2001005000000000005] | require 통과용 |
| 13 | overdueBlocks | [2, 2] | checkIsOverdue 통과용 |

**GlobalVar:**
| # | Variable | Value (interval) | Comment |
|---|----------|-------------------|---------|
| 1 | block.number | [2, 2] | blockDelta = 1 |

**중간 계산값 (검증용):**
- fee = 1000000000000001 (~1e15)
- blockDelta = 1
- borrowIndexNew = 1000005000000000001
- calculatingInterest = 5000000000001
- borrowBalanceView = 1000005000000000002

### 값 생성 조건 (Z3 constraint)
```
C1: debtCeiling > totalBorrows
    근거: if (debtCeiling >= totalBorrows) {return debtCeiling - totalBorrows;} (getRemainingLoanSize)

C2: amount >= minBorrow
    근거: require(amount >= minBorrow) (borrow)

C3: amount <= debtCeiling - totalBorrows
    근거: require(amount <= getRemainingLoanSize()) (borrow)

C4: accountBorrows[101].principal >= 1
    근거: if (loan.principal == 0) {return 0;} (calculatingInterest)

C5: block.number > accrualBlockNumber
    근거: uint256 blockDelta = currentBlockNumber - accrualBlockNumber; (calculatingInterest)

C6: overdueBlocks >= block.number - accountBorrows[101].lastRepay
    근거: require(!checkIsOverdue(msg.sender)) (borrow) — principal > 0이므로 else 분기, 연체 아닌 조건

C7: (((accountBorrows[101].principal + accountBorrows[101].interest)
      * ((0.0005e16 * (block.number - accrualBlockNumber) * borrowIndex) / WAD + borrowIndex))
      / accountBorrows[101].interestIndex)
    - accountBorrows[101].principal >= 1
    근거: calculatingInterest 반환값이 의미 있어야 함

C8: accountBorrows[101].principal
    + C7의 calculatingInterest 결과
    + amount + (originationFee * amount) / WAD
    <= maxBorrow
    근거: require(borrowBalanceView(msg.sender) + amount + fee <= maxBorrow) (borrow)
```

### Notes
- 버그: accrueInterest()가 borrowBalanceView()/getCreditLimit() 체크 뒤에 호출됨
- borrowBalanceView() → calculatingInterest() → borrowIndex(상태변수) 읽음
- accrueInterest() 미호출 시 borrowIndex 변화 없음 → stale 값으로 대출 한도 검사
- Changed(borrowIndex)로도 탐지 가능하나, Before < After가 더 정밀 (증가 방향 명시)
- checkIsOverdue 통과: principal > 0일 때 else 분기로 가서 overdueBlocks >= diff 이면 false 반환

---

## web3bugs_45_H_02

- **Contract**: CreditLimitByMedian
- **Function**: getLockedAmount
- **Bug lines (original)**: 66
- **Pattern**: erroneous_accounting
- **Status**: not_detectable (loop-body-granularity)

### Bug Description
`getLockedAmount()`의 for loop 내에서 `newLockedAmount = array[i].lockedAmount - 1`로 되어 있으나, 올바른 구현은 `array[i].lockedAmount - amount`여야 함. `1`이 하드코딩되어 있어서 lockedAmount가 제대로 unlock되지 않음.

### 탐지 불가 사유
IntentChecker는 loop를 statement 단위로 분석하지 않고 **fixed-point iteration**으로 loop 전체의 수렴값을 계산함. 따라서:
- Loop body 내부의 개별 statement에 intent annotation을 배치할 수 없음
- `newLockedAmount = array[i].lockedAmount - 1` vs `- amount` 같은 loop 내부 wrong-value 버그는 intent로 표현 불가
- Loop 밖에서 최종 반환값에 대한 annotation은 가능하나, fixed-point 결과가 이미 imprecise하므로 의미 있는 탐지가 어려움

### 버그 코드
```solidity
for (uint256 i = 0; i < array.length; i++) {
    if (array[i].lockedAmount > amount) {
        newLockedAmount = array[i].lockedAmount - 1;  // BUG: should be `- amount`
    } else {
        newLockedAmount = 0;
    }
    if (account == array[i].staker) {
        return newLockedAmount;
    }
}
```

---

## web3bugs_83_H_01

- **Contract**: MasterChef
- **Function**: add
- **Bug lines (original)**: 89 (totalAllocPoint 변경 전 massUpdatePools() 호출 누락)
- **Pattern**: inconsistent_state_updates
- **Status**: not_detectable (L4b: missing-call-no-effect)

### Bug Description
`add()` 함수에서 `totalAllocPoint`을 증가시키기 전에 `massUpdatePools()`를 호출하지 않음. 기존 풀들의 `accConcurPerShare`가 이전의 `totalAllocPoint`로 갱신되지 않은 채 새로운 (더 큰) `totalAllocPoint`가 적용되어, 기존 staker들의 reward가 소급적으로 희석됨.

### 탐지 불가 사유
`add()` 함수 내 실제 사용 변수(`totalAllocPoint`, `poolInfo`, `pid[_token]`)는 모두 자기 역할을 올바르게 수행하며 값 수준의 이상이 없음. 버그의 효과(기존 풀의 `accConcurPerShare` 미갱신)는 `add()` scope 밖의 변수에만 나타남.

- `poolInfo[1].accConcurPerShare(Entry != Exit)` 같은 post condition으로 표현은 가능하나, 개발자가 "기존 풀을 업데이트해야 한다"를 이미 인지해야 작성 가능 → 인지했으면 `massUpdatePools()` 호출을 추가하면 되므로 현실적 검출 시나리오가 아님
- 함수 내 변수만으로는 누락된 side effect를 감지할 수 없음

---

## web3bugs_83_H_02

- **Contract**: MasterChef
- **Function**: deposit
- **Bug lines (original)**: 170; 171; 172
- **Pattern**: erroneous_accounting
- **Status**: not_detectable (L4a: no-target-storage)

### Bug Description
`deposit()`에서 `depositFeeBP > 0`일 때 fee를 계산하여 `user.amount`에서 차감하지만, 그 fee를 받을 수신자(feeRecipient)의 `amount`를 증가시키는 코드가 없음. 결과적으로 deposit fee 만큼의 토큰이 컨트랙트에 영구 lock됨.

### 탐지 불가 사유
IntentChecker의 intent annotation은 **변수의 값에 대한 명제**(proposition)를 검증하는 방식이다. 명제를 세우려면 대상 변수가 코드에 존재해야 하는데, 이 버그는 fee를 credit할 대상 변수(`feeRecipient.amount`)가 코드에 없어 annotation을 구성할 수 없다.

- 기존 변수들은 모두 자기 역할을 올바르게 수행하여 값 수준의 이상이 없음:
  - `user.amount`: `_amount - depositFee`로 정확히 계산됨
  - `depositFee`: 올바르게 계산됨
  - `user.rewardDebt`: 새 amount 기반으로 정확히 재계산됨
- `Before/After`, `Assign/Current`, `Entry/Exit`, CommonClause 어떤 패턴으로도 기존 변수에서 이상을 탐지할 수 없음

### 버그 코드
```solidity
if (_amount > 0) {
    if (pool.depositFeeBP > 0) {
        uint depositFee = _amount.mul(pool.depositFeeBP).div(_perMille);
        user.amount = SafeCast.toUint128(user.amount + _amount - depositFee);
        // BUG: depositFee가 feeRecipient에게 credit되지 않음
    } else {
        user.amount = SafeCast.toUint128(user.amount + _amount);
    }
}
```

---

## web3bugs_3_H_04

- **Contract**: HourlyBondSubscriptionLending
- **Function**: viewHourlyBondAmount
- **Bug lines (original)**: 96; 97
- **Pattern**: erroneous_accounting
- **Status**: not_detectable (loop-widening-precision-loss)

### Bug Description
`viewHourlyBondAmount()`에서 `applyInterest()`의 리턴값 해석이 잘못됨.

**같은 컨트랙트 내 두 가지 사용 패턴:**
```solidity
// (1) updateHourlyBondAmount(): applyInterest = 원금+이자 (full balance) 로 취급
bond.amount = applyInterest(bond.amount, yA.accumulatorFP, yieldQuotientFP);
uint256 deltaAmount = bond.amount - oldAmount;  // delta를 따로 계산

// (2) viewHourlyBondAmount(): applyInterest = 이자만 (delta) 로 취급 → BUG
return bond.amount + applyInterest(bond.amount, cumulativeYield, yieldQuotientFP);
```

`updateHourlyBondAmount()`에서 `deltaAmount = bond.amount - oldAmount`으로 delta를 별도 계산하는 것을 보면, `applyInterest`는 **원금+이자(full balance)를 리턴**하는 함수. 따라서 `viewHourlyBondAmount()`의 `bond.amount + applyInterest(...)`는 원금을 **이중 계산(double-count)**하여 실제보다 약 2배 큰 값을 리턴.

### 탐지 가능성 분석

**후보 Annotation**: `@During returnExpression == <expected_value>` (debug annotation으로 구체적 값 제공)

**문제**: `returnExpression`에 대한 intent를 세우려면 `applyInterest`의 리턴값을 알아야 하는데, 그 값은 `cumulativeYield`에 의존하고, `cumulativeYield`는 `viewCumulativeYieldFP()` → `calcCumulativeYieldFP()`를 통해 계산됨.

### 탐지 불가 사유: calcCumulativeYieldFP의 반복문과 Widening

`calcCumulativeYieldFP()`에는 아래 반복문이 존재:

```solidity
function calcCumulativeYieldFP(
    YieldAccumulator storage yieldAccumulator,
    uint256 timeDelta
) internal view returns (uint256 accumulatorFP) {
    // Step 1: 시간 단위 미만 선형 보간
    uint256 secondsDelta = timeDelta % (1 hours);
    accumulatorFP =
        (yieldAccumulator.accumulatorFP *
            yieldAccumulator.hourlyYieldFP *
            secondsDelta) /
        (FP32 * 1 hours);     // 분모 = 2^32 × 3600 ≈ 1.5×10^13

    // Step 2: 시간 단위 복리 계산 (문제의 반복문)
    uint256 hoursDelta = timeDelta / (1 hours);
    if (hoursDelta > 0) {
        for (uint256 i = 0; i < hoursDelta; i++) {
            accumulatorFP =
                (accumulatorFP * yieldAccumulator.hourlyYieldFP) /
                FP32;
        }
    }
}
```

여기서 FP32 = 2^32 (고정소수점 32비트). 모든 `_FP` 접미사 변수는 실수값 × 2^32 형태.

**반복문의 수학적 의미 (개발자 의도):**
- `hourlyYieldFP`는 시간당 이자율 (예: 1.0001 → FP32로 ≈ 4,295,396,762)
- 매 iteration: `acc = acc × hourlyYield_real` (실수로 풀면 단순 곱셈)
- N시간 후: `acc = acc_initial × hourlyYield^N` (복리 계산)
- 실제 Solidity 실행 시에는 정상 동작

**IntentChecker의 Fixpoint 분석에서 발생하는 문제:**

IntentChecker는 반복문을 **fixpoint iteration + widening**으로 분석:

1. debug annotation으로 `hoursDelta = 2` 지정 시, 2회 반복까지 구체적으로 실행
2. 2회 후에도 fixpoint(수렴)가 안 되면 **widening operator** 적용

반복문 본체 `accumulatorFP = (accumulatorFP * hourlyYieldFP) / FP32`에서:
- `hourlyYieldFP > FP32` (이자율 > 1.0, 정상 케이스): 매 iteration마다 **증가** → fixpoint 불가 → widening → **∞ (inf)**
- `hourlyYieldFP < FP32` (이자율 < 1.0, 비정상): 매 iteration마다 **감소** → fixpoint 불가 → widening → **0**
- `hourlyYieldFP == FP32` (이자율 = 1.0, 비현실적): fixpoint 도달하나 이자 0%로 무의미

**결과적으로 `cumulativeYield`가 0 또는 ∞:**

```solidity
// applyInterest:
return (balance * accumulatorFP) / yieldQuotientFP;
```

- `cumulativeYield = 0` → `applyInterest` = 0 → buggy return = `bond.amount + 0` = `bond.amount`
  - 정상 return도 = `applyInterest(amount, 0, yieldQuotient)` = 0 → 구분 불가
- `cumulativeYield = ∞` → `applyInterest` = ∞ → buggy/correct 모두 ∞ → 구분 불가

두 경우 모두 buggy code와 correct code의 리턴값이 동일하게 되어 **annotation이 위반되지 않으므로 탐지 불가**.

### Step 1 (선형 보간)만으로 우회 가능한가?

`hoursDelta = 0` (timeDelta < 3600)으로 설정하면 반복문을 건너뛸 수 있으나:
```solidity
accumulatorFP = (acc * hourlyYield * secondsDelta) / (FP32 * 3600);
```
분모가 `2^32 × 3600 ≈ 1.5×10^13`이므로:
- 작은 debug 값 (acc=100, hourlyYield=100, secondsDelta=30): 분자 = 300,000 → 정수 나눗셈 → **0**
- FP32 스케일 값 (acc=2^32, hourlyYield=2^32): 의미 있는 결과가 나오지만, 이 경우 `secondsDelta`가 0이면 여전히 0이고, `secondsDelta > 0`이면 결과가 나와도 `applyInterest`까지 정확히 기대값을 계산해야 함 → diagnostic annotation 성격

### 요약

| 구분 | 내용 |
|------|------|
| **Limitation 유형** | loop-widening-precision-loss |
| **근본 원인** | `calcCumulativeYieldFP`의 반복문이 고정소수점 복리 계산 → 매 iteration 값 변화 → fixpoint 미수렴 → widening으로 0 또는 ∞ |
| **영향** | `cumulativeYield` (핵심 중간값)이 imprecise → `returnExpression` annotation의 expected value 계산 불가 |
| **우회 불가 사유** | 반복문 없이(hoursDelta=0) 실행해도 선형 보간 분모가 2^32×3600으로 커서 작은 값은 0 되고, FP32 스케일 값을 써도 applyInterest 결과를 미리 계산해야 하는 diagnostic 문제 존재 |
| **대조 (updateHourlyBondAmount)** | 같은 문제 — `getUpdatedHourlyYield` 내부에서도 `calcCumulativeYieldFP` 호출하므로 동일한 widening 문제 발생 |

---

## web3bugs_25_H_01

- **Contract**: CompositeMultiOracle
- **Function**: _peek; _get
- **Bug lines (original)**: 116; 126
- **Pattern**: erroneous_accounting
- **Status**: not_detectable (interface-call-return-top)

### Bug Description
`_peek()`/`_get()`에서 `priceOut`을 계산할 때 `10 ** source.decimals` (토큰 decimals)로 나누지만, 올바른 구현은 `10 ** IOracle(source.source).decimals()` (오라클 decimals)로 나눠야 함. 체인된 oracle path에서 가격 스케일이 누적적으로 잘못되어 inflated된 값을 반환.

### 탐지 불가 사유
버그가 있는 계산식:
```solidity
(priceOut, updateTimeOut) = IOracle(source.source).peek(base, quote, 10 ** source.decimals);
priceOut = priceIn * priceOut / (10 ** source.decimals);  // BUG: should be IOracle(source.source).decimals()
```

`IOracle(source.source).peek()`은 **interface 호출**이므로 구현 body가 없어 리턴값이 **⊤ (Top)**:
- `priceOut` = ⊤ (interface call return)
- `priceIn * ⊤ / (10 ** source.decimals)` = **⊤**
- 수정 버전 `priceIn * ⊤ / (10 ** IOracle(...).decimals())` = **⊤** (decimals()도 interface call → ⊤)
- buggy와 correct 모두 ⊤이므로 구분 불가

`peek()`/`get()` 함수에 for loop이 있어 `_peek`/`_get`을 반복 호출하지만, loop은 부차적 문제. Loop 밖의 단일 호출(line 86/106)에서도 interface call로 인해 이미 ⊤.

### 버그 코드
```solidity
function _peek(bytes6 base, bytes6 quote, uint256 priceIn, uint256 updateTimeIn)
    private view returns (uint priceOut, uint updateTimeOut)
{
    Source memory source = sources[base][quote];
    require (source.source != address(0), "Source not found");
    (priceOut, updateTimeOut) = IOracle(source.source).peek(base, quote, 10 ** source.decimals);   // return Top
    priceOut = priceIn * priceOut / (10 ** source.decimals);   // BUG: Top * anything = Top
    updateTimeOut = (updateTimeOut < updateTimeIn) ? updateTimeOut : updateTimeIn;
}
```

---

## web3bugs_34_H_01

- **Contract**: DrawCalculator
- **Function**: _numberOfPrizesForIndex
- **Bug lines (original)**: 422; 423; 424
- **Pattern**: erroneous_accounting
- **Status**: not_detectable (loop-widening)

### Bug Description
`_numberOfPrizesForIndex()`에서 특정 tier의 상금 개수를 계산할 때, while loop으로 모든 lower power를 빼서 올바른 값보다 작은 값을 반환.

**Buggy formula**: `b^d - b^(d-1) - b^(d-2) - ... - b^0` (while loop으로 과도하게 뺌)
**Correct formula**: `b^d - b^(d-1)` (한 번만 뺄셈, loop 불필요)

예시 (b=16, d=3): buggy = 4096 - 256 - 16 - 1 = 3823, correct = 4096 - 256 = 3840

### 탐지 불가 사유
함수 자체는 `internal pure`이고 모든 입력이 parameter에서 오므로 interface-call-return-top 문제 없음. Debugging annotation으로 parameter에 concrete value 부여 가능.

그러나 while loop의 fixpoint iteration + widening으로 인해 over-approximation 발생:
- `numberOfPrizesForIndex -= bitRangeDecimal**(_prizeTierIndex - 1)` 에서 `-=` operator
- 매 iteration마다 다른 exponential 값을 빼므로 fixpoint 미수렴 → widening 적용
- widening은 **sound over-approximation**: 실제값(3823)과 correct value(3840)를 모두 포함하는 범위 생성
- interval domain이면 [0, 4096], flat domain이면 Top → 3840 ∈ 범위 내 → violation 미검출

**핵심**: widening으로 나오는 0은 실제 프로그램 동작이 아닌 over-approximation의 하한. 실제 buggy output은 3823이고 correct output은 3840. 둘 다 widened range 안에 포함되므로 구분 불가.

### 버그 코드
```solidity
function _numberOfPrizesForIndex(uint8 _bitRangeSize, uint256 _prizeTierIndex)
    internal pure returns (uint256)
{
    uint256 bitRangeDecimal = 2**uint256(_bitRangeSize);
    uint256 numberOfPrizesForIndex = bitRangeDecimal**_prizeTierIndex;

    while (_prizeTierIndex > 0) {
        numberOfPrizesForIndex -= bitRangeDecimal**(_prizeTierIndex - 1);  // BUG: 과도한 뺄셈
        _prizeTierIndex--;
    }

    return numberOfPrizesForIndex;
}
```

### Correct code (fix)
```solidity
if (_prizeTierIndex > 0) {
    return (1 << _bitRangeSize * _prizeTierIndex) - (1 << _bitRangeSize * (_prizeTierIndex - 1));
} else {
    return 1;
}
```

---

## web3bugs_52_H_34

- **Contract**: TwapOracle
- **Function**: consult
- **Bug lines (original)**: 129; 152
- **Pattern**: erroneous_accounting
- **Status**: not_detectable (loop-widening)

### Bug Description
`consult()`에서 for loop 내부에서 `sumNative`와 `sumUSD`를 독립적으로 누적하여 최종적으로 `(sumUSD * decimals) / sumNative`로 나누는데, 각 pair의 native amount와 USD price가 올바르게 가중 결합되지 않아 잘못된 consultation 결과를 반환.

### 탐지 불가 사유

**문제 1: Loop body 내부 intent annotation 불가**
- 버그가 line 129 (`sumNative += ...`)와 line 152 (`sumUSD += ...`)에 있으며 둘 다 loop body 내부
- 올바른 수정은 accumulation 방식 자체의 변경 (예: weighted average) → 단일 라인의 값에 대한 intent로 표현 불가
- `result` (line 156)에 intent를 달더라도 `sumUSD`와 `sumNative`가 이미 Top이면 의미 없음

**문제 2: `+=` 에 의한 widening**
- `sumNative += pairData.price1Average.mul(1).decode144()` → `+=` operator → widening 방향은 ∞ → **Top**
- `sumUSD += uint256(price) * (10**10)` → `+=` operator → widening 방향은 ∞ → **Top**
- 결과: `result = (Top * Top) / Top` → **Top**
- buggy와 correct 모두 Top이므로 구분 불가

**참고**: `price`는 `AggregatorV3Interface(...).latestRoundData()` interface 호출이라 Top이지만, 이는 debugging annotation으로 해결 가능한 부차적 문제. 근본 blocker는 loop 내 `+=` widening.

### 버그 코드
```solidity
function consult(address token) public view returns (uint256 result) {
    uint256 pairCount = _pairs.length;
    uint256 sumNative = 0;
    uint256 sumUSD = 0;

    for (uint256 i = 0; i < pairCount; i++) {
        PairData memory pairData = _pairs[i];

        if (token == pairData.token0) {
            sumNative += pairData.price1Average.mul(1).decode144();  // line 129: += widening → Top
            ...
            sumUSD += uint256(price) * (10**10);                     // line 152: += widening → Top
        }
    }
    require(sumNative != 0, "TwapOracle::consult: Sum of native is zero");
    result = ((sumUSD * IERC20Metadata(token).decimals()) / sumNative);  // Top / Top = Top
}
```

---

## web3bugs_52_H_04

- **Contract**: TwapOracle
- **Function**: consult
- **Bug line (original)**: 156
- **Pattern**: erroneous_accounting
- **Status**: not_detectable (loop-widening)

### Bug Description
`consult()`의 최종 계산에서 `IERC20Metadata(token).decimals()` (= 18)를 사용하지만, 올바른 구현은 `10 ** IERC20Metadata(token).decimals()` (= 1e18)를 사용해야 함. scaling factor가 1e18이 아닌 18이 적용되어 결과가 크게 왜곡됨.

### 탐지 불가 사유
`sumNative`와 `sumUSD`가 모두 루프 내 `+=` 누적 → widening → Top. 최종 `result = (sumUSD * decimals) / sumNative` = Top / Top = Top으로, scaling 차이를 감지할 수 없음. web3bugs_52_H_34와 동일한 루프 구조.

### 버그 코드
```solidity
result = ((sumUSD * IERC20Metadata(token).decimals()) / sumNative);
// BUG: decimals() returns 18, should be 10**decimals() = 1e18
// Fix: uint256 scalingFactor = 10 ** IERC20Metadata(token).decimals();
//      result = (sumUSD * scalingFactor) / sumNative;
```

---

## web3bugs_52_H_28

- **Contract**: TwapOracle
- **Function**: consult
- **Bug line (original)**: 156
- **Pattern**: erroneous_accounting
- **Status**: excluded (duplicate_of_52_H_04)

### Notes
web3bugs_52_H_04와 동일한 컨트랙트, 동일한 함수, 동일한 버그 라인(156)을 다른 감사자가 중복 보고한 케이스. 52_H_04에서 분석.

---

## web3bugs_59_H_04

- **Contract**: AuctionBurnReserveSkew
- **Function**: getPegDeltaFrequency
- **Bug line (original)**: 131
- **Pattern**: erroneous_accounting
- **Status**: not_detectable (loop-widening)

### Bug Description
`getPegDeltaFrequency()`에서 `count < auctionAverageLookback`일 때 분모를 `auctionAverageLookback` 대신 `count`로 나눠야 함. 현재 구현은 실제 관측 수보다 큰 분모를 사용하여 과소평가된 값을 반환.

### 탐지 불가 사유
`total`이 루프 내에서 `total = total + pegObservations[index]`로 `+=` 누적 → widening → Top. 최종 `total * 10000 / auctionAverageLookback`든 `total * 10000 / count`든 결과가 Top → 구분 불가.

### 버그 코드
```solidity
function getPegDeltaFrequency() public view returns (uint256) {
    uint256 initialIndex = 0;
    if (count > auctionAverageLookback) {
        initialIndex = count - auctionAverageLookback;
    }
    uint256 total = 0;
    for (uint256 i = initialIndex; i < count; ++i) {
        index = _getIndexOfObservation(i);
        total = total + pegObservations[index];  // += widening → Top
    }
    return total * 10000 / auctionAverageLookback;  // BUG: should be / count when count < auctionAverageLookback
}
```

---

## web3bugs_70_H_03

- **Contract**: LiquidityBasedTWAP
- **Function**: _calculateUSDVPrice (동일 구조: _calculateVaderPrice)
- **Bug lines (original)**: 399; 403
- **Pattern**: erroneous_accounting
- **Status**: not_detectable (loop-widening)

### Bug Description
`_calculateUSDVPrice()`에서 pair가 2개 이상일 때 USDV 가격을 잘못 계산. "비율들의 가중평균"이 아니라 "가중평균들의 비율"을 계산함.

**수학적 문제**: `E[X/Y] ≠ E[X]/E[Y]`
- **Correct**: `Σ(weight_i/totalWeight × foreignPrice_i / nativePrice_i)` — 각 pair별 USD 가격을 먼저 구한 후 가중평균
- **Buggy**: `Σ(weight_i/totalWeight × foreignPrice_i) / Σ(weight_i/totalWeight × nativePrice_i)` — foreign price 평균과 native price 평균을 각각 구한 후 나누기

Pair가 1개면 두 식은 동일하지만, 2개 이상이면 결과가 달라짐. `_calculateVaderPrice()`도 동일한 구조적 문제 보유.

### 탐지 불가 사유

**문제 1: `+=` 에 의한 widening**
- `totalUSD += (foreignPrice * liquidityWeights[i]) / totalUSDVLiquidityWeight` → `+=` → widening → **Top**
- `totalUSDV += (nativeAvgPrice * liquidityWeights[i]) / totalUSDVLiquidityWeight` → `+=` → widening → **Top**
- 결과: `(Top * 1 ether) / Top` → **Top**
- buggy와 correct 모두 Top이므로 구분 불가

**문제 2: Loop body 내 intent annotation 불가**
- 버그가 accumulation 방식 자체의 문제 (비율의 평균 vs 평균의 비율)
- 수정하려면 loop body 구조 자체를 변경해야 함 → 단일 라인의 값에 대한 intent로 표현 불가

**참고**: `getChainlinkPrice()` → `oracle.latestRoundData()` interface 호출로 `foreignPrice`도 Top이지만, debugging annotation으로 해결 가능한 부차적 문제. 근본 blocker는 loop 내 `+=` widening.

### 버그 코드
```solidity
function _calculateUSDVPrice(
    uint256[] memory liquidityWeights,
    uint256 totalUSDVLiquidityWeight
) internal view returns (uint256) {
    uint256 totalUSD;
    uint256 totalUSDV;
    uint256 totalPairs = usdvPairs.length;

    for (uint256 i; i < totalPairs; ++i) {
        ...
        uint256 foreignPrice = getChainlinkPrice(address(foreignAsset));

        totalUSD +=                                          // line 399: += widening → Top
            (foreignPrice * liquidityWeights[i]) /
            totalUSDVLiquidityWeight;

        totalUSDV +=                                         // line 403: += widening → Top
            (pairData.nativeTokenPriceAverage
                .mul(pairData.foreignUnit)
                .decode144() * liquidityWeights[i]) /
            totalUSDVLiquidityWeight;
    }

    return (totalUSD * 1 ether) / totalUSDV;                 // Top / Top = Top
}
```

---

## web3bugs_70_H_04

- **Contract**: LiquidityBasedTWAP
- **Function**: syncVaderPrice
- **Bug lines (original)**: 131; 140; 144; 147
- **Pattern**: erroneous_accounting
- **Status**: not_detectable (loop-widening)

### Bug Description
`syncVaderPrice()`의 for loop에서 `timeElapsed < pairData.updatePeriod`인 pair를 `continue`로 건너뛰는데, 이때 해당 pair의 기여분이 완전히 누락됨.

**구체적 문제**:
1. `pastLiquidityWeights[i]`가 0으로 남음 (line 140 미실행) → `_calculateVaderPrice` 분자에서 누락
2. `_totalLiquidityWeight`에 해당 pair 미포함 (line 144 미실행)
3. `pastTotalLiquidityWeight`는 이전 저장된 **전체** 합 (line 124) → 분모는 모든 pair 포함
4. Line 147에서 불완전한 `_totalLiquidityWeight`를 state에 저장 → 다음 호출의 `pastTotalLiquidityWeight`도 오염

**결과**: 분자는 일부 pair만, 분모는 전체 pair → 가격 과소평가.

**올바른 수정**: `continue` 전에 `pastLiquidityWeights[i] = pairData.pastLiquidityEvaluation`과 `_totalLiquidityWeight += pairData.pastLiquidityEvaluation` 추가.

### 탐지 불가 사유

**문제 1: `+=` widening**
- `_totalLiquidityWeight += currentLiquidityEvaluation` → loop 내 `+=` → widening → **Top**
- 결과적으로 `totalLiquidityWeight` state 변수도 Top

**문제 2: Interface calls**
- `_updateVaderPrice` 내부에서 `pair.token0()`, `pair.getReserves()`, `UniswapV2OracleLibrary.currentCumulativePrices()` 등 interface 호출 → Top

**문제 3: Control flow 버그**
- `continue`로 인한 선택적 누락은 값(value) annotation으로 표현하기 어려움
- "skipped pair도 weight에 포함되어야 한다"는 제어 흐름 속성이지 값 속성이 아님

### 버그 코드
```solidity
function syncVaderPrice() public override returns (...) {
    uint256 _totalLiquidityWeight;
    ...
    pastTotalLiquidityWeight = totalLiquidityWeight[uint256(Paths.VADER)];  // 전체 합

    for (uint256 i; i < totalPairs; ++i) {
        ...
        if (timeElapsed < pairData.updatePeriod) continue;  // line 131: skip → 아래 전부 미실행

        pastLiquidityWeights[i] = pastLiquidityEvaluation;   // line 140: skip시 0으로 남음
        ...
        _totalLiquidityWeight += currentLiquidityEvaluation; // line 144: skip시 미포함
    }

    totalLiquidityWeight[uint256(Paths.VADER)] = _totalLiquidityWeight;  // line 147: 불완전한 합 저장
}
```

---

## web3bugs_70_H_05

- **Contract**: LiquidityBasedTWAP
- **Function**: _calculateUSDVPrice
- **Bug line (original)**: 412
- **Pattern**: erroneous_accounting
- **Status**: not_detectable (loop-widening)

### Bug Description
`_calculateUSDVPrice()`에서 Chainlink의 `foreignPrice`가 8 decimals (1e8 = $1)로 반환되는데, 프로토콜은 18 decimals (1e18 = $1)을 기대함. `foreignPrice`를 스케일링 없이 그대로 `totalUSD`에 누적하여, 최종 결과가 1e18이어야 할 것이 1e8로 반환됨.

### 탐지 불가 사유
`totalUSD`와 `totalUSDV` 모두 루프 내 `+=` 누적 → widening → Top. 최종 `(totalUSD * 1 ether) / totalUSDV` = Top / Top = Top. 스케일링 오류(1e8 vs 1e18)를 감지할 수 없음. web3bugs_70_H_03, web3bugs_70_H_04와 동일한 TWAP oracle 루프 구조.

### 버그 코드
```solidity
// foreignPrice = getChainlinkPrice(address(foreignAsset));  // 1e8 (8 decimals)
totalUSD += (foreignPrice * liquidityWeights[i]) / totalUSDVLiquidityWeight;  // += widening → Top
totalUSDV += ...;  // += widening → Top

return (totalUSD * 1 ether) / totalUSDV;  // Top / Top = Top
// BUG: foreignPrice is 1e8 scale, should be scaled to 1e18
```

---

## web3bugs_71_H_11

- **Contract**: PoolTemplate
- **Function**: resume
- **Bug lines (original)**: 709; 710; 711
- **Pattern**: erroneous_accounting
- **Status**: not_detectable (interface-call-return-top)

### Bug Description
`resume()`에서 각 index pool의 상환액(`_redeemAmount`)을 계산할 때 나눗셈(`_divCeil`)을 사용하지만, 올바른 계산은 곱셈이어야 함.

**수학적 문제**:
- `_deductionFromIndex` = 전체 index에서 차감할 총액 (× 1e6 scaled)
- `_shareOfIndex` = 해당 index의 비율 (× 1e6, 예: 30% → 300000)
- **Buggy**: `_divCeil(총액, 비율)` = 총액 ÷ 0.3 → 총액의 3.3배 (과다 상환)
- **Correct**: `총액 × 비율 / 1e6` → 총액의 30% (정상 비례 배분)

Index가 1개면 shareOfIndex = 1e6이라 나눠도 동일. 2개 이상이면 각 index가 과다 상환.

### 탐지 불가 사유

**본질: interface-call-return-top**

```solidity
uint256 _debt = vault.debts(address(this));  // vault = IVault → interface call → Top
...
uint256 _deductionFromIndex = (_debt * _totalCredit * MAGIC_SCALE_1E6) /
    totalLiquidity();                         // totalLiquidity() → vault.underlyingValue() → Top
```

- `_debt` = Top (interface call) → `_deductionFromIndex` = Top
- `_redeemAmount = _divCeil(Top, _shareOfIndex)` = **Top**
- buggy(나눗셈)든 correct(곱셈)든 Top → 구분 불가

**Loop body 변수의 수렴 여부**:
- `_index`, `_credit`, `_shareOfIndex`, `_redeemAmount` — 매 iteration 새로 선언 (declaration, not accumulation)
- Fixpoint iteration에서 join으로 수렴 가능 → loop-widening은 이들에 적용 안됨
- 유일한 accumulator `_actualDeduction += ...`만 widening 대상

**그러나 loop-widening은 부차적 문제**:
- `IIndexTemplate(_index).compensate(_redeemAmount)` → loop 내 interface call → 리턴값 Top
- `_actualDeduction += Top` → widening 없어도 이미 Top
- 근본 blocker는 interface call이지 loop widening이 아님

**Debugging annotation으로 해결 가능한가?**:
- `vault.debts()`, `totalLiquidity()` (loop 전 호출) → debugging annotation으로 concrete 가능
- 하지만 loop 내 `IIndexTemplate(_index).compensate()` → 매 iteration 다른 `_index`로 호출 → per-iteration 리턴값 지정 어려움
- 또한 bug line (709-711)이 loop body 내부 → intent annotation 배치 불가 (loop-body-granularity)

### 버그 코드
```solidity
function resume() external {
    ...
    uint256 _debt = vault.debts(address(this));           // interface call → Top
    uint256 _totalCredit = totalCredit;
    uint256 _deductionFromIndex = (_debt * _totalCredit * MAGIC_SCALE_1E6) /
        totalLiquidity();                                  // Top
    uint256 _actualDeduction;
    for (uint256 i = 0; i < indexList.length; i++) {
        address _index = indexList[i];
        uint256 _credit = indicies[_index].credit;
        if (_credit > 0) {
            uint256 _shareOfIndex = (_credit * MAGIC_SCALE_1E6) /
                _totalCredit;
            uint256 _redeemAmount = _divCeil(              // line 709: BUG — 나눗셈이 아니라 곱셈이어야 함
                _deductionFromIndex,                       // line 710: Top (from interface)
                _shareOfIndex                              // line 711
            );
            _actualDeduction += IIndexTemplate(_index).compensate(  // interface call → Top
                _redeemAmount
            );
        }
    }
    ...
}
```

---

## web3bugs_3_H_05

- **Contract**: CrossMarginAccounts
- **Function**: belowMaintenanceThreshold
- **Bug line (original)**: 203
- **Pattern**: erroneous_accounting
- **Status**: not_detectable (external-call-state-unknown)

### Bug Description
`belowMaintenanceThreshold()`에서 비교 방향이 반대. 함수 이름은 "maintenance threshold 이하인지"를 반환해야 하지만, 실제 구현은 건강한(healthy) 상태일 때 `true`를 반환:

```solidity
return 100 * holdings >= liquidationThresholdPercent * loan;  // BUG: >= should be < or <=
```

- `holdings >= loan * 1.1` → account가 건강 → `true` 반환
- 이름(`belowMaintenanceThreshold`)과 실제 반환값의 의미가 반대

### 탐지 불가 사유

**본질: external-call-state-unknown (L5b)**

`belowMaintenanceThreshold` → `loanInPeg` / `holdingsInPeg` → `sumTokensInPegWithYield` (loop) → `yieldTokenInPeg` → 외부 컨트랙트 호출:

```solidity
// yieldTokenInPeg (line 280):
uint256 yieldFP = Lending(lending()).viewBorrowingYieldFP(token);  // 외부 컨트랙트 호출 → Top

// yieldTokenInPeg (line 287):
return PriceAware.getCurrentPriceInPeg(...);                       // 외부 컨트랙트 호출 → Top
```

- `Lending`은 `import "./Lending.sol"`로 concrete type이 존재하나, 별도 deployment된 외부 컨트랙트
- `lending()`은 `RoleAware.mainCharacterCache[LENDING]`에서 address 반환 (type casting, not constructor)
- `Lending` 컨트랙트의 state variable에 debugging annotation 불가 → 내부 연산이 Top으로 흘러감
- `PriceAware.getCurrentPriceInPeg()`도 동일한 문제

**Call chain**:
```
belowMaintenanceThreshold
  → loanInPeg(account, true)
    → sumTokensInPegWithYield(account.borrowAmounts, account.borrowTokens, true)
      → for loop (index-bound)
        → yieldTokenInPeg(token, amount, true)
          → Lending(lending()).viewBorrowingYieldFP(token)  // Top
          → PriceAware.getCurrentPriceInPeg(...)            // Top
  → holdingsInPeg(account, true)
    → (동일 구조, 외부 호출로 Top)
```

**결과**:
- `loan` = Top (외부 호출 결과 누적)
- `holdings` = Top (동일)
- `100 * Top >= liquidationThresholdPercent * Top` → Top >= Top → **Top**
- buggy(`>=`)든 correct(`<`)든 결과가 모두 Top → 구분 불가

### 버그 코드
```solidity
function belowMaintenanceThreshold(CrossMarginAccount storage account)
    internal returns (bool)
{
    uint256 loan = loanInPeg(account, true);
    uint256 holdings = holdingsInPeg(account, true);
    // The following should hold:
    // holdings / loan >= 1.1
    // => holdings >= loan * 1.1
    return 100 * holdings >= liquidationThresholdPercent * loan;  // BUG: >= should be < or <=
}
```

---

## web3bugs_51_H_04

- **Contract**: SwapUtils (library)
- **Function**: getYC
- **Bug lines (original)**: 765; 767; 768
- **Pattern**: erroneous_accounting
- **Status**: not_detectable (inexpressible-expected-value)

### Bug Description
StableSwap AMM에서 amplifier를 2개(A1, A2) 사용하며, pool balance 비율(`xp[0]` vs `xp[1]`)에 따라 어떤 A를 쓸지 `determineA()`가 결정한다. Swap이 target price를 넘어 A가 전환될 때, 올바른 구현은 swap을 target price 기준으로 **2단계로 분할**하여 각각 A1, A2를 적용해야 한다.

그러나 `getYC()`는 A가 바뀌면 **새 A로 전체 swap을 재계산**한다:

```solidity
// 5. Check if we switched A's during the swap
if (aNew == a){     // We have used the correct A
    return y;
} else {    // We have switched A's, do it again with the new A
    return getY(self, tokenIndexFrom, tokenIndexTo, x, xp, aNew, d);  // BUG
}
```

`d`는 old `a`로 계산된 invariant인데, `aNew`와 함께 사용됨. 결과적으로 A2 커브를 전체 거래에 적용하여 실행 가격이 왜곡된다.

### 탐지 불가 사유

**본질: inexpressible-expected-value (L6)**

**1. 질적 차이 없음**

`getYC`의 반환값은 `_calculateSwap` → `swap`을 거쳐 `self.balances[tokenIndexTo]`를 갱신한다:
- buggy: `balances[tokenIndexTo]` 감소 (잘못된 dy만큼)
- correct: `balances[tokenIndexTo]` 감소 (올바른 dy만큼)

둘 다 **같은 방향으로 변화**하므로 `Changed`, `Before > After` 등 질적 annotation으로 구분 불가.

**2. 올바른 값을 산술식으로 표현 불가**

올바른 결과를 구하려면:
1. **split point `dx₁`** 계산 — `xp[0] + dx₁ == xp[1] - getY(dx₁)`를 만족하는 dx₁ (방정식의 해, 단순 산술식 아님)
2. `getY(..., a, d)`로 부분 swap 1 수행
3. 중간 상태로 새 `d₂ = getD(중간상태, aNew)` 계산
4. `getY(..., aNew, d₂)`로 부분 swap 2 수행

이 중 `dx₁` (split point)가 코드에 존재하지 않는 값이며, 기존 변수의 `+`, `-`, `*`, `/` 조합으로 표현 불가 (자체가 비선형 방정식의 해). 따라서 `@Post return == expr` 형태의 annotation을 구성할 수 없다.

**3. 시도한 annotation 접근과 실패 사유**

| 접근 | 실패 사유 |
|------|----------|
| `return == concrete_value` | 올바른 값을 미리 계산해야 함 → 탐지가 아닌 답 제공 |
| `return == y` (old A로 계산한 값) | correct code도 `y`를 리턴하지 않음 (split 결과 ≠ y) → 양쪽 모두 violation |
| `getY.arg == a` (파라미터 제약) | "old A 유지"는 올바른 수정이 아님 (split이 정답) |
| `Changed`/`Before > After` on balances | buggy/correct 모두 동일하게 만족 |
| `getD([x, return], aNew) == getD(xp, aNew)` | annotation 내 함수 호출 불가 |

### Loop 수렴 여부 (참고)

`getY` 내부에 Newton's method loop (MAX_LOOP_LIMIT=256)이 있으나, debugging annotation으로 concrete value를 제공하면 ~4회 이내 수렴. **loop-widening은 blocker가 아님**. 핵심 blocker는 올바른 값의 표현 불가능성.

`getD` 내부의 Newton's method loop도 마찬가지로 concrete input에서 수렴.

첫 번째 loop (`for i < numTokens`)은 2-3회만 반복하는 index-bound loop으로 사실상 unroll.

---

## web3bugs_51_H_06

- **Contract**: SwapUtils (library)
- **Function**: addLiquidity
- **Bug line (original)**: 1231
- **Pattern**: erroneous_accounting
- **Status**: not_detectable (inexpressible-expected-value)

### Bug Description

StableSwap의 `addLiquidity`에서 imbalanced liquidity 추가 시 fee를 계산하기 위해 "ideal balance"를 구한다. 이 값은 `d1/d0 * old_balance`로 계산되며, d0과 d1이 같은 커브(같은 A 값) 위에 있어야 비율이 의미를 가진다.

그러나 이 컨트랙트는 dual-A 시스템(A1, A2)을 사용하며, `determineA()`가 토큰 비율(`xp[0]` vs `xp[1]`)에 따라 A를 선택한다:

```solidity
v.d0 = getD(self);
// → 내부: determineA(self, _xp(self)) → old balances 기준 A (예: A1)

v.preciseA = determineA(self, _xp(self, newBalances));
// → new balances 기준 A (예: A2, A가 전환될 수 있음)

v.d1 = getD(_xp(self, newBalances), v.preciseA);
// → A2로 계산된 D

idealBalance = v.d1.mul(self.balances[i]).div(v.d0);  // BUG (line 1231)
// d0은 A1 커브, d1은 A2 커브 → 서로 다른 커브의 D 비율은 무의미
```

imbalanced liquidity 추가로 토큰 비율이 역전되면 (`xp[0] < xp[1]` → `xp[0] > xp[1]`), d0과 d1이 서로 다른 A 값으로 계산되어 idealBalance가 틀림 → fee 계산 오류 → 최종 `self.balances[i]`와 `toMint` 모두 부정확.

### 탐지 불가 사유

**본질: inexpressible-expected-value (L6)**

**1. 질적 차이 없음**

`addLiquidity` 후 `self.balances[i]`는 buggy/correct 모두 증가한다 (liquidity 추가 후 fee 차감). `Changed`, `Before < After` 등 질적 annotation으로 구분 불가.

**2. 올바른 값을 산술식으로 표현 불가**

올바른 `idealBalance`를 구하려면 d0과 d1을 **같은 A**로 계산한 `getD()` 결과가 필요:
- correct_d0 = getD(oldBalances, A_consistent)
- correct_d1 = getD(newBalances, A_consistent)
- correct_idealBalance = correct_d1 * old_balance / correct_d0

`getD()`는 Newton's method 반복(iterative) 함수이므로, annotation expression (`+`, `-`, `*`, `/` 조합)으로 표현 불가. annotation 내 함수 호출도 불가.

**3. 시도한 annotation 접근과 실패 사유**

| 접근 | 실패 사유 |
|------|----------|
| `Changed` / `Before < After` on self.balances | buggy/correct 모두 동일하게 만족 (둘 다 증가) |
| `self.balances[i] == expr` | 올바른 값이 getD() 호출 결과에 의존 → 산술식 표현 불가 |
| `getD(newBal, A_old) * bal / getD(oldBal, A_old)` | annotation 내 함수 호출 불가 |
| concrete value annotation | 올바른 값 자체를 수동 계산해야 함 → 탐지가 아닌 답 제공 |

### 참고: Newton loop 수렴 여부

51_H_04와 동일하게, `getD` 내부의 Newton's method loop는 concrete debugging annotation 하에서 ~4회 이내 수렴 가능. 따라서 loop-widening(L1)은 blocker가 아님. 핵심 blocker는 올바른 값의 표현 불가능성.

---

## web3bugs_70_H_10

- **Contract**: LiquidityBasedTWAP
- **Function**: syncVaderPrice
- **Bug line (original)**: 187
- **Pattern**: inconsistent_state_updates
- **Status**: detectable

### Bug Description

`syncVaderPrice()` → `_updateVaderPrice()` 호출 시 `previousPrices[uint256(Paths.VADER)]`가 갱신되지 않음. `setupVader()`에서 초기값 설정 후 한 번도 업데이트 안 됨. 시간이 지나면서 실제 VADER 가격과 괴리 → `currentLiquidityEvaluation` 왜곡 → TWAP 가격 부정확.

### 외부 타입 의존성

`ExchangePair` struct와 `Paths` enum은 `ILiquidityBasedTWAP` 인터페이스에 정의됨. `LiquidityBasedTWAP is ILiquidityBasedTWAP`로 상속.

- 이것은 L5(cross-deployment-call-top)와 **다름** — 외부 함수 호출이 아니라 **타입 상속**
- `twapData`는 target contract 자체의 storage → annotation scope 안
- 사전분석(dependency pre-analysis)에서 인터페이스의 struct/enum 정의를 resolve하면 됨

```
ILiquidityBasedTWAP (interface)
├── struct ExchangePair { lastMeasurement, updatePeriod, pastLiquidityEvaluation, ... }
├── enum Paths { VADER, USDV }
└── LiquidityBasedTWAP가 상속 → struct/enum 타입 사용 가능
```

### 루프 분석

`syncVaderPrice`의 루프 (line 90-111)에 `_totalLiquidityWeight += currentLiquidityEvaluation` (accumulation) 있음. 이건 70_H_03/04/05에서 loop-widening의 원인이었던 동일 루프.

그러나 이 버그의 annotation target은 `previousPrices[0]`이며, 루프 내에서 `previousPrices`에 대한 write는 (buggy code에서) **전혀 없음**. 따라서 `_totalLiquidityWeight`의 widening은 `previousPrices`의 Changed/Unchanged 판정에 영향 없음.

### Annotation 삽입 순서 및 라인 배치

**Step 1: Intent annotation 삽입** — contraction line 114 (`}` 직전)

```
113: totalLiquidityWeight[uint256(Paths.VADER)] = _totalLiquidityWeight;
114: // @Post Changed(previousPrices[0])      ← 삽입
115: }                                         ← 원래 114
```

**Step 2: Debug annotations 삽입** — line 85부터 (함수 body 시작 전, 8줄)

```
85: // @GlobalVar block.timestamp = [10000, 10000]
86: // @StateVar previousPrices[0] = [1000000000000000, 1000000000000000]
87: // @StateVar vaderPairs.length = [1, 1]
88: // @StateVar totalLiquidityWeight[0] = [1, 1]
89: // @StateVar twapData[1].lastMeasurement = [1000, 1000]
90: // @StateVar twapData[1].updatePeriod = [60, 60]
91: // @StateVar twapData[1].pastLiquidityEvaluation = [1, 1]
92: // @StateVar twapData[1].nativeTokenPriceCumulative = [0, 0]
93: uint256 _totalLiquidityWeight;            ← 원래 85
```

값은 Z3 constraint solving으로 결정 (`z3_solvers/web3bugs_70_H_10_solver.py`).
- `timeElapsed = 10000 - 1000 = 9000 >= updatePeriod(60)` → loop body 진입 보장
- `previousPrices[0] = 1e15` → 1e18 스케일 기준 0.001 VADER 가격

interpret 시 debug annotation으로 concrete 값 주입 → 분석 실행 → intent annotation 결과 출력.

### Z3 Constraints

debug annotation 값 결정 시 다음 제약 조건을 Z3로 풀어야 함:

1. **underflow 방지** (Solidity 0.8.9 checked arithmetic → revert 방지)
   - `block.timestamp >= twapData[1].lastMeasurement` (line 93: `block.timestamp - pairData.lastMeasurement`)
2. **loop body 진입 보장**
   - `block.timestamp - twapData[1].lastMeasurement >= twapData[1].updatePeriod` (line 95: `timeElapsed < updatePeriod`이면 continue)
3. **_updateVaderPrice 내부 overflow 방지**
   - `reserveNative * previousPrices[0]` overflow 없도록 (line 72-73)
   - `reserveForeign * chainlinkPrice` overflow 없도록 (line 74)
   - 단, `reserveNative`, `reserveForeign`은 외부 interface call → Top. constraint는 annotation 가능한 변수 범위 내에서 설정
4. **unchecked 블록 내 의미 있는 값**
   - `nativeTokenPriceCumulative(현재) >= twapData[1].nativeTokenPriceCumulative` (line 62-63, unchecked이라 revert는 안 하지만 의미 있는 분석을 위해)

### Debug Annotation 참고

- `block.timestamp` → GlobalVar로 설정 필요 (누락 시 분석 불가)
- `vaderPairs.length = [1, 1]` → 동적 배열 크기 설정 (DebugInitializer에서 `.length` 특별 처리 지원)
- `twapData[1]` → mapping의 리터럴 키 (address-keyed mapping에서 자동 AddressSet 변환)
- `twapData[1].lastMeasurement` 등 → mapping value의 struct 멤버 접근 (사전분석으로 ExchangePair struct 정의 필요)

### Intent Annotation 결과 예측

```
// @Post Changed(previousPrices[0])
```

- **Buggy**: `previousPrices[0]`에 write 없음 → Unchanged → `Changed` 위반 → **alarm**
- **Correct**: `previousPrices[0]`에 새 가격 기록 → Changed → **pass**

※ `Changed` 키워드는 Issue 2 (code_modification_issues.md) 구현 후 사용 가능. 현재 문법으로는 `previousPrices[0](Entry != Exit)`로 대체 가능 (buggy code에서 write 자체가 없으므로 Entry == Exit → 동일 효과).

---

## web3bugs_58_H_02

- **Contract**: LpIssuer
- **Function**: _chargeFees
- **Bug line (original)**: 270
- **Pattern**: erroneous_accounting
- **Status**: not_detectable (interface-call-return-top)

### Bug Description

Performance fee 계산 공식이 잘못됨. `toMint = (baseSupply * minLpPriceFactor) / DENOMINATOR`에서:
1. `minLpPriceFactor = lpPrice * DENOMINATOR / hwm` → lpPrice > hwm이면 항상 > DENOMINATOR
2. 따라서 `toMint > baseSupply` — 매번 전체 supply보다 많은 LP를 mint
3. `performanceFee` 비율이 계산에 아예 사용되지 않음 (> 0 체크만 하고 끝)

올바른 공식: `toMint = baseSupply * (minLpPriceFactor - DENOMINATOR) * performanceFee / (DENOMINATOR²)`

### 루프 분석 (lines 253-265)

```solidity
uint256 minLpPriceFactor = type(uint256).max;
for (uint256 i = 0; i < baseTvls.length; i++) {
    // ...
    if (delta < minLpPriceFactor) {
        minLpPriceFactor = delta;  // 항상 감소 방향 → 수렴
    }
}
```

min-finding 패턴으로 accumulation(`+=`)이 아님. monotonically non-increasing → widening 대상 아님. **루프는 blocker가 아님.**

### Not Detectable 사유: interface-call-return-top (L5a)

`_chargeFees`에 전달되는 핵심 데이터가 모두 interface call에서 유래:

| 데이터 | 출처 | 결과 |
|--------|------|------|
| `tvls` (→ baseTvls) | `subvault.tvl()` — IVault interface | Top |
| `strategyParams.performanceFee` | `ILpIssuerGovernance.delayedStrategyParams()` | Top |
| `strategyParams.strategyPerformanceTreasury` | 동일 | Top |
| `managementFee`, `protocolFee` | `ILpIssuerGovernance.*()` | Top |
| `managementFeeChargeDelay` | `ILpIssuerGovernance.delayedProtocolParams()` | Top |

Top 전파 경로:
- `baseTvls[i]` = Top → `lpPrice` = Top → `minLpPriceFactor` = Top → `toMint` = Top
- `_totalSupply` after mint = concrete + Top = Top

`baseSupply`는 LpIssuer 자체의 `_totalSupply`에서 유래하므로 concrete이지만, tvl과 fee 파라미터가 전부 interface call에서 오기 때문에 연산 결과가 Top.

### Annotation 실패 분석

| 접근 | 실패 사유 |
|------|----------|
| `_totalSupply: Changed` | buggy/correct 모두 Changed (둘 다 mint 발생) |
| `Before(_totalSupply) < After(_totalSupply)` | buggy/correct 모두 true (둘 다 증가) |
| `After(_totalSupply) == Before + expr` | `minLpPriceFactor`, `performanceFee` 등이 Top → 올바른 값 계산 불가 |
| early return 조건으로 구분 | `managementFeeChargeDelay`도 Top → 조건 자체가 Top → 양 분기 모두 가능 |

---

## web3bugs_29_H_14

- **Contract**: IndexPool
- **Function**: _computeSingleOutGivenPoolIn
- **Bug line (original)**: 279
- **Pattern**: erroneous_accounting
- **Status**: excluded (overflow-revert)

### Bug Description
`_computeSingleOutGivenPoolIn`이 `_pow(poolRatio, _div(BASE, normalizedWeight))`를 호출하는데, `_div(BASE, normalizedWeight)`는 WAD 단위(18 decimals) 값을 반환함. 그러나 `_pow(a, n)`은 `n`을 plain integer로 취급하므로, 예를 들어 weight가 25%면 exponent가 `4 * 10^18`이 되어 `a^(4*10^18)`을 계산 시도 → integer overflow → revert.

올바른 호출은 `_compute(poolRatio, _div(BASE, normalizedWeight))`이며, `_compute`는 WAD 단위 exponent를 whole/fractional로 분리하여 처리함.

### Excluded 사유
- Solidity >=0.8.0에서 overflow는 자동 revert됨 (checked arithmetic)
- 조용히 잘못된 값을 반환하는 것이 아니라 실행 자체가 중단됨
- **Numeric logical error 정의에 해당하지 않음**: compile 단계 통과 후 실행 시 잘못된 값을 "반환"하는 것이 아니라, overflow로 인해 revert되는 문제

---

## web3bugs_112_H_01

- **Contract**: StakerVault
- **Function**: transfer
- **Bug lines (original)**: 112; 113; 117; 118
- **Bug lines (contraction)**: 31; 32; 36; 37 (annotation 삽입 후: 31; 32; 37; 39)
- **Pattern**: erroneous_accounting
- **Status**: contraction 완료

### Bug Description
`transfer()`에서 `balances` 업데이트(contraction line 31-32)가 `userCheckpoint()` 호출(contraction line 37, 39) **전에** 실행됨. `userCheckpoint()`는 내부적으로 `stakedAndActionLockedBalanceOf(user)` → `balances[user]`를 읽어 보상을 계산하므로, 이미 변경된 balance로 보상이 계산됨. 수신자가 반복적으로 자기 계정 간 transfer하면서 보상을 과다 청구 가능.

대조: 같은 컨트랙트의 `transferFrom()`(original line 155-158)은 올바르게 **checkpoint → balance 변경** 순서.

### Dependencies
**Interfaces** (6):
- IStakerVault, IController, IAddressProvider, IERC20, ILiquidityPool, ILpGauge

**Libraries** (3):
- AddressProviderHelpers, SafeERC20, ScaledMath

**Contracts** (4):
- Authorization, Pausable, Initializable, Preparable

**기타**:
- Error (require 메시지용 라이브러리/contract)
- Transfer event (IStakerVault에 정의 추정)

### Intent Annotations (standalone)
| Type | Line (contraction, annotation 삽입 후) | Expression | Expected | Comment |
|------|---------------------------------------|------------|----------|---------|
| During | 36 (standalone, 대상: line 37) | Unchanged(balances[msg.sender]) | violated | checkpoint 시점에 balances[msg.sender]가 이미 변경됨 (line 31) → Entry ≠ Current → violated |
| During | 38 (standalone, 대상: line 39) | Unchanged(balances[account]) | violated | checkpoint 시점에 balances[account]가 이미 변경됨 (line 32) → Entry ≠ Current → violated |

### Debug Annotations
**LocalVar:**
| # | Variable | Value (interval) | Comment |
|---|----------|-------------------|---------|
| 1 | account | symbolicAddress 1 | 수신자 |
| 2 | amount | [100, 100] | 전송량 |

**StateVar:**
| # | Variable | Value (interval) | Comment |
|---|----------|-------------------|---------|
| 1 | balances[101] | [200, 200] | balances[msg.sender], require 통과용 |
| 2 | balances[1] | [0, 0] | balances[account] |
| 3 | currentAddresses[_LP_GAUGE] | symbolicAddress 2 | if 분기 진입용 (≠ address(0)), 피상속 상태변수 (Preparable) |

**입력 조건:**
- balances[101] >= amount (require 통과)
- currentAddresses[_LP_GAUGE] != address(0) (if 분기 진입)

**실행 후 검증:**
- balances[101] = 200 - 100 = 100 ≠ Entry(200) → Unchanged **violated** ✓
- balances[1] = 0 + 100 = 100 ≠ Entry(0) → Unchanged **violated** ✓

### Notes
- `@During Unchanged(var)` = "이 program point에서 var의 Current 값이 Entry 값과 같아야 한다"
- 버기 코드: balance 변경 → checkpoint → Unchanged violated → 탐지
- 정상 코드: checkpoint → balance 변경 → checkpoint 시점에 Unchanged satisfied
- `@During Unchanged` 구현 필요 (code_modification_issues.md Issue 2)
- standalone annotation 지원 필요 (code_modification_issues.md Issue 1)
- `userCheckpoint()`는 ILpGauge interface 호출 → 외부 컨트랙트 효과이나, annotation 대상은 StakerVault 내부의 `balances` 상태변수
- `currentAddresses`는 Preparable에서 상속된 상태변수 → 피상속 상태변수에 대한 debug annotation 가능 여부 확인 필요

### 버그 코드 (contraction, annotation 삽입 후)
```solidity
function transfer(address account, uint256 amount) external override notPaused returns (bool) {
    require(msg.sender != account, Error.SELF_TRANSFER_NOT_ALLOWED);
    require(balances[msg.sender] >= amount, Error.INSUFFICIENT_BALANCE);

    ILiquidityPool pool = controller.addressProvider().getPoolForToken(token);
    pool.handleLpTokenTransfer(msg.sender, account, amount);

    balances[msg.sender] -= amount;       // line 31: balance 먼저 변경
    balances[account] += amount;           // line 32: balance 먼저 변경

    address lpGauge = currentAddresses[_LP_GAUGE];
    if (lpGauge != address(0)) {
        // @During Unchanged(balances[msg.sender])          // line 36: standalone annotation
        ILpGauge(lpGauge).userCheckpoint(msg.sender);       // line 37: checkpoint 나중 → BUG
        // @During Unchanged(balances[account])              // line 38: standalone annotation
        ILpGauge(lpGauge).userCheckpoint(account);          // line 39: checkpoint 나중 → BUG
    }

    emit Transfer(msg.sender, account, amount);
    return true;
}
```
