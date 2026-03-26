import sys
import os
import json
import datetime
import argparse

from selenium import webdriver

root_path = os.path.dirname(os.path.dirname(__file__))
sys.dont_write_bytecode = True
sys.path.append(root_path)
from journal.post import sim, search
from utils.const import LABELS

parser = argparse.ArgumentParser()
parser.add_argument("-y", "--year", type=int, default=None)
parser.add_argument("-m", "--month", type=int, default=None)
parser.add_argument("-d", "--data", type=str, default=None)

args = parser.parse_args()
now = datetime.datetime.now()
todo = []

now_year = args.year if args.year else now.year
now_month = args.month if args.month else now.month
month_str = f"{now_year}{now_month:02d}"

data_path = args.data if args.data else os.path.join(root_path, f"data/{month_str}")
json_path = os.path.join(data_path, f"data.json")
info_path = os.path.join(data_path, f"info.json")

def filter(series: bool):
    return [{
        "title": entry["name"],
        "link": f"https://bgm.tv/subject/{entry['id']}",
        "conf": sim(item["title"], entry["name"])
    } for entry in response["data"]
        if entry["platform"] in ("小说", "其他") \
            and entry["series"] is series \
            and sim(item["title"], entry["name"]) >= 0.5
    ]

if __name__ == "__main__":
    with open(json_path, mode="r", encoding="utf-8") as r:
        books = json.load(r)

    for date in books["items"]:
        for label in books["items"][date]:
            for book in books["items"][date][label]:
                if book["page"] == "":
                    todo.append({
                        "title": book["title"],
                        "page": None,
                        "link": book["link"],
                        "info": {
                            "author": "",
                            "illust": "",
                            "publisher": "",
                            "label": LABELS[label][0],
                            "price": "",
                            "date": f"{now.year}-{now.month:02d}-{int(date):02d}",
                            "pages": "",
                            "isbn": ""
                        },
                        "desc": "",
                        "cover": "",
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

    with open(info_path, mode="w", encoding="utf-8") as w:
        json.dump(todo, w, ensure_ascii=False, indent=4)

    for item in todo:
        if item["stage"] == 0:
            # driver = webdriver.Chrome()

            item["stage"] = 1
            with open(info_path, mode="w", encoding="utf-8") as w:
                json.dump(todo, w, ensure_ascii=False, indent=4)

        if item["stage"] == 1:
            response = search(item["title"])
            # item["series"] = filter(True)
            # item["search"] = filter(False)
            # item["stage"] = 2

            with open(info_path, mode="w", encoding="utf-8") as w:
                json.dump(todo, w, ensure_ascii=False, indent=4)
