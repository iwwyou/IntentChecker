"""
RQ1 Evaluation Runner

카테고리별 테스트 케이스를 실행하고 결과를 수집합니다.

Usage:
    python runner.py                      # 모든 케이스 실행
    python runner.py --category operator_order_issue  # 특정 카테고리만
    python runner.py --case BoostToken    # 특정 케이스만
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from Analyzer.ContractAnalyzer import ContractAnalyzer
from Analyzer.DebugUnitAnalyzer import DebugBatchManager
from Analyzer.EnhancedSolidityVisitor import EnhancedSolidityVisitor
from Utils.Helper import ParserHelpers


class RQ1Runner:
    def __init__(self, cases_dir: Path, results_dir: Path):
        self.cases_dir = cases_dir
        self.results_dir = results_dir
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def discover_cases(self, category: str = None, case_id: str = None) -> list[dict]:
        """테스트 케이스 탐색"""
        cases = []

        for category_dir in self.cases_dir.iterdir():
            if not category_dir.is_dir():
                continue
            if category and category_dir.name != category:
                continue

            for case_file in category_dir.glob("*.json"):
                if case_id and case_file.stem != case_id:
                    continue

                with open(case_file, 'r', encoding='utf-8') as f:
                    case_data = json.load(f)
                    case_data['_category'] = category_dir.name
                    case_data['_file'] = str(case_file)
                    cases.append(case_data)

        return cases

    def run_case(self, case: dict) -> dict:
        """단일 테스트 케이스 실행"""
        print(f"\n{'='*60}")
        print(f"Running: {case['name']}")
        print(f"Category: {case['_category']}")
        print(f"{'='*60}")

        start_time = time.time()
        result = {
            "id": case["id"],
            "name": case["name"],
            "category": case["_category"],
            "source": case.get("source", ""),
            "target_contract": case.get("target_contract", ""),
            "target_function": case.get("target_function", ""),
            "bug_lines": case.get("bug_lines", []),
            "status": "pending",
            "violations": [],
            "warnings": [],
            "satisfied": [],
            "errors": [],
            "execution_time": 0,
            "metrics": {}
        }

        try:
            # 1. ContractAnalyzer 초기화
            analyzer = ContractAnalyzer()
            snapman = analyzer.snapman
            batch_mgr = DebugBatchManager(analyzer, snapman)

            # 2. 소스 코드 로드
            source_path = PROJECT_ROOT / case["source"]
            with open(source_path, 'r', encoding='utf-8') as f:
                records = json.load(f)

            print(f"Loaded {len(records)} code records")

            # 3. Phase 1: 코드 파싱
            for rec in records:
                code, s, e, ev = rec["code"], rec["startLine"], rec["endLine"], rec["event"]
                analyzer.update_code(s, e, code, ev)

                stripped = code.strip()
                if stripped and not stripped.startswith("// @"):
                    ctx = analyzer.get_current_context_type()
                    try:
                        tree = ParserHelpers.generate_parse_tree(code, ctx, False)
                        EnhancedSolidityVisitor(analyzer).visit(tree)
                    except:
                        pass

            # 4. Phase 2: Intent annotations 추가 (CFG 노드에 저장)
            for intent in case.get("intent_annotations", []):
                line_no = intent["line"]
                expr = intent["expr"]
                intent_type = intent.get("type", "During")

                annotation = f"// @{intent_type} {expr}"
                print(f"Adding intent at line {line_no}: {annotation}")

                try:
                    analyzer.add_intent_annotation(line_no, annotation)
                except Exception as e:
                    result["errors"].append(f"Intent annotation error at line {line_no}: {e}")

            # 5. Phase 3: Debug annotations 추가 및 실행
            batch_mgr.reset()

            # Debugging BEGIN
            debug_line = case.get("debug_annotations", [{}])[0].get("line", 140)
            analyzer.update_code(debug_line, debug_line, "// @Debugging BEGIN", "add")

            for debug in case.get("debug_annotations", []):
                var = debug["var"]
                value = debug["value"]
                line = debug.get("line", debug_line)

                if isinstance(value, list) and len(value) == 2:
                    value_str = f"[{value[0]}, {value[1]}]"
                else:
                    value_str = str(value)

                annotation = f"// @LocalVar {var} = {value_str}"
                print(f"Adding debug: {annotation}")
                batch_mgr.add_line(annotation, line, line)

            # 6. flush로 실행 - 결과 캡처
            import io
            from contextlib import redirect_stdout

            output_buffer = io.StringIO()
            with redirect_stdout(output_buffer):
                batch_mgr.flush()

            output = output_buffer.getvalue()

            # 7. 결과 파싱
            for line in output.split('\n'):
                if '[INTENT VIOLATION]' in line:
                    result["violations"].append(line.strip())
                elif '[INTENT SUCCESS]' in line or '[INTENT SATISFIED]' in line:
                    result["satisfied"].append(line.strip())
                elif '[INTENT ERROR]' in line:
                    result["errors"].append(line.strip())
                elif '[INTENT WARNING]' in line:
                    result["warnings"].append(line.strip())

            # 8. 메트릭 계산
            total_intents = case.get("expected_results", {}).get("total_intents",
                len(case.get("intent_annotations", [])))

            num_violations = len(result["violations"])
            num_warnings = len(result["warnings"])
            num_satisfied = len(result["satisfied"])
            num_errors = len(result["errors"])

            # 버그 탐지 관련 (violation + warning)
            num_bug_detected = num_violations + num_warnings

            result["metrics"] = {
                "total_intents": total_intents,
                "num_violations": num_violations,
                "num_warnings": num_warnings,
                "num_satisfied": num_satisfied,
                "num_errors": num_errors,
                "num_bug_detected": num_bug_detected,
                "violation_rate": round(num_violations / total_intents * 100, 1) if total_intents else 0,
                "warning_rate": round(num_warnings / total_intents * 100, 1) if total_intents else 0,
                "satisfied_rate": round(num_satisfied / total_intents * 100, 1) if total_intents else 0,
                "bug_detection_rate": round(num_bug_detected / total_intents * 100, 1) if total_intents else 0,
            }

            # 9. 결과 평가
            expected = case.get("expected_results", {})
            expected_violations = expected.get("expected_violations", 0)

            if num_bug_detected == expected_violations:
                result["status"] = "pass"
            elif num_bug_detected > 0:
                result["status"] = "partial"
            else:
                result["status"] = "fail"

            result["actual_violations"] = num_bug_detected
            result["expected_violations"] = expected_violations

        except Exception as e:
            result["status"] = "error"
            result["errors"].append(str(e))
            import traceback
            result["traceback"] = traceback.format_exc()

        result["execution_time"] = round(time.time() - start_time, 3)

        # 결과 출력
        metrics = result["metrics"]
        print(f"\nResult: {result['status'].upper()}")
        print(f"Time: {result['execution_time']}s")
        print(f"Intents: {metrics['total_intents']} total")
        print(f"  - Violations: {metrics['num_violations']} ({metrics['violation_rate']}%)")
        print(f"  - Warnings:   {metrics['num_warnings']} ({metrics['warning_rate']}%)")
        print(f"  - Satisfied:  {metrics['num_satisfied']} ({metrics['satisfied_rate']}%)")
        print(f"Bug Detection: {metrics['num_bug_detected']} (expected: {result['expected_violations']})")

        if result["violations"]:
            print("Violations:")
            for v in result["violations"]:
                print(f"  - {v}")
        if result["warnings"]:
            print("Warnings:")
            for w in result["warnings"]:
                print(f"  - {w}")
        if result["errors"]:
            print(f"Errors: {result['errors']}")

        return result

    def run_all(self, category: str = None, case_id: str = None) -> dict:
        """모든 (또는 필터된) 테스트 케이스 실행"""
        cases = self.discover_cases(category, case_id)

        if not cases:
            print("No test cases found!")
            return {"cases": [], "summary": {}}

        print(f"Found {len(cases)} test case(s)")

        results = []
        for case in cases:
            result = self.run_case(case)
            results.append(result)

            # 개별 결과 저장
            result_file = self.results_dir / f"{case['id']}.json"
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

        # 전체 요약
        summary = self._generate_summary(results)

        # 요약 저장
        summary_file = self.results_dir / "summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "cases": results,
                "summary": summary
            }, f, indent=2, ensure_ascii=False)

        self._print_summary(summary)

        return {"cases": results, "summary": summary}

    def _generate_summary(self, results: list[dict]) -> dict:
        """결과 요약 생성"""
        total = len(results)
        passed = sum(1 for r in results if r["status"] == "pass")
        partial = sum(1 for r in results if r["status"] == "partial")
        failed = sum(1 for r in results if r["status"] == "fail")
        errors = sum(1 for r in results if r["status"] == "error")

        # Intent 결과 집계
        total_intents = sum(r.get("metrics", {}).get("total_intents", 0) for r in results)
        total_violations = sum(r.get("metrics", {}).get("num_violations", 0) for r in results)
        total_warnings = sum(r.get("metrics", {}).get("num_warnings", 0) for r in results)
        total_satisfied = sum(r.get("metrics", {}).get("num_satisfied", 0) for r in results)
        total_errors = sum(r.get("metrics", {}).get("num_errors", 0) for r in results)
        total_bug_detected = total_violations + total_warnings

        # 시간 집계
        execution_times = [r.get("execution_time", 0) for r in results]
        total_time = sum(execution_times)
        avg_time = total_time / total if total else 0
        min_time = min(execution_times) if execution_times else 0
        max_time = max(execution_times) if execution_times else 0

        # 카테고리별 통계
        category_stats = {}
        for r in results:
            cat = r.get("category", "unknown")
            if cat not in category_stats:
                category_stats[cat] = {
                    "total": 0, "pass": 0, "partial": 0, "fail": 0, "error": 0,
                    "violations": 0, "warnings": 0, "satisfied": 0,
                    "execution_time": 0
                }
            category_stats[cat]["total"] += 1
            status = r["status"]
            if status in category_stats[cat]:
                category_stats[cat][status] += 1
            category_stats[cat]["violations"] += r.get("metrics", {}).get("num_violations", 0)
            category_stats[cat]["warnings"] += r.get("metrics", {}).get("num_warnings", 0)
            category_stats[cat]["satisfied"] += r.get("metrics", {}).get("num_satisfied", 0)
            category_stats[cat]["execution_time"] += r.get("execution_time", 0)

        # 카테고리별 pass_rate 계산
        for cat, stats in category_stats.items():
            stats["pass_rate"] = round(stats["pass"] / stats["total"] * 100, 1) if stats["total"] else 0
            stats["execution_time"] = round(stats["execution_time"], 3)

        return {
            # 케이스 결과
            "total_cases": total,
            "passed": passed,
            "partial": partial,
            "failed": failed,
            "errors": errors,
            "pass_rate": round(passed / total * 100, 1) if total else 0,

            # Intent 결과
            "intent_stats": {
                "total_intents": total_intents,
                "violations": total_violations,
                "warnings": total_warnings,
                "satisfied": total_satisfied,
                "errors": total_errors,
                "bug_detected": total_bug_detected,
                "violation_rate": round(total_violations / total_intents * 100, 1) if total_intents else 0,
                "warning_rate": round(total_warnings / total_intents * 100, 1) if total_intents else 0,
                "satisfied_rate": round(total_satisfied / total_intents * 100, 1) if total_intents else 0,
                "bug_detection_rate": round(total_bug_detected / total_intents * 100, 1) if total_intents else 0,
            },

            # 시간 통계
            "time_stats": {
                "total_time": round(total_time, 3),
                "avg_time": round(avg_time, 3),
                "min_time": round(min_time, 3),
                "max_time": round(max_time, 3),
            },

            # 카테고리별 통계
            "category_stats": category_stats
        }

    def _print_summary(self, summary: dict):
        """요약 출력"""
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")

        # 케이스 결과
        print("\n[Test Cases]")
        print(f"  Total:    {summary['total_cases']}")
        print(f"  Passed:   {summary['passed']}")
        print(f"  Partial:  {summary['partial']}")
        print(f"  Failed:   {summary['failed']}")
        print(f"  Errors:   {summary['errors']}")
        print(f"  Pass Rate: {summary['pass_rate']}%")

        # Intent 결과
        intent = summary.get("intent_stats", {})
        print("\n[Intent Verification]")
        print(f"  Total Intents:  {intent.get('total_intents', 0)}")
        print(f"  Violations:     {intent.get('violations', 0)} ({intent.get('violation_rate', 0)}%)")
        print(f"  Warnings:       {intent.get('warnings', 0)} ({intent.get('warning_rate', 0)}%)")
        print(f"  Satisfied:      {intent.get('satisfied', 0)} ({intent.get('satisfied_rate', 0)}%)")
        print(f"  Bug Detected:   {intent.get('bug_detected', 0)} ({intent.get('bug_detection_rate', 0)}%)")

        # 시간 통계
        time_stats = summary.get("time_stats", {})
        print("\n[Execution Time]")
        print(f"  Total:   {time_stats.get('total_time', 0)}s")
        print(f"  Average: {time_stats.get('avg_time', 0)}s")
        print(f"  Min:     {time_stats.get('min_time', 0)}s")
        print(f"  Max:     {time_stats.get('max_time', 0)}s")

        # 카테고리별 통계
        cat_stats = summary.get("category_stats", {})
        if cat_stats:
            print("\n[By Category]")
            for cat, stats in cat_stats.items():
                print(f"  {cat}:")
                print(f"    Cases: {stats['total']} (pass: {stats['pass']}, partial: {stats['partial']}, fail: {stats['fail']})")
                print(f"    Bugs:  {stats['violations']} violations, {stats['warnings']} warnings")
                print(f"    Time:  {stats['execution_time']}s")

        print(f"\n{'='*60}")


def main():
    parser = argparse.ArgumentParser(description="RQ1 Evaluation Runner")
    parser.add_argument("--category", "-c", help="Run specific category only")
    parser.add_argument("--case", "-t", help="Run specific test case only")
    parser.add_argument("--list", "-l", action="store_true", help="List available cases")
    args = parser.parse_args()

    base_dir = Path(__file__).parent
    cases_dir = base_dir / "cases"
    results_dir = base_dir / "results"

    runner = RQ1Runner(cases_dir, results_dir)

    if args.list:
        cases = runner.discover_cases()
        print(f"Available test cases ({len(cases)}):")
        for case in cases:
            print(f"  [{case['_category']}] {case['id']}: {case['name']}")
        return

    runner.run_all(category=args.category, case_id=args.case)


if __name__ == "__main__":
    main()
