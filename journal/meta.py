import sys
import os
import json
import datetime

from selenium import webdriver

sys.dont_write_bytecode = True
from post import sim, search
from utils.const import LABELS

now = datetime.datetime.now()
todo = []

month_str = f"{now.year}{now.month:02d}"
data_path = os.path.join(os.path.split(__file__)[0], f"data/{month_str}")
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
            driver = webdriver.Chrome()
            


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
