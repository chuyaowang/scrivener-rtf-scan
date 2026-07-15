from rtf_cite.tex import replace_markers_tex

# Minimal fake bib index: normalized_title -> [ {key, surname, year} ]
INDEX = {
    "invasive candidiasis": [{"key": "Pappas2018", "surname": "pappas", "year": "2018"}],
    "stress adaptation in a pathogenic fungus": [
        {"key": "Brown2014", "surname": "brown", "year": "2014"}],
    "candida albicans hyphae from growth initiation to invasion": [
        {"key": "Desai2018", "surname": "desai", "year": "2018"}],
}


def test_single_citep():
    text = r"foo \{Pappas et al., ``Invasive candidiasis'', 2018\} bar"
    out, unmatched = replace_markers_tex(text, INDEX)
    assert out == r"foo \citep{Pappas2018} bar"
    assert unmatched == []


def test_grouped_collapses_into_one_command():
    text = (r"x \{Brown et al., ``Stress adaptation in a pathogenic fungus'', 2014; "
            r"Desai, ``Candida albicans Hyphae: From Growth Initiation to Invasion'', 2018\} y")
    out, _ = replace_markers_tex(text, INDEX)
    assert out == r"x \citep{Brown2014,Desai2018} y"


def test_citet_command():
    text = r"\{Pappas et al., ``Invasive candidiasis'', 2018\}"
    out, _ = replace_markers_tex(text, INDEX, cite_cmd="citet")
    assert out == r"\citet{Pappas2018}"


def test_unmatched_left_in_place():
    text = r"a \{Nobody, ``Totally unknown title'', 1999\} b"
    out, unmatched = replace_markers_tex(text, INDEX)
    assert out == text
    assert unmatched == ['Nobody, "Totally unknown title", 1999']


def test_partial_match_keeps_only_found_keys():
    text = (r"\{Pappas et al., ``Invasive candidiasis'', 2018; "
            r"Nobody, ``Totally unknown title'', 1999\}")
    out, unmatched = replace_markers_tex(text, INDEX)
    assert out == r"\citep{Pappas2018}"
    assert len(unmatched) == 1