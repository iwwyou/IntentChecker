# 엔진 실행 트리아지 — baseline 20개 + phase_reviews 빌드 케이스 전수 실행

**2026-08-31 재구성**: 사용자 요청으로 "지금 안 되는 케이스"를 맨 위로 올리고,
이미 고쳐진 것들은 참고사항으로 문서 하단(§고쳐진 것들)으로 내림. 실행 명령은
전부 `.venv/Scripts/python.exe main.py <case.json>` (cwd = 프로젝트 루트).

**범위**: (A) `evaluation/RQ1/run_all.py`의 `CASE_JSONS` 목록에 있는 baseline 20개
케이스 (논문 RQ2 "20/20 VIOLATED" 결과의 근거). (B) `phase_reviews/` 35케이스
리비전 배치 중 실제 케이스 JSON이 있는 것들.

---

## 지금 안 되는 케이스 (우선순위 순) — 총 7건 (2026-09-03 기준)

**2026-09-03 업데이트**: `3_H_05`/`42_H_01` 둘 다 완전 해결(§고쳐진 것들로 이동) —
`3_H_05`는 stale dependency pkl + `Engine.py`의 named-composite-return `.value`
버그 + `PriceAware.sol` 함수 순서 재배치(3중 수정)로, `42_H_01`은 interface
리턴의 file-level struct 병합 누락 + file-level enum 추적 메커니즘 부재 +
`Refine.py`의 narrowing이 enum/library 상수를 lvalue로 착각해 write-back
시도하던 버그(3중 수정)로 해결됨. 그 과정에서 `35_H_08`/`35_H_12`에 회귀가
발생했다가(같은 계열의 library 상수 narrowing 버그가 새 위치에서 터짐) 같은
메커니즘으로 즉시 재수정, 그리고 `35_H_12`의 마지막 잔여 이슈였던 shift
타입 불일치 에러도 별도로 완전 해결됨(`@Post`/`@During` 어노테이션 숫자
리터럴이 부호 무관하게 무조건 `int`로 찍히던 게 원인 — 값의 부호로
int/uint 판정하도록 수정, `GuardianVerificationEngine._evaluate_inline_interval`
이 이미 쓰던 관례와 통일). 상세 근거는 `engine_code_changes.md`의
"2026-09-03" RESOLVED 항목들 참고. baseline 20/20 유지, 이번 세션 손댄
케이스 8건 전부 재검증 완료(verdict 변동 없음).

baseline 회귀 0 + Group H 1 + verdict 불일치 6 = 7건. **baseline은
`51_H_02` 완전 해결로 20/20 VIOLATED 복원**(더 이상 이 섹션에 없음). `79_H_02`는
livelock 자체는 해결됐지만 그 직후 별개의 새 크래시가 남아서 Group H에 그대로
1건. `113_H_05`는 완전 해결돼서 목록에서 빠짐. `52_H_23`/`52_H_04`/`52_H_34`는
크래시 자체는 사라졌지만 verdict가 WARNING이라 단발성 → verdict 불일치로
재분류(`52_H_04`/`52_H_34`의 `sumNative` 크래시는 사용자가 "fixpoint 전체는
빼되 이 크래시만은 고쳐달라"고 별도 지시해서 처리, fixpoint의 정밀도 자체는
안 건드림). `29_H_11`은 AddressSet narrowing 부분은 고쳤지만 LocalVar 시딩
부분은 "버그 아님, 케이스 설계 결함"으로 판정하고 안 고치기로 해서 더 이상
이 목록에 없음. **`3_H_05`/`42_H_01`은 2026-09-03에 각자 남아있던 새 크래시까지
완전히 해결돼서 목록에서 빠짐**(§고쳐진 것들 참고, 3중 근본 수정씩). **`35_H_08`/
`35_H_12`는 2026-09-02 후속 조사로 완전히 해결돼서 목록에서 빠짐**(진짜 근본 원인은
`Update.py`의 composite 전체-재할당 버그 — §고쳐진 것들 참고, 두 케이스 다 크래시 없이
완주. `35_H_12`의 잔여 shift 타입 불일치 에러도 2026-09-03에 완전 해결됨 — §고쳐진
것들 참고). `59_H_04`는 fixpoint의 loop-carried-accumulator 정밀도 문제라 원인만
정정하고 안 고침(concrete unroll을 시도했다가 사용자가 sound함을 확신 못 해서
반려, 전부 되돌림 — 아래 §고쳐진 것들 및 해당 verdict-불일치 항목 참고). (해결된
그룹은 확인 즉시 이 섹션에서 내리고 §고쳐진 것들로 옮기는 걸 원칙으로 함 —
Group C/D/E/F/G는 전부 §고쳐진 것들로 이동 완료. 그 수정 과정에서 새로 드러난
크래시들은 기존 그룹에 안 맞으면 전부 "단발성"으로 재분류함. **2026-09-01,
사용자 요청으로 이 시점까지 "수정 방향 없음"으로 남아있던 케이스 전부를 12개
병렬 fork(각자 격리된 worktree에서 실제 임시 프로브 삽입 → 실행 → 확인 →
원복 방식으로 트레이싱, 추측 아님)로 재조사함** — baseline 3건 전부, Group H,
단발성 대부분, verdict 불일치 2건. 그 결과 원인 추정이 부정확했던 게 여럿
드러나서 정정함(45_H_01/56_H_02/79_H_02는 문서에 있던 원인 자체가 틀렸었고,
59_H_04/70_H_04는 "현재 상태" 서술 자체가 stale했음). 모든 항목에 확정된
원인 + 구체적 수정 방향을 새로 달아놨음(아래 각 항목 참고). **사용자가 승인한
항목부터 순차 적용 중** — `56_H_02`(2026-09-01)에 이어 **2026-09-02에
`35_H_11`/`52_H_23`/`83_H_01`/`42_H_01`/`62_H_10`/`192_H_01`(단발성 표 1/5/6/7/11번)
적용**: `35_H_11`/`83_H_01`/`62_H_10`/`192_H_01`은 완전히 통과(VIOLATED)까지
확인, `52_H_23`/`42_H_01`은 원래 크래시는 고쳤지만 그 뒤에 별개의 새 크래시가
남아있어 여전히 단발성에 있음(아래 각 항목 참고). 나머지는 아직 실제 수정
구현 안 함, 사용자 검토 대기 중. 이 숫자가 바뀌면 이 줄도 같이 업데이트할 것.)

### 최우선 — baseline 회귀 — **2026-09-02, `51_H_02` 완전 해결로 baseline 20/20 VIOLATED 복원됨**

`web3bugs_51_H_02`는 §고쳐진 것들로 이동(아래 참고). baseline 회귀 표는 이제 비어있음
— `evaluation/RQ1/run_all.py` 재실행 결과 **20 VIOLATED / 20 cases**, 논문 원래 결과와
일치.

### Group H — livelock (1건) — 2026-09-02, **진짜 원인 확정** (ANTLR은 완전히 무관했음, 처음 가설이 맞았음)

| 케이스 | 확정된 원인 (요약) | 제안하는 수정 방향 (요약) |
|---|---|---|
| `web3bugs_79_H_02` | **진짜 원인 확정, ANTLR과는 완전히 무관함.** `DynamicCFGBuilder`가 4단 중첩 `if/else if/else if/else if/else` 체인에서 마지막 `else { revert(...); }` 블록의 CFG를 잘못 연결함 — `else_block_109 → ERROR`로 직행시키고 `revert_110`(revert 문 자체 노드)을 그래프에서 고아로 남김(`preds=[]`, 영원히 도달 불가능). 근데 그 `revert_110`을 predecessor로 기다리는 join 노드(`else_if_join_106`)가 있어서, `Interpreter/Engine.py`의 `_run_worklist`(825-834행) worklist 알고리즘이 그 join 노드를 영원히 "아직 준비 안 됨"으로 보고 뒤로 미루기만 하고, 체인으로 중첩된 다른 join 노드들(`else_if_join_103`/`100`/`if_join_97`)까지 서로를 근거로 삼아 상호 무한 재큐잉(진짜 livelock, 크래시 없음). **2026-09-01의 "ANTLR 파서 내부 공유 캐시" 진단은 완전한 red herring이었음** — 원래(세션 훨씬 이전) 문서에 있던 "`_run_worklist`의 CFG join-point 재큐잉"이라는 첫 가설이 사실 처음부터 맞았음. | `Analyzer/DynamicCFGBuilder.py`에서 본문이 `revert(...)` 하나뿐인 `else` 블록(구체적으로 4단 이상 중첩된 `else if` 체인의 마지막 `else`)을 CFG로 만들 때 `else_block → revert 노드 → ERROR`로 제대로 연결하도록 수정 — 지금은 `else_block → ERROR`로 건너뛰면서 `revert` 노드를 고아로 남김. 더 방어적으로는, `_run_worklist`(Engine.py) 자체도 join 노드의 predecessor 중 그래프에서 원천적으로 도달 불가능한 노드가 있으면 무한 대기하지 않도록 가드 추가 검토(근본 수정은 CFG 빌더 쪽, 이건 안전망). |

**진단 과정 요약** (자세한 재현 스크립트/스택은 `First Revision/external_review/web3bugs_79_H_02.md` §9-10 참고): 2026-09-01 세션에 fork가 faulthandler로 뜬 스택이 ANTLR 내부(`ParserATNSimulator.closure_`/`PredictionContext.merge`)를 가리켜서 "공유 파서 캐시가 원인"이라는 가설을 세우고 그 방향으로 계속 조사/실험했음(재포맷 반증 실험, 외부 LLM 리뷰, fresh DFA/PredictionContextCache 주입 실험까지) — 그런데 2026-09-02에 파싱 단계 자체를 격리해서 재현해보니 **파싱은 항상 10ms 이내로 즉시 끝남**(단독 호출이든, 실제 케이스의 정확히 같은 지점이든 동일). 진짜로 멈추는 곳은 파싱 다음 단계, `EnhancedSolidityVisitor.visit(tree)`가 `_atPhase(_phase)` 함수 호출을 해석하려고 `interpret_function_cfg` → `_run_worklist`에 들어가는 지점이었음 — faulthandler로 다시 뜬 스택이 이번엔 명확하게 `networkx.predecessors`/`Engine.py:829`를 가리켰고, `_atPhase()`의 CFG를 직접 덤프해서 고아 노드(`revert_110`)를 바로 찾아냄. **"ANTLR 파서 캐시" 가설 전체가 잘못된 스택 샘플(또는 이후 코드 변경으로 stale해진 진단)에서 출발한 헛다리였음** — 사용자가 "소스코드 자체를 자세히 봐야 하지 않겠냐"고 제안한 게 정확히 맞는 방향이었음.

### 단발성 (각각 독립적인 원인 — Group C/D/G/B/F 수정으로 새로 드러난 것들도 여기로 재분류)

**2026-09-01 재조사(fork로 실제 트레이싱)해서 아래 대부분 원인 확정 + 수정 방향 제시함. 2026-09-02, 사용자
승인 받은 `35_H_11`/`52_H_23`/`83_H_01`/`42_H_01`/`62_H_10`/`192_H_01` 적용 — 그중 `35_H_11`/`83_H_01`/
`62_H_10`/`192_H_01`은 완전히 해결(§고쳐진 것들로 이동), `52_H_23`/`42_H_01`은 원래 크래시는 고쳤지만
그 뒤에 별개의 새 크래시가 나와서 그때는 여기 남아있었음. `35_H_08`/`35_H_12`는 2026-09-02 후속
조사로 완전히 해결돼서(진짜 근본 원인은 `Update.py`의 composite 전체-재할당 버그였음) §고쳐진 것들로
이동. **2026-09-03, `3_H_05`/`42_H_01`도 남아있던 새 크래시까지 완전히 해결돼서 §고쳐진 것들로 이동**
— 이제 이 표엔 `29_H_11`만 남음(그마저도 (1)은 의도적으로 안 고치기로 한 항목).**

| 우선순위 | 케이스 | 확정된 원인 (요약) | 제안하는 수정 방향 (요약) |
|---|---|---|---|
| 1 | `web3bugs_29_H_11` | **(1) 2026-09-02 판정: 버그 아님, 케이스 설계 결함, 손대지 않기로 함.** `tokenOut`/`recipient`/`unwrapBento`는 `abi.decode(data, ...)`로 함수 중간에 **계산되는** local — `@LocalVar`로 직접 seed하면 그 계산 로직을 건너뛰고 임의 값을 주입하는 셈이라 **unsound**함(사용자 판정, `feedback_debug_seeding_soundness` 메모리 참고). `related_variables` 기반이라 못 찾아서 드롭되는 현재 동작(경고만 찍고 무시)이 오히려 올바름 — "pending override" 메커니즘 같은 걸 만들어서 이걸 seedable하게 만들면 안 됨. 케이스를 고치려면 `data` 자체를 seed해야 함(엔진 변경 불필요). **(2) 전역급 정밀도 갭, 2026-09-02 RESOLVED**(§고쳐진 것들 참고): `Refine.py`의 narrowing이 `AddressSet`을 명시적으로 제외해서 `if (addr1==addr2)` narrowing이 코드베이스 전체에서 단 한 번도 안 되던 것 — `AddressSet` 비교 narrowing 케이스 추가로 고침. | (1) 안 고침(고치면 안 됨) — 케이스가 `data`를 seed하도록 재설계해야 함(사용자 판단 필요, 이번 세션엔 안 함). (2) 완료. |

`3_H_05`/`42_H_01`의 완전 해결 상세 근거는 §고쳐진 것들 및 `engine_code_changes.md`의
"2026-09-03" RESOLVED 항목 참고. 자세한 근거는 아래 상세 설명 참고.

- **`web3bugs_29_H_11`**(구 Group G) — Group G의 원래 join 크래시도,
  `[INTENT ERROR]`도 둘 다 2026-09-01에 RESOLVED(§고쳐진 것들 참고, 둘 다
  진짜 엔진 수정) — `[INTENT WARNING]`으로 정상 완주함. **남은 문제 2가지,
  둘 다 원인 확정**:
  1. `[WARNING] Cannot resolve LHS expression`이 `tokenOut`/`recipient`/
     `unwrapBento`(전부 `burnSingle()`의 `abi.decode`로 destructure된 local)
     3건 뜸 — `@LocalVar` 디버그 시드가 `related_variables`(파라미터/
     리턴변수/주입된 state·global만 담김, CFG 빌드 시점에 확정)만 보기
     때문에, 함수 중간 statement로 생기는 local은 애초에 못 찾음(seed 값이
     조용히 드롭됨). **수정 방향**: "pending override" 메커니즘 필요 —
     lookup 실패 시 `FunctionCFG`에 `pending_local_debug_overrides` 같은
     레지스트리로 등록해두고, 실제 interpretation이 그 local을 만드는
     순간(tuple-destructure 대입, 일반 `T x = ...;` 선언 처리하는 코드)
     그 레지스트리를 체크해서 override를 적용하도록 — 정확히 어느 함수가
     "local 생성"을 처리하는지는 이번 조사에서 특정 못 함, 다음 단계.
  2. **더 근본적이고 파급력이 큰 발견**: 위 시드 문제가 고쳐져도 `if
     (tokenOut == token1)` 분기가 여전히 안 좁혀짐 — `Refine.py`의
     `_update_comparison_condition`이 narrowing하는 4개 케이스 전부
     `VariableEnv.is_interval(x)`로 게이트돼 있는데, 이 함수가 **`AddressSet`
     을 명시적으로 제외**함(`Utils/Helper.py:397-399` 주석: "AddressSet은
     제외"). 즉 **address 타입끼리의 `==`/`!=` 비교는 이 코드베이스
     전체에서 단 한 번도 분기 narrowing이 안 됨** — `tokenOut`이 제대로
     시드돼도 두 분기(161/168) 다 여전히 실행될 것(양쪽 다 `[INTENT
     WARNING]`이 뜨는 이유가 바로 이거였음). **수정 방향**: `AddressSet`끼리
     (그리고 `AddressSet` vs 리터럴) 비교하는 narrowing 케이스를
     `_update_comparison_condition`에 새로 추가 — `refine_intervals_for_comparison`
     이 숫자 interval에 하는 것과 동일하게 `==`면 교집합으로, `!=`면
     singleton 쪽 제외로. `Domain/AddressSet.py`에 이미 교집합류 메소드가
     있을 가능성이 커서 그걸 바로 재사용할 수 있을 걸로 보임. **이건
     `29_H_11` 하나만의 문제가 아니라 코드베이스 전역의 정밀도 갭**(어떤
     케이스든 `if (addr1 == addr2)`가 있으면 다 영향받음) — 우선순위를
     사례 하나짜리보다 높게 볼 것.
- **`web3bugs_52_H_04`** / **`web3bugs_52_H_34`**(구 Group G) — 원래 join
  크래시는 RESOLVED. 새 크래시(`sumNative` not declared) **원인 확정,
  `29_H_11`의 tuple-destructure 문제와는 다른 별개 버그**임(`sumNative`는
  평범한 `uint256 sumNative = 0;`, tuple-destructure 아님, 그리고 루프 안
  narrowing 시점엔 실제로 정상 값이 들어있음 — 확인함). 진짜 원인:
  `Interpreter/Engine.py`의 `fixpoint()`(루프 narrowing 단계, ~582-588행).
  이 함수의 모든 `require`/`revert` 실패가 하나의 공유 `ERROR` sink CFG
  노드로 수렴하는데, 이 `ERROR` 노드가 **루프 안** `require`(line 34,
  `sumNative != 0`)에서도, **루프 밖**(line 58) `require`에서도 둘 다
  도달 가능함 — `traverse_loop_nodes`는 전자 경로로 `ERROR`를 `loop_nodes`에
  올바르게 포함시키지만, 후자(루프 밖 require)는 `loop_nodes` 밖이라
  이 시점엔 아직 방문이 안 됨. narrowing이 `ERROR`의 predecessor를 계산할 때
  루프 안 predecessor(`sumNative != 0`의 false-edge)는 이 시나리오에서
  infeasible이라 기여가 없고, 루프 밖 predecessor(58행)가 유일하게 남는데
  이건 `loop_nodes` 밖이라 fallback으로 `.variables`(아직 방문 안 된 빈
  기본 `{}`)를 그대로 씀 — 그 빈 env가 전파돼서 `sumNative` 참조가 뻥 뚫림.
  **수정 방향**: `fixpoint()`의 narrowing predecessor 루프(~582-588행)에서
  `loop_nodes` 밖이면서 아직 실제 계산된 값이 없는 predecessor는 건너뛰도록
  (빈 dict fallback으로 join에 기여시키지 말 것). 더 근본적으로는, 루프
  안팎의 `require`가 하나의 공유 terminal `ERROR` 노드로 수렴하는 설계 자체가
  이런 경계-교차 predecessor 문제의 원인으로 보임 — `DynamicCFGBuilder`의
  `require`/`revert` 처리가 (적어도 루프 경계를 넘는 경우엔) 각자 별도
  sink를 갖게 하는 것도 검토해볼 만함.
- **`web3bugs_3_H_05`**(구 Group D) — 원래 크래시는 RESOLVED. 새 크래시
  **원인 확정, 처음 추정(라이브러리 이름 resolve 실패)이 틀렸음**:
  `PriceAware`는 라이브러리가 아니라 **base contract**(`abstract contract
  CrossMarginAccounts is RoleAware, PriceAware`). `PriceAware.getCurrentPriceInPeg(...)`
  는 Solidity의 "명시적 base-contract-qualified 호출" 문법(`super.foo()`와
  비슷하지만 조상 하나를 이름으로 못박는 것) — `evaluate_identifier_context`의
  `MemberAccessContext` 분기에 "이 식별자가 알려진 parent contract 이름인지"
  체크가 아예 없음(local var → this/super → block/tx/msg → enum →
  library_cfgs → 없으면 raise, 순서에 parent-contract 체크가 빠져있음).
  **수정 방향**: 바로 위(1035-1057행)에 이미 있는, 잘 동작하는 `super.foo()`
  핸들러를 그대로 미러링 — (1) `evaluate_identifier_context`의
  `MemberAccessContext` 분기에서 `library_cfgs` 체크 다음에 "`ident_str`이
  `self.an.contract_cfgs`에 있고 현재 컨트랙트의 `parent_cfgs`에서
  reachable하면" `{"isBaseContract": True, "contractName": ident_str}` 마커
  리턴(기존 `{"isLibrary": True, ...}` 모양 그대로 따라감). (2)
  `evaluate_member_access_context`에 super 처리와 나란히 분기 추가 —
  `baseVal.get("isBaseContract")`이면 `find_function_in_hierarchy(그
  contractName의 cfg, member)`로 함수 찾아서 기존 `SuperFunctionCallContext`
  태그로 감싸기(다운스트림 소비자는 이미 이 태그만 보고 동작해서 안 건드려도 됨).
  기존 코드 경로를 그대로 재사용하는 작고 안전한 수정.
  **2026-09-03, 이 새 크래시도 완전히 해결됨 → §고쳐진 것들로 이동.** 실제 원인은
  3중이었음(stale dependency pkl + `Engine.py`의 named-composite-return `.value`
  버그 + `PriceAware.sol` 함수 순서 재배치) — "base-contract 호출이 CFG 빌드
  상태를 오염시킨다"는 위 가설은 틀렸었음, 상세는 `engine_code_changes.md`
  "2026-09-03" 항목 참고. `[POST INTENT VIOLATION] Line 104` risk=10.0으로 완주.
- **`web3bugs_52_H_23`** — **원래 크래시(`EnhancedSolidityVisitor.py:771`,
  `Invalid key type in mapping: IERC20`, 케이스 JSON `startLine 21`)는
  2026-09-02에 RESOLVED**(§고쳐진 것들 참고: `visitMappingKeyType`에
  `identifierPath` 분기 추가, 기존 `visitUserDefinedType` 재사용). 그 직후
  바로 다음 문장에서 새로운 별개 크래시로 진행: `function mintSynth(...,
  address from, ...)` — `[ANTLR] mismatched input 'from' expecting ')'`.
  `Solidity.g4`가 `'import' ... 'from' importPath` 규칙에서 `'from'`을
  리터럴 토큰으로 등록해버려서, `identifier: Identifier;`만으로는 `from`을
  일반 식별자(파라미터 이름)로 못 씀. **2026-09-02, 이것도 RESOLVED** —
  `Solidity.g4`를 고치는 대신(재생성 필요, 더 무거운 변경) 케이스 데이터
  쪽에서 `from` → `_from`으로 이름만 바꿈(contraction `.sol`의 파라미터
  선언/본문 사용처, 케이스 JSON의 같은 두 곳 + `@LocalVar from = ...` 시드까지
  전부 동기화). 이게 안전한 이유: `ContractAnalyzer`가 `import` 라인 자체를
  아예 분석 대상에서 제외하고(`"pragma, import는 contract 밖이므로 분석
  불필요"`) `EnhancedSolidityVisitor`의 import 관련 visit 메소드들도 전부
  빈 `visitChildren` no-op이라 import 자체가 애초에 의미 있게 처리되는 게
  없음 — 게다가 이 테스트 스위트의 어떤 contraction `.sol`/케이스 JSON에도
  `import ... from ...`(symbol-alias) 형태가 단 하나도 없음(전수 확인함,
  있는 건 `52_H_04`/`52_H_34`의 `import "path";` 단순형뿐). 즉 `from`
  키워드가 실제로 import 문법으로 쓰일 일이 이 파이프라인엔 전혀 없으므로,
  이름을 바꾸는 게 grammar를 건드리는 것보다 훨씬 저위험. **검증**: `from`
  크래시 사라짐, baseline 20개 회귀 확인(19 VIOLATED/1 ERROR, 변동 없음 —
  `52_H_23`은 baseline 세트 밖). 그 직후 또 다른 별개 이슈 발견(위 단발성
  표 참고): 중괄호 없는 단일 statement `if` 본문에서 `[ANTLR] mismatched
  input 'synth' expecting '{'`(경고 수준, 크래시 아님, `[INTENT WARNING]`
  으로 완주는 함) — 조사 범위 밖, 이번엔 손 안 댐.
- **`web3bugs_42_H_01`** — **원래 크래시(`ContractAnalyzer.py:989`,
  `Modifier 'updateDebt' is not defined`)는 2026-09-02에 RESOLVED**(§고쳐진
  것들 참고: 케이스 JSON이 `modifier updateDebt`뿐 아니라 `accrueDebt`/
  `liveDebtIndex`/`mintFeeToPool`/`_liquidatable` 함수 전체를 빠뜨린 채
  stale해서 전체 재빌드함, 케이스 작성 문제였지 엔진 버그 아니었음). 재빌드
  후 문서가 예측했던 대로 다음 블로커가 정확히 그대로 나옴: `evaluate_
  member_access_context`에서 `'denominator' not in struct 'lf'`(cast 없는
  chained interface 호출, `engine.mochiProfile().liquidationFactor(...)`가
  struct를 반환하는 경로 미지원) — 여기서 발생한 예외가 `[LIBRARY CALL
  ERROR]`로 잡힌 뒤 그 처리 경로에서 2차로 CFG `KeyError`(networkx
  `successors()`가 그래프에 없는 노드를 조회)까지 따라옴. **수정 방향**:
  조사 범위 밖, 이번엔 손 안 댐 — cast 없는 interface 체이닝이 struct를
  반환하는 경우의 타입 추론을 `evaluate_library_function_call_context`/
  `evaluate_member_access_context` 쪽에 추가해야 할 것으로 보임(별도
  조사 필요, 위 2차 CFG 크래시도 같이 봐야 함).
  **2026-09-03, 이 새 크래시도 완전히 해결됨 → §고쳐진 것들로 이동.** 실제 원인은
  "cast 없는 interface 체이닝 자체를 지원 안 함"이 아니라, interface 함수의
  리턴 타입이 file-level struct일 때 그 struct 정의를 못 찾던 문제였음(interface
  리턴 TOP-값 생성 시 `file_level_structs` 병합 누락) + file-level enum을 아예
  추적하지 않던 문제 + `Refine.py`의 narrowing이 enum/library 상수를 lvalue로
  착각해 write-back 시도하다 크래시하던 문제, 3중. 상세는 `engine_code_changes.md`
  "2026-09-03" 항목 참고. `[INTENT WARNING] Line 104` risk=3.4로 완주.
- **`web3bugs_113_H_05`**(구 Group I) — **원인 확정됨.** `AttributeError:
  'str' object has no attribute 'multiply'` — 실제 근본 원인은 크래시
  지점(`startLine 66`, `openFeeShare = (totalShare * OPEN_FEE_BPS) / BPS;`)
  보다 한 줄 앞(`startLine 65`, `totalShare = bentoBox.toShare(asset,
  params.valuation, false);`). `bentoBox`는 진짜 interface 타입 state
  변수라서 이 호출이 `evaluate_function_call_context`의 "Pattern A"
  (`_resolve_ireturn_pattern_a`)로 라우팅되는데, 이 케이스엔 `@IReturn`/
  `@Debugging` 블록이 아예 없어서 그 lookup이 `None`을 리턴 — 그런데
  **Pattern A엔 그 이후 fallback이 없음**(형제 경로인 "Pattern B",
  `IERC20(x).balanceOf()`류 명시적 캐스트 호출은 `None`이면
  `_lookup_interface_return(...)` → 그것도 없으면 `UnsignedIntegerInterval.top()`
  까지 폴백하는데, Pattern A는 그냥 일반 member-access로 흘러서
  `f"symbolic(...)"` raw 문자열로 바텀아웃함). 그 문자열이 그대로
  `totalShare * OPEN_FEE_BPS`로 들어가서 크래시. **수정 방향**:
  `evaluate_function_call_context`의 Pattern-A 분기에서 `_resolve_ireturn_pattern_a`
  가 `None`이면, Pattern B가 이미 하는 것과 똑같이
  `self._lookup_interface_return(interface_name, member_name)` 호출 후
  그것도 `None`이면 `UnsignedIntegerInterval.top()`으로 폴백 — `.call()`/
  `.staticcall()`/`abi.decode`가 이미 쓰는 것과 같은 TOP-degradation
  컨벤션을, 이미 옆 분기에 있는 헬퍼를 그대로 재사용해서 적용하면 됨(같은
  함수 안에서 한 분기만 이 폴백이 빠져있던 비대칭).
- **`web3bugs_35_H_08`**(구 Group J) / **`web3bugs_35_H_12`**(구 Group J) —
  **2026-09-02 완전 해결(진짜 엔진 수정, 크래시 없이 완주).** 최초 크래시
  (`_is_abstractable`이 struct base type의 `elementaryTypeName=None`을
  못 버텨서 죽던 것)는 null 가드 한 줄로 없앴으나(여전히 유효한 수정,
  `if et is None: return False`), 그 뒤로 최소 세 겹의 별개 문제가 더
  있었고 전부 확인/수정함:
  1. qualified 네임스페이스 struct 생성자(`IPool.TokenAmount({...})`)를
     `evaluate_function_call_context`/`evaluate_identifier_context`가 아예
     인식 못 하던 문제 — interface 이름 인식 + qualified struct 생성자
     경로 추가로 해결(§고쳐진 것들 참고).
  2. `ArrayVariable._init_recursive`/`_create_new_array_element`가 struct
     원소를 실제 `StructVariable`로 안 만들고 raw 심볼 문자열로 바텀아웃
     시키던 문제 — struct 분기 추가로 해결.
  3. **진짜 근본 원인, 가장 마지막에 발견함**: `withdrawnAmounts = new
     IPool.TokenAmount[](2);`처럼 **이미 선언된 배열/구조체/매핑 변수 전체를
     새 composite 값으로 재할당**하는 문이 `Interpreter/Semantics/Update.py`의
     `update_left_var_of_identifier_context`에서 완전히 잘못 처리되고
     있었음 — `ArrayVariable`/`StructVariable`/`MappingVariable`이 전부
     `Variables`의 서브클래스라서, "top-level bare identifier 대입" 폴백
     분기(`if not isinstance(tgt, (Variables, EnumVariable))`)가 composite
     재할당도 그냥 통과시켜서 leaf 전용 헬퍼 `_apply_to_leaf`(`.value`에
     그냥 얹어버림)로 보내버림 — 새로 만든 배열(`new` 표현식이 만든, 원소
     2개 다 올바르게 초기화된 임시 `arr` 객체)이 통째로 버려지고, 원래
     상태변수 선언 시점의 **빈** `ArrayVariable`(`elements=[]`)이 그대로
     남음. 그 뒤 `withdrawnAmounts[0] = ...`가 실행되면 `Update.py`의
     literal-index 배열 분기(`update_left_var_of_literal_context`)의
     동적배열 padding 로직이 raw 심볼 `Variables`(base type 무관하게
     무조건)로 1칸만 채워 넣었고, 그 padding된 leaf에 struct 리터럴을
     `_to_interval`로 억지로 밀어넣으려다가 `elementaryTypeName=None`에서
     크래시. **게다가 별개로**, 같은 두 함수의 "composite 원소" 분기들
     (`if isinstance(elem, (Variables, EnumVariable))` vs `(ArrayVariable,
     StructVariable, MappingVariable)`)의 **체크 순서 자체가 잘못**돼
     있었음 — composite도 `Variables`의 서브클래스라서 leaf 체크가 항상
     먼저 걸려버려 composite 체크 분기가 **죽은 코드**였음(`arr[i] =
     StructLit`류 통짜 재할당, `arr[i].field = x`류 체이닝 둘 다 영향
     받는 일반적 버그, struct 배열에 국한된 문제가 아니었음).
     **수정**(`Interpreter/Semantics/Update.py`): (a) 새 정적 헬퍼
     `Update._assign_whole_composite(dst, src)` 추가 — dst/src가 같은
     계열 composite(Array/Struct/Mapping)면 `dst.elements`/`members`/
     `mapping`을 `VariableEnv.copy_single_variable`/`copy_variables`로
     **deep-copy**해서 교체(참조를 그냥 공유하면 `b = a;`처럼 양쪽 다
     계속 살아있는 경우 한쪽을 고치면 다른 쪽도 같이 바뀌는 aliasing
     버그가 생겨서, 기존에 있던 `MappingVariable` struct-entry 재할당
     코드가 이미 하던 것과 같은 방식으로 통일함); dst/src 계열이 안 맞으면
     `False`를 반환해 호출자가 기존 체이닝 로직을 계속 타게 함. (b)
     `update_left_var_of_identifier_context`의 top-level bare-identifier
     분기, `update_left_var_of_literal_context`의 ArrayVariable/
     MappingVariable 분기, `update_left_var_of_identifier_context`의
     ArrayVariable(`arr[i]=`)/StructVariable(`s.x=`) 분기까지 전부 이
     헬퍼를 먼저 시도하도록 통일(순서도 composite 체크를 leaf 체크보다
     앞으로 옮김). (c) `update_left_var_of_literal_context`의 동적배열
     padding도 raw 심볼 `Variables`를 손으로 만드는 대신
     `caller_object._create_new_array_element(...)`(이미 struct/nested
     array/mapping/enum 분기를 다 가진 헬퍼)를 재사용하도록 교체.
     **검증**: `35_H_08`/`35_H_12` 둘 다 원래 크래시 완전히 사라지고
     끝까지 완주 확인(`35_H_08` → `[POST INTENT WARNING]` risk=9.9,
     `withdrawnAmounts[0].token`/`.amount`, `withdrawnAmounts[1].token`/
     `.amount` 넷 다 독립적으로 올바르게 추적됨 — aliasing 없이 두 원소가
     분리돼 있음 확인; `35_H_12`는 원래 크래시는 사라지고 이후 무관한
     별개 `[POST INTENT ERROR]`(`Shift operands must both be int/uint
     intervals` — shift 연산 타입 불일치)로 완주 — **이것도 2026-09-03에
     완전히 해결됨**(`@Post`/`@During` 어노테이션 숫자 리터럴이 부호
     무관하게 무조건 `int`로 찍히던 게 원인, `EnhancedSolidityVisitor.
     visitNumLiteral` 수정. 상세는 `engine_code_changes.md` "2026-09-03"
     항목 참고. `[POST INTENT VIOLATION] Line 181` risk=10.0, RHS=`2^127`
     로 정확히 계산됨, `burn()`이 `secondsPerLiquidity`를 실제로 갱신 안
     하는 소스 구조와 부합하는 정당한 VIOLATED). baseline 20개 재실행
     확인(20/20 VIOLATED 유지, 회귀 없음).
     `web3bugs_3_H_05`/`113_H_05`/`52_H_04`/`52_H_34`/`52_H_23`/`29_H_11`
     (이번 세션에서 수정한 다른 케이스들)도 개별 재실행해서 verdict 동일함
     확인 — `Update.py`의 assignment 경로는 모든 케이스가 공유하는
     핵심 코드라 회귀 위험이 커서 별도로 재검증함.
  **남은 무관한 이슈**(조사 범위 밖, 손 안 댐): `35_H_08`에서
  `[WARNING] Cannot resolve LHS expression: VarRefBase (identifier:
  lower/upper/amount/recipient/unwrapBento)` — 아마 콜백 함수 파라미터
  destructuring 관련 별개 문제로 보이나 크래시는 아니고 최종 verdict에도
  영향 없어서 조사 안 함. (`35_H_12`의 shift 타입 불일치 에러는 위에서
  설명한 대로 2026-09-03에 완전히 해결됨.)
### 크래시는 안 나지만 verdict가 기대와 다름 (엔진 크래시 아님, 결과 정확성 문제)

**2026-09-01 재조사 결과 — 중요: 이 문서의 "현재 상태" 서술 자체가 stale했음이
드러남(두 케이스 다). 재실행해서 실제 현재 출력부터 다시 확인하고 원인 파악함.**

- **`web3bugs_52_H_04`** / **`web3bugs_52_H_34`**(구 단발성 2번, 2026-09-02
  재분류) — **`sumNative` 크래시 RESOLVED**(§고쳐진 것들 참고, 진짜 엔진
  수정) — `fixpoint()`의 narrowing/exit-env 계산이 루프 밖에 있고 아직
  outer worklist가 방문 안 한 predecessor를 빈 `{}` env로 fallback시켜서,
  그 predecessor가 `require(sumNative...)`류 condition node일 때 `sumNative`
  를 못 찾아 크래시하던 버그. **수정**: 그런 predecessor는 join에서 완전히
  제외하도록 `_pred_src` 헬퍼 추가(2군데 적용). **검증**: 크래시 사라지고
  `[POST INTENT WARNING]`(risk=9.9)으로 완주(정밀도는 그대로 낮음 —
  `sumNative`가 `[0, inf]`로 나오는 건 알려진 loop-carried-accumulator
  imprecision, 아래 `59_H_04` 참고, 이번엔 정밀도는 안 건드리기로 함).
  baseline 20개 회귀 확인(영향 없음, 20/20 유지).
- **`web3bugs_52_H_23`**(구 단발성 4번, 2026-09-02 재분류) — `from` 예약어 크래시
  (케이스 데이터에서 `from`→`_from` 개명) + 중괄호 없는 단일 statement `if` 본문
  ANTLR 파싱 경고(contraction `.sol`에 중괄호 추가 + 케이스 재빌드) 둘 다
  RESOLVED(§고쳐진 것들 참고) — 더 이상 크래시도 파싱 경고도 없음. 다만 최종
  결과는 여전히 `[INTENT WARNING]`(risk=9.9, `_update.arg[2]`) — 두 수정 다
  이 특정 `@During` 체크의 정밀도 자체와는 무관해서 verdict는 그대로임. 더
  이상 수정 방향 없음(남은 정밀도 문제는 이 두 수정과 무관한 별개 원인일 걸로
  보이나 조사 안 함).
- **`web3bugs_70_H_05`**(구 단발성 7번, 2026-09-02 재분류) — **원래 있던 크래시는
  사라졌지만 VIOLATED가 아니라 WARNING으로 수렴, 예상된 결과.** 두 가지가 겹쳐서
  일어남: (1) **진짜 엔진 버그**(아래 §고쳐진 것들 참고) — `usdvPairs`(`IERC20[]`,
  interface 타입 배열)의 `@StateVar usdvPairs[0] = symbolicAddress 1` 시딩이
  `ArrayVariable._create_new_array_element`에 `interface` typeCategory 분기가
  없어서 조용히 실패하고 있었음(고쳐서 `totalPairs = usdvPairs.length`가 이제
  TOP 대신 `[1,1]`로 정확히 resolve됨, 확인함). (2) **사용자가 의도적으로 받아들인
  정밀도 손실** — `@IReturn oracle.latestRoundData()[...]`이 콜리 함수
  (`getChainlinkPrice`)의 local `oracle`을 가리켜서 `@IReturn` 문법 자체가
  표현 못 하는 케이스임(아래 §고쳐진 것들의 "@IReturn 스코프 한계" 참고) — 사용자가
  그 3줄을 그냥 지우기로 결정, 그 결과 `oracle.latestRoundData()`가 unconstrained
  Top으로 평가되고 `foreignPrice`/`totalUSD`/`totalUSDV`로 퍼져서 `@Post`가
  `[POST INTENT WARNING]`(risk=9.9, Analysis==Intent==`[0, 2^256-1]`)으로 남음 —
  크래시는 아니지만 케이스가 원래 검증하려던 정밀한 값은 못 잡음(트리아지 문서가
  이미 예상했던 트레이드오프 그대로). **더 이상 수정 방향 없음** — `@IReturn`
  함수-한정자 문법을 새로 추가하지 않는 한 이게 이 케이스의 최종 상태.
- **`web3bugs_59_H_04`** — 문서엔 "SATISFIED"라고 적혀있었지만 **지금 실제로는
  `[POST INTENT WARNING]`**(risk 9.9)을 냄, Analysis=`[0, ~1.16e77]`,
  Intent=`[0, ~3.86e77]`. **원인 정정(2026-09-02)**: "widening 연산자가 없다"는
  기존 서술은 부정확했음 — `Interpreter/Engine.py`의 `fixpoint()`를 직접
  읽어보니 이미 표준적인 widening(`_estimate_loop_iterations`로 threshold
  추정) + narrowing 2단계 구현이 있음. 실제 근본 원인은 **알고리즘 자체의
  구조**: 루프 본문의 각 CFG 노드를 "모든 반복에 걸쳐 유효한 하나의 불변식"
  으로 계산하는 표준 fixpoint 방식이라, 서로 다른 반복에서 그 노드에 도달한
  환경을 매번 join(합집합)해야 함 — `total = total + pegObservations[index]`
  처럼 반복마다 다른 구체값이 쌓이는 accumulator는 이 join 자체 때문에
  반복마다 넓어짐(widening/narrowing을 아무리 튜닝해도 이 join 구조 자체는
  못 피함, 직접 프로브로 반복별 `total`/`index` 값을 찍어서 확인함). 이건
  `analysis.md`의 R1-7 항목이 이미 예견했던 결과이기도 함. **2026-09-02
  시도했다가 되돌림**: 조건의 양쪽 피연산자가 진입 시점에 singleton이면
  join 없이 반복마다 환경을 순차 교체하는 "concrete unroll" 경로를
  `fixpoint()`에 추가해봤고(실제로 `total`이 정확히 `[2,2]`로 수렴하는 것까지
  확인함) — **사용자가 이 접근의 sound함을 확신할 수 없다며 반려**, 기존
  widening/narrowing 알고리즘을 최대한 그대로 유지해달라고 요청. 코드
  전부 되돌림(`git diff` 깨끗함 확인). **현재 상태**: 정밀도 문제는 의도적으로
  안 건드리기로 함 — 이 케이스는 그대로 WARNING으로 남음. 나중에 다시
  다룬다면, concrete unroll 대신 (a) 기존 join 기반 알고리즘 안에서 accumulator
  전용 widening 연산자를 sound하게 설계하는 방향, 또는 (b) concrete unroll을
  다시 시도하되 이번엔 sound함을 더 엄밀하게(예: 정지성/모든 분기 처리 증명)
  검토한 뒤 진행하는 방향을 고려.
- **`web3bugs_70_H_04`** — 문서엔 "VIOLATED가 아니라 WARNING"이라고 적혀있었지만,
  **`analysis.md`의 target annotation 자체가 이후 리비전에서 `@Post` 절 2개로
  쪼개졌다는 걸 문서가 반영을 못 했음**(stale) — 지금 실제로 나오는 건:
  - Mechanism (A) `totalLiquidityWeight[0] == totalLiquidityWeight[0](Entry)`
    → **`[POST INTENT SUCCESS]`**(500==500) — 시나리오가 기대하는 건 VIOLATED
    (entry=500, exit=0이어야 버그가 잡히는데, 지금은 그 차이가 안 잡힘 =
    거짓 SATISFIED).
  - Mechanism (B) `pastLiquidityWeights[0] == twapData[...].pastLiquidityEvaluation`
    → **`[POST INTENT ERROR]`**, `Index 0 out of range for array
    'pastLiquidityWeights'`.

  **원래 공통 원인 진단("배열 자체의 length를 구체값으로 고정하는 방법이 없어
  보임")은 2026-09-02, `70_H_05` 조사 중 절반 틀렸음이 드러남 — 길이 추론
  메커니즘 자체는 정상 동작함, 막혀있던 건 `vaderPairs`(`IUniswapV2Pair[]`,
  `70_H_05`의 `usdvPairs`와 똑같이 interface 타입 배열)의 개별 인덱스 시딩이
  `ArrayVariable._create_new_array_element`의 `interface` typeCategory 분기
  누락으로 조용히 실패하던 것(아래 §고쳐진 것들 참고, `70_H_05`에서 먼저 발견해서
  고침). 그 수정 이후 재실행 확인: `totalPairs`가 이제 TOP이 아니라 정확히
  `[1,1]`로 resolve됨 — "길이를 직접 고정하는 방법이 없다"는 원래 진단은
  틀렸었음. 다만 **여전히 완전 해결은 아님, 원인이 바뀌었을 뿐**: (A)는 여전히
  `[POST INTENT SUCCESS]`(500==500)로 거짓 SATISFIED — `totalPairs`가 풀려도
  루프의 skip-vs-update 로직 정밀도 문제는 그대로 남아있음. (B)는 여전히
  `[POST INTENT ERROR] Index 0 out of range for array 'pastLiquidityWeights'`
  — `pastLiquidityWeights`는 `totalPairs`로 크기가 정해지는 별도의 동적 배열인데
  (`new uint256[](totalPairs)`류로 추정), `totalPairs`가 이제 `[1,1]`로 풀렸는데도
  여전히 `array(len=0)`으로 남음 — 즉 `new T[](변수 길이)`가 나중에 resolve된
  interval을 보고 배열을 다시 sizing하는 경로가 없는 것으로 보임, `interface`
  배열 버그와는 별개의 새로운 갭. **수정 방향(조사 필요, 이번엔 손 안 댐)**: (1)
  루프 skip-vs-update narrowing 정밀도 문제 조사. (2) `new T[](N)` 동적 배열
  할당이 `N`이 나중에 구체값으로 resolve됐을 때 재sizing되는 경로가 있는지
  확인 — 없으면 엔진 갭, 있는데 이 케이스가 못 타면 케이스 데이터 문제.

  (참고: `web3bugs_16_H_06`도 원래 이 목록에 있었지만 아래 §고쳐진 것들에서
  설명하는 `_preds` 버그 수정으로 이제 정상적인 WARNING을 내서 목록에서
  제거함.)

---

## 참고: 이번 세션에 고쳐진 것들

### 2026-09-02, "전부 수정" 라운드 — fixpoint 관련 제외 전 항목 시도 (baseline 20/20 VIOLATED 복원 포함)

사용자가 "fixpoint 함수 관련된 것 제외하고는 전부 수정해봐. 코드 문제인지 annotation
문제인지 먼저 검토하고, 코드면 잘 수정해줘"라고 요청. 아래 7건 시도, 결과 요약:
**완전 해결 3건**(`51_H_02`/`79_H_02` livelock/`52_H_23`), **원래 문제 해결 +
별개의 새 문제로 진행 3건**(`3_H_05`/`113_H_05`는 완전 해결, `35_H_08`/`35_H_12`는
이 라운드 시점엔 부분 해결 — **2026-09-02 후속 조사로 이후 완전 해결됨, 아래
`35_H_08` 상세 항목 참고**), **버그 아님으로 판정, 안 고침 1건**(`29_H_11`의
LocalVar 시딩 — 사용자가 unsound하다고 지적해서 되돌림, 대신 AddressSet
narrowing 부분은 고침).
전부 진짜 **코드(엔진) 수정**이었음 — annotation/케이스 데이터만으로 해결 가능한
게 있는지 먼저 확인했으나 없었음(단, `52_H_23`의 두 번째 이슈는 케이스 데이터
수정으로 해결됨, 아래 참고). 모든 수정 뒤 baseline 20개 재실행으로 회귀 확인함
(최종 20 VIOLATED / 20 — 최초 회귀 없음).

**1) `web3bugs_51_H_02` — baseline 완전 해결, baseline 20/20 VIOLATED 복원 (진짜 엔진 수정).**
`Utils/Helper.py`의 `top_from_soltype()`과 `Domain/Variable.py`의
`MappingVariable._make_value()` 둘 다 배열 분기에서 base type을 안 가리고
무조건 `arr.initialize_not_abstracted_type()`을 호출해서, `TargetPrice.
originalPrecisionMultipliers`(`uint256[2]`) 같은 numeric 배열의 원소가 진짜
`Interval`이 아니라 raw 문자열로 초기화되던 버그. **수정**: `Domain/Variable.py`의
`ArrayVariable`에 공용 헬퍼 `initialize_default_by_base_type(is_return_param=False)`
신규 추가(elementary numeric/bool이면 `initialize_elements(TOP 또는 0)`, 아니면
`initialize_not_abstracted_type()`으로 위임) — `top_from_soltype`/`MappingVariable.
_make_value`/`StaticCFGFactory.make_param_variable` 세 호출부 전부 이 헬퍼를
쓰도록 통일(예전엔 세 곳이 서로 다르게 복붙돼 있어서 두 곳이 틀렸었음, 이제
단일 진실 공급원). **검증**: `51_H_02` 크래시 사라지고 `[INTENT VIOLATED] Line
113: require condition is always false — never passable`로 정상 완주.
baseline 재실행: **20 VIOLATED / 20 cases**(18/2로 시작했던 이번 세션의 baseline
회귀가 이걸로 전부 해소됨 — 논문 원래 결과와 일치).

**2) `web3bugs_79_H_02` — Group H livelock 완전 해결 (진짜 엔진 수정, CFG 빌더 버그).**
자세한 원인 분석은 위 Group H 섹션 및 `First Revision/external_review/
web3bugs_79_H_02.md` §10 참고. **수정**: `Analyzer/DynamicCFGBuilder.py`의
`build_revert_statement`(740-782행) — `insert_new_statement_block`이 이미
`cur_block → new_block(revert 문 자체) → old_succs`로 재배선해뒀는데, 그 다음에
`cur_block`의 (이미 `[new_block]`으로 바뀐) successor를 다시 조회해서
`cur_block → ERROR`로 직접 재배선하는 바람에 `new_block`이 그래프에서 고아가
되던 버그. `cur_block` 대신 `new_block`의 successor를 조회/재배선하도록 수정
(`new_block → ERROR`), `line_info`의 `cfg_nodes` 등록 대상도 `cur_block`에서
`new_block`으로 수정(그 줄을 실제로 대표하는 노드가 맞게). **검증**: `79_H_02`가
더 이상 멈추지 않고(180초+ 걸리던 게 수 초 안에 다음 지점까지 진행), 다른
곳(`(, , lpSupply) = router.addLiquidity(...)` 튜플 destructure 중 빈 슬롯
파싱)에서 별개의 새 `[ANTLR] mismatched input ')' ...` 크래시로 진행 —
livelock 자체는 확실히 해결, 이 새 크래시는 조사 범위 밖으로 남겨둠. baseline
20개 회귀 확인(영향 없음, `79_H_02`는 baseline 세트 밖).

**3) `web3bugs_113_H_05` — 완전 해결 (진짜 엔진 수정, VIOLATED 확인).**
`Interpreter/Semantics/Evaluation.py`의 `evaluate_function_call_context`,
interface 변수를 통한 "Pattern A" 호출 경로(`bentoBox.toShare(...)`류, cast
없이 바로 interface 타입 변수로 호출)에 `_resolve_ireturn_pattern_a`가 `None`을
리턴했을 때의 폴백이 없어서, 그 아래 일반 member-access 평가 경로로 흘러가
호출 결과가 아니라 호출 대상 자체(함수 참조)가 반환되고 raw 문자열로
바텀아웃하던 버그. **수정**: Pattern B(`IERC20(x).balanceOf()`류 explicit cast)가
이미 하는 것과 동일한 폴백(`_lookup_interface_return(...)` → 그것도 없으면
`UnsignedIntegerInterval.top()`)을 Pattern A 분기에도 추가. **검증**:
`[INTENT VIOLATION] Line 52`(risk=10.0, LHS=[8600,8600]/RHS=[8000,8000])로
정상 완주.

**4) `web3bugs_3_H_05` — 원래 크래시 완전 해결(진짜 엔진 수정), 별개의 새 크래시로 진행.**
`PriceAware`는 라이브러리가 아니라 base contract(`abstract contract
CrossMarginAccounts is RoleAware, PriceAware`) — `PriceAware.getCurrentPriceInPeg(...)`
같은 명시적 base-contract-qualified 호출을 `evaluate_identifier_context`의
`MemberAccessContext` 분기가 아예 인식 못 하고 raise하던 버그. **수정**:
`Interpreter/Semantics/Evaluation.py`에 (1) `_is_known_parent_contract(contract_cfg,
name)` 헬퍼 신규 추가(부모 체인 재귀 검색), (2) `evaluate_identifier_context`의
`MemberAccessContext` 분기에서 `library_cfgs` 체크 다음, 최종 raise 이전에
이 헬퍼로 parent contract 이름인지 확인해서 `{"isBaseContract": True,
"contractName": ident_str}` 마커 반환, (3) `evaluate_member_access_context`에
`super.foo()` 핸들러 바로 뒤에 미러링한 새 분기 추가 — `find_function_in_hierarchy`
로 함수 찾아서 기존 `SuperFunctionCallContext` 태그로 감싸 반환(다운스트림
소비자 재사용, 새 태그 안 만듦). **검증**: 원래 크래시(`ValueError: This
'PriceAware' is may be array or struct...`) 사라짐. 그 직후 별개의 새 크래시로
진행: `networkx.exception.NetworkXError`(`DynamicCFGBuilder.insert_new_statement_block`
이 그래프에 없는 stale 노드를 조회) — 조사 범위 밖, 이번엔 손 안 댐(위 단발성
표 참고).

**5) `web3bugs_35_H_08` / `web3bugs_35_H_12` — 이 라운드 시점엔 `_is_abstractable`
null-guard만 적용해 부분 해결(진짜 엔진 수정), 별개의 새 크래시로 진행.**
`Domain/Variable.py`의 `_is_abstractable`이 struct 등 non-elementary base
type일 때 `elementaryTypeName`이 `None`인 걸 가드 안 해서 `new <StructType>[](n)`
을 쓰는 첫 케이스에서 크래시하던 버그(qualified-namespace 자체는 무관, red
herring이었음이 이미 확인돼 있었음). 이 시점의 수정: `if et is None: return
False` 가드 한 줄 추가(→ `initialize_not_abstracted_type()`으로 감, sound).
검증 결과 원래 크래시는 사라졌지만 바로 다음 줄에서 별개의 새 크래시로 진행함
확인(당시엔 여기서 멈춤, 조사 범위 밖으로 분류). **→ 2026-09-02 후속 조사로
완전히 해결됨 — 진짜 근본 원인은 `Update.py`의 composite 전체-재할당/체이닝
버그였음(qualified struct 생성자 인식 부재는 그 중간 단계에서 걸린 증상 중
하나였을 뿐), 상세 내용과 최종 수정은 위 "지금 안 되는 케이스" 섹션의
`35_H_08` 항목 참고.**

**6) `web3bugs_52_H_23` — 완전 해결(크래시/파싱 경고 둘 다 사라짐, verdict는 WARNING으로 유지).**
`from`→`_from` 개명(이미 이전 라운드에 완료)에 이어, 중괄호 없는 단일
statement `if` 본문(`if (synth == ISynth(address(0))) synth = synthFactory.
createSynth(...)`, 여러 줄에 걸침)이 `interactiveBlockUnit` 문법 경로에서
`[ANTLR] mismatched input 'synth' expecting '{'` 파싱 경고를 내던 문제 — **코드
문제가 아니라 케이스 데이터 문제로 판정**(이 프로젝트의 다른 모든 working
if-statement가 `if (...) {\n}` 스켈레톤 + 별도 본문 레코드 구조를 쓰는 것과
비교해서 확인). **수정**: contraction `.sol`에서 그 if문에 중괄호 추가, 케이스
JSON을 `soltotestjson.slice_solidity()`로 전체 재빌드(annotation 블록 라인
번호 재계산 포함, `@Debugging BEGIN`=96 불변, `@During` 타겟만 107→114로
이동). **검증**: ANTLR 경고 사라짐, 최종 verdict는 `[INTENT WARNING]`으로
동일(이 두 수정 다 그 특정 `@During` 체크의 정밀도 자체와는 무관해서 예상된
결과) — verdict-mismatch 섹션으로 재분류(아래 참고).

**7) `web3bugs_29_H_11` — AddressSet 비교 narrowing 신규 추가 (진짜 엔진 수정, 전 코드베이스 영향), LocalVar 시딩은 버그 아님으로 판정하고 되돌림.**
`Interpreter/Semantics/Refine.py`의 `_update_comparison_condition`이
narrowing하는 4개 CASE(숫자 interval, 숫자 vs 리터럴 양방향, bool, address-
as-interval)가 전부 `VariableEnv.is_interval(x)`로 게이트돼 있는데, 이 함수가
`AddressSet`을 명시적으로 제외해서 **address 타입끼리의 `==`/`!=` 비교는 이
코드베이스 전체에서 단 한 번도 분기 narrowing이 안 되고 있었음**(`29_H_11`
하나만의 문제가 아니라 전역 정밀도 갭). **수정**: `Refine.py`에 `AddressSet`
import 추가 + CASE 5(AddressSet 비교) 신규 추가 — `==`면 `AddressSet.meet()`
(기존 메소드 재사용)으로 양쪽 다 교집합, `!=`면 한쪽이 singleton일 때 그
반대쪽에서 그 id를 빼는 방식(숫자 interval의 `!=` narrowing과 동일한 패턴),
동일 singleton끼리 `!=`면 모순이라 양쪽 다 bottom. 리터럴(hex 문자열/정수 0
등)을 AddressSet으로 바꾸는 `_coerce_literal_to_addressset` 헬퍼도 신규 추가.
**LocalVar 부분은 되돌림**: `abi.decode` destructure로 생기는 `tokenOut`/
`recipient`/`unwrapBento` 같은 local을 `@LocalVar`로 직접 seed 가능하게 만드는
"pending override" 메커니즘을 만들려다가, **사용자가 이건 unsound하다고
지적**(파라미터가 아닌, 함수 로직으로 계산되는 local을 직접 override하면 그
계산 자체를 건너뛰는 셈이라 디버그 시나리오가 더 이상 실제 도달 가능한 상태를
대표 못 함) — 관련 코드(`Utils/CFG.py`의 `pending_local_debug_overrides`,
`ContractAnalyzer.py`의 등록/적용 로직) 전부 되돌림, `git diff` 확인해서 깨끗함.
이 항목은 "버그"가 아니라 "케이스 설계 결함"으로 재분류(위 단발성 표 1번
참고) — `feedback_debug_seeding_soundness` 메모리에 원칙으로 저장해둠.
**검증**: baseline 20개 회귀 확인(영향 없음, 20/20 유지).

### 2026-09-02, `web3bugs_45_H_01` baseline 회귀 완전 해결 (엔진 수정 + Group 1a 재빌드 + `@During`/`@Post` 문법 오해 정정)

네 단계를 거쳐 해결됨. 각 단계에서 이전 진단이 부분적으로만 맞았다는 게 드러났고,
그때마다 재실행해서 실제로 뭐가 바뀌는지 확인하며 진행함.

**1단계 — `_is_during_inline`의 진짜 엔진 버그(일반적으로 유용한 수정, 적용 완료).**
`Analyzer/SolidityAnalyzer.py:219-242`의 `_is_during_inline`이 "이 줄에 이미 실제
코드가 있는지"를 `full_code_lines[N].strip() != ""`로만 체크해서, 밀려난 함수 skeleton의
닫는 `}`(구조적 문자만 있는 줄)도 "텍스트 있음"으로 오판하고 있었음. 순수 `{`/`}`만 있는
줄은 제외하도록 수정(`target_line != "" and not all(c in "{}" for c in target_line)`
가드 추가). baseline 20개 회귀 확인(18 VIOLATED/2 ERROR, 변동 없음) — 안전하지만
이것만으론 `45_H_01`이 안 풀림(예상대로, 문서가 이미 "Group 1a 재빌드까지 필요"라고
해뒀었음).

**2단계 — 케이스 JSON을 Group 1a 컨벤션으로 전체 재빌드하면서 고아 시드도 같이 수정.**
원래 케이스 JSON은 `@LocalVar`/`@StateVar` 16줄이 `function borrow(...)` 헤더 바로
뒤에 실제 코드보다 먼저 인라인으로 박혀있던 옛날(pre-`@Debugging BEGIN/END`) 방식이었음.
`soltotestjson.py`로 contraction `.sol` 전체를 재슬라이스해서 순수 코드 레코드를 새로
얻고, 디버그 시드 블록을 배열 맨 뒤(`@Debugging BEGIN` = `borrow()` 헤더의 endLine)로
재배치. **재빌드 중 발견한 별개의 케이스 작성 버그**: `@LocalVar account = symbolicAddress
101`이 고아 상태였음 — `borrow(uint256 amount)`는 파라미터가 `amount` 하나뿐이고 함수 전체가
`account`라는 이름을 단 한 번도 안 씀(전부 `msg.sender`로 참조), 근데 `accountBorrows[101]`류
State 시드들은 명백히 이 대출자를 symbolicAddress 101로 잡으려는 의도였음 — `@LocalVar
account = symbolicAddress 101` → `@GlobalVar msg.sender = symbolicAddress 101`로 교체.
재실행하니 원래 크래시(`No CFG node found after line 220`)는 사라졌지만 `@During`
검증에서 새 에러 4개(`varRef(Before): no before-env captured for line N`)가 남음.

**3단계 — `@During`의 `Before`/`After`는 대입문 줄에만 붙을 수 있다는 제약 확인, `Entry`로
바꾸려던 첫 시도는 문법상 원천 불가능임을 확인.** `Interpreter/Engine.py:163-173`의
`_interpret_assignment`만이 `node.before_envs[line]`을 채우는 유일한 지점이라, `@During`을
`require(...)` 줄에 태깅하면 그 줄엔 캡처된 스냅샷이 절대 없음 — `Before`는 "바로 그 줄의
대입 직전 값"이라는 진짜 국소적인 의미였음. 원래 케이스는 이 불변식(`borrowIndex`가
증가했는지)을 함수 전체에 걸친 4개 지점(각 `require` 앞)에서 체크하려 했는데, `borrow()`
안엔 대입문이 함수 끝쪽 6줄에만 몰려있어서 애초에 이 문법으론 표현 불가능한 설계였음.
`Entry`/`After` 조합으로 바꾸면 될 것 같다고 처음엔 제안했으나, **`Parser/Solidity.g4:369-373`을
확인해보니 틀린 제안이었음** — ANTLR 시맨틱 프레디킷으로 `{not self.inDuring}? varRef '('
ENTRY ')'`/`EXIT` 그리고 `{self.inDuring}? varRef '(' BEFORE/AFTER/ASSIGN ')'`가 명시돼
있어서, **`Entry`/`Exit`는 `@Post` 전용, `Before`/`After`/`Assign`은 `@During` 전용으로
문법 자체가 하드 게이팅돼 있음**(`inDuring` 플래그가 `duringIntent`/`postIntent` 진입 시
토글). `@During` 안에 `varRef(Entry)`를 쓰면 그 grammar alternative가 아예 매칭이
안 돼서 `visit()`이 조용히 `None`을 리턴하고, 그게 `clause["lhs"]`로 들어가서
`AttributeError: 'NoneType' object has no attribute 'context'`로 크래시.

**4단계 — 진짜 해결: 4개의 `@During Before/After`를 하나의 `@Post Entry/Exit`로 교체
(완전 해결, VIOLATED 확인).** "함수 진입 시점 대비 지금까지 값이 늘었는지"를 확인하려는
원래 의도 자체가 정확히 `Entry`/`Exit`가 하기 위해 만들어진 일이고, 그건 `@During`이
아니라 `@Post`용 문법임 — 함수 여러 지점에 흩뿌린 4개의 During 대신 `// @Post
borrowIndex(Entry) < borrowIndex(Exit)` 하나로 교체(array 위치는 마지막 실제 코드 줄
바로 뒤, `@Debugging BEGIN` 바로 앞 — 다른 `@Post` 케이스와 동일한 컨벤션). **검증**:
`[POST INTENT VIOLATION] Line 236`(risk=10.0, LHS=RHS=`[1000000000000000001,
1000000000000000001]`, 즉 값이 안 늘어난 것 자체가 위반 — 이 케이스가 원래 잡으려던
버그와 정확히 일치). baseline 20개 재실행: **19 VIOLATED / 1 ERROR**(이전 18/2에서
`45_H_01` 한 건이 VIOLATED로 전환, 다른 19개 결과 전부 동일 — 회귀 없음). 문서가
우려했던 "getBorrowed forward-reference" 별개 이슈는 **실제로는 안 걸림**(2단계 재빌드
이후 크래시 없이 바로 통과) — 문서의 (2)번 우려는 기우였던 걸로 보임, 정정.

### 2026-09-02, `@IReturn` 스코프 한계 확인 + `70_H_05` interface 배열 시딩 버그 발견/수정

**`@IReturn`은 항상 `@Debugging BEGIN` 블록의 "현재" 함수 하나에만 스코프됨 —
콜리 함수의 local interface 변수는 표현 불가(진짜 문법 한계, 버그 아님).**
`Analyzer/ContractAnalyzer.py`의 `_find_interface_name_for_var`(2833-2860행)가
interface 변수를 찾는 범위를 state variable + `self.current_target_function`
(=`@Debugging BEGIN`이 걸린 그 함수) 자신의 param/local, 이 세 곳으로만 제한함 —
콜리 함수의 local은 어디에도 안 걸림. `process_ireturn`/`process_ireturn_cast`
(2862-2948행)도 `ireturn_registry`를 함수 하나(`current_target_function_cfg`)
밑에만 저장해서 애초에 콜리별 registry라는 개념이 없음. `web3bugs_70_H_05`의
`@IReturn oracle.latestRoundData()[...]`가 정확히 이 패턴(`oracle`이 콜리
`getChainlinkPrice()`의 local)이라 걸림. **조치**: 두 설계 대안(함수-한정자
문법 추가 / 케이스 분리) 중 아무것도 구현하지 않고, 사용자가 해당 `@IReturn`
3줄을 케이스 JSON에서 그냥 삭제하기로 결정 — `oracle.latestRoundData()`는
이제 unconstrained Top으로 평가됨(케이스 결과가 VIOLATED 대신 WARNING으로
수렴, 위 §verdict 불일치 섹션 참고).

**그 재실행 중 별개의 진짜 엔진 버그 발견 + 수정: interface 타입 배열의
원소 auto-생성 경로 자체가 없었음(완전 해결, engine 수정).**
`Domain/Variable.py`의 `ArrayVariable._create_new_array_element`(동적 배열
`push`/`.length` 확장/디버그 인덱스 시딩이 새 원소를 만들 때 공통으로 타는
경로)가 `elementary`/`struct`/`enum`/`mapping`/`array`(중첩 배열) 다섯
typeCategory만 분기 처리하고 마지막에 `raise ValueError(f"Unhandled array
base-type for {eid!r}")`로 fallback함 — `interface` typeCategory가 통째로
빠져있었음. `IERC20[]`/`IUniswapV2Pair[]`류 interface 타입 배열에
`@StateVar usdvPairs[0] = symbolicAddress 1`처럼 인덱스를 시딩하면
`get_or_create_element`가 이 함수를 호출 → `ValueError` → 그런데 호출부
(`DebugInitializer._update_left_var_of_literal_context_for_debug`,
~366-388행)가 이미 `except (IndexError, ValueError): return None`으로 감싸고
있어서 예외가 조용히 삼켜지고 `apply_debug_directive_enhanced`가
`[WARNING] Cannot resolve LHS expression`만 찍고 그 시딩을 통째로 스킵함 —
크래시가 아니라 "그냥 아무 일도 안 일어나는" 형태라 오래 안 들켰던 것으로
보임. 그 결과 배열이 실제로는 한 번도 채워지지 않아서, `길이 = "가장 큰
시드된 인덱스 + 1"`로 추론하는 다른 코드 경로도 항상 실패해서
`usdvPairs.length`가 TOP으로 남음. **수정**: `Domain/Variable.py`의
`MappingVariable._make_value`에 이미 있는 `interface` 분기(365-373행,
`Variables` 생성 + `typeInfo` 세팅 + `AddressSet.top()` + `_cast_interface`
태깅)를 그대로 미러링해서 `_create_new_array_element`에 여섯 번째 분기로
추가. **검증**: `70_H_05` 재실행 시 `usdvPairs[0]` 경고 사라지고
`totalPairs = usdvPairs.length`가 TOP 대신 `[1,1]`로 정확히 resolve됨.
**부수 발견**: `web3bugs_70_H_04`(§verdict 불일치, `vaderPairs: IUniswapV2Pair[]`)도
정확히 같은 버그를 갖고 있었음 — 재실행해서 `totalPairs`가 마찬가지로
`[1,1]`로 풀리는 것 확인(그 케이스의 원래 "length 고정 방법이 없다" 진단은
틀렸었음, 위 해당 항목에서 정정). baseline 20개 재실행 확인(18 VIOLATED/2
ERROR, 회귀 없음).

### 2026-09-02, 12-fork 제안 중 6건 사용자 승인 → 적용 (단발성 표 1/5/6/7/11번)

사용자가 12-fork 결과 표를 검토하고 "1,5,6,7,11번은 제안한 수정 방향대로 해줘도
될 것 같아"라고 승인. 4건은 완전히 통과(VIOLATED)까지 확인, 2건(`52_H_23`/
`42_H_01`)은 원래 크래시는 고쳤지만 그 뒤에 별개의 새 크래시가 나와서 §단발성에
남아있음(위 표 참고).

**`web3bugs_35_H_11` — During 레코드 재배치 + 재태깅, 두 단계 원인이었음 (완전
해결, VIOLATED 확인).** 12-fork가 찾은 "During 레코드가 코드 사이에 인라인으로
끼어있어서 고아 CFG 노드가 됨" 원인대로 배열 위치를 `@Debugging BEGIN` 바로
앞으로 옮겼지만, 그것만으로는 여전히 `[INTENT ...]` 출력이 전혀 안 나옴을
확인 — **두 번째, 이번에 새로 발견한 원인**이 있었음: 옮긴 뒤 `startLine=30`
태그가 가리키는 CFG 노드가 `if_join_22`라는, **문장(statement)이 하나도 없는
순수 join 노드**였음(직접 프로브로 확인: `n_stmts=0`). `Interpreter/Engine.py`의
During 체크 실행 경로(~941-945행)가 `for stmt in node.statements: ...
_process_during_annotations(...)` 형태 — 즉 그 노드에 속한 문장을 실행한
**직후에만** intent를 체크하는 구조라서, 문장이 0개인 노드에 붙은 intent는
노드가 정상적으로(고아 아니게) 방문돼도 **절대 체크되지 않음**(에러도 안 남,
그냥 조용히 스킵). 케이스 JSON에서 `@During` 태그를 문장이 실제로 있는 줄(29,
`feeGrowthOutside0` 대입문 — 체크 내용상 실행 순서가 안 바뀌어도 안전)로
재조정해서 해결. **검증**: `[INTENT VIOLATION] Line 29`(risk=10.0,
LHS=[30,30]/RHS=[70,70]) — `phase_reviews/07_web3bugs_35_H_11/analysis.md`가
기대하던 VIOLATED와 일치. **일반화 여지**: "During intent를 문장 없는 CFG
노드(join/branch 노드)에 붙이면 조용히 안 체크됨"은 `35_H_11`만의 문제가 아니라
케이스 작성 시 일반적으로 주의해야 할 함정으로 보임 — 근본적으로 고치려면
`_process_during_annotations`를 문장 유무와 무관하게 노드 진입/이탈 시점에도
호출하도록 `Interpreter/Engine.py`를 손봐야 하는데, 이번엔 케이스 데이터
재태깅만으로 해결(엔진 코드 변경 없음).

**`web3bugs_52_H_23` — mapping key 타입에 `identifierPath`(contract/interface/enum) 지원 추가 (진짜 엔진 수정, 부분 해결 — 원래 크래시만 사라짐).**
`Parser/Solidity.g4:203-205`의 `mappingKeyType: elementaryTypeName |
identifierPath;`는 이미 identifierPath를 허용하는데,
`Analyzer/EnhancedSolidityVisitor.py`의 `visitMappingKeyType`이
`ctx.elementaryTypeName()`만 처리하고 나머지는 무조건 `ValueError`를 던지고
있었음 — 문법과 visitor가 서로 어긋나 있던 상태. **수정**: `ctx.identifierPath()`
분기 추가, 새 `SolType()`을 만들어 기존 `visitUserDefinedType`(struct/enum/
interface/contract 이름을 이미 올바르게 구분해서 처리하는 헬퍼)에 위임 —
새 로직을 만들지 않고 이미 검증된 경로를 재사용. **검증**: `mapping(IERC20 =>
bool)` 파싱 크래시 사라짐, 다음 줄(`function mintSynth(..., address from,
...)`)에서 `from` 예약어 문제로 별개 크래시.

**`web3bugs_52_H_23` (2단계) — `from` 예약어 크래시, 케이스 데이터에서 `_from`으로 개명 (데이터 정리, 부분 해결 — 또 다른 별개 크래시 하나 더 사라짐).**
`Solidity.g4`의 `'import' ... 'from' importPath` 규칙이 `'from'`을 리터럴 토큰으로
등록해버려서 `identifier` 규칙만으론 일반 식별자(파라미터 이름)로 못 씀 —
`revert`류처럼 예외 허용 목록에 추가하는 게 문법 차원의 정석 수정이지만, 그러려면
`Solidity.g4` 재생성이 필요해서 더 무거움. 대신: `ContractAnalyzer.analyze_context`가
`import` 라인 자체를 분석 대상에서 아예 제외하고(주석: "pragma, import는 contract
밖이므로 분석 불필요"), `EnhancedSolidityVisitor`의 import 관련 visit 메소드들도
전부 빈 `visitChildren` no-op이라 이 프로젝트에서 import 문은 애초에 의미 있게
처리되는 게 없음을 확인 — 게다가 `evaluation/RQ1/target_contracts_contraction/`
와 `evaluation/RQ1/cases/`를 전수 검색해서 `import ... from ...`(symbol-alias)
형태가 단 하나도 없음을 확인함(있는 건 `52_H_04`/`52_H_34`의 `import "path";`
단순형뿐, `from` 키워드 자체를 안 씀). 즉 `from`이 이 파이프라인에서 실제 import
문법으로 쓰일 일이 전혀 없으므로, 파라미터 이름을 `from` → `_from`으로 바꾸는 게
문법을 건드리는 것보다 훨씬 안전한 워크어라운드 — contraction `.sol`의 파라미터
선언/본문 사용처, 케이스 JSON의 같은 두 곳 + `@LocalVar from = ...` 시드까지 전부
동기화해서 개명. **검증**: `from` 크래시 사라짐, baseline 20개 회귀 확인(19
VIOLATED/1 ERROR, 변동 없음 — `52_H_23`은 baseline 세트 밖이라 직접 영향 없음).
그 직후 또 다른, 완전히 별개인 새 이슈로 진행(위 단발성 표 참고, 손 안 댐): 중괄호
없는 단일 statement `if` 본문에서 `[ANTLR] mismatched input 'synth' expecting
'{'`(경고 수준, 크래시 아님 — `[INTENT WARNING]`으로 완주는 함).

**`web3bugs_83_H_01` — struct 배열 원소의 `initialize_struct()` 호출 누락 + 두 곳의 struct_defs 전파 gap (진짜 엔진 수정, 완전 해결, VIOLATED 확인).**
원래 문서(`Evaluation.py:1959` 파싱 크래시)는 **케이스 JSON 자체의 chunker
버그**였음(엔진 버그 아님) — `poolInfo.push(\n  PoolInfo({...})\n);` 같은 여러
줄짜리 struct-literal push를, `soltotestjson.py`의 `slice_solidity()`가 `PoolInfo({`
줄이 `{`로 끝난다는 이유로 "블록 헤더"로 오인식해서 statement 하나를 레코드
두 개로 잘못 쪼갬 — contraction `.sol`에서 이 statement를 한 줄로 합쳐서
청커가 정상적으로 한 레코드로 처리하게 만들고, 케이스 JSON을 그 지점부터
전체 재빌드(annotation 블록 라인 태그 재계산 포함, `@Post` 태그만 36→28로
이동, 나머지 debug 블록은 함수 헤더 위치가 안 바뀌어서 그대로)해서 해결.
그 다음 드러난 **진짜 엔진 버그 2가지**(둘 다 이번에 새로 발견): (1)
`Utils/Helper.py`의 `VariableEnv.copy_single_variable`의 `ArrayVariable` 분기가
`struct_defs=`/`enum_defs=`를 새 객체 생성 시 아예 안 넘김(바로 아래
`MappingVariable` 분기는 이미 넘기고 있어서 비대칭) — 모든 `copy_variables()`
호출(branch/join/widen마다 발생)마다 배열의 struct_defs가 조용히 리셋됨.
(2) `Interpreter/Semantics/DebugInitializer.py`의 `_create_array_element_with_bottom`
(`.length = N`으로 배열을 확장할 때 새 슬롯을 채우는 헬퍼)이 struct 타입
원소를 만들 때 `initialize_struct()`를 아예 호출 안 해서 필드가 통째로
빈 채로 남음(struct_defs 유무와 무관하게 항상 발생하는, 더 근본적인
누락) — `@StateVar poolInfo.length = [2,2]` 세팅 시점에 index 1의 `PoolInfo`
struct가 이 경로로 만들어지고 있었음. 같은 파일의 배열-인덱스 조회 두
경로(`_update_left_var_of_literal_context_for_debug`/
`_update_left_var_of_identifier_context_for_debug`)에도 `MappingVariable`
분기엔 있는 struct_defs 백필이 `ArrayVariable` 분기엔 없어서 같이 추가함
(대칭 맞춤, 예방적 수정). **검증**: `[POST INTENT VIOLATION] Line 28`
(risk=10.0, LHS=[0,0]/RHS=[20000000000000,20000000000000]). baseline 20개
재실행 확인(18 VIOLATED/2 ERROR, 회귀 없음) — `copy_single_variable`이
전역적으로 많이 쓰이는 함수라 특히 주의 깊게 확인함.

**`web3bugs_42_H_01` — 케이스 JSON 전체 재빌드 (데이터 정리, 부분 해결 — 원래 크래시만 사라짐).**
`Modifier 'updateDebt' is not defined` 크래시 원인 확인: 케이스 JSON이
`modifier updateDebt`뿐 아니라 `accrueDebt`/`liveDebtIndex`/`mintFeeToPool`/
`_liquidatable` 함수 전체를 빠뜨린 채로 멈춰있었음(contraction `.sol`엔 전부
있는데 JSON엔 state 변수 선언 다음으로 바로 `function borrow(...)`가 나옴) —
`case_progress.md`가 지목한 대로 relation 변경 후 JSON을 재빌드 안 한 것,
엔진 버그 아님. 현재 contraction `.sol` 전체를 `soltotestjson.py`로 재슬라이스
하고 `@During`/`@Debugging` 블록을 새 라인 번호로 재태깅해서 전체 재빌드.
**검증**: 원래 크래시 사라지고, 문서가 예측했던 대로 다음 블로커가 정확히
그대로 나옴(`'denominator' not in struct 'lf'`, 위 단발성 표 참고, 손 안 댐).

**`web3bugs_62_H_10` / `web3bugs_192_H_01` — `@Debugging BEGIN` 블록을 올바른 함수로 재배치 (데이터 정리, 완전 해결, 둘 다 VIOLATED 확인).**
두 케이스 다 `@Debugging BEGIN`/`@StateVar`/`@GlobalVar`/`@LocalVar`/
`@Debugging END` 블록의 `startLine` 태그가 대상 함수(각각
`creatorClaimSoldTokens`/`extendLock`)가 아니라 그 함수가 호출하는 다른
함수(`lockInternal()`/`claim(...)`)의 진입점을 가리키고 있어서, 디버그
시나리오 시딩이 전부 엉뚱한 함수 스코프에 적용되고 있었음 — `@Post`
자체는 원래도 올바른 위치에 있었음(대상 함수 소속). 케이스 JSON에서
`@Debugging BEGIN`의 `startLine`을 대상 함수의 헤더 endLine으로 재태깅하고
(`62_H_10`: 24→34, `192_H_01`: 24→31), 그 뒤 debug 레코드들도 순차적으로
재태깅. **검증**: `62_H_10` → `[POST INTENT VIOLATION] Line 46`(risk=10.0,
LHS=[1000,1000]/RHS=[0,0]). `192_H_01` → `[POST INTENT VIOLATION] Line 34`
(risk=10.0, LHS=[100,100]/RHS=[110,110]) — 단, `_asset`(로컬 변수, `address
_asset = claim(_id);`로 함수 중간에 생성됨)의 `@LocalVar` 시딩은 여전히
`related_variables`에 없어서 `[WARNING] Cannot resolve LHS expression`이
뜨지만, `@Post` 체크 자체는 시딩과 무관하게 정상적으로 VIOLATED를 잡아냄
(이 local-var 시딩 갭은 `29_H_11`에서 이미 별도로 추적 중인 기존 이슈,
위 단발성 표 1번 참고 — 새로 발견한 문제 아님).

### `web3bugs_56_H_02` — `@Post` 옛 grammar 텍스트 치환 (2026-09-01, 데이터 정리 — 엔진 코드 변경 없음)

12-fork 재조사에서 확정된 원인(위 baseline 회귀 섹션 참고)대로 사용자가 바로
적용을 승인함: 케이스 JSON(`evaluation/RQ1/cases/web3bugs_56_H_02/web3bugs_56_H_02.json`)
`startLine 46`의 `@Post` 줄을 옛 문법 `_self.totalCredit(Entry <= Exit)`에서
새 문법 `_self.totalCredit(Entry) <= _self.totalCredit(Exit)`으로 텍스트
치환(같은 줄 안 치환이라 `startLine`/`endLine` 재계산 불필요).

**검증**: `main.py`로 단독 실행 시 `[POST INTENT VIOLATION]`(risk=10.0,
`LHS=[1000,1000]` vs `RHS=[200,200]`)로 정상 완주 — 원래 파싱 크래시
사라짐. `evaluation/RQ1/run_all.py` 전체 재실행으로 18 VIOLATED / 2 ERROR
확인(이전 17 VIOLATED / 3 ERROR에서 `56_H_02` 한 건만 VIOLATED로 전환, 다른
19개 케이스 결과 전부 동일 — 회귀 없음). `evaluation/RQ1/rq1_results.csv`
자동 갱신됨. 남은 baseline ERROR 2건(`45_H_01`/`51_H_02`)은 위 표 참고.

(참고: 이 파일에 `using CDP for Data;`가 `struct Data`보다 앞서는 비슷한
forward-reference 패턴도 있지만, 실행이 46행까지 정상 도달하는 걸 보면
`using X for Y;`는 바인딩 시점에 `Y`를 즉시 resolve할 필요가 없어서 이
케이스에선 문제를 안 일으킴 — 별도 수정 불필요, red herring.)

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

### Group D — `StaticCFGFactory.make_param_variable`에 mapping 타입 파라미터 지원 추가 (2026-09-01, 진짜 엔진 수정)

이번엔 데이터 정리/워크어라운드가 아니라 **실제 엔진 코드 수정**. 사용자가
먼저 방향을 제안: mapping 타입 파라미터를 만난 함수의 `related_variables`에
동적으로 등록해야 하는지, CFG 노드에 등록해야 하는지, state variable node에
등록해야 하는지 헷갈린다며, `make_param_variable`(`Analyzer/
StaticCFGFactory.py:310`)에 mapping 분기를 추가하되 mapping 내부 dict는
해당 key를 실제로 만나는 시점에 lazy하게 만들면 되지 않겠냐고 먼저 방향을
제시하고 의견을 물음.

**조사 결과, 사용자 판단이 맞았음을 확인**:
- **등록 위치**: `make_function_cfg`(`StaticCFGFactory.py:234-307`)를 보면
  일반 파라미터(array/struct/enum/elementary)도 이미 "함수 CFG 빌드 시점에
  1회, `fcfg.add_related_variable(var)`로 `related_variables`에 등록 →
  `entry_env`/`entry_node.variables`로 복사"라는 범용 파이프라인을 타고
  있음. state 변수는 `state_variable_node.variables`가 원본이고
  `_inject_state_vars`가 그걸 `related_variables`로 복사해 넣는 것뿐 —
  파라미터는 애초에 다른 원본이 없어서 `related_variables`가 곧 원본. 즉
  mapping 파라미터도 이 기존 파이프라인에 얹으면 되고, 새로운 등록 경로가
  필요 없었음.
- **dict lazy 생성**: `MappingVariable.__init__`(`Domain/Variable.py:284`)은
  `self.mapping = {}`를 빈 채로 만들고, `get_or_create`(400행)가 실제 key
  접근 시점에 `_make_value`로 값을 생성 — Evaluation.py의 여러 곳(268/887/
  1108/1532행 등)이 이미 이 패턴으로 state-var mapping을 다루고 있어서,
  파라미터용으로 새 lazy 로직을 만들 필요 없이 그대로 재사용됨.
- **aliasing 문제**: Solidity의 `mapping storage` 파라미터는 caller의 실제
  mapping을 aliasing해야 하는 게 정석 시맨틱스지만, `make_param_variable`의
  기존 ① array 분기도 storage 배열 파라미터를 caller와 잇지 않고 독립적인
  fresh TOP 값으로 근사하고 있어서, mapping도 같은 컨벤션(진짜 aliasing 없이
  fresh & empty `MappingVariable`)으로 가는 게 이 코드베이스의 기존 설계와
  일관됨 — `abi.decode`/`.call()`이 TOP으로 degrade하는 것과 같은 계열의
  트레이드오프이지 새로 만드는 비일관성이 아님.

**수정**: `make_param_variable`에 ⑥ mapping 분기 추가 — `an.get_full_struct_enum_defs()`
(Group B 수정 때 만든 공용 헬퍼)로 struct_defs/enum_defs를 채운 빈
`MappingVariable`을 만들고 `an.register_var()` 호출 후 리턴. 그 외 아무것도
안 건드림(related_variables/entry_node 파이프라인은 이미 범용이라 무관).

**검증**: `web3bugs_35_H_11` — 원래 크래시(`Unsupported typeCategory
'mapping'`) 사라지고 끝까지 완주(EXIT 0). `web3bugs_3_H_05` — 원래 크래시
사라지고 새로운 별개 크래시(`PriceAware` 라이브러리 식별자 resolve 실패,
mapping과 무관)로 진행 — Group B/C/F 수정 때와 같은 "버그 고침 ≠ 케이스
통과" 패턴, §단발성에 재분류함. baseline 20개(`evaluation/RQ1/run_all.py`)
재실행으로 17 VIOLATED/3 ERROR 그대로 유지, 회귀 없음 확인.

**`35_H_11`의 "During 체크 안 찍힘" 원인, 2026-09-01 재조사로 확정됨**:
mapping 파라미터 지원 추가와는 무관 — `62_H_10`/`192_H_01`과 같은 계열이지만
정확히 같은 패턴은 아닌, **Group 1a와 완전히 같은 종류의 케이스 작성 버그**
로 확인됨. 이 케이스의 `@During` 레코드가 "코드 전체 뒤, `@Debugging BEGIN`
바로 앞"이라는 확정된 컨벤션을 안 따르고 실제 코드 레코드들 사이에 인라인으로
끼어있어서(line-29/line-31 레코드 사이), replay 시점에 `_is_during_inline`이
`False`를 리턴 → 진짜 라인-삽입 경로를 탐 → During 인텐트가 붙는 CFG 노드가
실제 함수 그래프에서 끊긴 고아 노드가 됨(노드 id 직접 대조로 확인: 붙은 노드가
`_run_worklist`가 실제로 방문하는 노드 목록에 전혀 없음) → 조용히 한 번도
안 체크됨. `29_H_11`의 `@During`은 이미 올바르게 배치돼 있어서 이건 전역
회귀가 아니라 `35_H_11` 하나가 컨벤션 확립 이전에 작성된 문제 — 수정 방향은
위 §단발성의 `35_H_11` 항목 참고(데이터 정리, `@During` 레코드를
`@Debugging BEGIN` 바로 앞으로 재배치).

### Group G — `Interval.copy()`가 `type_length`를 안 넘기던 버그 (2026-09-01, 진짜 엔진 수정)

사용자가 `web3bugs_29_H_11`의 크래시를 보고 127행의 `uint32(block.timestamp %
2**32)` 캐스팅이나 `&&` 연산 처리가 잘못된 게 아니냐고 먼저 가설을 제시,
`_blockTimestampLast`(uint32)가 evaluate될 때 뭔가 이상한 것 같다고 지적.

**직접 확인 결과, 캐스팅/`&&` 둘 다 원인이 아니었음**: `Utils/Helper.py`의
`_merge_by_mode`(join 실패 지점)와 `Interpreter/Semantics/Refine.py`의
`_update_comparison_condition`/`refine_intervals_for_comparison`(조건
narrowing 지점)에 임시 프로브를 넣어 추적함(작업 후 전부 원복).
`if (blockTimestamp != _blockTimestampLast && ...)`의 true 분기에서
`_blockTimestampLast`(uint32, `[0, 2^32-1]`, type_length=32)를 narrowing하는
과정에서 `refine_intervals_for_comparison`(`Refine.py:311`)이 맨 위에서
`A, B = a_iv.copy(), b_iv.copy()`를 호출하는데, **`Interval.copy()`
(`Domain/Interval.py:54-55`)가 `type(self)(self.min_value,
self.max_value)`로 `type_length`를 안 넘기고 있었음** —
`IntegerInterval`/`UnsignedIntegerInterval.__init__`이 `type_length=256`을
디폴트로 갖고 있어서, 32비트였던 값이 조용히 256비트로 바뀌어버림(narrowing
자체의 min 값 계산(`0`→`1`)은 정상이었음 — 순전히 타입 폭만 깨짐). else
분기(안 건드려진 32비트 값)와 join할 때 폭이 안 맞아서 크래시.

**`web3bugs_52_H_04`/`web3bugs_52_H_34`의 `roundID`(uint80) 크래시도 같은
버그로 확인** — 이전에 트리아지 문서에 "근본 원인이 다를 수 있다"고 적어뒀던
게 틀렸음, `require(answeredInRound >= roundID, ...)`의 `>=` narrowing에서
같은 `.copy()` 경로를 타서 똑같이 256으로 깨짐. 세 케이스 다 한 줄짜리
같은 버그.

**수정**: `Interval.copy()`를 `type_length`를 보존하도록 수정. 단, `type(self)
(min, max, self.type_length)`처럼 3번째 위치 인자로 바로 넘기면 `BoolInterval`
(`type_length` 인자를 안 받는 생성자)이 깨지므로, 생성 후 속성으로
`new_obj.type_length = self.type_length`를 별도로 설정하는 방식으로 함 — 모든
`Interval` 서브클래스에서 안전.

**검증**: `web3bugs_29_H_11` — 원래 크래시 사라지고 EXIT 0로 완주. 다만
`[WARNING] Cannot resolve LHS expression`(로컬 var 3개) +
**`[INTENT ERROR] Line 161/168: 'NoneType' object has no attribute
'is_bottom'`**가 남음 — 두 줄 다 이번 리비전에서 새로 만든 `varRef(Before)`
스냅샷 문법을 쓰는 `@During` 체크(이 `[INTENT ERROR]`는 바로 아래 항목에서
같은 날 추가로 RESOLVED됨). `web3bugs_52_H_04`/`web3bugs_52_H_34` — 원래
join 크래시 사라지고 새 크래시(`sumNative` 식별자 미해결, mapping/
`Interval.copy()`와 무관)로 진행. 셋 다 §단발성에 재분류함(자세한 내용은
그쪽 참고). `.copy()`가 `Refine.py`/`Evaluation.py`/`Domain/Variable.py`/
`Utils/Helper.py`/`Interpreter/Semantics/DebugInitializer.py` 등 여러 곳에서
쓰이고 있어서 파급 범위를 걱정했으나, baseline 20개(`evaluation/RQ1/
run_all.py`, 17 VIOLATED/3 ERROR 그대로) + 이번 세션에 손댄 케이스 20개
전체 spot-check(에러 시그니처 전부 기존 문서와 정확히 일치, 새 회귀 없음)로
확인함.

### `GuardianVerificationEngine`에 `_materialize_snapshot_refs` 추가 — 중첩된 `varRef(Before/Entry/Exit/After/Assign)`가 조용히 `None`으로 새던 버그 (2026-09-01, 진짜 엔진 수정)

바로 위 `Interval.copy()` 수정 이후에도 `web3bugs_29_H_11`에 남아있던
`[INTENT ERROR] Line 161/168: 'NoneType' object has no attribute
'is_bottom'`을 조사하다 발견함. `web3bugs_35_H_11`의 "During 체크가 아예 안
찍힘" 증상도 같은 새 grammar 기능(`varRef(Before)` 등, 이번 리비전에 추가된
"snapshot-qualified reference" — `engine_code_changes.md`의 "New feature"
섹션 참고)을 쓰고 있어서 처음엔 같은 근본 원인일 거라 의심했으나, **실제
조사 결과 서로 다른, 독립적인 두 버그**로 확인됨(`35_H_11`은 아래 §Group D
항목 참고, 케이스 작성 문제).

**`29_H_11`쪽 원인**: `GuardianVerificationEngine.evaluate_guardian_expression`
의 디스패치가 최상위 expr의 context가 5개 snapshot 컨텍스트
(`VarRefAtEntry/Exit/Before/After/Assign`) 중 하나가 아니면 서브트리 전체를
통째로 일반 평가기(`Interpreter/Semantics/Evaluation.py`)로 위임하는데,
그 일반 평가기는 이 5개 컨텍스트를 전혀 모름(`elif` 체인 어디에도 안 걸리고
암묵적으로 `None` 리턴). `amount1 == amount1(Before) + (... * (balance1 -
amount1(Before))) / (...)`처럼 `(Before)`가 최상위가 아니라 더 큰 산술식
안에 **중첩**되면, 최상위 `+`/`/` 노드가 통째로 일반 평가기로 넘어가고,
그 평가기가 재귀하다가 중첩된 `amount1(Before)` 노드를 만나 조용히 `None`을
리턴 → `balance1 - None`이 `Interval.subtract()` 내부의 `_bottom_propagate`
에서 `None.is_bottom()`을 호출하며 크래시. 프로브로 직접 확인:
`leftInterval=balance1(정상 Interval)`, `rightInterval=None (expr.right
context='VarRefAtBefore')`.

**설계 검토(사용자와 논의 후 확정)**: "A안"(Guardian 쪽이 모든 expression
shape을 직접 재귀 순회 — 삼항/함수호출/튜플 등)은 `Evaluation.evaluate_expression`
의 dispatch 테이블을 사실상 통째로 미러링해야 해서 유지보수 부담이 큼.
대신 "B안"을 채택: `Domain/IR.py`의 `Expression`이 자식을 담을 수 있는
필드가 고정되고 유한함(`left/right/function/arguments/base/index/
start_index/end_index/expression/condition/true_expr/false_expr/elements`)
을 이용해서, expr 트리를 **구조적으로만**(의미는 몰라도 됨) 순회하면서
5개 snapshot 컨텍스트 노드를 찾아 **먼저 계산해서 합성 변수로 치환**한 뒤,
그렇게 만들어진(이제 env가 하나뿐인) 트리 전체를 기존 일반 평가기에 한 번에
넘김 — "여러 env가 섞인 문제"를 "치환 한 번으로 env 하나만 남는 문제"로
먼저 풀어버리는 방식. struct 필드/array 원소를 `(Before)`로 감싸는 경우
(`s.field(Before)` 등 — `varRef : identifier subAccess*`라서 문법적으로
허용됨, `Parser/Solidity.g4:379-386` 확인)와, 같은 함수 안 다른 라인의
`(Before)`가 서로 안 섞이는지(`Interpreter/Engine.py`가 이미 clause 단위로
`guardian._before_cfg_node`/`_before_line_no`를 매 검증 호출 직전에 새로
세팅함, `_verify_during_annotation`/`_verify_during_clause_dynamic` 확인)
둘 다 사전에 검토해서 B안이 안 깨지는 것 확인 후 구현.

**구현**: `Analyzer/GuardianVerificationEngine.py`에 `_materialize_snapshot_refs`
(구조적 트리 순회 + 치환)와 `_clone_expr_with`(원본 트리 불변 유지를 위한
얕은 복사 헬퍼 — 파스 트리는 여러 CFG fixpoint 반복/여러 line에서 재사용되는
공유 객체라 in-place mutation은 위험) 추가. `evaluate_guardian_expression`
의 두 위임 분기(`NormalVarRef`/`IntentMemberAccess`/`IntentIndexAccess`와
최종 `else`)를 하나로 합쳐서, 위임 직전에 항상 이 치환을 먼저 거치도록 수정.

**검증**: `web3bugs_29_H_11` — `[INTENT ERROR]`가 완전히 사라지고 정상적인
`[INTENT WARNING]`(LHS/RHS 다 실제 계산된 값)로 이어짐. baseline 20개 +
이번 세션에 손댄 케이스 20개 전체 spot-check로 회귀 없음 확인. **다만
`web3bugs_35_H_11`은 이 수정으로 안 고쳐짐** — 완전히 다른 원인(아래 §Group D
항목의 2026-09-01 추가 내용 참고, 케이스 작성 문제로 확정).

**남은 사소한 이슈(별개, 안 고침)**: `29_H_11`의 `[INTENT WARNING]` 메시지에
`amount1 == <Domain.IR.Expression object at 0x...> → warning`처럼 RHS가
안 예쁘게 찍힘 — `_pretty_expr`(`getattr(expr, "identifier", "") or
str(expr)`)가 `.identifier`가 없는 복합 expression은 못 다루는, 이번 수정과
무관한 기존부터 있던 프리티프린팅 버그. 값 계산 자체는 정상.

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
