import re as _re
import shutil
import pytest
from rtf_cite.cli import main

pytestmark = pytest.mark.skipif(shutil.which("pandoc") is None, reason="pandoc not installed")


def test_full_run_on_thesis(tmp_path, capsys):
    rtf = "tests/fixtures/master_thesis.rtf"
    bib = "tests/fixtures/export.bib"
    out = tmp_path / "out.rtf"
    main([rtf, "--bib", bib, "--style", "nature", "-o", str(out)])

    text = out.read_text(encoding="latin-1")
    # valid-ish RTF: starts with header and braces balance
    assert text.lstrip().startswith("{\\rtf")
    assert text.count("{") == text.count("}")
    # bibliography appended
    assert "Bibliography" in text
    # no original marker text should remain (0 unmatched expected on this data)
    captured = capsys.readouterr()
    assert "0 unmatched" in captured.out
    assert r'\{Pappas et al.,' not in text


def test_multi_reference_marker_renders_as_one_group(tmp_path, capsys):
    # The thesis has a 3-reference marker (Fan 2013; Nobile 2006; Moyes 2016).
    # Nature is superscript-numeric, so the group must render as a single
    # superscript run like "1,2,3" -- NOT three separate superscripts.
    out = tmp_path / "out.rtf"
    main(["tests/fixtures/master_thesis.rtf", "--bib",
          "tests/fixtures/export.bib", "--style", "nature", "-o", str(out)])
    text = out.read_text(encoding="latin-1")
    # A grouped superscript citation joins multiple numbers in one \super run,
    # either comma-separated (1,2,3) or collapsed into a range (3-5 rendered
    # with the unicode en-dash, i.e. \\u8211). Either form proves grouping.
    grouped = _re.search(r"\\super\s*\d+\s*(?:,\s*|\\u8211-?)\d+", text)
    assert grouped, \
        "multi-ref marker did not collapse into one grouped superscript citation"
