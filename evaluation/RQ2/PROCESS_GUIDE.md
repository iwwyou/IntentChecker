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
- **원본 .sol 파일**: `evaluation/RQ2/target_contracts/` (89개 파일)
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
- `not_detectable`: 한계로 인해 탐지 불가
  - `limitation_type`: missing-operation, multi-transaction, access-control, fixed-point 등

**진행 상황**: dataset.csv 기준 row 10 (web3bugs_35_H_12)까지 완료
- web3bugs_35_H_12: `detectable` (During + Assign != Current 방식으로 missing-operation 간접 탐지 가능)

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
      "comment": "설명"
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
