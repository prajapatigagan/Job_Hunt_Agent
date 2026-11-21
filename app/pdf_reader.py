import re
from pathlib import Path

from pypdf import PdfReader


class PDFError(Exception):
    pass


def read_pdf_text(path) -> str:
    try:
        reader = PdfReader(str(Path(path)))
        pages = [(p.extract_text() or "") for p in reader.pages]
    except Exception as e:
        raise PDFError(f"PDF padh nahi paya: {e}") from e

    text = "\n".join(pages)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    if len(text) < 50:
        raise PDFError("PDF me text nahi mila (shayad scanned image hai). Text wala PDF use karo.")
    return text
