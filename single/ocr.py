import sys
import os
import re
import json
import base64
import ctypes
import argparse

import fitz
import requests
import pyautogui

from time import sleep
from tqdm import tqdm
from PIL import Image
from pycnnum import num2cn

pyautogui.FAILSAFE = True
parser = argparse.ArgumentParser()

parser.add_argument("-b", "--base", type=str, default="~/Downloads")
parser.add_argument("-v", "--vol", type=int)
parser.add_argument("-s", "--min", type=int)
parser.add_argument("-d", "--max", type=int)

parser.add_argument("--app-point", nargs="+", type=int)
parser.add_argument("--nxt-point", nargs="+", type=int)

parser.add_argument("--cht-point", nargs="+", type=int)
parser.add_argument("--tag-point", nargs="+", type=int)
parser.add_argument("--box-point", nargs="+", type=int)
parser.add_argument("--hnt-point", nargs="+", type=int)

parser.add_argument("--chck-point", nargs="+", type=int)
parser.add_argument("--halt-color", nargs="+", type=int)
parser.add_argument("--send-color", nargs="+", type=int)

parser.add_argument("--chapter-lne", type=int)
parser.add_argument("--line-length", type=int)
parser.add_argument("--rotat-angle", type=int)
parser.add_argument("--l-threshold", type=int)

parser.add_argument("--shot-region", nargs="+", type=int)
parser.add_argument("--crop-region", nargs="+", type=int)

args = parser.parse_args()
base_path = os.path.expanduser(args.base)

min_index = args.min
max_index = args.max
min_volume = args.vol

app_point = tuple(args.app_point)[:2]
nxt_point = tuple(args.nxt_point)[:2]

cht_point = tuple(args.cht_point)[:2]
tag_point = tuple(args.tag_point)[:2]
box_point = tuple(args.box_point)[:2]
send_point = tuple(args.hnt_point)[:2]

chck_point = tuple(args.chck_point)[:2]
halt_color = tuple(args.halt_color)[:3]
line_color = tuple(args.send_color)[:3]

chapter_lne = args.chapter_lne
line_length = args.line_length
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

def stack(output_dir_path, chat=False):
    def __screenshot(index):
        pyautogui.moveTo(*nxt_point)
        pyautogui.screenshot(os.path.join(output_dir_path, f"{index:04d}.png"), region=shot_region)
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
    assert max_index > 0
    for index in (pbar := tqdm(range(min_index, max_index))):
        pbar.set_description("Preprocess")
        image = Image.open(os.path.join(input_dir_path, f"{index:04d}.png"))
        if crop_region:
            image = image.crop(crop_region)
        image = image.rotate(rotat_angle, expand=True)
        image.save(os.path.join(output_dir_path, f"{index:04d}.png"))

def renormalize(dir_path):
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

def post(input_dir_path, output_dir_path):
    def __post_baidu(file_path):
        # https://ai.baidu.com/ai-doc/REFERENCE/Ck3dwjhhu
        request_url_base = "https://aip.baidubce.com/rest/2.0/ocr/v1/general"
        access_token = "TOKEN"
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
            cred = credential.Credential("TOKEN", "TOKEN")
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
        result = __post_baidu(os.path.join(input_dir_path, f"{index:04d}.png"))
        writable = open(os.path.join(output_dir_path, f"{index:04d}.json"), "w", encoding="utf-8")
        json.dump(result, writable, ensure_ascii=False, indent=2)
        sleep(SHRT_INTERVAL)

def postprocess(input_dir_path, output_dir_path):
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
        json.dump(response, open(output_file_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    if len(error_list) > 0:
        print(f"\033[1;31mThe following response are failed: \033[0m")
        for file_name in error_list:
            print(f"\033[1;31m  {file_name}\033[0m")

def merge(input_dir_path, output_dir_path):
    assert max_index > 0
    volume = min_volume
    writable = None
    first_line_flag = True
    skip_flag = False
    skip_list = list()

    for index in (pbar := tqdm(range(min_index, max_index))):
        pbar.set_description("Merge")
        readable = open(os.path.join(input_dir_path, f"{index:04d}.json"), "r", encoding="utf-8")
        response = json.load(readable)

        for line_index, line in enumerate(response["words_result"]):
            text = re.sub("”", "」", re.sub("“", "「", line["words"]))
            if line_index == 0 and response["new"]:
                if re.search(VOLUME_REG, text) or index == 0:
                    writable = open(os.path.join(output_dir_path, f"{volume:02d}.md"), "w", encoding="utf-8")
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

"""
使用方法：该脚本自动拍摄照片，裁减并交给百度 OCR 识别合并
- pip 安装包
    - 基础：pip install requests pyautogui tqdm pillow pycnnum
    - 特殊：pip install tencentcloud fitz（需要 Visual C++ 14.0 及以上版本）
- stack 用于拍摄，适用于 Windows
    - 保证 BlueStack 在下方任务栏一号位
    - 保证 TIM 在下方任务栏二号位，自己在好友列表最上方时，可调用 stack(sub("ocr-raw"), True)
    - 提前下载好所有章节，防止刷不出下一章
    - 拔下鼠标连线
    - 通知与动作 -> 关闭通知
    - 附加电源设置 -> 当关闭盖子时 -> 什么都不做
    - 当手机收到 MAX_INDEX（或风扇声减小）时，打开盖子
- 其余步骤适用于 Ubuntu：将 ocr-raw 转移到其他设备
    - 填写 BASE_PATH、MIN_INDEX、MAX_INDEX
    - 取消需要执行部分的注释
- 可能遇到的问题
    - 若收到 MAX_INDEX is changed to xxxx：请及时修改 MAX_INDEX
    - 若删除了部分 ocr-raw 中的图片：用 renormalize 重新整理图片顺序
    - 若需要 post 网址（而非发送文件 base64）
        - 将 sub("ocr-input") 修改为基础网址
        - 注释 image = base64.b64encode(open(file_path, "rb").read())
        - params = { "image": image } 改为 params = { "url": file_path }
    - 若 post 出现任何连接错误
        - 修改 MIN_INDEX 为最后一个有效 response + 1
        - 注释后续 postprocess、merge 后重新执行
    - 若 postprocess 提示 The following response are failed
        - 将 post 的 range(MIN_INDEX, MAX_INDEX) 改为对应 index 的 list
        - 重新执行 postprocess，保证不再出现相同错误
    - 若 merge 提示 The following chapters are skipped
        - 确保里面没有有效章节被白名单滤出
        - 若有，且被误判是因为章节名错误（例如「第三张」）：直接修改 json 文件
        - 若有，且被误判是因为章节名未登记：在 CHAPTERS 变量中登记新类别章节名
    - 若 merge 出现如下所述的任意分卷问题
        - 如果第一卷只是序幕：将 MIN_VOLUME 修改为 0（甚至负数）
        - 如果报错 'NoneType' object has no attribute 'write'：在 VOLUME_REG 增加首篇章节名
        - 如果新卷不从「第一章」标记：在 VOLUME_REG 标记出所有新卷首篇章节名
    - 若找不到章节线的位置，使用以下代码，找平均灰度最大的行序号：
        ```py
        image = Image.open("0000.png")
        pixels = image.load()
        result = []
        for i in range(image.size[1]):
            color = []
            for j in range(image.size[0]):
                red, green, blue = pixels[j, i]
                color.append(red)
                color.append(green)
                color.append(blue)
            result.append(sum(color) / (image.size[0] * 3))
        print(result.index(min(result)))
        ```
- merge 后文件的进一步精校
    - 填写书名和每一卷的具体名称
    - 修改错误的标点符号，复现被屏蔽词
    - 最高规格：通读全文并修正
"""

if __name__ == "__main__":
    convert(sub("ocr-raw.pdf"))
    stack(sub("ocr-raw"))
    renormalize(sub("ocr-raw"))
    preprocess(sub("ocr-raw"), sub("ocr-input"))
    post(sub("ocr-input"), sub("ocr-output"))
    postprocess(sub("ocr-input"), sub("ocr-output"))
    merge(sub("ocr-output"), sub("ocr-result"))
