# RQ2 Limitation Types

IntentChecker로 탐지 불가능한 케이스들의 한계 유형을 정의하고 분류한 문서.

---

## 분류 체계

### Not Detectable (not_detectable)

분석 대상이지만 IntentChecker의 구조적 한계로 탐지 불가능한 케이스. 크게 두 범주로 나뉜다:

- **분석 추상화 (Analysis Abstraction)**: 분석 엔진이 값을 TOP으로 추상화하여 buggy/correct 구분 불가
- **Annotation 한계 (Annotation Limitation)**: 효과적인 annotation을 작성할 수 없거나, 작성에 버그 인지가 전제됨

#### A. 분석 추상화 (Analysis Abstraction)

| ID | Limitation Type | 설명 | 해당 케이스 |
|----|----------------|------|------------|
| L1 | `loop-widening` | 루프 내 `+=` 등 누적 연산에 fixpoint iteration 시 widening 적용 → Top/∞. 버기 값과 정상 값이 모두 widened range에 포함되어 구분 불가 | web3bugs_34_H_01, web3bugs_52_H_04, web3bugs_52_H_34, web3bugs_59_H_04, web3bugs_70_H_03, web3bugs_70_H_04, web3bugs_70_H_05 |
| L1b | `loop-widening-precision-loss` | L1의 변형. loop-widening + precision loss가 결합된 케이스. 루프 내 누적 연산이 widening되어 precision loss 차이를 감지할 수 없음 | web3bugs_3_H_04 |
| L1c | `loop-body-granularity` | L1의 변형. intent annotation이 루프 바디 단위로만 배치 가능하나, 버그 탐지에 루프 내부의 더 세밀한 분석이 필요 | web3bugs_45_H_02 |
| L2 | `cross-deployment-call-top` | 별도 deployment된 외부 컨트랙트에 대한 호출 시, callee의 storage state가 annotation scope 밖 → 반환값 Top. 아래 두 하위 유형으로 구분 | - |
| L2a | `interface-call-return-top` | L2의 하위 유형. Interface를 통한 호출로 구현 코드 자체가 없음 → 반환값 Top | web3bugs_5_H_12, web3bugs_5_H_15, web3bugs_14_H_01, web3bugs_14_H_03, web3bugs_16_H_06, web3bugs_25_H_01, web3bugs_29_H_08, web3bugs_29_H_11, web3bugs_31_H_01, web3bugs_42_H_01, web3bugs_44_H_02, web3bugs_52_H_16, web3bugs_58_H_02, web3bugs_58_H_04, web3bugs_61_H_01, web3bugs_61_H_02, web3bugs_61_H_04, web3bugs_62_H_01, web3bugs_70_H_08, web3bugs_71_H_11, web3bugs_78_H_02, web3bugs_79_H_02, web3bugs_101_H_01, web3bugs_101_H_02, web3bugs_110_H_01 |
| L2b | `external-call-state-unknown` | L2의 하위 유형. 구현 코드는 import로 존재하나, 외부 컨트랙트의 런타임 state를 모름 → 반환값 Top | web3bugs_3_H_05 |

#### B. Annotation 한계 (Annotation Limitation)

| ID | Limitation Type | 설명 | 해당 케이스 |
|----|----------------|------|------------|
| L3 | `annotation-inexpressible` | annotation을 구조적으로 표현할 수 없는 케이스. 아래 하위 유형으로 구분 | - |
| L3a | `inexpressible-expected-value` | L3의 하위 유형. 올바른 값을 프로그램 내 기존 변수들의 산술 조합으로 표현할 수 없음. 올바른 값을 구하려면 현재 코드에 존재하지 않는 새로운 중간 계산이 필요 | web3bugs_25_H_05, web3bugs_29_H_05, web3bugs_39_H_02, web3bugs_51_H_04, web3bugs_51_H_06 |
| L3b | `no-target-storage` | L3의 하위 유형. 버기 함수가 target contract의 storage variable을 변경하지 않아 intent annotation을 부착할 대상이 없음 | web3bugs_83_H_02 |
| L4 | `bug-awareness-required` | annotation 표현은 가능하나, 올바른 annotation을 구성하려면 버그를 이미 인지하고 있어야 함. 아래 하위 유형으로 구분 | - |
| L4a | `missing-call-no-effect` | L4의 하위 유형. 필요한 함수 호출이 누락되어 있으나, 그 호출의 효과(side effect)가 타겟 함수 scope 내 변수에 반영되지 않아 함수 내 조건으로 탐지 불가. Post condition 표현은 가능하나 버그 인지를 전제로 함 | web3bugs_83_H_01 |
| L4b | `wrong-arg-order` | L4의 하위 유형. 외부 함수 호출의 인자 순서가 잘못되었으나, DuringFunctionArg annotation으로 인자 값을 검증하려면 callee의 파라미터 의미를 정확히 알아야 함. 그 지식이 있었다면 버그 자체가 발생하지 않았을 것 → 버그 인지 전제 | web3bugs_52_H_15 |
| L8 | `unsupported-construct-top` | 분석 엔진이 지원하지 않는 언어 구조(abi.decode, inline assembly 등)로 인해 관련 변수가 Top이 되어 buggy/correct 구분 불가. L1(loop), L2(cross-deployment)와 독립적인 별도 Top 발생 원인 | web3bugs_35_H_08 |

---

### 임시 분류 (리넘버링 예정)

L8은 Phase 1 완료 후 Group A의 적절한 번호로 리넘버링 예정.

---

| L4c | `missing-state-update` | L4의 하위 유형. 함수 내에서 특정 storage variable이 업데이트되어야 하나 해당 코드가 누락됨. `Changed`/`Before < After` 등의 post-condition으로 표현 가능하나, 어떤 변수가 변경되어야 하는지 아는 것 자체가 버그 인지를 전제 | web3bugs_35_H_10, web3bugs_35_H_12, web3bugs_36_H_02, web3bugs_62_H_03, web3bugs_62_H_10, web3bugs_65_H_01, web3bugs_192_H_01 |
| L4d | `wrong-validation-operator` | L4의 하위 유형. require/validation 조건의 비교 연산자가 잘못됨 (예: `>=` 대신 `<=`). 올바른 조건을 During annotation으로 표현 가능하나, 개발자가 이미 작성한 require를 redundant하게 재검증하는 것은 해당 require가 틀렸음을 인지해야 함 → 버그 인지 전제. 부가적으로 buggy 파라미터가 후속 computation에 미반영되어 state annotation으로도 탐지 불가 | web3bugs_113_H_05 |

---

## Limitation Type 상세 설명

### L1: loop-widening

IntentChecker는 루프를 fixpoint iteration으로 분석한다. 루프 내에서 `+=`, `*=` 등 누적(accumulation) 연산이 있을 경우, iteration 간 값이 수렴하지 않으면 widening이 적용되어 값이 Top(∞)으로 확장된다.

- `+=` 연산: widening → [0, +∞)
- `*=` 연산: widening → [0, +∞)
- `-=` 연산: widening → 0 방향

widening된 범위는 **sound over-approximation**으로, 모든 가능한 concrete 값을 포함한다. 따라서 버기 값과 정상 값이 모두 widened range 안에 들어가면, intent annotation으로 둘을 구분할 수 없다.

**주의**: 루프 내 모든 변수가 widening 대상은 아님. 매 iteration마다 새로 선언/할당되는 변수(declaration)는 fixpoint iteration에서 수렴 가능. 누적 변수(accumulator)만 widening 대상.

**예시** (web3bugs_52_H_34):
```solidity
for (uint256 i = 0; i < pairCount; i++) {
    sumUSD += uint256(price) * (10**10);   // += → widening → Top
    sumNative += ...;                       // += → widening → Top
}
result = sumUSD / sumNative;               // Top / Top → Top
```

#### L1b: loop-widening-precision-loss

L1(loop-widening)과 precision loss가 결합된 케이스. 버그 자체는 precision loss(나눗셈 먼저 수행으로 인한 정밀도 손실)이지만, 해당 연산이 루프 내 누적 변수에서 발생하여 widening → Top이 되면 precision loss 차이를 감지할 수 없다.

#### L1c: loop-body-granularity

IntentChecker의 intent annotation은 루프 바디 단위(iteration 전체)로만 배치 가능하다. 버그가 루프 바디 내부의 특정 지점에서 발생하며, 해당 지점 전후의 중간 상태를 구분해야 탐지 가능한 경우, 현재 annotation 체계로는 표현할 수 없다.

### L2: cross-deployment-call-top

별도로 deployment된 외부 컨트랙트에 대한 호출 시, IntentChecker의 annotation scope(= single deployment unit) 밖이므로 callee의 storage state를 알 수 없어 반환값이 Top이 되는 한계.

IntentChecker의 분석 scope = **single deployment unit**:
- target contract + 상속 컨트랙트 + library (delegatecall) = 같은 `address(this)`, 같은 storage
- 외부 컨트랙트 = 별도 deployment, 별도 storage

debugging annotation은 target contract의 state variable에만 제공 가능하므로, 외부 컨트랙트의 state는 제어할 수 없다.

#### L2a: interface-call-return-top

L2의 하위 유형. 호출 대상이 interface로 선언되어 구현 코드(function body) 자체가 존재하지 않음. 분석할 코드가 없으므로 반환값은 즉시 Top.

**예시** (web3bugs_71_H_11):
```solidity
uint256 _debt = vault.debts(address(this));  // vault = IVault → interface → Top
```

#### L2b: external-call-state-unknown

L2의 하위 유형. 구현 코드는 import로 존재하여 사전분석(dependency pre-analysis)으로 function body 진입은 가능하나, 해당 외부 컨트랙트의 런타임 state variable 값을 알 수 없어 내부 연산이 Top으로 흘러감.

**예시** (web3bugs_3_H_05):
```solidity
// lending()은 RoleAware에서 mainCharacterCache[LENDING] 반환 → address
// Lending은 import된 concrete type → 코드는 있음
// 하지만 Lending 컨트랙트의 state variable에 debugging annotation 불가
uint256 yieldFP = Lending(lending()).viewBorrowingYieldFP(token);  // → Top
```

### L3: annotation-inexpressible

annotation을 구조적으로 표현할 수 없는 케이스. 올바른 값을 기존 변수로 구성할 수 없거나, annotation을 부착할 대상 자체가 없음.

#### L3a: inexpressible-expected-value

버기 코드와 올바른 코드가 **질적(qualitative) 차이 없이 양적(quantitative) 차이만** 존재하여, IntentChecker의 annotation으로 구분할 수 없는 케이스.

**기존 탐지 가능 버그와의 차이:**

| 구분 | 탐지 가능 버그 | L3a 버그 |
|------|--------------|---------|
| 상태변수 변화 방향 | buggy/correct가 다름 (Changed vs Unchanged, 증가 vs 감소) | buggy/correct가 동일 (둘 다 같은 방향 변화) |
| 올바른 값 표현 | 기존 변수의 산술 조합으로 표현 가능 (`a*b` 대신 `a+b`) | 코드에 없는 새로운 중간값 계산 필요 |
| 버그 유형 | 잘못된 연산자, 잘못된 변수, 누락된 업데이트 | 누락된 알고리즘 단계 (결과를 기존 변수로 표현 불가) |

**탐지 불가 조건 (모두 충족 시):**
1. buggy/correct 모두 같은 state variable을 같은 방향으로 변경 → `Changed`/`Unchanged`, `Before < After` 등의 질적 annotation으로 구분 불가
2. 올바른 결과값이 프로그램 내 기존 변수들의 산술 조합(`+`, `-`, `*`, `/`)으로 표현 불가 → `return == expr` annotation 구성 불가
3. 올바른 결과값을 구하려면 코드에 존재하지 않는 새로운 중간 계산(새 변수, 새 함수 호출)이 필요

**예시** (web3bugs_51_H_04):
```solidity
// StableSwap에서 amplifier A가 2개 (A1, A2). swap이 target price를 넘으면 A가 전환됨.
// Buggy: A 전환 시 새 A로 전체 swap을 재계산
return getY(self, tokenIndexFrom, tokenIndexTo, x, xp, aNew, d);

// Correct: target price 기준으로 swap을 분할해야 함
// 1. split point dx₁ 계산 (코드에 없는 새 중간값)
// 2. getY(..., a, d)로 부분 swap 1
// 3. 중간 상태로 새 d₂ 계산
// 4. getY(..., aNew, d₂)로 부분 swap 2
```

올바른 결과는 split point `dx₁`(기존 변수의 단순 산술식이 아닌, 방정식의 해)과 2회의 `getY` 호출을 필요로 하며, 이 중간값들이 현재 프로그램에 존재하지 않아 annotation expression으로 구성할 수 없다.

**참고**: `getY` 내부의 Newton's method loop은 concrete debugging annotation 하에서 수렴 가능하므로 loop-widening(L1)은 blocker가 아님. 핵심 blocker는 올바른 값의 표현 불가능성.

#### L3b: no-target-storage

버기 함수가 target contract의 storage variable을 변경하지 않고 파라미터 계산이나 return 값만 관여하는 경우, intent annotation을 부착할 대상이 없다. IntentChecker의 intent annotation은 target contract의 storage variable 변경을 기준으로 올바름을 검증하므로, storage 변경이 없으면 검증 자체가 불가.

### L4: bug-awareness-required

annotation 표현 자체는 가능하나, 올바른 annotation을 구성하려면 **버그를 이미 인지하고 있어야 하는** 케이스. 개발자가 버그를 모르는 상태에서는 해당 annotation을 작성할 동기나 근거가 없으므로, 현실적 검출 시나리오가 아님.

#### L4a: missing-call-no-effect

필요한 함수 호출이 누락되어 있으나, 그 호출의 효과(side effect)가 타겟 함수 scope 내에서 사용/수정되는 변수에 반영되지 않아, 함수 내 변수 조건으로 탐지 불가.

타겟 함수 내 변수들은 모두 자기 역할을 올바르게 수행하여 값 수준의 이상이 없음. 누락된 호출이 영향을 미치는 변수에 대해 post condition을 걸면 표현 자체는 가능하나, 이는 개발자가 이미 버그를 인지한 것을 전제로 하므로 현실적 검출 시나리오가 아님.

**예시** (web3bugs_83_H_01):
```solidity
function add(address _token, uint _allocationPoints, ...) public onlyOwner {
    // massUpdatePools() 호출 누락 — 기존 풀의 accConcurPerShare 미갱신
    totalAllocPoint = totalAllocPoint.add(_allocationPoints);  // 값 자체는 올바름
    poolInfo.push(PoolInfo({...}));                             // 올바름
    pid[_token] = poolInfo.length - 1;                          // 올바름
}
```
- `totalAllocPoint`, `poolInfo`, `pid[_token]` 모두 정확한 값 → 함수 내 변수 조건으로 이상 감지 불가
- `poolInfo[1].accConcurPerShare(Entry != Exit)` post condition은 가능하나, 개발자가 "기존 풀을 업데이트해야 한다"는 사실을 이미 알아야 작성 가능 → 버그 인지 전제

#### L4b: wrong-arg-order

외부 함수 호출의 인자 순서가 잘못되었으나, `DuringFunctionArg` annotation으로 인자 값을 검증하려면 callee의 파라미터 의미(어떤 position이 어떤 의미인지)를 정확히 알아야 함. 그 지식이 있었다면 인자 순서 오류 자체가 발생하지 않았을 것 → 버그 인지 전제.

**예시** (web3bugs_52_H_15):
```solidity
// pool.swap(nativeAmountIn, foreignAmountIn, to)
// pool0는 foreign→native 스왑 → nativeAmountIn=0, foreignAmountIn=amountIn이어야 함

// Buggy: 인자 순서 뒤바뀜
return pool1.swap(0, pool0.swap(amountIn, 0, address(pool1)), to);

// Correct:
return pool1.swap(pool0.swap(0, amountIn, address(pool1)), 0, to);
```
- `@During pool0.swap.arg[0] == 0` 표현 가능하나, arg[0]이 nativeAmountIn임을 알아야 작성 가능
- 그 지식이 있었다면 `swap(amountIn, 0)` 대신 `swap(0, amountIn)`으로 정확히 썼을 것 → 버그 인지 전제

#### L4d: wrong-validation-operator

require/validation 조건의 비교 연산자가 잘못되었으나 (`>=` 대신 `<=` 등), require 자체가 직관적 검증문이라 annotation 대상이 아님. 올바른 조건을 During annotation으로 코드 중간에 별도 표현 가능하나, 이미 작성된 require를 redundant하게 재검증하는 것은 해당 require가 틀렸음을 인지해야 함 → 버그 인지 전제.

추가적으로, buggy 파라미터가 require 체크에서만 사용되고 후속 computation에 흘러가지 않는 경우, state variable annotation으로도 탐지 불가.

**예시** (web3bugs_113_H_05):
```solidity
// _lend(): lender의 accepted 조건이 borrower의 params보다 "at least as good" 인지 검증
require(
    params.valuation == accepted.valuation &&
        params.duration <= accepted.duration &&
        params.annualInterestBPS >= accepted.annualInterestBPS &&
        params.ltvBPS >= accepted.ltvBPS,   // Buggy: >= 대신 <= 여야 함
    "NFTPair: bad params"
);
```
- `@During params.ltvBPS <= accepted.ltvBPS` 표현 가능하나, require가 틀렸음을 인지해야 작성 가능
- `ltvBPS`는 require 이후 금액 계산에 사용되지 않음 → state variable에 불일치 미반영
- `feesEarnedShare`는 `bentoBox.toShare()` interface call → TOP (L2a 부가 blocker)

#### L4c: missing-state-update

함수 내에서 특정 storage variable이 업데이트되어야 하나 해당 코드가 누락됨. `Changed`/`Before < After` 등의 post-condition으로 표현 가능하나, 어떤 변수가 변경되어야 하는지 아는 것 자체가 버그 인지를 전제.

유사 함수(예: `lock()`)에서 해당 변수를 올바르게 업데이트하고 있더라도, 개발자가 `extendLock()`에서 동일 업데이트가 필요하다는 일관성을 놓쳤기 때문에 버그가 발생한 것. Annotation 시점에서 그 일관성을 챙길 수 있었다면, 코드 작성 시에도 챙겼을 것.

---

## Cross-Deployment-Call-Top 원리

IntentChecker의 분석 및 annotation scope = **single deployment unit**:
- target contract + 상속 컨트랙트 + library (delegatecall) = 같은 `address(this)`, 같은 storage → annotation 가능
- 외부 컨트랙트 = 별도 deployment, 별도 storage → annotation 불가 → Top

| 호출 유형 | 실행 컨텍스트 | storage | debug annotation | 결과 |
|-----------|-------------|---------|-----------------|------|
| 상속 함수 | 같은 deployment | 같은 storage | 가능 | 분석 가능 |
| Library (delegatecall) | 같은 deployment | 같은 storage | 가능 | 분석 가능 |
| 외부 컨트랙트 (코드 있음) | 다른 deployment | 다른 storage | 불가 | Top |
| Interface (코드 없음) | 다른 deployment | 다른 storage | 불가 | Top |

---

## Excluded (excluded)

Numeric logical error 정의에 해당하지 않거나 분석 대상에서 제외된 케이스.

| ID | Exclusion Reason | 설명 | 해당 케이스 |
|----|-----------------|------|------------|
| E1 | `excluded_fixed_code` | 제공된 소스코드가 이미 수정된 버전 | web3bugs_43_H_02 |
| E2 | `overflow-revert` | Solidity >=0.8.0에서 integer overflow가 자동 revert됨. 잘못된 값을 "반환"하는 것이 아니라 실행 자체가 중단 → numeric logical error 정의에 해당하지 않음 | web3bugs_29_H_14 |
| E3 | `duplicate` | 동일 컨트랙트의 동일 버그 지점을 다른 감사자가 중복 보고한 케이스. 원본 케이스에서 분석 | web3bugs_52_H_28 (duplicate of 52_H_04) |
| E4 | `not-a-bug` | 감사 리포트에 보고되었으나 실제로는 버그가 아닌 케이스. Sponsor가 의도된 설계라고 dispute하거나, 코드가 의도대로 정확히 동작함 | web3bugs_52_H_25 |
| E5 | `missing-dependency` | 분석에 필요한 외부 라이브러리(npm 패키지 등)의 소스코드가 제공되지 않아 dependency pre-analysis 불가 | web3bugs_52_H_23, web3bugs_16_H_04 |
| E6 | `multi-transaction` | 버그 발현이 별도 트랜잭션 간 상태 변화에 의존. IntentChecker의 single-transaction 분석 범위 밖 | - |

### Excluded Type 상세 설명

#### E1: excluded_fixed_code

제공된 소스코드가 버기 버전이 아니라 이미 수정(fix)이 적용된 버전. 버그가 재현되지 않으므로 분석 대상에서 제외.

#### E2: overflow-revert

Solidity >=0.8.0의 checked arithmetic에 의해 integer overflow/underflow 발생 시 자동으로 revert됨. 프로그램이 잘못된 값을 "반환"하는 것이 아니라 실행 자체가 중단되므로, numeric logical error(compile 통과 후 잘못된 값 반환) 정의에 해당하지 않음.
