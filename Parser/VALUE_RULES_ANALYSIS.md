# Value 규칙 통합 분석

## 현재 상태

### 1. duringValue (줄 300-303)
```antlr
duringValue
    : arithExpr    # DuringNExpr
    | addressExpr  # DuringAExpr
    | boolExpr     # DuringBExpr
    ;
```
**용도:** During 컨텍스트에서 사용되는 값
**위치:** duringClause에서 사용

### 2. postValue (줄 323-326)
```antlr
postValue
    : arithExpr    # PostNExpr
    | addressExpr  # PostAExpr
    | boolExpr     # PostBExpr
    ;
```
**용도:** Post 컨텍스트에서 사용되는 값
**위치:** postClause에서 사용

### 3. value (줄 366-369)
```antlr
value
    : arithExpr    #NExpr
    | addressExpr  #AExpr
    | boolExpr     #BExpr
    ;
```
**용도:** 일반적인 값 (원래 문법에 있던 것)
**위치:** 어디서 사용되는지 확인 필요

### 4. debugValue (줄 331-334+)
```antlr
debugValue
    : '[' signedNumberLiteral ',' signedNumberLiteral ']'     # DebugIntInterval
    | 'symbolicAddress' numberLiteral                         # DebugSymbolicAddress
    | 'symbolicBytes'   hexStringLiteral                      # DebugSymbolicBytes
    | 'symbolicString'  hexStringLiteral                      # DebugSymbolicString
    | ('true' | 'false' | 'any')                              # DebugBoolToken
    | identifier ('.' identifier)?                            # DebugEnumLiteral
    | 'array' '[' ( signedNumberLiteral (',' signedNumberLiteral)* )? ']'         # DebugIntArray
    | 'arrayAddress' '[' ( numberLiteral (',' numberLiteral)* )? ']'              # DebugAddressArray
    ;
```
**용도:** 테스트 입력값 지정 (디버깅용)
**위치:** debugInput에서 사용 (@GlobalVar, @StateVar, @LocalVar)

### 5. varRef (줄 353-356)
```antlr
varRef
    : 'return' '[' numberLiteral ']'              #ReturnElemRef   // tuple 원소
    | identifier subAccess*                       #NormalVarRef
    ;
```
**용도:** 변수 참조 (변수명, 멤버 접근, 배열 인덱스)
**위치:** intent 전반에 걸쳐 사용

---

## 분석

### 공통점
- **duringValue, postValue, value**: 정확히 같은 구조
  - 모두 arithExpr, addressExpr, boolExpr로 구성
  - 차이는 alt label 이름뿐

### 차이점
- **debugValue**: 완전히 다른 구조
  - 리터럴 구간 `[0, 100]`
  - symbolic 값 `symbolicAddress 1`
  - 배열 리터럴 `array [1, 2, 3]`
  - 테스트 입력 전용

- **varRef**: 변수 참조 전용
  - 값(value)이 아니라 참조(reference)
  - arithExpr 등에서 이미 사용됨

---

## 통합 제안

### ✓ 통합 가능: duringValue + postValue + value
```antlr
intentValue
    : arithExpr
    | addressExpr
    | boolExpr
    ;
```

**장점:**
- 중복 제거
- 더 깔끔한 문법
- 논문에 쓰기 좋음

**단점:**
- Alt label 제거해야 함 (DuringNExpr, PostNExpr, NExpr 중복)
- 또는 alt label 통일 필요

### ✗ 별도 유지: debugValue
- 완전히 다른 용도와 구조
- 테스트 입력 전용
- 통합 불가능

### ✗ 별도 유지: varRef
- 변수 참조 (reference)는 값(value)과 다른 개념
- arithExpr 내부에서 이미 사용됨
- 통합하면 순환 참조 가능성

---

## 구체적인 통합 방안

### 옵션 1: Alt label 제거 (권장)
```antlr
intentValue
    : arithExpr
    | addressExpr
    | boolExpr
    ;

// During context
duringClause
    : varRef '(' BEFORE  relOp AFTER   ')'     # DuringBeforeAfter
    | varRef '(' ASSIGN  relOp CURRENT ')'     # DuringAssignCurrent
    | 'returnExpression' relOp intentValue     # DuringReturnExprCmp
    | 'return' varRef      relOp intentValue   # DuringReturnVarCmp
    | intentValue          relOp intentValue   # DuringRelationalCmp
    | intentValue '=>' intentValue             # DuringImplication
    ;

// Post context
postClause
    : varRef '(' ENTRY relOp EXIT ')'          # PostEntryExit
    | UNCHANGED '(' varRef ')'                 # UnchangedVar
    | 'returnExpression' relOp intentValue     # PostReturnExprCmp
    | 'return' varRef      relOp intentValue   # PostReturnVarCmp
    | intentValue          relOp intentValue   # PostRelationalCmp
    | intentValue '=>' intentValue             # PostImplication
    ;

// Debug context (별도 유지)
debugValue
    : '[' signedNumberLiteral ',' signedNumberLiteral ']'  # DebugIntInterval
    | 'symbolicAddress' numberLiteral                      # DebugSymbolicAddress
    | ...
    ;
```

**효과:**
- duringValue, postValue, value → intentValue로 통합
- Alt label은 최상위(duringClause, postClause)에만 존재
- 깔끔하고 논문에 쓰기 좋음

### 옵션 2: 기존 value 재사용
```antlr
// value는 이미 존재하므로 그대로 사용
value
    : arithExpr
    | addressExpr
    | boolExpr
    ;

// duringValue와 postValue를 제거하고 value 사용
duringClause
    : ...
    | 'returnExpression' relOp value
    | 'return' varRef      relOp value
    | value                relOp value
    | value '=>' value
    ;
```

**장점:**
- 기존 규칙 활용
- 최소 변경

**단점:**
- 'value'라는 이름이 intent 전용이 아님
- 'intentValue'가 더 명확

---

## value 규칙이 현재 어디서 사용되는지 확인 필요

`value` 규칙이 intent 외의 다른 곳에서도 사용되는지 확인이 필요합니다:
- 만약 intent에서만 사용된다면 → intentValue로 이름 변경
- 다른 곳에서도 사용된다면 → value 재사용 또는 별도 유지

검색 필요: `grep -n "value" Solidity.g4` (규칙 사용처)

---

## 최종 권장사항

1. **통합:** duringValue + postValue + value → **intentValue** (옵션 1)
2. **별도 유지:** debugValue (테스트 입력 전용)
3. **별도 유지:** varRef (변수 참조)
4. **Alt label:** intentValue 자체에는 alt label 제거, 상위 규칙에만 유지

이렇게 하면 논문에 쓰기 좋은 깔끔한 문법이 됩니다.
