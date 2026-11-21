import pymupdf


def extract_text_from_pdf(file_path: str) -> str:
    """Return the concatenated text of every page in a PDF."""
    parts = []
    with pymupdf.open(file_path) as doc:
        for page in doc:
            parts.append(page.get_text())
    return "\n".join(parts).strip()
