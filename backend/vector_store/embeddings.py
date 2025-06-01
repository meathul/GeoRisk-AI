import os
import fitz
from functools import partial
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from huggingface_hub import login
from dotenv import load_dotenv

load_dotenv()
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_HUB_TOKEN")
login(HUGGINGFACE_TOKEN)

CONFIGS = {
    "climate": {
        "pdf_dir": "climate_pdf",
        "text_dir": "climate_docs",
        "chroma_dir": "climate_chroma_db"
    },
    "risk": {
        "pdf_dir": "risk_pdf",
        "text_dir": "risk_docs",
        "chroma_dir": "risk_chroma_db"
    }
}

def pdf_to_text(pdf_path, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    filename = os.path.basename(pdf_path).replace(".pdf", ".txt")
    output_path = os.path.join(output_dir, filename)
    doc = fitz.open(pdf_path)
    all_text = "".join([page.get_text() for page in doc])
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(all_text)
    print(f"Extracted: {output_path}")
    return output_path

def convert_all_pdfs(pdf_dir, text_dir):
    print(f"Converting PDFs from {pdf_dir} to text...")
    count = 0
    for filename in os.listdir(pdf_dir):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(pdf_dir, filename)
            print(f"Found PDF: {pdf_path}")
            pdf_to_text(pdf_path, text_dir)
            count += 1
    print(f"Converted {count} PDFs from {pdf_dir}.")

def load_documents(text_dir):
    print(f"Loading text documents from {text_dir}...")
    utf8_loader = partial(TextLoader, encoding="utf-8")
    loader = DirectoryLoader(text_dir, glob="**/*.txt", loader_cls=utf8_loader)
    documents = loader.load()
    print(f"Loaded {len(documents)} documents.")
    return documents

def split_documents(documents):
    print("Splitting documents into chunks...")
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(documents)
    print(f"Split into {len(chunks)} chunks.")
    return chunks

def save_to_chroma(chunks, chroma_dir):
    print(f"Saving embeddings to Chroma vector store at {chroma_dir}...")
    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    vectordb = Chroma.from_documents(chunks, embedding=embeddings, persist_directory=chroma_dir)
    vectordb.persist()
    print(f"Chroma vector store saved at: {chroma_dir}")

def run_pipeline(name):
    cfg = CONFIGS[name]
    convert_all_pdfs(cfg["pdf_dir"], cfg["text_dir"])
    documents = load_documents(cfg["text_dir"])
    chunks = split_documents(documents)
    save_to_chroma(chunks, cfg["chroma_dir"])

if __name__ == "__main__":
    print("Running Climate Pipeline...")
    run_pipeline("climate")
    print("Running Business Risk Pipeline...")
    run_pipeline("risk")
