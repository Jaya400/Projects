import streamlit as st
import os
import PyPDF2
import docx
import chromadb
import textwrap
from chromadb.utils.embedding_functions import GoogleGenerativeAiEmbeddingFunction
import google.generativeai as genai

# === Step 1: Configure Gemini API ===
os.environ["GOOGLE_API_KEY"] = "AIzaSyCHrPFUWdGbZAcV82nTm8WMhe9HDRwd5rg"  # <-- Replace with your Gemini API key
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

# === Step 2: Setup Embedding Function and ChromaDB Client ===
embedding_function = GoogleGenerativeAiEmbeddingFunction(api_key=os.environ["GOOGLE_API_KEY"])
chroma_client = chromadb.Client()

# Delete old collection if exists, then create new
try:
    chroma_client.delete_collection(name="docs")
except:
    pass

collection = chroma_client.create_collection(name="docs", embedding_function=embedding_function)

# === Step 3: Read and Extract Text from Uploaded File ===
def read_document(file):
    text = ""
    if file.name.endswith(".pdf"):
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            if page.extract_text():
                text += page.extract_text()
    elif file.name.endswith(".docx"):
        doc = docx.Document(file)
        for para in doc.paragraphs:
            text += para.text + "\n"
    elif file.name.endswith(".txt"):
        text = file.read().decode("utf-8")
    else:
        text = "❌ Unsupported file format."
    return text

# === Step 4: Split into Chunks ===
def chunk_text(text, max_length=500):
    paragraphs = text.split('\n')
    chunks = []
    chunk = ""
    for para in paragraphs:
        if len(chunk) + len(para) <= max_length:
            chunk += para + "\n"
        else:
            chunks.append(chunk.strip())
            chunk = para + "\n"
    if chunk:
        chunks.append(chunk.strip())
    return chunks

# === Step 5: Streamlit UI ===
st.title("📄 Document Q&A App (Powered by Gemini + ChromaDB)")

uploaded_file = st.file_uploader("Upload a document (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])

if uploaded_file:
    st.success("✅ File uploaded successfully!")

    # Extract and chunk text
    full_text = read_document(uploaded_file)
    chunks = chunk_text(full_text)

    # Store chunks in ChromaDB
    for i, chunk in enumerate(chunks):
        collection.add(
            documents=[chunk],
            metadatas=[{"chunk_id": i}],
            ids=[f"{uploaded_file.name}_chunk_{i}"]
        )

    # User asks a question
    question = st.text_input("❓ Ask a question about the document")

    if question:
        st.info("🔍 Finding the best answer...")

        # Search the most relevant chunk
        results = collection.query(query_texts=[question], n_results=1)
        relevant_chunk = results["documents"][0][0]

        # Ask Gemini
        model = genai.GenerativeModel("models/gemini-1.5-flash-latest")
        prompt = f"""Document content:\n\n{relevant_chunk}\n\nQuestion: {question}\n\nAnswer in a clear way. If it's a list, format it in lines or bullet points."""
        response = model.generate_content(prompt)

        st.markdown("### 💬 Answer")
        st.write(response.text)

else:
    st.info("📤 Upload a document to get started.")
