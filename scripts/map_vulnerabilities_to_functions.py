"""
NumScout 취약점 라인을 함수에 매핑하는 스크립트
"""
import json
import os
import re
from pathlib import Path
from collections import defaultdict

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
NUMSCOUT_DIR = Path(os.environ.get(
    "NUMSCOUT_EXPERIMENT_DIR",
    r"C:\Users\isjeon\NumScout\NumScout\Experiment\95_Samples_Run",
))
SAMPLES_DIR = NUMSCOUT_DIR / "95_samples"
OUTPUT_DIR = _PROJECT_ROOT / "analysis"
OUTPUT_DIR.mkdir(exist_ok=True)

def parse_function_ranges(sol_file):
    """
    Solidity 파일에서 함수 정의와 그 범위를 파싱
    Returns: [(function_name, start_line, end_line), ...]
    """
    try:
        with open(sol_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        functions = []
        stack = []  # (func_name, start_line, open_braces)

        for line_num, line in enumerate(lines, 1):
            # 함수 정의 찾기
            func_match = re.search(r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)', line)
            if func_match:
                func_name = func_match.group(1)
                # 함수 시작
                stack.append({
                    'name': func_name,
                    'start': line_num,
                    'braces': 0,
                    'started': False
                })

            # 중괄호 카운팅
            if stack:
                for item in stack:
                    if not item['started']:
                        if '{' in line:
                            item['started'] = True
                            item['braces'] += line.count('{')
                    else:
                        item['braces'] += line.count('{')

                    item['braces'] -= line.count('}')

                    # 함수 종료
                    if item['started'] and item['braces'] == 0:
                        functions.append((item['name'], item['start'], line_num))
                        stack.remove(item)
                        break

        return functions
    except Exception as e:
        print(f"Error parsing {sol_file}: {e}")
        return []

def extract_line_number(warning_text):
    """
    Warning 텍스트에서 라인 번호 추출
    예: "ex_95_samples/GameTime.sol:197:9: Warning: Div In Path."
    """
    match = re.search(r':(\d+):\d+:', warning_text)
    if match:
        return int(match.group(1))
    return None

def map_line_to_function(line_num, function_ranges):
    """
    라인 번호가 어떤 함수에 속하는지 찾기
    """
    for func_name, start, end in function_ranges:
        if start <= line_num <= end:
            return func_name
    return None

def analyze_contract_vulnerabilities(sol_file, json_file):
    """
    Contract의 취약점을 함수별로 매핑
    """
    # 함수 범위 파싱
    function_ranges = parse_function_ranges(sol_file)

    # JSON 파일 읽기
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except:
        return None

    result = {
        'file': sol_file.name,
        'contract': json_file.stem.split(':')[-1] if ':' in json_file.stem else json_file.stem,
        'vulnerabilities_by_function': defaultdict(lambda: defaultdict(list)),
        'function_ranges': function_ranges
    }

    # 각 취약점 유형별로 분석
    analysis = data.get('analysis', {})
    for vuln_type, warning_chains in analysis.items():
        if not warning_chains:
            continue

        for chain in warning_chains:
            for warning in chain:
                line_num = extract_line_number(warning)
                if line_num:
                    func_name = map_line_to_function(line_num, function_ranges)
                    if func_name:
                        # 코드 스니펫 추출
                        code_match = re.search(r'Warning:.*?\n\s*(.+)', warning)
                        code_snippet = code_match.group(1).strip() if code_match else ''

                        result['vulnerabilities_by_function'][func_name][vuln_type].append({
                            'line': line_num,
                            'code': code_snippet
                        })

    return result

def main():
    all_results = []

    # 0.8+ contract만 필터링
    with open(OUTPUT_DIR / "filtered_by_version.json", 'r', encoding='utf-8') as f:
        version_data = json.load(f)

    contracts_08_plus = {c['file'] for c in version_data['contracts_08_plus']}

    # 각 contract 분석
    for sol_file in SAMPLES_DIR.glob("*.sol"):
        if sol_file.name not in contracts_08_plus:
            continue

        json_file = None
        # JSON 파일 찾기
        for potential_json in SAMPLES_DIR.glob(f"{sol_file.stem}*.json"):
            json_file = potential_json
            break

        if json_file:
            result = analyze_contract_vulnerabilities(sol_file, json_file)
            if result and result['vulnerabilities_by_function']:
                all_results.append(result)

    # 결과 저장
    with open(OUTPUT_DIR / "vulnerabilities_by_function.json", 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)

    # Markdown 리포트 생성
    with open(OUTPUT_DIR / "vulnerabilities_by_function.md", 'w', encoding='utf-8') as f:
        f.write("# Vulnerabilities Mapped to Functions (Solidity 0.8+)\n\n")
        f.write(f"## Summary\n\n")
        f.write(f"- Total contracts with vulnerabilities: {len(all_results)}\n\n")

        for result in sorted(all_results, key=lambda x: x['contract']):
            f.write(f"## {result['contract']} ({result['file']})\n\n")

            for func_name, vulns in sorted(result['vulnerabilities_by_function'].items()):
                f.write(f"### Function: `{func_name}`\n\n")

                for vuln_type, instances in sorted(vulns.items()):
                    f.write(f"#### {vuln_type}\n\n")
                    for instance in instances:
                        f.write(f"- Line {instance['line']}: `{instance['code']}`\n")
                    f.write("\n")

    print(f"Vulnerability-to-function mapping completed!")
    print(f"  - Contracts analyzed: {len(all_results)}")
    print(f"  - Results saved to: {OUTPUT_DIR / 'vulnerabilities_by_function.md'}")

    # 통계 출력
    total_vulns = sum(
        len(instances)
        for result in all_results
        for vulns in result['vulnerabilities_by_function'].values()
        for instances in vulns.values()
    )
    print(f"  - Total vulnerability instances: {total_vulns}")

if __name__ == "__main__":
    main()
