"""
Script to find the target .sol files for all 75 non-excluded cases
and generate case_mapping.csv for RQ3.
"""
import os
import re
import csv

WEB3BUGS_BASE = "C:/Users/isjeon/Web3Bugs/contracts"
NUMSCOUT_BASE = "C:/Users/isjeon/PycharmProjects/pythonProject/SolidityGuardian/Dataset/Numscout"
OUTPUT_CSV = "C:/Users/isjeon/PycharmProjects/pythonProject/SolidityGuardian/evaluation/RQ3/case_mapping.csv"

# Project root subdirectories (relative to contest folder)
PROJECT_ROOTS = {
    "5": "", "17": "", "25": "", "44": "", "45": "", "47": "", "52": "", "56": "",
    "61": "", "70": "", "71": "", "78": "", "79": "", "83": "", "110": "", "113": "", "192": "",
    "8": "nftx-protocol-v2", "16": "src", "29": "trident", "31": "veCVX", "34": "v4-core",
    "35": "trident", "36": "contracts", "42": "projects/mochi-core", "51": "customswap",
    "58": "mellow-vaults", "59": "src", "60": "protocol", "62": "Streaming",
    "65": "contracts", "77": "elasticswap", "101": "sublime-v1", "112": "backd",
    "3": "", "39": "",
}

# NumScout mappings: case_id -> (pattern_subdir, sol_filename, solc_version)
NUMSCOUT_FILES = {
    "numscout_WANGMI": ("div_in_path", "39da420ac0d9a6d8e05c5d9acac75377decfbb42_WANGMI.sol", "0.6.12"),
    "numscout_Nokon": ("exchange_problem", "259562c54c07aca61e12ee12c62016eaf3fd7852_Nokon.sol", "0.7.4"),
    "numscout_SwordCrowdsale": (None, None, "0.6.12"),  # No original; contraction only
    "numscout_BoostToken_operator": ("operator_order_issue", "4E0fCa55a6C3A94720ded91153A27F60E26B9AA8_BoostToken.sol", "0.6.12"),
    "numscout_BoostToken_indivisible": ("indivisible_amount", "4E0fCa55a6C3A94720ded91153A27F60E26B9AA8_BoostToken.sol", "0.6.12"),
    "numscout_EthereumGod": ("precision_loss_trend", "2f0b287275Fc50a1Cb854797927A12a98d3b9460_EthereumGod.sol", "0.6.12"),
    "numscout_HIT": ("profit_opportunity", "2af6139c39c05e0597c0ac12c60b303c38aa69e7_HIT.sol", "0.4.24"),
}


def find_sol_file(contest_num, contract_name):
    """Find the .sol file containing 'contract ContractName' in the contest directory."""
    contest_dir = os.path.join(WEB3BUGS_BASE, contest_num)
    if not os.path.exists(contest_dir):
        return None, None

    # First try: look for file named after the contract
    for root, dirs, files in os.walk(contest_dir):
        # Skip node_modules, .git, etc.
        dirs[:] = [d for d in dirs if d not in ('node_modules', '.git', 'artifacts', 'cache', 'typechain')]
        for f in files:
            if f.endswith('.sol'):
                if f == contract_name + '.sol':
                    full_path = os.path.join(root, f).replace('\\', '/')
                    # Get pragma
                    solc = extract_solc(full_path)
                    rel_path = full_path.replace(WEB3BUGS_BASE + '/', '')
                    return rel_path, solc

    # Second try: grep for 'contract ContractName'
    pattern = re.compile(r'^\s*contract\s+' + re.escape(contract_name) + r'\s')
    for root, dirs, files in os.walk(contest_dir):
        dirs[:] = [d for d in dirs if d not in ('node_modules', '.git', 'artifacts', 'cache', 'typechain')]
        for f in files:
            if f.endswith('.sol'):
                full_path = os.path.join(root, f).replace('\\', '/')
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as fh:
                        for line in fh:
                            if pattern.search(line):
                                solc = extract_solc(full_path)
                                rel_path = full_path.replace(WEB3BUGS_BASE + '/', '')
                                return rel_path, solc
                except:
                    pass

    # Third try: look for library or abstract contract
    pattern2 = re.compile(r'^\s*(library|abstract\s+contract)\s+' + re.escape(contract_name) + r'\s')
    for root, dirs, files in os.walk(contest_dir):
        dirs[:] = [d for d in dirs if d not in ('node_modules', '.git', 'artifacts', 'cache', 'typechain')]
        for f in files:
            if f.endswith('.sol'):
                full_path = os.path.join(root, f).replace('\\', '/')
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as fh:
                        for line in fh:
                            if pattern2.search(line):
                                solc = extract_solc(full_path)
                                rel_path = full_path.replace(WEB3BUGS_BASE + '/', '')
                                return rel_path, solc
                except:
                    pass

    return None, None


def extract_solc(filepath):
    """Extract solc version from pragma solidity statement."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                m = re.search(r'pragma\s+solidity\s+[\^>=<]*\s*([\d.]+)', line)
                if m:
                    return m.group(1)
    except:
        pass
    return ""


def main():
    # Read dataset
    dataset_path = "C:/Users/isjeon/PycharmProjects/pythonProject/SolidityGuardian/evaluation/RQ1/dataset.csv"
    rows = []
    with open(dataset_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r['id'].strip() and not r['status'].startswith('excluded'):
                rows.append(r)

    print(f"Processing {len(rows)} non-excluded cases...")

    results = []
    for r in rows:
        case_id = r['id']
        source = r['source']
        contract_name = r['contract']
        function_name = r['function']
        pattern = r['pattern']
        status = r['status']

        if source == 'numscout':
            contest_number = ""
            project_root = ""
            ns = NUMSCOUT_FILES.get(case_id)
            if ns:
                subdir, sol_file, solc = ns
                if subdir and sol_file:
                    target_sol = f"Dataset/Numscout/Original/Target/{subdir}/{sol_file}"
                else:
                    # SwordCrowdsale - no original, use contraction
                    target_sol = f"Dataset/Numscout/contraction/greedy_contract/SwordCrowdsale_contraction.sol"
                solc_version = solc
            else:
                target_sol = ""
                solc_version = ""
        else:
            # web3bugs
            m = re.match(r'web3bugs_(\d+)_', case_id)
            contest_number = m.group(1) if m else ""
            project_root_sub = PROJECT_ROOTS.get(contest_number, "")
            if project_root_sub:
                project_root = f"{contest_number}/{project_root_sub}"
            else:
                project_root = contest_number

            print(f"  Searching {case_id} -> contract={contract_name} in contest {contest_number}...")
            sol_path, solc = find_sol_file(contest_number, contract_name)
            target_sol = sol_path if sol_path else ""
            solc_version = solc if solc else ""

        results.append({
            'case_id': case_id,
            'source': source,
            'contract_name': contract_name,
            'function_name': function_name,
            'pattern': pattern,
            'status': status,
            'contest_number': contest_number,
            'project_root': project_root,
            'target_sol_file': target_sol,
            'solc_version': solc_version,
        })

    # Write CSV
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'case_id', 'source', 'contract_name', 'function_name', 'pattern', 'status',
            'contest_number', 'project_root', 'target_sol_file', 'solc_version'
        ])
        writer.writeheader()
        writer.writerows(results)

    print(f"\nWrote {len(results)} rows to {OUTPUT_CSV}")

    # Summary of missing
    missing = [r for r in results if not r['target_sol_file']]
    if missing:
        print(f"\nWARNING: {len(missing)} cases with missing target_sol_file:")
        for r in missing:
            print(f"  {r['case_id']} ({r['contract_name']})")


if __name__ == '__main__':
    main()
