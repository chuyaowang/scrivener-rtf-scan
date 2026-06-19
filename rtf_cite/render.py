import re
import subprocess


def build_markdown(groups):
    """groups: list of lists of cite keys, one per marker (in document order)."""
    lines = []
    for i, keys in enumerate(groups):
        cites = "; ".join(f"@{k}" for k in keys)
        lines.append(f"ZZCITE{i}ZZ [{cites}]\n")
    lines.append("ZZBIBSTARTZZ\n")
    return "\n".join(lines)


def _strip_rtf_wrapper(rtf):
    # Keep the whole document string; sentinels below locate content within it.
    start = rtf.find(r"\rtf1")
    return rtf[start:] if start != -1 else rtf


def render_with_pandoc(groups, bib_path, csl_path):
    md = build_markdown(groups)
    out = subprocess.run(
        ["pandoc", "--citeproc", "--csl", csl_path,
         "--bibliography", bib_path, "-f", "markdown", "-t", "rtf",
         "--wrap=none"],
        input=md, capture_output=True, text=True, check=True,
    ).stdout
    body = _strip_rtf_wrapper(out)
    citations = {}
    for i in range(len(groups)):
        m = re.search(rf"ZZCITE{i}ZZ\s*(.*?)\\par", body, re.DOTALL)
        citations[i] = m.group(1).strip() if m else ""
    bib_m = re.search(r"ZZBIBSTARTZZ\s*\\par(.*)", body, re.DOTALL)
    bibliography = bib_m.group(1) if bib_m else ""
    # The capture starts just after the ZZBIBSTARTZZ paragraph's \par, so it
    # opens with that paragraph group's closing '}'. Drop that leading brace.
    bibliography = bibliography.lstrip()
    if bibliography.startswith("}"):
        bibliography = bibliography[1:].lstrip()
    # Trim the final closing brace of the RTF document from the bib tail.
    bibliography = bibliography.rstrip()
    if bibliography.endswith("}") and bibliography.count("{") < bibliography.count("}"):
        bibliography = bibliography[:-1].rstrip()
    return citations, bibliography
