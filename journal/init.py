import sys
import os
import re
import time
import json
import urllib
import datetime
import requests

from tqdm import tqdm
from bs4 import BeautifulSoup

sys.dont_write_bytecode = True
from utils.const import LABELS, BRANDS

now = datetime.datetime.now()
books = {
    "logs": [
        {
            "action": "init",
            "timestamp": int(now.timestamp() * 1000),
            "details": {
                "total": 0
            }
        }
    ],
    "items": {}
}

month_str = f"{now.year}{now.month:02d}"
data_path = os.path.join(os.path.split(__file__)[0], f"data/{month_str}")
json_path = os.path.join(data_path, f"data.json")

def clean_url(site, url):
    if site == BRANDS["rakuten"]:
        parsed = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed.query)

        target_url = query_params.get("pc", [None])[0]
        if target_url:
            target = urllib.parse.urlparse(target_url)
            clean_link = f"{target.scheme}://{target.netloc}{target.path}"
            return clean_link

    elif site == BRANDS["valuecommerce"]:
        parsed = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed.query)

        target_url = query_params.get("vc_url", [None])[0]
        if target_url:
            return urllib.parse.quote(target_url, safe=':/?=&')

    return url

def add_book(date: int, label: str, title: str, url: str) -> None:
    global books

    if date not in books["items"]:
        books["items"][date] = {}

    if label not in books["items"][date]:
        books["items"][date][label] = []

    books["items"][date][label].append({
        "title": title,
        "page": None,
        "link": url
    })
    books["logs"][-1]["details"]["total"] += 1

def add_books(soup: BeautifulSoup) -> None:
    global LABELS
    tags = soup.select("div.book")

    for tag in tags:
        if tag.select_one(".t_ul") is None:
            continue

        date = re.match(r"\d+/(\d+)\(.\)", tag.select_one(".book_info").text)[1]
        label = tag.select_one(".t_ul").attrs["href"].split("/")[3]
        title = tag.select_one(".book_title").text

        url = {
            list(BRANDS.values())[occur.index(True)]: a["href"] 
            for a in tag.select("div.book_btn_box>a")
            if any(occur := [key in a["href"] for key in BRANDS])
        }

        if label in LABELS:
            add_book(date, label, title, {
                key: clean_url(key, url[key])
                for key in url
            })

if __name__ == "__main__":
    os.makedirs(data_path, exist_ok=True)
    response = requests.get(f"https://lnovel.jp/lightnovel/monthlies/{month_str}")
    assert response.status_code == 200

    soup = BeautifulSoup(response.text, "html.parser")
    page_count = len(soup.select_one("ul.pagination").select("li"))
    add_books(soup)

    for page in tqdm(range(1, page_count)):
        url = f"https://lnovel.jp/lightnovel/monthlies/{month_str}/page/{page + 1}"
        response = requests.get(url)
        assert response.status_code == 200

        soup = BeautifulSoup(response.text, "html.parser")
        add_books(soup)
        time.sleep(5)

        with open(json_path, mode="w", encoding="utf-8") as w:
            json.dump(books, w, ensure_ascii=False, indent=4)
