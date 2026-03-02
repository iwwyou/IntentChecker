"""
_compare_intervals_prob 브루트포스 검증 스크립트

8개 연산자 × 11개 구간 케이스 = 88 조합에 대해
  - brute-force (L×R 전수 열거)로 기대 prob_true 계산
  - 함수의 반환 prob_true와 비교
  - 불일치 시 상세 출력
"""

import sys, os, operator as op_module

# 프로젝트 루트를 path 에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from Domain.Interval import Interval


# ── GuardianVerificationEngine mock ──────────────────────────────
# _compare_intervals_prob 은 self._compute_risk_type, self._compute_risk_score,
# self._false_regions_for_op 만 사용하므로 최소한으로 mock
class _MockAnalyzer:
    pass


from Analyzer.GuardianVerificationEngine import GuardianVerificationEngine

_engine = GuardianVerificationEngine(_MockAnalyzer())


# ── 헬퍼: Interval 생성 ─────────────────────────────────────────
def iv(lo, hi):
    return Interval(min_value=lo, max_value=hi)


# ── 연산자 목록 ─────────────────────────────────────────────────
OPERATORS = ['>', '>=', '<', '<=', '==', '!=', 'in', 'not in']

OP_FUNC = {
    '>':  op_module.gt,
    '>=': op_module.ge,
    '<':  op_module.lt,
    '<=': op_module.le,
    '==': op_module.eq,
    '!=': op_module.ne,
    'in':      lambda l, r: r[0] <= l <= r[1],   # R 범위에 포함 여부
    'not in':  lambda l, r: not (r[0] <= l <= r[1]),
}


# ── 11개 구간 케이스 ────────────────────────────────────────────
# (이름, L, R)
# 1류: 공유값 없음 (6개)
# 2류: 한쪽 공유 (4개)
# 3류: 양쪽 공유 (1개)
CASES = [
    # ── 1류: 공유값 없음 ──
    ("1-1 분리(L왼쪽)",      (0, 10),  (11, 15)),
    ("1-2 분리(R왼쪽)",      (8, 15),  (0, 5)),
    ("2-1 부분겹침(L왼쪽)",  (0, 6),   (4, 10)),
    ("2-2 부분겹침(R왼쪽)",  (5, 10),  (3, 7)),
    ("3-1 L엄격포함R",       (0, 12),  (4, 9)),
    ("3-2 R엄격포함L",       (5, 7),   (0, 12)),

    # ── 2류: 한쪽 공유 ──
    ("4-1 왼쪽공유,L넓음",   (3, 10),  (3, 7)),
    ("4-2 왼쪽공유,R넓음",   (3, 7),   (3, 10)),
    ("5-1 오른쪽공유,L넓음", (0, 10),  (3, 10)),
    ("5-2 오른쪽공유,R넓음", (3, 10),  (0, 10)),

    # ── 3류: 양쪽 공유 ──
    ("6   완전동일",         (7, 9),   (7, 9)),
]


def brute_force_prob(L, R, op_str):
    """
    L의 모든 정수 × R의 모든 정수 (균등분포)에 대해
    op_str 연산 적용 → true 비율 반환
    """
    l_vals = list(range(L[0], L[1] + 1))
    r_vals = list(range(R[0], R[1] + 1))
    total = len(l_vals) * len(r_vals)
    if total == 0:
        return 0.5

    fn = OP_FUNC[op_str]

    if op_str in ('in', 'not in'):
        # in/not in: R은 "범위"로 취급 — L 값이 R 범위 안에 있는지
        # R의 각 값에 대해 반복하지 않음 (R은 범위 자체)
        true_count = sum(1 for lv in l_vals if fn(lv, (R[0], R[1])))
        total = len(l_vals)
    else:
        true_count = sum(1 for lv in l_vals for rv in r_vals if fn(lv, rv))

    return true_count / total


def run_tests():
    total_tests = 0
    passed = 0
    failed = 0
    fail_details = []

    print("=" * 90)
    print(f"{'케이스':<22} {'연산자':<8} {'BF prob':>8} {'함수 prob':>9} {'상태':>10} {'결과':>6}")
    print("=" * 90)

    for case_name, L, R in CASES:
        for op_str in OPERATORS:
            total_tests += 1

            # 1) brute-force
            bf_prob = brute_force_prob(L, R, op_str)

            # 2) 함수 호출
            left_iv = iv(L[0], L[1])
            right_iv = iv(R[0], R[1])
            result = _engine._compare_intervals_prob(left_iv, right_iv, op_str)
            fn_prob = result["prob_true"]
            state = result["state"]

            # 3) 비교 (소수점 3자리까지)
            bf_rounded = round(bf_prob, 3)
            match = abs(bf_rounded - fn_prob) < 0.001

            status = "PASS" if match else "FAIL"
            if match:
                passed += 1
            else:
                failed += 1
                fail_details.append((case_name, op_str, L, R, bf_rounded, fn_prob, state))

            print(f"{case_name:<22} {op_str:<8} {bf_rounded:>8.3f} {fn_prob:>9.3f} {state:>10} {status:>6}")

        print("-" * 90)

    # ── 요약 ──
    print()
    print("=" * 90)
    print(f"총 {total_tests} 테스트  |  PASS: {passed}  |  FAIL: {failed}")
    print("=" * 90)

    if fail_details:
        print()
        print(">>> FAIL 상세 <<<")
        print()
        for case_name, op_str, L, R, bf, fn, state in fail_details:
            print(f"  [{case_name}]  L={list(L)}, R={list(R)}, op='{op_str}'")
            print(f"    brute-force: {bf:.3f}  vs  함수: {fn:.3f}  (state={state})")

            # 상세 열거
            l_vals = list(range(L[0], L[1] + 1))
            r_vals = list(range(R[0], R[1] + 1))
            fn_op = OP_FUNC[op_str]

            if op_str in ('in', 'not in'):
                true_vals = [lv for lv in l_vals if fn_op(lv, (R[0], R[1]))]
                false_vals = [lv for lv in l_vals if not fn_op(lv, (R[0], R[1]))]
                print(f"    L 정수: {l_vals}")
                print(f"    R 범위: [{R[0]},{R[1]}]")
                print(f"    true인 L값: {true_vals}  ({len(true_vals)}/{len(l_vals)})")
                print(f"    false인 L값: {false_vals}  ({len(false_vals)}/{len(l_vals)})")
            else:
                true_pairs = [(lv, rv) for lv in l_vals for rv in r_vals if fn_op(lv, rv)]
                total_pairs = len(l_vals) * len(r_vals)
                print(f"    L 정수: {l_vals}")
                print(f"    R 정수: {r_vals}")
                print(f"    true 쌍 수: {len(true_pairs)} / {total_pairs}")
                if len(true_pairs) <= 30:
                    print(f"    true 쌍: {true_pairs}")
            print()


if __name__ == "__main__":
    run_tests()
