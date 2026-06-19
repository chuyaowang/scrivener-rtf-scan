# Scrivener RTF Citation Scanner 

A command-line tool (`rtf-cite`) that replaces the plain-text citation
placeholders that Zotero's **RTF Scan** Quick Copy format leaves in an RTF file
with properly formatted in-text citations, and appends a bibliography — using
any CSL citation style.

## Why this exists

This tool is designed for the **Scrivener + Zotero** writing workflow. Zotero
has a built-in **RTF Scan** feature that does the same job, but it **breaks when
a single placeholder contains multiple references** (e.g.
`{Brown et al., "…", 2014; Desai, "…", 2018; Thomson et al., "…", 2016}`).
`rtf-cite` handles those grouped placeholders correctly, collapsing them into a
single grouped citation (e.g. superscript `1,2,3` or a range `1-3`), and is a
drop-in replacement for the final "RTF Scan" step described below.

## Setup

```bash
conda env create -f environment.yml
conda activate rtf-cite
pip install -e .
```

Requires `pandoc` 3.x on PATH.

## Usage

```bash
rtf-cite thesis.rtf --bib export.bib --style nature -o thesis_cited.rtf
```

- `--style` takes a bundled style name (default `nature`) or a path to a `.csl`
  file.
- Multiple references inside one placeholder render as a single grouped citation
  (e.g. superscript `1,2,3` or a collapsed range `1-3`).
- Unmatched placeholders are reported on stderr and left untouched in the
  output.

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
4. Zotero drops a placeholder that looks like this: `{Smith, 2019, #234}`.

That's it — you keep writing. The placeholder just sits there as plain text, not
a real citation yet. Multiple sources cited together appear as one placeholder
with each entry separated by a semicolon.

### At the end (when you're ready for a final output)

1. In Scrivener, **compile** your thesis to an **.RTF file**.
2. Export your library from Zotero as a **BibTeX** file (e.g. `export.bib`).
3. Run `rtf-cite` on the compiled RTF:

   ```bash
   rtf-cite thesis.rtf --bib export.bib --style nature -o thesis_cited.rtf
   ```

   - Choose your citation style with `--style` (see Bundled styles above).
   - `rtf-cite` finds every `{placeholder}` tag, replaces it with a real
     formatted citation, and appends a **Bibliography** at the end.
   - Any placeholder it can't match to a BibTeX entry is reported and left
     in place, so nothing is silently lost.

> **Why not Zotero's Tools → RTF Scan?** Zotero's built-in RTF Scan mishandles
> placeholders that contain multiple references; `rtf-cite` is the replacement
> for that step.

## License

This work is licensed under a [Creative Commons Attribution-NonCommercial 4.0 International License](http://creativecommons.org/licenses/by-nc/4.0/).
[![CC BY-NC 4.0](https://shields.io)](http://creativecommons.org/licenses/by-nc/4.0/)
