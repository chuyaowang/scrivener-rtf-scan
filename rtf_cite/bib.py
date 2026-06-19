import re
import bibtexparser


def normalize_title(title):
    s = title.lower()
    s = re.sub(r'[{}]', '', s)
    s = re.sub(r'[^a-z0-9]+', ' ', s)
    return s.strip()


def _surname(author_field):
    # bibtex author -> first author's surname, lowercased
    first = author_field.split(" and ")[0].strip()
    if "," in first:                      # "Surname, Given"
        return first.split(",")[0].strip().lower()
    return first.split()[-1].lower() if first.split() else ""


def index_bib(path):
    with open(path, encoding="utf-8") as fh:
        db = bibtexparser.load(fh)
    index = {}  # normalized_title -> list of dicts
    for e in db.entries:
        title = e.get("title", "")
        index.setdefault(normalize_title(title), []).append({
            "key": e.get("ID", ""),
            "surname": _surname(e.get("author", "")),
            "year": str(e.get("year", "")),
        })
    return index


def match_reference(ref, index):
    candidates = index.get(normalize_title(ref.title))
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]["key"]
    ref_surname = re.sub(r'\s+et al\.?$', '', ref.author_phrase).strip().lower()
    ref_surname = ref_surname.split(",")[0].split()[-1] if ref_surname else ""
    for c in candidates:
        if c["surname"] == ref_surname and c["year"] == ref.year:
            return c["key"]
    for c in candidates:                  # fall back to year only
        if c["year"] == ref.year:
            return c["key"]
    return candidates[0]["key"]
