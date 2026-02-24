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
import csv
import re
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

    @staticmethod
    def classify_intent_clause(intent_type: str, expr: str) -> str:
        """
        Intent expression을 clause type으로 분류

        During (3 types):
          - DuringBeforeAfter: var(Before relOp After)
          - DuringAssignCurrent: var(Assign relOp Current)
          - DuringFunctionArg: func.arg[N] relOp value

        Post (1 type for paper, 2 in implementation):
          - PostEntryExit: var(Entry relOp Exit) or Unchanged(var)

        Common (1 type):
          - CommonClause: relational comparisons, return checks, etc.
        """
        expr_lower = expr.lower()

        if intent_type == "Post":
            if "entry" in expr_lower and "exit" in expr_lower:
                return "PostEntryExit"
            elif "unchanged" in expr_lower:
                return "PostEntryExit"  # Unchanged는 Entry == Exit로 통합
            else:
                return "CommonClause"
        elif intent_type == "During":
            if "before" in expr_lower and "after" in expr_lower:
                return "DuringBeforeAfter"
            elif "assign" in expr_lower and "current" in expr_lower:
                return "DuringAssignCurrent"
            elif ".arg[" in expr:
                return "DuringFunctionArg"
            else:
                return "CommonClause"
        else:
            return "CommonClause"

    @staticmethod
    def parse_result_line(line: str) -> dict:
        """결과 라인에서 정보 추출"""
        result = {
            "actual_result": "unknown",
            "risk_score": None,
            "message": line
        }

        if "VIOLATION]" in line:
            result["actual_result"] = "violated"
        elif "SATISFIED]" in line or "SUCCESS]" in line:
            result["actual_result"] = "satisfied"
        elif "WARNING]" in line:
            result["actual_result"] = "warning"
        elif "ERROR]" in line:
            result["actual_result"] = "error"

        # risk score [risk=X.X] 추출
        risk_match = re.search(r'\[risk=([0-9.]+)\]', line)
        if risk_match:
            result["risk_score"] = float(risk_match.group(1))

        return result

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
            "metrics": {},
            "intent_details": []  # Intent별 상세 정보
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

            # 2.5. target contract/function 설정
            analyzer.current_target_contract = case.get("target_contract")
            analyzer.current_target_function = case.get("target_function")

            # 3. Phase 1: 코드 파싱
            for rec in records:
                code, s, e, ev = rec["code"], rec["startLine"], rec["endLine"], rec["event"]
                analyzer.update_code(s, e, code, ev)

                stripped = code.strip()
                if stripped and not stripped.startswith("// @"):
                    ctx = analyzer.get_current_context_type()
                    if ctx:  # ctx=None은 interface body 등 파싱 불필요한 라인
                        try:
                            tree = ParserHelpers.generate_parse_tree(code, ctx, False)
                            EnhancedSolidityVisitor(analyzer).visit(tree)
                        except Exception as parse_err:
                            # Debug: show parsing errors
                            print(f"[PARSE ERR] Line {s}: ctx={ctx}, code={code[:50]}... -> {parse_err}")

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
                    import traceback
                    result["errors"].append(f"Intent annotation error at line {line_no}: {e}")
                    print(f"Traceback: {traceback.format_exc()}")

            # 5. Phase 3: Debug annotations 추가 및 실행
            batch_mgr.reset()

            # Debugging BEGIN
            debug_line = case.get("debug_annotations", [{}])[0].get("line", 140)
            analyzer.update_code(debug_line, debug_line, "// @Debugging BEGIN", "add")

            for debug in case.get("debug_annotations", []):
                var = debug["var"]
                value = debug["value"]
                line = debug.get("line", debug_line)
                anno_type = debug.get("type", "LocalVar")  # LocalVar or StateVar

                if isinstance(value, list) and len(value) == 2:
                    value_str = f"[{value[0]}, {value[1]}]"
                else:
                    value_str = str(value)

                annotation = f"// @{anno_type} {var} = {value_str}"
                print(f"Adding debug: {annotation}")
                batch_mgr.add_line(annotation, line, line)

            # 6. flush로 실행 - 결과 캡처
            import io
            from contextlib import redirect_stdout

            # Set target context for debug annotations
            analyzer.current_target_contract = case.get("target_contract")
            analyzer.current_target_function = case.get("target_function")

            output_buffer = io.StringIO()
            try:
                with redirect_stdout(output_buffer):
                    batch_mgr.flush()
            except Exception as flush_err:
                import traceback
                print(f"[FLUSH ERR] {flush_err}")
                print(f"Traceback: {traceback.format_exc()}")

            output = output_buffer.getvalue()

            # 7. 결과 파싱
            output_lines = []
            for line in output.split('\n'):
                line = line.strip()
                if not line:
                    continue
                if 'VIOLATION]' in line:
                    result["violations"].append(line)
                    output_lines.append(line)
                elif 'SUCCESS]' in line or 'SATISFIED]' in line:
                    result["satisfied"].append(line)
                    output_lines.append(line)
                elif 'ERROR]' in line:
                    result["errors"].append(line)
                    output_lines.append(line)
                elif 'WARNING]' in line:
                    result["warnings"].append(line)
                    output_lines.append(line)

            # 7.5 Intent별 상세 정보 수집
            intent_annotations = case.get("intent_annotations", [])
            for i, intent in enumerate(intent_annotations):
                intent_type = intent.get("type", "During")
                expr = intent.get("expr", "")
                line_no = intent.get("line", 0)
                expected = intent.get("expected", "violated")

                # 해당 라인의 출력 찾기
                actual_result = "not_found"
                risk_score = None
                for out_line in output_lines:
                    if f"Line {line_no}:" in out_line:
                        parsed = self.parse_result_line(out_line)
                        actual_result = parsed["actual_result"]
                        risk_score = parsed["risk_score"]
                        break

                is_correct = (expected == actual_result) or \
                             (expected == "violated" and actual_result in ["violated", "warning"])

                result["intent_details"].append({
                    "intent_type": intent_type,
                    "intent_clause_type": self.classify_intent_clause(intent_type, expr),
                    "intent_expression": expr,
                    "intent_line": line_no,
                    "expected_result": expected,
                    "actual_result": actual_result,
                    "is_correct": is_correct,
                    "risk_score": risk_score
                })

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
            # 에러 시 기본 metrics 설정
            result["metrics"] = {
                "total_intents": 0,
                "num_violations": 0,
                "num_warnings": 0,
                "num_satisfied": 0,
                "num_errors": 1,
                "num_bug_detected": 0,
                "violation_rate": 0,
                "warning_rate": 0,
                "satisfied_rate": 0,
                "bug_detection_rate": 0,
            }
            result["actual_violations"] = 0
            result["expected_violations"] = case.get("expected_results", {}).get("expected_violations", 0)

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

        # CSV 출력
        self.export_csv(results)

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

    def export_csv(self, results: list[dict], filename: str = "rq1_results.csv"):
        """결과를 CSV 파일로 출력"""
        csv_path = self.results_dir / filename

        # CSV 컬럼 정의
        fieldnames = [
            "case_id", "category", "source_file",
            "target_contract", "target_function", "bug_lines",
            "intent_type", "intent_clause_type", "intent_expression", "intent_line",
            "expected_result", "actual_result", "is_correct", "risk_score",
            "total_intents", "num_violations", "num_satisfied",
            "execution_time_sec"
        ]

        rows = []
        for result in results:
            case_base = {
                "case_id": result["id"],
                "category": result["category"],
                "source_file": result["source"],
                "target_contract": result["target_contract"],
                "target_function": result["target_function"],
                "bug_lines": ";".join(map(str, result.get("bug_lines", []))),
                "total_intents": result["metrics"].get("total_intents", 0),
                "num_violations": result["metrics"].get("num_violations", 0),
                "num_satisfied": result["metrics"].get("num_satisfied", 0),
                "execution_time_sec": result.get("execution_time", 0)
            }

            intent_details = result.get("intent_details", [])
            if intent_details:
                for detail in intent_details:
                    row = {**case_base}
                    row["intent_type"] = detail.get("intent_type", "")
                    row["intent_clause_type"] = detail.get("intent_clause_type", "")
                    row["intent_expression"] = detail.get("intent_expression", "")
                    row["intent_line"] = detail.get("intent_line", "")
                    row["expected_result"] = detail.get("expected_result", "")
                    row["actual_result"] = detail.get("actual_result", "")
                    row["is_correct"] = detail.get("is_correct", "")
                    row["risk_score"] = detail.get("risk_score", "")
                    rows.append(row)
            else:
                # intent_details가 없으면 케이스 정보만 출력
                row = {**case_base}
                row["intent_type"] = ""
                row["intent_clause_type"] = ""
                row["intent_expression"] = ""
                row["intent_line"] = ""
                row["expected_result"] = ""
                row["actual_result"] = ""
                row["is_correct"] = ""
                row["risk_score"] = ""
                rows.append(row)

        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        print(f"\nCSV exported: {csv_path}")
        return csv_path


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
