import time
import chromadb
from chromadb.utils import embedding_functions
from google import genai
from config import GEMINI_API_KEY
from github_search import search_github

# -----------------------------
# Gemini Client
# -----------------------------
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# -----------------------------
# Embedding Function
# -----------------------------
embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# -----------------------------
# ChromaDB (existing collection)
# -----------------------------
chroma_client = chromadb.PersistentClient(path="chroma_db")

collection = chroma_client.get_collection(
    name="streamlit_docs",
    embedding_function=embedding_function
)


def ask_docs(question):
    """
    Runs the full RAG workflow for a single user question and returns
    exactly one tuple: (answer, sources, github_issues).
    """

    # Defaults set up front so that no matter what happens below, the
    # single return statement at the bottom always has valid values.
    answer = "I couldn't find this information in the official Streamlit documentation."
    sources = []
    github_issues = []

    try:
        # -----------------------------
        # 1. Retrieve top documentation chunks
        # -----------------------------
        results = collection.query(
            query_texts=[question],
            n_results=8
        )

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        retrieved = []
        query_lower = question.lower()

        for doc, meta, distance in zip(documents, metadatas, distances):
            score = 1 / (1 + distance)
            retrieved.append({
                "doc": doc,
                "meta": meta,
                "score": score
            })

        # -----------------------------
        # 2. Rank exact title matches higher
        # -----------------------------
        def ranking(item):
            title = item["meta"].get("title", "").lower()
            exact_match = query_lower in title
            return (exact_match, item["score"])

        retrieved.sort(key=ranking, reverse=True)

        # -----------------------------
        # 3. Build documentation context
        # -----------------------------
        context = ""
        for i, item in enumerate(retrieved):
            context += f"""
=========================
Document {i + 1}

Title:
{item['meta'].get('title', 'Untitled')}

URL:
{item['meta'].get('url', '')}

Content:

{item['doc']}

=========================

"""

        # -----------------------------
        # 4. Search GitHub issues (never let this crash the whole answer)
        # -----------------------------
        try:
            github_issues = search_github(question)
        except Exception as e:
            print(f"GitHub search failed: {e}")
            github_issues = []

        github_context = ""
        for issue in github_issues:
            github_context += f"""
Issue Title:
{issue.get('title', '')}

Issue Body:
{issue.get('body', '')}

Issue URL:
{issue.get('url', '')}

----------------------------------------
"""

        # -----------------------------
        # 5. Build prompt for Gemini
        # -----------------------------
        prompt = f"""
You are an expert Streamlit Documentation Assistant.

You have two sources of information:

1. Official Streamlit Documentation (PRIMARY SOURCE)
2. Relevant GitHub Issues (SECONDARY SOURCE)


Instructions:

- Always answer using the Official Documentation first.
- Use GitHub Issues only to provide additional context or common solutions.
- If the documentation and GitHub disagree, always trust the documentation.
- Explain clearly in simple, direct language.
- Keep your answer concise: 2-5 sentences for simple questions, and no more than one short paragraph plus one code example for anything more complex.
- Do NOT use headers, numbered lists, or multiple sub-sections unless the question specifically asks for a comparison of multiple options.
- Include ONE short Python example only if it directly helps answer the question — do not include multiple examples or extra variations.
- If the answer cannot be found, say:
  "I couldn't find this information in the official Streamlit documentation."
==================================================
OFFICIAL DOCUMENTATION

{context}

==================================================
RELATED GITHUB ISSUES

{github_context}

==================================================

User Question:

{question}
"""

        # -----------------------------
        # 6. Ask Gemini (retry on temporary server overload)
        # -----------------------------
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = gemini_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                answer = response.text
                break  # success — stop retrying
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # 1s, 2s, 4s
                    print(f"Gemini request failed ({e}). Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"Gemini request failed after {max_retries} attempts: {e}")
                    answer = (
                        "Sorry, the AI model is currently unavailable "
                        "(high demand or a temporary outage). "
                        "Please try again in a moment."
                    )

        # -----------------------------
        # 7. Remove duplicate sources
        # -----------------------------
        unique_sources = {}
        for item in retrieved:
            url = item["meta"].get("url", "")
            if url not in unique_sources:
                unique_sources[url] = {
                    "title": item["meta"].get("title", "Untitled"),
                    "url": url,
                    "score": round(item["score"], 3)
                }

        sources = list(unique_sources.values())

    except Exception as e:
        # Catch-all so a retrieval/DB-level failure never crashes the caller.
        print(f"ask_docs failed: {e}")
        answer = (
            "Sorry, something went wrong while processing your question. "
            "Please try again."
        )
        sources = []
        github_issues = []

    # -----------------------------
    # Single return statement
    # -----------------------------
    return answer, sources, github_issues


# -----------------------------
# Terminal Test
# -----------------------------
if __name__ == "__main__":

    while True:

        question = input("\nAsk: ")

        if question.lower() == "exit":
            break

        answer, sources, github_issues = ask_docs(question)

        print("\n")
        print("=" * 70)
        print("ANSWER")
        print("=" * 70)
        print(answer)

        print("\n")
        print("=" * 70)
        print("DOCUMENTATION SOURCES")
        print("=" * 70)

        for source in sources:
            print(f"Title      : {source['title']}")
            print(f"URL        : {source['url']}")
            print(f"Similarity : {source['score']}")
            print("-" * 70)

        print("\n")
        print("=" * 70)
        print("RELATED GITHUB ISSUES")
        print("=" * 70)

        if github_issues:
            for issue in github_issues:
                print(f"Issue #{issue.get('number')}")
                print(f"Title    : {issue.get('title')}")
                print(f"State    : {issue.get('state')}")
                print(f"Comments : {issue.get('comments')}")
                print(f"URL      : {issue.get('url')}")
                print("-" * 70)
        else:
            print("No related GitHub issues found.")