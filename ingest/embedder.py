"""
embedder.py — Embeds chunks using a local sentence-transformer model
and stores them in a persistent ChromaDB vector store.
"""

import chromadb
from chromadb.utils import embedding_functions

CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "documents"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def get_collection():
    """Return (or create) the ChromaDB collection with our embedding function."""
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embed_fn,
        metadata={"hnsw:space": "cosine"},
    )

    return collection


def embed_chunks(chunks: list[dict]) -> None:
    """
    Embed a list of chunk dicts and upsert them into ChromaDB.

    Upsert (not insert) means re-ingesting the same document won't
    create duplicates — existing chunks are overwritten.
    """
    collection = get_collection()

    texts = [c["text"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]

    # ids = [
    #     f"{m['source']}_p{m['page']}_c{m['chunk_index']}"
    #     for m in metadatas
    # ]
    
    ids = [
        f"{m.get('session_id', 'shared')}_{m['source']}_p{m['page']}_c{m['chunk_index']}"
        for m in metadatas
    ]

    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch_end = min(i + batch_size, len(chunks))
        collection.upsert(
            documents=texts[i:batch_end],
            metadatas=metadatas[i:batch_end],
            ids=ids[i:batch_end],
        )
        print(f"Embedded chunks {i + 1}–{batch_end} / {len(chunks)}")

    print(f"Done. Collection now has {collection.count()} chunks total.")


# def delete_document(source_filename: str) -> None:
#     """Remove all chunks belonging to a specific file."""
#     collection = get_collection()
#     collection.delete(where={"source": source_filename})
#     print(f"Deleted all chunks for: {source_filename}")

def delete_document(source_filename: str, session_id: str = None) -> None:
    """Remove all chunks belonging to a specific file (scoped to a session if given)."""
    collection = get_collection()

    if session_id:
        results = collection.get(
            where={"source": source_filename},
            include=["metadatas"],
        )
        ids_to_delete = [
            doc_id for doc_id, meta in zip(results["ids"], results["metadatas"])
            if meta.get("session_id") == session_id or meta.get("session_id") is None
        ]
        if ids_to_delete:
            collection.delete(ids=ids_to_delete)
    else:
        collection.delete(where={"source": source_filename})

    print(f"Deleted all chunks for: {source_filename}")


def list_documents(session_id: str = None) -> list[str]:
    """Return a list of unique source filenames in the vector store."""
    collection = get_collection()
    results = collection.get(include=["metadatas"])

    sources = set()
    # for meta in results["metadatas"]:
    #     sources.add(meta["source"])

    # return sorted(sources)
    for meta in results["metadatas"]:
        meta_session = meta.get("session_id")

        if meta_session is None:
            sources.add(meta["source"])

        elif session_id and meta_session == session_id:
            sources.add(meta["source"])

    return sorted(sources)
