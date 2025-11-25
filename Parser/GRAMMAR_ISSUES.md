# Solidity.g4 intentUnit 문법 문제점 분석

## 🔴 발견된 문제

### 1. Before/After, Entry/Exit가 일반 value로 파싱 가능

**현재 문법:**
```antlr
predicateDuring
    : varRef '(' 'Before'  relOp 'After'   ')' # DuringBeforeAfter
    | varRef '(' 'Assign'  relOp 'Current' ')' # DuringAssignCurrent
    | commonPredicate                          # DuringCommonPredicate
    ;

predicatePost
    : varRef '(' 'Entry' relOp 'Exit' ')' # PostEntryExit
    | 'Unchanged' '(' varRef ')'          # UnchangedVar
    | commonPredicate                     # PostCommonPredicate
    ;

commonPredicate
  : 'returnExpression' relOp value   # ReturnExprCmp
  | 'return' varRef      relOp value # ReturnVarCmp
  | value                relOp value # RelationalCmp    ← 문제!
  ;

value → arithExpr → arithTerm → arithFactor → varRef
                                            → '[' ... ']'  (interval)
                                            → signedNumberLiteral
```

**문제점:**

#### 1-1. 크로스 변수 비교 가능
`commonPredicate`의 `value relOp value`로 인해:

```solidity
// @During x(Before) < y(After)  ← 가능함 (의도하지 않음!)
```

- `x(Before)`가 `varRef`로 파싱됨
- `y(After)`도 `varRef`로 파싱됨
- 둘 다 `value`이므로 `value < value` 매칭

**의도:**
- `Before`/`After`는 **같은 변수**에만 적용
- `x(Before < After)` ✓
- `x(Before) < y(After)` ✗

#### 1-2. 키워드가 일반 식별자로 해석 가능

`Before`, `After`, `Entry`, `Exit`, `Current`가 키워드로 예약되지 않음:

```solidity
// @During Before < After  ← 'Before'와 'After'를 변수명으로 해석 가능
```

### 2. Implication 규칙의 혼란

**현재 문법:**
```antlr
duringClause
    : predicateDuring                      # DuringClauseSingle
    | predicateDuring '=>' predicateDuring # DuringImplication
    ;

postClause
    : predicatePost                      # PostClauseSingle
    | predicatePost '=>' predicatePost   # PostImplication
    ;
```

**문제:**
```solidity
// @During x(Before < After) => y(Assign < Current)
```

위 코드가 가능한데, 이게 의도한 것인지?

- 왼쪽: `x(Before < After)` - During predicate
- 오른쪽: `y(Assign < Current)` - During predicate
- 의미: "x가 증가하면 → y가 할당값보다 작아야 한다"?

**의도 확인 필요:**
1. Implication이 필요한가?
2. 필요하다면 어떤 조합이 허용되어야 하나?
   - `BeforeAfter => BeforeAfter` ✓?
   - `BeforeAfter => AssignCurrent` ✓?
   - `commonPredicate => BeforeAfter` ✓?

### 3. commonPredicate의 모호성

**현재 문법:**
```antlr
commonPredicate
  : 'returnExpression' relOp value   # ReturnExprCmp
  | 'return' varRef      relOp value # ReturnVarCmp
  | value                relOp value # RelationalCmp
  ;
```

**문제:**
- `value relOp value`가 너무 포괄적
- `varRef`가 `value`에 포함되므로 모든 변수 참조 가능
- During/Post 특수 키워드와 구분 안됨

**예:**
```solidity
// @During x < y          ← commonPredicate (일반 비교)
// @During x(Before) < 10 ← 이것도 가능? (Before가 varRef의 일부로 파싱?)
```

---

## ✅ 제안하는 수정 방안

### 옵션 1: 키워드 예약 + commonPredicate 제한 (권장)

```antlr
// 1. 키워드 예약
tokens {
    BEFORE, AFTER, ENTRY, EXIT, CURRENT, ASSIGN, UNCHANGED
}

// 2. predicateDuring 명확화
predicateDuring
    : varRef '(' BEFORE  relOp AFTER   ')' # DuringBeforeAfter
    | varRef '(' ASSIGN  relOp CURRENT ')' # DuringAssignCurrent
    | duringCommonPredicate                # DuringCommonPredicate
    ;

// 3. predicatePost 명확화
predicatePost
    : varRef '(' ENTRY relOp EXIT ')' # PostEntryExit
    | UNCHANGED '(' varRef ')'        # UnchangedVar
    | postCommonPredicate             # PostCommonPredicate
    ;

// 4. commonPredicate를 분리
duringCommonPredicate
  : 'returnExpression' relOp duringValue
  | 'return' varRef      relOp duringValue
  | duringValue          relOp duringValue
  ;

postCommonPredicate
  : 'returnExpression' relOp postValue
  | 'return' varRef      relOp postValue
  | postValue            relOp postValue
  ;

// 5. value를 제한적으로 정의
duringValue
    : arithExpr    // varRef를 포함하지만 Before/After 제외
    | addressExpr
    | boolExpr
    ;

postValue
    : arithExpr    // varRef를 포함하지만 Entry/Exit 제외
    | addressExpr
    | boolExpr
    ;
```

### 옵션 2: 단순화 - Implication 제거

만약 Implication이 실제로 사용되지 않는다면:

```antlr
duringClause
    : predicateDuring                      # DuringClauseSingle
    // | predicateDuring '=>' predicateDuring # DuringImplication  ← 제거
    ;

postClause
    : predicatePost                        # PostClauseSingle
    // | predicatePost '=>' predicatePost   # PostImplication     ← 제거
    ;
```

### 옵션 3: varRef 제한

`varRef`가 특수 키워드를 포함하지 않도록:

```antlr
varRef
    : 'return' '[' numberLiteral ']'
    | normalIdentifier subAccess*
    ;

normalIdentifier
    : identifier
    // Before, After, Entry, Exit, Current 등을 여기서 명시적으로 제외
    ;

// 또는 lexer에서 키워드 정의
BEFORE  : 'Before' ;
AFTER   : 'After' ;
ENTRY   : 'Entry' ;
EXIT    : 'Exit' ;
CURRENT : 'Current' ;
ASSIGN  : 'Assign' ;
```

---

## 🔍 확인이 필요한 사항

### 1. 의도한 사용 패턴
```solidity
// During
// @During x(Before < After)              ✓ 의도함
// @During x(Before) < 10                 ? 의도?
// @During x(Before) < y(After)           ✗ 의도하지 않음
// @During x(Before < After) => y < 100   ? Implication 필요?

// Post
// @Post x(Entry < Exit)                  ✓ 의도함
// @Post x(Entry) < 10                    ? 의도?
// @Post x(Entry) < y(Exit)               ✗ 의도하지 않음
// @Post x(Entry < Exit) => Unchanged(y)  ? Implication 필요?
```

### 2. commonPredicate 사용 범위
```solidity
// @During returnExpression < 100         ✓ 필요함
// @During return[0] < 10                 ✓ 필요함
// @During x < 10                         ✓ 일반 비교
// @During x < y                          ? 두 변수 비교 필요?
```

### 3. Implication 실제 사용
- 코드베이스에서 `=>`를 실제로 사용하는 곳이 있나?
- 있다면 어떤 패턴으로 사용하나?
- 없다면 문법에서 제거 고려

---

## 📝 권장 조치

1. **즉시 수정 필요:**
   - `Before`, `After`, `Entry`, `Exit`, `Current`를 키워드로 예약
   - `commonPredicate`의 `value relOp value`에서 이런 키워드 사용 금지

2. **설계 검토 필요:**
   - Implication(`=>`) 실제 사용 여부 확인
   - 사용하지 않으면 제거
   - 사용한다면 허용 조합 명확히 정의

3. **테스트:**
   - 의도하지 않은 구문 (`x(Before) < y(After)`)이 파싱 에러 발생하는지 확인
   - 의도한 구문만 허용되는지 검증
