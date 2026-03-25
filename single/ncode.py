import os
import time
import argparse

from tqdm import tqdm
from bs4 import BeautifulSoup
from selenium import webdriver

parser = argparse.ArgumentParser()
parser.add_argument("-n", "--ncode", type=str, default="n0770fw")
parser.add_argument("-d", "--dst", type=str, default="~/Downloads/dst")
parser.add_argument("-v", "--vol", type=int, default=1)
parser.add_argument("-c", "--cli", action="store_true")

args = parser.parse_args()
args_dst = os.path.expanduser(args.dst)
os.makedirs(args_dst, exist_ok=True)
url = lambda ncode, p_idx: f"https://ncode.syosetu.com/{ncode}/?p={p_idx}/"

def request_list(driver):
    vol_index = args.vol
    pg_index = 1
    pg_total = 1

    title = ""
    chap_list = []

    while True:
        driver.get(url(args.ncode, pg_index))
        time.sleep(4)
        soup = BeautifulSoup(driver.page_source, "html.parser")

        if pg_index == 1:
            title = soup.select_one(".p-novel__title").text
            last_link = soup.select_one(".c-pager__item--last")
            if last_link:
                pg_total = int(last_link["href"].split("?p=")[1])

        for tab in soup.select(".p-eplist > div"):
            classes = tab.get("class", [])
            if "p-eplist__chapter-title" in classes:
                chap_list.append({
                    "title": tab.text.strip(),
                    "index": vol_index,
                    "chapters": []
                })
                vol_index += 1

            elif "p-eplist__sublist" in classes:
                if len(chap_list) == 0:
                    chap_list.append({
                        "title": "",
                        "index": vol_index,
                        "chapters": []
                    })
                    vol_index += 1

                a = tab.select_one("a")
                href = a["href"]

                if href.startswith("/"):
                    href = "https://ncode.syosetu.com" + href

                chap_list[-1]["chapters"].append({
                    "title": a.text.strip(),
                    "href": href
                })

        pg_index += 1
        if pg_index > pg_total:
            break

    return title, chap_list

def request_text(driver, title, chap_list):
    pbar = tqdm(total=sum(len(v["chapters"]) for v in chap_list))

    for list_index, volume in enumerate(chap_list):
        volume_file_path = os.path.join(args_dst, f"{volume['index']:02d}.md")

        with open(volume_file_path, mode="w", encoding="utf-8") as writable:
            if list_index == 0:
                writable.write(f"# {title}\n\n")
            if volume['title']:
                writable.write(f"## {volume['title']}\n\n")
            writable.flush()

            for chap_index, chapter in enumerate(volume["chapters"]):
                driver.get(chapter["href"])
                time.sleep(4)

                soup = BeautifulSoup(driver.page_source, "html.parser")
                text_div = soup.select_one("div.js-novel-text.p-novel__text")

                text = ""
                for p in text_div.find_all("p"):
                    text += p.get_text().strip() + "\n"

                if chap_index > 0:
                    writable.write("\n\n")
                writable.write(f"### {chapter['title']}\n\n")
                writable.write(text.strip() + "\n\n")
                writable.flush()
                pbar.update(1)

if __name__ == "__main__":
    options = webdriver.ChromeOptions()
    if args.cli:
        options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)

    title, chap_list = request_list(driver)
    request_text(driver, title, chap_list)
