import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://docs.streamlit.io"
START_URL = "https://docs.streamlit.io/develop/api-reference"

# Create output folder
os.makedirs("data/docs", exist_ok=True)

# Download the API Reference page
response = requests.get(START_URL)
soup = BeautifulSoup(response.text, "lxml")

# Find all links
links = soup.find_all("a")

visited = set()

for link in links:
    href = link.get("href")

    if not href:
        continue

    if "/develop/api-reference/" not in href:
        continue

    full_url = urljoin(BASE_URL, href)

    if full_url in visited:
        continue

    visited.add(full_url)

    print("Downloading:", full_url)

print(f"\nTotal documentation pages found: {len(visited)}")