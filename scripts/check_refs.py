#!/usr/bin/env python3
"""
check_refs.py -- static cross-reference audit for a Scrivener-compiled thesis.

Two checks, run before latexmk so a dangling \\ref costs a second instead of a
90-second build:

  1. Unmatched references -- a \\ref whose target has no \\label. These print
     "??" in the finished PDF, so they are fatal (exit 1).

  2. Floats that are never referenced -- a figure or table the reader is never
     pointed at, or one carrying no label at all. Advisory only (exit 0).

Float labels are identified by name prefix (fig:, figure:, tab:, table:), not by
figure/table environment membership: the appendix uses \\captionof, which puts
the \\label *after* \\end{figure}, so scoping to the environment would miss it.
Scrivener also auto-labels every section, so prefix matching is what separates
the ~37 real floats from the ~106 section labels that are never cited by design.
"""

import re
import sys
import difflib

REF_CMDS = r"ref|autoref|pageref|eqref|cref|Cref|vref|nameref"
FLOAT_PREFIXES = ("fig:", "figure:", "tab:", "table:")

LABEL_RE = re.compile(r"\\label\{([^}]*)\}")
REF_RE = re.compile(r"\\(?:" + REF_CMDS + r")\{([^}]*)\}")
CAPTION_RE = re.compile(r"\\caption\{|\\captionof\{(?:figure|table)\}")

# How far from a caption to look for its label. The appendix pattern puts the
# label on the very next line; a small window keeps unrelated labels out.
LABEL_WINDOW = 6


def is_float_label(name):
    return name.lower().startswith(FLOAT_PREFIXES)


def snippet(text, width=70):
    """First readable words of a caption, for identifying it in the report."""
    t = re.sub(r"\\[a-zA-Z]+\*?", " ", text)      # drop commands
    t = re.sub(r"[{}\\]", " ", t)                  # drop braces
    t = " ".join(t.split())
    return t[:width] + ("..." if len(t) > width else "")


def main(path):
    try:
        lines = open(path, encoding="utf-8").read().split("\n")
    except OSError as e:
        print(f"error: cannot read {path}: {e}", file=sys.stderr)
        return 2

    labels = {}
    for i, line in enumerate(lines, 1):
        for m in LABEL_RE.finditer(line):
            labels.setdefault(m.group(1), i)

    refs = {}
    for i, line in enumerate(lines, 1):
        for m in REF_RE.finditer(line):
            refs.setdefault(m.group(1), []).append(i)

    float_labels = {n: l for n, l in labels.items() if is_float_label(n)}

    # --- check 1: unmatched references (fatal) --------------------------------
    unmatched = {n: ls for n, ls in refs.items() if n not in labels}

    # --- check 2: floats never referenced (advisory) --------------------------
    unreferenced = sorted(
        (l, n) for n, l in float_labels.items() if n not in refs
    )

    # --- check 2b: captions carrying no label at all (advisory) ---------------
    unlabelled = []
    for i, line in enumerate(lines, 1):
        if not CAPTION_RE.search(line):
            continue
        lo, hi = i - 1, min(len(lines), i + LABEL_WINDOW)
        has_label = any(
            is_float_label(m.group(1))
            for j in range(lo, hi)
            for m in LABEL_RE.finditer(lines[j])
        )
        if not has_label:
            unlabelled.append((i, snippet(line)))

    # --- report ---------------------------------------------------------------
    # Each summary line carries its own denominator and verdict: the three
    # counts measure different populations, so a bare "142 / 38 / 36" reads as
    # unrelated trivia unless each says what it is and whether it passed.
    n_floats = len(float_labels)
    n_float_ok = n_floats - len(unreferenced)
    n_targets = len(refs)
    n_target_ok = n_targets - len(unmatched)
    n_sections = len(labels) - n_floats

    float_issues = []
    if unreferenced:
        float_issues.append(f"{len(unreferenced)} never referenced")
    if unlabelled:
        float_issues.append(f"{len(unlabelled)} with no label")

    rows = [
        ("figures/tables",
         f"{n_floats} defined, {n_float_ok} referenced at least once",
         ", ".join(float_issues) if float_issues else "OK"),
        ("\\ref targets",
         f"{n_targets} used, {n_target_ok} resolved to a label",
         f"{len(unmatched)} UNMATCHED" if unmatched else "OK"),
    ]
    width = max(len(body) for _, body, _ in rows)
    for name, body, verdict in rows:
        print(f"  {name:<14} : {body:<{width}}   {verdict}")
    if n_sections:
        print(f"  ignored: {n_sections} Scrivener section labels")

    if unmatched:
        print(f"\n  UNMATCHED REFERENCES ({len(unmatched)}) "
              f"-- these render as '??' in the PDF:")
        for name in sorted(unmatched, key=lambda n: unmatched[n][0]):
            where = ", ".join(str(l) for l in unmatched[name])
            print(f"    line {where}: \\ref{{{name}}}  -- no such label")
            near = difflib.get_close_matches(name, labels, n=3, cutoff=0.6)
            if near:
                print(f"        did you mean: {', '.join(near)}")

    if unreferenced:
        print(f"\n  floats never referenced ({len(unreferenced)}):")
        for line_no, name in unreferenced:
            print(f"    line {line_no}: \\label{{{name}}}")

    if unlabelled:
        print(f"\n  captions with no float label ({len(unlabelled)}) "
              f"-- cannot be referenced:")
        for line_no, text in unlabelled:
            print(f"    line {line_no}: {text}")


    return 1 if unmatched else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: check_refs.py <file.tex>", file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))