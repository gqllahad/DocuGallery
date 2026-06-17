
import tempfile
import os
import streamlit as st
from groq import Groq
import uuid
import time

from ingest.loader import load_document
from ingest.chunker import chunk_pages
from ingest.embedder import embed_chunks, list_documents, delete_document
from query.generator import ask_stream




# Page config

st.set_page_config(
    page_title="AskMyDocs",
    page_icon="🗂️",
    layout="wide",
)

st.title("🗂️ AskMyDocs")
st.caption("Upload documents, then ask questions about them.")\
    
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# if st.button("🧪 TEST RETRIEVAL"):
#     from query.retriever import retrieve
#     test_chunks = retrieve("who made this system", session_id=st.session_state.session_id)
#     st.write("TEST RESULT:", test_chunks)

# general knowledge
KNOWLEDGE_BASE_DIR = "knowledge_base"
KNOWLEDGE_BASE_TAG = "__preloaded__"

def load_knowledge_base():
    if not os.path.exists(KNOWLEDGE_BASE_DIR):
        return
    try:
        already_ingested = list_documents()
    except Exception:
        already_ingested = []

    for filename in os.listdir(KNOWLEDGE_BASE_DIR):
        tagged_name = f"{KNOWLEDGE_BASE_TAG}{filename}"
        if tagged_name in already_ingested:
            continue
        filepath = os.path.join(KNOWLEDGE_BASE_DIR, filename)
        try:
            pages = load_document(filepath)
            for page in pages:
                page["metadata"]["source"] = tagged_name
                page["metadata"]["priority"] = "always"
                
            chunks = chunk_pages(pages)
            embed_chunks(chunks)
        except Exception as e:
            st.warning(f"Could not load knowledge base file {filename}: {e}")

load_knowledge_base()

# Session state

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "messages" not in st.session_state:
    st.session_state.messages = [] 
    
if "uploader_key" not in st.session_state: 
    st.session_state.uploader_key = 0

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    
# if "last_chunks" not in st.session_state:
#     st.session_state.last_chunks = []

# if "show_sources_panel" not in st.session_state:
#     st.session_state.show_sources_panel = False


# Sidebar: document management

with st.sidebar:
    st.header("Documents")

    # Upload
    uploaded_files = st.file_uploader(
        "Upload files",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        label_visibility="collapsed",
        key=f"uploader_{st.session_state.uploader_key}",
    )

    if uploaded_files:
        if st.button("Ingest uploaded files", type="primary", use_container_width=True):
            with st.spinner("Processing..."):
                all_success = True
                for uploaded_file in uploaded_files:
                    # Save to a temporary file
                    suffix = os.path.splitext(uploaded_file.name)[1]
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                        tmp.write(uploaded_file.read())
                        tmp_path = tmp.name

                    try:
                        pages = load_document(tmp_path)
                        
                        for page in pages:
                            # page["metadata"]["source"] = uploaded_file.name
                             page["metadata"]["source"] = uploaded_file.name
                             page["metadata"]["session_id"] = st.session_state.session_id

                        chunks = chunk_pages(pages)
                        embed_chunks(chunks)
                        st.success(f"✓ {uploaded_file.name}")
                    except Exception as e:
                        all_success = False
                        st.error(f"✗ {uploaded_file.name}: {e}")
                    finally:
                        os.unlink(tmp_path)
                        
            if all_success:
                st.session_state.uploader_key += 1
                st.rerun()

    # Ingested documents list
    st.divider()
    st.subheader("Ingested documents")

    # try:
    #     docs = list_documents()
    #     has_docs = bool(docs)
    #     if docs:
    #         for doc in docs:
    #             col1, col2 = st.columns([4, 1])
    #             col1.write(f"🗂️ {doc}")
    #             if col2.button("✕", key=f"del_{doc}", help=f"Remove {doc}"):
    #                 delete_document(doc)
    #                 st.rerun()
    #     else:
    #         st.info("No documents ingested yet.")
    # except Exception:
    #     st.info("No documents ingested yet.")
    
    # try:
    #     docs = list_documents(session_id=st.session_state.session_id)
    #     has_docs = bool(docs)
    # except Exception:
    #     docs = []
    #     has_docs = False
    
    try:
        docs = list_documents(session_id=st.session_state.session_id)
        user_docs = [doc for doc in docs if not doc.startswith(KNOWLEDGE_BASE_TAG)]
        has_docs = bool(docs)    
    except Exception:
        docs = []
        user_docs = []
        has_docs = False
        
    user_docs = [doc for doc in docs if not doc.startswith(KNOWLEDGE_BASE_TAG)]

    if user_docs:
        for doc in user_docs:
            col1, col2 = st.columns([4, 1])
            col1.write(f"🗂️ {doc}")
            if col2.button("✕", key=f"del_{doc}", help=f"Remove {doc}"):
                delete_document(doc, session_id=st.session_state.session_id)
                st.rerun()
    else:
        st.info("No documents ingested yet.")

    # if has_docs:
    #     for doc in docs:
    # #         col1, col2 = st.columns([4, 1])
    # #         col1.write(f"🗂️ {doc}")
    # #         if col2.button("✕", key=f"del_{doc}", help=f"Remove {doc}"):
    # #             delete_document(doc)
    # #             st.rerun()
    # # else:
    # #     st.info("No documents ingested yet.")
    
    #         if doc.startswith(KNOWLEDGE_BASE_TAG):
    #                     display_name = doc.replace(KNOWLEDGE_BASE_TAG, "")
    #                     st.write(f"📚 {display_name} *(built-in)*")

    #         # User uploaded docs
    #         else:
    #             col1, col2 = st.columns([4, 1])
    #             col1.write(f"🗂️ {doc}")
    #             if col2.button("✕", key=f"del_{doc}", help=f"Remove {doc}"):
    #                 delete_document(doc, session_id=st.session_state.session_id)
    #                 st.rerun()
    # else:
    #     st.info("No documents ingested yet.")

    st.divider()
    if st.button("Clear chat history", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.messages = []
        st.rerun()

    # Clear
    # st.divider()
    # if st.button("Clear chat history", use_container_width=True):
    #     st.session_state.chat_history = []
    #     st.session_state.messages = []
    #     st.rerun()


# Chat area 
# Previous messages
for i, msg in enumerate(st.session_state.messages): #for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        if msg["role"] == "assistant" and msg.get("citations"):
            toggle_key = f"show_sources_{i}"
            if toggle_key not in st.session_state:
                st.session_state[toggle_key] = False

            if st.button("📎 View Sources", key=f"btn_{i}"):
                st.session_state[toggle_key] = not st.session_state[toggle_key]

            if st.session_state[toggle_key]:
                with st.container(border=True):
                    st.caption(f"{len(msg['citations'])} chunks")
                    for c in msg["citations"]:
                        st.markdown(
                            f"**{c['source']}** — page {c['page']} "
                            f"*(relevance: {c['score']})*\n\n> {c['text'][:300]}..."
                        )

        # if "citations" in msg and msg["citations"]:
        #     with st.expander(f"Sources ({len(msg['citations'])} chunks)"):
        #         for c in msg["citations"]:
        #             st.markdown(
        #                 f"**{c['source']}** — page {c['page']} "
        #                 f"*(relevance: {c['score']})*\n\n> {c['text'][:300]}..."
        #             )
placeholder = "Ask about your documents..." if has_docs else "Ask me anything..."

# if has_docs:
#     col1, col2 = st.columns([1, 5])
#     with col1:
#         if st.button("📎 View Sources", use_container_width=True):
#             st.session_state.show_sources_panel = not st.session_state.show_sources_panel

#     if st.session_state.show_sources_panel:
#         with st.container(border=True):
#             if st.session_state.last_chunks:
#                 st.caption(f"Sources from your last question ({len(st.session_state.last_chunks)} chunks)")
#                 for c in st.session_state.last_chunks:
#                     st.markdown(
#                         f"**{c['source']}** — page {c['page']} "
#                         f"*(relevance: {c['score']})*\n\n> {c['text'][:300]}..."
#                     )
#             else:
#                 st.caption("No sources yet — ask a question first.")

if question := st.chat_input(placeholder):

    with st.chat_message("user"):
        st.markdown(question)

    st.session_state.messages.append({"role": "user", "content": question})

    with st.chat_message("assistant"):
        typing_placeholder = st.empty()
        typing_placeholder.markdown("● ● ●")
        # try:
        #     response_text = st.write_stream(
        #         ask_stream(question, st.session_state.chat_history)
        #     )
        #     citations = ask_stream.last_chunks

        #     if citations:
        #         with st.expander(f"Sources ({len(citations)} chunks)"):
        #             for c in citations:
        #                 st.markdown(
        #                     f"**{c['source']}** — page {c['page']} "
        #                     f"*(relevance: {c['score']})*\n\n> {c['text'][:300]}..."
        #                 )

        # except RuntimeError as e:
        #     response_text = str(e)
        #     citations = []
        #     st.error(response_text)
        
        # 📄 DOCUMENT MODE
        if has_docs:
            try:
                full_response = ""
                for chunk_text in ask_stream(question, st.session_state.chat_history, session_id=st.session_state.session_id):
                    full_response += chunk_text
                    typing_placeholder.markdown(full_response + "▌")
                
                typing_placeholder.markdown(full_response)
                response_text = full_response
                citations = ask_stream.last_chunks
                
                # response_text = st.write_stream(
                #     ask_stream(question, st.session_state.chat_history, session_id=st.session_state.session_id)
                # )
                # citations = ask_stream.last_chunks
                
                
                # st.session_state.last_chunks = citations

                # if citations:
                #     with st.expander(f"Sources ({len(citations)} chunks)"):
                #         for c in citations:
                #             st.markdown(
                #                 f"**{c['source']}** — page {c['page']} "
                #                 f"*(relevance: {c['score']})*\n\n> {c['text'][:300]}..."
                #             )
            # except RuntimeError as e:
            #     response_text = str(e)
            #     citations = []
            #     st.error(response_text)
            except RuntimeError as e:
                response_text = str(e)
                citations = []
                typing_placeholder.error(response_text)

        # General Chat
        else:
            citations = []
            try:
                def general_chat_stream():
                    stream = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": "You are a helpful and friendly general-purpose AI assistant."},
                            *[
                                {"role": m["role"], "content": m["content"]}
                                for m in st.session_state.messages
                            ],
                        ],
                        stream=True,
                    )
                    for chunk in stream:
                        text = chunk.choices[0].delta.content
                        if text:
                            yield text

                full_response = ""
                for chunk_text in general_chat_stream():
                    full_response += chunk_text
                    typing_placeholder.markdown(full_response + "▌")
                    
                typing_placeholder.markdown(full_response)
                response_text = full_response

            except Exception as e:
                response_text = f"Error: {str(e)}"
                typing_placeholder.error(response_text)

    # Update history
    st.session_state.messages.append({
        "role": "assistant",
        "content": response_text,
        "citations": citations,
    })

    st.session_state.chat_history.extend([
        {"role": "user", "content": question},
        {"role": "assistant", "content": response_text},
    ])
    
    st.rerun()
