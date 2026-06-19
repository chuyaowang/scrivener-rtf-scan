from rtf_cite.bib import normalize_title, index_bib, match_reference
from rtf_cite.markers import Reference

BIB = r"""
@article{Fan2013,
  author = {Yong Fan and Others},
  title = {Hyphae-Specific Genes HGC1, ALS3, HWP1, and ECE1},
  year = {2013}
}
@article{Smith2020a,
  author = {Alice Smith},
  title = {A Shared Title},
  year = {2020}
}
@article{Jones2020,
  author = {Bob Jones},
  title = {A Shared Title},
  year = {2020}
}
"""


def test_normalize_title_strips_punct_and_case():
    assert normalize_title('Hyphae-Specific Genes HGC1, ALS3!') == \
           normalize_title('hyphae specific genes hgc1 als3')


def test_match_by_title(tmp_path):
    p = tmp_path / "b.bib"; p.write_text(BIB)
    idx = index_bib(str(p))
    ref = Reference("Fan et al.", "Hyphae-Specific Genes HGC1, ALS3, HWP1, and ECE1", "2013")
    assert match_reference(ref, idx) == "Fan2013"


def test_match_tie_breaks_on_author_year(tmp_path):
    p = tmp_path / "b.bib"; p.write_text(BIB)
    idx = index_bib(str(p))
    ref = Reference("Jones", "A Shared Title", "2020")
    assert match_reference(ref, idx) == "Jones2020"


def test_unmatched_returns_none(tmp_path):
    p = tmp_path / "b.bib"; p.write_text(BIB)
    idx = index_bib(str(p))
    assert match_reference(Reference("X", "Nonexistent", "1999"), idx) is None
