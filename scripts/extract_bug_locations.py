#!/usr/bin/env python3
"""
Extract bug locations from Web3Bugs dataset for S6-* bugs.
"""

import csv
import re
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Tuple

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
WEB3BUGS_PATH = Path(os.environ.get("WEB3BUGS_ROOT", r"C:\Users\isjeon\Web3Bugs"))
OUTPUT_PATH = _PROJECT_ROOT / "Dataset"


@dataclass
class BugInfo:
    contest_id: str
    bug_id: str
    bug_label: str
    description: str
    reference: str
    # Extracted info
    file_name: Optional[str] = None
    function_name: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    code_snippet: Optional[str] = None


def load_s6_bugs() -> List[BugInfo]:
    """Load S6-* bugs from bugs.csv"""
    bugs = []
    csv_path = WEB3BUGS_PATH / "results" / "bugs.csv"

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            if len(row) >= 6:
                # Strip whitespace from all fields
                row = [cell.strip() for cell in row]
                contest_id, bug_id, bug_label, difficulty, description, reference = row[:6]
                if bug_label.startswith('S6-'):
                    bugs.append(BugInfo(
                        contest_id=contest_id,
                        bug_id=bug_id,
                        bug_label=bug_label,
                        description=description,
                        reference=reference
                    ))
    return bugs


def extract_bug_section(report_content: str, bug_id: str) -> Optional[str]:
    """Extract the section for a specific bug from the report"""
    # Pattern: ## [[H-01] or ## [[M-01] etc
    pattern = rf'## \[\[{re.escape(bug_id)}\].*?\n(.*?)(?=\n## \[\[|\n# |\Z)'
    match = re.search(pattern, report_content, re.DOTALL)
    if match:
        return match.group(0)
    return None


def extract_code_blocks(section: str) -> List[str]:
    """Extract Solidity code blocks from a section"""
    pattern = r'```solidity\n(.*?)```'
    matches = re.findall(pattern, section, re.DOTALL)
    return matches


def extract_function_names(section: str) -> List[str]:
    """Extract function names mentioned in the section"""
    # Pattern: ContractName.functionName or just functionName()
    patterns = [
        r'`(\w+)\.(\w+)`',  # Contract.function
        r'`(\w+)\(`',       # function(
        r'function (\w+)\(',  # function definition
    ]

    functions = []
    for pattern in patterns:
        matches = re.findall(pattern, section)
        for match in matches:
            if isinstance(match, tuple):
                functions.append(match[-1])  # Get function name
            else:
                functions.append(match)

    return list(set(functions))


def extract_github_file_info(section: str) -> List[Tuple[str, Optional[int], Optional[int]]]:
    """Extract file paths and line numbers from GitHub links"""
    # Pattern: [text](github_link)
    # GitHub link might contain: .../ContractName.sol#L27-L78 or .../ContractName.sol L27-L78
    pattern = r'\[.*?\]\((https://github\.com/[^)]+)\)'
    github_links = re.findall(pattern, section)

    results = []
    for link in github_links:
        # Extract file name
        file_match = re.search(r'/([^/]+\.sol)', link)
        if file_match:
            file_name = file_match.group(1)
            # Extract line numbers
            line_match = re.search(r'#?L(\d+)(?:-L?(\d+))?', link)
            if line_match:
                line_start = int(line_match.group(1))
                line_end = int(line_match.group(2)) if line_match.group(2) else line_start
                results.append((file_name, line_start, line_end))
            else:
                results.append((file_name, None, None))

    # Also check for inline mentions like `ContractName.sol` L27-L78
    inline_pattern = r'`([^`]+\.sol)`\s*L(\d+)(?:-L?(\d+))?'
    inline_matches = re.findall(inline_pattern, section)
    for match in inline_matches:
        file_name = match[0]
        line_start = int(match[1])
        line_end = int(match[2]) if match[2] else line_start
        results.append((file_name, line_start, line_end))

    return results


def find_function_in_contracts(contest_id: str, function_name: str) -> List[Tuple[str, int]]:
    """Find function definition in contract files"""
    contracts_dir = WEB3BUGS_PATH / "contracts" / contest_id
    if not contracts_dir.exists():
        return []

    results = []
    pattern = rf'function\s+{re.escape(function_name)}\s*\('

    for sol_file in contracts_dir.rglob("*.sol"):
        try:
            with open(sol_file, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f, 1):
                    if re.search(pattern, line):
                        rel_path = sol_file.relative_to(contracts_dir)
                        results.append((str(rel_path), i))
        except Exception:
            pass

    return results


def process_bug(bug: BugInfo) -> BugInfo:
    """Process a single bug to extract location info"""
    report_path = WEB3BUGS_PATH / "reports" / f"{bug.contest_id}.md"

    if not report_path.exists():
        return bug

    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            report_content = f.read()
    except Exception:
        return bug

    # Extract bug section
    section = extract_bug_section(report_content, bug.bug_id)
    if not section:
        return bug

    # Extract code blocks
    code_blocks = extract_code_blocks(section)
    if code_blocks:
        bug.code_snippet = code_blocks[0][:500]  # First 500 chars

    # Extract file info from GitHub links
    file_infos = extract_github_file_info(section)
    if file_infos:
        bug.file_name = file_infos[0][0]
        bug.line_start = file_infos[0][1]
        bug.line_end = file_infos[0][2]

    # Extract function names and try to find in contracts
    if not bug.line_start:
        function_names = extract_function_names(section)
        for func_name in function_names:
            locations = find_function_in_contracts(bug.contest_id, func_name)
            if locations:
                bug.file_name = locations[0][0]
                bug.line_start = locations[0][1]
                bug.function_name = func_name
                break

    return bug


def main():
    print("Loading S6-* bugs from bugs.csv...")
    bugs = load_s6_bugs()
    print(f"Found {len(bugs)} S6-* bugs")

    print("\nProcessing bugs to extract locations...")
    processed_bugs = []
    for i, bug in enumerate(bugs):
        print(f"  [{i+1}/{len(bugs)}] Contest {bug.contest_id} - {bug.bug_id}...", end=" ")
        processed_bug = process_bug(bug)
        processed_bugs.append(processed_bug)

        if processed_bug.file_name:
            loc = f"{processed_bug.file_name}"
            if processed_bug.line_start:
                loc += f":{processed_bug.line_start}"
                if processed_bug.line_end and processed_bug.line_end != processed_bug.line_start:
                    loc += f"-{processed_bug.line_end}"
            print(f"Found: {loc}")
        else:
            print("No location found")

    # Generate report
    output_file = OUTPUT_PATH / "Web3Bugs_S6_BugLocations.md"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Web3Bugs S6-* Bug Locations\n\n")
        f.write(f"> Total: {len(processed_bugs)} bugs\n\n")

        # Group by S6 subcategory
        categories = {
            'S6-1': 'Incorrect Calculating Order',
            'S6-2': 'Unexpected Return Value',
            'S6-3': 'Wrong Numbers in Calculation',
            'S6-4': 'Other Accounting Errors'
        }

        for cat, cat_name in categories.items():
            cat_bugs = [b for b in processed_bugs if b.bug_label == cat]
            if not cat_bugs:
                continue

            f.write(f"## {cat}: {cat_name} ({len(cat_bugs)} bugs)\n\n")
            f.write("| # | Contest | Bug | Description | File | Lines | Function |\n")
            f.write("|---|---------|-----|-------------|------|-------|----------|\n")

            for i, bug in enumerate(cat_bugs, 1):
                file_info = bug.file_name or "-"
                line_info = "-"
                if bug.line_start:
                    line_info = str(bug.line_start)
                    if bug.line_end and bug.line_end != bug.line_start:
                        line_info += f"-{bug.line_end}"
                func_info = bug.function_name or "-"
                desc = bug.description[:50] + "..." if len(bug.description) > 50 else bug.description

                f.write(f"| {i} | {bug.contest_id} | {bug.bug_id} | {desc} | {file_info} | {line_info} | {func_info} |\n")

            f.write("\n")

        # Summary stats
        found_count = sum(1 for b in processed_bugs if b.file_name)
        line_count = sum(1 for b in processed_bugs if b.line_start)

        f.write("---\n\n")
        f.write("## Summary\n\n")
        f.write(f"- Total S6-* bugs: {len(processed_bugs)}\n")
        f.write(f"- File location found: {found_count} ({100*found_count//len(processed_bugs)}%)\n")
        f.write(f"- Line numbers found: {line_count} ({100*line_count//len(processed_bugs)}%)\n")

    print(f"\nOutput written to: {output_file}")

    # Also save as JSON for later use
    import json
    json_output = OUTPUT_PATH / "Web3Bugs_S6_BugLocations.json"

    json_data = []
    for bug in processed_bugs:
        json_data.append({
            'contest_id': bug.contest_id,
            'bug_id': bug.bug_id,
            'bug_label': bug.bug_label,
            'description': bug.description,
            'reference': bug.reference,
            'file_name': bug.file_name,
            'function_name': bug.function_name,
            'line_start': bug.line_start,
            'line_end': bug.line_end,
        })

    with open(json_output, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)

    print(f"JSON output written to: {json_output}")


if __name__ == "__main__":
    main()
