"""
Streamlit Documentation Assistant - Chat Interface
----------------------------------------------------
ChatGPT-style UI for the RAG pipeline defined in rag.py.

Expects rag.py to expose:
    answer, sources, github_issues = ask_docs(question)
"""

import streamlit as st
from rag import ask_docs, collection

# ---------------------------------------------------------------------------
# Page configuration (must be the first Streamlit command)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Streamlit Docs Assistant",
    page_icon="📘",
    layout="centered",
)

MODEL_NAME = "Gemini 2.5 Flash"

# -----------------------------
# ChromaDB status + doc page count (checked live, so the sidebar always
# reflects the real state of the database instead of a hardcoded number)
# -----------------------------
try:
    DOC_PAGE_COUNT = collection.count()
    CHROMADB_STATUS = "🟢 Connected"
except Exception:
    DOC_PAGE_COUNT = "N/A"
    CHROMADB_STATUS = "🔴 Unavailable"


# ---------------------------------------------------------------------------
# Session state setup
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []


def clear_chat():
    """Reset the conversation history."""
    st.session_state.messages = []


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("📘 Docs Assistant")
    st.caption("AI-powered Streamlit documentation helper")

    st.divider()

    st.metric("Documentation Chunks", DOC_PAGE_COUNT)
    st.write(f"**ChromaDB:** {CHROMADB_STATUS}")
    st.write(f"**Model:** {MODEL_NAME}")

    st.divider()

    st.button("🗑️ Clear Chat", on_click=clear_chat, use_container_width=True)

    st.divider()
    st.caption(
        "Answers are generated only from official Streamlit documentation "
        "and related GitHub issues."
    )


# ---------------------------------------------------------------------------
# Helper to render sources / github issues under an assistant message
# ---------------------------------------------------------------------------
def render_sources(sources):
    if not sources:
        return
    with st.expander("📄 Documentation Sources"):
        for s in sources:
            title = s.get("title", "Untitled")
            url = s.get("url", "")
            score = s.get("score", 0)

            st.markdown(f"**{title}**")
            st.caption(f"Similarity score: {score:.2f}")
            if url:
                st.link_button("Open Documentation", url)
            st.write("")


def render_github_issues(github_issues):
    if not github_issues:
        return
    with st.expander("🐙 Related GitHub Issues"):
        for issue in github_issues:
            number = issue.get("number", "")
            title = issue.get("title", "Untitled issue")
            state = issue.get("state", "unknown")
            comments = issue.get("comments", 0)
            body = issue.get("body", "") or ""
            url = issue.get("url", "")

            st.markdown(f"**#{number} — {title}**")
            st.caption(f"Status: {state} · Comments: {comments}")
            if body:
                preview = body[:200] + ("..." if len(body) > 200 else "")
                st.write(preview)
            if url:
                st.link_button("Open on GitHub", url)
            st.write("")


# ---------------------------------------------------------------------------
# Main chat area
# ---------------------------------------------------------------------------
st.title("Streamlit Documentation Assistant")
st.caption("Ask me anything about using Streamlit.")

# Welcome message shown only when there's no conversation yet.
if not st.session_state.messages:
    with st.chat_message("assistant"):
        st.write(
            "👋 Hi! I'm your Streamlit documentation assistant. "
            "Ask me how to use any Streamlit feature, widget, or API — "
            "I'll answer using the official docs and cite my sources."
        )

# Render the existing conversation history.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if message["role"] == "assistant":
            render_sources(message.get("sources") or [])
            render_github_issues(message.get("github_issues") or [])


# ---------------------------------------------------------------------------
# Chat input and response generation
# ---------------------------------------------------------------------------
user_question = st.chat_input("Ask a question about Streamlit...")

if user_question:
    # 1. Show the user's message immediately.
    with st.chat_message("user"):
        st.write(user_question)
    st.session_state.messages.append({"role": "user", "content": user_question})

    # 2. Generate and show the assistant's response.
    with st.chat_message("assistant"):
        try:
            with st.spinner("Searching documentation..."):
                answer, sources, github_issues = ask_docs(user_question)

            st.write(answer)
            render_sources(sources)
            render_github_issues(github_issues)

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                    "github_issues": github_issues,
                }
            )

        except Exception as e:
            # Never let the app crash on a bad query / API hiccup.
            error_message = (
                "⚠️ Sorry, something went wrong while generating a response. "
                "Please try again."
            )
            st.error(error_message)
            print(f"app.py error: {e}")
            st.session_state.messages.append(
                {"role": "assistant", "content": error_message}
            )