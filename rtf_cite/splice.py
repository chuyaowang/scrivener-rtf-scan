def splice_document(rtf, spans, citations, bibliography):
    """spans: list of (start, end) in marker order, aligned with citations[i].
    Replace each span with its citation (or leave intact if citation is None),
    then append a Bibliography section before the document's final '}'."""
    chars = rtf
    # Replace back-to-front so earlier spans keep their offsets.
    for i in range(len(spans) - 1, -1, -1):
        start, end = spans[i]
        cite = citations.get(i)
        if cite is None or cite == "":
            continue                       # leave the original marker intact
        chars = chars[:start] + cite + chars[end:]
    # Append bibliography before the final closing brace.
    close = chars.rstrip().rfind("}")
    heading = r"\par\par {\b Bibliography}\par "
    block = heading + bibliography + " "
    return chars[:close] + block + chars[close:]
