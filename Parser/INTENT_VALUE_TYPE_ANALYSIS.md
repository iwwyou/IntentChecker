# Intent Value Type Analysis

## NumScout 5개 취약점에서 실제 사용되는 패턴

### 1. Div In Path
```solidity
// @During (msg.value / 1 ether) < minAmount
```
**사용 타입:** arithExpr only

### 2. Operator Order Issue
```solidity
// @During devReward(Before < After)
// @During (almReward > 0) => (devReward > 0)
```
**사용 타입:** arithExpr only

### 3. Minor Amount Retention
```solidity
// @Post contractBalance(Entry > Exit)
// @During (totalGameInterest % winners.length != 0) => Unchanged(contractBalance)
```
**사용 타입:** arithExpr only

### 4. Exchange Problem ⭐⭐
```solidity
// @During (poolAmountOut > 0) => (tokenAmountIn > 0)
// @During poolAmountOut < tokenAmountIn
```
**사용 타입:** arithExpr only

### 5. Precision Loss Trend
```solidity
// @During (amountToTaker > 0) => (fee > 0)
// @During fee(Before < After)
```
**사용 타입:** arithExpr only

---

## 결론: Implication에서 필요한 것

### ✓ 필요함
```solidity
duringValue '=>' duringValue  // (x > 0) => (y > 0)
```
- 변수 간 숫자 비교가 주 사용 사례
- arithExpr가 핵심

### ✗ 필요 없음
```solidity
returnExpression '=>' returnExpression  // 의미 없음
return x > return y                     // 의미 없음
```
- 반환값 비교는 implication 외부에서만 사용
- implication은 함수 실행 중의 변수 관계 검증용

---

## duringValue/postValue에 포함된 타입들

### 1. arithExpr (필수 ✓)
```solidity
x > 0
balance + amount
msg.value / 1 ether
```
**사용 빈도:** 매우 높음
**필요성:** 필수

### 2. addressExpr (검토 필요 ?)
```solidity
msg.sender == owner
recipient != address(0)
```
**사용 빈도:** 낮음
**implication에서 사용?**
- `(recipient == address(0)) => revert` ← require로 처리
- 실제 implication보다는 단순 조건문에서 사용
- **제안:** 일반 비교에는 유지, implication에서는 불필요

### 3. boolExpr (검토 필요 ?)
```solidity
isActive == true
hasPermission
```
**사용 빈도:** 낮음
**implication에서 사용?**
- `(isActive) => (balance > 0)` ← 가능하지만 드묾
- **제안:** 일반 비교에는 유지, implication에서는 불필요

---

## 제안하는 문법 구조

### 옵션 1: Implication을 duringValue만으로 (권장)
```antlr
duringClause
    : varRef '(' BEFORE  relOp AFTER   ')'     # DuringBeforeAfter
    | varRef '(' ASSIGN  relOp CURRENT ')'     # DuringAssignCurrent
    | 'returnExpression' relOp duringValue     # DuringReturnExprCmp
    | 'return' varRef      relOp duringValue   # DuringReturnVarCmp
    | duringValue          relOp duringValue   # DuringRelationalCmp
    | duringValue '=>' duringValue             # DuringImplication
    ;

duringValue
    : arithExpr    # DuringNExpr
    | addressExpr  # DuringAExpr   // 일반 비교용
    | boolExpr     # DuringBExpr    // 일반 비교용
    ;
```

**장점:**
- 깔끔하고 단순
- `returnExpression => returnExpression` 불가능
- `return x > return y` 불가능
- 실제 필요한 패턴만 허용

**단점:**
- implication에서 address/bool 비교 불가 (하지만 필요 없을 가능성 높음)

### 옵션 2: Implication을 arithExpr만으로 (가장 제한적)
```antlr
duringClause
    : varRef '(' BEFORE  relOp AFTER   ')'     # DuringBeforeAfter
    | varRef '(' ASSIGN  relOp CURRENT ')'     # DuringAssignCurrent
    | 'returnExpression' relOp duringValue     # DuringReturnExprCmp
    | 'return' varRef      relOp duringValue   # DuringReturnVarCmp
    | duringValue          relOp duringValue   # DuringRelationalCmp
    | arithExpr '=>' arithExpr                 # DuringImplication
    ;
```

**장점:**
- NumScout 5개 취약점 모두 커버
- 가장 명확하고 제한적

**단점:**
- 향후 address/bool implication이 필요하면 수정 필요

### 옵션 3: duringValue를 arithExpr만으로 (극단적)
```antlr
duringValue
    : arithExpr    # DuringNExpr
    ;
```

**고려사항:**
- address 비교 (`msg.sender == owner`)가 필요한 경우 있음
- bool 비교도 가끔 필요
- **제안:** addressExpr, boolExpr는 유지

---

## 최종 권장사항

1. **Implication:** `duringValue '=>' duringValue`만 허용 (옵션 1)
   - `returnExpression`, `return varRef` 제거

2. **duringValue 타입:** arithExpr, addressExpr, boolExpr 모두 유지
   - NumScout 외의 취약점에서도 필요할 수 있음
   - 제거할 이유 없음

3. **Post도 동일하게 적용**

이렇게 하면:
- ✓ `(x > 0) => (y > 0)` 허용
- ✗ `returnExpression => returnExpression` 금지
- ✗ `return x > return y` 금지
- ✓ `msg.sender == owner` 허용 (일반 비교)
- ✓ `isActive` 허용 (일반 비교)
