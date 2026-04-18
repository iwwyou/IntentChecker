# L4/L5 Case-by-Case Deep Review

**대상**: 34개 not_detectable cases (L4a 10, L4b 8, L4c 1, L4d 1, L5a 7, L5b 7)
**목적**: 각 case의 audit report + source code를 바탕으로 분류 타당성·근본 원인 재검토, paper (Introduction / RQ2 / Discussion) 반영용 insight 도출.

---

# Paper-Ready Insights (누적)

아래는 case 분석에서 추출된 **교차 관찰** — 논문 본문(RQ1 / RQ2 / Discussion)에 바로 인용·편집 가능한 형태. Case별 상세는 하위 섹션 참조.

## I1. Annotation grammar ≠ Abstract interpretation 엔진

**관찰** (Case 1 유래): IntentChecker에는 두 개의 분리된 언어 계층이 있고 paper 본문에서 혼동될 위험이 있음:

- **분석 엔진 (abstract interpretation)**: `**`, 비트 연산, 루프, external view 호출 등 풍부한 Solidity 연산을 soundly 추상화 가능.
- **Intent annotation grammar**: 변수·정수 리터럴·interval `[a,b]`·`+ − × / %`·괄호만 허용 — 엔진이 다룰 수 있는 것의 **엄격한 하위집합**.
- **Debug annotations** (`@StateVar`, `@LocalVar`, `@IReturn` 등): **분석 엔진을 위한** 값 공급 장치. Intent annotation grammar를 확장하는 수단이 아님. 두 layer는 설계상 독립.

**Paper 반영**:
- Figure 6 (grammar BNF) 캡션에 한 문장 — annotation grammar의 단순성이 의도된 design choice이며 엔진 제약이 아님을 명시.
- RQ2 opening — 두 axis(engine expressiveness / annotation expressiveness) 분리 선언.
- L4a·L5 본문에서 "IntentChecker가 `**`를 지원 안 함" 같은 표현 금지 — "annotation grammar가 `**`를 포함하지 않음"으로 정확히 표기.

## I2. L4a / L5a 판정 기준 — "전지적 개발자 테스트"

**판정 기준** (Case 2 유래):
> 버그를 정확히 알고 있는 개발자가 grammar만 가지고 buggy/correct를 구분하는 annotation을 작성할 수 있는가?
> - **가능** → **L5a** (*behavior deficit*): annotation 표현 가능, "어떤 annotation을 쓸지" 결정이 버그 인지 전제.
> - **불가능** → **L4a** (*expressibility deficit*): 전지적 개발자조차 grammar로 distinguishing annotation 작성 불가.

**Paper 반영**:
- L4a·L5a 도입부에 위 기준을 공식 판정 룰로 선언.
- L5a 본문에서 "bug-awareness required"는 **증상**이고 **원인은 "annotation 공간이 충분히 풍부해 선택이 의미를 갖는다"**는 점 명시.

## I3. L4a 내부 primary blocker — 두 갈래

**두 축** (Case 1·2·3 유래):

- **(α) 변수-관계에 함수 호출이 포함 (Case 1, Case 3 유형)**: scope에는 correct 관계식에 기여하는 변수들이 있으나, 관계 자체가 **함수 호출 결과**(external interface view 또는 internal view)를 피연산자로 요구. intentValue는 변수·상수만 허용하므로 함수가 관계 안에 들어갈 수 없음.
- **(β) 관계 맺을 변수 자체 부재 (Case 2 유형)**: correct RHS가 가리키는 도메인(예: underlying token decimals)에 대한 **proxy 변수가 scope·컨트랙트 어디에도 없음**. RHS가 scope 변수의 기여 없이 "literal + 외부 값"으로만 구성.

**공통**: 두 축 모두 pure annotation-only workflow에서 작성 실패.

**Paper 반영**:
- L4a 본문(line 1307) 재서술에서 두 축을 구분 언급.
- Discussion에서 grammar 확장 효과는 축에 따라 다름 — (α)는 제한적 함수 reference 허용으로 해소 여지, (β)는 코드 수정이 필요.

## I4. L4a / L5 경계의 투과성 — auxiliary local 주입

**관찰** (Case 2·3 유래): 개발자가 **side-effect-free auxiliary local**을 production code에 주입하면 (e.g., `uint256 D0 = _computeLiquidity(...)` 혹은 `uint8 uD = IERC20(...).decimals()`), scope landscape가 확장되어 annotation이 grammar-expressible해짐. 그러나 주입 결정 자체가 "이 값이 correctness에 중요하다"는 판단 → 버그 인지 전제 → **L5 영역으로 이동**.

**함의**: L4a / L5 경계는 **pure annotation-only workflow** 전제 하에서만 고정. "annotation-driven refactor" (annotation 작성 위해 auxiliary 변수 도입 허용) 환경에서는 L4a 다수가 L5로 재분류됨.

**Paper 반영**:
- Discussion/future work에서 "annotation-driven refactor" 워크플로우를 대안으로 제시 — grammar 확장보다 실용적일 수 있음.

## I5. "Silent sanction" 위험 — L4a 내 fail-by-confirmation mode

**관찰** (Case 3 유래): Grammar가 허용하는 "가장 경제적으로 그럴듯한" rational-polynomial specification이 하필 **buggy 공식 자체와 일치**하는 경우. 개발자가 선의로 작성한 annotation이 buggy 코드를 tautologically validation → IntentChecker가 버그를 "올바르다"고 재확인.

**두 failure mode**:
- **Mode-1 (fail-silent-by-omission)**: annotation 작성 시도 자체가 실패 → 아예 판정이 안 나옴.
- **Mode-2 (fail-by-confirmation, silent sanction)**: annotation이 grammar-expressible하고 buggy에서 Satisfied → 버그가 통과.

**Paper 인용 가치**:
- 단순 grammar 확장이 Mode-2를 해소하지 못함 — 수학적으로 rational-polynomial 범위를 아무리 확장해도 Cardano 연산·iterative solution은 포함 불가.
- L4a를 "inexpressibility" 단일 메시지로 요약하면 Mode-2 위험을 숨김. Discussion에서 별도 언급 권장.

## I6. L4a 경계 관찰 — general form vs specific form

**관찰** (Case 2 유래): L4a case의 correctness 조건이 "parameter에 따라 달라지는 값"일 때, **특정 instance 고정** 시 상수 annotation은 grammar-expressible. 하지만:
- 모든 instance에 적용되는 단일 annotation → 외부 값 참조 필요 → **L4a**.
- Instance별 상수 박기 → 표현 가능하되 상수 = 정답 지식 → **L5a-flavored** (bug-awareness).

**함의**: "일반화된 intent annotation"의 표현력과 "특정 사례용 intent annotation"의 표현력이 구분되어야 하며, annotation 재사용성이 structural 한계의 다른 축을 드러냄.

---

Grammar 제약 빠른 참고:
- **intentValue**: 변수(member/index access 포함) · 정수 리터럴 · `[a,b]` · `+ - * / %` · 괄호.
- **불가**: 함수 호출, 비트 연산(`<<`, `>>`, `&`, `|`, `^`), 지수(`**`), 사용자 정의 호출, scope 밖 변수.
- **Debug annotations**: `@IReturn`은 view/pure interface 호출에만. Intent grammar와 독립 (I1 참조).

근본 원인 G-카테고리:
- **G1** grammar 내 함수 호출 부재
- **G2** grammar 내 비트·지수 연산 부재
- **G3** intermediate variable 코드에 없고 grammar로 도출 불가
- **G4** 상태 변경 자체 없음 (view/pure, library, 외부 위임)
- **G5** buggy/correct 질적 동일 · 양적 차이 (`changed`/entry-exit 구분 불가)
- **G6** 다중 변수 invariant (곱 보존 등) PostEntryExit 표현 불가
- **G7** 버그 인지 전제 (정답 annotation = fix 지식)
- **G8** 외부 contract state 의존 (`@IReturn` 허용 범위 밖)
- **G9** 기타

---

## L4a — Inexpressible Expected Value (10 cases)

---

### Case 1 — `web3bugs_25_H_01` (현재 분류: **L4a**)

#### 1. Audit report 인용

- **출처**: `reports/25.md` → `[H-01] CompositeMultiOracle returns wrong decimals for prices?`
- **Severity**: High. **Warden**: cmichel (C4 2021-08-yield micro)
- **핵심 주장 (원문 발췌)**:

  > The `CompositeMultiOracle.peek/get` functions seem to return wrong prices. A single price is computed as:
  > ```
  > (priceOut,_) = IOracle(source.source).peek(base, quote, 10 ** source.decimals);
  > priceOut = priceIn * priceOut / (10 ** source.decimals);
  > ```
  > Assume all oracles use 18 decimals and `source.decimals` refers to the token decimals of `source.source`. Going from USDC → DAI → USDT (`path = [DAI]`) starts with price `1e18`:
  > - `_peek(USDC, DAI, 1e18)`: `priceOut = 1e18 * 1e18 / 1e6 = 1e30`
  > - `_peek(DAI, USDT, 1e30)`: `priceOut = 1e30 * 1e18 / 1e18 = 1e30`
  >
  > Final `value = 1e30 * 1e6 / 1e18 = 1e18` = 10^12 USDT. Inflates USDT by 10^12.
  >
  > The issue is that `peek` assumes the final price is in 18 decimals (`value = price * amount / 1e18`) but `_peek`/`_get` don't enforce this.

- **권고된 수정안**:
  ```solidity
  priceOut = priceIn * priceOut / (10 ** IOracle(source.source).decimals());
  ```
  — 분모를 "오라클 자신이 말하는 출력 precision"으로. Sponsor(alcueca)는 이후 "모든 하위 oracle이 18 decimals를 갖도록 강제"하는 invariant로 patch.

#### 2. 코드 의미 이해

##### (2a) Contract 목적 & 시스템 위치

`CompositeMultiOracle` — Yield Protocol v2의 **가격 집계기(price aggregator)**. 직접 pair가 없는 A→B 가격을 구할 때 `paths[A][B] = [X₁, X₂, …]` 경유점으로 여러 하위 `IOracle`을 **곱셈 체이닝**하여 합성 환율을 얻음. Yield의 vault 담보 평가·liquidation·CR(collateralization ratio) 계산의 **가격 진실 공급원**.

##### (2b) 함수의 컨트랙트 내 역할

두 private helper:
- `_peek(base, quote, priceIn, updateTimeIn) → (priceOut, updateTimeOut)` (line 110–118, view)
- `_get(...)` (line 120–128, `_peek`의 mirror — `.peek` 대신 `.get`)

공개 `peek`/`get` (line 74–108)가 path를 순회하며 각 홉마다 이 helper를 호출. 즉 **체이닝의 단일 단계**를 curried multiplier로 수행.

**`base`/`quote` 용어가 두 층위에서 재사용됨에 주의** (이 case 이해의 핵심):
- **공개 `peek(base, quote, amount)` 관점**: `base` = 변환 출발 토큰(A), `quote` = 변환 도착 토큰(B). 사용자 관점의 최종 "A→B".
- **내부 `_peek(base, quote, …)` 관점**: 한 홉만 처리. `base`는 "이번 홉의 출발", `quote`는 "이번 홉의 도착". path 순회 중 **이전 홉의 도착이 다음 홉의 base로 바뀜** (line 84 `base_ = path[p]`). `base_`가 경로 위를 전진하는 포인터 역할.

##### (2c) 함수 의도 (수식 + 스케일 규약)

내부 환율 표현 규약: **`price`는 언제나 "rate × 10^18" 형태의 18-decimal fixed-point 누적 환율**.
- 시작값 `price = 1e18` (= rate 1.0, 아무 홉도 거치지 않음).
- 각 홉이 하는 일: "이번 홉의 raw 환율을 누적가에 곱하고 다시 18-dp로 정규화".

수식:
```
priceOut = priceIn    ×    raw_price_from_oracle    /   10^(output_scale)
           ^^^^^^^^        ^^^^^^^^^^^^^^^^^^^^^         ^^^^^^^^^^^^^^^^
           누적 환율(18dp)  이번 홉 환율(scale-dp)        정규화 divisor
```

**"priceIn을 곱한다" 직관**: rate composition. `USDC→USDT = USDC→DAI × DAI→USDT`. 각 홉은 자기 몫만 제공, 누적은 곱셈.

**"18 decimals로 정렬한다" 직관**: 오라클이 `10^scale`로 부풀린 숫자를 돌려주므로, 같은 크기로 나눠 다시 "순수 rate × 10^18"로 되돌림. 그래야 다음 홉 곱셈 때 스케일이 누적 오염되지 않음.

**Invariant (peek 계약)**: `peek(base, quote, amount) = value` ⇒ "`amount` 단위의 base 토큰은 현재 환율 기준 `value` 단위의 quote 토큰과 경제적으로 동등". `amount`·`value` 모두 각 토큰의 native integer representation (1 USDC = `1e6`, 1 DAI = `1e18`).

##### (2d) Line-by-line 분석 (`_peek` line 110–118)

```solidity
113  Source memory source = sources[base][quote];
114  require (source.source != address(0), "Source not found");
115  (priceOut, updateTimeOut) = IOracle(source.source).peek(base, quote, 10 ** source.decimals);
116  priceOut = priceIn * priceOut / (10 ** source.decimals);   // BUG
117  updateTimeOut = (updateTimeOut < updateTimeIn) ? updateTimeOut : updateTimeIn;
```

- **L113**: `sources[base][quote]` 조회 — `Source { address source; uint8 decimals; }`. `decimals`는 `_setSource`(line 131)에서 `IOracle(source).decimals()`를 snapshot — **의도상 하위 오라클의 출력 정밀도**.
- **L114**: source 미설정 시 revert.
- **L115**: 하위 오라클에게 "`10^source.decimals` 단위 base"의 quote 환산가를 요청 → `priceOut = raw_oracle_price`. 코멘트 "Get price for one unit"는 `source.decimals`를 **token decimals**로 전제한 표현 (cmichel 해석 지점).
- **L116 (BUG)**: `priceIn * priceOut / 10^source.decimals`. 분모의 의미론적 역할은 "오라클 출력 precision 제거"여야 하나, 변수 이름(`source.decimals`)이 모호. 실제 구현에서는 `_setSource`가 `IOracle.decimals()` 값을 넣어 수치적으로는 맞지만, **코드가 자기 의도를 표현하지 않아** 취약.
- **L117**: freshness 전파 (가장 오래된 updateTime 보존).

##### (2e) 버그의 근본 의미 (예시 포함)

**예시 A — 정상 동작** (`source.decimals == 18`, 모든 환율 1.0):

| hop | `priceIn` | sub raw | 계산 | `priceOut` |
|---|---|---|---|---|
| USDC→DAI | `1e18` | `1e18` | `1e18*1e18/1e18` | `1e18` ✅ |
| DAI→USDT | `1e18` | `1e18` | `1e18*1e18/1e18` | `1e18` ✅ |

최종: `value = 1e18 * 1e6 / 1e18 = 1e6` → 1 USDT. 정확.

**예시 B — cmichel 해석 (버그 시나리오)**: USDC source의 `source.decimals = 6` (토큰 decimals). 오라클 실제 출력은 여전히 18-dp.

| hop | `priceIn` | sub call | raw | 잘못된 나눗셈 | `priceOut` |
|---|---|---|---|---|---|
| USDC→DAI | `1e18` | peek(...,10^6) | `1e18` | `1e18*1e18/1e6` | **`1e30`** ❌ |
| DAI→USDT | `1e30` | peek(...,10^18) | `1e18` | `1e30*1e18/1e18` | `1e30` |

최종: `value = 1e30 * 1e6 / 1e18 = 1e18` → USDT 관점 `1e18/1e6 = 10^12` USDT. 1 USDC가 1조 USDT로 평가됨.

오류 지점: **첫 홉의 `/1e6`**. 오라클이 18-dp로 돌려준 숫자를 6-dp로 나눠 `10^12` 배율이 누적가에 주입, 마지막까지 남음.

**Protocol-level 결과**: Yield vault가 담보 평가 시 `value`를 담보 수량으로 사용 → 평가액이 `10^k` 배 부풀거나 축소 → 무담보 대출 혹은 정상 포지션의 즉시 liquidation → 양방향 자산 손실.

##### (2f) 올바른 fix

```solidity
priceOut = priceIn * priceOut / (10 ** IOracle(source.source).decimals());
```
분모를 "저장된 숫자 `source.decimals`"가 아니라 "지금 이 순간 하위 오라클이 말하는 자기 decimals"로. 변수명의 모호성과 무관하게 수학적으로 정확.

#### 3. IntentChecker annotation 시도

**(a) state variable 변화?** 없음. `_peek`는 view, `_get`도 storage write 없음. Post `changed`/entry-exit 대상 부재.

**(b) 올바른 반환값을 arithExpr로?**
```
@Post returnExpression == priceIn * priceOut_raw / (10 ^ IOracle(source.source).decimals())
```
- `10 ** x` / `10 ^ x` → **G2** (지수 부재).
- `IOracle(source.source).decimals()` → **G1** (함수 호출 부재). `@IReturn`으로 view call 공급을 시도해도 결과를 `**`와 함께 쓸 방법이 없음.
- 하위 raw `priceOut`은 `@IReturn`으로 공급 가능하지만 `10^decimals` 나눗셈 표현 자체가 막힘.
- 우회로 `1e18` 하드코딩 → 코드에 없는 invariant를 annotation이 선행 주장하는 꼴, 의미 왜곡.

**(c) 버그 인지 전제?** 표현 불가 단계에서 막힘 → L5 후보 아님.

**예측**: 어떤 형식이어도 파싱/표현 불가 → buggy/correct 양쪽 판정 없음.

#### 4. 분류 타당성

- 현재: **L4a**. ✅ 유지.
- blocker 본질: 올바른 분모가 `10^IOracle(...).decimals()` — **지수 + 함수 호출** 조합에 의존. 새 중간값이 target 함수 scope 밖 (`_setSource`에만 있음).
- `annotation_plans.md` line 360의 "Interface call은 이제 지원되어 ... TOP이 아님" 설명은 맞지만 **진짜 blocker인 G1/G2/G3**를 가리는 면이 있음 → 보강 필요.

#### 5. 근본 원인

**본질 (impedance mismatch)**: IntentChecker의 intent annotation은 **함수 trace 상에 실제로 존재하는 값들 사이의 1차 관계**를 표현하는 변수-관계 언어. 즉 허용되는 피연산자는 (i) 함수 local/parameter/storage 변수, (ii) 정수 리터럴, (iii) `@IReturn`으로 label된 **코드에 이미 있는 호출**의 반환. 반면 이 버그의 correctness 조건은 `IOracle(source.source).decimals()` — **함수가 호출하지 않는 함수**의 반환값 — 에 대한 관계. 즉 "annotation이 말할 수 있는 세계"와 "correctness가 요구하는 세계"가 단절. 아래 G-카테고리는 모두 이 한 mismatch의 표면 증상.

- **G1 (문법적 표면)** — annotation 문법에 함수 호출 자리가 없음. `IOracle(...).decimals()`를 intentValue에 쓸 수 없다는 직접적 제약.
- **G3 (의미론적 표면)** — 설령 grammar가 허용해도 `.decimals()` 호출 사이트가 `_peek`/`_get` 본문에 없어 `@IReturn`으로의 우회 불가. `_setSource`에만 존재하므로 target 함수 trace 바깥.
- **G2 (보조, annotation-only)** — annotation 문법이 `**`를 포함하지 않아 `10 ** x` 형태 표현 불가. ※ **단, 이 한계는 annotation 언어에 국한됨** — abstract interpretation 엔진은 `**`를 지원하므로 **buggy 런타임의 `10 ** source.decimals` 계산은 정밀하게 추상화됨** (TOP 아님). 따라서 G2는 "분석 불가"의 표면이 아니라 "정답 표현 불가"의 표면. (별도 paper correction 필요 — `paper_corrections.md` 참조.)
- **G4 (augmenting)** — view/effectively-view 함수라 post-state 채널도 닫힘 → G1/G3가 유일 채널이면서 막힘.

#### 6. paper 문장 개선 제안

현재 (main.tex line 1307):
> **L4a (Inexpressible expected value, 10).** The correct expected value depends on a new intermediate computation, an external contract's state, or a function call that does not appear in the program; no intentValue expression can be constructed.

개선안 (impedance mismatch로 상위 명제화):
> **L4a (Inexpressible expected value, 10).** The corrective specification references values that the target function's trace does not produce — most commonly, the return of a function the target does not call. Since `intentValue` is a first-order language over variables and call returns already bound in the function (`@IReturn` applies only to call sites already present in the code), no expression matches the correctness condition.

(Annotation 문법이 `**`를 포함하지 않는 별개의 한계는 본문 표현력 논의에서 분리해 기술 — 아래 Case 1 에서 제안.)

---

### Case 2 — `web3bugs_25_H_05` (현재 분류: **L4a**)

#### 1. Audit report 인용

- **출처**: `reports/25.md` → `[H-05] Exchange rates from Compound are assumed with 18 decimals`
- **Severity**: High. **Warden**: shw.
- **핵심 주장 (원문 발췌)**:
  > `CTokenMultiOracle` assumes the exchange rates of Compound always have 18 decimals. According to the Compound documentation, the exchange rate returned from `exchangeRateCurrent`/`exchangeRateStored` is scaled by `1 * 10^(18 - 8 + Underlying Token Decimals)`. Using a wrong decimal number on the exchange rate could cause incorrect pricing on tokens. See `CTokenMultiOracle.sol#L110`.
- **권고된 수정안**: "get the decimals of the underlying tokens to set the correct decimal of a Source."
- **Sponsor**: confirmed and patched (`e9c1ee5532...`).

#### 2. 코드 의미 이해

##### (2a) Contract 목적 & 시스템 위치

`CTokenMultiOracle` — Compound cToken과 그 underlying ERC20 간 환율을 Yield 시스템 내부 표현(18-dp)으로 노출하는 **어댑터 oracle**. e.g. cDAI ↔ DAI, cUSDC ↔ USDC. `CompositeMultiOracle`(case 1)이 path 구성 시 하위 `IOracle` 중 하나로 이 어댑터를 지목할 수 있으므로, **cToken 기반 Yield vault의 담보 평가 전 구간**에 영향.

Compound의 `exchangeRate`는 "1 cToken이 얼마만큼의 underlying을 대표하는가"를 나타내는 raw 숫자로, Compound는 이를 **`10^(18 - 8 + uD)` 스케일** (여기서 `uD` = underlying 토큰 decimals)로 리턴. cToken 자체 decimals는 8 고정. 예: cDAI (uD=18) → 스케일 `10^28`, cUSDC (uD=6) → 스케일 `10^16`.

Yield 내부 규약: 모든 오라클의 출력은 18-dp (`decimals = 18` public constant, line 14).

##### (2b) 함수의 컨트랙트 내 역할

- `_setSource(cTokenId, underlying, source)` (line 109–124, internal): `sources[cTokenId][underlying]`와 `sources[underlying][cTokenId]` 양방향 엔트리 설정. 후자는 `inverse = true`.
- 이 함수가 저장하는 `decimals` 값이 이후 모든 `_peek`/`_get` 호출의 **가격 스케일 정규화 파라미터**가 됨.

L110 `uint8 decimals_ = 18;` — 이 한 줄이 버그.

##### (2c) 함수 의도 (수식)

`_peek`/`_get` 내부 정규화 (line 82–86):
```solidity
if (source.inverse)  price = 10 ** (source.decimals + 18) / rawPrice;   // underlying → cToken
else                 price = rawPrice * 10 ** (18 - source.decimals);   // cToken → underlying
```
여기서 `source.decimals`의 의미론적 역할 = **"rawPrice가 들고 있는 scale"** = `10 + uD` (= 18 - 8 + uD).

그러므로 `_setSource` 의도:
```
decimals_ = 10 + IERC20(CTokenInterface(source).underlying()).decimals()
```
예: cDAI → `decimals_ = 28`, cUSDC → `decimals_ = 16`.

##### (2d) Line-by-line 분석 (`_setSource` line 109–124)

```solidity
109  function _setSource(bytes6 cTokenId, bytes6 underlying, address source) internal {
110      uint8 decimals_ = 18; // Does the borrowing rate have 18 decimals?   // BUG
111      require (decimals_ <= 18, "Unsupported decimals");
112      sources[cTokenId][underlying] = Source({
113          source: source,
114          decimals: decimals_,
115          inverse: false
116      });
117      sources[underlying][cTokenId] = Source({
118          source: source,
119          decimals: decimals_,
120          inverse: true
121      });
122      emit SourceSet(cTokenId, underlying, source);
123      emit SourceSet(underlying, cTokenId, source);
124      // }
```

- **L110 (BUG)**: `decimals_`를 하드코딩 `18`. 주석 `// Does the borrowing rate have 18 decimals?`는 개발자도 확신이 없었음을 드러냄 — 결국 틀린 가정을 코드로 박음.
- **L111**: tautology (`18 <= 18`). 실제 underlying decimals를 조회했다면 이 guard가 의미를 가졌을 것.
- **L112–116**: 정방향 엔트리 저장. `decimals = 18`이 `_peek` 분기의 `18 - 18 = 0` 지수로 흘러감 → `price = rawPrice * 10^0 = rawPrice`. Underlying이 DAI면 `rawPrice`는 `10^28` 스케일인데 18-dp 규약을 주장하는 price로 그대로 노출 → **10^10 배 부풀림**.
- **L117–121**: 역방향 엔트리 (inverse). 동일 `decimals = 18`로 저장 → `_peek`의 inverse 분기 `10^(18+18) / rawPrice = 10^36 / rawPrice`. Underlying이 DAI면 `10^36 / 10^28 = 10^8`대 값이 나오는데, 18-dp price 규약 위배.
- **L122–123**: 양방향 이벤트.

##### (2e) 버그의 근본 의미

`_setSource`에 "underlying의 decimals를 조회하라"는 명령이 없어, 저장된 `source.decimals = 18`이 이후 모든 환율 계산에서 **잘못된 정규화 지수**로 사용. `_peek`/`_get`의 수식은 대수적으로 맞지만, 입력 파라미터 `source.decimals`가 틀려 체계적 스케일 오차.

Protocol-level: case 1과 같은 경로 — Yield vault가 이 오라클 결과를 담보 평가에 사용 → cUSDC 담보가 10^2배 축소 평가되어 즉시 liquidation, 또는 cDAI 담보가 10^10배 부풀어 무담보 대출. **체계적 편향** (버그 방향이 underlying 토큰마다 다름)이라 공격자가 유리한 방향을 선택 가능.

##### (2f) 올바른 fix

Audit 권고를 구현 수준으로:
```solidity
uint8 uD = IERC20(CTokenInterface(source).underlying()).decimals();
uint8 decimals_ = uint8(10 + uD);
require(decimals_ <= 36, "Unsupported decimals");   // _peek inverse branch overflow 방지
```
Sponsor는 이 방향으로 commit `e9c1ee5532...`에 patch.

#### 3. IntentChecker annotation 시도

**(a) state variable 변화?** — `sources[...][...]`에 write 있음 (L112, L117). `changed(sources[cTokenId][underlying], true)`는 buggy/correct 모두 satisfied (둘 다 쓴다, 값만 다름). → 질적 구분 불가.

**(b) 올바른 값의 산술 표현?** — 이상적 annotation:
```
@Post sources[cTokenId][underlying].decimals == 10 + IERC20(CTokenInterface(source).underlying()).decimals()
```
- `IERC20(...).decimals()`, `CTokenInterface(source).underlying()` → **G1** (함수 호출). 둘 다 view라 `@IReturn` 이론적 허용 대상이지만:
  - `_setSource` 본문에 해당 호출 사이트 **없음** (underlying이나 decimals를 가져오지 않음).
  - `@IReturn`은 코드에 존재하는 call expression에만 값 공급. 존재하지 않는 호출을 annotation으로 "가상 주입" 불가.
- 숫자만 두고 본다면 `10 + <token decimals>`는 단순 `+`이므로 grammar 허용. 그러나 `<token decimals>`에 해당하는 변수가 함수 scope·상속 scope 어디에도 없음 → **G3**.
- 우회: `@LocalVar`로 `decimals_` 값 자체를 넣어도 이는 **입력을 buggy 값 `18`로 정답 선언**하는 꼴. Value condition 불가.

**(c) 버그 인지 전제?** 여기 도달하지 못함.

**예측**: annotation 작성 단계에서 표현 실패 → 양쪽 판정 없음.

#### 4. 분류 타당성

- 현재: **L4a**. ✅ 유지.
- blocker: 올바른 값이 "코드에 존재하지 않는 두 view 호출의 반환에 의존". 심지어 hop별 계산 결과가 아닌 **저장되는 파라미터 자체의 값**이 틀려 모든 downstream 계산에 파급.
- `annotation_plans.md` line 2006–2012 설명은 정확. 다만 "새로운 중간 계산 필요"가 G1+G3 조합임을 명시하면 더 날카로움.

#### 5. 근본 원인

**본질 (한 줄)**: L110의 `decimals_ = 18`이 틀렸음을 IntentChecker가 알아채려면, buggy/correct를 구분하는 grammar-expressible annotation을 **기존 `CTokenMultiOracle` 변수 landscape 만으로** 구성할 수 있어야 함. 그런데 **전지적 개발자조차 그런 annotation을 작성할 수 없음** — 관계식의 피연산자가 컨트랙트 어디에도 없기 때문. (이 점이 L5a "missing-code"와의 결정적 차이: L5a는 landscape는 충분하되 "어떤 annotation을 쓸지" 결정이 버그 인지 전제 — 이 case는 landscape 자체가 부족.)

**변수 현황 검증** — L110 시점에 참조 가능한 식별자와 `decimals_`와의 관계 가능성:

| 식별자 | 타입 | `decimals_`와의 관계 |
|---|---|---|
| `decimals` (contract constant) | `uint8` = 18 | `decimals_ == decimals` → 동어반복 (18 == 18). buggy/correct 구분 불가 |
| `cTokenId`, `underlying` | `bytes6` | 타입 mismatch — 수치 산술 불가 |
| `source` | `address` | 타입 mismatch |
| `sources[...][...]` | struct mapping | L110 시점엔 미기입, 이후 `decimals_` 자체로 채워짐 |

→ 올바른 값 `10 + uD`의 피연산자 `uD` (underlying decimals)에 **상응하는 변수가 컨트랙트 어디에도 없음**. 값을 얻으려면 `CTokenInterface(source).underlying()` 후 `IERC20(...).decimals()` 두 번의 외부 호출이 필요하고, 두 호출 모두 이 함수(`_setSource`)에 쓰이지 않음.

G-표면:
- **G1** — `CTokenInterface(...).underlying()`·`IERC20(...).decimals()`를 intentValue에 쓸 수 없음.
- **G3** — 위 호출들의 반환을 담는 변수 부재 + **호출 사이트 자체 부재** → `@IReturn` 우회도 불가.
- **G2 해당 없음** — 필요한 산술은 `10 + x`. grammar 허용 연산만. 문제는 오로지 `x`를 얻을 수 없다는 것.

**Case 1 대비 부수 관찰**: Case 1의 `_peek`은 `10 ** source.decimals`로 decimals 수치 도메인을 한 번은 통과. Case 2의 `_setSource`는 decimals 도메인에 전혀 진입하지 않음 — `18` 은 흔적이 아니라 fabrication. 런타임 trace의 깊이는 다르나, **annotation 차단 측면에서는 둘 다 "관계 피연산자가 컨트랙트에 없다"로 수렴**.

**L4a ↔ L5 경계 관찰** — 특정 cToken-underlying pair를 고정하면 상수 annotation (`sources[cDAI][DAI].decimals == 28`)은 grammar-expressible. 하지만:
- 모든 pair에 단일 annotation을 달려면 uD 참조 필요 → uD는 컨트랙트 밖 → **L4a**.
- Pair별 상수 박기는 표현 가능하나 상수 = 정답 지식 → **L5a-flavored** (bug-awareness).

이 "general form ↔ specific form" 분리는 L4a와 L5의 경계 현상으로 paper에 인용 가치.

---

### Case 3 — `web3bugs_29_H_05` (현재 분류: **L4a**)

#### 1. Audit report 인용

- **출처**: `reports/29.md` → `[H-05] hybrid pool uses wrong non_optimal_mint_fee`
- **Severity**: High. **Warden**: broccoli (C4 2021-09-sushitrident).
- **핵심 주장 (원문 발췌)**:
  > When an LP provider deposits an imbalanced amount of tokens, a swap fee is applied. `HybridPool` uses the same `_nonOptimalMintFee` as `constantProductPool`; however, since the two pools use different AMM curves, the ideal balance is not the same.
  >
  > Stable swap pools are designed for 1B+ TVL. Any issue related to pricing/fee is serious. I consider this is a high-risk issue.
- **권고된 수정안**: Curve의 `StableSwap3Pool.vy#L322-L337` 방식으로 재작성 — 입금 전후 invariant `D` 차이 기반으로 ideal balance 계산.
- **Sponsor**: confirmed.

#### 2. 코드 의미 이해

##### (2a) Contract 목적 & 시스템 위치

`HybridPool` — Sushi **Trident**의 stableswap pool template. 1:1에 가까운 자산 쌍(예: USDC-USDT, DAI-USDC)에 대해 Curve-style amplified invariant `D`를 사용해 슬리피지를 최소화. Trident router·aggregator가 이 pool과 상호작용하며, pool 내 모든 가격·유동성·수수료 계산은 stableswap invariant에 종속.

##### (2b) 함수의 컨트랙트 내 역할

`_nonOptimalMintFee(_amount0, _amount1, _reserve0, _reserve1) → (token0Fee, token1Fee)` (line 426–441, internal view). 
- 호출자: `mint(bytes data)` (line 99).
- 역할: LP provider가 **불균형 입금** 시 암묵적 swap이 일어난 것으로 간주하고 그만큼 swap fee를 부과. 입금 후 보상 LP 토큰 수를 계산하기 전에 fee를 차감.
- 잘못된 fee는 protocol revenue의 과소/과다 징수, LP 간 가치 이전 왜곡으로 이어짐.

##### (2c) 함수 의도 (수식)

Stableswap 이론 기반 올바른 의도:
- D₀ = current invariant (입금 전): `D₀ = computeLiquidity(_reserve0, _reserve1)`
- D₁ = post-deposit invariant: `D₁ = computeLiquidity(_reserve0 + _amount0, _reserve1 + _amount1)`
- 각 토큰 i의 **ideal balance** (balanced growth 하에서): `idealᵢ = D₁ × _reserveᵢ / D₀`
- **Imbalance** (실제 post-balance – idealᵢ): `|(_reserveᵢ + _amountᵢ) − idealᵢ|`
- Fee per token: `swapFee × imbalanceᵢ / (2 × MAX_FEE)`

즉, "ideal balance"의 정의가 curve에 따라 달라짐:
- **Constant product** (xy=k): `idealᵢ = _amountⱼ × _reserveᵢ / _reserveⱼ` — reserve 비율.
- **Stableswap** (D-invariant): 위 수식. D를 Newton iteration으로 계산해야 함.

##### (2d) Line-by-line 분석 (line 426–441)

```solidity
431  ) internal view returns (uint256 token0Fee, uint256 token1Fee) {
432      if (_reserve0 == 0 || _reserve1 == 0) return (0, 0);
433      uint256 amount1Optimal = (_amount0 * _reserve1) / _reserve0;   // BUG — CP 공식
434
435      if (amount1Optimal <= _amount1) {
436          token1Fee = (swapFee * (_amount1 - amount1Optimal)) / (2 * MAX_FEE);
437      } else {
438          uint256 amount0Optimal = (_amount1 * _reserve0) / _reserve1;   // BUG — CP 공식
439          token0Fee = (swapFee * (_amount0 - amount0Optimal)) / (2 * MAX_FEE);
440      }
441  }
```

- **L432**: 빈 pool 처리 — 둘 중 하나 0이면 fee 없음. (virgin mint 시 적용.)
- **L433 (BUG)**: `amount1Optimal = _amount0 × _reserve1 / _reserve0`. 이는 **constant-product** pool의 balanced deposit 공식. StableSwap에서는 reserve 비율이 ideal deposit 비율이 아님 (amplification A가 curve를 flatten).
- **L435**: 입금한 `_amount1`이 CP 기준 optimal 이하면 → token1 부족 → token1 측에 fee 부과.
- **L436**: `token1Fee = swapFee × (_amount1 - amount1Optimal) / (2 × MAX_FEE)`. 수식 구조는 맞지만 `amount1Optimal`이 틀림.
- **L437–440**: 반대 분기, 동일하게 CP 공식으로 `amount0Optimal` 계산 후 fee. 동일 버그.
- **L441**: 종료.

##### (2e) 버그의 근본 의미

HybridPool은 amplification `A`를 가진 stableswap curve로 운영되어, **가격 곡선이 구간별로 flat**. A가 클수록 소액 임밸런스가 유발하는 가격 이탈이 작음. 따라서 "LP가 얼마나 imbalanced 했는가"의 측정 기준이 **reserve ratio**가 아니라 **invariant D 기반 ideal balance**.

CP 공식을 그대로 쓰면:
- 정상 stableswap 환경(작은 price impact)에서 **imbalance가 과대 평가** → 실제 유발된 swap보다 큰 fee 부과. LP가 억울하게 손해.
- 극단적 불균형(near-depeg)에서는 반대로 **과소 평가** 가능성도 존재.
- 공격 관점: LP가 이 공식을 역산해 보상을 얻을 수 있는 deposit 패턴을 설계 가능 (MEV).

Protocol-level: stableswap의 1B+ TVL 설계 전제 하에서 소규모 fee 왜곡도 누적 금액으로는 크며, pool의 유인 구조 (LP가 imbalance 기여한 만큼 부담) 자체가 파손.

##### (2f) 올바른 fix

```solidity
function _nonOptimalMintFee(...) internal view returns (uint256 token0Fee, uint256 token1Fee) {
    if (_reserve0 == 0 || _reserve1 == 0) return (0, 0);
    uint256 D0 = _computeLiquidity(_reserve0, _reserve1);
    uint256 D1 = _computeLiquidity(_reserve0 + _amount0, _reserve1 + _amount1);
    uint256 ideal0 = D1 * _reserve0 / D0;
    uint256 ideal1 = D1 * _reserve1 / D0;
    uint256 new0 = _reserve0 + _amount0;
    uint256 new1 = _reserve1 + _amount1;
    uint256 diff0 = new0 > ideal0 ? new0 - ideal0 : ideal0 - new0;
    uint256 diff1 = new1 > ideal1 ? new1 - ideal1 : ideal1 - new1;
    token0Fee = swapFee * diff0 / (2 * MAX_FEE);
    token1Fee = swapFee * diff1 / (2 * MAX_FEE);
}
```
Curve StableSwap3Pool.vy L322–337의 전형적 구조. `_computeLiquidity` (line 341)는 HybridPool이 이미 정의한 internal view function — Newton iteration 내장.

#### 3. IntentChecker annotation 시도 (개발 시점 관점 포함)

**개발 시점 가정**: HybridPool 저자는 stableswap 구조를 이해하고 있음 (`_computeLiquidity`, `_getY`, `_getYD` 작성). 버그 인지 없이 `_nonOptimalMintFee`에 annotation을 달려 하면?

**(a) state variable 변화?** — `_nonOptimalMintFee`는 `internal view`, storage write 없음. `changed`/entry-exit 채널 부재.

**(b) 기존 landscape의 grammar-expressible annotation으로 buggy/correct 구분?**

함수 scope 변수: `_amount0`, `_amount1`, `_reserve0`, `_reserve1`, `swapFee`, `MAX_FEE`, `amount1Optimal`(or `amount0Optimal`), `token0Fee`, `token1Fee`. 모두 uint256. Grammar-expressible annotation은 이들의 **다항 산술 결합**뿐.

발달 시점 개발자가 자연스럽게 시도할 만한 annotation들:

1. **상·하한 bound**: `@Post token1Fee <= swapFee * _amount1 / MAX_FEE`. Grammar OK. 그러나 buggy·correct 모두 satisfied → 구분 불가.
2. **비율 기반 intent**: `@Post token1Fee == swapFee * (_amount1 - _amount0 * _reserve1 / _reserve0) / (2 * MAX_FEE)` (개발자가 "imbalance = _amount1 − CP-optimal"로 정의한 경우). Grammar OK. **하지만 이것이 정확히 buggy 코드의 수식** → buggy는 tautologically satisfied, correct는 violated. 결과: **IntentChecker가 correct를 violation으로 오판**.
3. **올바른 stableswap 공식**: `@Post token1Fee == swapFee * (_new1 - D1 * _reserve1 / D0) / (2 * MAX_FEE)` 형식. `D0`·`D1`이 함수 scope에 없음 → **표현 실패**.

→ **핵심 관찰 (수학적 엄밀)**: Grammar의 expressive range = scope 변수에 대한 **rational-polynomial 함수**. 반면 correct ideal balance는 stableswap invariant D에 의존하며, D는 3차 방정식 `D³ − 16A·xy·D + 16A·xy·(x+y) − 4xy·D = 0`의 해로 **rational-polynomial이 아님** (Cardano 공식 적용 시 세제곱근 등장). 따라서 `A`, `_reserve0`, `_reserve1`가 모두 scope 안에 있음에도 **이들의 어떤 rational-polynomial 조합도 D와 같아지지 않음**. 재료 부족이 아니라 **허용된 연산의 닫힘 범위** 밖 (자·컴퍼스로 각의 삼등분 불가와 같은 구조적 제약).

이 맥락에서 개발자가 자연스럽게 시도하는 "경제학적으로 가장 그럴듯한" rational-polynomial specification(`_amount_j × _reserveᵢ / _reserveⱼ`)이 하필 **buggy 공식 그 자체**. Grammar가 허용하는 다른 표현도 많지만 그 어느 것도 correct가 아니며, 가장 단순·직관적 후보가 buggy와 일치해 **IntentChecker가 오히려 버그를 sanction하는 위험**을 낳음.

**(c) 보조 local 주입 우회?**: 개발자가 `uint256 D0 = _computeLiquidity(_reserve0, _reserve1);`를 함수 상단에 추가해 landscape 확장 가능. 그러면 `@Post amount1Optimal == D1 * _reserve1 / D0`가 grammar-expressible. 그러나:
- 이 주입은 **production code 변경**이며, 개발자가 "D가 fee 계산에 관여한다"는 것을 알고 있어야 수행 → **버그 인지 전제**.
- 주입 이후에는 "buggy amount1Optimal = CP 기반 ≠ D 기반 ideal"이므로 annotation이 fire — 즉 **L4a가 auxiliary injection을 통해 L5 영역으로 이동**.

**"Pure annotation-only" paradigm에서는 표현 불가** → L4a 확정.

#### 4. 분류 타당성

- 현재: **L4a**. ✅ 유지.
- blocker 본질: 함수의 기존 variable landscape에서 grammar-expressible annotation 중 어떤 것도 buggy/correct를 구분하지 못함. Grammar의 algebraic 범위가 CP 공식 가족을 정확히 덮음 — 즉 **grammar로 쓸 수 있는 정답 후보들이 모두 실은 오답(buggy 코드 자체)** 이라는 특이한 배치.
- `annotation_plans.md` line 1419–1424 설명은 정확. 다만 "D가 Newton iteration으로 계산됨"이라는 표현이 한계의 원인을 독자에게 정확히 전달하는지 — **분석 엔진은 `_computeLiquidity`를 호출·추상화할 수 있으나 annotation grammar가 함수 호출을 허용하지 않는다**는 점을 명시하면 더 분명.

#### 5. 근본 원인

**본질 (I3 axis α — 변수-관계에 함수 호출이 포함)**: `_nonOptimalMintFee` scope에는 correct 관계에 기여하는 변수들(`_reserve0`, `_reserve1`, `_amount0`, `_amount1`, `swapFee`, `MAX_FEE`, `A`, `N_A`, `A_PRECISION`)이 **존재함**. 문제는 correct 관계식이 이들 사이의 rational-polynomial 조합만으로는 표현되지 않고 **`_computeLiquidity(_reserve0, _reserve1)`, `_computeLiquidity(_reserve0 + _amount0, _reserve1 + _amount1)` 두 internal 함수 호출 결과**를 피연산자로 요구한다는 점. intentValue grammar는 변수·상수만 허용하므로 함수 호출이 관계 안에 들어갈 수 없음.

Case 2와의 구분: Case 2는 scope에 correct 관계를 맺을 변수 자체가 부재 (axis β). 본 case는 Case 1과 같은 축 (axis α) — 재료가 없는 것이 아니라, **재료를 올바르게 조합하려면 함수 경계를 넘는 호출이 필요**.

Sub-variation (I3 axis α 내부):
- **Case 1**: external interface view call (`IOracle(source.source).decimals()`) — grammar 확장 시 `@IReturn`-style 바인딩으로 접근 가능할 수 있는 대상.
- **Case 3 (본 case)**: **internal view function** (`_computeLiquidity`) — 현재 `@IReturn`은 interface 전용이라 grammar 확장에도 별도 채널 설계 필요.

G-표면:
- **G1** — `_computeLiquidity(...)`를 intentValue에 쓸 수 없음 (internal function call).
- **G3** — D₀, D₁ 값을 담는 local이 `_nonOptimalMintFee` scope에 부재. (주입 경로는 I4 참조 — L5 영역으로 이동.)
- **G2 해당 없음** — 사용자 관찰대로 D를 얻은 뒤에는 `D*D*D` 같은 반복 곱셈이면 충분. `**` 부재는 이 case의 primary blocker 아님.

**부차 관찰 — "silent sanction" 위험 (I5 유래)**: Grammar가 허용하는 rational-polynomial specification 중 "가장 경제적으로 그럴듯한" 선택(`_amount_j × _reserveᵢ / _reserveⱼ`)이 하필 buggy 공식 자체. 개발자가 선의로 작성한 annotation이 buggy 코드를 tautologically validation할 수 있음 → **L4a 내에서도 fail-by-confirmation mode가 가능한 위험 사례**. I3 axis α의 일반 패턴에 얹힌 부가 위험이며, α 분류 자체와는 독립.

#### 6. paper 문장 개선 제안

현재 L4a 문장 (line 1307) 유지 가능하되, 이 case의 insight는 **별도 insight 문단**으로 Discussion에 배치 가치 (C5 항목 참조):
> *When the annotation grammar's algebraic range coincides with the buggy code's formula, even a well-intentioned developer producing the most specific annotation confirms the buggy behavior. This is a failure mode of simple grammars that goes beyond "inexpressibility" — the specification language silently sanctions the wrong answer.*

---


#### 6. paper 문장 개선 제안

Case 1에서 제안한 문장과 동일 개선안이 이 case도 포괄. 다만 "function call that does not appear in the program"을 유지해도 되지만 **G3 강조가 필요**: "intermediate values not bound to any variable in the target function's scope"를 포함한 개선안이 25_H_05에도 잘 맞음.

추가 insight: 이 case는 **"호출 사이트 자체의 부재"**가 `@IReturn`으로의 이론적 우회마저 막는다는 점을 보여줌 — L4a 내 엄격한 하위 패턴으로 식별 가능.

---
