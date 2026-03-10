# RQ2 실험 수행 프로세스 가이드

## 프로젝트 개요
- **프로젝트**: SolidityGuardian (IntentChecker)
- **목적**: Solidity 스마트 컨트랙트의 numeric logic vulnerability를 개발자 의도(intent annotation) 기반으로 탐지/완화하는 정적 분석 도구
- **분석 방법**: Abstract interpretation (interval domain) + developer-provided debug/intent annotations
- **논문**: `paper/main.tex`

## 핵심 지시사항
- **오류가 나면 바로 수정하지 말고 사용자에게 먼저 보고할 것**
- **모르는 것이 있으면 사용자에게 물어볼 것**
- **항상 위 두 가지를 지킬 것**

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
   - **External call 분석**: interface call → Top (L5a), 외부 contract call → state unknown → Top (L5b). 단, interface에서 상속받은 struct/enum **타입 정의**는 compile-time 정보이므로 L5 아님 (target contract 자체 storage에 있는 데이터는 annotatable)
   - **대상 변수 존재 여부**: storage variable 없음 (L4a), 누락된 함수 호출의 효과가 scope 밖 (L4b)
   - **값 표현 가능성**: 올바른 값을 기존 변수의 산술 조합으로 표현 불가 (L6)
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
