# Scrivener RTF Citation Scanner

A command-line tool (`rtf-cite`) that replaces the plain-text citation
placeholders left by Zotero's **RTF Scan** Quick Copy format with properly
formatted citations. It handles **RTF** (rendering citations with any CSL style
and appending a bibliography) and **LaTeX** (emitting natbib `\citep` commands
for LaTeX to format at compile time).

## Why this exists

This tool is designed for the **Scrivener + Zotero** writing workflow. Zotero
has a built-in **RTF Scan** feature that does the same job, but it **breaks when
a single placeholder contains multiple references** (e.g.
`{Brown et al., "…", 2014; Desai, "…", 2018; Thomson et al., "…", 2016}`).
`rtf-cite` handles those grouped placeholders correctly, collapsing them into a
single grouped citation (e.g. superscript `1,2,3` or a range `1-3`), and is a
drop-in replacement for the final "RTF Scan" step described below.

The tool auto-detects the input format from the file extension:

- **`.rtf`** — replaces markers with CSL-formatted citations and appends a
  bibliography (uses `pandoc` + a bundled `.csl` style).
- **`.tex`** — replaces markers with **natbib** `\cite` commands (no
  bibliography is appended; LaTeX builds it from `\bibliography{...}` at
  compile time). This suits a Scrivener project compiled to LaTeX rather than
  RTF.

## Setup

```bash
conda env create -f environment.yml
conda activate rtf-cite
pip install -e .
```

External requirements depend on what you build:

| You want | You need |
| --- | --- |
| `.rtf` input | `pandoc` 3.x on PATH |
| `.tex` input | nothing extra — citations are inserted as plain text |
| PDF via `scripts/build.sh` | `latexmk` and a LaTeX distribution |
| docx via `scripts/build.sh` | `pandoc` 3.x |

## Usage

```bash
rtf-cite thesis.rtf --bib export.bib --style nature -o thesis_cited.rtf
```

- `--style` takes a bundled style name (default `nature`) or a path to a `.csl`
  file. (Only used for `.rtf` input.)
- Multiple references inside one placeholder render as a single grouped citation
  (e.g. superscript `1,2,3` or a collapsed range `1-3`).
- Unmatched placeholders are reported on stderr and left untouched in the
  output.

### LaTeX / natbib

For a `.tex` input, each placeholder is replaced by a single natbib command,
with multiple references collapsed into one grouped citation:

```bash
rtf-cite thesis.tex --bib export.bib -o thesis_cited.tex
```

- `--cite-command` selects the natbib command (default `citep` for
  parenthetical; use `citet` for textual). A grouped placeholder becomes
  e.g. `\citep{Brown2014,Desai2018,Thomson2016}`.
- No bibliography is appended. Your preamble supplies it — add
  `\usepackage[sort&compress]{natbib}` (so grouped keys sort and compress into
  ranges), and `\bibliographystyle{...}` + `\bibliography{export.bib}` where the
  reference list should appear.
- `--style` is ignored for `.tex` input.

Compile the result the usual way — `pdflatex`, `bibtex`, then `pdflatex` twice,
or just `latexmk -pdf thesis_cited`. `bibtex` resolves `\bibliography{...}`
relative to the compile directory, so keep the `.bib` there (or set
`BIBINPUTS`).

### One-shot rebuild (`scripts/build.sh`)

Scrivener overwrites its compiled `.tex` on every compile, which brings the
placeholders back. This script closes that loop in one command — it inserts the
citations, then builds both a PDF and a `.docx`:

```bash
./scripts/build.sh path/to/thesis.tex
```

It reads the Scrivener-owned `.tex` without ever writing to it (emitting a
separate `<stem>_cited.tex`), so it is safe to re-run after every compile. It
also copies the `.bib` into the compile directory for `bibtex`, and resolves
`rtf-cite` from `PATH` or falls back to `conda run`.

| Option | Default | Purpose |
| --- | --- | --- |
| `-b, --bib` | `export.bib` at repo root | BibTeX file |
| `-s, --style` | `styles/nature.csl` | CSL style, **docx only** |
| `-c, --cite-command` | `citep` | natbib command |
| `-e, --env` | `rtf-cite` | conda env, if not on `PATH` |
| `--no-pdf` / `--no-docx` | both built | Skip a format |
| `-h, --help` | — | Show usage |

Because `latexmk` often exits nonzero on benign warnings while still producing
a valid PDF, the script judges success on whether the output files were
actually created, and points at `<stem>_cited.build.log` when one is missing.

Note that the PDF and the docx are formatted by **different** machinery: the
PDF uses natbib and your `\bibliographystyle{...}`, while the docx uses pandoc
with the CSL style from `--style`. Align the two if consistent citation
formatting matters.

### Other output formats

Once a `.tex` carries real `\citep` commands, pandoc can render it to any
format it supports, resolving the citations from the `.bib`:

```bash
pandoc thesis_cited.tex --citeproc --bibliography=export.bib \
  --csl=styles/nature.csl -o thesis.docx
```

The output format follows the `-o` extension (`.docx`, `.odt`, `.html`,
`.epub`). Add `--reference-doc=template.docx` to control docx styling.

Pandoc parses LaTeX rather than running it, so document-class and custom-macro
features do not survive: unknown commands are dropped **along with their
arguments**. Annotation macros such as `\todo{...}` (and wrappers built on
`\newcommandx`) disappear silently. Check tables and structure before relying
on a converted file.

### Bundled styles

The following styles ship in `styles/` (pass the name without `.csl` to
`--style`):

`american-chemical-society`, `american-medical-association`,
`american-political-science-association`, `american-sociological-association`,
`apa`, `chicago-author-date`, `chicago-notes-bibliography`,
`chicago-shortened-notes-bibliography`, `elsevier-harvard`,
`harvard-cite-them-right`, `ieee`, `mhra-notes`, `modern-language-association`,
`nature`, `nlm-citation-sequence`, `rtf-scan`.

To add more, drop any `.csl` file into `styles/` (Zotero keeps its styles in
`~/Zotero/styles/`) and pass its filename stem to `--style`.

## Use with Scrivener

This is the end-to-end workflow `rtf-cite` is built for.

### Setup (one time only)

1. In **Scrivener** → Preferences/Settings → General → Citations, point it to
   your Zotero installation. This enables the Alt+Y (Windows) / Cmd+Y (Mac)
   shortcut to open Zotero while writing.
2. In **Zotero** → Settings → Export, set "Quick Copy" format to **RTF Scan**.
   This makes Zotero output citations in the right placeholder format.
   1. The RTF Scan format may need to be added in the Citation panel.

### While writing

When you need to cite something mid-sentence:

1. Place your cursor where you want the citation (usually inside a footnote in
   Scrivener).
2. Hit **Alt+Y / Cmd+Y** → Zotero opens.
3. Find your source, and drag it into Scrivener (or copy it with Quick Copy).
4. Zotero drops a placeholder that looks like this:
   `{Pappas et al., "Invasive candidiasis", 2018}` — author phrase, quoted
   title, year.

That's it — you keep writing. The placeholder just sits there as plain text, not
a real citation yet. Multiple sources cited together appear as one placeholder
with each entry separated by a semicolon.

### At the end (when you're ready for a final output)

1. In Scrivener, **compile** your thesis — to **.RTF**, or to **LaTeX** if you
   want a typeset PDF.
2. Export your library from Zotero as a **BibTeX** file (e.g. `export.bib`).
3. Run the tool on the compiled file.

**If you compiled to RTF:**

```bash
rtf-cite thesis.rtf --bib export.bib --style nature -o thesis_cited.rtf
```

Choose your citation style with `--style` (see Bundled styles above).
`rtf-cite` finds every `{placeholder}`, replaces it with a real formatted
citation, and appends a **Bibliography** at the end.

**If you compiled to LaTeX:**

```bash
./scripts/build.sh thesis.tex
```

This inserts natbib citations and builds the PDF and docx in one step. Because
Scrivener rewrites its compiled `.tex` on every compile — restoring the
placeholders — re-run this after each one.

Either way, any placeholder that can't be matched to a BibTeX entry is reported
on stderr and left in place, so nothing is silently lost.

> **Why not Zotero's Tools → RTF Scan?** Zotero's built-in RTF Scan mishandles
> placeholders that contain multiple references; `rtf-cite` is the replacement
> for that step.

## License

This work is licensed under a [Creative Commons Attribution-NonCommercial 4.0 International License](http://creativecommons.org/licenses/by-nc/4.0/).
See [LICENSE](LICENSE) for the full text.

[![License: CC BY-NC 4.0](https://licensebuttons.net/l/by-nc/4.0/80x15.png)](https://creativecommons.org/licenses/by-nc/4.0/)
