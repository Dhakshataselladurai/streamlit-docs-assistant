"""
Streamlit Documentation Scraper (Improved)

Scrapes the Streamlit API documentation and stores it in JSON format.

Output:
data/docs/streamlit_docs.json
"""

import os
import json
import time
import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://docs.streamlit.io"
API_REFERENCE_URL = "https://docs.streamlit.io/develop/api-reference"

OUTPUT_DIR = "data/docs"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "streamlit_docs.json")

REQUEST_DELAY = 1

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}


def discover_doc_urls(start_url):
    """Collect all Streamlit documentation URLs."""

    print("Discovering documentation pages...")

    response = requests.get(
        start_url,
        headers=HEADERS,
        timeout=20,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")

    urls = set()

    for link in soup.find_all("a", href=True):

        href = link["href"]

        if (
            href.startswith("/develop/api-reference/")
            or href.startswith("/library/")
        ):

            full_url = urljoin(BASE_URL, href)

            full_url = full_url.split("#")[0]

            urls.add(full_url)

    urls = sorted(urls)

    print(f"Found {len(urls)} documentation pages.\n")

    return urls


def extract_page(url):
    """Extract documentation page."""

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=20,
        )

        response.raise_for_status()

    except Exception as e:

        print(f"Skipped {url}")

        print(e)

        return None

    soup = BeautifulSoup(response.text, "lxml")

    main = soup.find("article")

    if main is None:
        main = soup.find("main")

    if main is None:
        main = soup

    title = ""

    h1 = main.find("h1")

    if h1:
        title = h1.get_text(" ", strip=True)
    elif soup.title:
        title = soup.title.get_text(" ", strip=True)
    else:
        title = url.split("/")[-1]

    paragraphs = []

    for tag in main.find_all(["p", "li"]):

        text = tag.get_text(" ", strip=True)

        if len(text) > 0:
            paragraphs.append(text)

    text = "\n\n".join(paragraphs)

    code_blocks = []

    for pre in main.find_all("pre"):

        code = pre.get_text("\n", strip=True)

        if code:
            code_blocks.append(code)

    if not text and not code_blocks:
        return None

    return {
        "library": "streamlit",
        "source": "official_docs",
        "version": "latest",
        "title": title,
        "url": url,
        "text": text,
        "code_blocks": code_blocks,
        "scraped_at": datetime.date.today().isoformat(),
    }


def main():

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    urls = discover_doc_urls(API_REFERENCE_URL)

    documents = []

    total = len(urls)

    for i, url in enumerate(urls, start=1):

        print(f"[{i}/{total}] {url}")

        page = extract_page(url)

        if page:
            documents.append(page)

        time.sleep(REQUEST_DELAY)

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            documents,
            f,
            indent=4,
            ensure_ascii=False,
        )

    print("\n===================================")
    print("Scraping Completed")
    print(f"Pages Saved : {len(documents)}")
    print(f"Output File : {OUTPUT_FILE}")
    print("===================================")


if __name__ == "__main__":
    main()