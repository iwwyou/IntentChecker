# L4/L5 Case-by-Case Deep Review Prompt

## 목적

나는 Solidity 스마트 컨트랙트의 development-time 검증 도구 **IntentChecker**에 대한 논문을 쓰고 있어. 논문의 RQ2는 mitigation이 불가능했던 55개 instance를 5개 limitation type (L1-L3: analysis-engine, L4-L5: annotation-grammar)으로 분류함.

L1-L3(21 case)는 이미 검토가 끝났고, 이제 **L4-L5에 해당하는 34개 case를 하나씩 깊이 이해하고 분류의 타당성과 근본 원인을 재검토**하려 함. 이 분석 결과는 paper의 **Introduction, RQ2, Discussion** 세 섹션 모두에서 insight로 쓰일 예정.

단순히 기존 분류를 그대로 받아들이지 말고, **실제 코드의 의미(컨트랙트가 뭘 하려는지, 버그의 본질이 무엇인지)를 audit report와 source code로 깊이 이해한 뒤** 재검토할 것.

---

## 프로젝트 경로

프로젝트 루트: `C:/Users/isjeon/PycharmProjects/pythonProject/SolidityGuardian/`

### 필수 참고 파일

| 파일 | 용도 |
|---|---|
| `evaluation/RQ1/limitation_types.md` | 현재 L4-L5 taxonomy 정의 (L4a~L5b 각 subcategory 설명) |
| `evaluation/RQ1/annotation_plans.md` | case별 annotation 시도 및 not_detectable 사유 기록 |
| `evaluation/RQ1/target_contracts_original/*.sol` | case별 원본 Solidity 코드 (예: `web3bugs_25_H_01.sol`) |
| `evaluation/RQ1/target_contracts_contraction/*.sol` | target function + internal chain만 추출한 contraction |
| `evaluation/RQ1/cases/<name>/<name>.json` | 최종 분석 입력 (contraction + annotation injection) |
| `paper/main.tex` (line 1307-1342) | L4a~L5b 현재 paper 문장 (재작성 대상) |
| `paper/main.tex` (line 584-620, Figure 6) | IntentChecker annotation grammar BNF |
| `C:/Users/isjeon/Web3Bugs/reports/<contest>.md` | **audit report** — 버그의 origin, description, severity 상세. 필수 참조. |

### Audit report 매핑 규칙

`web3bugs_{contest}_H_{idx}` → `C:/Users/isjeon/Web3Bugs/reports/{contest}.md`의 `[H-{idx}]` 섹션

예:
- `web3bugs_25_H_01` → `reports/25.md` 내 `## [[H-01] CompositeMultiOracle returns wrong decimals...]`
- `web3bugs_51_H_04` → `reports/51.md` 내 `## [[H-04] ...]`
- `web3bugs_113_H_05` → `reports/113.md` 내 `## [[H-05] ...]`

---

## IntentChecker Annotation Grammar 요약 (판단의 기준)

L4/L5 판정은 **이 grammar 하에서 올바른 annotation을 작성 가능한가** 여부로 결정됨.

### 지원하는 annotation 유형

- `// @During <duringClause>` — 함수 실행 중 특정 지점의 intent
- `// @Post <postClause>` — 함수 종료 시 intent

### duringClause 주요 형태

- `intentValue (before relOp after)` — 특정 문장 전후 값 비교
- `intentValue (assign relOp current)` — 대입 시 값 비교
- `identifier.arg[n] relOp intentValue` — 호출 인자 검증
- `require feasible` / `assert feasible` — guard의 도달 가능성
- 아래 commonClause 공통 형태 사용 가능

### postClause 주요 형태

- `intentValue (entry relOp exit)` — 함수 입장/종료 시 state variable 비교
- commonClause 사용 가능

### commonClause (공통)

- `returnExpression relOp intentValue` — 반환값 조건
- `return[n] relOp intentValue` — tuple 반환의 n번째
- `intentValue relOp PercentOf(intentValue, p)` — 비율 기반 비교
- `intentValue relOp ceil(intentValue, d)` / `floor(intentValue, d)` — 반올림
- `intentValue relOp intentValue` — 단순 비교
- `intentValue => intentValue` — implication
- `changed(intentValue, true|false)` — state variable 변경 여부

### intentValue (핵심 제약)

```
intentValue → arithExpr
arithExpr   → arithExpr (+|-) arithTerm | arithTerm
arithTerm   → arithTerm (*|/|%) arithFactor | arithFactor
arithFactor → number | [number, number] | varRef | (arithExpr)
varRef      → identifier subAccess*
subAccess   → . identifier | [expr]
```

**허용되는 것**: 변수 참조 (member/index access 포함), 정수 리터럴, interval `[a, b]`, +, -, *, /, %, 괄호.

**허용되지 않는 것**:
- 함수 호출 (e.g., `IOracle(x).decimals()`, `sqrt(x)`)
- 비트 연산자 (`<<`, `>>`, `&`, `|`, `^`)
- 지수 (`**`)
- 사용자 정의 함수·라이브러리 호출
- 현재 scope에 없는 임시 변수 참조

### Debug annotations (분석의 입력)

`@StateVar`, `@LocalVar`, `@GlobalVar`, `@IReturn` — 변수 범위를 공급. view/pure interface call의 반환에만 `@IReturn` 가능.

---

## 분석 대상 34개 case

### L4a (inexpressible-expected-value, 10 cases)

| Case | 원본 .sol | annotation_plans.md line |
|---|---|---|
| web3bugs_25_H_01 | `target_contracts_original/web3bugs_25_H_01.sol` | 348 |
| web3bugs_25_H_05 | `target_contracts_original/web3bugs_25_H_05.sol` | 1998 |
| web3bugs_29_H_05 | `target_contracts_original/web3bugs_29_H_05.sol` | 1410 |
| web3bugs_39_H_02 | `target_contracts_original/web3bugs_39_H_02.sol` | 1283 |
| web3bugs_51_H_04 | `target_contracts_original/web3bugs_51_H_04.sol` | 838 |
| web3bugs_51_H_06 | `target_contracts_original/web3bugs_51_H_06.sol` | 904 |
| web3bugs_59_H_05 | `target_contracts_original/web3bugs_59_H_05.sol` | 2386 |
| web3bugs_61_H_01 | `target_contracts_original/web3bugs_61_H_01.sol` | 1819 |
| web3bugs_61_H_02 | `target_contracts_original/web3bugs_61_H_02.sol` | 2326 |
| web3bugs_61_H_04 | `target_contracts_original/web3bugs_61_H_04.sol` | 2016 |

### L4b (no-target-storage, 8 cases)

| Case | 원본 .sol |
|---|---|
| web3bugs_17_H_02 | `target_contracts_original/web3bugs_17_H_02.sol` |
| web3bugs_52_H_15 | `target_contracts_original/web3bugs_52_H_15.sol` |
| web3bugs_52_H_16 | `target_contracts_original/web3bugs_52_H_16.sol` |
| web3bugs_58_H_04 | `target_contracts_original/web3bugs_58_H_04.sol` |
| web3bugs_62_H_01 | `target_contracts_original/web3bugs_62_H_01.sol` |
| web3bugs_70_H_08 | `target_contracts_original/web3bugs_70_H_08.sol` |
| web3bugs_83_H_02 | `target_contracts_original/web3bugs_83_H_02.sol` |
| web3bugs_110_H_01 | `target_contracts_original/web3bugs_110_H_01.sol` |

### L4c (magnitude-only-difference, 1 case)

| Case | 원본 .sol |
|---|---|
| web3bugs_35_H_10 | `target_contracts_original/web3bugs_35_H_10.sol` |

### L4d (invariant-masked, 1 case)

| Case | 원본 .sol |
|---|---|
| web3bugs_36_H_02 | `target_contracts_original/web3bugs_36_H_02.sol` |

### L5a (missing-code, 7 cases)

| Case | 원본 .sol |
|---|---|
| web3bugs_35_H_12 | `target_contracts_original/web3bugs_35_H_12.sol` |
| web3bugs_52_H_23 | `target_contracts_original/web3bugs_52_H_23.sol` |
| web3bugs_62_H_03 | `target_contracts_original/web3bugs_62_H_03.sol` |
| web3bugs_62_H_10 | `target_contracts_original/web3bugs_62_H_10.sol` |
| web3bugs_65_H_01 | `target_contracts_original/web3bugs_65_H_01.sol` |
| web3bugs_83_H_01 | `target_contracts_original/web3bugs_83_H_01.sol` |
| web3bugs_192_H_01 | `target_contracts_original/web3bugs_192_H_01.sol` |

### L5b (wrong-code, 7 cases)

| Case | 원본 .sol |
|---|---|
| web3bugs_31_H_01 | `target_contracts_original/web3bugs_31_H_01.sol` |
| web3bugs_35_H_11 | `target_contracts_original/web3bugs_35_H_11.sol` |
| web3bugs_70_H_09 | `target_contracts_original/web3bugs_70_H_09.sol` |
| web3bugs_79_H_02 | `target_contracts_original/web3bugs_79_H_02.sol` |
| web3bugs_101_H_02 | `target_contracts_original/web3bugs_101_H_02.sol` |
| web3bugs_112_H_01 | `target_contracts_original/web3bugs_112_H_01.sol` |
| web3bugs_113_H_05 | `target_contracts_original/web3bugs_113_H_05.sol` |

---

## Case별 분석 템플릿

34개 case를 **하나씩 순서대로** 다음 템플릿으로 깊이 분석한다. 한 case를 끝내기 전에 다음 case로 넘어가지 말 것.

```markdown
## Case: web3bugs_{contest}_H_{idx} (현재 분류: L{_x})

### 1. Audit report 인용
- 출처: `reports/{contest}.md` 내 `[H-{idx}]` 섹션
- Title: (원문 인용)
- Severity: High / Medium / ...
- Warden(s): (보고자)
- Proof of concept / attack scenario: (audit report 원문의 핵심 3~5줄 발췌)
- 권고된 수정안: (audit report가 제시한 fix)

### 2. 코드 의미 이해
**목적: 논문에 적을 insight와 정확한 정보를 위해, 표면적 설명이 아닌 protocol-level 의미까지 파고들 것.**

- **(2a) Contract 목적 & 시스템 위치**: 이 컨트랙트가 전체 protocol에서 어떤 역할인지 (oracle aggregator / vault / AMM pool / staking 등). 어떤 invariant·워크플로우를 담당하는지.
- **(2b) 대상 함수의 컨트랙트 내 역할**: `FunctionName(...)` 시그니처. 이 함수가 왜 존재하는지 — 어떤 caller가 어떤 목적으로 호출하며, 이 함수의 성공/실패가 시스템에 어떤 영향을 주는지.
- **(2c) 함수 의도 (수식 포함)**: 원래 해야 할 일을 명시적으로. 가능하면 수학적 표현 (e.g., `out = in * rate / 1e18`).
- **(2d) Line-by-line 분석**: bug 주변 ±몇 줄을 줄 단위로 해석. 각 줄이 무엇을 하는지, 왜 그 순서로 쓰였는지. Bug line은 특히 상세하게.
- **(2e) 버그의 근본 의미**: 단순 "연산자 오류"가 아니라 "이 오류가 protocol 수준에서 왜 자산 손실·권한 우회·회계 파손으로 이어지는가". Audit report의 attack scenario와 연결.
- **(2f) 올바른 fix (audit 권고 + 코드)**: audit report가 제시한 fix를 인용하고, 실제 코드 diff 수준으로 기술.

### 3. IntentChecker annotation 시도
어떤 annotation이 이상적일까? 아래 순서로 시도:

- (a) buggy/correct를 구분할 수 있는 state variable 변화가 있는가?
  - yes → `changed(x, true)` / `x(entry relOp exit)` 시도
  - no → L4b 후보
- (b) 올바른 값을 기존 변수·상수·산술 조합으로 쓸 수 있는가?
  - yes → `returnExpression == arithExpr` 또는 `var(entry == arithExpr)` 시도
  - no → L4a 후보 (왜 표현 불가능한지 명시)
- (c) 표현 가능하지만 "버그를 이미 알아야 쓸 수 있는" annotation인가?
  - yes → L5 후보 (L5a: missing code / L5b: wrong code)

시도한 annotation을 한 줄로 작성하고, IntentChecker가 buggy/correct 각각에서 어떤 판정(Satisfied/Warning/Violated)을 낼지 예측.

### 4. 분류 타당성 검토
- 현재 분류: L4a/L4b/L4c/L4d/L5a/L5b 중 하나
- 이 case의 blocker 본질: (분류에 부합하는지, 더 적절한 분류는 있는지)
- 만약 재분류가 필요하면: **from L{_x} → to L{_y}** 이유 포함

### 5. 이 case가 드러내는 근본 원인
다음 중 어떤 것에 해당하는가? (복수 선택 가능, 필요하면 새 카테고리 제안)

- [G1] Grammar 내 함수 호출 부재
- [G2] Grammar 내 비트 연산·지수 부재
- [G3] intermediate variable이 코드에 없고 grammar로 도출 불가
- [G4] 상태 변경 자체가 없어 attach 대상 부재 (view/pure, library, 외부 위임)
- [G5] buggy/correct가 질적 동일, 양적 차이만 — `changed`/`entry-exit`로 구분 불가
- [G6] 다중 변수 invariant (곱 보존 등)를 PostEntryExit가 표현 못 함
- [G7] 버그 인지 전제 — 올바른 annotation이 fix의 특정 형태를 이미 알고 있어야 가능
- [G8] 외부 contract의 state 의존성 — `@IReturn`이 허용하는 view/pure 밖
- [G9] 기타 (구체 기술)

### 6. paper 문장 개선 제안 (필요 시)
현재 `paper/main.tex` 해당 subcategory 문장이 이 case의 본질을 충분히 설명하는가?
- yes → 그대로 유지
- no → 개선 제안 (3줄 이내)
```

---

## Subcategory별 종합 요약 (각 10개 case 끝날 때마다)

한 subcategory(L4a 10개, L4b 8개, ...)의 모든 case 분석이 끝나면 종합 요약 작성:

```markdown
### L{_x} Summary ({N} cases reviewed)

**공통 root cause (G-카테고리 빈도)**:
- G1: X cases
- G3: Y cases
- ...

**재분류 제안**:
- {case} → L{_y} ({이유})

**paper 문장 개선 최종안** (1307-1342의 해당 항목):
> <수정된 문장>

**Introduction/Discussion에 반영할 insight**:
- (이 subcategory가 보여주는 한계의 본질 — 2~3줄)
```

---

## 최종 산출물

전체 34개 case 분석이 끝나면:

1. **`evaluation/RQ1/l4_l5_case_review.md`** — 각 case의 상세 분석 (위 템플릿) + 6개 subcategory summary
2. **`evaluation/RQ1/annotation_plans.md`** — 기존 case 항목 중 잘못된 설명 수정 (diff 제안)
3. **`evaluation/RQ1/limitation_types.md`** — subcategory 정의가 case 실태와 불일치하면 수정 제안
4. **`paper/main.tex` 1307-1354 개선안** — Expressibility 분석 포함 L4a~L5b 전체 재작성 제안 (기존 본문에 적용 가능한 형태로)
5. **Cross-cutting insight** — 6개 subcategory를 아우르는 관찰 (예: "L4a의 blocker 다수는 G1+G3 조합이다"). 이는 Introduction의 motivation과 Discussion의 future work 섹션에 들어갈 소재.

---

## 작업 태도

- **실제 코드를 직접 읽고 이해한 뒤** 설명할 것. 기존 `annotation_plans.md`/`limitation_types.md`의 설명을 그대로 복사하지 말 것 (오류 가능성 있음).
- Audit report를 **반드시 참조**하고, 핵심 주장은 report 원문을 발췌해 근거로 사용.
- IntentChecker grammar 제약을 정확히 적용. 특히 "함수 호출 불가", "비트 연산 불가" 등 세부 제약을 놓치지 말 것.
- 분류 체계 자체를 수정할 필요가 있으면 제안할 것 (기존 L4a~L5b가 완벽하다고 가정하지 않음).
- Abstract interpretation 기반 분석임을 기억 (symbolic execution 아님 — "path explosion" 같은 용어 사용 금지).
- 한 번에 한 case씩 깊이 분석. 간단한 한 줄 요약이 아닌 **"리뷰어가 읽어도 버그와 blocker를 이해할 수 있을 만큼"** 상세하게.

---

## 참고: 현재 paper 1307-1342 원문 (개선 대상)

```latex
\item \textbf{L4a (Inexpressible expected value, 10).} The correct expected value depends on a new intermediate computation, an external contract's state, or a function call that does not appear in the program; no intentValue expression can be constructed.

\item \textbf{L4b (No target storage variable, 8).} The buggy function (a view function, a pure function, a thin wrapper, or a library helper) does not modify any storage variable in the target contract, so no @Post annotation has anything to attach to.

\item \textbf{L4c (Magnitude-only difference, 1).} Buggy and correct code change the same state variable in the same direction; only the magnitude differs. changed( ) and Entry op Exit both succeed in both versions.

\item \textbf{L4d (Invariant masked, 1).} A different statement in the same function already modifies the target state variable, so changed( ) is satisfied in both versions. The actual invariant is a multi-variable relation that PostEntryExit cannot express.

\item \textbf{L5a (Bug-awareness-required: missing code, 7).} A required statement is omitted; the post-condition that would catch this is expressible, but knowing what is missing already presupposes knowing the bug.

\item \textbf{L5b (Bug-awareness-required: wrong code, 7).} A required statement uses the wrong identifier, operator, or struct field; the corrective annotation is expressible, but writing it requires knowledge of the correct form.
```

---

## 출력 지침

- 한 번에 하나의 case만 처리. case 사이에 사용자 확인 요청.
- case 분석 결과는 Korean으로 (논문은 영어지만 분석 노트는 한국어가 작업에 편함).
- subcategory summary는 bilingual 가능 (한국어 분석 + 영어 paper 문장 제안).
