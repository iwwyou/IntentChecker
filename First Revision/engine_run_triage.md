# 엔진 실행 트리아지 — baseline 20개 + phase_reviews 빌드 케이스 전수 실행

**2026-08-31 재구성**: 사용자 요청으로 "지금 안 되는 케이스"를 맨 위로 올리고,
이미 고쳐진 것들은 참고사항으로 문서 하단(§고쳐진 것들)으로 내림. 실행 명령은
전부 `.venv/Scripts/python.exe main.py <case.json>` (cwd = 프로젝트 루트).

**범위**: (A) `evaluation/RQ1/run_all.py`의 `CASE_JSONS` 목록에 있는 baseline 20개
케이스 (논문 RQ2 "20/20 VIOLATED" 결과의 근거). (B) `phase_reviews/` 35케이스
리비전 배치 중 실제 케이스 JSON이 있는 것들.

---

## 지금 안 되는 케이스 (우선순위 순) — 총 20건 (2026-09-01 기준)

baseline 회귀 3 + Group D 2 + Group G 3 + Group H 1 + 단발성 9 + verdict 불일치
2 = 20건. (해결된 그룹은 확인 즉시 이 섹션에서 내리고 §고쳐진 것들로 옮기는
걸 원칙으로 함 — Group C/E/F는 전부 §고쳐진 것들로 이동 완료. 다만 그 수정
과정에서 새로 드러난 크래시들은 기존 그룹에 안 맞으면 전부 "단발성"으로
재분류함 — `113_H_05`/`70_H_05`(구 Group I), `35_H_08`/`35_H_12`(구 Group J).
`62_H_10`/`192_H_01`은 크래시는 없어졌지만 디버그 시나리오 자체가 잘못된
함수를 가리키고 있어서 검증이 실제로 실행되지 않는 걸 확인해 단발성에 새로
추가함 — 그래서 18 → 20으로 늘어남. 이 숫자가 바뀌면 이 줄도 같이 업데이트할 것.)

### 최우선 — baseline 회귀 (논문 결과에 직접 영향)

| 케이스 | 크래시 지점 | 원인 |
|---|---|---|
| `web3bugs_45_H_01` | `DynamicCFGBuilder.py:1403`, "No CFG node found after line 220". **크래시 레코드(2026-09-01 재확인)**: 케이스 JSON `startLine 220`, `require(borrowBalanceView(msg.sender) + amount + fee <= maxBorrow, ...)` | 같은 파일 안에서 callee(`getBorrowed`, 174행)가 caller(`checkIsOverdue`, 98행)보다 뒤에 선언됨 — 엔진이 같은 컨트랙트 내 전방 참조를 못 품(`web3bugs_35_H_08`/`35_H_12`의 struct forward-reference 문제와 같은 계열 — 함수든 타입이든 "선언 전 사용"을 못 품). `phase_reviews/check_callee_order.py`가 이미 있고 이 파일이 baseline 세트에서 유일하게 알려진 위반 사례. 사용자 본인의 미해결 질문("이게 전엔 왜 통과했지?")도 아직 답이 없음 — 함수 순서 재배치 전에 git blame/히스토리 먼저 볼 것.
| `web3bugs_51_H_02` | `Evaluation.py:1188`, `member 'div' is not a recognised global-member`. **크래시 레코드(2026-09-01 재확인)**: 케이스 JSON `startLine 123`, `return self.originalPrecisionMultipliers[0].mul(initialTargetPricePrecise).div(WEI_UNIT);` | 체인된 `.add().sub().mul().div()` SafeMath 스타일 호출에서 `.div`가 바인딩된 멤버로 인식 안 됨. VIOLATED→ERROR로 회귀. `struct_defs=`/`enum_defs=` 전달 관련 변경과 연관 있을 걸로 추정되지만 미확정.
| `web3bugs_56_H_02` | `EnhancedSolidityVisitor.py:1013`, `_build_common_clause_dict`에서 `Unknown common clause type: CommonClauseContext`. **크래시 레코드(2026-09-01 재확인)**: 케이스 JSON `startLine 46`, `// @Post _self.totalCredit(Entry <= Exit)` | grammar가 확장되면서 이 dispatch가 새 `CommonClauseContext` 노드를 처리 못 하게 됐거나, 리팩터링으로 처리 범위가 좁아짐. `Parser/Solidity.g4`의 `commonClause`/`postClause` 규칙과 dispatch를 직접 diff 떠봐야 함. (참고: `struct Data`가 `using CDP for Data;`보다 뒤에 정의돼 있는 유사 forward-reference 패턴도 이 파일에서 발견됐지만, 이미 이 별개의 grammar-dispatch 버그를 갖고 있는 baseline 케이스라 손대지 않음 — §고쳐진 것들의 Group C 항목 참고.)

### Group D — mapping 타입 함수 파라미터 미지원 (2건)

`web3bugs_35_H_11`, `web3bugs_3_H_05` 둘 다 `StaticCFGFactory.py:422`
(`make_param_variable`, `Unsupported typeCategory 'mapping'`). Solidity는
`internal`/`private` 함수에서 mapping 타입 파라미터를 storage 참조로 허용하므로,
파라미터를 caller 쪽 mapping의 alias로 모델링하는 실제 케이스가 필요함(최소한
value 타입의 `TOP`으로라도). **크래시 레코드(2026-09-01 재확인)**:
- `web3bugs_35_H_11` — 케이스 JSON `startLine 13-21`, `function cross(
  mapping(int24 => Tick) storage ticks, ... )`.
- `web3bugs_3_H_05` — 케이스 JSON `startLine 22-28`, `function yieldTokenInPeg(
  address token, uint256 amount, mapping(address => uint256) storage
  yieldQuotientsFP, ... )`.

### Group G — interval `join()`이 type length 다르면 크래시 (3건)

`web3bugs_29_H_11` — `abi.decode` 수정 이후(현재 픽스됨, §고쳐진 것들 참고)
`burnSingle()`의 `if/else` 분기 join에서 `Domain/Interval.py:584`,
`Cannot join intervals of different type lengths`. **크래시 변수(2026-09-01,
`Utils/Helper.py:354`에 임시 프로브 넣어서 확인 후 원복함)**: 실패하는 변수
이름은 `_blockTimestampLast`. **크래시 레코드**: 케이스 JSON `startLine
128-129`, `if (blockTimestamp != _blockTimestampLast && _reserve0 != 0 &&
_reserve1 != 0) {` — `_update()` 함수 안, TWAP 갱신 분기의 `if`문. `abi.decode`
수정 자체가 만든 버그 아님 — 그동안 그 크래시에 막혀서 아예 도달 못 했던
코드에서 처음 드러난 별개 버그. 주석 정리 전/후로 에러 메시지·크래시 지점
동일 — 주석 오염과 무관한 순수 엔진 버그로 재확인됨.

`web3bugs_52_H_04`/`web3bugs_52_H_34` — Group B(struct_defs 클로버 버그,
§고쳐진 것들 참고) 수정 이후 원래 크래시(`'token0' not in struct 'pairData'`)는
없어졌지만, 똑같이 `Domain/Interval.py:584` join 크래시로 다시 멈춤.
**2026-09-01 추가 확인, 근본 원인 확정**: 처음엔 `TwapOracle.consult()`의
`if (token == pairData.token0)` 분기가 원인일 거라 추정했었는데, 임시 프로브로
직접 확인해보니 **실패 변수는 `roundID`**(추정과 다름) — 케이스 JSON
`startLine 37-44`의 `( uint80 roundID, int256 price, , , uint80
answeredInRound ) = AggregatorV3Interface(...).latestRoundData();`(Chainlink
튜플 언패킹)에서 온 `uint80` 변수이고, `startLine 46-49`의 `require(
answeredInRound >= roundID, "...stale chainlink price" );`에서 join이
일어남 — `roundID`가 한쪽 분기에서 선언된 `uint80` 폭을 못 지키고 다른 쪽
분기에서 다른 폭(디폴트 `uint256` TOP 등)으로 남는 것으로 보임. `29_H_11`과
크래시 시그니처는 같지만 **근본 원인은 다름**(변수도 다르고, 하나는 `if`
분기 join, 하나는 튜플 언패킹 결과의 폭 불일치) — 공통 수정으로 한 번에 안
풀릴 가능성이 큼, 두 부류를 따로 취급할 것.

### Group H — `Engine.py` worklist livelock (1건, 진단만 됨)

`web3bugs_79_H_02` — `faulthandler.dump_traceback_later`로 실제 스택 확인함:
`_run_worklist`(`Interpreter/Engine.py:829`) 안에서 멈춤. `deque` 기반 worklist가
방문 안 된 predecessor 있는 `join_point_node`를 계속 재큐잉하는데, 그 predecessor가
이 노드 자신의 처리 결과로만 reachable해지는 구조라면 영원히 재큐잉만 반복함(진짜
livelock, 시간을 줘도 안 풀림 — 크래시가 아니라 무한루프라 "실패 레코드"
자체가 없음, CFG 노드 단위 문제). **수정 방향, 미확정**: (a) 재큐잉 횟수 제한 후
현재까지 방문된 predecessor만으로 강제 처리, 또는 (b) SCC-aware/reverse-postorder
스케줄링. `currentPhase()`/`_atPhase()`의 실제 CFG 엣지를 직접 추적해야 확정 가능.

### 단발성 (각각 독립적인 원인 — Group C/B/F 수정으로 새로 드러난 것들도 여기로 재분류)

- **`web3bugs_52_H_23`** — `EnhancedSolidityVisitor.py:771`, `Invalid key type
  in mapping: IERC20`. mapping key 타입 체크가 elementary만 허용하는 하드코딩된
  화이트리스트라, contract/interface(→address)/enum(→정수) 타입을 못 받음.
  **크래시 레코드**: 케이스 JSON `startLine 21`, `mapping(IERC20 => bool)
  public supported;` — state 변수 선언 자체에서 바로 실패(파싱 단계). 주석
  정리 전/후로 에러 메시지·크래시 지점 동일 — 순수 엔진 버그.
- **`web3bugs_83_H_01`** — `Evaluation.py:1959`, `AttributeError: 'NoneType'
  object has no attribute 'context'`. `poolInfo[1]`의 `struct_defs=`/`enum_defs=`가
  array 분기에서 전달 안 됨 — mapping 분기의 처리 방식(`parent_cfgs` 포함)을
  array 분기에도 그대로 적용하면 될 것으로 보임(Group B와 같은 계열).
  **크래시 레코드(2026-09-01 재확인)**: 케이스 JSON `startLine 28-34`,
  `depositToken: IERC20(_token), allocPoint: _allocationPoints, ... })` —
  struct-literal push 표현식.
- **`web3bugs_42_H_01`** — `ContractAnalyzer.py:989`, `Modifier 'updateDebt' is
  not defined`. modifier는 실제로 파일에 선언돼 있음 — `case_progress.md`가 이후
  relation 변경 후 케이스 JSON을 재빌드 안 했다고 명시함. 깨끗한 엔진 버그 신호
  아님. **크래시 레코드(2026-09-01 재확인)**: 케이스 JSON `startLine 22-27`,
  `function borrow( uint256 _id, uint256 _amount, bytes memory _data ) public
  override updateDebt(_id) {`. **재진단 전에 현재 contraction에서 케이스
  JSON부터 재빌드할 것.** (재빌드해도 그 밑에 있는 진짜 블로커 — cast 없는
  chained interface 호출이 struct 반환, `'denominator' not in struct 'lf'`
  — 는 여전히 남아있을 것으로 예상.)
- **`web3bugs_113_H_05`**(구 Group I) — `AttributeError: 'str' object has no
  attribute 'multiply'` (`Evaluation.py`의 `evaluate_binary_operator`,
  `leftInterval.multiply(rightInterval)`). `bentoBox.toShare(...)` 같은 외부
  인터페이스 호출의 반환값이 interval이 아니라 symbolic 문자열(`f"symbol_..."`)로
  degrade된 채 산술 연산에 그대로 들어간 것으로 보임 — 어느 호출인지 아직 안 짚음.
  Group B(struct_defs 클로버 버그, §고쳐진 것들 참고) 수정으로 원래 크래시가
  없어지고 도달한, 별개의 사전-존재 버그. **크래시 레코드(2026-09-01 재확인)**:
  케이스 JSON `startLine 66`, `uint256 openFeeShare = (totalShare *
  OPEN_FEE_BPS) / BPS;`.
- **`web3bugs_70_H_05`**(구 Group I) — `ValueError: @IReturn: 'oracle' is not
  an interface-typed variable` (`ContractAnalyzer.process_ireturn`,
  `EnhancedSolidityVisitor.visitIReturnPatternA`). 디버그 시나리오의 `@IReturn`
  줄이 `oracle`을 인터페이스 타입 변수로 기대하는데 실제 변수 타입이 다른 것 —
  Group F(라이브러리 메소드 오인, §고쳐진 것들 참고) 수정으로 원래 크래시가
  없어지고 도달함. 케이스 JSON의 디버그 블록 자체를 다시 봐야 할 수도 있음
  (엔진 버그가 아니라 케이스 작성 문제일 가능성 있음 — `62_H_10`/`192_H_01`
  에서 확인된 "`@Debugging BEGIN`이 엉뚱한 함수를 가리킴" 패턴과 비슷할 수
  있음, 아직 미확인). **크래시 레코드**: 케이스 JSON `startLine 39`,
  `// @IReturn oracle.latestRoundData()[0] = [1, 1]` — `@Debugging BEGIN`
  (L33) 블록의 첫 `@IReturn` 라인. 주석 정리 전/후로 에러 메시지·크래시 지점
  동일.
- **`web3bugs_35_H_08`**(구 Group J) / **`web3bugs_35_H_12`**(구 Group J) —
  `Domain/Variable.py:282`, `ArrayVariable._is_abstractable`,
  `AttributeError: 'NoneType' object has no attribute 'startswith'`.
  `Evaluation.py:544`의 `evaluate_new_expression_context`가
  `sol_t.arrayBaseType`을 `_is_abstractable`에 넘기는데, 배열 원소 타입이
  `IPool.TokenAmount`처럼 인터페이스에 qualified된(네임스페이스 붙은) struct
  타입이라 `arrayBaseType`이 제대로 resolve 안 되고 `None`으로 남은 것으로
  보임 — 아직 진단만 됨, 수정 안 함. Group C(struct forward-reference, §고쳐진
  것들 참고) 수정으로 원래 크래시가 없어지고 도달한, 별개의 버그. **크래시
  레코드**: `35_H_08` 케이스 JSON `startLine 165`, `35_H_12` `startLine 168`,
  둘 다 `withdrawnAmounts = new IPool.TokenAmount[](2);`.
- **`web3bugs_62_H_10`** / **`web3bugs_192_H_01`** — 크래시 없음(원래 크래시는
  주석 정리로 해결, §고쳐진 것들 참고), 하지만 **디버그 시나리오의
  `@Debugging BEGIN` target line이 애초에(주석 정리 전부터) 엉뚱한 함수를
  가리키고 있어서 검증이 실제로 실행되지 않음**을 확인 — 케이스 작성 오류,
  엔진 버그 아님. 실행하면 `[WARNING] Cannot resolve LHS expression`만 뜨고
  조용히 끝남(INTENT WARNING/VIOLATION 없음 — `run_all.py` 집계 기준으로는
  잘못 SATISFIED로 잡힐 위험):
  - `62_H_10` — `@Debugging BEGIN`이 `creatorClaimSoldTokens(address
    destination)`가 아니라 **`lockInternal()`의 진입점**을 가리킴.
  - `192_H_01` — `@Debugging BEGIN`이 `extendLock(uint _id, uint _amount,
    uint _period)`가 아니라 **`claim(uint256 _id)`의 진입점**을 가리킴.

  **수정 방향(미착수)**: 케이스 JSON에서 `@Debugging BEGIN`/`@LocalVar`/
  `@StateVar`/`@GlobalVar`/`@Post` 블록 전체를 올바른 함수(각각
  `creatorClaimSoldTokens`/`extendLock`)의 진입점으로 재배치해야 함 — 이번
  세션에서는 손 안 댐.

### 크래시는 안 나지만 verdict가 기대와 다름 (엔진 크래시 아님, 결과 정확성 문제)

- **`web3bugs_59_H_04`** — SATISFIED. `analysis.md`의 계산값은 buggy=2000 vs
  intended=6666로 명백한 violation을 예측함.
- **`web3bugs_70_H_04`** — VIOLATED가 아니라 WARNING. 꼭 틀렸다는 건 아님(Entry가
  붙은 다중-statement 관계는 Warning이 정당할 수 있음), 다만 기대 결과와 독립
  검증은 안 됐음.

  두 건 다 더 추적 안 했음(크래시가 아니라 "완주는 하는데 값이 이상함" 부류라
  위의 "크래시 레코드" 같은 단일 라인 지목이 잘 안 맞음) — 디버그 시나리오가
  실제로 target annotation까지 의도한 구체값으로 도달하는지, 아니면
  relation/annotation 자체가 설계대로 트리거 안 되는 다른 이유가 있는지 확인
  필요. (참고: `web3bugs_16_H_06`도 원래 이 목록에 있었지만 아래 §고쳐진
  것들에서 설명하는 `_preds` 버그 수정으로 이제 정상적인 WARNING을 내서
  목록에서 제거함.)

---

## 참고: 이번 세션에 고쳐진 것들

### Group C — struct 정의를 사용 지점보다 앞으로 재배치 (2026-09-01, 데이터 정리/워크어라운드 — 엔진 코드 변경 없음)

사용자가 `web3bugs_35_H_08`의 케이스 JSON을 보고 `struct Position {...}`이
그걸 참조하는 `mapping(... => Position) ...` 선언보다 **뒤에** 와 있다는 걸
지적, 앞으로 옮길 것과 비슷한 케이스도 같이 처리할 것을 요청. 전체
`evaluation/RQ1/cases/**/*.json`을 스캔(각 `struct X {` 정의 레코드보다 앞에
`\bX\b`를 쓰는 레코드가 있는지 검사)해서 정확히 같은 패턴인 `web3bugs_35_H_12`
하나를 더 찾음(`web3bugs_56_H_02`도 `using CDP for Data;`가 `struct Data`보다
앞서는 유사 패턴이 걸렸지만, 이건 이미 별개의 알려진 baseline 회귀
버그(`_build_common_clause_dict`의 grammar dispatch 문제)를 갖고 있고
baseline 20개 세트 소속이라 손대지 않음 — mapping 사용과 `using` 디렉티브는
엔진 처리 경로가 다를 수 있어서, 별도 확인 없이 같이 옮기는 건 리스크가 큼).

**작업 방식**: `struct Position {...}` 블록(스켈레톤 + 필드 3개, 총 4개 레코드)과
그 앞에 있던 `mapping(...) public positions;` 레코드의 순서를 물리적으로
스왑 — struct가 먼저, mapping이 나중에 오도록. 케이스 JSON의 `startLine`/
`endLine`을 다시 계산할 때, 처음엔 주석 제거 때 썼던 "삭제 레코드는 skip,
나머지는 순차 누적 shift" 방식을 그대로 재사용하려다가 실패함 — 이번엔 삭제가
아니라 재배치라서, `_insert_lines`가 실제로 어떤 순서로 재생되느냐 자체가
달라지고, 안 건드린 앞쪽 레코드(인덱스 0~32)까지 전부 밀리는 회귀가 남(자동
스크립트의 anchor 계산 로직 버그로 확인). 결국 `_insert_lines`의 "닫는
중괄호 앞에 통계문이 하나씩 삽입되면서 그 중괄호가 계속 뒤로 밀리는" 시맨틱스를
그대로 손으로 재현해서(스켈레톤 삽입 → 필드마다 중괄호 앞 삽입 → 남는 blank/
mapping은 append) 정확한 새 좌표를 계산하고, **윈도우 밖 레코드는 원본과
바이트 단위로 동일함을 스크립트로 검증**한 뒤 적용함. contraction `.sol`
파일도 같은 순서로 물리적으로 재배치.

**결과**: 두 케이스 다 원래 크래시(`Type 'Position' is not defined... in
contract 'ConcentratedLiquidityPool'`)는 사라짐 — 하지만 곧바로 새로운
별개 크래시(`AttributeError: 'NoneType' object has no attribute 'startswith'`,
`Domain/Variable.py:282`의 `_is_abstractable`, `new IPool.TokenAmount[](2)`
같은 qualified struct 타입의 `new` 배열 표현식에서 발생)로 다시 멈춤 —
Group C 크래시에 막혀 그동안 도달 못 했던 코드에서 처음 드러난 것. 이번에도
"버그 고침(정확히는 데이터 정리로 우회) ≠ 케이스 통과" — 이 두 건은 여전히
"지금 안 되는 케이스"에 있고, 기존 그룹에 안 맞는 새 크래시라 위 §단발성으로
재분류함. baseline 20개 세트에 없는 케이스라 회귀 리스크는 없음(확인함).

**엔진 자체의 forward-reference 미지원은 안 고침**: 이건 어디까지나 이 두
케이스의 소스 순서를 엔진이 처리 가능한 순서로 맞춰준 것뿐 — 엔진이 "같은
컨트랙트 안에서 나중에 선언된 struct/타입을 먼저 참조하는" 진짜 valid
Solidity 코드를 일반적으로 처리 못 하는 근본 한계는 그대로 남아있음(baseline
`web3bugs_45_H_01`의 callee-순서 문제와 같은 계열의 제약 — 함수든 타입이든
"선언 전 사용"을 엔진이 못 품).

### 케이스 JSON/contraction 파일에 섞여있던 일반 주석 제거 (2026-09-01, 데이터 정리 — 엔진 코드 변경 없음)

사용자가 `web3bugs_3_H_04`의 케이스 JSON/contraction `.sol`에 intent(`@During`/
`@Post`)·debug(`@Debugging`/`@LocalVar`/`@StateVar`/`@GlobalVar`/`@IReturn`)
어노테이션이 아닌 일반 설명 주석(예: `// issuer => holder => bond record`)이
섞여있는 걸 지적, 제거를 요청. 전체 `evaluation/RQ1/cases/**/*.json`과
`target_contracts_contraction/*.sol`을 스캔해서 같은 문제가 있는 케이스를
모두 찾아 정리함.

**작업 방식**: 케이스 JSON의 `startLine`/`endLine`은 절대 줄 번호가 아니라
`main.py`의 `simulate_inputs` → `sa.update_code` → `_insert_lines`가 순서대로
재생하는 **incremental 버퍼 안에서의 현재 위치**임(각 레코드가 실행되는
시점의 버퍼 상태 기준) — 그래서 주석 레코드를 단순히 배열에서 삭제하는 것만
으로는 안 되고, 그 뒤(정확히는 버퍼 상 그 위치 이후)에 오는 모든 레코드의
좌표를 다시 계산해야 함. 처음엔 순서대로 누적 shift를 빼는 방식으로 했다가
`web3bugs_70_H_05`에서 회귀가 남 — `@Debugging BEGIN` 블록이 코드 뒷부분보다
**앞쪽 줄**을 다시 가리키는 경우(디버그 스냅샷이 함수 시작 직후를 가리킴)가
있어서, 시퀀스 순서 기준 누적 shift는 틀린 결과를 냄. 최종적으로는 원본
전체 시퀀스를 실제 `_insert_lines`와 동일한 방식으로 시뮬레이션(각 삽입이
현재 상태의 어느 위치에서 일어나는지 슬롯 단위로 추적)하고, 제거 대상
레코드는 old-buffer에만 반영하고 new-buffer에는 반영하지 않은 채, 남는
레코드는 old-buffer상 자기 위치 기준으로 "가장 가까운, 아직 살아있는 다음
슬롯"에 anchor해서 new-buffer 위치를 구하는 방식(anchor-based replay)으로
정확하게 재계산함. 각 케이스를 정리 전/후로 실행해서 에러 메시지가 동일하게
유지되는지(회귀 없음) 또는 크래시가 아예 사라지는지 확인함.

**정리한 케이스**(케이스 JSON + contraction `.sol` 둘 다, `web3bugs_3_H_05`는
contraction만 — 그 케이스 JSON엔 애초에 주석이 없었음):

| 케이스 | 제거/정리한 것 | 정리 후 결과 |
|---|---|---|
| `web3bugs_3_H_04` | 일반 주석 8줄 | **크래시 사라짐** — WARNING까지 도달(§Group C 참고, `Type 'bond' is not defined`는 주석 오염이 원인이었음) |
| `web3bugs_29_H_11` | `// @dev ...` NatSpec 한 줄 주석 7개 + 설명 주석 1줄 (총 8줄) | 크래시 지점/메시지 동일(§Group G, 별개의 진짜 엔진 버그) |
| `web3bugs_52_H_23` | 일반 주석 1줄 + `// gas savings` 인라인 주석(같은 줄에 코드와 병합돼 있던 것, 줄 수 변화 없음) | 크래시 지점/메시지 동일(§단발성, 별개의 진짜 엔진 버그) |
| `web3bugs_62_H_03` | 일반 주석 5줄 + `/** @dev ... */` NatSpec 블록 주석(함수 헤더와 한 레코드로 뒤엉켜있던 것) | **크래시 사라짐** |
| `web3bugs_62_H_10` | 일반 주석 4줄 + `/** @dev ... */` NatSpec 블록 주석 | **크래시 사라짐** |
| `web3bugs_70_H_05` | 일반 주석 1줄 | 크래시 지점/메시지 동일(§단발성, 별개의 진짜 엔진 버그) |
| `web3bugs_192_H_01` | `/** @notice ... */` NatSpec 블록 주석 2개(둘 다 함수 헤더와 뒤엉켜있던 것) | **크래시 사라짐** |
| `web3bugs_3_H_05` | (contraction만) 설명 주석 3줄 — 케이스 JSON엔 이 부분이 애초에 없었음 | 해당 없음(§Group D는 여전히 별개 원인으로 미해결) |

**중요 — "크래시 사라짐"이 "케이스 통과"를 뜻하지 않음**: `3_H_04`는
WARNING까지 도달하지만 기대 verdict와 일치하는지는 검증 안 됨. `62_H_03`은
직접 확인 결과 진짜로 깨끗함(정확한 값으로 SATISFIED, warning 없음).
`62_H_10`/`192_H_01`은 크래시 없이 끝까지 실행되지만 `@Debugging BEGIN`이
검증하려는 함수가 아니라 **완전히 다른, 엉뚱한 함수의 진입점**을 가리키고
있어서(주석 정리 전부터 있던 케이스-작성 오류, git HEAD 원본과 대조해서
확인함 — 엔진 버그 아님) 검증이 실제로 실행되지 않음, `[WARNING] Cannot
resolve LHS expression`만 뜨고 조용히 끝남(상세: §단발성의 `62_H_10`/
`192_H_01` 항목). 지금까지의 "버그 고침 ≠ 케이스 통과" 원칙을 그대로
적용해서, `3_H_04`/`62_H_10`/`192_H_01` 세 건은 "크래시는 없다"까지만 확인된
상태로, `62_H_03`만 실제로 완전히 통과한 것으로 취급할 것.

**근본 원인(엔진 버그 아님, 미해결로 남겨둠)**: 위 세 건의 크래시는 전부
`soltotestjson.py`(케이스 JSON 생성기)가 안 끝난 `/** ... */` 블록 주석이나
설명용 `//` 주석을 다음 statement와 한 레코드로 합쳐버리는 병합 로직 때문에
생긴 데이터 오염이었음 — 엔진(`main.py`/`Analyzer/*`) 쪽 코드는 이번에
전혀 건드리지 않았고, 이미 생성된 JSON 파일만 손으로 정리함. **`soltotestjson.py`
자체는 아직 안 고쳤으므로, 이 케이스들을 원본 소스에서 다시 생성하면 같은
문제가 재발함** — 근본 수정은 생성기의 청크 병합 로직을 손보는 것.

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
