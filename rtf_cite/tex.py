"""Replace RTF-scan citation markers in a LaTeX document with natbib commands.

Unlike the RTF path, no CSL rendering or appended bibliography is needed:
natbib formats citations and builds the bibliography at compile time from
\\bibliography{...}. Each marker becomes one grouped \\citep{k1,k2,...} so that
multiple references collapse into a single citation.
"""
from .markers import extract_markers
from .bib import match_reference


def replace_markers_tex(text, index, cite_cmd="citep"):
    """Return (new_text, unmatched) with every marker replaced in place.

    unmatched is a list of "author, \"title\", year" strings for references
    that had no bib match; markers with no matched keys are left untouched.
    """
    markers = extract_markers(text)
    unmatched = []
    # Build (span, replacement) pairs; spliced back-to-front to keep offsets.
    edits = []
    for m in markers:
        keys = []
        for ref in m.references:
            key = match_reference(ref, index)
            if key is None:
                unmatched.append(f'{ref.author_phrase}, "{ref.title}", {ref.year}')
            else:
                keys.append(key)
        if keys:
            edits.append((m.start, m.end, "\\%s{%s}" % (cite_cmd, ",".join(keys))))

    out = text
    for start, end, replacement in sorted(edits, reverse=True):
        out = out[:start] + replacement + out[end:]
    return out, unmatched