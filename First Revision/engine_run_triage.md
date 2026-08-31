# 엔진 실행 트리아지 — baseline 20개 + phase_reviews 빌드 케이스 전수 실행

**2026-08-31 재구성**: 사용자 요청으로 "지금 안 되는 케이스"를 맨 위로 올리고,
이미 고쳐진 것들은 참고사항으로 문서 하단(§고쳐진 것들)으로 내림. 실행 명령은
전부 `.venv/Scripts/python.exe main.py <case.json>` (cwd = 프로젝트 루트).

**범위**: (A) `evaluation/RQ1/run_all.py`의 `CASE_JSONS` 목록에 있는 baseline 20개
케이스 (논문 RQ2 "20/20 VIOLATED" 결과의 근거). (B) `phase_reviews/` 35케이스
리비전 배치 중 실제 케이스 JSON이 있는 것들.

---

## 지금 안 되는 케이스 (우선순위 순)

### 최우선 — baseline 회귀 (논문 결과에 직접 영향)

| 케이스 | 크래시 지점 | 원인 |
|---|---|---|
| `web3bugs_45_H_01` | `DynamicCFGBuilder.py:1403`, "No CFG node found after line 220" | 같은 파일 안에서 callee(`getBorrowed`, 174행)가 caller(`checkIsOverdue`, 98행)보다 뒤에 선언됨 — 엔진이 같은 컨트랙트 내 전방 참조를 못 품. `phase_reviews/check_callee_order.py`가 이미 있고 이 파일이 baseline 세트에서 유일하게 알려진 위반 사례. 사용자 본인의 미해결 질문("이게 전엔 왜 통과했지?")도 아직 답이 없음 — 함수 순서 재배치 전에 git blame/히스토리 먼저 볼 것.
| `web3bugs_51_H_02` | `Evaluation.py:1188`, `member 'div' is not a recognised global-member` | 체인된 `.add().sub().mul().div()` SafeMath 스타일 호출에서 `.div`가 바인딩된 멤버로 인식 안 됨. VIOLATED→ERROR로 회귀. `struct_defs=`/`enum_defs=` 전달 관련 변경과 연관 있을 걸로 추정되지만 미확정.
| `web3bugs_56_H_02` | `EnhancedSolidityVisitor.py:1013`, `_build_common_clause_dict`에서 `Unknown common clause type: CommonClauseContext` | grammar가 확장되면서 이 dispatch가 새 `CommonClauseContext` 노드를 처리 못 하게 됐거나, 리팩터링으로 처리 범위가 좁아짐. `Parser/Solidity.g4`의 `commonClause`/`postClause` 규칙과 dispatch를 직접 diff 떠봐야 함.

### Group C — user-defined struct 타입을 스코프에서 못 찾음 (3건)

`web3bugs_3_H_04`(`Type 'bond' is not defined... in file level`),
`web3bugs_35_H_08` + `web3bugs_35_H_12`(`Type 'Position' is not defined... in
contract 'ConcentratedLiquidityPool'`, 같은 struct). **2026-08-31 확인**: 처음 가정했던
수정 방향("컨트랙트 → 상속 체인 → 파일 레벨 순회 추가")은 이미 구현되어 있음
(`EnhancedSolidityVisitor.visitUserDefinedType`의 `_find_in_chain`이 `parent_cfgs`까지
재귀로 돎, file-level struct도 별도 체크함) — 그런데도 실패하므로 원인이 다른 데
있음. `web3bugs_3_H_04`는 `contract_cfg`가 애초에 `None`(파일 레벨 컨텍스트에서
타입 resolve)이라 체인 자체를 못 탔을 가능성, `web3bugs_35_H_08`/`35_H_12`는
`contract_cfg`가 있는데도 실패하므로 `parent_cfgs`가 lookup 시점에 아직 안 채워져
있거나(빌드 순서 문제) `Position`이 진짜 상속 관계가 아닌 다른 경로로만 연결돼
있을 가능성. **수정 방향(재검토 필요)**: 실패 케이스에서 `contract_cfg`/
`parent_cfgs`를 직접 찍어보고 원인부터 좁혀야 함 — 단순 체인-워크 추가로는
해결 안 됨. (사용자가 직접 조사 중.)

### Group D — mapping 타입 함수 파라미터 미지원 (2건)

`web3bugs_35_H_11`, `web3bugs_3_H_05` 둘 다 `StaticCFGFactory.py:422`
(`make_param_variable`, `Unsupported typeCategory 'mapping'`). Solidity는
`internal`/`private` 함수에서 mapping 타입 파라미터를 storage 참조로 허용하므로,
파라미터를 caller 쪽 mapping의 alias로 모델링하는 실제 케이스가 필요함(최소한
value 타입의 `TOP`으로라도).

### Group E — 일반 주석(`//` 및 `/** */`)이 ANTLR replay를 깨뜨림 (3건)

`web3bugs_62_H_03`/`web3bugs_62_H_10`은 `//` 한 줄 주석(`ContractAnalyzer.py:1029`,
`current_target_contract`가 `None`인 채로 dict 조회 → `KeyError: None`). 두 파일 다
제거 안 된 일반 주석이 실제로 남아있음을 직접 확인함(`62_H_03.sol:55`의
`// ∆time*rewardTokensPerSecond...`가 ANTLR 에러 메시지와 정확히 일치).
**`web3bugs_192_H_01`도 동일한 최종 예외를 맞는데, 이번에 원인이 새로 확인됨**:
`//` 주석이 아니라 `/** @notice ... */` 형태의 **NatSpec 블록 주석**(`claimGovFees()`
바로 위 등)이 원인으로 보임 — `soltotestjson.py`의 `_comment` 정규식이 `^\s*//`만
체크해서 `/** */`는 못 걸러냄. 이전 트리아지에서 "일반 주석 못 찾음, 트리거 미확인"
으로 남겨뒀던 게 이번에 해소된 것. **2026-08-31 추가 조사**: `web3bugs_62_H_03`
기준으로 끝까지 추적함 — 단순 정규식 누락이 아니라, `soltotestjson.py`의 청크
병합 로직이 안 끝난 `/** ... */` 블록 주석을 `;`나 단독 `{`로 끝나는 줄을 만날
때까지 계속 다음 줄과 합치는데, 그게 하필 **다음 statement(함수 헤더)** 라서
`/** ... */ function claimReward() public lock {` 형태로 주석과 실제 코드가
한 레코드에 뒤엉켜버림. 이게 `current_target_contract` 추적 상태를 깨뜨려서
몇 레코드 뒤(다음 함수 정의)에서야 `KeyError: None`으로 터짐 — 크래시 지점과
실제 원인 지점이 떨어져 있어서 처음엔 안 보였음. **한 줄 정규식 추가로 안 되고
soltotestjson.py의 forward-merge 로직 자체를 손봐야 함** — 아직 미해결.

### Group F — 바인딩된 라이브러리 메소드가 struct 필드 조회로 오인됨 (RESOLVED 2026-08-31)

`web3bugs_70_H_05` — `'decode144' not in struct 'temp_uq144x112_...'`. 원인은
`using FixedPoint for FixedPoint.uq144x112;`(qualified 타입 형태)가
`using_libraries["FixedPoint.uq144x112"]`로 등록되는데, struct 값 자신의 타입 이름은
bare `"uq144x112"`라서 `find_library_function`의 정확 일치 검색이 실패하던 것.
`Utils/CFG.py`의 `find_library_function`(ContractCFG/LibraryCFG 둘 다) 양방향
bare↔qualified 폴백 추가로 해결 — `engine_code_changes.md` RESOLVED 항목 참고.

### Group G — interval `join()`이 type length 다르면 크래시 (3건, 계속 늘어나는 중)

`web3bugs_29_H_11` — `abi.decode` 수정 이후(현재 픽스됨, §고쳐진 것들 참고)
`burnSingle()`의 `if/else` 분기 join에서 `Domain/Interval.py:584`,
`Cannot join intervals of different type lengths`. 어느 변수의 두 분기 값이
비트 폭이 다른지 아직 안 짚었음 — `Utils/Helper.py:354`의 `_merge_by_mode`
호출부에서 `name`이 트레이스에 안 찍혀서, `join()` 호출 직전에 직접 찍어봐야 함.
`abi.decode` 수정 자체가 만든 버그 아님 — 그동안 그 크래시에 막혀서 아예
도달 못 했던 코드에서 처음 드러난 별개 버그.

**2026-08-31 추가**: `web3bugs_52_H_04`/`web3bugs_52_H_34`도 Group B(struct_defs
클로버 버그, §고쳐진 것들 참고) 수정 이후 원래 크래시(`'token0' not in struct
'pairData'`)는 없어졌지만, 똑같이 이 `Domain/Interval.py:584` join 크래시로
다시 멈춤 — `TwapOracle.consult()`가 이전엔 아예 이 코드까지 못 갔던 것.
`29_H_11`과 같은 근본 원인(어떤 변수의 분기별 비트 폭이 다름)일 가능성이 높지만
아직 각각 개별 확인은 안 됨.

### Group I — Group B/F 수정으로 새로 드러난, 별개의 크래시 (2건, 새로 드러남)

Group B/F(§고쳐진 것들 참고)에서 고친 원래 크래시는 없어졌지만, 두 케이스 다
그 밑에 있던 **다른, 사전에 존재하던** 버그에서 다시 멈춤 — 아직 진단만 됨,
수정 안 함.

- **`web3bugs_113_H_05`** — `AttributeError: 'str' object has no attribute
  'multiply'` (`Evaluation.py`의 `evaluate_binary_operator`,
  `leftInterval.multiply(rightInterval)`). `bentoBox.toShare(...)` 같은 외부
  인터페이스 호출의 반환값이 interval이 아니라 symbolic 문자열(`f"symbol_..."`)로
  degrade된 채 산술 연산에 그대로 들어간 것으로 보임 — 어느 호출인지 아직 안 짚음.
- **`web3bugs_70_H_05`** — `ValueError: @IReturn: 'oracle' is not an
  interface-typed variable` (`ContractAnalyzer.process_ireturn`,
  `EnhancedSolidityVisitor.visitIReturnPatternA`). 디버그 시나리오의 `@IReturn`
  줄이 `oracle`을 인터페이스 타입 변수로 기대하는데 실제 변수 타입이 다른 것 —
  케이스 JSON의 디버그 블록 자체를 다시 봐야 할 수도 있음(엔진 버그가 아니라
  케이스 작성 문제일 가능성도 있음, 아직 미확인).

### Group H — `Engine.py` worklist livelock (1건, 진단만 됨)

`web3bugs_79_H_02` — `faulthandler.dump_traceback_later`로 실제 스택 확인함:
`_run_worklist`(`Interpreter/Engine.py:829`) 안에서 멈춤. `deque` 기반 worklist가
방문 안 된 predecessor 있는 `join_point_node`를 계속 재큐잉하는데, 그 predecessor가
이 노드 자신의 처리 결과로만 reachable해지는 구조라면 영원히 재큐잉만 반복함(진짜
livelock, 시간을 줘도 안 풀림). **수정 방향, 미확정**: (a) 재큐잉 횟수 제한 후
현재까지 방문된 predecessor만으로 강제 처리, 또는 (b) SCC-aware/reverse-postorder
스케줄링. `currentPhase()`/`_atPhase()`의 실제 CFG 엣지를 직접 추적해야 확정 가능.

### 단발성 (각각 독립적인 원인)

- **`web3bugs_52_H_23`** — `EnhancedSolidityVisitor.py:771`, `Invalid key type
  in mapping: IERC20`. mapping key 타입 체크가 elementary만 허용하는 하드코딩된
  화이트리스트라, contract/interface(→address)/enum(→정수) 타입을 못 받음.
- **`web3bugs_83_H_01`** — `Evaluation.py:1959`, `AttributeError: 'NoneType'
  object has no attribute 'context'`. `poolInfo[1]`의 `struct_defs=`/`enum_defs=`가
  array 분기에서 전달 안 됨 — mapping 분기의 처리 방식(`parent_cfgs` 포함)을
  array 분기에도 그대로 적용하면 될 것으로 보임(Group B와 같은 계열).
- **`web3bugs_42_H_01`** — `ContractAnalyzer.py:989`, `Modifier 'updateDebt' is
  not defined`. modifier는 실제로 파일에 선언돼 있음 — `case_progress.md`가 이후
  relation 변경 후 케이스 JSON을 재빌드 안 했다고 명시함. 깨끗한 엔진 버그 신호
  아님. **재진단 전에 현재 contraction에서 케이스 JSON부터 재빌드할 것.** (재빌드
  해도 그 밑에 있는 진짜 블로커 — cast 없는 chained interface 호출이 struct 반환,
  `'denominator' not in struct 'lf'` — 는 여전히 남아있을 것으로 예상.)

### 크래시는 안 나지만 verdict가 기대와 다름 (엔진 크래시 아님, 결과 정확성 문제)

- **`web3bugs_59_H_04`** — SATISFIED. `analysis.md`의 계산값은 buggy=2000 vs
  intended=6666로 명백한 violation을 예측함.
- **`web3bugs_70_H_04`** — VIOLATED가 아니라 WARNING. 꼭 틀렸다는 건 아님(Entry가
  붙은 다중-statement 관계는 Warning이 정당할 수 있음), 다만 기대 결과와 독립
  검증은 안 됐음.

  두 건 다 더 추적 안 했음 — 디버그 시나리오가 실제로 target annotation까지
  의도한 구체값으로 도달하는지, 아니면 relation/annotation 자체가 설계대로
  트리거 안 되는 다른 이유가 있는지 확인 필요. (참고: `web3bugs_16_H_06`도 원래
  이 목록에 있었지만 아래 §고쳐진 것들에서 설명하는 `_preds` 버그 수정으로
  이제 정상적인 WARNING을 내서 목록에서 제거함.)

---

## 참고: 이번 세션에 고쳐진 것들

### During/Post 어노테이션 배치 컨벤션 (확정, 20개 baseline과 대조 검증됨)

- **`@During`**: 배열 위치 = 코드 전체 처리 끝난 뒤, `@Debugging BEGIN` 바로 앞.
  `startLine` 태그 = 체크하는 대상 statement 자신의 줄(뒤 statement를 감시하는
  `changed(...)` 형태면 그 다음 statement의 줄). 기존 코드 줄에 붙는 "inline"
  경로를 타서 라인 밀기가 안 일어남.
- **`@Post`**: 배열 위치는 During과 동일(코드 전체 뒤, Debugging BEGIN 앞)이지만
  `startLine` 태그는 **자기 자신의 원래(안 밀린) 줄** — target statement의 줄이
  아님. 원본 `web3bugs_16_H_06.json`과 baseline 5개 케이스 전부와 대조해서 확정.
  실제로 밀기(`_insert_lines`) 경로를 탐 — During과 반대.
- **디버그 블록**: `@Debugging BEGIN`의 `startLine` = 대상 함수 헤더의 (가짜)
  endLine, 즉 함수 진입 직후(첫 실제 statement 앞). 이후 각 디버그 라인은 순차
  +1. baseline 5개 케이스(WANGMI/Nokon/HIT/`101_H_01`/`5_H_07`) 전부와 대조해서
  확정 — 이전에 이번 세션이 썼던 "코드 전체 뒤에 순차 배치" 컨벤션은 틀렸었음.

이 세 가지를 적용해서 `numscout_EthereumGod`/`web3bugs_31_H_01`/
`web3bugs_112_H_01`(Group 1a였던 것)과 `web3bugs_16_H_06`/`web3bugs_29_H_08`이
전부 크래시 없이, 기대한 verdict를 냄.

### `main.py`의 During/Post 중복 `update_code` 호출 제거

`simulate_inputs` 루프 맨 위에서 모든 레코드에 대해 이미 `sa.update_code(...)`를
호출하는데, `@During`/`@Post` 분기에서 같은 레코드에 대해 한 번 더 호출하고
있었음. 여러 줄에 걸친 statement 뒤에 During이 오는 경우, 첫 호출이 (버퍼가
아직 안 채워져서) 밀기 경로로 잘못 빠졌다가 두 번째 호출 시점엔 이미 뒤쪽이
다 밀려버린 상태라 원래의 Group 1a 크래시로 이어졌었음.

### `SolidityAnalyzer._is_during_inline`이 `line_info`도 확인하도록 수정

여러 줄에 걸친 statement는 실제 텍스트가 span의 끝(`write_start`)에 쓰이고
시작 줄의 `full_code_lines`는 빈 placeholder로 남음 — 반면 CFG 노드는
`current_start_line`(그 statement 선언 시점의 시작 줄) 기준으로 등록됨.
`full_code_lines`만 보면 이런 경우 "비어있다"고 오판해서 불필요한 밀기가
일어났었음 — `line_info`에 실제 CFG 노드가 있는지도 함께 확인하도록 수정.

### `GuardianVerificationEngine._preds`가 잘못된 exit 노드를 조회하던 버그 (진짜 엔진 버그, `web3bugs_16_H_06` 근본 원인)

`return` statement는 일반 `fn_cfg.get_exit_node()`가 아니라 별도의
`fn_cfg.get_return_exit_node()`에 엣지를 연결함(`DynamicCFGBuilder.
build_return_statement`). 그런데 `_preds`(→`_exit_env`→ 대부분의
`verify_post_*` 검증 함수가 거침)는 일반 `get_exit_node()`를 직접 조회하고
있어서, return이 있는 함수는 predecessor가 0개로 나오고 `related_variables`
(전역/state 이름만 있는 generic set)로 폴백 — 로컬 변수가 하나도 없어서
"not declared" 에러가 났음. 이미 존재하던 올바른 셀렉터
`_get_post_exit_node`(return_vals 있으면 return_exit, 없으면 일반 exit_node)로
교체해서 해결. `web3bugs_16_H_06`이 정확한 값(`15000000000000000000000`)으로
WARNING을 내는 것으로 검증됨(WARNING인 이유는 `PRBMathUD60x18.mul`의 rounding
분기를 엔진이 정밀하게 못 따라가서 — 이건 정당한 결과).

### `EnhancedSolidityVisitor.visitGlobalVarAddressBalance`의 `ctx.identifier()` 리스트 버그

`@GlobalVar address(X).balance = ...` 문법 규칙에 `identifier`가 두 번 나오는데
(`address(X)`의 X, `.balance`의 balance) `ctx.identifier()`를 인덱스 없이 호출해서
리스트를 단일 노드처럼 다루다 크래시. `ctx.identifier(0)`으로 수정.

### Group 2 — `abi.decode`/`abi.encode*` 엔진 시맨틱스 부재 (RESOLVED)

`EnhancedSolidityVisitor.visitTypeNameExp`가 완전 stub이라 `abi.decode`의
타입-리스트가 파싱 단계부터 `None`이 되던 걸 고쳐서 타입 이름을 실제로 담은
`Expression`을 반환하게 함. `Evaluation.evaluate_function_call_context`에
`abi.` 호출을 가로채는 분기를 추가해서 `abi.decode`는 타입별 `TOP`(단일/리스트),
`abi.encode*`는 `BytesSet.top()`을 반환 — `.call()`/`.staticcall()`이 이미
크래시 없이 TOP으로 degrade하던 것과 동일한 패턴. `web3bugs_29_H_08`이 크래시
없이 WARNING을 냄. `web3bugs_29_H_11`은 `abi.decode` 3건은 다 통과하지만
그 덕에 처음 도달한 곳에서 Group G(interval join)를 새로 만남 — `abi` 수정
자체의 문제는 아님.

### baseline 20개 / 이번 세션 빌드 15개 회귀 없음

`evaluation/RQ1/run_all.py` 재실행 결과 이번 세션 내내 17 VIOLATED / 3 ERROR로
동일(3개는 위 "baseline 회귀" 항목, 전부 사전에 알려진/독립적인 이슈). 이번
세션에 다시 만든 15개 케이스(`numscout_EthereumGod`, `web3bugs_31_H_01`,
`web3bugs_112_H_01`, `web3bugs_113_H_05`, `web3bugs_16_H_06`,
`web3bugs_192_H_01`, `web3bugs_29_H_08`, `web3bugs_29_H_11`, `web3bugs_35_H_08`,
`web3bugs_35_H_12`, `web3bugs_52_H_23`, `web3bugs_62_H_03`, `web3bugs_62_H_10`,
`web3bugs_65_H_01`, `web3bugs_79_H_02`)도 전부 재실행해서 위 "지금 안 되는
케이스" 섹션에 반영된 대로 일관됨.

### Group B, Group F, `365.25 days` 리터럴 — 버그 자체는 RESOLVED (2026-08-31, 같은 세션 후반부)

**주의**: 아래는 "이 버그는 고쳤다"는 기록이지 "이 케이스들이 이제 통과한다"는 뜻이
아님. `113_H_05`/`52_H_04`/`52_H_34`/`70_H_05` 4건은 여전히 안 됨 — 원래
크래시는 없어졌지만 각각 다른 사전-존재 버그로 다시 멈춤. 새 크래시는 위
"지금 안 되는 케이스" 섹션의 Group G/Group I에 반영돼 있음. 완전히 통과하게 된
건 `65_H_01` 하나뿐(그리고 이 라운드 이전에 이미 고쳐졌던 `29_H_08`/`16_H_06`
등).

- **Group B**(`113_H_05`/`52_H_04`/`52_H_34`, struct 필드 누락): 진짜 원인은
  `ContractAnalyzer._create_variable_object`의 struct_defs 전달 누락이 아니라,
  `Interpreter/Semantics/{Update.py,Evaluation.py,DebugInitializer.py}`에 흩어진
  13곳의 `if not X.struct_defs or not X.enum_defs: X.struct_defs = ccf.structDefs`
  패턴이었음 — `or` 조건 때문에 `enum_defs`만 정상적으로 비어있어도(예: enum
  멤버가 없는 struct) 이미 올바르게 채워진 `struct_defs`를 현재 컨트랙트 자체
  구조체만 담은 좁은 dict로 통째로 덮어씀. `ContractAnalyzer.get_full_struct_enum_defs()`
  헬퍼를 새로 만들고 13곳 전부 "없는 것만 채우기"(`{**전체, **기존}`)로 교체.
  덤으로 `ArrayVariable`(state array-of-struct)과 중첩 mapping/array 생성 경로에도
  같은 종류의 struct_defs 전달 누락이 있어서 같이 고침. 상세: `engine_code_changes.md`.
- **Group F**(`70_H_05`, 라이브러리 메소드 오인): `using FixedPoint for
  FixedPoint.uq144x112;`(qualified 타입)로 등록된 키와 struct 값의 bare 타입
  이름이 안 맞아서 실패하던 것 — `Utils/CFG.py`의 `find_library_function` 양쪽
  구현에 bare↔qualified 폴백 추가.
- **`web3bugs_65_H_01`**(`365.25 days`): `visitLiteralSubDenomination`이
  `int(num_txt, 0)`만 받고 소수 리터럴을 거부하던 것 — `Fraction`으로 파싱 후
  결과가 정수로 안 떨어지면 에러, 떨어지면(예: `365.25*86400=31557600`) 정상
  리터럴로 인정하도록 수정 — 실제 solc 시맨틱스와 동일.

세 건 다 baseline 20개(`evaluation/RQ1/run_all.py`, 17 VIOLATED/3 ERROR 유지)와
이번 세션에 다시 만든 15개 케이스 전체 재실행으로 회귀 없음 확인.
