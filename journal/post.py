import sys
import os
import re
import time
import json
import argparse
import datetime
import unicodedata

import requests
import dotenv

from tqdm import tqdm
from bs4 import BeautifulSoup
from rapidfuzz import fuzz

root_path = os.path.dirname(os.path.dirname(__file__))
sys.dont_write_bytecode = True
sys.path.append(root_path)
from utils.const import LABELS, BRANDS

parser = argparse.ArgumentParser()
parser.add_argument("-y", "--year", type=int, default=None)
parser.add_argument("-m", "--month", type=int, default=None)
parser.add_argument("-d", "--data", type=str, default=None)
parser.add_argument("-p", "--post", type=str, default="")
parser.add_argument("-u", "--update", action="store_true")

args = parser.parse_args()
always_update = args.update
last_post = args.post

dotenv.load_dotenv()
ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]
USER_ID = os.environ["USER_ID"]
USER_AGENT = os.environ["USER_AGENT"]

now = datetime.datetime.now()
limit = 12 * 60 * 60 * 1000
lines = []

now_year = args.year if args.year else now.year
now_month = args.month if args.month else now.month
month_str = f"{now_year}{now_month:02d}"

data_path = args.data if args.data else os.path.join(root_path, f"data/{month_str}")
json_path = os.path.join(data_path, f"data.json")
text_path = os.path.join(data_path, f"post.txt")

def norm(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.lower()
    text = text.replace("!", "！")
    text = text.replace(".", "．")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[（(]([\d．.]+)[）)]", r"\1", text)
    return text

def sim(left: str, right: str) -> float:
    left = norm(left)
    right = norm(right)

    return max(
        fuzz.ratio(left, right),
        fuzz.token_sort_ratio(left, right),
        fuzz.partial_ratio(left, right),
    ) / 100

def find_uid(title, results):
    if len(results) == 0:
        return None

    sims = [sim(title, item["name"]) for item in results]
    max_index = sims.index(max(sims))

    return results[max_index]["id"] if sims[max_index] >= 0.9 else None

def search(title: str, **kwargs) -> dict:
    return requests.post(
        f"https://api.bgm.tv/v0/search/subjects",
        headers={
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "User-Agent": f"{USER_ID}/blog-info-search"
        },
        params={
            "limit": 15
        },
        json={
            "keyword": title.replace("-", ""),
            "sort": "match",
            "filter": {"type": [1], **kwargs}
        }
    ).json()

if __name__ == "__main__":
    with open(json_path, mode="r", encoding="utf-8") as r:
        books = json.load(r)

    pbar = tqdm(total=books["logs"][0]["details"]["total"])
    stage_clear = all([
        book["page"] is not None for date in books["items"]
        for label in books["items"][date]
        for book in books["items"][date][label]
    ])
    far_enough = now.timestamp() * 1000 - books["logs"][-1]["timestamp"] > limit

    if len(books["logs"]) == 1:
        books["logs"].append({
            "action": "post-first",
            "timestamp": int(now.timestamp() * 1000),
            "details": {
                "increment": 0
            }
        })

    elif always_update and stage_clear and far_enough:
        books["logs"].append({
            "action": "post-append",
            "timestamp": int(now.timestamp() * 1000),
            "details": {
                "increment": 0
            }
        })

    last_year = now.year
    last_month = now.month - 1
    if last_month == 0:
        last_month = 12
        last_year -= 1

    if last_post != "":
        last_url = f"https://bgm.tv/blog/{last_post}"
        response = requests.get(last_url, headers={"User-Agent": USER_AGENT})
        response.encoding = "utf-8"

        soup = BeautifulSoup(response.text, "html.parser")
        last_title = soup.select_one("h1.title").text.strip()
        expected_title = f"{last_year} 年 {last_month} 月文库・单行本新刊情报"
        assert last_title == expected_title, f"{last_title} ≠ {expected_title}"
        lines.append(f"[url={last_url}]{last_title}[/url]")
        time.sleep(2.5)

    lines.append(f"""无法找到对应 Bangumi 链接的可能原因：
1. 截至搜索时（{now.strftime('%Y/%#m/%#d %#H:%M')}），条目尚未创建
2. 条目记载发售时间不一致，或者列出的是已发售作品的特装版本
3. 搜索结果与标题的顺序相似度、乱序相似度及部分相似度均低于 0.9
""")

    for date in books["items"]:
        lines.append(f"[b][size=25]{now.month}/{date}[/size][/b]")
        for label in books["items"][date]:
            lines.append(f"[b][size=20]{LABELS[label][1]}[/size][/b]")
            for entry in books["items"][date][label]:
                if (always_update and stage_clear and entry["page"] == "") \
                    or entry["page"] is None:
                    date_str = f"{now.year}-{now.month:02d}-{int(date):02d}"
                    response = search(
                        entry["title"],
                        air_date=[f">={date_str}", f"<={date_str}"]
                    )
                    time.sleep(2.5)

                    uid = find_uid(entry["title"], [
                        item for item in response["data"]
                        if item["date"] == date_str \
                            and item["series"] is False \
                            and item["platform"] in ("小说", "其他")
                    ])

                    if uid is not None:
                        books["logs"][-1]["details"]["increment"] += 1
                        entry["page"] = f"https://bgm.tv/subject/{uid}"
                    else:
                        entry["page"] = ""

                    with open(json_path, mode="w", encoding="utf-8") as w:
                        json.dump(books, w, ensure_ascii=False, indent=4)

                title_text = entry["title"] if len(entry["page"]) == 0 \
                    else f"[url={entry['page']}]{entry['title']}[/url]"

                link_text = ""
                if len(entry["link"]) > 0:
                    for value in BRANDS.values():
                        if value in entry["link"]:
                            brand, url = value, entry["link"][value]
                            break
                    link_text = f" ([url={url}]{brand}[/url])"
        
                lines.append(title_text + link_text)
                pbar.update(1)

            lines.append("")

    lines.append(f"收录书系：{'、'.join([LABELS[item][1] for item in LABELS])}")
    lines.append(f"数据来源：[url=https://lnovel.jp/]ライトノベル新刊・アニメの放送予定と原作情報まとめサイト[/url]")

    with open(text_path, mode="w", encoding="utf-8") as w:
        w.write("\n".join(lines))
