# Dependencies 사전분석 이슈

## 현재 상태 (2026-03-27)

### 정상 등록
- Interfaces: 46개 (IBasePoolV2, IVaderPoolV2 추가)
- Libraries: 17개 (Float 포함 전부 함수 body 빌드 완료, 0 empty)
- Contracts: 18개

### 정상적으로 0 functions인 interfaces
| Interface | 이유 |
|-----------|------|
| IMochi | `interface IMochi is IERC20 {}` — 빈 interface |
| IPreparable | event만 정의, 함수 없음 |
| IPooledCreditLineEnums | enum만 정의 |
| IPooledCreditLineDeclarations | struct/enum만 정의 |

---

## 해결된 이슈

### Issue A/B: FloatStruct file-level struct — ✅ 해결 (2026-03-26)
- Phase 0에서 file-level struct 사전 수집 (`scan_file_level_structs`)
- `sa.file_level_structs`에 주입
- `StaticCFGFactory.make_param_variable`에서 file-level struct fallback 추가
- Float library 11 functions 정상 빌드

### Issue C: float → FloatStruct rename — ✅ 해결 (2026-03-26)
- Dependencies 쪽 완료
- `web3bugs_42_H_01.sol` contraction에서 `float` → `FloatStruct` rename 완료

### Issue D: contracts/ 폴더 사전분석 — ✅ 해결 (2026-03-26)
- 18개 contract pkl 생성 완료
- parent pkl 로드로 상속 state variable 주입

### Issue E: IVaderPoolV2 interface — ✅ 해결 (2026-03-26)
- IVaderPoolV2.sol, IBasePoolV2.sol을 Dependencies/interfaces/에 추가 후 사전분석
- ExchangePair struct, Paths enum은 ILiquidityBasedTWAP.pkl에 이미 포함

---

## 미해결 이슈

### Issue F: ERC1155Upgradeable 사전분석 필요

**영향 케이스**: web3bugs_101_H_01 (LenderPool._calculatePrincipalWithdrawable)

**필요한 contract**:
- `ERC1155Upgradeable` — `balanceOf(address, uint256)` 함수 제공
- LenderPool이 ERC1155Upgradeable 상속 → `balanceOf` internal call

**현재 상태**:
- `ERC1155Upgradeable` pkl 미존재 → parent contract CFG 없음 → `balanceOf` 해석 불가
- NO_RESULT 상태 (intent 동작, debug annotation 반영, 하지만 balanceOf 결과가 top)

**해결 방안**:
1. ERC1155Upgradeable.sol contraction 후 Dependencies/contracts/에 추가 → 사전분석
2. 또는 contraction에 `balanceOf` 함수 직접 포함

---

## 남은 한계 (당장 블로커 아님)
- Assembly 함수 (AddressUpgradeable.functionCall 등): annotated 케이스에서 미사용
- Virtual/abstract 빈 함수: 정상 동작
- constant/immutable 변수 state_variable_node 미등록: not_detectable 케이스만 해당

---

# RQ2 실험 진행 현황 (2026-03-27)

## 이번 세션 엔진 수정 사항

### 1. Overload 함수 구분 (ContractAnalyzer, CFG)
- `find_function_context()`: 함수명 + param_types 튜플 반환 (multi-line 대응 포함)
- `analyze_context()`: `current_target_function_param_types` 저장
- `get_function_cfg()` 30곳: `param_types` 전달
- type alias resolve (UFixed18 → uint256 등)

### 2. Cross-library 호출 (Dependencies/main.py, Evaluation.py)
- `_global_library_cfgs` 누적 주입 + library 분석 순서 조정
- Qualified library call (`LibName.func()`) — identifier에서 library marker 반환 + member access에서 library CFG 조회
- `callerContext` 분기에서도 library 이름 인식

### 3. Struct 인자 전달 (Evaluation.py, Engine.py)
- 함수 호출 시 struct 인자: `.members` deepcopy
- identifier evaluate 시 StructVariable 객체 자체 반환
- `caller_env` 병합: 덮어쓰기 → `if k not in` 방식

### 4. Interface type cast (EnhancedSolidityVisitor.py, Evaluation.py, AddressSet.py)
- `visitFunctionCall`에서 interface/contract 이름이면 `TypeConversion` Expression 생성
- `evaluate_type_conversion_context`에서 interface cast → AddressSet + `_cast_interface` 태깅
- AddressSet `__slots__`에 `_cast_interface` 추가
- member access에서 cast된 interface 함수 호출 → `InterfaceFunctionCallContext`
- function call에서 interface function return type lookup (pkl에서) → top 반환

### 5. MetaType (EnhancedSolidityVisitor.py)
- `visitMetaType`에서 `expr.typeName` 설정 → `type(int256).max` 정상 동작

### 6. Mapping struct value 지원 (ContractAnalyzer.py)
- state/local MappingVariable 생성 시 `struct_defs`/`enum_defs` 주입
- file-level struct + parent 체인 포함

### 7. Modifier placeholder variables (DynamicCFGBuilder.py)
- `build_modifier_placeholder`에서 새 node에 `cur_block.variables` 복사

### 8. For문 grammar 수정 (EnhancedSolidityVisitor.py)
- `visitInteractiveForStatement`: condition은 `ctx.expressionStatement().expression()`, update는 `ctx.expression()`

### 9. Refine 미지원 operator 스킵 (Refine.py)
- 함수 호출 등 refine 불가능한 operator → `return` (sound overapproximation)

### 10. Logical operator BoolInterval 변환 (Evaluation.py)
- `&&`/`||` 연산에서 non-BoolInterval 피연산자 → `BoolInterval.top()` 변환

### 11. Narrowing unreachable node 스킵 (Engine.py)
- fixpoint narrowing에서 widening 미도달(out_vars=None) node 제외

### 12. Node variables 백업/복원 (Engine.py)
- `_interpret_function_cfg_impl`에서 시작 시 node variables 백업, 종료 시 복원
- debug annotation `flush()` 후 definition-time node 상태 보존

### 13. Snapshot restore 수정 (Snapshot.py)
- `restore_from_snap`에서 실제 객체 `__dict__` 복원 추가

### 14. Parent state variable 주입 (StaticCFGFactory.py)
- `make_function_cfg`, `make_modifier_cfg`에서 parent 체인 순회하여 state variable 주입

### 15. Dependencies pkl 로드 확장 (main.py)
- `load_dependencies()`에서 `ifc_*.pkl`, `lib_*.pkl`, `con_*.pkl` 전부 로드
- contract pkl: prefix 제거 후 `contract_cfgs`에 등록

### 16. SafeMathUpgradeable 순서 (Dependencies/contracts)
- 3-arg overload를 2-arg 위로 reorder (forward reference 해결)

### 17. Update.py struct 반환
- `update_left_var_of_member_access_context`에서 mapping entry가 StructVariable이면 바로 반환

---

## 케이스별 실행 결과 (19/21건, 42_H_01/78_H_02 미생성) — 2026-03-27 최신

| # | Case | Status | 비고 |
|---|------|--------|------|
| 1 | WANGMI | ✅ VIOLATED (V=1) | _merge_values None 방어 추가 후 해결 |
| 2 | Nokon | ⚠️ WARNING (W=1) | intent 동작, violation 미확정 |
| 3 | SwordCrowdsale | ✅ VIOLATED (V=2) | |
| 4 | BoostToken_operator | ✅ VIOLATED (V=2) | |
| 5 | BoostToken_indivisible | ✅ VIOLATED (V=4) | |
| 6 | HIT | ❌ ERROR | ImplicationContext.commonClause (보류) |
| 7 | 5_H_07 | ✅ VIOLATED (V=1) | |
| 8 | 5_H_08 | ✅ VIOLATED (V=1) | |
| 9 | 5_H_12 | ✅ VIOLATED (V=1) | |
| 10 | 77_H_01 | ✅ VIOLATED (V=1) | |
| 11 | 101_H_01 | ⚠️ WARNING (W=1) | Issue F(ERC1155) 필요 |
| 12 | 45_H_01 | ❌ ERROR | str.is_bottom — mapping[msg.sender] 접근 시 top key로 기존 entry 미조회 |
| 13 | 47_H_02 | ❌ ERROR | Type 'ERC20Upgradeable' — contraction에서 parent contract 타입 미인식 |
| 14 | 51_H_02 | ❌ ERROR | Type 'LPToken' — contract 타입 미인식 |
| 15 | 56_H_02 | ❌ ERROR | struct member 'getEarnedYield' — struct가 interface function call 결과인 경우 |
| 16 | 58_H_02 | ❌ ERROR | str.is_bottom — interface call 반환값이 str (45_H_01과 동류) |
| 17 | 60_H_01 | ❌ ERROR | KeyError: None |
| 18 | 62_H_08 | ❌ ERROR | Modifier 'governed' not defined |
| 19 | 70_H_10 | ❌ ERROR | Type 'ExchangePair' — struct 전파 |

**9 VIOLATED + 2 WARNING + 8 ERROR = 19건**

---

## 이번 세션 완료 사항 (2026-03-27 세션 2)

### 1. @Debugging BEGIN/END 전체 삽입
- 모든 19개 케이스 JSON에 `@Debugging BEGIN/END` 추가
- 이전에는 debug annotation 개별 flush → 동일 intent 반복 체크 (V 수 과다)
- 수정 후 일괄 flush → 정확한 V 수

### 2. _merge_values None 방어 (Helper.py)
- `VariableEnv._merge_values`: v1/v2가 None이면 다른 쪽 반환
- WANGMI의 `INITIAL_DOMAIN_SEPARATOR` BytesSet/None join 에러 해결

### 3. Interface 타입 state variable 지원
- `process_state_variable`: typeCategory=="interface" → AddressSet.top() + `_cast_interface`
- `process_variable_declaration`: 동일 (local variable)
- `evaluate_identifier_context`: MemberAccessContext에서 interface 타입은 `.value` 반환
- 45_H_01의 `interestRateModel.getBorrowRate()` str.multiply 에러 해결

### 4. JSON 재생성 (에러 케이스 8건)
- clean contraction .sol(target_contracts_contraction/)에서 soltotestjson.py로 code records 생성
- 기존 JSON에서 annotation 추출 → code + intent + BEGIN/debug/END 순서로 재조합
- 대상: 45_H_01, 47_H_02, 51_H_02, 56_H_02, 58_H_02, 60_H_01, 62_H_08, 70_H_10

---

## 다음 작업 (TODO)

### 우선순위 1: 45_H_01 mapping 접근 문제
- `accountBorrows[msg.sender].principal`이 `symbolic(None.principal)` → mapping entry 미조회
- msg.sender는 사전 정의(top) → top key로 mapping 접근 시 기존 annotation entry `101`을 찾지 못함
- mapping에서 top key 접근 시 기존 entry fallback 로직 확인 필요

### 우선순위 2: 58_H_02 동류 문제
- `str.is_bottom` — interface call 반환값이 interval이 아닌 string
- 45_H_01과 동일 유형, interface member access 경로 추가 확인 필요

### 우선순위 3: 타입 미인식 문제
- 47_H_02: `ERC20Upgradeable` parent contract 타입
- 51_H_02: `LPToken` contract 타입
- 70_H_10: `ExchangePair` struct (ILiquidityBasedTWAP에 정의 → 전파 필요)
- contraction .sol에서 해당 타입을 사용하는 코드를 visitFunctionCall에서 인식하도록 수정 필요

### 우선순위 4: 기타 에러
- 56_H_02: `'getEarnedYield' not in struct '_self'` — struct member가 interface function인 경우
- 60_H_01: `KeyError: None` — 원인 미분석
- 62_H_08: `Modifier 'governed' not defined` — modifier dependency 필요

### 우선순위 5: 미생성 케이스
- 42_H_01: FloatStruct rename 완료, JSON 생성 필요 (Float library dependency 복잡)
- 78_H_02: ERC20 상속 private state variable 문제 (Issue 8)

### 우선순위 6: Implication 구현
- HIT 케이스: `ImplicationContext.commonClause` 미구현

### 우선순위 7: Dependency 추가
- Issue F: ERC1155Upgradeable (101_H_01용)
