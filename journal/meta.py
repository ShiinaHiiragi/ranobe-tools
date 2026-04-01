import sys
import os
import re
import io
import json
import time
import datetime
import argparse

import dotenv
import requests
from urllib.parse import urlparse

from tqdm import tqdm
from PIL import Image
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

root_path = os.path.dirname(os.path.dirname(__file__))
sys.dont_write_bytecode = True
sys.path.append(root_path)
from journal.post import sim, search
from utils.const import BRANDS

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

dotenv.load_dotenv(os.path.join(root_path, ".env"))
user_agent = os.environ.get("USER_AGENT", "")
httpx_proxy = os.environ.get("HTTPX_PROXY", "")

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

def _parse(date_str):
    if (m := re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date_str)):
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"

def _convert(img_data, img_name):
    img = Image.open(io.BytesIO(img_data))
    if img.format != "JPEG":
        img_name = os.path.splitext(img_name)[0] + ".jpg"
        img.convert("RGB").save((buf := io.BytesIO()), format="JPEG")
        img_data = buf.getvalue()
    return img_data, img_name

def _half(name):
    return name.translate(str.maketrans(
        '　＂＃＄％＆＇（）＊＋，－．／０１２３４５６７８９：；＜＝＞＠ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ［＼］＾＿｀ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ｛｜｝～',
        ' "#$%&\'()*+,-./0123456789:;<=>@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~'
    ))

def _format(item):
    item["_title"] = item["title"]
    item["title"] = _half(item["title"])
    item["info"]["author"] = [_half(name) for name in item["info"]["author"]]
    item["info"]["illust"] = [_half(name) for name in item["info"]["illust"]]

def _popup(driver):
    try:
        popup = driver.find_element(By.CSS_SELECTOR, "div[id^=zigzag]")
        sroot = popup.shadow_root
        sroot.find_element(By.CSS_SELECTOR, "button[id$=close]").click()
        time.sleep(2)

    except NoSuchElementException:
        ...

def _read_one(item, driver):
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
    item["info"]["price"] = f"￥{price}"
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
    img_element = soup.select("div#imageSliderWrap img")[0]
    img_url = "https:" + img_element.attrs["src"].split("?")[0]

    img_name = os.path.basename(urlparse(img_url).path)
    img_path = os.path.join(imgs_path, img_name)
    item["cover"] = None if img_url.endswith(".gif") else img_name

    if item["cover"] is not None and not os.path.exists(img_path):
        session = requests.Session()
        session.headers["User-Agent"] = user_agent
        for cookie in driver.get_cookies():
            session.cookies.set(cookie["name"], cookie["value"])

        response = session.get(img_url)
        img_data, img_name = _convert(response.content, img_name)
        with open(img_path, "wb") as f:
            f.write(img_data)

    if "シリーズ" in meta:
        item["series"]["name"] = meta["シリーズ"]
        series_links = [
            item.select_one("a") for item in soup.select("li.productInfo")
            if item.select_one("span.category").text.strip() == "シリーズ"
        ]
        return __import__("html").unescape(series_links[0]["href"])

    else:
        item["series"] = None

def _read_series(item, driver):
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    volumes = [{
        "title": item.select_one(".info__title").text,
        "date": _parse(item.select_one(".info__date").text)
    } for item in soup.select(".list__info ")]

    is_desc = "新" in soup.select_one(".sort__order__list > .active").text
    volumes = list(reversed(volumes)) if is_desc else volumes

    item["series"]["order"] = next(
        i for i, v in enumerate(volumes)
        if v["date"] == item["info"]["date"]
    )
    item["series"]["abstract"] = volumes

def save_info(todo):
    with open(info_path, mode="w", encoding="utf-8") as w:
        json.dump(todo, w, ensure_ascii=False, indent=4)

def fill_info(driver, todo):
    index = 0
    pbar = tqdm(total=len(todo))

    while True:
        if index >= len(todo):
            break

        item = todo[index]
        title = item["title"]

        if item["stage"] == 0:
            if BRANDS["rakuten"] not in item["link"]:
                del todo[index]
                pbar.update(1)
                continue

            driver.get(item["link"][BRANDS["rakuten"]])
            time.sleep(8)
            series_url = _read_one(item, driver)

            # process series
            if series_url:
                _popup(driver)
                driver.get(series_url)
                time.sleep(8)
                _read_series(item, driver)

            _format(item)
            item["stage"] = 1
            save_info(todo)

        if item["stage"] == 1:
            response = search(title)
            time.sleep(4)
            item["search"]["series"] = _filter(title, response, series=True)
            item["search"]["single"] = _filter(title, response, series=False)

            item["stage"] = 2
            save_info(todo)

        index += 1
        pbar.update(1)

if __name__ == "__main__":
    options = webdriver.ChromeOptions()
    if httpx_proxy:
        options.add_argument(f"--proxy-server={httpx_proxy}")
    driver = webdriver.Chrome(options=options)
    time.sleep(2)

    with open(info_path, mode="r", encoding="utf-8") as r:
        todo = json.load(r)
    fill_info(driver, todo)
