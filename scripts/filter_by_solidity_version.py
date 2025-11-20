"""
Solidity 0.8 이상 버전의 contract만 필터링
"""
import json
import csv
import re
from pathlib import Path
from collections import defaultdict

# 경로 설정
NUMSCOUT_DIR = Path(r"C:\Users\isjeon\NumScout\NumScout\Experiment\95_Samples_Run")
SAMPLES_DIR = NUMSCOUT_DIR / "95_samples"
OUTPUT_DIR = Path(r"C:\Users\isjeon\PycharmProjects\pythonProject\SolidityGuardian\analysis")
OUTPUT_DIR.mkdir(exist_ok=True)

def parse_solidity_version(version_str):
    """
    Solidity 버전 파싱
    예: "0.8.7" -> (0, 8, 7)
        "v0.4.24" -> (0, 4, 24)
    """
    # v 제거
    version_str = version_str.strip().lstrip('v')

    # 버전 숫자 추출
    match = re.match(r'^(\d+)\.(\d+)(?:\.(\d+))?', version_str)
    if match:
        major = int(match.group(1))
        minor = int(match.group(2))
        patch = int(match.group(3)) if match.group(3) else 0
        return (major, minor, patch)
    return None

def load_vulnerability_data():
    """
    이전 분석 결과에서 취약점 정보 로드
    """
    with open(OUTPUT_DIR / "numscout_analysis_summary.json", 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Contract별 취약점 매핑
    vuln_map = {}
    for contract_info in data['all_contracts']:
        contract_name = contract_info['contract']
        vuln_map[contract_name] = {
            'defects': contract_info['defects'],
            'target_functions': list(contract_info['target_functions']),
            'pub_fun_count': contract_info['pub_fun_count']
        }

    return vuln_map

def main():
    # CSV 파일 읽기
    csv_file = NUMSCOUT_DIR / "95_samples.csv"

    contracts_by_version = defaultdict(list)
    version_08_plus = []
    version_below_08 = []

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 3:
                file_name, contract_name, version = row[0], row[1], row[2]

                parsed_version = parse_solidity_version(version)

                contract_info = {
                    'file': file_name,
                    'contract': contract_name,
                    'version': version,
                    'parsed_version': parsed_version
                }

                if parsed_version:
                    version_key = f"{parsed_version[0]}.{parsed_version[1]}"
                    contracts_by_version[version_key].append(contract_info)

                    # 0.8 이상 체크
                    if parsed_version[0] == 0 and parsed_version[1] >= 8:
                        version_08_plus.append(contract_info)
                    else:
                        version_below_08.append(contract_info)

    # 취약점 데이터 로드
    vuln_map = load_vulnerability_data()

    # 0.8+ contract에 취약점 정보 추가
    for contract in version_08_plus:
        contract_name = contract['contract']
        if contract_name in vuln_map:
            contract.update(vuln_map[contract_name])
        else:
            contract['defects'] = {}
            contract['target_functions'] = []
            contract['pub_fun_count'] = 0

    # 결과 저장
    result = {
        'total_contracts': len(version_08_plus) + len(version_below_08),
        'version_08_plus': len(version_08_plus),
        'version_below_08': len(version_below_08),
        'version_distribution': {k: len(v) for k, v in sorted(contracts_by_version.items())},
        'contracts_08_plus': version_08_plus,
        'contracts_below_08': version_below_08
    }

    with open(OUTPUT_DIR / "filtered_by_version.json", 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    # Markdown 리포트 생성
    with open(OUTPUT_DIR / "solidity_08_plus_contracts.md", 'w', encoding='utf-8') as f:
        f.write("# Solidity 0.8+ Contracts from NumScout Dataset\n\n")
        f.write("## Version Distribution\n\n")
        f.write("| Version | Count |\n")
        f.write("|---------|-------|\n")
        for version, contracts in sorted(contracts_by_version.items()):
            f.write(f"| {version} | {len(contracts)} |\n")

        f.write(f"\n**Total 0.8+ contracts: {len(version_08_plus)}**\n")
        f.write(f"**Total <0.8 contracts: {len(version_below_08)}**\n\n")

        f.write("## Solidity 0.8+ Contracts with Vulnerabilities\n\n")
        f.write("| No | Contract | File | Version | Defect Types | Target Functions |\n")
        f.write("|-----|----------|------|---------|--------------|------------------|\n")

        contracts_with_vulns = [c for c in version_08_plus if c.get('defects')]
        for idx, contract in enumerate(sorted(contracts_with_vulns, key=lambda x: x['contract']), 1):
            defect_types = ', '.join(contract['defects'].keys()) if contract.get('defects') else 'None'
            target_funcs = ', '.join(contract.get('target_functions', [])[:5])
            if len(contract.get('target_functions', [])) > 5:
                target_funcs += '...'
            f.write(f"| {idx} | {contract['contract']} | {contract['file'][:35]}... | {contract['version']} | {defect_types} | {target_funcs[:40]}... |\n")

        f.write(f"\n**Total 0.8+ contracts with vulnerabilities: {len(contracts_with_vulns)}**\n\n")

        f.write("## All Solidity 0.8+ Contracts\n\n")
        f.write("| No | Contract | File | Version | Has Defects |\n")
        f.write("|-----|----------|------|---------|-------------|\n")

        for idx, contract in enumerate(sorted(version_08_plus, key=lambda x: x['contract']), 1):
            has_defects = "Yes" if contract.get('defects') else "No"
            f.write(f"| {idx} | {contract['contract']} | {contract['file'][:40]}... | {contract['version']} | {has_defects} |\n")

    print(f"Version filtering completed!")
    print(f"  - Total contracts: {result['total_contracts']}")
    print(f"  - Solidity 0.8+: {len(version_08_plus)}")
    print(f"  - Solidity <0.8: {len(version_below_08)}")
    print(f"  - 0.8+ with vulnerabilities: {len(contracts_with_vulns)}")
    print(f"\nVersion distribution:")
    for version, count in sorted(contracts_by_version.items()):
        marker = " [0.8+]" if version.startswith("0.") and int(version.split('.')[1]) >= 8 else ""
        print(f"  - {version}: {count}{marker}")
    print(f"\n  - Results saved to: {OUTPUT_DIR / 'solidity_08_plus_contracts.md'}")

if __name__ == "__main__":
    main()
