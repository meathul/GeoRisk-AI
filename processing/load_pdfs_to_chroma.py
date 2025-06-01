import os
import fitz  # PyMuPDF
from functools import partial
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Set paths
PDF_DIR = "pdfs"      # Folder with input PDFs
TEXT_DIR = "docs"     # Folder to save extracted text files
CHROMA_DIR = "chroma_store"  # Folder to save Chroma vector store

# Step 0: Convert PDF to text
def pdf_to_text(pdf_path, output_dir=TEXT_DIR):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    filename = os.path.basename(pdf_path).replace(".pdf", ".txt")
    output_path = os.path.join(output_dir, filename)

    doc = fitz.open(pdf_path)
    all_text = ""

    for page in doc:
        all_text += page.get_text()

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(all_text)

    print(f"✅ Extracted: {output_path}")
    return output_path

def convert_all_pdfs():
    print("📥 Converting PDFs to text...")
    count = 0
    for filename in os.listdir(PDF_DIR):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(PDF_DIR, filename)
            print(f"🔍 Found PDF: {pdf_path}")
            pdf_to_text(pdf_path)
            count += 1
    print(f"✅ Converted {count} PDFs.\n")

# Step 1: Load all .txt files
def load_documents():
    print("📄 Loading text documents...")
    utf8_loader = partial(TextLoader, encoding="utf-8")
    loader = DirectoryLoader(TEXT_DIR, glob="**/*.txt", loader_cls=utf8_loader)
    documents = loader.load()
    print(f"✅ Loaded {len(documents)} documents.")
    return documents

# Step 2: Split documents into smaller chunks
def split_documents(documents):
    print("✂️ Splitting documents into chunks...")
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(documents)
    print(f"✅ Split into {len(chunks)} chunks.")
    return chunks

# Step 3: Embed and store in Chroma
def save_to_chroma(chunks):
    print("📦 Saving embeddings to Chroma vector store...")
    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    vectordb = Chroma.from_documents(chunks, embedding=embeddings, persist_directory=CHROMA_DIR)
    vectordb.persist()
    print("✅ Chroma vector store saved at:", CHROMA_DIR)

# Pipeline
def run_pipeline():
    convert_all_pdfs()
    documents = load_documents()
    chunks = split_documents(documents)
    save_to_chroma(chunks)

if __name__ == "__main__":
    run_pipeline()
