#!/usr/bin/env bash
#
# build.sh -- one-shot rebuild for a Scrivener-compiled LaTeX manuscript.
#
# Scrivener overwrites its compiled .tex on every compile, which brings the
# RTF-scan citation markers back. This re-inserts the citations and rebuilds
# both output formats:
#
#   <stem>.tex --rtf-cite--> <stem>_cited.tex --latexmk--> <stem>_cited.pdf
#                                             --pandoc---> <stem>_cited.docx
#
# References are audited statically before the build (see check_refs.py): an
# unmatched \ref is fatal, an unreferenced figure or table is a warning.
#
# The Scrivener-owned .tex is only ever read, never written, so this is safe
# to re-run after every compile.
#
# Note: latexmk often exits nonzero on benign warnings while still producing a
# good PDF, so its exit code alone is not a verdict. But file existence alone
# isn't either: a pdflatex crash mid-write leaves a truncated PDF behind, which
# used to let a broken build report success. So the PDF is judged on three
# things -- no hard failure in the log, the file exists, and it ends in %%EOF.
#
# With --two-stage, latexmk resolves references with figures in draft mode
# (correct-sized boxes, no embedded pixels) and a single final pdflatex pass
# embeds them, so the large PDF is written once instead of on every pass.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

BIB=""
STYLE="$REPO_ROOT/styles/nature.csl"
ENV_NAME="rtf-cite"
CITE_CMD="citep"
DO_PDF=1
DO_DOCX=1
DO_REF_CHECK=1
TWO_STAGE=0
INPUT=""

die()  { printf 'error: %s\n' "$*" >&2; exit 1; }
warn() { printf 'warning: %s\n' "$*" >&2; }
step() { printf '\n==> %s\n' "$*"; }

usage() {
  cat <<'EOF'
Usage: scripts/build.sh [options] <input.tex>

Insert natbib citations into a Scrivener-compiled .tex, then build a PDF
(latexmk) and a .docx (pandoc).

Options:
  -b, --bib FILE       BibTeX file            (default: <repo>/export.bib)
  -s, --style FILE     CSL style for the docx (default: <repo>/styles/nature.csl)
  -e, --env NAME       Conda env providing rtf-cite, used only if rtf-cite is
                       not already on PATH    (default: rtf-cite)
  -c, --cite-command C natbib command         (default: citep)
      --no-pdf         Skip the PDF build
      --no-docx        Skip the docx build
      --no-ref-check   Don't fail on unmatched \ref targets (draft builds)
      --two-stage      Resolve refs with figures in draft, then embed them on a
      --fast           single final pass. Writes the large PDF once instead of
                       on every latexmk pass -- faster for high-res figures.
  -h, --help           Show this help

Example:
  scripts/build.sh master_thesis.tex/master_thesis.tex
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -b|--bib)          BIB="${2:-}";      shift 2 ;;
    -s|--style)        STYLE="${2:-}";    shift 2 ;;
    -e|--env)          ENV_NAME="${2:-}"; shift 2 ;;
    -c|--cite-command) CITE_CMD="${2:-}"; shift 2 ;;
    --no-pdf)          DO_PDF=0;          shift ;;
    --no-docx)         DO_DOCX=0;         shift ;;
    --no-ref-check)    DO_REF_CHECK=0;    shift ;;
    --two-stage|--fast) TWO_STAGE=1;      shift ;;
    -h|--help)         usage; exit 0 ;;
    -*)                usage >&2; die "unknown option: $1" ;;
    *)                 INPUT="$1";        shift ;;
  esac
done

[[ -n "$INPUT" ]] || { usage >&2; exit 1; }
[[ -f "$INPUT" ]] || die "input not found: $INPUT"

BIB="${BIB:-$REPO_ROOT/export.bib}"
[[ -f "$BIB" ]] || die "bib not found: $BIB (pass one with --bib)"

# Absolute paths: we cd into the tex directory before building.
abspath() { printf '%s/%s\n' "$(cd "$(dirname "$1")" && pwd)" "$(basename "$1")"; }
INPUT="$(abspath "$INPUT")"
BIB="$(abspath "$BIB")"
if (( DO_DOCX )); then
  [[ -f "$STYLE" ]] || die "CSL style not found: $STYLE"
  STYLE="$(abspath "$STYLE")"
fi

TEX_DIR="$(dirname "$INPUT")"
STEM="$(basename "$INPUT" .tex)"
JOB="${STEM}_cited"

# rtf-cite lives in a conda env; prefer PATH, fall back to `conda run`.
run_rtf_cite() {
  if command -v rtf-cite >/dev/null 2>&1; then
    rtf-cite "$@"
  elif command -v conda >/dev/null 2>&1; then
    conda run --no-capture-output -n "$ENV_NAME" rtf-cite "$@"
  else
    die "rtf-cite not on PATH and conda not found; activate the '$ENV_NAME' env"
  fi
}

step "Inserting citations -> $JOB.tex"
run_rtf_cite "$INPUT" --bib "$BIB" --cite-command "$CITE_CMD" \
  -o "$TEX_DIR/$JOB.tex" || die "citation step failed"

# Cheaper to catch a dangling \ref here than to find it 90 seconds into latexmk.
# Scanned on the Scrivener input, not the _cited.tex, so the reported line
# numbers match the file you actually edit (rtf-cite substitutes in place).
step "Checking references"
CHECKER="$REPO_ROOT/scripts/check_refs.py"
if (( DO_REF_CHECK )) && [[ -f "$CHECKER" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    python3 "$CHECKER" "$INPUT" \
      || die "unmatched references (fix them, or pass --no-ref-check)"
  else
    warn "python3 not found -- skipping reference check"
  fi
else
  printf '  skipped\n'
fi

# bibtex resolves \bibliography{export.bib} relative to the compile directory.
cp "$BIB" "$TEX_DIR/"
BIB_LOCAL="$(basename "$BIB")"

cd "$TEX_DIR" || die "cannot cd into $TEX_DIR"

if (( DO_PDF )); then
  step "Building PDF (latexmk)"
  command -v latexmk >/dev/null 2>&1 || die "latexmk not found on PATH"
  rm -f "$JOB.pdf"

  if (( TWO_STAGE )); then
    command -v pdflatex >/dev/null 2>&1 || die "pdflatex not found on PATH"

    # Stage 1: stabilize .aux/.toc/.bbl with graphicx in draft mode. Draft
    # reserves each figure's true-size box -- so pagination and every \ref page
    # number are identical to the final -- but skips embedding the image data,
    # so these repeated passes write a tiny PDF instead of the full one.
    # \PassOptionsToPackage is queued before \documentclass loads graphicx.
    printf '  stage 1/2: resolving references (figures in draft)\n'
    latexmk -pdf -interaction=nonstopmode \
      -pdflatex='pdflatex -interaction=nonstopmode %O "\PassOptionsToPackage{draft}{graphicx}\input{%S}"' \
      "$JOB.tex" > "$JOB.build.log" 2>&1
    if grep -q 'Errors, so I did not complete making targets' "$JOB.build.log"; then
      die "latexmk failed during stage 1 (reference resolution); see $TEX_DIR/$JOB.build.log"
    fi

    # Drop the draft PDF so a stage-2 crash can't pass the checks below by
    # leaving the tiny draft file (which has its own valid %%EOF) behind.
    rm -f "$JOB.pdf"

    # Stage 2: one plain pdflatex pass. The .aux is already stable, so a single
    # run embeds every figure at full resolution and writes the large PDF once.
    printf '  stage 2/2: embedding figures at full resolution\n'
    pdflatex -interaction=nonstopmode "$JOB.tex" >> "$JOB.build.log" 2>&1
    pdf_status=$?
    if grep -q 'no output PDF file produced' "$JOB.build.log"; then
      die "pdflatex failed during stage 2 (figure embedding); see $TEX_DIR/$JOB.build.log"
    fi
  else
    latexmk -pdf -interaction=nonstopmode "$JOB.tex" > "$JOB.build.log" 2>&1
    pdf_status=$?

    # latexmk prints this only when a target genuinely failed to build; benign
    # warnings never produce it, so it separates real failures from noise.
    if grep -q 'Errors, so I did not complete making targets' "$JOB.build.log"; then
      die "latexmk failed to build the PDF; see $TEX_DIR/$JOB.build.log"
    fi
  fi

  (( pdf_status == 0 )) \
    || warn "PDF builder exited $pdf_status (warnings only) -- verifying output"

  [[ -f "$JOB.pdf" ]] || die "no PDF produced; see $TEX_DIR/$JOB.build.log"

  # A complete PDF ends in %%EOF. A pdflatex that died mid-write does not.
  tail -c 1024 "$JOB.pdf" | grep -qa '%%EOF' \
    || die "PDF is truncated, no %%EOF (pdflatex likely crashed mid-write); see $TEX_DIR/$JOB.build.log"
fi

if (( DO_DOCX )); then
  step "Building docx (pandoc)"
  command -v pandoc >/dev/null 2>&1 || die "pandoc not found on PATH"
  rm -f "$JOB.docx"
  pandoc "$JOB.tex" --citeproc --bibliography="$BIB_LOCAL" --csl="$STYLE" \
    -o "$JOB.docx" || die "pandoc failed"
  [[ -f "$JOB.docx" ]] || die "no docx produced"
fi

step "Done"
(( DO_PDF ))  && printf '  PDF  %s\n'  "$TEX_DIR/$JOB.pdf"
(( DO_DOCX )) && printf '  DOCX %s\n' "$TEX_DIR/$JOB.docx"
exit 0