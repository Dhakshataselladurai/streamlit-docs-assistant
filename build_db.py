import json
import chromadb
from chromadb.utils import embedding_functions

INPUT_FILE = "data/docs/chunked_docs.json"

# Load chunked documents
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    chunks = json.load(f)

# Create Chroma client
client = chromadb.PersistentClient(path="chroma_db")

# Embedding model (free)
embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# Delete old collection if it exists
try:
    client.delete_collection("streamlit_docs")
except:
    pass

collection = client.create_collection(
    name="streamlit_docs",
    embedding_function=embedding_function
)

print("Adding documents...")

for chunk in chunks:
    collection.add(
        ids=[str(chunk["chunk_id"])],
        documents=[chunk["text"]],
        metadatas=[{
            "title": chunk["title"],
            "url": chunk["url"],
            "library": chunk["library"],
            "source": chunk["source"],
            "version": chunk["version"]
        }]
    )

print("=" * 50)
print("Database Created Successfully!")
print("Total Documents:", collection.count())
print("=" * 50)