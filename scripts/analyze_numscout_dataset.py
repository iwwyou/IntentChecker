"""
NumScout 95개 데이터셋의 타겟 함수 및 취약점 분석 스크립트
"""
import json
import os
import re
from collections import defaultdict
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
NUMSCOUT_DIR = Path(os.environ.get(
    "NUMSCOUT_EXPERIMENT_DIR",
    r"C:\Users\isjeon\NumScout\NumScout\Experiment\95_Samples_Run",
))
SAMPLES_DIR = NUMSCOUT_DIR / "95_samples"
OUTPUT_DIR = _PROJECT_ROOT / "analysis"
OUTPUT_DIR.mkdir(exist_ok=True)

def extract_function_name(warning_text):
    """
    Warning 텍스트에서 함수 이름 추출
    예: "ex_95_samples/926476bfc3550ccb424202004b9aab9ac40e32de_VeChainX.sol:179:9: Warning: Div In Path.\n        getTokens()"
    """
    # 함수 호출 패턴 찾기: functionName(...) 또는 functionName
    match = re.search(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', warning_text)
    if match:
        return match.group(1)
    return None

def parse_json_file(json_path):
    """
    개별 contract의 json 파일 파싱
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        result = {
            'file': json_path.stem.replace(':' + json_path.stem.split(':')[-1], ''),
            'contract': json_path.stem.split(':')[-1],
            'defects': {},
            'target_functions': set(),
            'evm_coverage': data.get('evm_code_coverage', 'N/A'),
            'pub_fun_count': data.get('pub_fun_count', 0),
        }

        analysis = data.get('analysis', {})

        # 각 취약점 유형별로 분석
        for vuln_type, warnings_list in analysis.items():
            if warnings_list:  # 취약점이 있는 경우
                functions = set()
                for warning_chain in warnings_list:
                    for warning in warning_chain:
                        func_name = extract_function_name(warning)
                        if func_name:
                            functions.add(func_name)
                            result['target_functions'].add(func_name)

                if functions:
                    result['defects'][vuln_type] = list(functions)

        return result
    except Exception as e:
        print(f"Error parsing {json_path}: {e}")
        return None

def main():
    # 전체 summary 로드
    with open(NUMSCOUT_DIR / "95_samples.json", 'r', encoding='utf-8') as f:
        summary = json.load(f)

    all_results = []
    vuln_stats = defaultdict(lambda: {'count': 0, 'contracts': []})

    # 각 contract의 json 파일 분석
    for json_file in SAMPLES_DIR.glob("*.json"):
        result = parse_json_file(json_file)
        if result:
            all_results.append(result)

            # 취약점 통계
            for vuln_type, functions in result['defects'].items():
                vuln_stats[vuln_type]['count'] += 1
                vuln_stats[vuln_type]['contracts'].append({
                    'contract': result['contract'],
                    'file': result['file'],
                    'functions': functions
                })

    # 결과 정리
    summary_report = {
        'total_contracts': len(all_results),
        'vulnerability_summary': summary['vul'],
        'contracts_with_defects': sum(1 for r in all_results if r['defects']),
        'vulnerability_details': dict(vuln_stats),
        'all_contracts': all_results
    }

    # JSON 저장
    with open(OUTPUT_DIR / "numscout_analysis_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary_report, f, indent=2, ensure_ascii=False, default=str)

    # Markdown 리포트 생성
    with open(OUTPUT_DIR / "numscout_target_functions.md", 'w', encoding='utf-8') as f:
        f.write("# NumScout 95개 데이터셋 타겟 함수 분석\n\n")
        f.write(f"## 전체 통계\n\n")
        f.write(f"- 총 Contract 수: {len(all_results)}\n")
        f.write(f"- 취약점 발견된 Contract 수: {summary_report['contracts_with_defects']}\n\n")

        f.write("## 취약점 유형별 통계\n\n")
        for vuln_type, stats in vuln_stats.items():
            f.write(f"### {vuln_type}\n")
            f.write(f"- 발견 횟수: {stats['count']}\n")
            f.write(f"- 영향받은 Contract:\n")
            for contract_info in stats['contracts']:
                f.write(f"  - **{contract_info['contract']}** ({contract_info['file']})\n")
                f.write(f"    - 타겟 함수: {', '.join(contract_info['functions'])}\n")
            f.write("\n")

        f.write("## 전체 Contract 목록\n\n")
        f.write("| No | Contract | File | Defect Types | Target Functions | Public Functions |\n")
        f.write("|-----|----------|------|--------------|------------------|------------------|\n")

        for idx, result in enumerate(sorted(all_results, key=lambda x: x['contract']), 1):
            defect_types = ', '.join(result['defects'].keys()) if result['defects'] else 'None'
            target_funcs = ', '.join(sorted(result['target_functions'])) if result['target_functions'] else 'N/A'
            f.write(f"| {idx} | {result['contract']} | {result['file'][:30]}... | {defect_types} | {target_funcs[:50]}... | {result['pub_fun_count']} |\n")

    print(f"Analysis completed!")
    print(f"  - Total contracts analyzed: {len(all_results)}")
    print(f"  - Contracts with defects: {summary_report['contracts_with_defects']}")
    print(f"  - Results saved to: {OUTPUT_DIR / 'numscout_target_functions.md'}")

    # Vulnerability summary
    print("\nVulnerability type summary:")
    for vuln_type, count in summary['vul'].items():
        print(f"  - {vuln_type}: {count}")

if __name__ == "__main__":
    main()
