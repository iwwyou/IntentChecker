#!/usr/bin/env python3
"""
Callee-before-caller order checker for RQ1 contraction .sol files.

Background: this engine's static analyzer processes a contract's functions
top-to-bottom and needs a callee's CFG already built when it resolves a call
inside a caller -- so a contraction file must declare same-file callees
*before* the caller that calls them, even when the original audited source
had them in the opposite order (Solidity itself doesn't care about
declaration order; this engine does). Found and fixed for `web3bugs_16_H_04`
(`getFee`/`applyTrade`, deliberately reordered from the original source) and
`web3bugs_59_H_04` (`_getIndexOfObservation`/`getPegDeltaFrequency`, missed
in the first build -- this script exists because that miss wasn't caught
until the user re-read the file by hand).

Heuristic, not a real Solidity parser: extracts `function <name>(` and
`modifier <name>(` declarations with their line numbers (ignores contract/
library block boundaries -- fine for these small, mostly-single-contract
contraction files, but a false positive is possible if two different
contracts in the same file happen to reuse a function name). For each
declared function, scans its own body span (start of this declaration to the
start of the next top-level function/modifier declaration) for bare calls
`name(` to any OTHER declared name in the file, and separately scans each
function's modifier-list (the text between its `)` and its `{`) for
references to declared modifiers. Flags any callee whose declaration line is
*after* the caller's declaration line.

Does NOT understand: calls made via `this.foo()`, calls through inherited
base-contract functions defined in a separate pkl'd Dependencies file
(those are resolved by the analyzer independently of file position and are
out of scope here -- see `web3bugs_3_H_05`'s `RoleAware`/`PriceAware`),
library `using X for Y` calls, or interface/external casts (`IFoo(x).bar()`
is correctly ignored since `bar` is not a bare identifier call).

Usage:
    python check_callee_order.py                    # check every .sol in target_contracts_contraction/
    python check_callee_order.py <path/to/file.sol>  # check one file
    python check_callee_order.py <case_id>           # e.g. web3bugs_59_H_04
"""

import re
import sys
import pathlib

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

BASE = pathlib.Path(__file__).parent
CONTRACTION_DIR = BASE.parent.parent / "evaluation" / "RQ1" / "target_contracts_contraction"

DECL_RE = re.compile(
    r"^\s*(function|modifier)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", re.MULTILINE
)
CALL_RE_TMPL = r"(?<![A-Za-z0-9_.]){name}\s*\("


def strip_comments(src: str) -> str:
    src = re.sub(r"//[^\n]*", "", src)
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.DOTALL)
    return src


def check_file(path: pathlib.Path):
    src = strip_comments(path.read_text(encoding="utf-8"))
    lines = src.splitlines()

    decls = []  # (name, kind, line_idx, char_offset)
    for m in DECL_RE.finditer(src):
        kind, name = m.group(1), m.group(2)
        line_idx = src[: m.start()].count("\n")
        decls.append({"name": name, "kind": kind, "line": line_idx, "start": m.start()})

    if not decls:
        return []

    decls.sort(key=lambda d: d["start"])
    names = {d["name"] for d in decls}
    first_line_of = {}
    for d in decls:
        first_line_of.setdefault(d["name"], d["line"])

    findings = []
    for i, d in enumerate(decls):
        body_start = d["start"]
        body_end = decls[i + 1]["start"] if i + 1 < len(decls) else len(src)
        body = src[body_start:body_end]

        # header span: from this decl's own "(" to its "{" (or ";" for interface
        # decls with no body) -- this is where modifier references live.
        header_end_paren = body.find(")")
        brace_idx = body.find("{")
        header = body[:brace_idx] if brace_idx != -1 else body

        for other in names:
            if other == d["name"]:
                continue
            callee_line = first_line_of[other]
            if callee_line <= d["line"]:
                continue  # callee already declared before this caller -- fine
            call_re = re.compile(CALL_RE_TMPL.format(name=re.escape(other)))
            if call_re.search(body):
                findings.append(
                    {
                        "caller": d["name"],
                        "caller_line": d["line"] + 1,
                        "callee": other,
                        "callee_line": callee_line + 1,
                        "file": path.name,
                    }
                )
    return findings


def main():
    args = sys.argv[1:]
    if not args:
        targets = sorted(CONTRACTION_DIR.glob("*.sol"))
    else:
        targets = []
        for a in args:
            p = pathlib.Path(a)
            if p.is_file():
                targets.append(p)
            else:
                cand = CONTRACTION_DIR / f"{a}.sol"
                if cand.exists():
                    targets.append(cand)
                else:
                    print(f"! could not resolve {a!r} to a file", file=sys.stderr)

    any_findings = False
    for t in targets:
        findings = check_file(t)
        if findings:
            any_findings = True
            print(f"\n{t.name}:")
            for f in findings:
                print(
                    f"  [ORDER] {f['caller']} (line {f['caller_line']}) calls "
                    f"{f['callee']}, but {f['callee']} is declared LATER "
                    f"(line {f['callee_line']}) -- move {f['callee']} above {f['caller']}."
                )

    if not any_findings:
        print(f"OK -- no callee-after-caller ordering issues found in {len(targets)} file(s).")
    return 1 if any_findings else 0


if __name__ == "__main__":
    sys.exit(main())
