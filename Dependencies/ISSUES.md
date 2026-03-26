# Dependencies 사전분석 이슈

## 현재 상태 (2026-03-24)

### 정상 등록
- Interfaces: 37/44 (함수 등록 완료)
- Libraries: 17개 (전부 함수 등록 완료, Float 제외)
- Contracts: 2개 (ERC20, LockeERC20)

### 정상적으로 0 functions인 interfaces
| Interface | 이유 |
|-----------|------|
| IMochi | `interface IMochi is IERC20 {}` — 빈 interface |
| IPreparable | event만 정의, 함수 없음 |
| IPooledCreditLineEnums | enum만 정의 |
| IPooledCreditLineDeclarations | struct/enum만 정의 |

---

## 미해결 이슈

### Issue A: FloatStruct file-level struct 미등록

**영향 범위**: IDiscountProfile, IMochiProfile, IMochiVault (3개 interface) + Float library

**원인**:
- `Float.sol`에 `struct FloatStruct` (원래 `struct float`, 예약어 충돌로 rename)가 file-level에 정의
- `library Float`과 `struct FloatStruct`가 같은 파일에 공존
- 사전분석 시 `SolidityAnalyzer`가 각 파일을 독립 분석 → file-level struct가 다른 파일에 전파 안 됨
- IDiscountProfile 등이 `FloatStruct memory`를 반환 타입으로 사용 → 타입 미인식 → 함수 등록 실패

**해결 방안**:
1. Phase 0에 file-level struct 사전 수집 추가 (type alias처럼)
2. 또는 42_H_01 타겟 분석 시 Float.sol을 먼저 로드하여 struct 등록

**관련 케이스**: web3bugs_42_H_01 (annotated)

**관련 파일**:
- `Dependencies/libraries/Float.sol` — `struct FloatStruct` + `library Float`
- `Dependencies/interfaces/IDiscountProfile.sol` — `returns (FloatStruct memory)`
- `Dependencies/interfaces/IMochiProfile.sol` — `returns (FloatStruct memory)` 다수
- `Dependencies/interfaces/IMochiVault.sol` — `IERC20`, `Status` enum 사용

---

### Issue B: Float library 0 functions

**원인**:
- `Float.sol` 내 `struct FloatStruct`가 file-level → `library Float` 분석 시 `FloatStruct` 타입 미인식
- 함수 파라미터 `FloatStruct memory f`에서 타입 resolve 실패 → 함수 정의 실패

**해결 방안**: Issue A와 동일 — file-level struct 사전 등록 또는 같은 파일 내 struct를 library 분석 전에 등록

---

### Issue C: `float` → `FloatStruct` rename 일관성

**배경**:
- Solidity에서 `float`은 예약어 (미래 fixed-point 타입용)
- `Float.sol` 원본: `struct float { ... }` → ANTLR lexer가 keyword로 인식
- rename 체인: `float` → `Float` (첫 시도) → `FloatStruct` (library Float와 이름 충돌 해결)

**일관성 필요한 파일들**:
- `Dependencies/libraries/Float.sol` — ✅ `struct FloatStruct`
- `Dependencies/interfaces/IDiscountProfile.sol` — ✅ `FloatStruct memory`
- `Dependencies/interfaces/IMochiProfile.sol` — ✅ `FloatStruct memory`
- `evaluation/RQ2/target_contracts_contraction/web3bugs_42_H_01.sol` — ❌ 아직 미수정
- `evaluation/RQ2/rename_reserved_identifiers.py` — ✅ `'float': 'FloatStruct'` 등록

---

### Issue D: contracts/ 폴더 사전분석 미완료

**현재 상태**: Dependencies/contracts/에 LockeERC20.sol과 solmate_ERC20.sol만 분석 완료

**미분석 (evaluation/RQ2/.../dependencies/contracts/)**:
- `112_Controller.sol`, `45_Controller.sol` — concrete contract (상속용)
- `112_Roles.sol` — 상수 정의
- `47_AddressUpgradeable.sol`, `47_ContextUpgradeable.sol`, `47_ERC20Upgradeable.sol` — OpenZeppelin Upgradeable
- `47_Initializable.sol`, `47_SafeMathUpgradeable.sol` — OpenZeppelin
- `58_IVault.sol` — interface (IVault와 다른 버전)
- `AddressProviderKeys.sol`, `AddressProviderMeta.sol` — 상수/struct 정의
- `Authorization.sol`, `AuthorizationBase.sol` — 권한 관리
- `Pausable.sol`, `Preparable.sol` — modifier 컨트랙트
- `ReentrancyGuardUpgradeable.sol` — reentrancy guard
- `TokenProxyLike.sol` — 상수 정의

**prefix 충돌 문제**: `112_IVault`와 `58_IVault`가 다른 interface지만 같은 이름. 타겟별로 다른 dependency 세트를 로드해야 함.

**우선순위**: annotated 타겟 분석 시 필요한 것만 개별 처리

---

### Issue E: web3bugs_70_H_10용 interface 사전분석 필요

**영향 케이스**: web3bugs_70_H_10 (LiquidityBasedTWAP.syncVaderPrice)

**필요한 interface**:
- `IVaderPoolV2` — `70_IVaderPoolV2.sol` (evaluation/RQ2/target_contracts_original/dependencies/)
- `IBasePoolV2` — IVaderPoolV2가 상속
- `ExchangePair` struct, `Paths` enum — ILiquidityBasedTWAP에 정의 (이미 pkl 존재하나 struct/enum 전파 필요)

**현재 상태**:
- `IVaderPoolV2`가 Dependencies/interfaces/에 없음 → pkl 미생성 → interface_names 사전 스캔으로만 이름 등록
- `ExchangePair` struct가 ILiquidityBasedTWAP.sol에 정의되어 있으나 다른 contract로 전파 안 됨

**해결 방안**:
1. `70_IVaderPoolV2.sol`을 Dependencies/interfaces/에 복사 후 사전분석
2. `ExchangePair` struct를 file-level struct 사전 수집으로 전파 (Issue A와 동일 패턴)
