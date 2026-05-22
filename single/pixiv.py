import os
import re
import time
import json
import argparse

from typing import List
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementClickInterceptedException

parser = argparse.ArgumentParser()
parser.add_argument("-u", "--uid", type=str, default="2948941")
parser.add_argument("-s", "--srt", type=int, default=1)
parser.add_argument("-d", "--dst", type=str, default="~/Downloads/dst")
parser.add_argument("-c", "--cli", action="store_true")
parser.add_argument("-l", "--login", action="store_true")

args = parser.parse_args()
page_url = lambda uid, page: f"https://www.pixiv.net/users/{uid}/novels?p={page}"
text_url = lambda pid: f"https://www.pixiv.net/novel/show.php?id={pid}"

dst_dir = os.path.expanduser(args.dst)
os.makedirs(dst_dir, exist_ok=True)

INTRO_SELECTOR = 'p[id^="expandable-paragraph"]'
PARAS_SELECTOR = 'p, h1, h2, h3, h4, h5, h6'
NEXT_SELECTOR = 'button[class$="footer-pager-next"]'

class Record:
    def __init__(self, filename="record.json"):
        self._path = os.path.join(dst_dir, filename)
        if not os.path.exists(self._path):
            with open(self._path, mode="w", encoding="utf-8") as writable:
                writable.write("[]")
            self._data = []
        else:
            with open(self._path, mode="r", encoding="utf-8") as readable:
                self._data: List[str] = json.load(readable)

    def push(self, item: str):
        self._data.append(item)
        with open(self._path, mode="w", encoding="utf-8") as writable:
            json.dump(self._data, writable)

    def __contains__(self, item: str):
        return item in self._data

def cruise_text(driver):
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    paras = soup.select_one('main main').select(PARAS_SELECTOR)
    texts = "\n\n".join([(
        para.get_text("\n").strip()
        if para.name == "p"
        else ("#" * (int(para.name[1]) + 2) + " "+ para.get_text("\n").strip())
    ) for para in paras])

    return soup, texts

def cruise_page(driver, index, record):
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    tabs = [
        [a.attrs["href"] for a in tab.select('a')]
        for tab in soup.select('li[offset="0"]')
    ]

    pids = [[
        link for link in tab
        if link.startswith("/novel/show.php")
    ][0].split("?id=")[1] for tab in tabs]

    for pid in pids:
        file_path = os.path.join(dst_dir, f"{pid}.md")
        if pid in record:
            continue

        driver.get(text_url(pid))
        time.sleep(4)
        sub_soup, text = cruise_text(driver)

        title = sub_soup.select_one('h1').text
        intro = sub_soup.select_one(INTRO_SELECTOR)
        intro = intro.get_text("\n") if intro else None

        texts = [text]
        panel = sub_soup.select_one('h1').parent
        series = panel.select_one('a[href^="/novel/series"]')

        while len(sub_soup.select(NEXT_SELECTOR)) > 0:
            try:
                driver.find_element(By.CSS_SELECTOR, NEXT_SELECTOR).click()
            except ElementClickInterceptedException:
                pack = driver.current_url.split("#")
                tag = int(pack[1]) + 1 if len(pack) > 1 else 2
                driver.get(f"{pack[0]}#{tag}")
            time.sleep(2)

            sub_soup, text = cruise_text(driver)
            texts.append(text)

        block = f"### {title}\n\n"
        if intro is not None:
            block += f"{intro}\n\n"
            block += f"---\n\n"
        block += "\n\n\n\n　◇\n\n\n\n".join(texts).strip()

        if series is not None:
            series_title = series.text.split(" #")[0]
            series_id = re.search(r'(\d+)', series.attrs["href"])[1]
            file_path = os.path.join(dst_dir, f"s{series_id}.md")

            if os.path.exists(file_path):
                with open(file_path, mode="r", encoding="utf-8") as readable:
                    lines = readable.read().splitlines()
                lines.insert(2, block + "\n\n\n")
                block = "\n".join(lines)
            else:
                block = f"## {series_title}\n\n" + block

        with open(file_path, mode="w", encoding="utf-8") as writable:
            writable.write(block + "\n")

        print(f"{pid}: {title}")
        record.push(pid)

    return len(soup.select(f'a[href$="p={index+1}"]')) > 0

if __name__ == "__main__":
    options = webdriver.ChromeOptions()
    if args.cli and not args.login:
        options.add_argument("--headless=new")
    driver = webdriver.Chrome()

    index = args.srt
    record = Record()

    while True:
        driver.get(page_url(args.uid, index))
        if index == args.srt and args.login:
            print("login manually to access hidden post")
            breakpoint()
            driver.get(page_url(args.uid, index))

        time.sleep(4)
        if cruise_page(driver, index, record):
            index += 1
        else:
            exit(0)
