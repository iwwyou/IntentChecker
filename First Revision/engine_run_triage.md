# 엔진 실행 트리아지 — baseline 20개 + phase_reviews 빌드 케이스 전수 실행

진단 전용 문서. 아래 모든 케이스는 실제로 venv python으로 `main.py`를 돌려서 확인함
(`.venv/Scripts/python.exe main.py <case.json>`, cwd = 프로젝트 루트), 케이스당 90초
타임아웃, 실행일 2026-08-30. 이 문서에서 고친 것은 아무것도 없음 — 사용자가 무엇을,
어떤 순서로 고칠지 결정하기 전에 보고 싶다고 한 로그임. 각 케이스의 stdout/stderr
전체는 세션 scratchpad(`out_<case>.txt`)에 저장되어 있음 — 여기 발췌보다 더 많은
맥락이 필요하면 그쪽을 참고.

**범위**: (A) `evaluation/RQ1/run_all.py`의 `CASE_JSONS` 목록에 있는 baseline 20개
케이스 (논문 RQ2 "20/20 VIOLATED" 결과의 근거가 되는 그 세트). (B) `phase_reviews/`
35케이스 리비전 배치 중 실제 케이스 JSON이 `evaluation/RQ1/cases/<id>/<id>.json`에
존재하는 것들 (25개 — `web3bugs_101_H_02`/`web3bugs_70_H_09`는 제외/inexpressible
판정으로 빌드된 적 없어서 제외; `web3bugs_42_H_01`은 포함은 했지만 아래에서
설명하듯 stale 빌드라 엔진의 순수한 테스트로 보기 어려움).

**2026-08-31 업데이트**: Group 2(`abi.decode`/`abi.encode*`)를 실제로 고침 — 아래
Group 2 항목과 `engine_code_changes.md`에 상세 내용 기록됨. `web3bugs_29_H_08`은
이제 크래시 없이 끝까지 돌아감(WARNING). `web3bugs_29_H_11`은 `abi.decode` 호출
3개는 다 통과했지만, 그동안 도달조차 못했던 곳에서 별개의 새 크래시(interval
`join()`의 type-length 불일치)를 만남 — 이것도 아래에 새 단발성 항목으로 추가함.
baseline 20개 재실행해서 회귀 없음 확인함(여전히 17 VIOLATED / 3 ERROR, 그대로).

## 헤드라인: baseline 회귀

**baseline 20개 중 3개가 이제 VIOLATED가 아니라 ERROR로 나옴**: `web3bugs_45_H_01`,
`web3bugs_51_H_02`, `web3bugs_56_H_02`. 지금 다시 돌리면 논문의 "20/20 VIOLATED"
결과가 그대로 성립하지 않음. 이 중 2개(`45_H_01`, `51_H_02`)는 **이미 알고 있었고
의도적으로 보류해둔** 이슈임 (`engine_code_changes.md`에 기록됨) — 이번 실행은 그걸
재확인한 것이고, `45_H_01`은 애매했던 부분(아래 Group 1)까지 정리됨.
`56_H_02`는 **이번에 새로 발견된** 것으로, 이전에 로그된 적 없음.

---

## 요약 표

| 케이스 | 구분 | 결과 | 크래시/행 지점 | 그룹 |
|---|---|---|---|---|
| WANGMI, Nokon, SwordCrowdsale, BoostToken×2, HIT, `5_H_07`, `5_H_08`, `5_H_12`, `47_H_02`, `58_H_02`, `60_H_01`, `62_H_08`, `70_H_10`, `77_H_01`, `78_H_02`, `101_H_01` (16개) | baseline | VIOLATED | — | 정상 |
| `web3bugs_45_H_01` | baseline | **ERROR** | `DynamicCFGBuilder.py:1403` (`No CFG node found after line 220`) | G1b (callee 순서, 기존 로그) |
| `web3bugs_51_H_02` | baseline | **ERROR** | `Evaluation.py:1188` (`member 'div' is not a recognised global-member`) | 단발성 (기존 로그, 보류) |
| `web3bugs_56_H_02` | baseline | **ERROR** | `EnhancedSolidityVisitor.py:1013` (`Unknown common clause type`) | 단발성 (**신규**) |
| `numscout_EthereumGod` | phase_review | **ERROR** | `DynamicCFGBuilder.py:1403` (141행) | G1a (`@During` 인접, 기존 로그) |
| `web3bugs_112_H_01` | phase_review | **ERROR** | `DynamicCFGBuilder.py:1403` (26행) | G1a (기존 로그) |
| `web3bugs_31_H_01` | phase_review | **ERROR** | `DynamicCFGBuilder.py:1403` (86행) | G1a (기존 로그) |
| `web3bugs_29_H_08` | phase_review | ~~ERROR~~ → **WARNING** (2026-08-31 수정됨) | — | G2 (해결됨) |
| `web3bugs_29_H_11` | phase_review | ~~ERROR~~ (abi는 해결) → **ERROR** (다른 원인) | `Interval.py:584` (`Cannot join intervals of different type lengths`) | G2 해결로 새로 드러난 신규 단발성 |
| `web3bugs_62_H_03` | phase_review | **ERROR** | 일반 주석에서 ANTLR 파싱 에러 → `KeyError: None` | G3 (트리거는 기존 로그, 증상 디테일은 신규) |
| `web3bugs_62_H_10` | phase_review | **ERROR** | 동일 `KeyError: None` | G3 |
| `web3bugs_192_H_01` | phase_review | **ERROR** | 동일 `KeyError: None`, **일반 주석은 발견 안 됨** | G3 (트리거 미확인) |
| `web3bugs_35_H_11` | phase_review | **ERROR** | `StaticCFGFactory.py:422` (`Unsupported typeCategory 'mapping'`) | G4 (기존 로그) |
| `web3bugs_3_H_05` | phase_review | **ERROR** | `StaticCFGFactory.py:422` (동일) | G4 (신규 사례) |
| `web3bugs_113_H_05` | phase_review | **ERROR** | `Evaluation.py:1276` (`'valuation' not in struct 'params'`) | G5a (기존 로그) |
| `web3bugs_52_H_04` | phase_review | **ERROR** | `Refine.py:229`→`Evaluation.py:1276` (`'token0' not in struct 'pairData'`) | G5a (신규 사례) |
| `web3bugs_52_H_34` | phase_review | **ERROR** | `52_H_04`와 동일 (같은 함수) | G5a |
| `web3bugs_70_H_05` | phase_review | **ERROR** | `Evaluation.py:1864` (`'decode144' not in struct 'temp_uq144x112_...'`) | G5b (신규, 관련) |
| `web3bugs_3_H_04` | phase_review | **ERROR** | `EnhancedSolidityVisitor.py:732` (`Type 'bond' is not defined as struct...`) | G6 (**신규**) |
| `web3bugs_35_H_08` | phase_review | **ERROR** | `EnhancedSolidityVisitor.py:732` (`Type 'Position' is not defined...`) | G6 (**신규**) |
| `web3bugs_35_H_12` | phase_review | **ERROR** | `35_H_08`와 동일 (같은 소스 파일) | G6 |
| `web3bugs_65_H_01` | phase_review | **ERROR** | `EnhancedSolidityVisitor.py:2429` (`invalid numeric literal "365.25"`) | 단발성 (**신규**) |
| `web3bugs_52_H_23` | phase_review | **ERROR** | `EnhancedSolidityVisitor.py:771` (`Invalid key type in mapping: IERC20`) | 단발성 (**신규**) |
| `web3bugs_83_H_01` | phase_review | **ERROR** | `Evaluation.py:1959` (`AttributeError: 'NoneType' object has no attribute 'context'`) | 단발성 (기존 로그: `poolInfo`/`struct_defs`) |
| `web3bugs_42_H_01` | phase_review | **ERROR** | `ContractAnalyzer.py:989` (`Modifier 'updateDebt' is not defined`) | 단발성 (stale 빌드, 아래 참고) |
| `web3bugs_79_H_02` | phase_review | **TIMEOUT/행(hang)** | `Engine.py:829` (`_run_worklist`)에서 livelock | 기존에 로그만 되고 미진단이던 hang의 신규 진단 |
| `web3bugs_16_H_06` | phase_review | SATISFIED | — | 크래시는 없지만 **예상과 다른 verdict** (아래 참고) |
| `web3bugs_59_H_04` | phase_review | SATISFIED | — | 크래시는 없지만 **예상과 다른 verdict** |
| `web3bugs_70_H_04` | phase_review | WARNING | — | 크래시는 없으나 기대 결과와 대조 검증 안 됨 |

45개 중 24개가 ERROR 또는 TIMEOUT으로 끝남. 그중 3개는 baseline 회귀임.

---

## 근본 원인 그룹

### Group 1 — `DynamicCFGBuilder.get_current_block()`: "No CFG node found after line X" (4케이스, baseline 1개 포함)

같은 예외, 같은 크래시 지점(`Analyzer/DynamicCFGBuilder.py:1403`)이지만
**이미 별도로 진단된, 서로 다른 두 가지 트리거**임 — 하나의 수정으로 묶으면 안 됨:

**1a. `@During` 주석 청크 바로 뒤에 실제 코드 청크가 오는 경우.** 3번 확인됨:
`numscout_EthereumGod`(141행), `web3bugs_31_H_01`(86행), `web3bugs_112_H_01`(26행).
`engine_code_changes.md`에 이미 상세히 정리되어 있음("Open issue: an `@During`
comment chunk immediately followed by another real-code chunk crashes...") — 원래
"함수 헤더 줄번호 중복" 가설은 `31_H_01` 재현으로 이미 기각됐고, 트리거는 줄번호
충돌과 무관하게 그 인접성 자체임. 여기서 더 파고들지는 않았고, 이번 실행은 3건 모두
재확인한 것뿐임. **근본 수정 방향** (기존 로그에서도 아직 확정하지 않은 부분):
`get_current_block()`의 실제 탐색 알고리즘을 직접 추적해볼 것 — 조회한 줄에
CFG 노드가 없을 때(예: 주석 줄이거나 CFG 노드를 만들지 않는 줄이라서) 좁은 범위의
전방 탐색이 비었다고 바로 raise할 게 아니라, 가장 가까운 선행/포함 CFG 노드로
폴백해야 함. 소스 줄과 CFG 노드가 1:1로 대응하지 않는 언어에서 "정확히 일치하는
게 없으면 raise"는 줄 기반 조회의 기본 동작으로 적절하지 않음.

**1b. 같은 파일 안에서 callee가 caller *뒤에* 선언된 경우** (엔진이 같은 컨트랙트
내 전방 참조를 해석 못 함). 이게 실제로 `web3bugs_45_H_01`을 깨뜨리는 원인:
`checkIsOverdue`(98행)가 `getBorrowed`(174행, 더 뒤에 선언됨)를 호출함 — 이미
직접 실행으로 확인/진단된 사항으로 `engine_code_changes.md`의 "same-file
contraction functions must be declared callee-before-caller" 항목에 있고, 이번
세션의 다른 엔진 변경 전에는 왜 됐었는지 사용자가 조사할 때까지 이 baseline 파일을
일부러 안 고치기로 했었다는 메모도 함께 있음. **이번 트리아지 실행은 동일한 크래시**
(`No CFG node found after line 220`)가 여전히 살아있음을 재확인함. **1a와 1b를
구분하는 게 중요함**: `45_H_01`은 220행 근처에 `@During` 인접 문제가 전혀 없음 —
순수한 전방 참조 케이스라서, 1a를 고쳐도 `45_H_01`은 안 고쳐지고 반대도 마찬가지임.
1b에 대한 체크 스크립트는 이미 존재함(`phase_reviews/check_callee_order.py`);
`45_H_01`은 baseline 세트에서 유일하게 알려진, 의도적으로 안 고친 위반 사례임.

baseline 회귀라는 점을 감안하면, **이 그룹에서는 1b가 더 우선순위 높음** — 논문의
헤드라인 결과를 실제로 깨뜨리고 있는 쪽이고, 사용자 본인의 미해결 질문("이게 전에는
정말 통과했었나, 왜 지금은 안 되지?")도 여전히 답이 없는 상태임. 기존 로그의 제안
그대로, 함수 순서를 재배치하기 전에 `web3bugs_45_H_01.sol`/`.json`과 `main.py`의
git blame/히스토리를 먼저 볼 것을 권함.

### Group 2 — `abi.decode`/`abi.encodeWithSelector`에 엔진 시맨틱스가 없음 (2건 확인) — **RESOLVED (2026-08-31)**

**고쳤음.** 상세 구현/검증 내용은 `engine_code_changes.md`의 해당 항목 참고. 요약: (1)
`EnhancedSolidityVisitor.visitTypeNameExp`가 완전 stub이라 `abi.decode`의 타입-리스트
(`(uint256, address)` 같은)가 파싱 단계에서부터 `None`이 되던 걸 고쳐서 타입 이름을
실제로 담은 `Expression`을 반환하게 함. (2) `Evaluation.evaluate_function_call_context`에
`abi.` 호출을 가로채는 분기를 추가해서 `abi.decode`는 타입-리스트 각 원소에 대한
`TOP`(단일 타입이면 값 하나, 여러 개면 기존 튜플-값 컨벤션대로 리스트)를, `abi.encode`
계열은 전부 `BytesSet.top()`을 반환하도록 함 — `.call()`/`.staticcall()`이 이미
인자를 안 보고 바로 TOP을 반환하던 것과 동일한 패턴. `web3bugs_29_H_08`은 크래시 없이
끝까지 돎(WARNING). `web3bugs_29_H_11`은 `abi.decode` 3건 모두 통과했지만 그 덕에
처음 도달하게 된 곳에서 별개의 새 크래시를 만남(아래 "G2 해결로 새로 드러난 신규
단발성" 참고) — `abi` 수정 자체의 문제는 아님. baseline 20개 재실행 결과 회귀 없음
(17 VIOLATED / 3 ERROR, 그대로).

**원래 진단 내용 (참고용으로 아래 그대로 둠):**

`web3bugs_29_H_08`, `web3bugs_29_H_11` 둘 다 `Evaluation.py:949`
(`evaluate_identifier_context`, `evaluate_member_access_context`를 통해 호출됨)에서
`abi.`로 크래시함. `engine_code_changes.md`에 이미 완전히 진단되어 있음("the `abi`
identifier ... has no semantics anywhere in the engine"): `abi`가 고정된
글로벌 네임스페이스 화이트리스트(`["block","tx","msg","address","code"]`)에
없어서 그대로 raise까지 떨어짐. 이번 실행은 예측대로 두 케이스 모두 크래시함을
확인한 것뿐임. `web3bugs_35_H_08`도 원래 이걸 맞을 걸로 예상됐지만(`burn()`이
`abi.decode(...)`로 시작함) 이번 실행에서는 거기까지 가지도 못하고 다른 버그
(Group 6)에서 먼저 죽음.

**근본 수정 방향** (기존 로그에 이미 두 가지 옵션이 정리되어 있고, 아직 미확정):
크래시를 피하기 위한 특수 케이스를 추가하는 게 아니라 `abi`를 실제로 인식되는
유사-네임스페이스로 취급해야 함 — `abi.decode(data, (T1, T2, ...))`는 두 번째
인자로부터 반환 타입을 정적으로 알 수 있으니 선언된 타입들의 `TOP` 튜플을 생성해야
하고, `abi.encodeWithSelector(...)`/`abi.encode(...)`는 `.call`/`.staticcall`/
`.delegatecall`이 이미 크래시 없이 `TOP`으로 degrade하는 것과 마찬가지로 불투명한
bytes 타입의 `TOP`을 생성해야 함.

### Group 3 — 일반(`@` 없는) 한 줄 주석이 ANTLR replay 파싱을 깨뜨림 (2건 확인 + 증상은 같은데 트리거 미확인 1건)

`web3bugs_62_H_03`, `web3bugs_62_H_10` 둘 다 `ContractAnalyzer.py:1029`
(`contract_cfgs[self.current_target_contract]`, `current_target_contract`가
아직 `None`인 상태)에서 ANTLR 인식 에러 뒤에 `KeyError: None`으로 크래시함.
**`113_H_05`를 빌드하면서 이미 로그된 것과 같은 종류의 버그**임("a plain
(non-`@`) full-line comment anywhere in a contraction file crashes `main.py`'s
replay" — 그때는 주석을 제거해서 우회함), 다만 이번 실행에서는 기존 메모에는
없던 구체적인 메커니즘을 하나 추가로 확인함: 주석 텍스트 자체가 마치 statement인
것처럼 그대로 ANTLR에 먹여짐. 두 파일 모두 제거되지 않은 일반 주석이 실제로
남아있음을 직접 확인함:
```
# web3bugs_62_H_03.sol:55
// ∆time*rewardTokensPerSecond*oneDepositToken / totalVirtualBalance
```
이게 이번 실행의 ANTLR 에러 메시지와 그대로 일치함(`token recognition error
at: '∆'`, `no viable alternative at input 'time*'`). `web3bugs_62_H_10`은 일반
주석이 4개(37/40/42/44행) 있고, 그중 어느 하나만으로도 트리거로 충분함.

`web3bugs_192_H_01`은 **동일한 최종 예외**(`KeyError: None`, 같은 줄)를 맞지만
contraction 파일 어디에도 일반 주석이 **없음** — 직접 확인함. 트리거가 (`.sol`이
아니라) 케이스 JSON 자체의 레코드 어딘가에 있는 별도 주석이라서 아직 못 찾았거나,
아니면 같은 깨진 상태(`current_target_contract` 미설정)로 이어지는 완전히 다른
경로가 있는 것 중 하나임. 추측으로 이 그룹에 묶지 않고 미확인으로 별도 표시해둠.

**근본 수정 방향**: interactive/replay 청크 파이프라인이 일반 `//` 주석 청크를
grammar의 `accept()`에 넘기기 전에 인식하고 건너뛰어야 함 — `@`로 시작하는
어노테이션 청크가 이미 일반 코드와 다르게 라우팅되는 것과 같은 방식으로. 주석은
파싱할 statement로 ANTLR에 절대 넘어가면 안 됨. 이게 고쳐진 뒤에도
`current_target_contract`가 조용히 `None`인 채로 dict 조회에 들어가는 대신
크게 실패해야 하는지는 별도로 점검해볼 가치가 있지만, 1차 수정은 그 앞단임.

### Group 4 — mapping 타입 함수 파라미터 미지원 (2건)

`web3bugs_35_H_11`, `web3bugs_3_H_05` 둘 다 `StaticCFGFactory.py:422`
(`make_param_variable`, `Unsupported typeCategory 'mapping'`)에서
`process_function_definition` → `make_function_cfg`를 거쳐 크래시함. 이미 로그됨
(`35_H_11` 빌드 중 발견) — 이번 실행은 정확히 같은 크래시 지점을 공유하는 두 번째
확인 사례로 `3_H_05`를 추가한 것이고, 둘이 같은 크래시 지점을 공유한다는 건 이전에는
몰랐던 사실임.

**근본 수정 방향**: `make_param_variable`의 타입 분기에는 `mapping` 케이스가
아예 없음. Solidity는 `internal`/`private` 함수에서 mapping 타입 파라미터를
storage 참조로 실제로 허용하므로, 수정 방향은 이 두 파일에서만 크래시를 피하는
특수 케이스가 아니라 파라미터를 caller 쪽 mapping 값의 alias로 모델링하는(최소한
mapping의 value 타입의 `TOP`으로라도) 실제 케이스를 추가하는 것임. 두 케이스의
정확한 파라미터 시그니처를 먼저 확인해서 실제로 어떤 형태(storage 참조인지 다른
무언가인지)인지 확정할 필요가 있음.

### Group 5 — struct 멤버/필드 resolution ("'X' not in struct 'Y'") — 관련된 두 서브 메커니즘 (4건)

**5a. mapping→struct 메모리 복사가 필드를 잃어버림.** `web3bugs_113_H_05`
(`'valuation' not in struct 'params'`)는 이미 `engine_code_changes.md`에
처음부터 끝까지 진단되어 있는 바로 그 케이스임("Confirmed: mapping-to-struct
memory-copy fields resolve empty"). 이번 실행에서 **같은 계열의 신규 확인 사례
2건**을 추가함: `web3bugs_52_H_04`, `web3bugs_52_H_34`(`'token0' not in struct
'pairData'`, 둘 다 `TwapOracle.consult` 안, 동일한 `pairData = someMapping[key]`
형태의 복사)인데, 도달 경로가 살짝 다름 — 단순 `require`가 아니라
`Refine.py:229`(`_update_comparison_condition`)를 거침, 즉 일반 필드 읽기뿐
아니라 *조건 refine* 과정도 이걸로 깨진다는 뜻임. 기존 로그 기준 근본 원인은:
`ContractAnalyzer._create_variable_object`의 array/mapping 분기가 복사된 struct를
만들 때 `struct_defs=`/`enum_defs=`를 일관되게 전달하지 않아서, 복사본이 실제
struct 타입이 선언한 것보다 적은 필드만 가진 채로 조용히 만들어지고, 나중에 (선언은
됐지만) 없는 필드를 읽으면 `TOP`을 반환하는 대신 raise함.
**기존 로그에 이미 제안된 수정 방향**: struct 값을 만드는 모든 경로(mapping 복사든,
array 원소든, 다른 어디서든)는 항상 struct 타입이 선언한 모든 필드를 채워야 함
(각각 `TOP`/bottom으로 기본값 설정), 절대 부분적인 dict를 만들면 안 됨 — 타입
자체가 선언한 필드에 대해서는 필드-존재 체크가 구조적으로 실패할 수 없어야 함.

**5b. 바인딩된 라이브러리 메소드가 struct 필드 조회로 잘못 resolve됨.**
`web3bugs_70_H_05`는 `Evaluation.py:1864`(`evaluate_function_call_context`)에서
`'decode144' not in struct 'temp_uq144x112_...'`로 크래시함. 이건
`FixedPoint.decode144()`를 다른 라이브러리 호출이 반환한 중간 `uq144x112` 값에
호출한 것(이름 붙은 struct 필드가 아니라 `using X for Y`로 바인딩된 메소드를
합성된/무명 receiver에 호출한 것)인데, 에러 메시지의 합성된 이름을 보면 interpreter가
그 중간값을 임의의 struct 레코드로 모델링한 다음 `using` 바인딩 테이블을 먼저
확인하지 않고 `.decode144`에 대해 필드 조회를 시도한 것으로 보임. **새로 발견된
것으로 이전에 로그된 적 없음.** 5a와 관련은 있음(같은 "struct 표현이 불완전하거나
잘못 쓰임" 계열, `evaluate_member_access_context`/`evaluate_function_call_context`
근처의 같은 코드) 하지만 다른 버그임 — 5a와 같이 점검해볼 가치는 있지만 한 번의
수정으로 둘 다 해결된다고 가정하지는 말 것. **수정 방향**: receiver 타입이
라이브러리의 바인딩 타입과 일치할 때는, receiver가 이름 붙은 변수가 아니라 합성된
중간값인 경우를 포함해서, 일반 struct-필드 조회로 폴백하기 전에 `using X for Y`
바인딩 테이블을 먼저 확인하도록 호출 resolution을 고쳐야 함.

### Group 6 — 스코프 안에서 user-defined struct 타입을 못 찾음 ("Type 'X' is not defined as struct, enum, or type alias") (3건, 신규)

`web3bugs_3_H_04`(`Type 'bond' is not defined... in file level`)와
`web3bugs_35_H_08` + `web3bugs_35_H_12`(`Type 'Position' is not defined...
in contract 'ConcentratedLiquidityPool'`, 같은 소스 파일, 같은 struct) 모두
**동일한** 함수 쌍에서 실패함 — `EnhancedSolidityVisitor.py:580`
(`visitTypeName`) → `EnhancedSolidityVisitor.py:732`(`visitUserDefinedType`),
다만 호출한 쪽이 다름(`3_H_04`는 `visitStateVariableDeclaration`,
나머지 둘은 `visitMapping`). **`engine_code_changes.md`에 아직 없는 신규
발견.** `35_H_08`/`35_H_12`는 이 지점에서 실패한 게 그 케이스들에 대해 예측했던
`abi.decode` 크래시(Group 2)에 *도달하기도 전*임 — 이 둘한테는 이게 더 앞단의
블로커임.

**추정 메커니즘** (완전히 추적하지는 못함): 두 struct 타입 모두, mapping/상태변수
선언이 그 타입을 참조하는 시점에 확인되는 스코프와는 다른 스코프에서 선언되어
있는 것으로 보임 — 예를 들면 상속받은 부모 컨트랙트의 struct를 자식 컨트랙트에서
비한정 이름으로 참조하는 경우, 또는 파일 레벨 struct를 컨트랙트 본문 안에서
참조하는 경우. `visitUserDefinedType`/`visitTypeName`은 현재 컨트랙트 자체에
로컬로 선언된 타입 테이블만 확인하고, 전체 상속/파일 스코프 체인은 확인하지 않는
것으로 보임. **수정 방향**: 타입 이름 resolution이 타입이 정의되지 않았다고
결론 내리기 전에 컨트랙트 → 상속 체인 → 파일 레벨 타입 순으로 순회해야 함,
Solidity의 실제 스코프 규칙을 그대로 반영해서 — 이건 파싱 단계의 문제가 아니라
analyzer의 타입 테이블에서의 등록/조회 순서 문제로 보임(두 이름 모두 올바르게
읽히고 있고, 다만 확인 중인 테이블에서 못 찾는 것뿐임).

---

## 단발성 발견들

**`web3bugs_29_H_11` — G2 해결로 새로 드러난 신규 단발성 (2026-08-31, 아직 미진단)**
— `abi.decode` 수정 이후 `burnSingle()`의 `if (tokenOut == token1) {...} else
{...}` 분기를 합류(join)하는 지점에서 `Domain/Interval.py:584`
(`Cannot join intervals of different type lengths`)로 크래시함
(`DynamicCFGBuilder.py:257` → `Utils/Helper.py`의 `_merge_by_mode`/
`_merge_values`를 거쳐 도달). 어느 변수의 두 분기 값이 비트 폭이 다른지는 아직
안 짚었음 — 트레이스에 `name`이 안 찍혀서 다음엔 `join()` 호출 직전에 찍어봐야 함.
`abi.decode` 수정 자체가 만든 버그는 아님(`_elementary_type_top`이 만드는 비트
폭은 각 타입 이름에서 그대로 읽은 것이라 선언된 타입과 정확히 일치함,
예: `"int24"`→24, `"uint128"`→128) — 그동안 `abi.decode` 크래시에 막혀서 아예
도달하지 못했던 코드에서 처음으로 드러난 별개의 버그임. 상세 트레이스는
`engine_code_changes.md`의 새 항목 참고. 아직 안 고침.

**`web3bugs_51_H_02` (baseline, 회귀)** — 체인된
`.add().sub().mul().div()` SafeMath 스타일 호출에서 `member 'div' is not a
recognised global-member`. `engine_code_changes.md`에 **이미 로그되어 있고
의도적으로 보류 중**("`web3bugs_51_H_02` regressed from VIOLATED to ERROR"),
이번 세션의 `struct_defs=`/`enum_defs=` 전달 관련 변경과 연관이 있을 걸로
추정되지만 아직 진단 안 됨. 이번 실행은 여전히 동일하게 에러난다는 것만 재확인함.
Group 5b의 수정(체인/합성된 receiver에서의 바인딩된 라이브러리 호출 resolution)이
이것도 우연히 해결할지 확인해볼 가치는 있음 — 증상 모양(체인 도중 `.div`가
바인딩된 멤버로 인식이 안 됨)이 비슷해 보임 — 다만 이건 확인해볼 가설이지
당연한 전제로 삼지는 말 것.

**`web3bugs_56_H_02` (baseline, 회귀, 신규)** — `EnhancedSolidityVisitor.py:1013`
(`_build_common_clause_dict`, `visitPostIntent`를 통해 호출됨)에서 `Unknown
common clause type: <class 'Parser.SolidityParser.SolidityParser.
CommonClauseContext'>`. `engine_code_changes.md`에 이전에 로그된 적 없음.
이게 예전엔 통과했던 baseline 케이스라는 점을 감안하면, grammar가 확장되면서
이 dispatch가 한 번도 업데이트되지 않은 채로 새로운 `CommonClauseContext` 노드를
만들어내게 됐거나, 아니면 리팩터링으로 dispatch가 처리하는 범위가 좁아진 것 중
하나임. `Parser/Solidity.g4`의 `commonClause`/`postClause` 규칙과
`_build_common_clause_dict`가 처리하는 케이스를 직접 diff 떠봐야 어느 쪽이
어긋난 건지 알 수 있음 — 트레이스만으로는 알 수 없음.

**`web3bugs_65_H_01` (신규)** — `EnhancedSolidityVisitor.py:2429`
(`visitLiteralSubDenomination`)에서 `invalid numeric literal "365.25"`.
문제가 되는 줄은 contraction 과정에서 생긴 게 아니라 실제 원본 소스 그대로임
(`uint256 public constant ONE_YEAR = 365.25 days;`, 감사받은 컨트랙트에서
그대로 복사됨). subdenomination 리터럴 평가기가 `days`/`hours` 등의 배수를
적용하기 전에 정수 리터럴 피연산자만 받고 소수는 아예 거부하는 것으로 보이는데,
둘 다 유효한 Solidity 숫자 리터럴임. **수정 방향**: 정수 리터럴이 이미 이
경로에서 받아들여지는 것과 똑같은 방식으로 소수 리터럴도 받아들여야 함 —
소수 단위의 day/hour/week 개수는 실제 컨트랙트에서 흔한 패턴이라(이 데이터셋
안에도 최소 하나 더 있음) 특수 케이스로 우회할 게 아니라 그냥 완전성이
빠져있는 부분임.

**`web3bugs_52_H_23` (신규)** — `EnhancedSolidityVisitor.py:771`
(`visitMappingKeyType`)에서 `mapping(IERC20 => bool)` /
`mapping(IERC20 => PairInfo)`에 대해 `Invalid key type in mapping: IERC20`.
실제 Solidity는 elementary/contract/interface/enum 타입 모두 mapping key로
허용하는데, visitor의 key 타입 체크는 하드코딩된 elementary 타입 화이트리스트만
강제하는 것으로 보임. **수정 방향**: 현재 화이트리스트 바깥이면 무조건 거부하는
대신, contract/interface 타입(밑바탕 `address` 표현으로 취급)과 enum 타입
(밑바탕 정수 표현으로 취급)을 받아들이도록 체크를 확장해야 함.

**`web3bugs_83_H_01`** — `Evaluation.py:1959`(`evaluate_function_call_context`,
`visitInteractiveExpressionStatement` → `process_function_call`을 거쳐 도달)에서
`AttributeError: 'NoneType' object has no attribute 'context'`. 이미 로그된
"state-level struct-array debug annotations resolve to empty struct members"
항목과 일치함(`poolInfo[1]`의 `struct_defs=`/`enum_defs=`가
`ContractAnalyzer._create_variable_object`의 array 분기에서 전달 안 됨) —
그 항목에는 이미 **제안된 수정**이 있음(mapping 분기의 `all_structs`/
`all_enums` 구성 방식을, `parent_cfgs`까지 포함해서, array 분기에도 그대로
적용). 이번 실행은 빌드 시점에 나왔던 `[WARNING] Cannot resolve LHS
expression`이라는 증상 수준이 아니라, 이 케이스가 실제로 막혀있다는 걸 실행으로
처음 확인한 것임.

**`web3bugs_42_H_01` — 깨끗한 엔진 버그 신호가 아님.** `updateDebt` modifier가
`ContractAnalyzer.py:989`에서 `Modifier 'updateDebt' is not defined`로
크래시하는데, 실제로는 현재 contraction 파일에 그 modifier가 선언되어 있음
(`web3bugs_42_H_01.sol:75`, 84행의 유일한 사용 지점보다 앞에). `case_progress.md`
의 이 케이스 행 자체가 이후 relation/contraction 변경 이후 케이스 JSON을 다시
빌드하지 않았다고 명시하고 있음("Case JSON not yet rebuilt with the new
relation (blocked case anyway)"). 이 크래시는 신선한 엔진 발견이 아니라 오래된
JSON/`.sol` 불일치와 맞아떨어짐. **재진단하기 전에 현재 contraction으로부터
케이스 JSON을 다시 빌드할 것을 권함** — 이 케이스에 대해 이전에 로그된, 더 깊은
곳에 있는 진짜 블로커(cast 없는 chained interface 호출이 struct를 반환하는 문제,
`'denominator' not in struct 'lf'`, `engine_code_changes.md`에 이미 있음)는
modifier 문제가 해결되고 나면 아마 여전히 그 밑에 남아있을 것이고, 그게 실제로
고쳐야 할 대상으로 남아있음.

---

## `web3bugs_79_H_02` — 행(hang)이었던 것, 이번엔 실제로 진단함

이전에는 "약 6분 안에 종료 안 됨, 진단 안 됨"이라고만 로그되어 있었고, 두 가지
가설(진짜 무한정지 vs. 느리지만 진행은 되고 있음)이 열려있었음. 이번 실행에서는
그냥 타임아웃만 재확인한 게 아니라 `faulthandler.dump_traceback_later`(45초
기준, hard-exit)로 실제 스택 트레이스를 떠서 확인함:

```
Thread (most recent call first):
  Interpreter/Engine.py:829 in _run_worklist
  Interpreter/Engine.py:685 in interpret_function_cfg
  Interpreter/Semantics/Evaluation.py:2095 in evaluate_function_call_context
  Analyzer/ContractAnalyzer.py:1694 in process_function_call
  Analyzer/EnhancedSolidityVisitor.py:1518 in visitInteractiveExpressionStatement
  ...
  main.py:173 in simulate_inputs
```

이걸로 애매했던 부분이 **기존 로그의 가설 (a)** 쪽으로 확정됨: callee 자신의
CFG worklist 순회(`_run_worklist`, 함수 호출을 interpret하는 도중에 진입) 안에서
멈춰있는 것이지(`currentPhase()`/`_atPhase()`가 여러 분기에서 서로를 호출하는
형태가 이미 의심스럽다고 표시되어 있었음), 단순히 느린 게 아님.

`_run_worklist`를 직접 읽어보면(`Interpreter/Engine.py:795-836`): `deque` 기반
worklist인데, 방문 안 된 predecessor가 남은 `join_point_node`는 다시 큐에
넣고 미룸(`if unvisited_preds and len(work) > 0: work.append(node); continue`).
이건 모든 predecessor가 다른 경로를 통해서 결국은 방문될 거라는 보장이 있을
때만 안전함. 만약 어떤 predecessor가 오직 *이 join 노드 자신의 처리 결과를
통해서만* reachable해지는 경우(예: 그 join의 output에 의존하는 루프 back-edge)
거나, 그래프 상에는 구조적으로 존재하지만 `start_block`에서의 어떤 전방 경로로도
실제로 enqueue되지 않는 경우라면, 그 노드는 영원히 계속 스스로를 다시 큐에
넣게 됨(pop할 때마다 같은 불만족 조건을 발견하는데, 그 노드 자신이 다시 work에
들어가 있는 상태이기 때문). 이건 livelock이지 느린 수렴이 아님 — 시간을 아무리
줘도 해결되지 않음.

**근본 수정 방향, 아직 완전히 확정 안 됨**: CFG 사이클에 대해 종료가 보장되는
join 전략이 필요함 — 예를 들면 (a) 노드가 몇 번 미뤄졌는지 추적해서, 특정
횟수를 넘으면 현재까지 방문된 predecessor만으로 강제로 처리하도록 하거나
(사이클이 있는 그래프에 대한 worklist 알고리즘에서 표준적인 방식), (b) 사이클
안의 노드가 사이클을 최소 한 번은 거친 뒤에 처리되도록 보장하는 제대로 된
reverse-postorder / SCC-aware 스케줄링을 쓰는 것. `currentPhase()`/
`_atPhase()`의 구체적인 CFG가 왜 만족 불가능한 predecessor 집합을 만들어내는지
직접 볼 수 있는 정보가 부족해서 둘 중 어느 쪽이 맞는지는 말할 수 없음 — worklist
알고리즘만 따로 읽어서 될 문제가 아니라 `Evaluation.py:2095`에서 도달하는 callee의
실제 CFG 엣지를 직접 추적해야 함.

---

## 크래시는 안 나지만 예상과 다른 verdict가 나온 것들 — 크래시가 아니라 별도로 표시

아래 세 개는 에러는 안 났지만, 각 `analysis.md`의 전제 자체가 그 시나리오가
실제 버그를 보여준다는 것이므로, 위와는 다른 종류의 문제(엔진 크래시가 아니라
결과 정확성 문제)이긴 해도 VIOLATED가 아닌 결과는 확인해볼 가치가 있음:

- **`web3bugs_16_H_06`** — SATISFIED. `analysis.md`의 시나리오
  (`gasOracle.decimals()=9`, `priceOracle.decimals()=6`, `gasPrice=5e9`,
  `ethPrice=3e9`)는 누락된 `toWad` 정규화 단계가 잘못된 결과를 만든다는 걸
  보여줘야 하는 것임.
- **`web3bugs_59_H_04`** — SATISFIED. `analysis.md`의 계산된 수치 자체가
  buggy=2000 vs intended=6666, 즉 명백한 violation을 예측하고 있음.
- **`web3bugs_70_H_04`** — VIOLATED가 아니라 WARNING. 꼭 틀렸다는 건 아님
  (interval-domain에서 `(Entry)`가 붙은 다중-statement 관계에 대해 Warning이
  정당한 결과일 수도 있음), 다만 케이스 자체가 기대하는 결과와 독립적으로
  검증되지는 않았음.

여기서 더 추적하지는 않았음 — 디버그로 심어놓은 시나리오가 실제로 의도한 구체적인
값으로 target annotation까지 도달하고 있는지(`engine_code_changes.md`에 이미
문서화되어 있는 `@Debugging END` 이전 unseeded-read 아티팩트 같은 게 그럴듯한
설명 중 하나지만 미확인임), 아니면 relation/annotation 자체가 설계한 대로
트리거되지 않는 다른 이유가 있는지는 누군가 확인해봐야 함.
