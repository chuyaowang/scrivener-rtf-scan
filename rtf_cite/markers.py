import re
from dataclasses import dataclass, field

# Escaped-brace group: \{ ... \}  (inner text has no raw braces).
_MARKER_RE = re.compile(r'\\\{(.*?)\\\}', re.DOTALL)
# A reference: author phrase , "title" , year
_REF_RE = re.compile(r'^(?P<author>.*?),\s*"(?P<title>.*)"\s*,\s*(?P<year>\d{4})\b')


@dataclass
class Reference:
    author_phrase: str
    title: str
    year: str


@dataclass
class Marker:
    start: int
    end: int
    raw: str
    references: list = field(default_factory=list)


def parse_reference(text):
    m = _REF_RE.search(text.strip())
    if not m:
        return None
    return Reference(
        author_phrase=m.group("author").strip(),
        title=m.group("title").strip(),
        year=m.group("year"),
    )


def extract_markers(text):
    markers = []
    for m in _MARKER_RE.finditer(text):
        inner = m.group(1)
        # Qualify: must contain a quoted title and a 4-digit year.
        if '"' not in inner or not re.search(r'\d{4}', inner):
            continue
        refs = [parse_reference(part) for part in inner.split(";")]
        refs = [r for r in refs if r is not None]
        if not refs:
            continue
        markers.append(Marker(start=m.start(), end=m.end(), raw=m.group(0),
                              references=refs))
    return markers
