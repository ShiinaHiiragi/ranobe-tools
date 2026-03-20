import sys
import os
import re
import json
import base64
import ctypes
import argparse

import fitz
import dotenv
import requests
import pyautogui

from time import sleep
from tqdm import tqdm
from PIL import Image
from pycnnum import num2cn

dotenv.load_dotenv(os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    ".env"
))

access_token = os.environ.get("ACCESS_TOKEN", "")
secret_id = os.environ.get("SECRET_ID", "")
secret_key = os.environ.get("SECRET_KEY", "")

pyautogui.FAILSAFE = True
parser = argparse.ArgumentParser()

parser.add_argument("-b", "--base", type=str, default="~/Downloads")
parser.add_argument("-v", "--vol", type=int)
parser.add_argument("-s", "--min", type=int)
parser.add_argument("-d", "--max", type=int)

parser.add_argument("-p", "--pdf", action="store_true")
parser.add_argument("-o", "--ocr", choices=["baidu", "tencent"], default="baidu")

parser.add_argument("--app-point", nargs="+", type=int)
parser.add_argument("--nxt-point", nargs="+", type=int)

parser.add_argument("--cht-point", nargs="+", type=int)
parser.add_argument("--tag-point", nargs="+", type=int)
parser.add_argument("--box-point", nargs="+", type=int)
parser.add_argument("--hnt-point", nargs="+", type=int)

parser.add_argument("--chck-point", nargs="+", type=int)
parser.add_argument("--halt-color", nargs="+", type=int)
parser.add_argument("--send-color", nargs="+", type=int)

parser.add_argument("--line-length", type=int)
parser.add_argument("--chapter-lne", type=int)
parser.add_argument("--rotat-angle", type=int)
parser.add_argument("--l-threshold", type=int)

parser.add_argument("--shot-region", nargs="+", type=int)
parser.add_argument("--crop-region", nargs="+", type=int)

args = parser.parse_args()
base_path = os.path.expanduser(args.base)

min_index = args.min
max_index = args.max
min_volume = args.vol

args_pdf = args.pdf
args_ocr = args.ocr

app_point = tuple(args.app_point)[:2]
nxt_point = tuple(args.nxt_point)[:2]

cht_point = tuple(args.cht_point)[:2]
tag_point = tuple(args.tag_point)[:2]
box_point = tuple(args.box_point)[:2]
send_point = tuple(args.hnt_point)[:2]

chck_point = tuple(args.chck_point)[:2]
halt_color = tuple(args.halt_color)[:3]
line_color = tuple(args.send_color)[:3]

line_length = args.line_length
chapter_lne = args.chapter_lne
rotat_angle = args.rotat_angle
l_threshold = args.l_threshold

shot_region = tuple(args.shot_region)[:4]
crop_region = tuple(args.crop_region)[:4]

AR_NUM = "[0123456789]"
CN_NUM = "[〇零一两二三四五六七八九十百千万]"
CHAPTERS = [
    f"第{AR_NUM}+话",
    f"第{CN_NUM}+章",
    f"(番外|特典){CN_NUM}*",
    "序章|序幕|引子",
    "间章|间幕",
    "终章|终幕|后话",
    "后记|完结感言"
]

CHAPTER_REG = f"^({'|'.join(CHAPTERS)})"
REPLACE_REG = "### \\1　"
VOLUME_REG = (
    "^(第0话)"
    "|^(第一章)"
    "|^(序章)"
    "|^(序幕)"
    "|^(引子)"
)

NORM_INTERVAL = 0.4
SHRT_INTERVAL = NORM_INTERVAL / 2
LONG_INTERVAL = NORM_INTERVAL * 2

def sub(name):
    result = os.path.join(base_path, name)
    os.makedirs(result, exist_ok=True)
    return result

def convert(input_file_path):
    input_file_path = sub(input_file_path)

    page_num = 1
    dir_path = sub(input_file_path.split('.')[-2])
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    pdf = fitz.open(input_file_path)
    for page in tqdm(pdf):
        zoom_x = 1
        zoom_y = 1
        mat = fitz.Matrix(zoom_x, zoom_y)
        pixmap = page.get_pixmap(matrix=mat, alpha=False)
        pixmap.pil_save(os.path.join(dir_path, f"{page_num:04d}.png"))
        page_num += 1

def reader(output_dir_path, chat=False):
    output_dir_path = sub(output_dir_path)

    def __screenshot(index):
        pyautogui.moveTo(*nxt_point)
        pyautogui.screenshot(
            os.path.join(output_dir_path, f"{index:04d}.png"),
            region=shot_region
        )
        sleep(SHRT_INTERVAL)
        pyautogui.click()
        sleep(NORM_INTERVAL)

    sleep(LONG_INTERVAL)
    pyautogui.hotkey("win", "d")
    sleep(NORM_INTERVAL)
    pyautogui.moveTo(*app_point)
    sleep(NORM_INTERVAL)
    pyautogui.click()
    sleep(NORM_INTERVAL)

    global max_index
    if max_index > 0:
        for index in (pbar := tqdm(range(min_index, max_index))):
            pbar.set_description("Screenshot")
            __screenshot(index)
    else:
        index = min_index
        while True:
            __screenshot(index)
            index += 1
            (red, green, blue) = pyautogui.pixel(*chck_point)
            if (red, green, blue) == halt_color:
                max_index = index
                print(f"\033[1;31mMAX_INDEX is changed to {index}. \033[0m")
                break

    sleep(NORM_INTERVAL)
    if sys.platform == "win32":
        if chat:
            notify()
        ctypes.windll.user32.LockWorkStation()
    elif sys.platform == "linux":
        pyautogui.hotkey("win", "l")

def notify():
    pyautogui.moveTo(*cht_point, duration=LONG_INTERVAL)
    pyautogui.click()
    pyautogui.moveTo(*tag_point, duration=LONG_INTERVAL)
    pyautogui.click()
    pyautogui.moveTo(*box_point, duration=LONG_INTERVAL)
    pyautogui.click()
    pyautogui.typewrite(str(max_index), SHRT_INTERVAL)
    pyautogui.moveTo(*send_point, duration=LONG_INTERVAL)
    pyautogui.click()
    sleep(LONG_INTERVAL)

def preprocess(input_dir_path, output_dir_path):
    input_dir_path = sub(input_dir_path)
    output_dir_path = sub(output_dir_path)

    assert max_index > 0
    for index in (pbar := tqdm(range(min_index, max_index))):
        pbar.set_description("Preprocess")
        image = Image.open(os.path.join(input_dir_path, f"{index:04d}.png"))
        if crop_region:
            image = image.crop(crop_region)
        image = image.rotate(rotat_angle, expand=True)
        image.save(os.path.join(output_dir_path, f"{index:04d}.png"))

def renormalize(dir_path):
    dir_path = sub(dir_path)

    global max_index
    assert max_index > 0
    real_index = min_index

    for index in (pbar := tqdm(range(min_index, max_index))):
        pbar.set_description("Renormalization")
        if os.path.exists(os.path.join(dir_path, f"{index:04d}.png")):
            if real_index < index:
                os.rename(
                    os.path.join(dir_path, f"{index:04d}.png"),
                    os.path.join(dir_path, f"{real_index:04d}.png")
                )
            real_index += 1
    if real_index < max_index:
        max_index = real_index
        print(f"\033[1;31mMAX_INDEX is changed to {real_index}. \033[0m")

def recognize(input_dir_path, output_dir_path):
    input_dir_path = sub(input_dir_path)
    output_dir_path = sub(output_dir_path)

    def __post_baidu(file_path):
        # ref: https://ai.baidu.com/ai-doc/REFERENCE/Ck3dwjhhu
        request_url_base = "https://aip.baidubce.com/rest/2.0/ocr/v1/general"
        image = base64.b64encode(open(file_path, "rb").read())

        request_url = f"{request_url_base}?access_token={access_token}"
        params = { "image": image }
        headers = { "content-type": "application/x-www-form-urlencoded" }
        try:
            response = requests.post(request_url, data=params, headers=headers)
            if response:
                return response.json()
            else:
                raise RuntimeError("\033[1;31mResponse failed.\033[0m")
        except requests.exceptions.RequestException:
            return __post_baidu(file_path)

    def __post_tencent(file_path):
        from tencentcloud.common import credential
        from tencentcloud.common.profile.client_profile import ClientProfile
        from tencentcloud.common.profile.http_profile import HttpProfile
        from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
        from tencentcloud.ocr.v20181119 import ocr_client, models
        try:
            cred = credential.Credential(secret_id, secret_key)
            httpProfile = HttpProfile()
            httpProfile.endpoint = "ocr.tencentcloudapi.com"
            clientProfile = ClientProfile()
            clientProfile.httpProfile = httpProfile
            client = ocr_client.OcrClient(cred, "ap-shanghai", clientProfile)

            req = models.GeneralAccurateOCRRequest()
            image = base64.b64encode(open(file_path, "rb").read()).decode()
            params = {
                "Action": "GeneralAccurateOCR",
                "Version": "2018-11-19",
                "ImageBase64": image
            }
            req.from_json_string(json.dumps(params))
            resp = client.GeneralAccurateOCR(req)
            return json.loads(resp.to_json_string())

        except TencentCloudSDKException:
            return __post_tencent(file_path)

    assert max_index > 0
    for index in (pbar := tqdm(range(min_index, max_index))):
        pbar.set_description("Request")
        result = {
            "baidu": __post_baidu,
            "tencent": __post_tencent
        }[args_ocr](os.path.join(input_dir_path, f"{index:04d}.png"))
        writable = open(os.path.join(
            output_dir_path,
            f"{index:04d}.json"
        ), "w", encoding="utf-8")
        json.dump(result, writable, ensure_ascii=False, indent=2)
        sleep(SHRT_INTERVAL)

def postprocess(input_dir_path, output_dir_path):
    input_dir_path = sub(input_dir_path)
    output_dir_path = sub(output_dir_path)

    assert max_index > 0
    error_list = list()

    for index in (pbar := tqdm(range(min_index, max_index))):
        pbar.set_description("Postprocess")
        input_file_path = os.path.join(input_dir_path, f"{index:04d}.png")
        output_file_path = os.path.join(output_dir_path, f"{index:04d}.json")
        image = Image.open(input_file_path)
        pixels = image.load()

        line_count = 0
        for j in range(image.size[0]):
            if pixels[j, chapter_lne] == line_color:
                line_count += 1

        response = json.load(open(output_file_path, "r", encoding="utf-8"))
        if "error_code" in response:
            error_list.append(f"{index:04d}.json")
        response["new"] = True if line_count == line_length else False
        json.dump(
            response,
            open(output_file_path, "w", encoding="utf-8"),
            ensure_ascii=False,
            indent=2
        )

    if len(error_list) > 0:
        print(f"\033[1;31mThe following response are failed: \033[0m")
        for file_name in error_list:
            print(f"\033[1;31m  {file_name}\033[0m")

def merge(input_dir_path, output_dir_path):
    input_dir_path = sub(input_dir_path)
    output_dir_path = sub(output_dir_path)

    assert max_index > 0
    volume = min_volume
    writable = None
    first_line_flag = True
    skip_flag = False
    skip_list = list()

    for index in (pbar := tqdm(range(min_index, max_index))):
        pbar.set_description("Merge")
        readable = open(
            os.path.join(input_dir_path, f"{index:04d}.json"),
            mode="r",
            encoding="utf-8"
        )
        response = json.load(readable)

        for line_index, line in enumerate(response["words_result"]):
            text = re.sub("”", "」", re.sub("“", "「", line["words"]))
            if line_index == 0 and response["new"]:
                if re.search(VOLUME_REG, text) or index == 0:
                    writable = open(
                        os.path.join(output_dir_path, f"{volume:02d}.md"),
                        mode="w",
                        encoding="utf-8"
                    )
                    writable.write(f"## 第{num2cn(volume) if volume != 1 else '一'}卷\n\n")
                    volume += 1
                    first_line_flag = True

                if re.search(CHAPTER_REG, text):
                    skip_flag = False
                    if not first_line_flag:
                        writable.write("\n\n\n\n")
                    text = re.sub(CHAPTER_REG, REPLACE_REG, text)
                else:
                    skip_list.append(text)
                    skip_flag = True
                    break
            elif skip_flag:
                break
            elif line["location"]["left"] > l_threshold:
                writable.write("\n\n")
            writable.write(text)
            first_line_flag = False

    writable.write("\n")
    if len(skip_list) > 0:
        print(f"\033[1;31mThe following chapters are skipped: \033[0m")
        for chapter_name in skip_list:
            print(f"\033[1;31m  {chapter_name}\033[0m")

if __name__ == "__main__":
    convert("raw.pdf") if args_pdf else reader("raw")
    renormalize("raw")
    preprocess("raw", "src")
    recognize("src", "dst")
    postprocess("src", "dst")
    merge("dst", "res")
