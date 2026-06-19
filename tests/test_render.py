import shutil
import pytest
from rtf_cite.render import build_markdown, render_with_pandoc

pytestmark = pytest.mark.skipif(shutil.which("pandoc") is None, reason="pandoc not installed")

MINI_BIB = r"""
@article{Smith2020,
  author = {Alice Smith},
  title = {A Tiny Paper},
  journal = {J. Test},
  year = {2020},
  volume = {1},
  pages = {1-2}
}
"""


def test_build_markdown_lists_groups_and_sentinels():
    md = build_markdown([["Smith2020"], ["Smith2020"]])
    assert "ZZCITE0ZZ [@Smith2020]" in md
    assert "ZZCITE1ZZ [@Smith2020]" in md
    assert "ZZBIBSTARTZZ" in md


def test_multiple_refs_go_in_one_group():
    # All refs for a marker share ONE [...] so the style collapses them into a
    # single grouped citation (e.g. superscript 1,2,3 or [1,2,3]) -- never
    # separate [1][2][3] / 1 2 3.
    md = build_markdown([["A2020", "B2021", "C2022"]])
    assert "ZZCITE0ZZ [@A2020; @B2021; @C2022]" in md
    assert "[@A2020]" not in md          # not emitted as separate citations


def test_render_returns_citations_and_bibliography(tmp_path):
    bib = tmp_path / "b.bib"; bib.write_text(MINI_BIB)
    style = tmp_path / "s.csl"
    shutil.copy("styles/nature.csl", style)
    citations, bibliography = render_with_pandoc(
        [["Smith2020"]], str(bib), str(style))
    assert 0 in citations
    assert citations[0].strip() != ""          # non-empty formatted in-text cite
    assert "Smith" in bibliography              # bibliography contains the entry
    assert r"\rtf" not in citations[0]          # fragment, not a full document
    assert "HYPERLINK" not in bibliography       # links stripped, no URL field


def test_bibliography_has_no_hyperlink_but_keeps_title(tmp_path):
    # A DOI-bearing entry must render its title as plain text, with no
    # HYPERLINK field left behind (the field is what leaks a visible
    # 'HYPERLINK "url"' string into word processors).
    bib = tmp_path / "b.bib"
    bib.write_text(r"""
@article{Doi2018,
  author = {Jane Doe},
  title = {A Linked Title},
  journal = {J. Test},
  year = {2018},
  volume = {4},
  pages = {10},
  doi = {10.1234/abc}
}
""")
    style = tmp_path / "s.csl"
    shutil.copy("styles/nature.csl", style)
    _cites, bibliography = render_with_pandoc([["Doi2018"]], str(bib), str(style))
    assert "HYPERLINK" not in bibliography
    assert "A linked title" in bibliography or "A Linked Title" in bibliography
