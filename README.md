# rtf-cite

Replace auto-generated `\{Author, "Title", Year; …\}` markers in an RTF file
with CSL-formatted in-text citations and append a bibliography.

## Setup

```bash
conda env create -f environment.yml
conda activate rtf-cite
pip install -e .
```

Requires `pandoc` 3.x on PATH.

## Usage

```bash
rtf-cite master_thesis.rtf --bib export.bib --style nature -o thesis_cited.rtf
```

- `--style` takes a bundled style name from `styles/` (default `nature`) or a
  path to a `.csl` file.
- Multiple references inside one marker render as a single grouped citation
  (e.g. superscript `1,2,3` or a collapsed range `1-3`).
- Unmatched markers are reported on stderr and left untouched in the output.

## Adding styles

Drop any `.csl` file into `styles/` and pass its filename stem to `--style`.
