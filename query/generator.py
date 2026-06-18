"""
generator.py — Builds a prompt from retrieved chunks and streams
the LLM's answer back with source citations.
"""

import os
from groq import Groq
# from dotenv import load_dotenv
from query.retriever import retrieve

# load_dotenv()

# client = Groq(api_key=os.getenv("GROQ_API_KEY"))

import streamlit as st
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

LLM_MODEL = "llama-3.3-70b-versatile" 


SYSTEM_PROMPT = """You are a helpful assistant that answers questions strictly 
based on the provided document context. 

Rules:
- Only use information from the context below to answer.
- If the answer is not in the context, say: "I couldn't find that in the uploaded documents."
- Always cite your source as: [filename, page X] at the end of each claim.
- Be concise but complete."""


def build_context(chunks: list[dict]) -> str:
    """Format retrieved chunks into a readable context block."""
    if not chunks:
        return "No relevant context found."

    lines = []
    for i, chunk in enumerate(chunks, 1):
        lines.append(
            f"[{i}] Source: {chunk['source']}, Page {chunk['page']} "
            f"(relevance: {chunk['score']})\n{chunk['text']}"
        )

    return "\n\n---\n\n".join(lines)


def ask(question: str, chat_history: list[dict] = None, session_id: str = None) -> tuple[str, list[dict]]:
    """
    Ask a question against the ingested documents.

    Args:
        question:     The user's question string.
        chat_history: Previous turns as [{"role": "user"|"assistant", "content": str}].
                      Pass None or [] for a fresh conversation.

    Returns:
        (answer_text, retrieved_chunks)
        — answer_text is the full LLM response
        — retrieved_chunks lets the UI display source citations
    """
    if chat_history is None:
        chat_history = []

    chunks = retrieve(question, session_id=session_id)

    if not chunks:
        no_context_msg = "I couldn't find relevant information in the uploaded documents."
        return no_context_msg, []

    context = build_context(chunks)
    user_message = f"Context from documents:\n\n{context}\n\nQuestion: {question}"

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(chat_history[-6:])  
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        temperature=0.2,   
        max_tokens=1024,
    )

    answer = response.choices[0].message.content
    return answer, chunks


def ask_stream(question: str, chat_history: list[dict] = None, session_id: str = None):
    """
    Streaming version of ask() — yields text chunks as they arrive.
    Use this in Streamlit with st.write_stream().

    Yields:
        str — incremental text chunks from the LLM
    Also sets ask_stream.last_chunks after the stream ends (for citations).
    """
    if chat_history is None:
        chat_history = []

    chunks = retrieve(question, session_id=session_id)
    ask_stream.last_chunks = chunks 

    if not chunks:
        ask_stream.last_chunks = []
        yield "I couldn't find relevant information in the uploaded documents."
        return

    context = build_context(chunks)
    user_message = f"Context from documents:\n\n{context}\n\nQuestion: {question}"

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(chat_history[-6:])
    messages.append({"role": "user", "content": user_message})

    stream = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        temperature=0.2,
        max_tokens=1024,
        stream=True,
    )

    full_text = ""
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta is not None:
            full_text += delta
            yield delta
            
            
    if "couldn't find that" in full_text.lower() or "couldn't find relevant" in full_text.lower():
        ask_stream.last_chunks = []
    else:
        ask_stream.last_chunks = chunks