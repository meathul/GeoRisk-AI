---

# 🔧 Setup Instructions for ChromaDB Creation & Agent Scripts

This guide will walk you through setting up and running the scripts that process PDF documents, convert them to text, and store them in a Chroma vector store for downstream use with LLM agents.

---

## 📁 Directory Structure

```
processing/
├── pdfs/                  # Put your source PDF files here
├── docs/                  # Auto-generated .txt files from PDFs
├── chroma_store/          # Auto-generated Chroma vector store files
├── load_pdfs_to_chroma.py # Converts PDFs to text and stores embeddings
├── main.py                # Additional logic (e.g., for agent interaction)
├── .gitignore
└── requirements.txt
```

---

## ⚙️ 1. Setup Python Environment

### 🐍 Create and activate a virtual environment (optional but recommended)

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

### 📦 Install required dependencies

```bash
pip install -r processing/requirements.txt
```

---

## 📥 2. Add PDF Files

Place your PDF files inside the `processing/pdfs/` directory.
These will be automatically converted to `.txt` files in `processing/docs/`.

---

## 🚀 3. Run the Processing Script

This script does three things:

1. Converts PDFs to `.txt`
2. Splits the text into chunks
3. Embeds the chunks and saves them to a Chroma vector store

### ▶️ Command:

```bash
python processing/load_pdfs_to_chroma.py
```

You should see log messages confirming:

* PDFs converted to `.txt`
* Texts split into chunks
* Embeddings saved to `processing/chroma_store/`

---

## ✅ Result

After the script runs:

* Your `.txt` files will be in `processing/docs/`
* Your Chroma DB will be in `processing/chroma_store/`

These are now ready to be used in any retrieval-augmented generation (RAG) pipeline or LLM agent interaction.

---


## 🛑 Ignore These in Git

Make sure `.gitignore` contains:

```gitignore
venv/
__pycache__/
*.pyc
processing/pdfs/
processing/docs/
processing/chroma_store/
.env
```

---
