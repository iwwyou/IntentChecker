# Intent 문법 최종 구조 (논문용)

## 목표
- **Numeric 취약점 탐지**: NumScout 5개 취약점 완벽 지원
- **명확한 verification logic**: 각 top-level 규칙이 논문에 설명 가능
- **단순성**: 불필요한 중복 제거

---

## 최종 문법 구조

### 1. Intent 정의

```antlr
// During Intent
duringIntent
    : '//' '@During' duringClause (logicOp duringClause)*
    ;

// Post Intent
postIntent
    : '//' '@Post' postClause (logicOp postClause)*
    ;
```

**변경점:**
- `,` 구분자 제거
- `&&`, `||` (logicOp)만으로 조합
- `duringFormula`, `postFormula` 중간 단계 제거

---

### 2. During Verification Patterns

```antlr
duringClause
    : intentValue '(' BEFORE  relOp AFTER   ')'     # DuringBeforeAfter
    | intentValue '(' ASSIGN  relOp CURRENT ')'     # DuringAssignCurrent
    | 'returnExpression' relOp intentValue          # DuringReturnExprCmp
    | 'return' intentValue     relOp intentValue    # DuringReturnVarCmp
    | intentValue              relOp intentValue    # DuringRelationalCmp
    | intentValue '=>' intentValue                  # DuringImplication
    ;
```

**각 패턴의 의미:**

#### DuringBeforeAfter
```solidity
// @During balance(Before < After)
// @During devReward(Before < After)
```
- **용도**: 변수의 변화 추적
- **취약점**: Operator Order Issue, Precision Loss Trend

#### DuringAssignCurrent
```solidity
// @During x(Assign < Current)
```
- **용도**: 할당 시점과 현재 값 비교
- **사용 빈도**: 낮음

#### DuringReturnExprCmp
```solidity
// @During returnExpression < 100
```
- **용도**: 함수 반환값 전체 검증

#### DuringReturnVarCmp
```solidity
// @During return tokenAmountIn > 0
```
- **용도**: 특정 반환 튜플 요소 검증

#### DuringRelationalCmp
```solidity
// @During x < y
// @During fee > 0
// @During msg.value / 1 ether > minAmount
// @During devReward == PercentOf(almReward, 10)
```
- **용도**: 일반 변수/표현식 비교
- **취약점**: 모든 NumScout 취약점에서 사용

#### DuringImplication ⭐
```solidity
// @During (poolAmountOut > 0) => (tokenAmountIn > 0)
// @During (amountToTaker > 0) => (fee > 0)
```
- **용도**: 조건부 검증 (A이면 B도 성립)
- **취약점**: Exchange Problem, Precision Loss Trend
- **중요도**: 매우 높음 (무료 토큰 방지)

---

### 3. Post Verification Patterns

```antlr
postClause
    : intentValue '(' ENTRY relOp EXIT ')'          # PostEntryExit
    | UNCHANGED '(' intentValue ')'                 # UnchangedVar
    | 'returnExpression' relOp intentValue          # PostReturnExprCmp
    | 'return' intentValue     relOp intentValue    # PostReturnVarCmp
    | intentValue              relOp intentValue    # PostRelationalCmp
    | intentValue '=>' intentValue                  # PostImplication
    ;
```

**각 패턴의 의미:**

#### PostEntryExit
```solidity
// @Post balance(Entry < Exit)
// @Post contractBalance(Entry > Exit)
```
- **용도**: 함수 진입/종료 시점 값 비교
- **취약점**: Minor Amount Retention

#### UnchangedVar
```solidity
// @Post Unchanged(owner)
// @Post Unchanged(totalSupply)
```
- **용도**: 변수가 변경되지 않음을 검증
- **취약점**: Minor Amount Retention (implication과 함께)

#### PostImplication
```solidity
// @Post (winners.length > 0) => (contractBalance(Entry) == contractBalance(Exit))
```
- **용도**: 조건부 검증
- **취약점**: Minor Amount Retention

---

### 4. intentValue - Numeric Expression

```antlr
intentValue
    : arithExpr
    ;

arithExpr
    : arithExpr ('+' | '-') arithTerm
    | arithTerm
    ;

arithTerm
    : arithTerm ('*' | '/' | '%') arithFactor
    | arithFactor
    ;

arithFactor
    : signedNumberLiteral
    | '[' signedNumberLiteral ',' signedNumberLiteral ']'   // Interval
    | varRef
    | 'PercentOf' '(' arithExpr ',' numberLiteral ')'
    | 'ceil' '(' arithExpr ',' numberLiteral ')'
    | 'floor' '(' arithExpr ',' numberLiteral ')'
    | '(' arithExpr ')'
    ;
```

**특징:**
- **Numeric 전용**: address, bool 제거
- **NumScout 완벽 지원**: 5개 취약점 모두 커버
- **Interval domain 안전**: PercentOf, ceil, floor 모두 안전하게 요약 가능

---

### 5. 예약 키워드

```antlr
BEFORE    : 'Before' ;
AFTER     : 'After' ;
ENTRY     : 'Entry' ;
EXIT      : 'Exit' ;
CURRENT   : 'Current' ;
ASSIGN    : 'Assign' ;
UNCHANGED : 'Unchanged' ;
```

**효과:**
- 크로스 변수 temporal 비교 방지: `x(Before) < y(After)` ✗
- 명확한 의미론

---

## NumScout 5개 취약점 매핑

### 1. Div In Path
```solidity
// @During (msg.value / 1 ether) < minAmount
```
**패턴**: DuringRelationalCmp

### 2. Operator Order Issue
```solidity
// @During devReward(Before < After)
// @During devReward == PercentOf(almReward, 10)
// @During (almReward > 0) => (devReward > 0)
```
**패턴**: DuringBeforeAfter, DuringRelationalCmp, DuringImplication

### 3. Minor Amount Retention
```solidity
// @Post contractBalance(Entry > Exit)
// @Post Unchanged(contractBalance)
// @During (totalGameInterest % winners.length != 0) => Unchanged(contractBalance)
```
**패턴**: PostEntryExit, UnchangedVar, DuringImplication

### 4. Exchange Problem ⭐⭐
```solidity
// @During (poolAmountOut > 0) => (tokenAmountIn > 0)
// @During poolAmountOut < tokenAmountIn
```
**패턴**: DuringImplication, DuringRelationalCmp

### 5. Precision Loss Trend
```solidity
// @During fee(Before < After)
// @During (amountToTaker > 0) => (fee > 0)
```
**패턴**: DuringBeforeAfter, DuringImplication

---

## 제거된 요소

### 1. duringValue, postValue, value
**이유**: intentValue로 통합 (중복 제거)

### 2. addressExpr, boolExpr
**이유**: Numeric 취약점 탐지가 목표, NumScout에서 불필요

### 3. duringFormula, postFormula
**이유**: `,` 구분자 제거, logicOp만 사용

### 4. 복잡한 alt label
**이유**:
- `DuringNExpr`, `PostNExpr`, `NExpr` 중복 제거
- intentValue는 alt label 없이 단순하게

---

## 논문 작성 포인트

### 1. 명확한 Verification Pattern
각 top-level 규칙이 특정 verification 의미를 가짐:
- BeforeAfter: 시간적 변화
- Implication: 조건부 검증
- Unchanged: 불변성
- etc.

### 2. Numeric 전용
- address, bool 제외
- Precision loss, rounding error 등 numeric 취약점에 집중

### 3. Interval Domain 안전성
- PercentOf, ceil, floor 모두 interval에서 안전하게 요약 가능
- Static analysis 가능

### 4. 실용성
- NumScout 5개 취약점 100% 커버
- 실제 Solidity 코드에서 발견된 취약점 기반

---

## 문법 변천사

### Before
```antlr
duringIntent: '//' '@During' duringFormula (',' duringFormula)*
duringFormula: duringClause (logicOp duringClause)*
duringClause: predicateDuring | predicateDuring '=>' predicateDuring
predicateDuring: varRef '(' 'Before' ... ')' | commonPredicate
commonPredicate: value relOp value  // 문제: x(Before) < y(After) 가능
duringValue: arithExpr | addressExpr | boolExpr
postValue: arithExpr | addressExpr | boolExpr
value: arithExpr | addressExpr | boolExpr
```

### After (Final)
```antlr
duringIntent: '//' '@During' duringClause (logicOp duringClause)*
duringClause: intentValue '(' BEFORE ... ')'
            | intentValue relOp intentValue
            | intentValue '=>' intentValue
            | ...
intentValue: arithExpr  // Numeric only
```

**개선점:**
- 3개 value 규칙 → 1개 intentValue
- 키워드 예약으로 모호성 제거
- `,` 제거로 단순화
- address/bool 제거로 목표 명확화
