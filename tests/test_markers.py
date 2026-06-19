from rtf_cite.markers import extract_markers, parse_reference

SINGLE = r'before \{Pappas et al., "Invasive candidiasis", 2018\} after'
MULTI = (r'x \{Fan et al., "Hyphae-Specific Genes HGC1", 2013; '
         r'Nobile et al., "Function of Candida albicans adhesin hwp1 in biofilm formation", 2006\} y')


def test_extract_single_marker_span_and_refs():
    markers = extract_markers(SINGLE)
    assert len(markers) == 1
    m = markers[0]
    # span maps back to the exact source text including the escaped braces
    assert SINGLE[m.start:m.end] == r'\{Pappas et al., "Invasive candidiasis", 2018\}'
    assert len(m.references) == 1
    assert m.references[0].title == "Invasive candidiasis"
    assert m.references[0].year == "2018"
    assert m.references[0].author_phrase == "Pappas et al."


def test_extract_multi_reference_marker():
    m = extract_markers(MULTI)[0]
    assert [r.year for r in m.references] == ["2013", "2006"]
    assert m.references[1].title == "Function of Candida albicans adhesin hwp1 in biofilm formation"


def test_ignores_non_citation_groups():
    # RTF metadata groups use UNescaped braces and have no quoted title
    rtf = r'{\creatim\yr2026\mo6} plain \{Smith, "A Real Title", 2020\}'
    markers = extract_markers(rtf)
    assert len(markers) == 1
    assert markers[0].references[0].title == "A Real Title"


def test_parse_reference_handles_trailing_period_and_spaces():
    ref = parse_reference('  Moyes et al., "Candidalysin is a fungal peptide toxin", 2016 ')
    assert ref.author_phrase == "Moyes et al."
    assert ref.title == "Candidalysin is a fungal peptide toxin"
    assert ref.year == "2016"
