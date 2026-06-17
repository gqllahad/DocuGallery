"""
retriever.py — Finds the most relevant chunks for a user's question
using semantic (vector) search against ChromaDB.

The query is embedded with the same model used during ingestion,
then compared against all stored chunks using cosine similarity.
"""

from ingest.embedder import get_collection

TOP_K = 5  #5            
MIN_SIMILARITY = 0.15 #0.30     
PRIORITY_BOOST = 0.15            # bonus added to priority chunks' similarity score
PRIORITY_MIN_SIMILARITY = 0.20 

def _get_priority_chunks(collection, session_id: str = None) -> list[dict]:
    """Fetch all chunks tagged priority='always', scoped to the session."""
    results = collection.get(
        where={"priority": "always"},
        include=["documents", "metadatas"],
    )

    chunks = []
    for doc, meta in zip(results["documents"], results["metadatas"]):
        meta_session = meta.get("session_id")
        
        if session_id is not None:
            if meta_session is not None and meta_session != session_id:
                continue

        chunks.append({
            "text":   doc,
            "source": meta["source"],
            "page":   meta["page"],
            "score":  1.0, 
        })

    return chunks

def retrieve(query: str, top_k: int = TOP_K, session_id: str = None) -> list[dict]:
    """
    Search the vector store for chunks relevant to the query.
    Priority chunks (document headers with names/contact info) get a
    relevance boost so they surface only when the question is actually
    about that file/person — not unconditionally on every question.
    """
    collection = get_collection()

    if collection.count() == 0:
        raise RuntimeError("Vector store is empty. Run ingest first.")

    query_kwargs = {
        "query_texts": [query],
        "n_results": min(top_k * 4, collection.count()), 
        "include": ["documents", "metadatas", "distances"],
    }
    results = collection.query(**query_kwargs)

    candidates = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        # Session boundary check
        meta_session = meta.get("session_id")
        if session_id is not None:
            if meta_session is not None and meta_session != session_id:
                continue

        similarity = 1 - (dist / 2)
        is_priority = meta.get("priority") == "always"

        if is_priority:
            boosted_score = similarity + PRIORITY_BOOST
            if boosted_score < PRIORITY_MIN_SIMILARITY:
                continue
            final_score = min(boosted_score, 1.0)
        else:
            if similarity < MIN_SIMILARITY:
                continue
            final_score = similarity

        candidates.append({
            "text":   doc,
            "source": meta["source"],
            "page":   meta["page"],
            "score":  round(final_score, 3),
        })

    candidates.sort(key=lambda c: c["score"], reverse=True)
    return candidates[:top_k]

# def retrieve(query: str, top_k: int = TOP_K, session_id: str = None) -> list[dict]:
#     """
#     Search the vector store for chunks relevant to the query.

#     Returns a list of result dicts sorted by relevance (best first):
#         {
#             "text":       str,   # chunk content
#             "source":     str,   # filename
#             "page":       int,   # page number
#             "score":      float, # cosine similarity (higher = better)
#         }
#     """
#     collection = get_collection()

#     if collection.count() == 0:
#         raise RuntimeError("Vector store is empty. Run ingest first.")

#     # results = collection.query(
#     #     query_texts=[query],
#     #     n_results=min(top_k, collection.count()),
#     #     include=["documents", "metadatas", "distances"],
#     # )
    
#     priority_chunks = _get_priority_chunks(collection, session_id=session_id)
#     priority_sources = {(c["source"], c["page"]) for c in priority_chunks}

#     query_kwargs = {
#         "query_texts": [query],
#         "n_results": min(top_k * 3, collection.count()),
#         "include": ["documents", "metadatas", "distances"],
#     }
     
#     results = collection.query(**query_kwargs)

#     chunks = []
#     for doc, meta, dist in zip(
#         results["documents"][0],
#         results["metadatas"][0],
#         results["distances"][0],
#     ):
        
#         # Session boundary check
#         meta_session = meta.get("session_id")
#         if session_id is not None:
#             if meta_session is not None and meta_session != session_id:
#                 continue
            
#         if (meta["source"], meta["page"]) in priority_sources and meta.get("priority") == "always":
#             continue
    
#         similarity = 1 - (dist / 2)

#         if similarity < MIN_SIMILARITY:
#             continue  

#         chunks.append({
#             "text":   doc,
#             "source": meta["source"],
#             "page":   meta["page"],
#             "score":  round(similarity, 3),
#         })
        
#         if len(chunks) >= top_k:
#             break

#     return priority_chunks + chunks
