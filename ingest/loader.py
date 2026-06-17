"""
loader.py — Extracts raw text from PDF, DOCX, and TXT files.
Each document is returned as a list of pages with metadata attached.
"""

import fitz  # PyMuPDF
from docx import Document
from pathlib import Path

HEADER_CHAR_LIMIT = 300

def _split_header(text: str, char_limit: int = HEADER_CHAR_LIMIT) -> tuple[str, str]:
    """Split text into (header_portion, rest) at a clean boundary near char_limit."""
    if len(text) <= char_limit:
        return text, ""

    cut = text.rfind("\n", 0, char_limit)
    if cut == -1:
        cut = char_limit

    return text[:cut].strip(), text[cut:].strip()


def load_pdf(file_path: str) -> list[dict]: 
    """Extract text page-by-page from a PDF."""
    pages = []
    doc = fitz.open(file_path)

    for page_num, page in enumerate(doc, start=1):
        text = page.get_text("text").strip()
        if text: 
            pages.append({
                "text": text,
                "metadata": {
                    "source": Path(file_path).name,
                    "page": page_num,
                    "file_type": "pdf",
                    "is_first_page": page_num == 1,
                }
            })

    doc.close()
    return pages


def load_docx(file_path: str) -> list[dict]:
    """Extract text paragraph-by-paragraph from a Word document."""
    doc = Document(file_path)
    full_text = "\n".join(
        para.text for para in doc.paragraphs if para.text.strip()
    )

    return [{
        "text": full_text,
        "metadata": {
            "source": Path(file_path).name,
            "page": 1,
            "file_type": "docx",
            "is_first_page": True,
        }
    }]


def load_txt(file_path: str) -> list[dict]:
    """Load a plain text file as a single page."""
    text = Path(file_path).read_text(encoding="utf-8")

    return [{
        "text": text,
        "metadata": {
            "source": Path(file_path).name,
            "page": 1,
            "file_type": "txt",
            "is_first_page": True,
        }
    }]


def load_document(file_path: str) -> list[dict]:
    """Route a file to the correct loader based on its extension."""
    ext = Path(file_path).suffix.lower()

    loaders = {
        ".pdf":  load_pdf,
        ".docx": load_docx,
        ".txt":  load_txt,
    }

    if ext not in loaders:
        raise ValueError(f"Unsupported file type: {ext}. Supported: {list(loaders.keys())}")

    return loaders[ext](file_path)


def load_folder(folder_path: str) -> list[dict]:
    """Load all supported documents from a folder."""
    folder = Path(folder_path)
    supported = {".pdf", ".docx", ".txt"}
    all_pages = []

    for file in sorted(folder.iterdir()):
        if file.suffix.lower() in supported:
            print(f"Loading: {file.name}")
            pages = load_document(str(file))
            all_pages.extend(pages)

    print(f"Loaded {len(all_pages)} pages from {folder_path}")
    return all_pages
