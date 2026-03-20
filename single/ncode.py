import os
import re
import time
import argparse

from tqdm import tqdm
from functools import reduce

from selenium import webdriver
from selenium.webdriver.common.by import By

parser = argparse.ArgumentParser()
parser.add_argument("-n", "--ncode", type=str, default="n0770fw")
parser.add_argument("-d", "--dst", type=str, default="~/Downloads/dst")
parser.add_argument("-v", "--vol", type=int, default=1)

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
        dl_index = 0
        driver.get(url(args.ncode, pg_index))
        time.sleep(4)

        if pg_index == 1:
            title = driver.find_elements(
                By.XPATH,
                '//*[@class="p-novel__title"]'
            )[0].text

            if len(last_link := driver.find_elements(
                By.XPATH,
                '//*[@class="c-pager__item c-pager__item--last"]'
            )) > 0:
                pg_total = int(last_link[0].get_attribute("href").split("?p=")[1])

        tabs_element = driver.find_elements(
            By.XPATH,
            '//*[@class="p-eplist"]/div'
        )

        for tab_element in tabs_element:
            if tab_element.get_attribute("class") == "p-eplist__chapter-title":
                volume_title = tab_element.text
                chap_list.append({
                    "title": volume_title,
                    "index": vol_index,
                    "chapters": []
                })
                vol_index += 1

            elif tab_element.get_attribute("class") == "p-eplist__sublist":
                assert len(chap_list) > 0
                link_element = driver.find_elements(
                    By.XPATH,
                    '//*[@class="p-eplist"]/div[@class="p-eplist__sublist"]/a'
                )[dl_index]

                chapter_title = link_element.text.split("\n")[0]
                chapter_link = link_element.get_attribute("href")
                chap_list[-1]["chapters"].append({
                    "title": chapter_title,
                    "href": chapter_link
                })
                dl_index += 1

        pg_index += 1
        if pg_index > pg_total:
            break

    return title, chap_list

def request_text(driver, title, chap_list):
    pbar = tqdm(total=reduce(
        lambda now, next: now + len(next["chapters"]),
        chap_list,
        0
    ))

    for list_index, volume in enumerate(chap_list):
        volume_file_path = os.path.join(args_dst, f"{volume['index']:02d}.md")

        with open(volume_file_path, mode="w", encoding="utf-8") as writable:
            if list_index == 0:
                writable.write(f"# {title}\n\n")
            writable.write(f"## {volume['title']}\n\n")
            writable.flush()

            for chapter in volume["chapters"]:
                driver.get(chapter["href"])
                time.sleep(4)

                text_elements = driver.find_elements(
                    By.XPATH,
                    '//div[@class="js-novel-text p-novel__text"]'
                )[0].get_attribute("innerHTML")

                text = re.sub("<p id=\"L\\d+\">(.+)</p>", "\\1", text_elements)
                text = re.sub("<br>", "\n", text)

                writable.write(f"### {chapter['title']}\n\n")
                writable.write(text.strip() + "\n\n")
                writable.flush()
                pbar.update(1)

if __name__ == "__main__":
    driver = webdriver.Chrome()
    title, chap_list = request_list(driver)
    request_text(driver, title, chap_list)
