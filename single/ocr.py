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

parser = argparse.ArgumentParser()
parser.add_argument("--min", type=int, default=0)
parser.add_argument("--max", type=int, default=0)
arg = parser.parse_args()

BASE_PATH = ""
if sys.platform == "win32":
    BASE_PATH = "C:/Users/Ichinoe/Downloads"
elif sys.platform == "linux":
    BASE_PATH = "/media/ichinoe/Download/raw-00"

MIN_INDEX = arg.min                       # 第一张图的序号，基本不用变
MAX_INDEX = arg.max                       # 最后一张图的序号加一，除了拍摄时都不能为零
MIN_VOLUME = 0                            # 首卷序号，部分书籍首卷是番外

APP_POINT = (110, 1400)                   # BlueStack 在一号位的坐标
NEXT_POINT = (180, 1280)                  # 用于点击下一页的坐标

CHAT_POINT = (180, 1400)                  # QQ/TIM 在二号位的坐标
TAG_POINT = (300, 150)                    # 需要发送消息的对象在消息列表的坐标
INBOX_POINT = (800, 1200)                 # 输入框的坐标
SEND_POINT = (2440, 1320)                 # 发送按钮的坐标

CHECK_POINT = (2350, 1200)                # 检查这个位置的像素，以决定是否停止拍摄
HALT_COLOR = (255, 99, 72)                # 被检查像素的目标颜色 RGB
LINE_COLOR = (122, 122, 122)              # 新章节线的颜色

CHAPTER_LINE = 76                         # 新章节线在处理后图片所在的行数
LINE_LENGTH = 1235                        # 新章节线颜色的像素个数
ROTATE_ANGLE = 90                         # 横屏拍摄后如何旋转到正确位置
LEFT_THRESHOLD = 40                       # 判定为新一段的缩进临界值

SHOT_REGION = (85, 50, 2340, 1315)        # 拍摄的范围，前两个是坐标，后两个是长和宽
CROP_REGION = (50, 30, 2240, 1276)        # 裁剪的范围，前后两个似乎都是坐标

NUM = "[0123456789]"                      # 阿拉伯数字和中文数字
CN_NUM = "[〇零一两二三四五六七八九十百千万]"
CHAPTERS = [                              # 章节序号标注方式
    f"第{NUM}+话",
    f"第{CN_NUM}+章",
    f"(番外|特典){CN_NUM}*",
    "序章|序幕|引子",
    "间章|间幕",
    "终章|终幕|后话",
    "后记|完结感言"
]

CHAPTER_REG = f"^({'|'.join(CHAPTERS)})"  # 未被捕获的都是非章节（通知或请假条等）
REPLACE_REG = "### \\1　"
VOLUME_REG = (                            # 可作为卷首章节的标号，若分不开可临时添加
    "^(第0话)"
    "|^(第一章)"
    "|^(序章)"
    "|^(序幕)"
    "|^(引子)"
)

INTERVAL = 0.4
SHORT_INTERVAL = INTERVAL / 2
LONG_INTERVAL = INTERVAL * 2
pyautogui.FAILSAFE = True                 # 开启后，快速将光标移动到屏幕四角可停止进程

def sub(name):
    result = os.path.join(BASE_PATH, name)
    if not os.path.exists(result):
        os.mkdir(result)
    return result

def convert_pdf(input_file_path):
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
        pyautogui.moveTo(*NEXT_POINT)
        pyautogui.screenshot(os.path.join(output_dir_path, f"{index:04d}.png"), region=SHOT_REGION)
        sleep(SHORT_INTERVAL)
        pyautogui.click()
        sleep(INTERVAL)

    sleep(LONG_INTERVAL)
    pyautogui.hotkey("win", "d")
    sleep(INTERVAL)
    pyautogui.moveTo(*APP_POINT)
    sleep(INTERVAL)
    pyautogui.click()
    sleep(INTERVAL)

    global MAX_INDEX
    if MAX_INDEX > 0:
        for index in (pbar := tqdm(range(MIN_INDEX, MAX_INDEX))):
            pbar.set_description("Screenshot")
            __screenshot(index)
    else:
        index = MIN_INDEX
        while True:
            __screenshot(index)
            index += 1
            (red, green, blue) = pyautogui.pixel(*CHECK_POINT)
            if (red, green, blue) == HALT_COLOR:
                MAX_INDEX = index
                print(f"\033[1;31mMAX_INDEX is changed to {index}. \033[0m")
                break

    sleep(INTERVAL)
    if sys.platform == "win32":
        if chat:
            notify()
        ctypes.windll.user32.LockWorkStation()
    elif sys.platform == "linux":
        pyautogui.hotkey("win", "l")

def notify():
    pyautogui.moveTo(*CHAT_POINT, duration=LONG_INTERVAL)
    pyautogui.click()
    pyautogui.moveTo(*TAG_POINT, duration=LONG_INTERVAL)
    pyautogui.click()
    pyautogui.moveTo(*INBOX_POINT, duration=LONG_INTERVAL)
    pyautogui.click()
    pyautogui.typewrite(str(MAX_INDEX), SHORT_INTERVAL)
    pyautogui.moveTo(*SEND_POINT, duration=LONG_INTERVAL)
    pyautogui.click()
    sleep(LONG_INTERVAL)

def preprocess(input_dir_path, output_dir_path):
    assert MAX_INDEX > 0
    for index in (pbar := tqdm(range(MIN_INDEX, MAX_INDEX))):
        pbar.set_description("Preprocess")
        image = Image.open(os.path.join(input_dir_path, f"{index:04d}.png"))
        if CROP_REGION:
            image = image.crop(CROP_REGION)
        image = image.rotate(ROTATE_ANGLE, expand=True)
        image.save(os.path.join(output_dir_path, f"{index:04d}.png"))

def renormalize(dir_path):
    global MAX_INDEX
    assert MAX_INDEX > 0
    real_index = MIN_INDEX

    for index in (pbar := tqdm(range(MIN_INDEX, MAX_INDEX))):
        pbar.set_description("Renormalization")
        if os.path.exists(os.path.join(dir_path, f"{index:04d}.png")):
            if real_index < index:
                os.rename(
                    os.path.join(dir_path, f"{index:04d}.png"),
                    os.path.join(dir_path, f"{real_index:04d}.png")
                )
            real_index += 1
    if real_index < MAX_INDEX:
        MAX_INDEX = real_index
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

    assert MAX_INDEX > 0
    for index in (pbar := tqdm(range(MIN_INDEX, MAX_INDEX))):
        pbar.set_description("Request")
        result = __post_baidu(os.path.join(input_dir_path, f"{index:04d}.png"))
        writable = open(os.path.join(output_dir_path, f"{index:04d}.json"), "w", encoding="utf-8")
        json.dump(result, writable, ensure_ascii=False, indent=2)
        sleep(SHORT_INTERVAL)

def postprocess(input_dir_path, output_dir_path):
    assert MAX_INDEX > 0
    error_list = list()

    for index in (pbar := tqdm(range(MIN_INDEX, MAX_INDEX))):
        pbar.set_description("Postprocess")
        input_file_path = os.path.join(input_dir_path, f"{index:04d}.png")
        output_file_path = os.path.join(output_dir_path, f"{index:04d}.json")
        image = Image.open(input_file_path)
        pixels = image.load()

        line_count = 0
        for j in range(image.size[0]):
            if pixels[j, CHAPTER_LINE] == LINE_COLOR:
                line_count += 1

        response = json.load(open(output_file_path, "r", encoding="utf-8"))
        if "error_code" in response:
            error_list.append(f"{index:04d}.json")
        response["new"] = True if line_count == LINE_LENGTH else False
        json.dump(response, open(output_file_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    if len(error_list) > 0:
        print(f"\033[1;31mThe following response are failed: \033[0m")
        for file_name in error_list:
            print(f"\033[1;31m  {file_name}\033[0m")

def merge(input_dir_path, output_dir_path):
    assert MAX_INDEX > 0
    volume = MIN_VOLUME
    writable = None
    first_line_flag = True
    skip_flag = False
    skip_list = list()

    for index in (pbar := tqdm(range(MIN_INDEX, MAX_INDEX))):
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
            elif line["location"]["left"] > LEFT_THRESHOLD:
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
    convert_pdf(sub("ocr-raw.pdf"))
    stack(sub("ocr-raw"))
    renormalize(sub("ocr-raw"))
    preprocess(sub("ocr-raw"), sub("ocr-input"))
    post(sub("ocr-input"), sub("ocr-output"))
    postprocess(sub("ocr-input"), sub("ocr-output"))
    merge(sub("ocr-output"), sub("ocr-result"))
