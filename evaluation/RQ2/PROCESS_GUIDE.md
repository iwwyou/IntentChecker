# RQ2 실험 수행 프로세스 가이드

## 프로젝트 개요
- **프로젝트**: SolidityGuardian (IntentChecker)
- **목적**: Solidity 스마트 컨트랙트의 numeric logic vulnerability를 개발자 의도(intent annotation) 기반으로 탐지/완화하는 정적 분석 도구
- **분석 방법**: Abstract interpretation (interval domain) + developer-provided debug/intent annotations
- **논문**: `paper/main.tex`

## 핵심 지시사항
- **오류가 나면 바로 수정하지 말고 사용자에게 먼저 보고할 것**
- **모르는 것이 있으면 사용자에게 물어볼 것**
- **코드 수정 전 반드시 사용자에게 수정 방향을 설명하고 승인받을 것** (직접 판단하여 수정 금지)
- **방어 코드(try-except 무시, None 체크 후 pass 등) 금지** — 근본 원인을 파악하고 일반화된 방향으로 해결할 것
- **항상 위 사항들을 지킬 것**

## 데이터셋 구성
- **총 89건**: Web3Bugs 81건 + Numscout 8건
- **마스터 인덱스**: `evaluation/RQ2/dataset.csv`
- **원본 .sol 파일**: `evaluation/RQ2/target_contracts_original/` (89개 파일)
- **축약 .sol 파일**: `evaluation/RQ2/target_contracts_contraction/` (detectable 건)
- **의존성 파일**: `evaluation/RQ2/target_contracts/dependencies/` (302개 파일)
- **dependency 정보 스크립트**: `evaluation/RQ2/collect_dependencies.py`

## RQ 구조
- **RQ1**: Validation Algorithm Soundness (interval comparison 알고리즘 검증)
- **RQ2**: Mitigation (IntentChecker로 실제 취약점 완화 가능 여부)
- **RQ3**: Comparison with Existing Tools (GPTScan/NumScout과 비교)
  - Table A: NumScout vs IntentChecker on Numscout 8건
  - Table B: GPTScan vs IntentChecker on Web3Bugs 81건
- **RQ4**: Developer Perception (개발자 인식 조사)

## 수행 Phase

### Phase 1: Feasibility Review (89건 전수 검토)
각 contract를 검토하여 IntentChecker로 탐지/완화 가능한지 판정.

**판정 기준:**
- `detectable`: IntentChecker의 annotation으로 탐지 가능
- `not_detectable`: 한계로 인해 탐지 불가 (limitation type은 `limitation_types.md` 참조)
- `excluded`: numeric logical error 정의에 해당하지 않거나 분석 대상 제외

**Three-file update rule**: 케이스 분석 시 아래 세 파일을 **항상 함께** 업데이트:
1. `dataset.csv` — status 변경
2. `annotation_plans.md` — 분석 내용/annotation 계획 기록
3. `limitation_types.md` — not_detectable인 경우 limitation type 및 해당 케이스 목록 갱신

**케이스별 수행 절차:**
1. 원본 contract 읽기 (`target_contracts_original/`)
2. 버그 이해 (bug description, bug report)
3. Blocker 분석:
   - **Loop 분석**: 누적 연산(`+=`, `*=`) → widening → Top. 단, min-finding 등 monotonically non-increasing 루프는 widening 대상 아님. 또한 widening 되더라도 annotation 대상 변수가 widened 변수와 독립적이면 blocker 아님
   - **External call 분석**: interface call → Top (L2a), 외부 contract call → state unknown → Top (L2b). 단, interface에서 상속받은 struct/enum **타입 정의**는 compile-time 정보이므로 L2 아님 (target contract 자체 storage에 있는 데이터는 annotatable)
   - **Annotation 표현 한계**: storage variable 없음 (L3b), 올바른 값을 기존 변수의 산술 조합으로 표현 불가 (L3a)
   - **Bug awareness 전제**: 누락된 함수 호출의 효과가 scope 밖 (L4a), 인자 순서 오류 (L4b), 누락된 state update (L4c)
4. detectable/not_detectable 판정
5. Three-file update (dataset.csv + annotation_plans.md + limitation_types.md)
6. detectable인 경우: annotation 계획 수립 (아래 상세)

**detectable 케이스 annotation 계획 수립:**
1. Contraction 파일 확인 (`target_contracts_contraction/`)
2. Intent annotation 결정: 타입(@Post/@During), 대상 변수, 표현식, 삽입 라인
3. Debug annotation 결정: 필요한 변수, 삽입 라인
4. **Z3 solver 생성** (`evaluation/RQ2/z3_solvers/`): underflow/overflow 방지, require 통과, 버그 경로 진입 조건 등을 Z3 constraint로 모델링하여 안전한 debug annotation 값 도출
5. **Annotation 삽입 순서**: Step 1에서 intent annotation 삽입 → Step 2에서 debug annotation 삽입 → interpreter가 둘 다 포함된 상태로 실행

### Phase 2: 환경 준비
- contract별 import dependency 사전 수집 (collect_dependencies.py 완료)
- `hardhat/console.sol` import 제거 (17개 파일)
- OpenZeppelin dependency 파일 추가
- direct library call 지원 구현 (필요 시)

### Phase 3: Contraction (detectable 건만)
각 contract에서 vulnerability 관련 함수 중심으로 축약.

**산출물:**
- `_contraction.sol`: 축약된 Solidity 소스
- `_contraction.json`: `soltotestjson.py`로 변환한 JSON (IntentChecker 입력 형식)

**변환 명령:**
```bash
python soltotestjson.py [_contraction.sol 경로] -o [_contraction.json 경로]
```

### Phase 4: Annotation 명세 (Case JSON 생성)
각 contracted contract에 대해 case JSON 파일 생성.

**Case JSON 구조** (예: `evaluation/RQ2/cases/div_in_path/WANGMI.json`):
```json
{
  "id": "WANGMI",
  "name": "WANGMI div_in_path",
  "description": "버그 설명",
  "source": "Dataset/Numscout/contraction/div_in_path/WANGMI_contraction.json",
  "target_contract": "WANGMI",
  "target_function": "_transfer",
  "bug_lines": [428],
  "web3bugs_report": "35.md",
  "annotation_rationale": "35.md H-12: secondsPerLiquidity가 liquidity 변경 시 업데이트 안됨. mint에서 Ticks.insert() 전 업데이트 누락 → Assign != Current로 검증",
  "debug_annotations": [
    {
      "type": "StateVar|LocalVar|GlobalVar",
      "var": "변수명",
      "value": "값 또는 [min, max] interval 또는 symbolicAddress N 또는 true/false",
      "line": 라인번호,
      "comment": "설명"
    }
  ],
  "intent_annotations": [
    {
      "type": "During|Post",
      "line": 라인번호,
      "expr": "intent 표현식",
      "expected": "violated|satisfied",
      "rationale": "35.md H-12: 어떤 bug report 내용을 근거로 이 annotation을 선택했는지"
    }
  ],
  "expected_results": {
    "total_intents": N,
    "expected_violations": N,
    "expected_satisfied": N
  }
}
```

**Debug Annotation 생성 규칙:**
1. 대상 함수의 **모든 관련 변수**에 debug annotation 필요 (함수 파라미터, state variables, global variables)
2. `require` 문을 분석하여 **조건을 통과하는 값** 생성:
   - `require(x != address(0))` → `symbolicAddress N`
   - `require(isLaunched)` → `true`
   - `require(!isBlacklisted[x])` → `false`
   - `require(amount <= maxLimit)` → amount보다 큰 interval
   - `require(a + b <= c)` → 관계를 만족하는 값 조합
3. 버그가 trigger되는 경로로 실행이 흐르도록 값 설정
4. mapping 접근 시 key에 파라미터 이름 매칭 (e.g., `isExcludedFromFees[_from]`)

**Intent Annotation 문법** (Solidity.g4 기준):
```
// During:
//   @During var(Before relOp After)              -- DuringBeforeAfter
//   @During var(Assign relOp Current)            -- DuringAssignCurrent
//   @During func.arg[N] relOp value              -- DuringFunctionArg
//   @During var relOp value                      -- CommonClause

// Post:
//   @Post var(Entry relOp Exit)                  -- PostEntryExit
//   @Post Unchanged(var)                         -- UnchangedVar
//   @Post var relOp value                        -- CommonClause

// relOp: >, <, >=, <=, ==, !=
// logicOp: && (여러 clause 연결 가능)
```

**Intent Annotation 사용자 제공 정보:**
- 사용자가 제공: 어떤 변수에 어떤 의도의 annotation을 줄지, 어느 라인에 줄지
- Claude가 생성: 해당 함수의 require 통과용 debug annotation 값 전체

**Annotation 근거 추적 (Provenance):**
- Web3Bugs 원본 bug report: `Web3Bugs/reports/{contest번호}.md` (e.g., `35.md`)
  - 경로: 사용자 로컬 `C:\Users\isjeon\Web3Bugs\reports\`
  - contest 번호는 contract_id에서 추출 (e.g., `web3bugs_35_H_12` → `35.md`)
- Case JSON에 기록할 필드:
  - `web3bugs_report`: `"35.md"` (report 파일 번호)
  - `annotation_rationale`: 전체 annotation 선택 이유 (어떤 bug report를 보고 왜 이 annotation을 선택했는지)
  - 각 intent의 `rationale`: `"35.md H-12: ..."` 형태로 리포트 항목 번호 + 근거 요약
- 목적: Threats to Validity에서 "bug report 기반으로 annotation 작성" 주장의 증거

### Phase 5: 일괄 실행 + 결과 정리 (마지막에 한번에)
- `runner.py`로 IntentChecker 실행
- TP/FP/FN 수집
- `paper/main.tex` RQ2, RQ3 표 채우기
- Threats to Validity, Discussion 작성

**실행 명령:**
```bash
cd evaluation/RQ2
python runner.py                          # 전체 실행
python runner.py --category div_in_path   # 카테고리별
python runner.py --case WANGMI            # 개별 케이스
```

## 핵심 파일 경로
| 파일 | 경로 | 설명 |
|------|------|------|
| 논문 | `paper/main.tex` | 메인 논문 파일 |
| 데이터셋 CSV | `evaluation/RQ2/dataset.csv` | 89건 마스터 인덱스 |
| 타겟 계약 | `evaluation/RQ2/target_contracts/*.sol` | 원본 .sol 파일 |
| 의존성 | `evaluation/RQ2/target_contracts/dependencies/` | import 의존성 파일 |
| 케이스 JSON | `evaluation/RQ2/cases/{category}/{name}.json` | 실행 케이스 |
| 결과 | `evaluation/RQ2/results/` | 실행 결과 JSON/CSV |
| Runner | `evaluation/RQ2/runner.py` | RQ2 실행 스크립트 |
| Sol→JSON 변환 | `soltotestjson.py` | .sol → JSON 변환기 |
| Dependency 수집 | `evaluation/RQ2/collect_dependencies.py` | import 정보 수집 |
| Grammar | `Parser/Solidity.g4` | Intent annotation 문법 정의 |
| Annotation 계획 | `evaluation/RQ2/annotation_plans.md` | 케이스별 annotation 계획/분석 기록 |
| Limitation 유형 | `evaluation/RQ2/limitation_types.md` | not_detectable 한계 유형 정의/분류 |
| 추가 구현 사항 | `evaluation/RQ2/code_modification_issues.md` | IntentChecker 코드 수정 필요 사항 추적 |
| Z3 솔버 | `evaluation/RQ2/z3_solvers/` | debug annotation 값 생성용 Z3 constraint solver |
| 원본 계약 | `evaluation/RQ2/target_contracts_original/` | 원본 .sol 파일 |
| 축약 계약 | `evaluation/RQ2/target_contracts_contraction/` | 축약된 .sol 파일 (detectable 건) |

## Numscout 기존 contraction 예시
| 파일 | 경로 |
|------|------|
| WANGMI sol | `Dataset/Numscout/contraction/div_in_path/WANGMI_contraction.sol` |
| WANGMI json | `Dataset/Numscout/contraction/div_in_path/WANGMI_contraction.json` |
| WANGMI case | `evaluation/RQ2/cases/div_in_path/WANGMI.json` |
| BoostToken case | `evaluation/RQ2/cases/operator_order_issue/BoostToken.json` |
| Nokon case | `evaluation/RQ2/cases/exchange_problem/Nokon.json` |
| SwordCrowdsale case | `evaluation/RQ2/cases/greedy_contract/SwordCrowdsale.json` |

## Threats to Validity에 포함할 내용
1. **연구자 작성 annotation ≠ 개발자 의도**: 실험에서 사용된 intent annotation은 연구자가 bug report와 원본 코드를 기반으로 작성한 것이며, 실제 개발자의 의도와 다를 수 있다.
2. **완화 방안**: bug report, fix commit, 원본 소스코드를 참고하여 annotation 작성.

## Discussion에 포함할 내용
1. **Annotation 작성의 순환 논리**: annotation 작성에 버그 인지가 전제되는 한계 → LLM 기반 annotation suggestion 필요성 (future work: IntentKeeper)
2. **Missing-operation 간접 탐지**: debug annotation 초기값 + `Assign != Current` 패턴으로 값 변경 여부를 간접 탐지 가능하지만, 업데이트 결과가 초기값과 동일한 edge case에서 false positive 발생 가능.

---

## 아키텍처 리팩토링 (2026-03-25)

### SolidityAnalyzer / ContractAnalyzer 분리
- **SolidityAnalyzer** (`Analyzer/SolidityAnalyzer.py`): 소스 관리 + context 분배 + file-level 처리
  - `full_code_lines`, `full_code`, `line_info` 소유
  - `update_code()` 진입점
  - `_insert_lines()`, `_shift_source_meta()`, `update_brace_count()` 등 소스 관리
  - `analyze_context()` dispatcher: file-level → 자체 처리, assembly → context 설정, 나머지 → CA 위임
- **ContractAnalyzer** (`Analyzer/ContractAnalyzer.py`): contract-level 분석 전용
  - `self.sa.xxx`로 소스 데이터 접근 (property 없이 직접 참조)
  - `_shift_cfg_meta()`: recorder.ledger + CFGNode/Statement src_line shift
  - `analyze_context()`: contract scope 전용
  - 모든 `process_*`, CFG building, `make_*_cfg`
- Entry point: `main.py → SolidityAnalyzer.update_code() → ContractAnalyzer (위임)`

### Yul 파서 분리
- **Yul.g4** (`Parser/Yul.g4`): 별도 lexer/parser (Solidity lexer 토큰 충돌 방지)
- **EnhancedYulVisitor** (`Analyzer/EnhancedYulVisitor.py`): Yul parse tree → Expression IR
- **Solidity.g4**: Yul rule 전부 삭제, `assemblyBlock: '{' (~('{' | '}') | assemblyBlock)* '}'` 로 simplified
- 흐름: `visitAssemblyStatement` → 내부 텍스트 추출 → YulParser → EnhancedYulVisitor → ContractAnalyzer

### Function Overloading
- `CFG.py`: `functions = {name: {signature: FunctionCFG}}` (nested dict)
- `add_function_cfg()`, `update_function_cfg()`, `get_function_cfg(name, param_types)`
- `iter_all_functions()`, `_build_signature()`
- `FunctionCFG.parameter_types: list[str]` 필드 추가

---

## Grammar 변경사항 (2026-03-25)

### Solidity.g4
| 변경 | 내용 |
|------|------|
| assemblyStatement | Yul rule 전부 제거, balanced brace 소비로 simplified |
| Yul lexer rules | `YulEvmBuiltin`, `YulIdentifier` 등 삭제 (balance 토큰 충돌 해결) |
| debugGlobalVar | `GlobalVarSimple` / `GlobalVarAddressBalance` 분리 |
| DuringFeasible | `'require feasible' \| 'assert feasible'` |
| VarChangedEval | `'changed' '(' intentValue ',' ('true'\|'false') ')'` in commonClause |
| _CTX_MAP | `fileLevelStruct`, `fileLevelStructMember`, `fileLevelTypeAlias` 매핑 추가 |

### Yul.g4 (신규)
- 별도 lexer/parser, `antlr4 -Dlanguage=Python3 -visitor Yul.g4`

---

## 구현 완료된 Code Modification Issues (2026-03-25)

### Issue 1: During standalone
- `_is_during_inline()`, `_find_prev_cfg_node()`, Engine `report_line`

### Issue 3: File-level struct
- `_handle_file_level()`, visitor 라우팅, `sa.file_level_structs` fallback

### Issue 5: User-defined value type
- `process_type_alias()`, `visitUserDefinedValueTypeDefinition()`, `resolve_type()`
- `wrap/unwrap`: `TypeWrapUnwrapContext` → `evaluate_type_wrap_unwrap()`

### Issue 6: require feasible
- `verify_during_feasible()`: CFG에서 require condition → BoolInterval `[0,0]` 이면 violated

### Issue 2: Changed(x, true/false)
- `verify_during_changed()`, `verify_post_changed()`: Entry vs Current/Exit 비교
- 기존 `Unchanged` 제거

### Issue 7: address(this).balance GlobalVar
- `visitGlobalVarAddressBalance()`, `_get_address_this_balance()`
- `this.balance` / `address(X).balance` 접근 시 GlobalVar 값 우선

### Solidity Built-in 함수
- `_evaluate_builtin_function()`: `addmod`, `mulmod` 계산, 나머지 TOP

### Yul/Assembly
- `EnhancedYulVisitor`: binary ops, mulmod/addmod, not, iszero → Expression IR
- `process_yul_assignment()`, `process_yul_variable_declaration()` (미지원→TOP)

### using 키워드 (Issue 4)
- pkl 로드 경로: `Dependencies/objectfile/lib_*.pkl`
- 같은 타입에 여러 library: `using_libraries[type] = list[LibraryCFG]`

---

## Dependencies 사전분석 파이프라인 (2026-03-25)

### 디렉토리 구조
```
Dependencies/
├── interfaces/     ← 44개 interface .sol
├── libraries/      ← 17개 library .sol
├── contracts/      ← 공통 + 타겟별 서브폴더 (45/, 47/, 58/, 101/, 112/)
├── objectfile/     ← 79개 pkl (ifc_*, lib_*, con_*)
├── main.py         ← 사전분석 스크립트
└── ISSUES.md       ← 미해결 이슈 (FloatStruct 등)
```

### 실행
```bash
python Dependencies/main.py --type all    # 전체 분석
python Dependencies/main.py --file X.sol  # 단일 파일
```

### Dependency .sol 작성 규칙

**함수 순서 — callee가 caller보다 앞에 위치해야 함**
- IntentChecker는 소스를 순차적으로 파싱하므로, 호출되는 함수(callee)가 호출하는 함수(caller)보다 뒤에 정의되면 CFG가 제대로 구축되지 않음
- 예: `_transfer`가 `transferFrom`보다 **앞에** 정의되어야 함
- Dependency .sol을 작성/수정할 때 반드시 호출 관계를 확인하고 순서 정렬

**pkl 재생성 순서 — 상속 체인의 부모부터 생성**
- 자식 contract의 pkl 생성 시 부모 pkl이 이미 존재해야 `parent_cfgs`, `using_libraries` 상속이 정상 동작
- 재생성 순서 예시 (47번):
  1. `SafeMathUpgradeable` (library, 독립)
  2. `AddressUpgradeable` (library, 독립)
  3. `Initializable` (base contract)
  4. `ContextUpgradeable` (← Initializable)
  5. `ERC20Upgradeable` (← Initializable, ContextUpgradeable)
- `Dependencies/main.py --type all`은 알파벳순이라 상속 순서와 다를 수 있으므로, 개별 재생성 시 직접 순서를 지정할 것

### Phase 0
- type alias 사전 수집 (`type X is Y;` regex)
- interface 이름 사전 수집 (`interface X` regex)
- 각 파일 분석 시 `sa.type_aliases` / `ca.interface_names`에 주입

### 전처리 스크립트
- **preprocess_contraction.py**: import/주석/event 제거, `from→_from`, enum 한줄화
- **rename_reserved_identifiers.py**: `float→FloatStruct`, `from→_from`
- **slice_solidity**: assembly 내부 `in_assembly` depth 추적 → 줄 단위 chunk

---

## Dataset 변경 (2026-03-25)

| 케이스 | 변경 전 | 변경 후 | 이유 |
|--------|---------|---------|------|
| numscout_HippoHotel | not_detectable (L3) | **annotated** | address(this).balance + SafeMath 해결 |
| numscout_EthereumGod | not_detectable (L3) | not_detectable (**L2a**) | state-modifying interface call |

### Limitation 분류 개편
- L1 → L1a (8건, 기존 L1b 흡수), L1c → L1b (2건)
- 상위 그룹: A. Analysis Imprecision / B. Annotation Limitation

### 현재 통계
- annotated: **23건**, not_detectable: **53건**, excluded: **13건**

---

## 분석 준비 상태 (2026-03-25)

### 준비 완료: 22/23 annotated 케이스
dependency pkl 전부 준비, using/assembly/overloading 지원 완료.

### 미준비: 1건
- **web3bugs_42_H_01**: FloatStruct file-level struct 미등록 (Dependencies/ISSUES.md 참조)

### 추가 구현 필요
- **Issue 8** (78_H_02): 피상속 컨트랙트의 private state variable 접근

---

## Input JSON 형식 규칙 (2026-03-27)

### JSON 생성 절차
1. **전처리**: `preprocess_contraction.py` 실행 (import/주석/constructor 제거, single-line if 확장 등)
2. **Code records 생성**: `soltotestjson.py`로 clean contraction .sol에서 변환
3. **Annotation 추가**: code records 뒤에 intent → debug annotation 순서로 추가

### JSON 레코드 순서 (반드시 준수)
```
1. Code records        (soltotestjson.py 출력 그대로)
2. Intent annotations  (// @During ..., // @Post ...)
3. // @Debugging BEGIN
4. Debug annotations   (// @LocalVar, @StateVar, @GlobalVar, @IReturn)
5. // @Debugging END
```

### @Debugging BEGIN/END 필수
- Debug annotation은 반드시 `// @Debugging BEGIN` ~ `// @Debugging END`로 감싸야 함
- BEGIN/END 없이 개별 flush하면 **동일 intent를 debug annotation 개수만큼 반복 체크**하게 됨
- BEGIN/END의 startLine은 debug annotation 중 첫 번째의 startLine과 동일하게 설정

### Debug annotation startLine 규칙
- **각 debug annotation의 startLine은 서로 고유해야 함** (batch_mgr가 startLine을 dict key로 사용)
- 함수 body 내 코드 라인 번호를 순차적으로 할당 (예: 197, 198, 199, ...)
- Intent annotation의 startLine은 해당 코드 라인과 동일해도 됨 (debug와 별도 처리)

### Contraction .sol에 annotation을 넣지 말 것
- `target_contracts_contraction/` .sol은 순수 코드만 포함
- annotation은 JSON에서만 추가
- .sol에 annotation이 섞이면 soltotestjson.py가 라인 갭을 만들어 CFG 빌드 실패

---

## 엔진 수정 사항 (2026-03-27)

### _merge_values None 방어
- `VariableEnv._merge_values(v1, v2, mode)`: v1 또는 v2가 None이면 다른 쪽 반환
- 한쪽 branch에서 초기화 안 된 변수가 join 시 에러 방지

### Interface 타입 state variable 지원
- `process_state_variable`: typeCategory=="interface"이면 AddressSet.top() + `_cast_interface` 설정
- `process_variable_declaration`: 동일 처리 (local 변수)
- `evaluate_identifier_context`: MemberAccessContext에서 interface 타입 변수는 `.value`(AddressSet) 반환
- 이를 통해 `interestRateModel.getBorrowRate()` 같은 interface member call이 정상 동작

---

## 엔진 수정 사항 (2026-03-30 세션 3)

### Mapping key 통일 — AddressSet 값 기반
- global var(msg.sender)가 mapping index일 때 `"msg.sender"` 리터럴 대신 `str(AddressSet({101}))` 사용
- **5곳 수정**: Evaluation.py, Update.py, DebugInitializer.py
- annotation `accountBorrows[msg.sender]`와 callee `accountBorrows[account]` 모두 동일 key 수렴
- 45_H_01 해결

### `top_from_soltype` 범용 유틸리티
- `VariableEnv.top_from_soltype(sol_t, struct_defs, enum_defs, identifier)` → top-valued domain object
- struct, enum, array, mapping, interface, elementary 전부 지원
- interface function return 시 모든 return type에 대해 proper domain value 반환

### Interface struct return + parent chain 검색
- InterfaceFunctionCallContext에서 `top_from_soltype`으로 StructVariable 반환
- `_lookup_interface_return`: parent interface chain BFS 검색 (IVaultGovernance → ILpIssuerGovernance 등)
- `resolve_library_struct`: interface/contract pkl에서도 struct/enum 조회

### Interface 타입 전반 지원 강화
- `top_from_soltype`, `initialize_struct._make_var`, `MappingVariable._make_value`, `Engine._interpret_var_decl`: interface typeCategory → AddressSet.top() + `_cast_interface`
- `AddressSet.join/meet/narrow`: `_cast_interface` 보존 (`getattr` safe access)
- `_make_bottom`: AddressSet bottom 시 `_cast_interface` 타입 정보 보존
- `evaluate_identifier_context`: composite 타입(Struct/Array/Mapping) 객체 직접 반환

### @IReturn Grammar 일반화
- `debugIReturn` rule: 기존 4개 → PatternA/B 2개 + `ireturnAccessChain`
- access chain: `("member", name)`, `("index", int)`, `("call", name)` 3종
- Registry key: `(contract_var, func_name, access_chain_tuple)` 형식
- `_assemble_ireturn_value`: access chain 따라 struct member 설정

### Library constant 조회
- `evaluate_member_access_context`: library의 `state_variable_node.variables`에서 상수 조회

### Dependency 사전분석 확장
- `_load_parent_pkls`: 모든 모드(contract, interface, library)에서 호출
- regex: `contract|interface|library` 모두 매칭
- interface 결과 추출: `_pre_existing_all` 기반

### Refine non-l-value skip
- function call, binary/unary op, literal, tuple, type conversion 등 non-l-value expression narrowing 방지

### SolidityAnalyzer._insert_lines shift 수정
- `skip_shift_at_start=True` 시 `actual_offset = offset - 1`
- for loop 이후 코드가 loop 내부로 잘못 포함되던 CFG 구축 문제 해결

---

## 엔진 수정 사항 (2026-03-30 세션 4)

### Contract 타입 인식 (visitUserDefinedType)
- `contract_cfgs`에 등록된 contract 타입 (부모 컨트랙트 등)을 interface와 동일하게 address로 처리
- `library_cfgs`에 있는 타입은 제외 (library는 변수 타입으로 사용 불가)
- 47_H_02 해결 (ERC20Upgradeable), 51_H_02 해결 (LPToken)

### 부모 contract의 using 선언 상속
- `make_contract_cfg` / `make_abstract_contract_cfg`에서 `_inherit_using_libraries(cfg)` 호출
- 부모 pkl의 `using_libraries` / `using_all_libraries`를 자식 cfg에 복사
- Solidity semantics: `using X for Y;`는 derived contract에도 적용

### process_using_directive — library_cfgs 우선 조회
- 기존: pkl 파일 경로로만 검색 (`lib_{name}.pkl`) → `lib_47_SafeMathUpgradeable.pkl` 같은 prefix 있는 경우 못 찾음
- 수정: `self.library_cfgs`를 먼저 확인, pkl은 fallback
- 이미 로드된 library를 재활용하므로 일관성 + 일반성 확보

### Library globals (block.timestamp 등)
- `LibraryCFG`에 `globals` 필드 추가 (`CFG.py`)
- `make_library_cfg`에서 `StaticCFGFactory._create_global_variables()` 호출
- library 함수도 `block.timestamp`, `msg.sender` 등 사용 가능 (Solidity semantics)
- 51_H_02 해결 (SwapUtils library에서 block.timestamp 접근)

### require/assert 분기에서 During intent 검증
- Engine.py require/assert 분기 (`condition_node_type in ["require", "assert"]`)에서 `_process_node_intents` 호출 추가
- 기존: require 노드에 statements가 없어 intent 검증이 스킵됨
- 수정: `continue` 직전에 `_process_node_intents(node, cur_vars, src_line)` 호출
- `@During require feasible` annotation 정상 동작
- 51_H_02 해결 (require 조건이 항상 false → VIOLATED)

### 51번 Dependency 신규 생성
- `Dependencies/contracts/51/`: Context, ERC20 (OZ 0.6 표준), ERC20Burnable, Ownable, LPToken
- `Dependencies/interfaces/ISwap.sol`
- pkl 생성 순서: ISwap → Context → ERC20 → ERC20Burnable → Ownable → LPToken

### struct 생성자 검색 일반화 (_find_struct_def)
- `evaluate_function_call_context`에서 struct 생성자 검색 시 현재 contract + parent chain + using libraries + library_cfgs 전체 검색
- library에서 찾은 경우 qualified name 반환 (e.g., `FixedPointMath.FixedDecimal`) → using key와 매칭
- positional argument 지원: `FixedDecimal(x)` 같은 positional 인자도 struct 멤버에 매핑
- 56_H_02 해결 (FixedPointMath.FixedDecimal struct 생성자 인식)

### FixedPointMath inline assignment 분리
- `require((x = self.x * value) / value == self.x)` → `uint256 x = self.x * value; require(x / value == self.x);`
- IntentChecker가 조건식 내 inline assignment를 지원하지 않으므로 semantics 동일한 형태로 분리
- `fromU256`, `add`, `sub`, `mul` 4개 함수 모두 적용

### divide에서 0 제외 (Interval.py)
- 기존: 분모에 0 포함 시 무조건 BOTTOM
- 수정: Solidity에서 div-by-zero는 revert → 0을 제외하고 나눗셈 수행
- `UnsignedIntegerInterval`: `[0, MAX]` → `[1, MAX]`으로 0 제외
- `IntegerInterval`: `[-5, 5]` → `[-5, -1]` ∪ `[1, 5]` 두 구간으로 분리, 결과 보수적 합산
- 분모가 정확히 `[0, 0]`일 때만 BOTTOM (항상 revert)

### OR(||) short-circuit BOTTOM 전파 수정
- 기존: `||`에서 한쪽 피연산자가 BOTTOM이면 결과도 BOTTOM
- 수정: `||`에서 한쪽이 true 가능하면 다른 쪽 BOTTOM이어도 결과는 `[0,1]` (Solidity short-circuit semantics)
- `&&`는 기존대로 한쪽 BOTTOM이면 BOTTOM 유지

---

## 케이스별 실행 결과 (2026-03-30 세션 4)

| # | Case | Status | 비고 |
|---|------|--------|------|
| 1 | WANGMI | ✅ VIOLATED (V=1) | |
| 2 | Nokon | ⚠️ WARNING (W=1) | |
| 3 | SwordCrowdsale | ✅ VIOLATED (V=2) | |
| 4 | BoostToken_operator | ✅ VIOLATED (V=2) | |
| 5 | BoostToken_indivisible | ✅ VIOLATED (V=4) | |
| 6 | HIT | ❌ ERROR | ImplicationContext.commonClause |
| 7 | 5_H_07 | ✅ VIOLATED (V=1) | |
| 8 | 5_H_08 | ✅ VIOLATED (V=1) | |
| 9 | 5_H_12 | ✅ VIOLATED (V=1) | |
| 10 | 77_H_01 | ✅ VIOLATED (V=1) | |
| 11 | 101_H_01 | ⚠️ WARNING (W=1) | Issue F(ERC1155) 필요 |
| 12 | 45_H_01 | ✅ VIOLATED (V=2) | 세션3 해결 |
| 13 | 47_H_02 | ✅ VIOLATED (V=1) | 세션4 해결 — contract 타입 인식 + using 상속 |
| 14 | 51_H_02 | ✅ VIOLATED (V=1) | 세션4 해결 — LPToken dep + library globals + require intent |
| 15 | 56_H_02 | ⚠️ WARNING (W=1) | 세션4 해결 — struct chaining + divide fix, annotation 검토 필요 |
| 16 | 58_H_02 | ⚠️ WARNING (W=1) | 세션3 해결, annotation 검토 필요 |
| 17 | 60_H_01 | ⚠️ WARNING (W=1) | 세션4 부분 해결 — file-level struct + type alias + aliasName, qualified lib static call 체이닝 미해결 |
| 18 | 62_H_08 | ❌ ERROR | Modifier 'governed' |
| 19 | 70_H_10 | ❌ ERROR | qualified lib static call (UniswapV2OracleLibrary) |

**13 VIOLATED + 5 WARNING + 1 ERROR = 19건** (42_H_01, 78_H_02 미생성)

### 62_H_08 수정 사항 (세션4)
- contraction sol에서 modifier를 함수 앞으로 이동 + soltotestjson 재생성
- annotation `[101]` → `[msg.sender]`
- Refine 비트 길이 통일: literal(256bit default) vs 변수(실제 비트) — promotion 후 refine, 원래 비트 복원
- `visitUserDefinedType`: struct/enum 검색 시 parent chain 순회 추가
- `StaticCFGFactory.make_param_variable`: struct 파라미터 parent chain 검색 추가

### 60_H_01, 70_H_10 공통 미해결 사항
- **Qualified library static call**: `Fixed18Lib._from(x)`, `UniswapV2OracleLibrary.currentCumulativePrice(pair)` 등 library 이름을 identifier로 평가할 때 resolve 안 됨
- **Qualified static call 체이닝**: `Fixed18Lib._from(x).add(y)` — static call 반환값에 library 함수 체이닝
- **Cross-library call**: `Fixed18Lib.abs()` → `UFixed18Lib._from()` 호출
- 해결 시 60_H_01, 70_H_10 모두 re-test 필요
