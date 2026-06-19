import re

# Inline character formatting we keep; everything else (fonts, colors,
# paragraph layout) is dropped so it can't reference the host doc's tables.
_ALLOWED = {"i", "i0", "b", "b0", "super", "sub", "nosupersub", "par",
            "line", "tab", "emdash", "endash", "u"}

# Matches one control word with optional numeric parameter and optional space.
_CONTROL = re.compile(r"\\([a-zA-Z]+)(-?\d+)?( ?)")


def _repl(m):
    word, num, sp = m.group(1), m.group(2) or "", m.group(3)
    if word == "u":                       # \uNNNN unicode -> always keep
        return f"\\u{num}{sp}"
    if word in _ALLOWED:
        return f"\\{word}{num}{sp}"
    return ""                             # drop disallowed control word


def sanitize_rtf(fragment):
    # Protect escaped literals \{ \} \\ and \'xx hex before scrubbing controls.
    placeholders = {}

    def stash(m):
        key = f"\x00{len(placeholders)}\x00"
        placeholders[key] = m.group(0)
        return key

    protected = re.sub(r"\\(?:[{}\\]|'[0-9a-fA-F]{2})", stash, fragment)
    scrubbed = _CONTROL.sub(_repl, protected)
    for key, val in placeholders.items():
        scrubbed = scrubbed.replace(key, val)
    return scrubbed
