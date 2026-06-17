# DocuGallery System

Ask questions across your PDF, Word, and text documents using RAG (Retrieval-Augmented Generation).

---

## Setup (VS Code)

### 1. Create a virtual environment

Open the VS Code terminal (`Ctrl + `` ` ``) and run:

```bash
python -m venv venv
```

Activate it:
- **Windows:** `venv\Scripts\activate`
- **Mac/Linux:** `source venv/bin/activate`

VS Code will ask if you want to use this environment — click **Yes**.

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

> The first run will download the embedding model (~90MB). This only happens once.

### 3. Add your OpenAI API key

Edit the `.env` file and replace the placeholder:

```
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
```

Get a key at: https://platform.openai.com/api-keys

### 4. Run the app

```bash
streamlit run app.py
```

Your browser will open automatically at `http://localhost:8501`.

---

## How to use

1. Click **Browse files** in the sidebar and upload your documents (PDF, DOCX, or TXT).
2. Click **Ingest uploaded files** — this embeds them into the local vector store.
3. Type a question in the chat input at the bottom.
4. Expand **Sources** under any answer to see which chunks were used.

---

## Project structure

```
doc_qa/
├── ingest/
│   ├── loader.py       # Extracts text from PDF, DOCX, TXT
│   ├── chunker.py      # Splits text into overlapping chunks
│   └── embedder.py     # Embeds chunks and stores in ChromaDB
├── query/
│   ├── retriever.py    # Semantic search — finds relevant chunks
│   └── generator.py    # Builds prompt and calls the LLM
├── chroma_db/          # Auto-created — your local vector store
├── app.py              # Streamlit UI
├── requirements.txt
└── .env                # Your API key goes here
```

---

## Packages used

| Package | Purpose |
|---|---|
| `PyMuPDF` | Extract text from PDFs |
| `python-docx` | Extract text from Word documents |
| `langchain-text-splitters` | Split text into overlapping chunks |
| `sentence-transformers` | Local embedding model (no API key needed) |
| `chromadb` | Local vector database for storing embeddings |
| `openai` | Call GPT for answer generation |
| `streamlit` | Web UI |
| `python-dotenv` | Load API key from `.env` file |

---

## Recommended VS Code extensions

- **Python** (Microsoft) — required
- **Pylance** — type checking and autocomplete
- **Python Debugger** — debug your code with breakpoints
