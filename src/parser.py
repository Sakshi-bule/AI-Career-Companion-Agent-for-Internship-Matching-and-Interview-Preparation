import fitz  # PyMuPDF


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    text_chunks = []
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            text_chunks.append(page.get_text("text"))

    full_text = "\n".join(text_chunks).strip()
    if not full_text:
        raise ValueError("No readable text found in PDF.")
    return full_text