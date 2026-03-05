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

## web3bugs_83_H_02

- **Contract**: MasterChef
- **Function**: deposit
- **Bug lines (original)**: 170; 171; 172
- **Pattern**: erroneous_accounting
- **Status**: not_detectable (no-target-storage)

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
