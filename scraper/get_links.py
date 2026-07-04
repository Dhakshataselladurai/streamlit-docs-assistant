import requests
from bs4 import BeautifulSoup

url = "https://docs.streamlit.io/develop/api-reference"

response = requests.get(url)

soup = BeautifulSoup(response.text, "lxml")

links = soup.find_all("a")

print("Total links found:", len(links))

for link in links[:20]:
    print(link.get("href"))