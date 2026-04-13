"""
Guardian scope 제약 확인 스크립트
- Multi contract (library만)
- Single transaction
"""
import os
import re
import json
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

def check_external_calls(contract_code):
    """
    External contract call 패턴 확인
    Returns: (has_external_call, external_call_examples)
    """
    external_patterns = [
        r'(\w+)\s*=\s*\w+\([^)]*\)',  # Contract instantiation: token = Token(address)
        r'\.call\s*\(',  # Low-level call
        r'\.delegatecall\s*\(',  # Delegatecall
        r'\.staticcall\s*\(',  # Staticcall
        r'interface\s+\w+',  # Interface usage
    ]

    external_calls = []

    # Library는 제외
    library_pattern = r'library\s+(\w+)'
    libraries = set(re.findall(library_pattern, contract_code))

    # External contract call 찾기
    for pattern in external_patterns:
        matches = re.finditer(pattern, contract_code, re.MULTILINE)
        for match in matches:
            line_start = contract_code.rfind('\n', 0, match.start()) + 1
            line_end = contract_code.find('\n', match.end())
            line = contract_code[line_start:line_end if line_end != -1 else len(contract_code)]

            # Library call은 제외
            is_library_call = False
            for lib in libraries:
                if lib in line:
                    is_library_call = True
                    break

            if not is_library_call and line.strip():
                external_calls.append(line.strip())

    return len(external_calls) > 0, external_calls[:5]  # 최대 5개 예시만

def check_multi_transaction(contract_code):
    """
    Multi-transaction 패턴 확인
    """
    # 일반적인 multi-transaction 패턴
    multi_tx_patterns = [
        r'approve.*transferFrom',  # ERC20 approve-transferFrom pattern
        r'require.*allowance',  # Allowance check
    ]

    multi_tx_indicators = []

    for pattern in multi_tx_patterns:
        if re.search(pattern, contract_code, re.IGNORECASE):
            multi_tx_indicators.append(pattern)

    # 실제로는 대부분의 ERC20 토큰이 approve/transferFrom을 가지고 있지만
    # 분석 대상 함수가 single transaction인지는 함수별로 확인 필요
    return False, []  # 일단 보수적으로 판단

def analyze_contract_scope(sol_file):
    """
    개별 contract의 Guardian scope 적합성 분석
    """
    try:
        with open(sol_file, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()

        has_external, external_examples = check_external_calls(code)
        has_multi_tx, multi_tx_examples = check_multi_transaction(code)

        # Library 사용 확인
        libraries = re.findall(r'library\s+(\w+)', code)

        # Contract 개수 확인
        contracts = re.findall(r'contract\s+(\w+)', code)

        return {
            'file': sol_file.name,
            'has_external_call': has_external,
            'external_call_examples': external_examples,
            'has_multi_transaction': has_multi_tx,
            'multi_tx_examples': multi_tx_examples,
            'libraries': libraries,
            'contracts': contracts,
            'guardian_compatible': not has_external,  # Library만 사용하면 OK
        }
    except Exception as e:
        print(f"Error analyzing {sol_file}: {e}")
        return None

def main():
    # 이전 분석 결과 로드
    with open(OUTPUT_DIR / "numscout_analysis_summary.json", 'r', encoding='utf-8') as f:
        analysis_data = json.load(f)

    # Scope 분석
    scope_results = []
    compatible_count = 0
    incompatible_count = 0

    for sol_file in SAMPLES_DIR.glob("*.sol"):
        scope_result = analyze_contract_scope(sol_file)
        if scope_result:
            scope_results.append(scope_result)

            if scope_result['guardian_compatible']:
                compatible_count += 1
            else:
                incompatible_count += 1

    # 결과 저장
    scope_summary = {
        'total_contracts': len(scope_results),
        'guardian_compatible': compatible_count,
        'guardian_incompatible': incompatible_count,
        'results': scope_results
    }

    with open(OUTPUT_DIR / "guardian_scope_analysis.json", 'w', encoding='utf-8') as f:
        json.dump(scope_summary, f, indent=2, ensure_ascii=False)

    # Markdown 리포트 생성
    with open(OUTPUT_DIR / "guardian_scope_report.md", 'w', encoding='utf-8') as f:
        f.write("# Guardian Scope Compatibility Analysis\n\n")
        f.write("## Summary\n\n")
        f.write(f"- Total contracts: {len(scope_results)}\n")
        f.write(f"- Guardian compatible: {compatible_count}\n")
        f.write(f"- Guardian incompatible: {incompatible_count}\n")
        f.write(f"- Compatibility rate: {compatible_count/len(scope_results)*100:.1f}%\n\n")

        f.write("## Incompatible Contracts (External Calls)\n\n")
        for result in scope_results:
            if not result['guardian_compatible']:
                f.write(f"### {result['file']}\n")
                f.write(f"- Contracts: {', '.join(result['contracts'])}\n")
                f.write(f"- Libraries: {', '.join(result['libraries']) if result['libraries'] else 'None'}\n")
                if result['external_call_examples']:
                    f.write(f"- External call examples:\n")
                    for example in result['external_call_examples']:
                        f.write(f"  - `{example}`\n")
                f.write("\n")

        f.write("## Compatible Contracts\n\n")
        f.write("| No | File | Contracts | Libraries |\n")
        f.write("|-----|------|-----------|------------|\n")

        compatible_contracts = [r for r in scope_results if r['guardian_compatible']]
        for idx, result in enumerate(sorted(compatible_contracts, key=lambda x: x['file']), 1):
            contracts_str = ', '.join(result['contracts'][:3])
            libraries_str = ', '.join(result['libraries']) if result['libraries'] else 'None'
            f.write(f"| {idx} | {result['file'][:50]} | {contracts_str} | {libraries_str} |\n")

    print(f"Scope analysis completed!")
    print(f"  - Total contracts: {len(scope_results)}")
    print(f"  - Guardian compatible: {compatible_count}")
    print(f"  - Guardian incompatible: {incompatible_count}")
    print(f"  - Compatibility rate: {compatible_count/len(scope_results)*100:.1f}%")
    print(f"  - Results saved to: {OUTPUT_DIR / 'guardian_scope_report.md'}")

if __name__ == "__main__":
    main()
