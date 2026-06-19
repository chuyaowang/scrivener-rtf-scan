import argparse
import sys
from pathlib import Path

from .markers import extract_markers
from .bib import index_bib, match_reference
from .render import render_with_pandoc
from .sanitize import sanitize_rtf
from .splice import splice_document

STYLES_DIR = Path(__file__).resolve().parent.parent / "styles"


def resolve_style(style):
    p = Path(style)
    if p.suffix == ".csl" and p.exists():
        return str(p)
    cand = STYLES_DIR / f"{style}.csl"
    if cand.exists():
        return str(cand)
    available = sorted(s.stem for s in STYLES_DIR.glob("*.csl"))
    sys.exit(f"Unknown style '{style}'. Available: {', '.join(available)}")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="rtf-cite")
    ap.add_argument("input")
    ap.add_argument("--bib", required=True)
    ap.add_argument("--style", default="nature")
    ap.add_argument("-o", "--output")
    args = ap.parse_args(argv)

    csl = resolve_style(args.style)
    rtf = Path(args.input).read_text(encoding="latin-1")
    markers = extract_markers(rtf)
    index = index_bib(args.bib)

    spans, groups, citations = [], [], {}
    unmatched = []
    for i, m in enumerate(markers):
        keys = []
        for ref in m.references:
            key = match_reference(ref, index)
            if key is None:
                unmatched.append(f'{ref.author_phrase}, "{ref.title}", {ref.year}')
            else:
                keys.append(key)
        spans.append((m.start, m.end))
        if keys:
            groups.append((i, keys))

    rendered, bibliography = render_with_pandoc(
        [g[1] for g in groups], args.bib, csl)
    # map render index -> marker index
    for render_idx, (marker_idx, _keys) in enumerate(groups):
        citations[marker_idx] = sanitize_rtf(rendered.get(render_idx, ""))
    bibliography = sanitize_rtf(bibliography)

    out_rtf = splice_document(rtf, spans, citations, bibliography)
    out_path = args.output or str(Path(args.input).with_name(
        Path(args.input).stem + "_cited.rtf"))
    Path(out_path).write_text(out_rtf, encoding="latin-1")

    if unmatched:
        sys.stderr.write("WARNING: unmatched references (left as-is):\n")
        for u in unmatched:
            sys.stderr.write(f"  - {u}\n")
    print(f"Wrote {out_path} ({len(markers)} markers, {len(unmatched)} unmatched)")


if __name__ == "__main__":
    main()
