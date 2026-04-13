"""
RQ1: Algorithm Soundness — Interval Comparison Brute-Force Verification

11개 구간 배치 유형(topology) × 5개 크기 변형(width profile) × 8개 연산자
= 440 조합에 대해 brute-force 전수 열거와 함수 출력의 일치를 검증한다.

Width profiles:
  S (Small)   : 양쪽 폭 1~3
  M (Medium)  : 양쪽 폭 5~10
  L (Large)   : 양쪽 폭 20~50
  A-L (Asym-L): L이 훨씬 넓음
  A-R (Asym-R): R이 훨씬 넓음

Usage:
    python algorithm_soundness.py              # 전체 실행
    python algorithm_soundness.py --csv        # CSV 결과 출력
    python algorithm_soundness.py --summary    # 요약만 출력
"""

import sys, os, csv, argparse
import operator as op_module
from pathlib import Path

# 프로젝트 루트를 path에 추가
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from Domain.Interval import Interval
from Analyzer.GuardianVerificationEngine import GuardianVerificationEngine


# ── Mock & Engine ─────────────────────────────────────────────
class _MockAnalyzer:
    pass

_engine = GuardianVerificationEngine(_MockAnalyzer())


# ── 헬퍼 ─────────────────────────────────────────────────────
def iv(lo, hi):
    return Interval(min_value=lo, max_value=hi)


# ── 연산자 ────────────────────────────────────────────────────
OPERATORS = ['>', '>=', '<', '<=', '==', '!=', 'in', 'not in']

OP_FUNC = {
    '>':  op_module.gt,
    '>=': op_module.ge,
    '<':  op_module.lt,
    '<=': op_module.le,
    '==': op_module.eq,
    '!=': op_module.ne,
    'in':     lambda l, r: r[0] <= l <= r[1],
    'not in': lambda l, r: not (r[0] <= l <= r[1]),
}


# ── 11 topology × 5 width profile 케이스 생성 ────────────────
# 각 topology에 대해 제약 조건을 만족하는 5가지 크기 조합을 정의한다.
# 일부 topology는 특정 크기 조합이 불가능하면 대체 케이스를 사용한다.

CASES = []

def _add(topo_id, topo_name, width_id, width_desc, L, R):
    """케이스를 CASES 리스트에 추가"""
    CASES.append({
        "topo_id": topo_id,
        "topo_name": topo_name,
        "width_id": width_id,
        "width_desc": width_desc,
        "L": L,
        "R": R,
    })


# ── 1-1 분리(L왼쪽): L_max < R_min ──
_add("1-1", "분리(L왼쪽)", "S", "small",   (5,7),    (10,12))
_add("1-1", "분리(L왼쪽)", "M", "medium",  (0,8),    (12,20))
_add("1-1", "분리(L왼쪽)", "L", "large",   (0,30),   (35,80))
_add("1-1", "분리(L왼쪽)", "AL","asym-L",  (0,40),   (45,47))
_add("1-1", "분리(L왼쪽)", "AR","asym-R",  (5,7),    (12,55))

# ── 1-2 분리(R왼쪽): R_max < L_min ──
_add("1-2", "분리(R왼쪽)", "S", "small",   (10,12),  (5,7))
_add("1-2", "분리(R왼쪽)", "M", "medium",  (12,20),  (0,8))
_add("1-2", "분리(R왼쪽)", "L", "large",   (35,80),  (0,30))
_add("1-2", "분리(R왼쪽)", "AL","asym-L",  (45,85),  (10,12))
_add("1-2", "분리(R왼쪽)", "AR","asym-R",  (50,52),  (0,40))

# ── 2-1 부분겹침(L왼쪽): L_min < R_min <= L_max < R_max ──
_add("2-1", "부분겹침(L왼쪽)", "S", "small",   (3,5),    (4,7))
_add("2-1", "부분겹침(L왼쪽)", "M", "medium",  (0,8),    (5,15))
_add("2-1", "부분겹침(L왼쪽)", "L", "large",   (0,30),   (20,60))
_add("2-1", "부분겹침(L왼쪽)", "AL","asym-L",  (0,40),   (35,42))
_add("2-1", "부분겹침(L왼쪽)", "AR","asym-R",  (10,13),  (12,55))

# ── 2-2 부분겹침(R왼쪽): R_min < L_min <= R_max < L_max ──
_add("2-2", "부분겹침(R왼쪽)", "S", "small",   (4,7),    (3,5))
_add("2-2", "부분겹침(R왼쪽)", "M", "medium",  (5,15),   (0,8))
_add("2-2", "부분겹침(R왼쪽)", "L", "large",   (20,60),  (0,30))
_add("2-2", "부분겹침(R왼쪽)", "AL","asym-L",  (5,50),   (3,8))
_add("2-2", "부분겹침(R왼쪽)", "AR","asym-R",  (30,35),  (0,32))

# ── 3-1 L엄격포함R: L_min < R_min and R_max < L_max ──
_add("3-1", "L엄격포함R", "S", "small",   (2,6),    (3,5))
_add("3-1", "L엄격포함R", "M", "medium",  (0,12),   (3,9))
_add("3-1", "L엄격포함R", "L", "large",   (0,60),   (10,50))
_add("3-1", "L엄격포함R", "AL","asym-L",  (0,50),   (24,26))
_add("3-1", "L엄격포함R", "AR","asym-R",  (5,15),   (6,14))

# ── 3-2 R엄격포함L: R_min < L_min and L_max < R_max ──
_add("3-2", "R엄격포함L", "S", "small",   (3,5),    (2,6))
_add("3-2", "R엄격포함L", "M", "medium",  (3,9),    (0,12))
_add("3-2", "R엄격포함L", "L", "large",   (10,50),  (0,60))
_add("3-2", "R엄격포함L", "AL","asym-L",  (20,30),  (19,31))
_add("3-2", "R엄격포함L", "AR","asym-R",  (24,26),  (0,50))

# ── 4-1 왼쪽공유,L넓음: L_min = R_min, L_max > R_max ──
_add("4-1", "왼쪽공유,L넓음", "S", "small",   (3,6),    (3,4))
_add("4-1", "왼쪽공유,L넓음", "M", "medium",  (3,12),   (3,7))
_add("4-1", "왼쪽공유,L넓음", "L", "large",   (0,50),   (0,20))
_add("4-1", "왼쪽공유,L넓음", "AL","asym-L",  (0,50),   (0,2))
_add("4-1", "왼쪽공유,L넓음", "AR","asym-R",  (5,12),   (5,10))

# ── 4-2 왼쪽공유,R넓음: L_min = R_min, R_max > L_max ──
_add("4-2", "왼쪽공유,R넓음", "S", "small",   (3,4),    (3,6))
_add("4-2", "왼쪽공유,R넓음", "M", "medium",  (3,7),    (3,12))
_add("4-2", "왼쪽공유,R넓음", "L", "large",   (0,20),   (0,50))
_add("4-2", "왼쪽공유,R넓음", "AL","asym-L",  (5,10),   (5,12))
_add("4-2", "왼쪽공유,R넓음", "AR","asym-R",  (0,2),    (0,50))

# ── 5-1 오른쪽공유,L넓음: L_max = R_max, L_min < R_min ──
_add("5-1", "오른쪽공유,L넓음", "S", "small",   (2,6),    (4,6))
_add("5-1", "오른쪽공유,L넓음", "M", "medium",  (0,10),   (5,10))
_add("5-1", "오른쪽공유,L넓음", "L", "large",   (0,50),   (20,50))
_add("5-1", "오른쪽공유,L넓음", "AL","asym-L",  (0,50),   (48,50))
_add("5-1", "오른쪽공유,L넓음", "AR","asym-R",  (8,12),   (10,12))

# ── 5-2 오른쪽공유,R넓음: L_max = R_max, R_min < L_min ──
_add("5-2", "오른쪽공유,R넓음", "S", "small",   (4,6),    (2,6))
_add("5-2", "오른쪽공유,R넓음", "M", "medium",  (5,10),   (0,10))
_add("5-2", "오른쪽공유,R넓음", "L", "large",   (20,50),  (0,50))
_add("5-2", "오른쪽공유,R넓음", "AL","asym-L",  (40,50),  (38,50))
_add("5-2", "오른쪽공유,R넓음", "AR","asym-R",  (48,50),  (0,50))

# ── 6 완전동일: L = R ──
_add("6",   "완전동일", "S", "small",   (5,7),    (5,7))
_add("6",   "완전동일", "M", "medium",  (3,12),   (3,12))
_add("6",   "완전동일", "L", "large",   (0,50),   (0,50))
_add("6",   "완전동일", "P1","point",   (10,10),  (10,10))
_add("6",   "완전동일", "P2","point-2", (0,0),    (0,0))


# ── Brute-force 계산 ─────────────────────────────────────────
def brute_force_prob(L, R, op_str):
    """L의 모든 정수 × R의 모든 정수에 대해 op_str 적용 → true 비율"""
    l_vals = list(range(L[0], L[1] + 1))
    r_vals = list(range(R[0], R[1] + 1))

    fn = OP_FUNC[op_str]

    if op_str in ('in', 'not in'):
        total = len(l_vals)
        if total == 0:
            return 0.5
        true_count = sum(1 for lv in l_vals if fn(lv, (R[0], R[1])))
    else:
        total = len(l_vals) * len(r_vals)
        if total == 0:
            return 0.5
        true_count = sum(1 for lv in l_vals for rv in r_vals if fn(lv, rv))

    return true_count / total


# ── 테스트 실행 ───────────────────────────────────────────────
def run_tests(summary_only=False):
    total_tests = 0
    passed = 0
    failed = 0
    fail_details = []
    all_rows = []

    if not summary_only:
        hdr = f"{'Topo':<6} {'Width':<6} {'Op':<8} {'L':<14} {'R':<14} {'BF':>7} {'Func':>7} {'State':>10} {'Result':>6}"
        print("=" * len(hdr))
        print(hdr)
        print("=" * len(hdr))

    prev_topo = None
    for case in CASES:
        topo_id = case["topo_id"]
        L = case["L"]
        R = case["R"]

        if not summary_only and prev_topo and prev_topo != topo_id:
            print("-" * len(hdr))
        prev_topo = topo_id

        for op_str in OPERATORS:
            total_tests += 1

            # brute-force
            bf_prob = brute_force_prob(L, R, op_str)

            # 함수 호출
            left_iv = iv(L[0], L[1])
            right_iv = iv(R[0], R[1])
            result = _engine._compare_intervals_prob(left_iv, right_iv, op_str)
            fn_prob = result["prob_true"]
            state = result["state"]
            risk_score = result.get("risk_score", None)

            # 비교
            bf_rounded = round(bf_prob, 3)
            match = abs(bf_rounded - fn_prob) < 0.001

            status = "PASS" if match else "FAIL"
            if match:
                passed += 1
            else:
                failed += 1
                fail_details.append(case | {"op": op_str, "bf": bf_rounded,
                                            "fn": fn_prob, "state": state})

            # 결과 행 저장
            all_rows.append({
                "topo_id": topo_id,
                "topo_name": case["topo_name"],
                "width_id": case["width_id"],
                "width_desc": case["width_desc"],
                "L": f"[{L[0]},{L[1]}]",
                "R": f"[{R[0]},{R[1]}]",
                "op": op_str,
                "bf_prob": bf_rounded,
                "fn_prob": fn_prob,
                "state": state,
                "risk_score": risk_score,
                "match": status,
            })

            if not summary_only:
                L_str = f"[{L[0]},{L[1]}]"
                R_str = f"[{R[0]},{R[1]}]"
                print(f"{topo_id:<6} {case['width_id']:<6} {op_str:<8} "
                      f"{L_str:<14} {R_str:<14} {bf_rounded:>7.3f} {fn_prob:>7.3f} "
                      f"{state:>10} {status:>6}")

    # ── 요약 ──
    print()
    print("=" * 70)
    print(f"  Total: {total_tests}  |  PASS: {passed}  |  FAIL: {failed}  |  "
          f"Pass Rate: {passed/total_tests*100:.1f}%")
    print("=" * 70)

    # Topology별 요약
    topo_stats = {}
    for row in all_rows:
        tid = row["topo_id"]
        if tid not in topo_stats:
            topo_stats[tid] = {"name": row["topo_name"], "total": 0, "pass": 0, "fail": 0}
        topo_stats[tid]["total"] += 1
        if row["match"] == "PASS":
            topo_stats[tid]["pass"] += 1
        else:
            topo_stats[tid]["fail"] += 1

    print(f"\n{'Topo':<6} {'Name':<22} {'Total':>6} {'Pass':>6} {'Fail':>6}")
    print("-" * 52)
    for tid, s in topo_stats.items():
        print(f"{tid:<6} {s['name']:<22} {s['total']:>6} {s['pass']:>6} {s['fail']:>6}")

    # FAIL 상세
    if fail_details:
        print("\n>>> FAIL DETAILS <<<\n")
        for d in fail_details:
            L, R = d["L"], d["R"]
            print(f"  [{d['topo_id']} {d['width_id']}] L=[{L[0]},{L[1]}], R=[{R[0]},{R[1]}], op='{d['op']}'")
            print(f"    brute-force: {d['bf']:.3f}  vs  func: {d['fn']:.3f}  (state={d['state']})")

    return all_rows, {"total": total_tests, "passed": passed, "failed": failed}


# ── CSV 출력 ──────────────────────────────────────────────────
def export_csv(rows, filepath):
    """결과를 CSV로 저장"""
    fieldnames = ["topo_id", "topo_name", "width_id", "width_desc",
                  "L", "R", "op", "bf_prob", "fn_prob", "state",
                  "risk_score", "match"]

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nCSV exported: {filepath}")


# ── main ──────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="RQ1: Algorithm Soundness Test")
    parser.add_argument("--csv", action="store_true", help="Export results to CSV")
    parser.add_argument("--summary", action="store_true", help="Print summary only")
    args = parser.parse_args()

    rows, stats = run_tests(summary_only=args.summary)

    if args.csv:
        results_dir = Path(__file__).parent / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        export_csv(rows, results_dir / "algorithm_soundness.csv")


if __name__ == "__main__":
    main()
