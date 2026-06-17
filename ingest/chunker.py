"""
chunker.py — Splits loaded pages into smaller overlapping chunks.
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter

HEADER_CHAR_LIMIT = 300


def chunk_pages(pages: list[dict], chunk_size: int = 600, overlap: int = 80) -> list[dict]:
    """
    Split a list of page dicts into smaller chunks.

    Args:
        pages:      Output from loader.py — list of {text, metadata} dicts.
        chunk_size: Target size in characters per chunk (not tokens).
        overlap:    How many characters to repeat between adjacent chunks.

    Returns:
        List of chunk dicts, each with text + enriched metadata.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )

    chunks = []

    for page in pages:
        raw_chunks = splitter.split_text(page["text"])
        is_first_page = page["metadata"].get("is_first_page", False)

        for i, chunk_text in enumerate(raw_chunks):
            if not chunk_text.strip():
                continue
            
            metadata = {
                **page["metadata"],
                "chunk_index": i,
            }
            
            if is_first_page and i == 0:
                metadata["priority"] = "always"

            # chunks.append({
            #     "text": chunk_text.strip(),
            #     "metadata": {
            #         **page["metadata"],  
            #         "chunk_index": i,       
            #     }
            # })
            
            chunks.append({
                "text": chunk_text.strip(),
                "metadata": metadata,
            })

    print(f"Created {len(chunks)} chunks from {len(pages)} pages")
    return chunks
