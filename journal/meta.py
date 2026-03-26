import sys
import os
import re
import json
import datetime
import argparse

from bs4 import BeautifulSoup
from selenium import webdriver

root_path = os.path.dirname(os.path.dirname(__file__))
sys.dont_write_bytecode = True
sys.path.append(root_path)
from journal.post import sim, search
from utils.const import LABELS, BRANDS

parser = argparse.ArgumentParser()
parser.add_argument("-y", "--year", type=int, default=None)
parser.add_argument("-m", "--month", type=int, default=None)
parser.add_argument("-d", "--data", type=str, default=None)

args = parser.parse_args()
now = datetime.datetime.now()

now_year = args.year if args.year else now.year
now_month = args.month if args.month else now.month
month_str = f"{now_year}{now_month:02d}"

data_path = args.data if args.data else os.path.join(root_path, f"data/{month_str}")
json_path = os.path.join(data_path, f"data.json")
info_path = os.path.join(data_path, f"info.json")

imgs_path = os.path.join(data_path, f"images")
os.makedirs(imgs_path, exist_ok=True)

def _filter(title, response, series):
    return [{
        "title": entry["name"],
        "link": f"https://bgm.tv/subject/{entry['id']}",
        "conf": sim(title, entry["name"])
    } for entry in response["data"]
        if entry["platform"] in ("小说", "其他") \
            and entry["series"] is series \
            and sim(title, entry["name"]) >= 0.5
    ]

def _init(todo, title, link, label, date):
    todo.append({
        "title": title,
        "page": None,
        "link": link,
        "info": {
            "author": [],
            "illust": [],
            "publisher": label["pub"],
            "label": label["jp"],
            "price": "",
            "date": date,
            "pages": "",
            "isbn": ""
        },
        "desc": "",
        "cover": {
            "link": "",
            "stage": 0
        },
        "series": {
            "name": "",
            "order": 0,
            "abstract": []
        },
        "search": {
            "single": [],
            "series": []
        },
        "stage": 0
    })

def _split(cc_str):
    # content creators (cc_str) example:
    # "泉サリ(著・絵)"
    # "浅葱(著) , しの(絵)"
    author, illust = [], []
    if len(cc_str) == 0:
        return author, illust

    cc_list = [item.strip() for item in cc_str.split(",")]
    for cc_item in cc_list:
        if cc_item.endswith("(著・絵)"):
            author.append(cc_item[:-5])
            illust.append(cc_item[:-5])
        elif cc_item.endswith("(著)"):
            author.append(cc_item[:-3])
        elif cc_item.endswith("(絵)"):
            illust.append(cc_item[:-3])
    return author, illust

def save_info(todo):
    with open(info_path, mode="w", encoding="utf-8") as w:
        json.dump(todo, w, ensure_ascii=False, indent=4)

def init_info():
    if os.path.exists(info_path):
        with open(info_path, mode="r", encoding="utf-8") as r:
            return json.load(r)

    else:
        todo = []
        with open(json_path, mode="r", encoding="utf-8") as r:
            books = json.load(r)

        for date in books["items"]:
            for label in books["items"][date]:
                for book in books["items"][date][label]:
                    assert book["page"] is not None
                    if book["page"] == "":
                        _init(
                            todo,
                            book["title"],
                            book["link"],
                            LABELS[label],
                            f"{now.year}-{now.month:02d}-{int(date):02d}"
                        )

        save_info(todo)
        return todo

def fill_info(todo):
    index = 0
    while True:
        if index >= len(todo):
            break
        item = todo[index]

        if item["stage"] == 0:
            driver = webdriver.Chrome()
            if BRANDS["rakuten"] not in item["link"]:
                del todo[index]
                continue

            rakuten_link = item["link"][BRANDS["rakuten"]]
            bid = re.search(r'rb/(\d+)', rakuten_link)[1]
            driver.get(rakuten_link)
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")

            # get meta info
            meta = {
                item.select_one("span.category").text.strip():
                item.select_one("span.categoryValue").text.strip()
                for item in soup.select("li.productInfo")
            }

            author, illust = _split(meta.get("著者／編集", ""))
            price = round(int(soup.select_one("span.price")["content"]) * 10 / 11)

            item["info"]["author"] = author
            item["info"]["illust"] = illust
            item["info"]["price"] = str(price)
            item["info"]["pages"] = meta.get("ページ数", "").strip("p")
            item["info"]["isbn"] = meta.get("ISBN", "")

            # get first desc from jpro / book database
            desc = {
                item.text.strip(): item.find_next_sibling().text.strip()
                for item in soup.select("div.saleDesc h3")
            }
            if len(desc) > 0:
                item["desc"] = list(desc.values())[0]

            # download image of cover
            ...

            # process series
            ...

            item["stage"] = 1
            save_info(todo)

        if item["stage"] == 1:
            title = item["title"]
            response = search()
            item["series"] = _filter(title, response, series=True)
            item["search"] = _filter(title, response, series=False)
            item["stage"] = 2

            save_info(todo)

        index += 1

if __name__ == "__main__":
    todo = init_info()
    fill_info(todo)
