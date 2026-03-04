# IntentChecker 코드 수정 이슈 (나중에 일괄 수정)

## Issue 1: During standalone 라인 지원
- **현재**: During annotation은 반드시 코드 옆에 붙어야 함 (코드가 처리될 때 같이 평가)
- **필요**: DuringChanged, DuringAssignCurrent, CommonClause 등은 특정 코드와 무관 → 코드 없이 annotation만 있는 standalone 라인 지원 필요
- **예시**: web3bugs_35_H_12.sol mint() 함수
  - line 229: `// @During Changed(secondsPerLiquidity)` (standalone annotation line)
  - line 230-242: `nearestTick = Ticks.insert(...)` (기존 코드가 한 줄 밀림)
- **영향 범위**: Interpreter에서 During annotation 파싱/평가 로직, soltotestjson.py에서 annotation-only 라인 처리

## Issue 2: Changed/Unchanged annotation 신규 구현
- **배경**: `Assign != Current`는 값 기반 비교 → 중간에 바뀌었다가 원래값 복귀 시 감지 불가 (false negative)
- **신규**: `Changed(var)` / `Unchanged(var)` — 이벤트 기반, write operation 발생 여부만 추적
- **Validation logic**:
  - `@Post Changed(var)`: Entry → Exit, CFG 전 경로에서 var에 write가 있었는지
  - `@During Changed(var)`: Entry → 해당 라인, CFG 전 경로에서 var에 write가 있었는지
  - `@Post Unchanged(var)`: 기존 구현이 Entry/Exit 값 비교라면 → 이벤트 기반으로 변경 필요
- **기존 `@Post Unchanged(var)` 수정**: 값 비교 → write event 추적으로 변경
- **예시**: `// @During Changed(secondsPerLiquidity)` expected "violated" → write 없음 → missing-operation 탐지
- **영향 범위**: Parser/Solidity.g4 (문법 추가), Analyzer (CFG write tracking), Interpreter (validation logic)
