import json
import os

INPUT_FILE = "data/docs/streamlit_docs.json"
OUTPUT_FILE = "data/docs/chunked_docs.json"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100


def chunk_text(text, chunk_size=500, overlap=100):
    chunks = []

    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


def main():

    if not os.path.exists(INPUT_FILE):
        print("Input file not found!")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        documents = json.load(f)

    chunked_documents = []

    total_chunks = 0

    for doc in documents:

        chunks = chunk_text(doc["text"], CHUNK_SIZE, CHUNK_OVERLAP)

        for i, chunk in enumerate(chunks):

            chunked_documents.append({
                "chunk_id": total_chunks + 1,
                "page_chunk": i + 1,
                "title": doc["title"],
                "url": doc["url"],
                "library": doc.get("library", "streamlit"),
                "source": doc.get("source", "official_docs"),
                "version": doc.get("version", "latest"),
                "text": chunk
            })

            total_chunks += 1

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(chunked_documents, f, indent=2, ensure_ascii=False)

    print("=" * 50)
    print("Chunking Completed")
    print(f"Original Pages : {len(documents)}")
    print(f"Total Chunks   : {total_chunks}")
    print(f"Saved To       : {OUTPUT_FILE}")
    print("=" * 50)


if __name__ == "__main__":
    main()