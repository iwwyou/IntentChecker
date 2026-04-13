"""
web3bugs_70_H_10 (LiquidityBasedTWAP.syncVaderPrice) debug annotation 값 생성기
Z3 solver를 이용해 underflow/overflow 없이 loop body에 진입하는
변수 조합을 생성한다.

생성 조건 (annotation_plans.md 참조):
C1: block.timestamp >= twapData[1].lastMeasurement  (underflow 방지)
C2: block.timestamp - lastMeasurement >= updatePeriod  (loop body 진입)
C3: previousPrices[0] > 0  (의미 있는 가격)
C4: 모든 값 양수 및 합리적 범위
C5: _updateVaderPrice 내부 overflow 방지 (reserveNative * previousPrices[0] 등)

참고: reserveNative, reserveForeign, chainlinkPrice, nativeTokenPriceCumulative(new)는
      외부 interface call → Top. annotation 가능 변수만 constraint 대상.
"""

from z3 import *

# ── 변수 선언 ──

# GlobalVar
block_timestamp = Int('block_timestamp')

# StateVar
previousPrices_0 = Int('previousPrices_0')          # previousPrices[uint256(Paths.VADER)]
vaderPairs_length = Int('vaderPairs_length')          # vaderPairs.length (고정 1)
totalLiquidityWeight_0 = Int('totalLiquidityWeight_0')  # totalLiquidityWeight[uint256(Paths.VADER)]
lastMeasurement = Int('twapData_1_lastMeasurement')
updatePeriod = Int('twapData_1_updatePeriod')
pastLiquidityEvaluation = Int('twapData_1_pastLiquidityEvaluation')
nativeTokenPriceCumulative = Int('twapData_1_nativeTokenPriceCumulative')

# ── 중간 계산식 ──
# timeElapsed = block.timestamp - pairData.lastMeasurement
timeElapsed = block_timestamp - lastMeasurement

# ── Solver ──
s = Solver()

# 기본 양수/합리적 범위 제약
s.add(block_timestamp > 0)
s.add(previousPrices_0 > 0)
s.add(vaderPairs_length == 1)  # pair 1개 고정
s.add(totalLiquidityWeight_0 > 0)
s.add(lastMeasurement > 0)
s.add(updatePeriod > 0)
s.add(pastLiquidityEvaluation > 0)
s.add(nativeTokenPriceCumulative >= 0)

# ── 생성 조건 ──

# C1: underflow 방지 - block.timestamp >= lastMeasurement
# (line 93: uint256 timeElapsed = block.timestamp - pairData.lastMeasurement)
s.add(block_timestamp >= lastMeasurement)

# C2: loop body 진입 - timeElapsed >= updatePeriod
# (line 95: if (timeElapsed < pairData.updatePeriod) continue)
s.add(timeElapsed >= updatePeriod)

# C3: previousPrices[0] 의미 있는 값
s.add(previousPrices_0 >= 1)

# C4: _updateVaderPrice 내부 overflow 방지
# reserveNative * previousPrices[0] 이 uint256 범위 내여야 함
# reserveNative는 외부 call → Top이지만, previousPrices[0]를 합리적으로 제한
# (TWAP 가격은 보통 1e18 스케일)
UINT256_MAX = 2**256 - 1
s.add(previousPrices_0 <= 10**24)  # 가격이 1e24 이하 (넉넉한 범위)

# C5: nativeTokenPriceCumulative(old)가 합리적 범위
# unchecked { (newCumulative - oldCumulative) / timeElapsed } 에서
# newCumulative는 Top이므로 oldCumulative는 문서화 목적
s.add(nativeTokenPriceCumulative >= 0)
s.add(nativeTokenPriceCumulative <= 10**30)

# ── 값 범위 힌트 (현실적인 값 유도) ──
# block.timestamp: 실제 이더리움 시간은 ~1.7e9 (2024년 기준) 범위지만 간소화
s.add(block_timestamp >= 10000)
s.add(block_timestamp <= 10**10)

# updatePeriod: TWAP 업데이트 주기 (보통 수 분 ~ 수 시간)
s.add(updatePeriod >= 60)         # 최소 1분
s.add(updatePeriod <= 86400)      # 최대 1일

# lastMeasurement: 과거 시점
s.add(lastMeasurement >= 1000)
s.add(lastMeasurement <= block_timestamp)

# totalLiquidityWeight: 유동성 가중치
s.add(totalLiquidityWeight_0 >= 1)
s.add(totalLiquidityWeight_0 <= 10**30)

# pastLiquidityEvaluation
s.add(pastLiquidityEvaluation >= 1)
s.add(pastLiquidityEvaluation <= 10**30)

# previousPrices[0]: VADER 가격 (보통 1e18 스케일)
s.add(previousPrices_0 >= 10**15)   # 최소 0.001 (1e18 스케일 기준)
s.add(previousPrices_0 <= 10**21)   # 최대 1000

# ── 풀기 ──
print("Solving...")
result = s.check()

if result == sat:
    m = s.model()
    print("\n=== Solution Found ===\n")

    # 변수 출력
    vars_info = [
        ("GlobalVar", [
            ("block.timestamp", block_timestamp),
        ]),
        ("StateVar", [
            ("previousPrices[0]", previousPrices_0),
            ("vaderPairs.length", vaderPairs_length),
            ("totalLiquidityWeight[0]", totalLiquidityWeight_0),
            ("twapData[1].lastMeasurement", lastMeasurement),
            ("twapData[1].updatePeriod", updatePeriod),
            ("twapData[1].pastLiquidityEvaluation", pastLiquidityEvaluation),
            ("twapData[1].nativeTokenPriceCumulative", nativeTokenPriceCumulative),
        ]),
    ]

    for var_type, vars_list in vars_info:
        print(f"[{var_type}]")
        for name, var in vars_list:
            val = m.evaluate(var)
            print(f"  {name} = {val}")
        print()

    # 중간 계산값 출력
    print("[Computed Values]")
    te = m.evaluate(timeElapsed)
    print(f"  timeElapsed = {te}")
    up = m.evaluate(updatePeriod)
    print(f"  timeElapsed >= updatePeriod? → {te.as_long() >= up.as_long() if hasattr(te, 'as_long') and hasattr(up, 'as_long') else 'check manually'}")
    print()

    # Debug annotation 출력 (복사-붙여넣기용)
    print("[Debug Annotations for contraction file]")
    bt = m.evaluate(block_timestamp)
    pp = m.evaluate(previousPrices_0)
    vl = m.evaluate(vaderPairs_length)
    tl = m.evaluate(totalLiquidityWeight_0)
    lm = m.evaluate(lastMeasurement)
    uper = m.evaluate(updatePeriod)
    ple = m.evaluate(pastLiquidityEvaluation)
    ntpc = m.evaluate(nativeTokenPriceCumulative)

    print(f"  // @GlobalVar block.timestamp = [{bt}, {bt}]")
    print(f"  // @StateVar previousPrices[0] = [{pp}, {pp}]")
    print(f"  // @StateVar vaderPairs.length = [{vl}, {vl}]")
    print(f"  // @StateVar totalLiquidityWeight[0] = [{tl}, {tl}]")
    print(f"  // @StateVar twapData[1].lastMeasurement = [{lm}, {lm}]")
    print(f"  // @StateVar twapData[1].updatePeriod = [{uper}, {uper}]")
    print(f"  // @StateVar twapData[1].pastLiquidityEvaluation = [{ple}, {ple}]")
    print(f"  // @StateVar twapData[1].nativeTokenPriceCumulative = [{ntpc}, {ntpc}]")
    print()

    # Intent annotation 결과 예측
    print("[Intent Annotation Prediction]")
    print(f"  // @Post Changed(previousPrices[0])")
    print(f"  → Buggy: previousPrices[0]에 write 없음 → Unchanged → alarm")
    print(f"  → Correct: previousPrices[0]에 새 가격 기록 → Changed → pass")

else:
    print(f"No solution: {result}")
    print("Unsat core (if available):")
    print(s.unsat_core())
