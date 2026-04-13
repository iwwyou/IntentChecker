"""
web3bugs_45_H_01 (UToken.borrow) debug annotation 값 생성기
Z3 solver를 이용해 모든 require를 통과하면서
calculatingInterest가 의미 있는 값을 반환하는 변수 조합을 생성한다.

생성 조건 (annotation_plans.md 참조):
C1: debtCeiling > totalBorrows
C2: amount >= minBorrow
C3: amount <= debtCeiling - totalBorrows
C4: accountBorrows[101].principal >= 1
C5: block.number > accrualBlockNumber
C6: overdueBlocks >= block.number - accountBorrows[101].lastRepay
C7: calculatingInterest 결과 >= 1
C8: borrowBalanceView + amount + fee <= maxBorrow
"""

from z3 import *

# ── 변수 선언 ──
# LocalVar
amount = Int('amount')

# StateVar
minBorrow = Int('minBorrow')
debtCeiling = Int('debtCeiling')
totalBorrows = Int('totalBorrows')
originationFee = Int('originationFee')
WAD = Int('WAD')
principal = Int('accountBorrows_101_principal')
accrualBlockNumber = Int('accrualBlockNumber')
borrowIndex = Int('borrowIndex')
interest = Int('accountBorrows_101_interest')
interestIndex = Int('accountBorrows_101_interestIndex')
lastRepay = Int('accountBorrows_101_lastRepay')
maxBorrow = Int('maxBorrow')
overdueBlocks = Int('overdueBlocks')

# GlobalVar
blockNumber = Int('block_number')

# ── 중간 계산식 ──
# fee = (originationFee * amount) / WAD
fee = (originationFee * amount) / WAD

# blockDelta = block.number - accrualBlockNumber
blockDelta = blockNumber - accrualBlockNumber

# simpleInterestFactor = borrowRate * blockDelta
# borrowRate = 0.0005e16 = 5000000000000 (borrowRatePerBlock 상수 가정)
borrowRate = IntVal(5000000000000)  # 0.0005e16
simpleInterestFactor = borrowRate * blockDelta

# borrowIndexNew = (simpleInterestFactor * borrowIndex) / WAD + borrowIndex
borrowIndexNew = (simpleInterestFactor * borrowIndex) / WAD + borrowIndex

# principalTimesIndex = (principal + interest) * borrowIndexNew
principalTimesIndex = (principal + interest) * borrowIndexNew

# balance = principalTimesIndex / interestIndex
balance = principalTimesIndex / interestIndex

# calculatingInterest = balance - principal
calcInterest = balance - principal

# borrowBalanceView = principal + calculatingInterest
borrowBalanceView = principal + calcInterest

# ── Solver ──
s = Solver()

# 기본 양수/합리적 범위 제약
s.add(amount > 0)
s.add(minBorrow > 0)
s.add(debtCeiling > 0)
s.add(totalBorrows >= 0)
s.add(originationFee > 0)
s.add(WAD == 1000000000000000000)  # 1e18
s.add(principal > 0)
s.add(interest >= 0)
s.add(interestIndex > 0)
s.add(borrowIndex > 0)
s.add(accrualBlockNumber > 0)
s.add(blockNumber > 0)
s.add(lastRepay > 0)
s.add(maxBorrow > 0)
s.add(overdueBlocks > 0)

# ── 생성 조건 (C1~C8) ──

# C1: debtCeiling > totalBorrows
s.add(debtCeiling > totalBorrows)

# C2: amount >= minBorrow
s.add(amount >= minBorrow)

# C3: amount <= debtCeiling - totalBorrows
s.add(amount <= debtCeiling - totalBorrows)

# C4: accountBorrows[101].principal >= 1
s.add(principal >= 1)

# C5: block.number > accrualBlockNumber
s.add(blockNumber > accrualBlockNumber)

# C6: overdueBlocks >= block.number - lastRepay (checkIsOverdue 통과)
s.add(overdueBlocks >= blockNumber - lastRepay)

# C7: calculatingInterest 결과 >= 1 (의미 있는 이자)
s.add(calcInterest >= 1)

# C8: borrowBalanceView + amount + fee <= maxBorrow
s.add(borrowBalanceView + amount + fee <= maxBorrow)

# C9: fee >= 1 (fee가 의미 있는 값)
s.add(fee >= 1)

# ── 값 범위 힌트 (현실적인 값 유도) ──
# fee >= 1 이려면 originationFee * amount >= WAD 이어야 함
# → amount를 WAD 스케일로 허용 (e.g. 1e18 = 1 token in wei)
s.add(amount >= WAD)  # 최소 1 token (wei 단위)
s.add(amount <= 1000 * WAD)  # 최대 1000 tokens
s.add(minBorrow >= 1)
s.add(minBorrow <= WAD)
s.add(principal >= WAD)  # principal도 token 단위
s.add(principal <= 100 * WAD)
s.add(interest >= 0)
s.add(interest <= 10 * WAD)
s.add(borrowIndex >= WAD)  # borrowIndex는 보통 1e18 이상
s.add(borrowIndex <= 2 * WAD)
s.add(interestIndex >= WAD)
s.add(interestIndex <= 2 * WAD)
s.add(originationFee >= WAD / 1000)  # 최소 0.1%
s.add(originationFee <= WAD / 10)    # 최대 10%
s.add(blockNumber <= 1000)
s.add(accrualBlockNumber <= 1000)
s.add(maxBorrow <= 10000 * WAD)
s.add(debtCeiling <= 10000 * WAD)

# ── 풀기 ──
print("Solving...")
result = s.check()

if result == sat:
    m = s.model()
    print("\n=== Solution Found ===\n")

    # 변수 출력
    vars_info = [
        ("LocalVar", [
            ("amount", amount),
        ]),
        ("StateVar", [
            ("minBorrow", minBorrow),
            ("debtCeiling", debtCeiling),
            ("totalBorrows", totalBorrows),
            ("originationFee", originationFee),
            ("WAD", WAD),
            ("accountBorrows[101].principal", principal),
            ("accrualBlockNumber", accrualBlockNumber),
            ("borrowIndex", borrowIndex),
            ("accountBorrows[101].interest", interest),
            ("accountBorrows[101].interestIndex", interestIndex),
            ("accountBorrows[101].lastRepay", lastRepay),
            ("maxBorrow", maxBorrow),
            ("overdueBlocks", overdueBlocks),
        ]),
        ("GlobalVar", [
            ("block.number", blockNumber),
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
    print(f"  fee = {m.evaluate(fee)}")
    print(f"  blockDelta = {m.evaluate(blockDelta)}")
    print(f"  simpleInterestFactor = {m.evaluate(simpleInterestFactor)}")
    print(f"  borrowIndexNew = {m.evaluate(borrowIndexNew)}")
    print(f"  calculatingInterest = {m.evaluate(calcInterest)}")
    print(f"  borrowBalanceView = {m.evaluate(borrowBalanceView)}")
    print()

    # intent annotation 방향 확인
    bi_val = m.evaluate(borrowIndex)
    bi_new_val = m.evaluate(borrowIndexNew)
    print("[Intent Annotation Direction]")
    print(f"  borrowIndex (Before) = {bi_val}")
    print(f"  borrowIndexNew (After, if accrueInterest called) = {bi_new_val}")
    print(f"  Before < After? → {bi_val.as_long() < bi_new_val.as_long() if hasattr(bi_val, 'as_long') and hasattr(bi_new_val, 'as_long') else 'check manually'}")
    print(f"  → @During borrowIndex(Before < After) expected: violated (accrueInterest not called yet)")

else:
    print(f"No solution: {result}")
    print("Unsat core (if available):")
    print(s.unsat_core())
