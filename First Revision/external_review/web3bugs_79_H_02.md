# 리뷰 기록: `web3bugs_79_H_02` 케이스 livelock (결론: CFG 빌더 버그, ANTLR 무관)

이 문서는 원래 다른 LLM에게 두 번째 의견을 구하려고 작성한 리뷰 요청서였습니다(§1-8).
그 리뷰에서 나온 지적을 검증하고 제안받은 실험을 실행하는 과정(§9)에서, 최종적으로는
전혀 다른, 진짜 원인을 찾았습니다(§10) — **ANTLR과는 완전히 무관한, `Analyzer/DynamicCFGBuilder`의
CFG 연결 버그**였습니다. §1-9는 그 과정의 기록으로 남겨둡니다(틀렸던 가설도 왜 그럴듯해
보였는지, 어떻게 반증됐는지가 나중에 참고할 가치가 있어서). **결론만 필요하면 §10으로
바로 가세요.**

## 1. 프로젝트 배경 (필요한 만큼만)

**IntentChecker**는 Solidity 스마트컨트랙트용 정적 분석기입니다. 구간(interval) 기반
추상 해석(abstract interpretation)으로 컨트랙트를 분석하고, 소스에 `@During`/`@Post` 같은
"의도(intent)" 주석을 달아서 "이 시점에 이 값이 이래야 한다"를 명세하면, 분석기가 그 의도가
위반되는지 여부를 판정합니다.

테스트 케이스는 `.sol` 소스 전체가 아니라, "한 줄(또는 한 statement)씩 순서대로
추가해나가는 편집 이벤트 목록"을 담은 JSON입니다. `main.py`가 이 JSON을 읽어서 레코드
하나마다: (1) 내부 소스 버퍼 갱신 → (2) 그 레코드 자신의 코드 조각만 ANTLR로 파싱 →
(3) 파스 트리를 방문(visit)해서 CFG/변수 상태를 갱신, 을 반복합니다.

## 2. 증상

`web3bugs_79_H_02.json`을 `main.py`로 실행하면 **크래시가 아니라 멈춥니다**(livelock)
— 프로세스가 CPU를 100% 가까이 계속 쓰면서 끝나지 않습니다.

## 3. 최초 관찰 (나중에 틀린 것으로 밝혀짐, §9-10 참고)

- Python의 `faulthandler.dump_traceback_later`로 실행 중 스택을 두 번 독립적으로
  샘플링했을 때, 두 샘플 모두 **ANTLR4 런타임 내부**(`antlr4.atn.ParserATNSimulator.closure_`,
  `antlr4.PredictionContext.merge`/`mergeArrays`)에 멈춰 있는 것으로 보였습니다.
- 케이스 JSON에서 `_atPhase(_phase);`(`modifier atPhase(uint8 _phase) { _atPhase(_phase); _; }`의
  본문) 레코드를 처리하는 지점에서 멈췄습니다.
- 그 한 줄을 완전히 독립된 새 프로세스에서 단독으로 파싱하면 16ms만에 끝났습니다 — 그래서
  "이 statement 자체가 아니라 누적된 무언가"라는 방향으로 추측했습니다.

## 4. 최초 가설 (틀림 — §9-10에서 반증)

이 프로젝트가 쓰는 ANTLR4-Python 파서 클래스는 `atn`뿐 아니라 `decisionsToDFA`,
`sharedContextCache`도 클래스 레벨(class-level)로 정의해서, 같은 프로세스 안에서 생성되는
모든 파서 인스턴스가 이 캐시들을 공유합니다. "이 프로젝트가 파서를 프로세스 하나 안에서
수백 번 새로 만드는데 그 공유 캐시는 절대 리셋 안 되니까, `PredictionContext` 병합 비용이
누적돼서 어느 시점에 조합적으로 폭발한다"는 가설을 세웠습니다.

## 5. 반증 실험 1 — 사용자의 소스 재포맷 가설 테스트 (결과: 기각, 그런데 원래 가설 반증은 아니었음)

사용자가 "원래 소스가 지저분하게 포맷돼 있어서(여러 줄 statement, `} else`가 같은 줄
등) 그런 게 원인 아니냐"는 가설을 냈습니다. `.sol`을 손으로 정리한 뒤 케이스를 재빌드해서
다시 실행 — **여전히 멈춤.** 케이스 JSON을 만드는 청커가 여러 줄 statement를 파싱 전에
이미 레코드 하나로 합치기 때문에(포맷과 무관하게) 재포맷 전/후 레코드 개수가 112개로
완전히 동일했고, 그래서 이건 애초에 "총 파싱 호출 횟수"에 영향을 주지 않는 실험이었습니다.

## 6. 다른 LLM 리뷰어에게 검토 요청, 지적 두 가지 (둘 다 맞았음, §9에서 코드로 검증)

이번 세션에 문법 파일(`Solidity.g4`)의 `arithFactor` 규칙에 `varRef(Entry/Exit/Before/
After/Assign)`라는 새 alternative 5개가 추가된 게 이 livelock과 시간상 겹쳐서 의심했는데,
다른 LLM에게 §1-8 내용으로 리뷰를 요청했더니 두 가지를 정확히 반박했습니다:
1. "누적 소스 전체를 매번 재파싱한다"는 설명이 틀렸다 — 각 호출은 그 레코드 자신의 작은
   텍스트만 파싱할 것이다.
2. `arithFactor`는 `_atPhase(_phase);` 같은 일반 statement가 타는 문법 경로와 완전히
   분리돼 있고, `arithFactor` 자체도 좌재귀가 아니다 — 진짜 좌재귀 후보는 `expression`
   규칙 쪽이다.

## 7. 코드로 직접 검증 (둘 다 확인됨)

- `main.py:176`을 읽어보니 `ParserHelpers.generate_parse_tree(code, ctx, True)`의 `code`는
  `rec["code"]`, 즉 그 레코드 자신의 텍스트일 뿐이었습니다. 임시 로그로 확인: 문제의
  레코드는 `chars=17 lines=1 '_atPhase(_phase);'` — 정확히 17글자짜리 단독 statement.
- `Parser/Solidity.g4`를 읽어보니 `arithFactor`는 `@During`/`@Post` 전용 문법
  (`intentValue → arithExpr → arithAdd → arithTerm → arithFactor`)에만 있고,
  `_atPhase(_phase)`는 `expression: expression callArgumentList #FunctionCall`
  (`Solidity.g4:601`, 원래부터 있던 별도의 좌재귀 규칙)을 탑니다. `arithFactor` 자체도
  자기참조가 없어서 좌재귀가 아닙니다.

## 8. 결정적 실험 — fresh DFA/PredictionContextCache 주입 (결과: 가설 반증)

다른 LLM이 제안한 실험: 매 `generate_parse_tree` 호출마다 그 호출 하나에서만 쓸 완전히
새 `ParserATNSimulator`(새 DFA 배열 + 새 `PredictionContextCache`)를 주입해서 "이전
호출들과 공유되는 예측 상태가 전혀 없는" 상태로 파싱. 추가로 렉서(`SolidityLexer.py`에도
같은 구조의 class-level `decisionsToDFA`가 있는 걸 발견해서) 쪽에도 똑같이 적용.

**결과: 파서·렉서 둘 다 완전히 새 예측 상태를 줘도 정확히 같은 지점에서 여전히 멈춤**
(180초 넘게 대기). "공유 캐시가 원인"이라는 원래 가설은 이걸로 상당 부분 반증됐다고
판단했습니다 — 그런데 진짜 원인은 아직 못 찾은 상태였습니다.

## 9. 실제로 멈추는 지점을 다시 찾음 — 파싱은 결백했음

사용자가 "그냥 소스코드/케이스 JSON 자체를 자세히 들여다보자"고 제안해서, 파싱 단계를
완전히 격리해서 재현했습니다. `main.py`의 한 레코드 처리는 (1) `sa.update_code(...)`
(2) `ctx = contract_analyzer.get_current_context_type()` (3) `generate_parse_tree(code,
ctx, True)` (4) `EnhancedSolidityVisitor(...).visit(tree)` 순서인데, 문제의 레코드
직전까지(78개 레코드)를 실제 파이프라인으로 그대로 재생한 뒤 (1)~(3)만 따로 호출해보니
**전부 10ms 이내로 즉시 끝났습니다.** 파싱 자체는 처음부터 결백했습니다 — §3-8에서
조사한 방향 전체가 틀린 곳을 보고 있었던 것입니다.

## 10. 최종 결론 — 진짜 원인은 CFG 빌더의 `else { revert(...) }` 연결 버그

진짜 멈추는 지점은 (4) `visit(tree)` 안이었고, 거기서 다시 faulthandler를 떠보니:

```
Interpreter/Engine.py:829 in _run_worklist
  ← networkx predecessors()
Interpreter/Engine.py:685 in interpret_function_cfg
Evaluation.py:2158 in evaluate_function_call_context
ContractAnalyzer.py:1721 in process_function_call
```

`_atPhase(_phase);`를 해석하면서 `_atPhase()` 함수 자체를 인터프리트하려고
`_run_worklist`(CFG worklist 순회)에 들어가는데, 거기서 **진짜 무한루프**에 갇혀
있었습니다. `_atPhase()`의 CFG를 직접 덤프해서 정확한 원인을 찾았습니다:

```
else_block_109   succs=['ERROR']                                    # else { revert(...) } 블록
revert_110       n_stmts=1  preds=[]  succs=['else_if_join_106']     # revert 문 자체 (고아!)
else_if_join_106 join=True  preds=['require_true_107', 'revert_110']
```

`_atPhase()`는 `if/else if/else if/else if/else`(4단 중첩) 구조인데, 마지막
`else { revert("..."); }` 블록의 CFG 연결이 잘못됐습니다 — `else_block_109`가
`revert_110`(revert 문 노드)을 거치지 않고 곧장 `ERROR`로 가버려서, `revert_110`이
**preds가 아예 없는 고아 노드**(그래프상 영원히 도달 불가능)가 됐습니다. 근데 join
노드 `else_if_join_106`은 여전히 그 `revert_110`을 predecessor로 기다리고 있어서,
`Interpreter/Engine.py`의 worklist 알고리즘(825-834행)이 그 노드를 "아직 준비 안 됨"
으로 보고 영원히 뒤로 미룹니다. 이 `else if` 체인이 4단 중첩이라 join 노드도 4개가
중첩돼 있고(`else_if_join_106` ← `103` ← `100` ← `if_join_97`), 얘네가 서로를 "아직
work에 남은 게 있다"는 근거로 삼아 **상호 무한 재큐잉**에 빠집니다 — 크래시 없이
CPU만 계속 도는 진짜 livelock의 정체였습니다.

**§3-8에서 조사했던 ANTLR 캐시/문법 관련 내용은 전부 이 livelock과 무관한 헛다리였습니다.**
애초에 이 프로젝트 문서의 가장 처음 버전에 있었던 "`_run_worklist`의 CFG join-point
재큐잉" 가설이 사실 정확히 맞았고, 그 뒤 어느 시점에 faulthandler 스택을 잘못 읽었거나
(혹은 그때 코드 상태가 지금과 달랐거나) 해서 ANTLR 쪽으로 잘못 방향을 틀었던 것으로
보입니다.

**다음 조사 대상**: `Analyzer/DynamicCFGBuilder.py`가 "본문이 `revert(...)` 하나뿐인
else 블록"을 CFG로 만들 때 왜 revert 노드를 건너뛰고 바로 `ERROR`로 연결하는지 — 아직
안 고침. 이 특정 CFG 위상(4단 이상 중첩 `else if` 체인 + 마지막 `else`의 본문이
`revert` 하나뿐)이 이번 테스트 스위트에서 처음이라 지금까지 한 번도 안 걸렸던 것으로
보입니다.
