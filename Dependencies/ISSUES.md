# Dependencies 사전분석 이슈

## 현재 상태 (2026-03-26)

### 정상 등록
- Interfaces: 46개 (IBasePoolV2, IVaderPoolV2 추가)
- Libraries: 17개 (Float 포함 전부 함수 body 빌드 완료)
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

### Issue C: float → FloatStruct rename — ✅ 부분 해결
- Dependencies 쪽은 완료
- `evaluation/RQ2/target_contracts_contraction/web3bugs_42_H_01.sol` — 아직 미수정 (42_H_01 실행 시 필요)

### Issue D: contracts/ 폴더 사전분석 — ✅ 해결 (2026-03-26)
- 18개 contract pkl 생성 완료
- parent pkl 로드로 상속 state variable 주입

### Issue E: IVaderPoolV2 interface — ✅ 해결 (2026-03-26)
- IVaderPoolV2.sol, IBasePoolV2.sol을 Dependencies/interfaces/에 추가 후 사전분석
- ExchangePair struct, Paths enum은 ILiquidityBasedTWAP.pkl에 이미 포함

---

## 남은 한계 (당장 블로커 아님)
- Assembly 함수 (AddressUpgradeable.functionCall 등): annotated 케이스에서 미사용
- Virtual/abstract 빈 함수: 정상 동작
- constant/immutable 변수 state_variable_node 미등록: not_detectable 케이스만 해당
