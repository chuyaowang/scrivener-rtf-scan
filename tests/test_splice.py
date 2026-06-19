from rtf_cite.splice import splice_document


def test_replaces_spans_back_to_front_and_appends_bibliography():
    rtf = r"{\rtf1 a \{M0\} b \{M1\} c \par}"
    # marker spans located by the caller
    s0 = rtf.index(r"\{M0\}")
    s1 = rtf.index(r"\{M1\}")
    spans = [(s0, s0 + len(r"\{M0\}")), (s1, s1 + len(r"\{M1\}"))]
    citations = {0: r"\super 1\nosupersub ", 1: r"\super 2\nosupersub "}
    bib = r"Smith, A. A Tiny Paper. J. Test 1, 1-2 (2020)."
    out = splice_document(rtf, spans, citations, bib)
    assert r"\{M0\}" not in out and r"\{M1\}" not in out
    assert out.count(r"\super") == 2
    assert "Bibliography" in out
    assert "A Tiny Paper" in out
    assert out.rstrip().endswith("}")      # still a closed RTF document
