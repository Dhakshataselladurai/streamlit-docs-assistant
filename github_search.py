import requests
import streamlit as st

GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]

OWNER = "streamlit"
REPO = "streamlit"

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}


def search_github(query, max_results=5):
    """
    Search GitHub issues related to the user's query.
    """

    search_url = (
        f"https://api.github.com/search/issues"
        f"?q={query}+repo:{OWNER}/{REPO}+is:issue"
    )

    try:
        response = requests.get(
            search_url,
            headers=HEADERS,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

    except Exception as e:
        print("GitHub Search Error:", e)
        return []

    issues = []

    for item in data.get("items", [])[:max_results]:

        body = item.get("body", "")

        if body is None:
            body = ""

        issues.append({

            "title": item["title"],

            "url": item["html_url"],

            "body": body[:500],

            "number": item["number"],

            "state": item["state"],

            "comments": item["comments"]

        })

    return issues


# ---------------------------------------
# Testing
# ---------------------------------------
if __name__ == "__main__":

    query = input("Search GitHub: ")

    results = search_github(query)

    print()

    print("=" * 60)

    print("Found", len(results), "Issues")

    print("=" * 60)

    for issue in results:

        print()

        print("Issue #", issue["number"])

        print(issue["title"])

        print(issue["state"])

        print(issue["comments"], "comments")

        print(issue["url"])

        print()

        print(issue["body"])

        print("-" * 60)
