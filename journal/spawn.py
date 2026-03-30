import os
import re
import time
import json
import argparse
import datetime
import requests

import dotenv
from bs4 import BeautifulSoup

parser = argparse.ArgumentParser()
parser.add_argument("-y", "--year", type=int, default=None)
parser.add_argument("-m", "--month", type=int, default=None)
parser.add_argument("-d", "--data", type=str, default=None)

args = parser.parse_args()
now = datetime.datetime.now()

now_year = args.year if args.year else now.year
now_month = args.month if args.month else now.month
month_str = f"{now_year}{now_month:02d}"

root_path = os.path.dirname(os.path.dirname(__file__))
data_path = args.data if args.data else os.path.join(root_path, f"data/{month_str}")
info_path = os.path.join(data_path, f"info.json")
imgs_path = os.path.join(data_path, f"images")

dotenv.load_dotenv(os.path.join(root_path, ".env"))
form_hash = os.environ.get("FORM_HASH", "")
user_agent = os.environ.get("USER_AGENT", "")
session_cookie = os.environ.get("SESSION_COOKIE", "")

def save_info(todo):
    with open(info_path, mode="w", encoding="utf-8") as w:
        json.dump(todo, w, ensure_ascii=False, indent=4)

def check_info(todo):
    for item in todo:
        assert item["stage"] == 2

def _entry(item):
    meta = f"""{{{{Infobox animanga/Novel
|作者= {",".join(item["info"]["author"])}
|插图= {",".join(item["info"]["illust"])}
|出版社= {item["info"].get("publisher", "")}
|书系= {item["info"].get("label", "")}
|价格= {item["info"].get("price", "")}
|发售日= {item["info"].get("date", "")}
|页数= {item["info"].get("pages", "")}
|ISBN= {item["info"].get("isbn", "")}
}}}}"""

    headers = {
        "Cookie": session_cookie,
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://bgm.tv",
        "Referer": "https://bgm.tv/new_subject/1",
        "User-Agent": user_agent
    }

    data = {
        "formhash": form_hash,
        "subject_title": item["title"],
        "platform": "1002",
        "subject_infobox": meta,
        "subject_summary": item["desc"],
        "subject_meta_tags": "小说",
        "editSummary": "新条目",
        "submit": "提交"
    }

    print(meta)
    input("press enter to continue...")

    response = requests.post(
        "https://bgm.tv/new_subject/1",
        headers=headers,
        data=data
    )

    return re.search(r'subject/(\d+)', response.url)[1]

def _cover(item, sid):
    image_path = os.path.join(imgs_path, item["cover"])
    upload_url = f"https://bgm.tv/subject/{sid}/upload_img"

    response = requests.get(upload_url, headers={"User-Agent": user_agent})
    response.encoding = "utf-8"
    soup = BeautifulSoup(response.text, "html.parser")

    if len(soup.select(".photoList li")) > 0:
        return

    headers = {
        "Cookie": session_cookie,
        "Origin": "https://bgm.tv",
        "Referer": upload_url,
        "User-Agent": user_agent
    }

    with open(image_path, mode="rb") as rb:
        response = requests.post(
            upload_url,
            data={"formhash": form_hash, "submit": "上传图片"},
            files={"picfile": ("cover.jpg", rb, "image/jpeg")},
            headers=headers
        )

        assert response.status_code == 200

def submit_info(todo):
    while True:
        if len(todo) == 0:
            return
        item = todo[0]

        sid = _entry(item)
        _cover(item, sid)

        del todo[0]
        save_info(todo)
        time.sleep(10)

if __name__ == "__main__":
    with open(info_path, mode="r", encoding="utf-8") as r:
        todo = json.load(r)

    check_info(todo)
    submit_info(todo)
