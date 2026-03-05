"""
Contraction 전처리 스크립트
- web3bugs .sol 파일에서 import, 주석, constructor, SPDX 라인 제거
- target_contracts_contraction/ 폴더의 web3bugs_*.sol 파일 대상
- dependencies/ 폴더는 건드리지 않음
"""

from __future__ import annotations
import re, pathlib, sys, argparse

# ── 대상 디렉토리 ──
BASE_DIR = pathlib.Path(__file__).parent / "target_contracts_contraction"

# ── 패턴 ──
RE_SPDX       = re.compile(r"^\s*//\s*SPDX-License-Identifier.*$")
RE_IMPORT     = re.compile(r"^\s*import\s+")
RE_PRAGMA     = re.compile(r"^\s*pragma\s+")
RE_STANDALONE = re.compile(r"^\s*(//|/\*\*|\*\s|/\*|\*/)")  # 독립 주석 라인
RE_INLINE_CMT = re.compile(r"\s*(//(?!/\s*@(?:During|Post|StateVar|LocalVar|GlobalVar)).*)$")  # intent annotation은 보존
RE_BLOCK_CMT_SINGLE = re.compile(r"/\*.*?\*/")  # 한 줄 안의 /* ... */


def is_standalone_comment(line: str) -> bool:
    """순수 주석 라인인지 판별 (코드 없이 주석만)"""
    stripped = line.strip()
    if not stripped:
        return False
    # // 또는 /// 로 시작
    if stripped.startswith("//"):
        return True
    # /* 로 시작하는 블록 주석 시작
    if stripped.startswith("/*"):
        return True
    # * 로 시작 (블록 주석 중간)
    if stripped.startswith("*"):
        return True
    return False


def strip_inline_comment(line: str) -> str:
    """코드 뒤의 인라인 주석 제거 (문자열 리터럴 안의 // 는 보존)"""
    # intent annotation 주석은 보존
    stripped = line.strip()
    if re.search(r"//\s*@(During|Post|StateVar|LocalVar|GlobalVar)", line):
        return line

    result = []
    in_string = None  # None, "'", '"'
    i = 0
    while i < len(line):
        ch = line[i]

        # 문자열 리터럴 처리
        if ch in ('"', "'") and in_string is None:
            in_string = ch
            result.append(ch)
            i += 1
            continue
        elif ch == in_string:
            in_string = None
            result.append(ch)
            i += 1
            continue

        if in_string is None:
            # // 발견 → 여기서 잘라냄
            if ch == '/' and i + 1 < len(line) and line[i + 1] == '/':
                break
            # /* 발견 → 같은 줄에 */ 있으면 제거, 없으면 잘라냄
            if ch == '/' and i + 1 < len(line) and line[i + 1] == '*':
                end = line.find("*/", i + 2)
                if end != -1:
                    i = end + 2  # /* ... */ 건너뛰기
                    continue
                else:
                    break

        result.append(ch)
        i += 1

    return "".join(result).rstrip()


def find_constructor_range(lines: list[str]) -> list[tuple[int, int]]:
    """constructor 블록의 시작-끝 인덱스 쌍 반환 (0-based)"""
    ranges = []
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        # constructor 시작 탐지
        if re.match(r"^\s*constructor\s*[\(\{]", stripped) or stripped == "constructor" or stripped.startswith("constructor "):
            start = i
            # brace 카운트로 블록 끝 찾기
            brace_count = 0
            found_open = False
            j = i
            while j < len(lines):
                for ch in lines[j]:
                    if ch == '{':
                        brace_count += 1
                        found_open = True
                    elif ch == '}':
                        brace_count -= 1
                if found_open and brace_count == 0:
                    ranges.append((start, j))
                    i = j + 1
                    break
                j += 1
            else:
                # 끝까지 못찾으면 그냥 넘어감
                i += 1
        else:
            i += 1
    return ranges


def find_block_comment_ranges(lines: list[str]) -> list[tuple[int, int]]:
    """여러 줄 블록 주석 /* ... */ 의 시작-끝 인덱스 쌍 반환"""
    ranges = []
    i = 0
    in_block = False
    start = 0
    while i < len(lines):
        line = lines[i]
        if not in_block:
            # /* 가 있고 같은 줄에 */ 가 없는 경우 → 멀티라인 블록 주석 시작
            idx = line.find("/*")
            if idx != -1:
                # 문자열 리터럴 안인지 간단 체크 (완벽하진 않지만)
                before = line[:idx]
                if before.count('"') % 2 == 0 and before.count("'") % 2 == 0:
                    end_idx = line.find("*/", idx + 2)
                    if end_idx == -1:
                        # 멀티라인 블록 주석 시작
                        in_block = True
                        start = i
                        # 이 줄에 코드가 /* 앞에 있으면 주석 부분만 제거해야 하지만
                        # 간단하게 독립 주석 라인으로 판단
                        if line[:idx].strip() == "":
                            pass  # 순수 주석 시작 라인
        else:
            if "*/" in line:
                in_block = False
                end_idx = line.find("*/")
                after = line[end_idx + 2:].strip()
                if after == "":
                    ranges.append((start, i))
                else:
                    # */ 뒤에 코드가 있으면 시작~i-1 까지만
                    ranges.append((start, i - 1))
        i += 1
    # 닫히지 않은 블록 주석
    if in_block:
        ranges.append((start, len(lines) - 1))
    return ranges


def remove_bare_scoping_blocks(lines: list[str]) -> list[str]:
    """bare scoping block { } 제거 + 내부 코드 dedent 4칸"""
    result = []
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()

        # 단독 '{' 라인 탐지
        if stripped == '{':
            # 이전 비어있지 않은 라인 확인
            prev_line = ""
            for j in range(len(result) - 1, -1, -1):
                if result[j].strip():
                    prev_line = result[j].strip()
                    break

            # 이전 라인이 ';' 또는 ')' + ';' 로 끝나면 bare scoping block
            # (제어문 헤더는 ')' 로 끝나고 ';' 없음, 키워드 단독은 해당 안됨)
            if prev_line.endswith(';') or prev_line.endswith('}'):
                # 매칭되는 '}' 찾기
                brace_indent = len(lines[i]) - len(lines[i].lstrip())
                brace_count = 1
                block_start = i + 1
                block_end = None
                j = i + 1
                while j < len(lines):
                    for ch in lines[j]:
                        if ch == '{':
                            brace_count += 1
                        elif ch == '}':
                            brace_count -= 1
                    if brace_count == 0:
                        block_end = j
                        break
                    j += 1

                if block_end is not None:
                    # 내부 코드 dedent (4 spaces)
                    for k in range(block_start, block_end):
                        line = lines[k]
                        if line.strip() == '':
                            result.append(line)
                            continue
                        line_indent = len(line) - len(line.lstrip())
                        if line_indent >= brace_indent + 4:
                            result.append(' ' * brace_indent + line[brace_indent + 4:])
                        else:
                            result.append(line)
                    i = block_end + 1  # skip closing '}'
                    continue

        result.append(lines[i])
        i += 1

    return result


RE_SINGLE_IF = re.compile(
    r"^(\s*)"                    # (1) 들여쓰기
    r"(if\s*\(.*\))\s+"         # (2) if (조건)
    r"(.+;)\s*$"                 # (3) statement;
)


def expand_single_line_if(lines: list[str]) -> list[str]:
    """if (cond) stmt; → if (cond) {\n    stmt;\n}"""
    result = []
    for line in lines:
        m = RE_SINGLE_IF.match(line)
        if m:
            indent = m.group(1)
            condition = m.group(2)
            statement = m.group(3)
            result.append(f"{indent}{condition} {{")
            result.append(f"{indent}    {statement}")
            result.append(f"{indent}}}")
        else:
            result.append(line)
    return result


def collapse_empty_lines(lines: list[str]) -> list[str]:
    """연속 빈 줄을 하나로 축소, 파일 끝 빈 줄 제거"""
    result = []
    prev_empty = False
    for line in lines:
        is_empty = line.strip() == ""
        if is_empty:
            if not prev_empty:
                result.append("")
            prev_empty = True
        else:
            result.append(line)
            prev_empty = False
    # 파일 끝/시작 빈 줄 제거
    while result and result[-1].strip() == "":
        result.pop()
    while result and result[0].strip() == "":
        result.pop(0)
    return result


def preprocess(source: str) -> str:
    """전처리 수행: import, 주석, constructor, SPDX 제거"""
    lines = source.splitlines()

    # 1단계: constructor 범위 표시
    constructor_ranges = find_constructor_range(lines)
    constructor_lines = set()
    for start, end in constructor_ranges:
        for i in range(start, end + 1):
            constructor_lines.add(i)

    # 2단계: 멀티라인 블록 주석 범위 표시
    block_comment_ranges = find_block_comment_ranges(lines)
    block_comment_lines = set()
    for start, end in block_comment_ranges:
        for i in range(start, end + 1):
            block_comment_lines.add(i)

    # 3단계: 한 줄씩 처리
    result = []
    for i, line in enumerate(lines):
        # constructor 블록 → 제거
        if i in constructor_lines:
            continue

        # 멀티라인 블록 주석 → 제거
        if i in block_comment_lines:
            continue

        stripped = line.strip()

        # SPDX → 제거
        if RE_SPDX.match(line):
            continue

        # import → 제거
        if RE_IMPORT.match(stripped):
            continue

        # 독립 주석 라인 → 제거
        if is_standalone_comment(stripped):
            continue

        # 인라인 주석 제거
        processed = strip_inline_comment(line)

        # 빈 줄이 된 경우도 포함 (collapse에서 처리)
        result.append(processed)

    # 4단계: bare scoping block 제거 + dedent
    result = remove_bare_scoping_blocks(result)

    # 5단계: single-line if 확장 → if () {\n    stmt;\n}
    result = expand_single_line_if(result)

    # 6단계: 빈 줄 정리
    result = collapse_empty_lines(result)

    return "\n".join(result) + "\n"


def process_file(filepath: pathlib.Path, dry_run: bool = False) -> dict:
    """단일 파일 전처리. 통계 반환."""
    original = filepath.read_text(encoding="utf-8")
    original_lines = original.splitlines()
    processed = preprocess(original)
    processed_lines = processed.splitlines()

    stats = {
        "file": filepath.name,
        "original_lines": len(original_lines),
        "processed_lines": len(processed_lines),
        "removed": len(original_lines) - len(processed_lines),
    }

    if not dry_run:
        filepath.write_text(processed, encoding="utf-8")

    return stats


def main():
    parser = argparse.ArgumentParser(description="Contraction 전처리: import/주석/constructor 제거")
    parser.add_argument("--dry-run", action="store_true", help="실제 파일 수정 없이 통계만 출력")
    parser.add_argument("--file", type=str, help="특정 파일만 처리 (e.g., web3bugs_35_H_12.sol)")
    args = parser.parse_args()

    if not BASE_DIR.exists():
        sys.exit(f"디렉토리 없음: {BASE_DIR}")

    if args.file:
        files = [BASE_DIR / args.file]
        if not files[0].exists():
            sys.exit(f"파일 없음: {files[0]}")
    else:
        files = sorted(BASE_DIR.glob("web3bugs_*.sol"))

    if not files:
        sys.exit("처리할 web3bugs_*.sol 파일이 없습니다.")

    print(f"{'파일':<35} {'원본':>6} {'결과':>6} {'제거':>6}")
    print("-" * 60)

    total_original = 0
    total_processed = 0
    for f in files:
        stats = process_file(f, dry_run=args.dry_run)
        total_original += stats["original_lines"]
        total_processed += stats["processed_lines"]
        print(f"{stats['file']:<35} {stats['original_lines']:>6} {stats['processed_lines']:>6} {stats['removed']:>6}")

    print("-" * 60)
    print(f"{'합계':<35} {total_original:>6} {total_processed:>6} {total_original - total_processed:>6}")
    print(f"\n총 {len(files)}개 파일 처리 {'(dry-run)' if args.dry_run else '완료'}")


if __name__ == "__main__":
    main()
