import os
import time
import argparse

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By

parser = argparse.ArgumentParser()
parser.add_argument("-u", "--uid", type=str, default="2948941")
parser.add_argument("-d", "--dst", type=str, default="~/Downloads/dst")
parser.add_argument("-l", "--login", action="store_true")

args = parser.parse_args()
page_url = lambda uid, page: f"https://www.pixiv.net/users/{uid}/novels?p={page}"
text_url = lambda pid: f"https://www.pixiv.net/novel/show.php?id={pid}"

dst_dir = os.path.expanduser(args.dst)
os.makedirs(dst_dir, exist_ok=True)

INTRO_SELECTOR = 'p[id^="expandable-paragraph"]'
PARAS_SELECTOR = 'p, h1, h2, h3, h4, h5, h6'
NEXT_SELECTOR = 'button[class$="footer-pager-next"]'

def cruise_text(driver):
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    paras = soup.select_one('main main').select(PARAS_SELECTOR)
    texts = "\n\n".join([(
        para.get_text("\n").strip()
        if para.name == "p"
        else ("#" * int(para.name[1] + 2) + " "+ para.get_text("\n").strip())
    ) for para in paras])

    return soup, texts

def cruise_page(driver, index):
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
        driver.get(text_url(pid))
        time.sleep(2)
        sub_soup, text = cruise_text(driver)

        texts = []
        title = sub_soup.select_one('h1').text
        intro = sub_soup.select_one(INTRO_SELECTOR).get_text("\n")
        texts.append(text)

        while len(sub_soup.select(NEXT_SELECTOR)) > 0:
            driver.find_element(By.CSS_SELECTOR, NEXT_SELECTOR).click()
            time.sleep(2)

            sub_soup, text = cruise_text(driver)
            texts.append(text)

        print(f"{pid}: {title}")
        with open(
            os.path.join(dst_dir, f"{pid}.md"),
            mode="w",
            encoding="utf-8"
        ) as writable:
            writable.write(f"### {title}\n\n")
            writable.write(f"{intro}\n\n")
            writable.write(f"---\n\n")
            writable.write("\n\n\n\n　◇\n\n\n\n".join(texts) + "\n")

    return len(soup.select(f'a[href$="p={index+1}"]')) > 0

if __name__ == "__main__":
    index = 1
    driver = webdriver.Chrome()

    while True:
        driver.get(page_url(args.uid, index))
        if index == 1 and args.login:
            print("Login manually to access hidden post")
            breakpoint()

        time.sleep(4)
        if cruise_page(driver, index):
            index += 1
        else:
            exit(0)
