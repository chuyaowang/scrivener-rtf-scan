from rtf_cite.sanitize import sanitize_rtf


def test_keeps_whitelisted_inline_controls():
    frag = r"{\super 12\nosupersub } and \i italic\i0  text"
    out = sanitize_rtf(frag)
    assert r"\super" in out
    assert r"\nosupersub" in out
    assert r"\i " in out and r"\i0" in out


def test_strips_font_and_color_controls():
    frag = r"\f3\fs24\cf2 hello \ql world"
    out = sanitize_rtf(frag)
    for bad in (r"\f3", r"\fs24", r"\cf2", r"\ql"):
        assert bad not in out
    assert "hello" in out and "world" in out


def test_preserves_unicode_and_escaped_literals():
    frag = r"Kov\u225 cs \'92 \{lit\}"
    out = sanitize_rtf(frag)
    assert r"\u225" in out
    assert r"\'92" in out
    assert r"\{lit\}" in out
