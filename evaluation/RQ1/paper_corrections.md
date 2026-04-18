# Paper Corrections & Clarifications

L4/L5 case-by-case 리뷰 과정에서 발견된, `paper/main.tex`·Figure 6 등에 **정정 혹은 명시적 구분**이 필요한 항목을 누적 기록. RQ1·RQ2·Discussion 완성 시 일괄 반영.

---

## C1. Annotation grammar 한계 ≠ Abstract interpretation 엔진 한계

**발견 경로**: Case 1 (`web3bugs_25_H_01`) 분석 중, 저자 피드백으로 확인.

**문제**: 현재 paper가 annotation 언어의 표현력 한계와 AI 엔진의 분석 능력을 **혼재**할 위험. 특히 L4·L5 문장을 읽으면 "IntentChecker는 `**`를 지원하지 않는다"처럼 일반화되어 보일 수 있음.

**실제 구분**:

| 기능 | Abstract interpretation 엔진 | Intent annotation grammar |
|---|---|---|
| `**` (지수) | **지원** (정밀 추상화) | **미지원** |
| 비트 연산 (`<<`, `>>`, `&`, `|`, `^`) | (확인 필요) | 미지원 |
| view/pure 함수 호출 결과 참조 | 분석 가능 (해당 함수 바디 pre-analysis) | `@IReturn`으로 **코드에 존재하는 호출 사이트**의 반환에만 binding |
| 임의의 Solidity 식 | 분석 시에는 코드 내 식 그대로 처리 | `intentValue` = 변수·상수·`[a,b]` interval·`+ - * / %`·괄호만 |
| loop / `**`·`*=` 등 누적 연산 | fixpoint iteration (widening 적용) | 해당 없음 (annotation은 선언적) |

**요지**: annotation 문법은 **AI 엔진이 추상화할 수 있는 것의 엄격한 하위집합**. Annotation이 표현 못한다고 해서 엔진이 분석 못하는 것은 아니며, 그 반대 역시 성립하지 않음.

**Paper 반영 위치**:

1. **Figure 6 (main.tex line 584–620) annotation grammar BNF** — 캡션 또는 서두에 한 문장 추가:
   > *The annotation grammar is intentionally simpler than the underlying abstract domain; operators such as `**` and bitwise operations are precisely supported by the analysis engine but excluded from the annotation surface to keep specifications accessible to developers.*

2. **L4a 본문 (line 1307)** — "function call that does not appear in the program" 서술에서 "`**` 같은 operator"도 같은 문장에 끼워 넣지 말 것. **"annotation 문법 밖 연산자"와 "함수 trace 밖 피연산자"를 두 축으로 분리**. (Case 1의 §6 개선안 참조.)

3. **RQ2 opening (한계 taxonomy 도입부)** — 두 축(engine / annotation)의 독립성을 한 문장으로 선언. 예:
   > *We distinguish two kinds of expressiveness limits: (i) what the abstract interpretation engine can soundly track, and (ii) what the annotation grammar can express as an intent. Most of the unmitigated cases in our study stem from (ii), not (i).*

4. **Discussion / future work** — annotation grammar 확장(제한적 `**`, view 호출 reference)으로 해소 가능한 L4a 하위 패턴이 존재함을 언급. 단, grammar 복잡도↔작성 용이성 tradeoff를 제시.

---

## C2. L4a 정의 재진술 (variable-relational vs function-relational)

**발견 경로**: Case 1·2 공통 본질 추출 중.

**문제**: 현재 L4a 문장 (line 1307) 은 세 가지 원인을 "or"로 나열 — "new intermediate computation, external contract's state, or a function call that does not appear in the program". 나열은 정확하지만 **공통 본질을 놓침**.

**공통 본질 (한 줄)**: Intent annotation은 **함수 trace 상에 실제로 존재하는 값들 사이의 1차 관계**만 표현. L4a는 correctness 조건이 **trace 바깥의 값** (함수가 호출하지 않는 함수의 반환, 혹은 코드가 만들지 않는 중간 계산)을 요구할 때 발생.

**제안 문장 (대체 후보)**:
> **L4a (Inexpressible expected value, N).** The corrective specification references values that the target function's trace does not produce — most commonly, the return of a function the target does not call. Since `intentValue` is a first-order language over variables and call returns already bound by the function (`@IReturn` applies only to call sites present in the code), no annotation can match the correctness condition.

**추가 insight (cross-cutting)**: L4a 내부에도 결이 나뉨 — (a) 호출 grammar만 추가하면 풀리는 케이스 vs (b) 호출 사이트 자체가 부재해 grammar 확장으로도 해소 불가인 케이스 (예: 25_H_05). 이 구분은 Discussion의 "annotation grammar 확장이 어디까지 효과적인가" 논의의 앵커.

---

## C3. L4a 본질의 단순 프레이밍 (type-α/β 구분 폐기)

**발견 경로**: Case 2 (`web3bugs_25_H_05`) 재점검 + 저자 피드백으로 과도한 추상화 제거.

**결정된 프레이밍 (사용할 문장)**:
> 해당 버기 라인의 값이 틀렸음을 개발 시점에 IntentChecker가 알아채려면, 그 값을 **컨트랙트 내 다른 변수와의 관계식**으로 기술할 수 있어야 한다. L4a는 그런 관계식을 만들 수 있는 피연산자가 컨트랙트 전체 scope에 존재하지 않는 경우다.

**폐기된 프레이밍**: "type-α (도메인 포함) / type-β (도메인 disjoint)" 구분. 관찰 자체는 사실이지만 annotation 차단 측면에서는 둘 다 "관계 피연산자 부재"로 수렴하므로, type 구분은 **원인이 아니라 부수 묘사**. Paper에 별도로 소개할 가치 없음. Case 1·2 모두 위 단일 문장으로 충분.

**L4a ↔ L5 경계 관찰 (유지)**: 특정 instance를 고정하면 상수 annotation이 grammar-expressible. 그러나:
- 모든 instance에 단일 annotation → 컨트랙트 밖 값 참조 필요 → **L4a**.
- Instance별 상수 박기 → 표현은 되나 bug-awareness 전제 → **L5a-flavored**.

이 "general vs specific" 분리는 annotation 일반화 능력의 한계를 보여주는 유효한 관찰로 유지. Discussion에 1문단 인용 가치.

**Paper 반영 위치**:

1. **RQ2 L4a 본문 (line 1307)** — 위 단일 문장으로 재진술. C2와 병합 가능.
2. **Discussion** — "general vs specific" 경계 현상 언급. grammar 확장 제안의 효과가 instance-level 재사용성에서는 제한됨을 설명.

---

## C4. L4a vs L5a 엄밀 구분 (landscape deficit vs behavior deficit)

**발견 경로**: Case 2 재점검 시 저자의 "L5a와 뭐가 다른가?" 질문으로 경계 재검증.

**결정 기준 — "전지적 개발자 테스트"**:
> 버그를 정확히 알고 있는 전지적 개발자가 grammar만 가지고 buggy/correct를 구분하는 annotation을 작성할 수 있는가?
> - **가능** → L5a (남은 문제는 "개발자가 버그 인지를 할 수 있는가"뿐)
> - **불가능** → L4a (지식 총량이 annotation 표현력의 한계를 넘어섬)

**본질 구분**:
- **L5a = 행동 결핍 (behavior deficit)**: 컨트랙트의 변수 landscape는 충분. 기존 변수만으로도 grammar-expressible annotation이 buggy/correct를 구분함. 누락된 것은 **statement/call 등 실행 동작** — 그 동작이 들어가면 기존 변수 상태가 바뀌며 기존 annotation이 fire.
- **L4a = 지형 결핍 (landscape deficit)**: 기존 변수 landscape 자체가 부족. 전지적 개발자조차 기존 변수만으로는 distinguishing annotation을 구성할 수 없음. Fix는 landscape 자체를 확장 (새 local·새 intermediate).

**구체 대조**:
- `83_H_01` (L5a): `massUpdatePools()` 호출 누락. `@Post poolInfo[1].accConcurPerShare(Entry != Exit)` 가 기존 변수만으로 작성 가능 + 구분 성공. 작성 결정 = 버그 인지.
- `25_H_05` (L4a): `decimals_ = 18` 하드코딩. `decimals_ == 18`은 동어반복, `decimals_ == 10 + uD`는 `uD` 부재로 표현 불가. 전지적 개발자도 실패.

**Paper 반영 위치**:
1. **RQ2 L4a·L5a 도입부** — 위 "전지적 개발자 테스트"를 두 분류의 판정 기준으로 **명시적으로 선언**. 현재 본문은 차이를 암시할 뿐 공식 기준이 없어 리뷰어 challenge 여지.
2. **L4a 본문 (line 1307)** — "landscape deficit" 프레임으로 재진술 (C2·C3과 병합).
3. **L5a 본문 (line 1325)** — "behavior deficit" 프레임으로 재진술. "bug-awareness-required"는 **증상**이고 **원인은 "기존 landscape로 표현 가능하므로 선택이 필요하다"**는 점 명시.

---

## C5. Grammar-expressible "natural" specification이 buggy 공식과 일치하는 위험 ("silent sanction")

**발견 경로**: Case 3 (`web3bugs_29_H_05`, HybridPool._nonOptimalMintFee) 분석 + 저자의 "correct를 정말 쓸 수 없는가" pressure-test.

**수학적 엄밀화**:
- Annotation grammar의 표현 범위 = scope 변수들에 대한 **rational-polynomial 함수** (+, −, ×, /, % 및 상수).
- Correct specification이 요구하는 값(D = stableswap invariant)은 3차 방정식의 해 — **rational-polynomial이 아님**. Cardano 공식 적용 시 세제곱근 등장, grammar가 허용하지 않는 연산.
- 따라서 `A`, `_reserve0`, `_reserve1` 모두 scope 안에 있음에도 **이들의 어떤 rational-polynomial 조합도 D와 같아지지 않음**. 재료 부족이 아니라 **허용 연산의 닫힘 범위 문제** (자·컴퍼스로 각의 삼등분 불가와 같은 구조).

**실용적 위험 (silent sanction)**:
- Grammar는 buggy 공식(`_amount_j × _reserveᵢ / _reserveⱼ`)을 **허용**하고, correct 공식(D 기반)을 **배제함**.
- 개발자가 "imbalance"를 rational-polynomial로 자연스럽게 표현하려 할 때 가장 그럴듯한 선택이 하필 **buggy 공식 자체**.
- 결과: 선의의 developer가 작성한 annotation이 buggy 코드를 tautologically validate → **IntentChecker가 버그를 sanction하는 꼴**.
- 단순 "표현 불가(fail-silent-by-omission)"를 넘어 "잘못된 답을 인증(fail-by-confirmation)"하는 더 심각한 failure mode.

**Paper 인용 가치**:
- L4a 내부에 존재하는 **두 개의 서로 다른 failure mode**를 구분:
  - Mode-1 (일반 L4a): annotation 작성 자체가 막힘 → 아예 아무 판정도 안 나옴 (fail-silent).
  - Mode-2 (silent sanction): annotation이 작성 가능하지만 그것이 정확히 buggy와 일치 → buggy 코드가 Satisfied로 통과 (fail-by-confirmation). 개발자 입장에서 더 위험.
- 단순 grammar 확장(예: `**` 허용)이 Mode-2를 해소하지 못함 — 수학적으로 rational-polynomial 확장을 얼마나 해도 Cardano 연산은 포함 불가.

**Paper 인용 가치**:
- 단순 "L4a는 표현 불가"보다 강한 메시지: **grammar가 잘못된 답을 silently sanction한다**.
- 단순 grammar 확장의 위험성 경고 — 연산 한 가지(`**` 등) 추가가 해소하지 못하는 구조적 한계.

**제안 paper 문장** (Discussion 혹은 L4a 본문 말미):
> *A particularly treacherous subset of L4a cases arises when the grammar's algebraic range coincides with the buggy code's formula. Here, the most specific annotation a diligent developer can write is tautologically satisfied by the buggy implementation; the specification language silently sanctions the incorrect behavior. This failure mode motivates admitting limited non-algebraic constructs (e.g., references to internal function results) into the intent grammar — a direction we leave to future work.*

---

## C6. "Auxiliary local 주입" 경유 L4a → L5 전이 (workflow 축)

**발견 경로**: Case 3 분석 중, 개발자가 `uint256 D0 = _computeLiquidity(...);`를 production 코드에 삽입하면 annotation이 가능해지는 경로를 검토. Case 2 (`uint8 uD = IERC20(...).decimals()`)에도 같은 경로 성립.

**관찰**: L4a case 다수는 아래 경로로 detectability 획득 가능:
1. 개발자가 **production code에 auxiliary local 변수**를 주입 — annotation만을 위한 side-effect-free 계산 (기존 internal/interface view 호출 결과를 local로 받음).
2. 해당 local이 landscape에 편입되므로 annotation이 grammar-expressible하게 됨.
3. 주입 결정은 "이 값이 correctness에 중요하다"는 판단 → **버그 인지 전제**.

**결과**: 해당 case는 L4a → L5 영역으로 이동.

**즉, L4a/L5 경계는 workflow 가정에 따라 투과적**:
- Pure annotation-only workflow에서는 L4a로 고정.
- Annotation-motivated code modification을 허용하면 L4a 다수가 L5로 재분류됨.

**주의**: 이 관찰은 "세 case의 primary blocker가 같다"는 *통일 주장이 아님* — Case 2(axis β, 관계 맺을 변수 부재)와 Case 1·3(axis α, 관계에 함수 포함)은 여전히 별개의 blocker. 다만 "auxiliary local 주입"이라는 workflow 장치가 **두 축 모두**에 공통으로 적용될 수 있다는 별개의 실용적 관찰.

**Paper 함의**:
- L4a·L5 분류는 **작업 환경 가정**에 따라 해석이 달라진다는 점 명시 필요.
- "IntentChecker가 annotation과 함께 auxiliary local 주입을 유도하는" workflow가 future work 후보 — grammar 확장보다 실용적 대안일 수 있음.

**제안 paper 문장** (Discussion):
> *The boundary between L4a and L5 is permeable under a practical observation: many L4a cases become annotatable if the developer injects side-effect-free auxiliary computations into the production code purely to enable specification. Such injection requires the very bug awareness that L5 presupposes, but it suggests a workflow in which IntentChecker nudges developers toward exposing correctness-critical intermediates rather than merely extending the annotation grammar.*

---

## C7. (추가 예정)

이후 case 분석에서 paper 보완이 필요한 사항 누적 기록.

---
