#!/usr/bin/env python3
"""
Structural completeness checker for RQ1/RQ2 case analysis.md files.

Checks each `<case_id>/analysis.md` under this directory against README.md
section 10's required per-case record fields. Purely structural: flags a
field as missing if no recognizable mention is found, and flags a small set
of known-stale terms left over from earlier methodology revisions.

Does NOT check semantic correctness (e.g. whether "Relevant statements"
correctly includes/excludes the target statement, or whether a count is
right) - that is Agent B's / the user's job. This only catches "the field
isn't there at all" and "this case is still using an old field name."

Usage:
    python check_case_completeness.py            # check all case dirs
    python check_case_completeness.py <case_id>   # check one case
"""

import re
import sys
import pathlib

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

BASE = pathlib.Path(__file__).parent

# README §10 fields required in every case record, matched loosely against
# the raw markdown (case-insensitive). Order follows §10.
REQUIRED_FIELDS = [
    ("R1-1 (reported/intended behavior)", r"R1-1\b"),
    ("R1-3 (alternatives considered)",    r"R1-3\b"),
    ("R1-4 (During/Post + why)",          r"R1-4\b"),
    ("R1-5 (relation form)",              r"R1-5\b"),
    ("R1-6 (target annotation)",          r"R1-6\b"),
    ("R1-7 (expressibility)",             r"R1-7\b"),
    ("Expressible: Yes/No",               r"Expressible\s*[:=—-]\s*\**\s*(Yes|No)"),
    ("Quantified property instantiated: Yes/No",
                                           r"Quantified property instantiated\s*:\s*(Yes|No)"),
    ("Usable/Unusable (§5)",         r"\b(Usable|Unusable)\b"),
]

# README §6 RQ2-A sub-fields, required only when Expressible: Yes.
# Patterns are deliberately loose (don't require README's exact wording) -
# stale-terminology detection below handles catching old field names.
RQ2A_FIELDS = [
    ("Relevant statements",
        r"Relevant statements"),
    ("Unique relevant program values",
        r"Unique relevant (program )?values"),
    ("Additional functions required",
        r"Additional functions (required|inspected)"),
    ("Additional protocol/application-specific contracts/libraries required",
        r"Additional[^.\n]{0,60}(contracts?/librar|librar[^.\n]{0,20}contracts?)"),
    ("Context breadth",
        r"Context breadth"),
    ("External specification required",
        r"External specification required"),
]

# Known-stale terms from earlier methodology revisions (README change log).
# A hit here means the section exists but under an old name/concept -
# reported separately from MISSING so it's clear the content is present
# but needs a rename/rewrite, not fresh authoring.
STALE_TERMS = [
    (r"Additional functions inspected\b",
        "README §6 renamed this to 'Additional functions required'"),
    (r"Additional contracts/libraries(?!\s+required)",
        "README §6 renamed this to 'Additional protocol/application-specific "
        "contracts/libraries required'"),
    (r"\bbug[- ]awareness\b",
        "old L5 concept, retired per README §0/§3 - should not appear in a live record"),
    (r"Relevant control predicates\s*[:—-]",
        "README §6 dropped this as a separately counted metric (folded into "
        "'Relevant statements' with an inline note where needed)"),
    (r"operand-defining\s*\(a/b\)|soundness-justifying\s*\(c\)",
        "README §6 dropped the formal operand-defining/soundness-justifying "
        "labeling requirement (inline notes only, no formal taxonomy)"),
]

# Words that, if found within ~40 chars before a bare "L5" mention, mark it as
# an acknowledged historical reference rather than a live leftover label
# (e.g. "the old L1-L5 bucket", "retired L5 classification").
_L5_HISTORICAL_CONTEXT = re.compile(
    r"\b(old|retired|former|historical|superseded|used to|no longer)\b",
    re.IGNORECASE,
)


def _find_live_l5_references(text: str) -> bool:
    """True if a bare 'L5' appears without nearby historical-context wording."""
    for m in re.finditer(r"\bL5\b", text):
        window_start = max(0, m.start() - 40)
        window = text[window_start:m.start()]
        if not _L5_HISTORICAL_CONTEXT.search(window):
            return True
    return False


def check_case(path: pathlib.Path) -> dict:
    text = path.read_text(encoding="utf-8")
    result = {"missing": [], "stale": [], "expressible": None}

    for label, pattern in REQUIRED_FIELDS:
        if not re.search(pattern, text, re.IGNORECASE):
            result["missing"].append(label)

    m = re.search(r"Expressible\s*[:=—-]\s*\**\s*(Yes|No)", text, re.IGNORECASE)
    if m:
        result["expressible"] = m.group(1).capitalize()

    if result["expressible"] == "Yes":
        for label, pattern in RQ2A_FIELDS:
            if not re.search(pattern, text, re.IGNORECASE):
                result["missing"].append(f"RQ2-A: {label}")

    for pattern, note in STALE_TERMS:
        if re.search(pattern, text, re.IGNORECASE):
            result["stale"].append(note)

    if _find_live_l5_references(text):
        result["stale"].append(
            "bare 'L5' reference without nearby historical-context wording "
            "(old/retired/former/...) - verify this isn't a leftover live label"
        )

    return result


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None

    case_dirs = sorted(
        p for p in BASE.iterdir()
        if p.is_dir() and (p / "analysis.md").exists()
    )
    if only:
        # exact match first, then tolerate a missing numeric prefix (folders are
        # now named "NN_<case_id>" for at-a-glance ordering - see case_progress.md)
        matched = [d for d in case_dirs if d.name == only]
        if not matched:
            matched = [d for d in case_dirs if d.name == only or d.name.split("_", 1)[-1] == only]
        case_dirs = matched
        if not case_dirs:
            sys.exit(f"No analysis.md found for case '{only}'")

    if not case_dirs:
        sys.exit("No case directories with analysis.md found.")

    any_issue = False
    for d in case_dirs:
        result = check_case(d / "analysis.md")
        header = f"{d.name}/analysis.md"
        if result["expressible"] is not None:
            header += f"  (Expressible: {result['expressible']})"

        if result["missing"] or result["stale"]:
            any_issue = True
            print(f"\n{header}")
            for m in result["missing"]:
                print(f"  MISSING: {m}")
            for s in result["stale"]:
                print(f"  STALE:   {s}")
        else:
            print(f"{header}: OK")

    print()
    if any_issue:
        print("Issues found above. MISSING = no recognizable mention of a required "
              "field; STALE = field present but under a retired name/concept.")
    else:
        print("All checked case files pass structural completeness.")


if __name__ == "__main__":
    main()
