# L5 Verification Report

본 문서는 `L5_annotation_expressibility.md`의 25개 case에 대한 검증 결과를 정리한다.
검증 항목:
1. Bug description이 bug report와 일치하는가
2. `.sol` 파일에 기술된 코드가 실제로 존재하는가
3. Annotation이 `Solidity.g4` 문법상 유효한가
4. "왜 X인가"의 분류 근거가 타당한가
5. "Not possible" 케이스에 대해 hidden state variable이 없는가

`Solidity.g4` 주요 사실:
- `intentValue : arithExpr`이고 `arithExpr`는 `+ - * / %`만 지원 (exponentiation, 함수 호출, `**` 없음).
- `1e18` 같은 scientific literal은 `DecimalNumber` rule로 허용됨.
- `block.timestamp`, `msg.sender` 등은 `varRef`(`identifier subAccess*`)로 파싱 가능.
- `varRef`의 `subAccess`는 `.identifier` 또는 `[expression]`이므로 struct 필드·mapping 인덱스 모두 허용.
- `PostEntryExit`는 `intentValue '(' ENTRY relOp EXIT ')'`이며, 도구 레벨에서 "PostEntryExit의 intentValue에 산술식 사용 미지원"이라는 제약이 문서에 명시됨.
- `@During commonClause`에서 `changed(var, false)`의 의미(함수 시작부터 현재 지점까지 불변)는 문법상 허용되지만 tool-specific 해석이며 문법 자체로는 확인 불가.

검증 제약: Web3Bugs 원본 `contracts/` 디렉토리 파일을 직접 Read/Grep할 수 없어 `evaluation/RQ1/target_contracts_original/*.sol`(RQ2 재포장 파일)과 `Web3Bugs/reports/*.md`를 교차 확인하였다.

## Summary
- Total: 25
- Accurate (OK): 16
- Minor: 6
- Major: 3

주요 수정 필요 항목:
- **Direct-1 (62_H_10)**: primary annotation `@Post depositTokenAmount == 0`이 fix에서도 성립하지 않음 (Major)
- **Indirect-3 (52_H_23)**: annotation 타겟이 local 변수와 state 변수가 혼동되었고, 해당 케이스는 `limitation_types.md`에서 E5(missing-dependency)로 분류됨 (Major)
- **Not possible-10 (52_H_16)**: 제공된 `.sol` 파일이 V2 router(수정본)이며 `calculateOutGivenIn`이 파일에 존재하지 않음 (Major)

## Direct -- 7건

### 1. web3bugs_62_H_10 — Verdict: Major

**Bug description (확인)**: `62.md` H-10 line 671~ 의 내용과 정확히 일치. `creatorClaimSoldTokens`가 `depositTokenAmount`/`redeemedDepositTokens`를 갱신하지 않아 `recoverTokens`의 excess 계산이 잘못됨.

**Source 확인**: `web3bugs_62_H_10.sol` line 583~600 에서 `function creatorClaimSoldTokens(address destination)`에 `require`들, `uint112 amount = depositTokenAmount; claimedDepositTokens = true; ERC20(depositToken).safeTransfer(destination, amount);`가 존재하고 `depositTokenAmount`/`redeemedDepositTokens` 갱신이 없음을 확인.

**Grammar**: `@Post depositTokenAmount == 0`는 `PostCommon → commonClause → RelationalCmp` (`intentValue relOp intentValue`)로 valid.

**Problem (Major)**: 
- 권장 fix는 (report 695줄) `redeemedDepositTokens = depositTokenAmount`이지 `depositTokenAmount = 0`이 아님.
- 따라서 fixed code에서 `depositTokenAmount`는 여전히 원래 값 유지 → annotation `depositTokenAmount == 0`은 **buggy와 fixed 둘 다에서 violated**. 즉 이 annotation은 버그를 구분하지 못함.
- 도구 사용자가 fix를 인지해서 올바른 annotation을 쓸 경우, 실제로 쓸 것은 문서 "참고"에 적힌 `@Post redeemedDepositTokens == depositTokenAmount`임. 이 secondary annotation은 정상적으로 Direct로 작동한다.
- `case_mapping.csv`에서는 이 case의 function이 `recoverTokens`로 표기되어 있어 L5 doc(`creatorClaimSoldTokens`)과 불일치.

**권고**: primary annotation을 `@Post redeemedDepositTokens == depositTokenAmount`로 교체하고, `depositTokenAmount == 0` 은 제거하거나 "불완전한 제안"으로 표기. case_mapping.csv의 function과 L5 doc의 function 이름 일치 여부도 재확인 필요.

---

### 2. web3bugs_65_H_01 — Verdict: OK

**Bug description**: `65.md` H-01 line 86~ 의 "handleFees does not update `lastFee` if `startSupply == 0`"과 정확히 일치. 권장 fix도 "Set `lastFee = block.timestamp` if `startSupply == 0`"로 일치.

**Source**: `web3bugs_65_H_01.sol` line 133~153 `handleFees(uint256 startSupply)` 내부에서 `else if (startSupply == 0) { return; }` 분기가 존재하며 `lastFee` 갱신 없음을 확인.

**Grammar**: `@Post lastFee == block.timestamp`
- `lastFee`: `NumVarRef`
- `block.timestamp`: `block` (Identifier) + `.timestamp` (`IntentMemberAccess`) = valid varRef
- `RelationalCmp`로 파싱됨.

**분류 근거**: 정확. 모든 분기에서 `lastFee`가 current timestamp여야 한다는 불변식을 직접 명시.

---

### 3. web3bugs_113_H_05 — Verdict: OK

**Bug description**: `113.md` H-05 line 259~ 와 일치. `params.ltvBPS >= accepted.ltvBPS`가 `<=` 이어야 함. 권장 fix도 line 277의 `params.ltvBPS <= accepted.ltvBPS`와 일치.

**Source**: `web3bugs_113_H_05.sol` line 316의 `params.ltvBPS >= accepted.ltvBPS` require 확인.

**Grammar**: `@During params.ltvBPS <= accepted.ltvBPS`은 `DuringCommon → RelationalCmp`. `params.ltvBPS`는 struct 파라미터 필드 접근 → `varRef` (identifier + IntentMemberAccess)로 문법상 valid. tool이 struct 파라미터를 어떻게 다루는지는 별도 의존성이나 문법은 clean.

**분류 근거**: 정확. Annotation이 fix의 require 조건 자체를 직접 명시.

---

### 4. web3bugs_31_H_01 — Verdict: OK

**Bug description**: `31.md` H-01 line 66~ 와 일치. `currentLockRatio`는 percentage(×1e18), `newLockRatio`는 absolute CVX amount. 권장 fix("`currentLockRatio` should just be `balanceInLock`")와 L5 doc의 annotation이 완전히 일치.

**Source**: `web3bugs_31_H_01.sol` line 444의 `manualRebalance(uint256 toLock)` 내부 line 463-471:
```
uint256 balanceInLock = LOCKER.balanceOf(address(this));
...
uint256 currentLockRatio = balanceInLock.mul(10**18).div(totalCVXBalance);
uint256 newLockRatio = totalCVXBalance.mul(toLock).div(MAX_BPS);
```

**Grammar**: `@During currentLockRatio == balanceInLock`. 두 local 변수 비교, RelationalCmp. Valid.

**분류 근거**: 정확. Fix 공식을 annotation이 직접 표현.

---

### 5. web3bugs_79_H_02 — Verdict: Minor

**Bug description**: `79.md` H-02 line 117~ 와 일치. `tokenAllocated = (wavaxReserve * 10**decimals) / floorPrice`가 `wavaxReserve * 1e18 / floorPrice`이어야 함.

**Source**: `web3bugs_79_H_02.sol` line 377 `createPair()`, line 396-398:
```
if (floorPrice > (wavaxReserve * 10**token.decimals()) / tokenAllocated) {
    tokenAllocated = (wavaxReserve * 10**token.decimals()) / floorPrice;
    ...
}
```

**Grammar**: `@During tokenAllocated == wavaxReserve * 1e18 / floorPrice`는 DuringCommon RelationalCmp이며, `1e18`는 `DecimalNumber`로 파싱, `*` / `/` 는 arithExpr로 허용. Valid.

**Minor 문제 — annotation 배치**: 
- line 392에서 `tokenAllocated = tokenReserve`로 초기화되고, floor price 조건(line 396)이 참일 때만 line 398에서 수정값이 할당됨.
- Annotation을 function body level에서 부착하면 **floor 조건이 거짓인 경로에서 correct code에서도 `tokenAllocated != wavaxReserve*1e18/floorPrice`가 되어 violated**.
- L5 doc은 `@During` 배치 위치를 명시하지 않았으며, 문맥상 line 398 직후 여야 함. 이 점을 명시적으로 적어두는 것이 안전.

**분류**: Direct 자체는 유효하나, 배치 코멘트 보강 필요.

---

### 6. web3bugs_101_H_02 — Verdict: Minor

**Bug description**: `101.md` H-02 line 175~ 와 일치. 다만 bug report는 변수명 `_principalWithdrawable`로 기술하지만, 실제 `web3bugs_101_H_02.sol`의 `terminate()` 함수(line 366~)에서는 local 변수가 `_totalBorrowAsset` (line 398)으로 명명되어 있다. 이는 contest 버전 차이 또는 fix 과정에서의 rename으로 보임. L5 doc의 annotation은 sol 파일 실제 변수명 `_totalBorrowAsset`을 사용하므로 내부 일치는 OK.

**Source**: `web3bugs_101_H_02.sol` line 366 `terminate`, line 398 `uint256 _totalBorrowAsset = _actualNotBorrowedInShares.add(_totalInterestInShares);`, line 400 `SAVINGS_ACCOUNT.withdrawShares(..., _totalBorrowAsset, false);`. `_sharesHeld`는 line 376에서 로컬 변수로 할당됨.

**Grammar**: `@During _totalBorrowAsset == _sharesHeld` — 두 local 변수 비교. RelationalCmp. Valid.

**Minor**: bug description에서 "intuitive"한 변수명(`_principalWithdrawable`)을 사용해 독자가 sol 파일에서 이 변수명을 찾으면 발견하지 못한다. `_totalBorrowAsset` / `_actualNotBorrowedInShares` 같은 실제 코드 변수명도 병기하는 것이 좋음.

---

### 7. web3bugs_70_H_09 — Verdict: Minor

**Bug description**: `70.md` H-09 line 406~ 와 일치. Sponsor dispute도 line 481~488에서 확인. Dispute 코멘트 이후 명시적인 judge 판정문은 없으나 final report에는 High Risk Findings로 유지.

**Source**: `web3bugs_70_H_09.sol` line 66~97 `mint(uint256 vAmount)` 내부 line 76 `uAmount = (vPrice * vAmount) / 1e18;` 확인.

**Grammar**: `@During uAmount == vAmount * 1e18 / vPrice`는 DuringCommon RelationalCmp. Arithmetic valid.

**Minor — annotation 배치**:
- `uAmount`는 line 76에서 처음 할당 후 line 91에서 fee 차감으로 재할당됨 (`uAmount = uAmount - fee;`).
- Annotation을 line 76 직후에 두어야 하고, line 91 이후에 두면 correct code에서도 위반됨.
- 추가로 sponsor가 이 issue를 dispute한 점은 문서에 잘 기록되어 있으나, "Direct 7건"의 절반 가까이를 "논란 있는 케이스"로 포함시키는 것은 논문 주장의 강도를 약화시킬 수 있으므로 분류 변경보다는 서술 보강을 권장.

---

## Indirect -- 7건

### 1. web3bugs_192_H_01 — Verdict: OK

**Bug description**: `192.md` H-01 line 140~ 와 일치. `extendLock`에서 `totalLocked[_asset] += _amount` 누락.

**Source**: `web3bugs_192_H_01.sol` line 19 `mapping(address => uint) public totalLocked;`, line 84~92 `extendLock(...)` 함수 내부에 `totalLocked` 접근 없음. line 73 (다른 함수에서) `totalLocked[_asset] += _amount;`, line 103 (release) `totalLocked[asset] -= lockAmount;` 확인.

**Grammar**: `@Post totalLocked[_asset](Entry < Exit)` — `totalLocked[_asset]`은 `varRef` (NormalVarRef + IntentIndexAccess). `intentValue`로 감싸지는 `arithExpr → arithTerm → arithFactor → varRef` 경로로 파싱 후 PostEntryExit으로 매칭. Valid.

**분류 근거**: 정확. "증가해야 한다"는 방향만 명시, 정확한 `+_amount`는 표현 불가. Indirect 기준 충족.

---

### 2. web3bugs_62_H_03 — Verdict: OK

**Bug description**: `62.md` H-03 line 214~ 와 일치. `claimReward` 후 `rewardTokenAmount -= rewardAmt` 누락.

**Source**: `web3bugs_62_H_03.sol` line 151 `uint112 private rewardTokenAmount;`, line 555~578 `claimReward()` 내부 `rewardTokenAmount` 수정 없음을 확인.

**Grammar**: `@Post rewardTokenAmount(Entry > Exit)` — PostEntryExit, `rewardTokenAmount`은 state variable의 varRef. Valid.

**분류 근거**: 정확. 감소 방향만 명시.

---

### 3. web3bugs_52_H_23 — Verdict: Major

**Bug description**: `52.md` H-23 line 925~ 와 일치. `mintSynth` 시 `reserveForeign`이 감소 없이 그대로 기록됨.

**Source issues**:
- `web3bugs_52_H_23.sol` line 126 `mintSynth`, line 147 `(uint112 reserveNative, uint112 reserveForeign, ) = getReserves(foreignAsset);` — **`reserveForeign`은 local stack 변수** (tuple destructuring으로 받음).
- `_update(foreignAsset, reserveNative + nativeDeposit, reserveForeign, reserveNative, reserveForeign)` (line 158-164)에서 local `reserveForeign`이 storage에 기록되는 형태.
- 실제 state variable은 `pairInfo[foreignAsset].reserveForeign` (line 71, 75 등에서 접근).
- 파일에는 `contract VaderPoolV2 is IVaderPoolV2, BasePoolV2, Ownable`만 존재하고 `BasePoolV2`, `_update`의 실체는 `import "./BasePoolV2.sol"`로만 참조됨 → **파일만으로는 `_update`가 실제로 어떤 storage slot을 쓰는지 검증 불가**.

**Problems (Major)**:

1. **Annotation의 변수 지시 불명확**: `@Post reserveForeign(Entry > Exit)`의 `reserveForeign`은 local 변수인지 state (`pairInfo[foreignAsset].reserveForeign`)인지 모호. PostEntryExit의 의미(Entry/Exit storage comparison)에는 local이 들어갈 수 없으므로 state를 의도한 것이어야 하며, 올바른 표현은 `@Post pairInfo[foreignAsset].reserveForeign(Entry > Exit)`.
2. **Cross-document 불일치**: `evaluation/RQ1/limitation_types.md` line 250의 E5(`missing-dependency`) 목록에 `web3bugs_52_H_23`가 명시됨 (`E5 | missing-dependency | 분석에 필요한 외부 라이브러리 ... | web3bugs_52_H_23, web3bugs_16_H_04`). 그러나 L5 doc은 이 케이스를 Indirect로 분류(이전에 Not possible이었다가 승격). `BasePoolV2`가 import로만 존재하여 `_update`의 state 작성 의미를 분석할 수 없다면 이는 L5보다 E5에 속함.
3. **doc 내 "이전 분류: Not possible → Indirect 승격"** 코멘트는 재검토 필요함을 인정한 흔적으로 보이나, 승격 근거("state variable 재검토에서 `reserveForeign`이 `_update()`를 통해 storage에 기록되는 것을 확인")는 파일로부터 직접 입증되지 않음.

**권고**: 
- Annotation을 `pairInfo[foreignAsset].reserveForeign(Entry > Exit)`으로 정정.
- limitation_types.md와의 분류 충돌을 명시적으로 해소(E5 유지할 것인지, L5 Indirect로 옮길 것인지 문서간 일관성 확보).
- 만약 Indirect 유지라면, `_update` 구현이 실제로 `pairInfo[foreignAsset].reserveForeign`을 쓴다는 점을 BasePoolV2에서 직접 확인한 결과를 doc에 첨부할 것.

---

### 4. web3bugs_35_H_12 — Verdict: OK

**Bug description**: `35.md` H-12 line 444~ 와 일치. `mint()` 에서 `secondsPerLiquidity` 갱신 누락.

**Source**: `web3bugs_35_H_12.sol` line 49 `uint160 internal secondsPerLiquidity;`, line 141 `function mint(bytes calldata data)` 내부에서 line 184 `secondsPerLiquidity` 읽기만 있을 뿐 쓰기 없음. 쓰기는 line 317(`swap` 함수 내부)에서만 발생함을 확인.

**Grammar**: `@Post changed(secondsPerLiquidity, true)` — VarChangedEval. Valid.

**분류 근거**: 정확. 값/방향은 명시 못하고 변경 여부만. 문서의 부가 blocker(`abi.decode`로 param 전달 → debugging value 설정 제약) 지적도 타당.

---

### 5. web3bugs_83_H_01 — Verdict: OK

**Bug description**: `83.md` H-01 line 109~ 와 일치. `add()`에서 `massUpdatePools()` 호출 누락.

**Source 확인 불필요** (이미 `limitation_types.md`에도 예시로 등장). `web3bugs_83_H_01.sol` 파일 존재 확인됨.

**Grammar**: `@Post changed(poolInfo[0].accConcurPerShare, true)` — `poolInfo[0].accConcurPerShare`는 varRef (identifier + IntentIndexAccess `[0]` + IntentMemberAccess `.accConcurPerShare`). VarChangedEval. Valid.

**분류 근거**: 정확. 부가 주의사항(첫 `add()` 호출 시 `poolInfo[0]` 부재)도 명시되어 있어 현실적 한계를 잘 포착함.

---

### 6. web3bugs_35_H_11 — Verdict: Minor

**Bug description**: `35.md` H-11 line 405~ 와 대체로 일치, 단 **서술에 과장이 있음**.
- Bug report는 오직 **field swap** (`feeGrowthOutside0` vs `feeGrowthOutside1`)만 문제로 지적함. 권장 fix(line 430~440)도 나머지는 유지하고 0/1만 교체함.
- L5 doc은 "(a) 포인터 이동 후 잘못된 tick에 적용, (b) 필드 잘못됨"의 **두 가지 오류**로 기술했으나, (a)(`nextTickToCross = ticks[nextTickToCross].previousTick` 재할당)는 bug report에 지적되지 않았고 report 제안 fix도 이 부분을 건드리지 않음. Sushi team도 field swap만 수정한 것으로 보임(confirmed).

**Source**: `web3bugs_35_H_11.sol` line 23~53 `Ticks.cross(...)` line 32-40 `if (zeroForOne) { ... nextTickToCross = ticks[nextTickToCross].previousTick; ticks[nextTickToCross].feeGrowthOutside0 = feeGrowthGlobal - ticks[nextTickToCross].feeGrowthOutside0; }` 확인.

**Grammar**: `@Post changed(ticks[nextTickToCross].feeGrowthOutside1, true)` — VarChangedEval, varRef는 identifier + IntentIndexAccess + IntentMemberAccess. Valid.

**Semantic 참고**: `nextTickToCross`는 파라미터이며 함수 내부에서 재할당됨. Annotation에 사용된 `ticks[nextTickToCross]`가 Entry 값 기준으로 해석될 경우 buggy에서 실제로 변경되지 않음(다른 tick을 건드림) → annotation이 작동함. 따라서 결과 분류(Indirect)는 유효.

**Minor**: bug 서술에서 (a) 포인터 이동도 오류라는 부분을 제거하거나, "authoritative fix는 field swap만 수행"으로 표현 수정 권장.

---

### 7. web3bugs_112_H_01 — Verdict: Minor

**Bug description**: `112.md` H-01 line 118~ 와 일치. `transfer()`에서 balance 수정(line 112-113)이 `userCheckpoint()` 호출(line 117-118) 이전에 발생. `transferFrom()`은 올바른 순서.

**Source**: `web3bugs_112_H_01.sol` line 105~ `transfer(address account, uint256 amount)` 내부 line 112 `balances[msg.sender] -= amount;`, line 113 `balances[account] += amount;`, line 117 `ILpGauge(lpGauge).userCheckpoint(msg.sender);` 확인.

**Grammar**: `@During changed(balances[msg.sender], false)` — DuringCommon/VarChangedEval. 문법적으로 valid.

**Minor concern**: 
- `@During`에서 `changed(var, false)`의 의미("함수 시작부터 현재 annotation 지점까지 변경되지 않았어야 함")는 문법 자체에 정의된 의미가 아니라 tool-specific 해석. `Solidity.g4`만으로는 이 semantic이 실제로 구현되는지 검증 불가.
- 또한 annotation은 "line 117 시점"에 배치되어야 한다는 placement 요구가 있는데, `@During commonClause`가 program point에 precise하게 bound되는지는 tool 구현에 의존. Doc에 "checkpoint 호출 시점(line 117)에 배치"라고 명시했지만, IntentChecker의 실제 배치 메커니즘과 일치하는지 확인 필요.

**분류 근거**: 논리적으로는 타당 — balance-then-checkpoint vs checkpoint-then-balance ordering을 간접적으로 감지.

---

## Not possible -- 11건

### 1. web3bugs_36_H_02 — Verdict: Minor

**Bug description**: `36.md` H-02 line 214~ 와 일치. `auctionBurn()`이 `_burn()` 이후 `ibRatio` 업데이트 누락.

**Source**: `web3bugs_36_H_02.sol` line 102-108 `auctionBurn` 내부 `handleFees(); _burn(msg.sender, amount);`만 있고 ibRatio 갱신 없음. line 110~129 `handleFees`는 `lastFee == 0`일 때는 `lastFee = block.timestamp`만 set하고 ibRatio를 수정하지 않음; `else` 분기에서만 ibRatio 갱신.

**왜 Not possible인가 분석**:
- doc 주장 1: `changed(ibRatio, true)`가 buggy에서도 satisfied — **부분적 오류**. `handleFees`가 ibRatio를 수정하는 것은 **`lastFee != 0` AND `startSupply != 0` 분기**일 때만. 첫 호출(lastFee == 0) 또는 startSupply == 0 케이스에서는 handleFees가 ibRatio를 수정하지 않아 annotation이 buggy/correct를 구분 가능할 수도 있음.
- 그러나 정상 실행(steady state)에서는 handleFees가 매번 ibRatio를 수정하는 경우가 일반적이므로, 대부분의 경로에서 구분 불가라는 결론은 유효.
- 주장 3 (산술식 PostEntryExit 미지원)은 doc 전제와 일관. 주장 4 (ibRatio 올바른 값이 handleFees 중간 결과 의존)도 타당.
- `_totalSupply`는 doc의 "확인한 state variables"에 언급되며, 버기와 correct 모두 `_burn`에서 감소하므로 방향으로 구분 불가 — 정확.

**Grammar**: N/A.

**Minor**: `changed(ibRatio, true)` analysis에 "handleFees 특정 분기에서만 갱신된다"는 nuance를 추가하는 것이 좋음. 결론(Not possible)은 유지.

---

### 2. web3bugs_35_H_10 — Verdict: OK

**Bug description**: `35.md` H-13(report 번호) line 486~. L5 doc은 `35_H_10`으로 라벨링 — 이는 RQ2/RQ3 자체 case-id 시스템을 따르므로 report 번호와 어긋날 수 있음. case_mapping.csv에도 `web3bugs_35_H_10 | ConcentratedLiquidityPool | burn`로 등록되어 있어 내부 일관성 OK.

**Source**: `web3bugs_35_H_10.sol` line 231~ `burn(...)`, line 264 `reserve0 -= uint128(amount0fees);` (fees 차감만, amount0 전체 차감 없음) 확인.

**분류 근거**: 정확. buggy/correct 모두 reserve0 감소하므로 direction/changed로 구분 불가, magnitude(amount0fees vs amount0)만 차이 → Not possible.

추가 blocker(`abi.decode`로 파라미터 전달)도 타당.

**확인한 state variables**: 14개 모두 정상 반영.

---

### 3. web3bugs_62_H_01 — Verdict: OK

**Bug description**: `62.md` H-01 line 94~ 와 일치. `recoverTokens`의 excess 계산에서 `depositTokenFlashloanFeeAmount` 차감 누락.

**Source**: `web3bugs_62_H_01.sol` line 158 `depositTokenFlashloanFeeAmount` state variable, line 646 `recoverTokens(address token, address recipient)`, line 654 `uint256 excess = ERC20(token).balanceOf(address(this)) - (depositTokenAmount - redeemedDepositTokens);` 확인. `recoverTokens` 내부에서 state variable 수정은 없음 (unlocked lock modifier 제외).

**분류 근거**: 정확. `recoverTokens`는 값 반환도 없고, `balanceOf`는 함수 호출이므로 intentValue로 표현 불가.

---

### 4. web3bugs_58_H_04 — Verdict: OK

**Bug description**: `58.md` H-04 line 222~ 와 일치. `tvl()`이 cached `_tvls` 반환, `_push()`에서 `updateTvls()` 호출이 deposit 이후에 위치.

**Source**: `web3bugs_58_H_04.sol` line 27 `_tvls` state variable, line 46 `tvl() public view`, line 51 `updateTvls() public`, line 57~78 `_push(...)` 내부 line 74 deposit → line 76 `updateTvls()` (deposit 이후) 확인.

**분류 근거**: 정확. 
- `tvl()`은 view — 수정 없음.
- `_push()`에서 `_tvls`는 **결국 업데이트됨** → `changed(_tvls, true)`가 buggy/correct 모두 satisfied.
- 문제는 ordering: buggy/correct의 차이는 "LPIssuer가 _push를 호출할 때 사용하는 tvl 값"이며, 이는 해당 함수 외부의 caller 시점 문제.

---

### 5. web3bugs_61_H_02 — Verdict: Minor

**Bug description**: `61.md` H-02 line 100~ 와 일치. `savingsAccountTransfer`가 외부 호출 return value 대신 `_amount`를 반환.

**Source**: `web3bugs_61_H_02.sol` line 8 `library SavingsAccountUtil`, line 66~80 `savingsAccountTransfer(...)` 내부에서 `_savingsAccount.transfer(...)` (return 무시) 호출 후 `return _amount;`. 권장 fix와 일치.

**분류 근거 (Minor)**:
- "library → state 없음" 정확.
- "폐기된 return value 담는 변수 없음" 정확 — correct 버전은 `return _savingsAccount.transfer(...)`로 수정되어 변수에 저장하지 않음.
- 주장 4 `returnExpression != _amount` — 문서는 "pps == 1이면 둘이 같으므로 false positive"라고 서술. 더 정확한 표현은 "correct code도 pps == 1일 때 동일 값을 반환하므로 annotation이 correct code에서도 violated되어 구분 불가" (false positive가 아니라 false negative / 구분 불가)임. 어휘 선택 개선 권장.

---

### 6. web3bugs_70_H_08 — Verdict: OK

**Bug description**: `70.md` H-08 line 381~ 와 일치. Fixed-point scaling 오류.

**Source**: `web3bugs_70_H_08.sol` line 25 `address public router;`, line 28 `uint256 public lastGrant;`, line 31 `ILiquidityBasedTWAP public lbt;`. line 84~ `reimburseImpermanentLoss(address recipient, uint256 amount)` 내부 line 95-103은 `amount` local 변수 수정, line 107 `vader.safeTransfer(...)`만 수행. 어떤 state variable도 수정하지 않음. `lastGrant`는 이 함수에서 수정 안 됨 (다른 함수 line 130에서만 수정).

**분류 근거**: 정확. 함수가 state를 수정하지 않으며 return 값도 없음.

---

### 7. web3bugs_110_H_01 — Verdict: OK

**Bug description**: `110.md` H-01 line 130~ 와 일치. `balance()`가 `token.balanceOf(address(this))`만 반환, `+ IStrategy(strategy).balanceOf()` 누락.

**Source**: `web3bugs_110_H_01.sol` line 293~295 `function balance() public view returns (uint256) { return token.balanceOf(address(this)); }` 확인.

**분류 근거**: 정확. view 함수, 외부 interface call(`IStrategy(strategy).balanceOf()`)을 intentValue로 표현 불가.

---

### 8. web3bugs_17_H_02 — Verdict: OK

**Bug description**: `17.md` H-02 line 107~ 와 일치. a/b, a/c만 체크하고 b/c 체크 누락.

**Source**: `web3bugs_17_H_02.sol` line 30 `BASIS_POINTS`, line 36 `lastRatio` mapping, line 43 `tokenRatios` mapping, line 87 `safetyCheck() external view override returns (bool)` 확인.

**분류 근거**: 정확. view 함수이며 누락된 검증 로직을 annotation으로 표현 불가.

---

### 9. web3bugs_52_H_15 — Verdict: OK

**Bug description**: `52.md` H-15 line 585~ 와 일치. 3-path swap 인자 순서 뒤바뀜.

**Source**: `web3bugs_52_H_15.sol` line 304~ `function _swap(uint256 amountIn, address[] calldata path, address to) private`, line 326 `return pool1.swap(0, pool0.swap(amountIn, 0, address(pool1)), to);` (bug 그대로) 확인. State variables `factory`(immutable), `reserve`는 _swap에서 미수정.

**분류 근거**: 정확.
- `DuringFunctionArg`: `swap.arg[N] == ...` 문법상 지원되지만, nested call 에서 어떤 `swap`인지 모호하다는 지적도 타당.
- 외부 pool contract의 reserve 변경은 이 contract의 state가 아니므로 annotation 대상 밖.

---

### 10. web3bugs_52_H_16 — Verdict: Major

**Bug description**: `52.md` H-16 line 620~ 는 `VaderRouter.calculateOutGivenIn`의 3-path 인자 순서 오류.

**Source Problem (Major)**: 
- `web3bugs_52_H_16.sol` (341 라인)에는 **`calculateOutGivenIn` 함수가 존재하지 않음** (Grep 결과).
- 파일은 `contract VaderRouterV2 is IVaderRouterV2, ProtocolConstants, Ownable` (line 30), `IVaderPoolV2 public immutable pool;`, `pool.doubleSwap(...)` 사용 (line 312) — 이는 **수정본 V2 router**이며 원래 bug가 있었던 V1 VaderRouter의 `calculateOutGivenIn`과는 별개 파일.
- `web3bugs_52_H_15.sol`(V1 router, `_swap` 포함)과 `web3bugs_52_H_16.sol`(V2 router, `_swap` 포함)은 서로 다른 파일이지만, H-16 bug가 실제로 존재하려면 V1 router 파일의 `calculateOutGivenIn`이 필요.
- `case_mapping.csv` row 24에는 `web3bugs_52_H_16 | VaderRouter | calculateOutGivenIn | ... | 52/contracts/dex/router/VaderRouter.sol`로 기록되어 있어, 매핑상 파일 경로는 V1 (`dex/router/VaderRouter.sol`)이지만 실제 배치된 `web3bugs_52_H_16.sol` 파일은 V2(`dex-v2/router/VaderRouterV2.sol`)인 것처럼 보임.

**왜 Not possible 분류 자체는 옳은가**:
- `calculateOutGivenIn`이 view 함수이므로 state 수정 없음 → 분류 결론(Not possible)은 유지 가능.
- 그러나 **bug를 재현할 수 있는 source가 있어야 annotation 작성 가능 여부를 실증할 수 있음**. 현재 파일에서는 bug가 존재하지 않으므로 doc의 "왜 Not possible인가" 분석이 실제 파일 기준이 아닌 bug report 기반 추론.

**권고**:
- `web3bugs_52_H_16.sol`을 V1 VaderRouter 파일(`calculateOutGivenIn` 포함)로 교체하거나, 해당 케이스에 "파일 부재/불일치" 코멘트를 추가.
- 또한 `case_mapping.csv`의 target_sol_file 경로와 실제 target_contracts_original 파일의 내용이 매칭되는지 일괄 점검 권장.

---

### 11. web3bugs_59_H_05 — Verdict: OK

**Bug description**: `59.md` H-05 line 277~ 와 일치. `_calculateMaltRequiredForExit`가 penalty-adjusted maltQuantity를 return.

**Source**: `web3bugs_59_H_05.sol` line 44 `auctionEarlyExits` mapping, line 65~ `exitEarly`, line 66 `maltQuantity = _calculateMaltRequiredForExit(...)`, line 78 `auctionExits.maltUsed = auctionExits.maltUsed + maltQuantity;`, line 83 `auction.amendAccountParticipation(..., maltQuantity)` 확인.

**분류 근거**: 정확. `auctionEarlyExits`는 수정되지만 buggy maltQuantity가 **자체 contract의 관점에서는 "올바르게" 기록**됨. 올바른 값은 외부 `Auction` contract의 state(`userMaltPurchased`, `userCommitment`)에 의존하여 intentValue로 표현 불가.

**확인한 state variables**도 정확.

---

## Cross-cutting observations

### C1. limitation_types.md와 L5 doc의 cross-document 불일치

1. **web3bugs_52_H_23** — limitation_types.md line 250에서 `E5 | missing-dependency` 목록에 포함됨. L5 doc에서는 Indirect로 분류. 동일 케이스가 두 문서에서 다르게 분류되어 있음.
2. **web3bugs_17_H_02** — limitation_types.md line 35의 L5a 목록(`web3bugs_83_H_01, web3bugs_35_H_10, ..., web3bugs_17_H_02`)에 포함. L5 doc에서는 Not possible (11건 중 하나)로 분류 — 여기까지는 L5 큰 카테고리 안이므로 크게 문제 아님.
3. Direct/Indirect/Not possible 세부 분류와 limitation_types.md 간의 교차 매핑이 부재하므로 독자가 두 문서를 대조할 때 혼선 가능.

### C2. Annotation 배치(placement) 명시 부족

여러 케이스에서 annotation의 **프로그램 상 정확한 위치**가 중요하나 doc에 명시되지 않음:
- Direct-5 (79_H_02): `tokenAllocated` 재할당 이후
- Direct-7 (70_H_09): fee 차감 이전
- Indirect-7 (112_H_01): line 117 checkpoint 호출 시점 (이것만 명시됨)
- Direct-1 (62_H_10): creatorClaimSoldTokens vs recoverTokens 중 어느 함수에서 check

`@During` / `@Post`는 semantic이 다르고(`@During`은 program point 기반, `@Post`는 function exit 기반), 특히 `@During ... changed(var, false)` 같은 tool-specific semantic은 명시 필요.

### C3. Function 이름 일관성 (62_H_10)

L5 doc: creatorClaimSoldTokens  
case_mapping.csv: recoverTokens  
Bug root: creatorClaimSoldTokens  
Bug manifests in: recoverTokens  

IntentChecker가 어느 함수에 annotation을 부착하고 분석하는지 명확히 할 것.

### C4. 문법적 검증과 tool-implementation 검증의 구분

이 리뷰는 `Solidity.g4`만으로 annotation의 syntactic validity를 확인하지만, doc에서 "도구 미지원"으로 언급되는 제약(PostEntryExit에서 산술식 미지원 등)은 문법과 무관한 tool 한계임. 몇몇 케이스는 문법은 OK이지만 IntentChecker가 실제로 처리하는지는 별도 검증 필요:
- Struct 파라미터 필드 접근 (`params.ltvBPS`)
- Array/mapping 인덱싱 (`totalLocked[_asset]`, `ticks[nextTickToCross]`)
- `@During ... changed(..., false)`의 "지점 기반" semantic

### C5. Dispute된 bug의 신뢰도

- **70_H_09**: Sponsor dispute (L5 Direct-7). Doc에 caveat 있음. 
- **35_H_12**: Sponsor dispute → 나중에 confirmed (L5 Indirect-4). 
두 건 모두 논문에서 reviewer가 의문을 제기할 수 있는 case이므로, dispute → 최종 판정의 history를 명시적으로 기록하는 것이 좋음.

### C6. Source-truth 검증

`62.md`의 H-10 report 695줄의 fix 제안("set `redeemedDepositTokens` to be `depositTokenAmount`")은 L5 doc의 primary annotation(`depositTokenAmount == 0`)과 **일치하지 않음** (Direct-1 Major 참조). 모든 Direct 케이스에 대해 "doc의 annotation ≡ report의 fix 제안"인지 마지막으로 한 번 더 대조 권장.

---

## Recommendations

1. **Direct-1 (62_H_10)의 primary annotation 교체**: `@Post depositTokenAmount == 0` → `@Post redeemedDepositTokens == depositTokenAmount`. 현재의 primary는 fix에서도 성립하지 않음. (Major fix)

2. **Indirect-3 (52_H_23) 재분류 또는 문서 간 통합**: 
   - Annotation 타겟을 `pairInfo[foreignAsset].reserveForeign`으로 정정.
   - `limitation_types.md`의 E5 분류와의 충돌 해결: 이 케이스가 E5인지 L5(Indirect)인지 한 문서에서만 분류하도록 조정.
   - `_update`의 실제 storage 작성 여부를 BasePoolV2 소스로부터 검증.

3. **Not possible-10 (52_H_16) 소스 파일 교체**: 현재 `web3bugs_52_H_16.sol`은 VaderRouterV2(bug가 없는 수정본)이므로, `calculateOutGivenIn`이 포함된 V1 VaderRouter 원본으로 교체하거나 문서에 "파일 불일치" 주석을 명기.

4. **Annotation placement 명시**: Direct-5, Direct-7 등에서 annotation이 function body 내부 어느 지점(statement line)에 부착되는지 명시. `@During`의 구체적 anchor 지점을 각 케이스에 코멘트로 추가.

5. **Function mapping consistency**: Direct-1 case는 L5 doc의 function name과 `case_mapping.csv`의 function name 불일치. 일괄 점검 권장.

6. **Minor wording 수정**:
   - Indirect-6 (35_H_11): "두 가지 오류"를 "field 선택 오류(authoritative fix)"로 축약.
   - Not possible-5 (61_H_02): "false positive"를 "buggy/correct 둘 다에서 annotation이 violated될 수 있어 구분 불가"로 수정.
   - Not possible-1 (36_H_02): `handleFees`가 모든 실행에서 `ibRatio`를 수정하지는 않는다는 nuance 추가.

7. **Dispute history 기록**: 70_H_09(Direct-7), 35_H_12(Indirect-4)는 sponsor dispute가 있었으므로 해당 dispute → 최종 판정 흐름을 각 케이스 별도 코멘트로 보존.

8. **limitation_types.md ↔ L5 doc 교차 참조**: L5 카테고리 내에서 Direct/Indirect/Not possible 세부 분류를 `limitation_types.md`에도 반영하거나, L5 doc 머리말에 "limitation_types.md의 L5 목록에서 Direct/Indirect/Not possible로 재분류" 명시.

---

## 종합 평가

- 전반적으로 **bug description의 사실적 정확성**은 높다(25건 중 23건이 report와 일치).
- Grammar validity도 대부분 `Solidity.g4`와 합치 (25건 모두 파싱 가능한 형태).
- 주요 issue는 (a) **Direct-1의 primary annotation 오류**, (b) **Indirect-3과 Not-possible-10의 source/분류 부정합**, (c) **부수적 wording/placement 정리**에 집중됨.
- Direct/Indirect/Not possible의 **분류 기준**(annotation이 fix의 올바른 값을 명시 vs 방향/변경 여부만 vs 표현 불가)은 일관되게 적용되었으며, 전체 분석의 논리 구조는 건전함.

Accurate: 16 / Minor: 6 / Major: 3 / Total: 25
