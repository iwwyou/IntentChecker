# RQ1 Scatter Plot Metric Improvement Prompt

나는 Solidity 스마트 컨트랙트 분석 도구(IntentChecker)의 논문을 쓰고 있어.
RQ1에서 20개 mitigated case의 분석 시간과 코드 복잡도 메트릭의 상관관계를
scatter plot (3+2 레이아웃, PDF)으로 보여주려 해.

---

## 프로젝트 구조

프로젝트 루트: `C:/Users/isjeon/PycharmProjects/pythonProject/SolidityGuardian/`

### 1) Case JSON (분석 입력)

위치: `evaluation/RQ1/cases/<category>/<name>.json`

각 JSON은 배열이고, 레코드 구조:
```json
{"code": "uint x = 10;", "startLine": 5, "endLine": 5, "event": "add"}
```
- `code`: Solidity 코드 한 줄 또는 annotation (`// @During`, `// @Post`, `// @StateVar` 등)
- `event`: `"add"` | `"modify"` | `"delete"`

타겟 함수 + internal call chain을 contraction한 것이라서,
이 JSON에는 타겟 함수와 그 함수가 내부적으로 호출하는 함수들의 코드만 들어있음.
Dependency(상속 컨트랙트, 라이브러리 등)는 사전 분석(pre-analysis)되어 캐시되므로
per-case 분석 시간에 영향을 주지 않음. 따라서 **모든 메트릭은 case JSON에서만 추출**한다.

20개 case 목록:
```
cases/div_in_path/WANGMI_input.json
cases/exchange_problem/Nokon_input.json
cases/greedy_contract/SwordCrowdsale_input.json
cases/operator_order_issue/BoostToken_input.json
cases/indivisible_amount/BoostToken_input.json
cases/profit_opportunity/HIT_input.json
cases/web3bugs_5_H_07/web3bugs_5_H_07.json
cases/web3bugs_5_H_08/web3bugs_5_H_08.json
cases/web3bugs_5_H_12/web3bugs_5_H_12.json
cases/web3bugs_45_H_01/web3bugs_45_H_01.json
cases/web3bugs_47_H_02/web3bugs_47_H_02.json
cases/web3bugs_51_H_02/web3bugs_51_H_02.json
cases/web3bugs_56_H_02/web3bugs_56_H_02.json
cases/web3bugs_58_H_02/web3bugs_58_H_02.json
cases/web3bugs_60_H_01/web3bugs_60_H_01.json
cases/web3bugs_62_H_08/web3bugs_62_H_08.json
cases/web3bugs_70_H_10/web3bugs_70_H_10.json
cases/web3bugs_77_H_01/web3bugs_77_H_01.json
cases/web3bugs_78_H_02/web3bugs_78_H_02.json
cases/web3bugs_101_H_01/web3bugs_101_H_01.json
```

### 2) 기존 메트릭 수집/플롯 코드

- `evaluation/validation_soundness/collect_metrics.py` (메트릭 수집)
- `evaluation/validation_soundness/plot_correlations.py` (scatter plot 생성)
- `evaluation/validation_soundness/rq1_metrics.csv` (현재 결과)
- 출력: `paper/figure/rq1_scatter.pdf`

---

## 현재 문제점

`collect_metrics.py`의 `extract_source_metrics()`가 case JSON을 파싱해서 메트릭을 추출하는데,
카운팅 방식에 문제가 있음.

구체적 문제:
1. **external_calls** 휴리스틱이 `CapName(expr).method()` 패턴만 잡음
   - `using SafeMath for uint256` 후 `x.add(y)` 같은 라이브러리 호출 누락
   - 대부분의 case에서 external_calls = 0으로 나옴
2. **functions**는 함수 "정의" 수를 세는데, 실제로는 call site 수가 더 의미 있음
3. **branch_count**가 `if`만 카운트하고 `else if`, `else`, `require`, `assert`를 무시
4. 기존 6개 메트릭 중 의미가 약한 것이 있어서 재구성이 필요

---

## 원하는 5개 메트릭 (개선안)

기존 6개(lines, functions, branch_count, debug_total, loop_count, external_calls)를 5개로 재구성.
**모든 메트릭은 case JSON에서만 추출** (dependency는 사전 분석되어 분석 시간에 미포함):

1. **Source lines**: case JSON 내 코드 라인 수 (annotation 제외, 기존 `lines`와 동일)
2. **Internal calls**: case JSON 내에서 같은 contraction 안의 함수를 호출하는 call site 수
   - 예: contraction 안에 정의된 `_calculateFee()`를 호출하는 부분
3. **External calls**: case JSON 내에서 dependency(라이브러리, 상속 컨트랙트, 인터페이스)를 호출하는 call site 수
   - 기존 휴리스틱 개선 필요: `CapName(addr).method()` 뿐 아니라
     `using` directive에 의한 라이브러리 호출 (`x.add(y)`, `x.mul(y)` 등)도 포함
   - `using X for Y` 선언이 JSON에 있으면 그 라이브러리의 메서드 호출을 external로 분류
4. **Control flow**: case JSON 내 아래 항목 합산
   - loop: `for`, `while`
   - branch: `if`, `else if`, `else`
   - guard: `require(...)`, `assert(...)`
5. **Debug annotations**: `@StateVar` + `@LocalVar` + `@GlobalVar` + `@IReturn` 수 (기존 `debug_total`과 동일)

---

## 요청사항

### (a) collect_metrics.py 수정

- internal/external call site 구분 로직 구현:
  - JSON에서 함수 정의(`function X`)를 먼저 수집하여 internal 함수 목록 생성
  - 코드 내 함수 호출에서 internal 목록에 있으면 internal call, 없으면 external call
  - `using X for Y` 선언 파싱하여 해당 라이브러리 메서드 호출도 external call로 카운트
- control flow 카운팅 개선: `for`, `while`, `if`, `else if`, `else`, `require(...)`, `assert(...)` 포함
- 5개 메트릭으로 CSV 컬럼 재구성
- 기존 분석 시간 데이터(`analysis_time_mean` 등)는 그대로 유지

### (b) plot_correlations.py 수정

- 2x3 -> 3+2 레이아웃 (상단 3개, 하단 2개 중앙 정렬)
- 메트릭 라벨: "Source lines", "Internal calls", "External calls", "Control flow", "Debug annotations"
- 출력: `paper/figure/rq1_scatter.pdf` (기존 파일 덮어쓰기)

### (c) 검증

- 기존 `rq1_metrics.csv`와 새 결과를 비교해서 어떤 case에서 차이가 큰지 보고
- 특히 external_calls가 기존에 0이었던 case에서 새로운 값이 합리적인지 확인
- **수동 전수 검증**: 20개 case JSON을 전부 직접 읽어서, 스크립트가 뽑은 메트릭 값(source lines, internal calls, external calls, control flow, debug annotations)과 일치하는지 하나씩 확인
- 불일치가 있으면 원인을 분석하고 스크립트를 수정해줘

---

## 참고

- Python 환경: `.venv/Scripts/python.exe` 사용 (networkx 3.4.2 필요)
- 분석 시간 데이터: `rq1_metrics.csv`의 `analysis_time_mean` 컬럼을 그대로 사용 (재실행 불필요)
