import sys
import os
import re
import time
import json
import argparse

import requests
from markdown_it import MarkdownIt

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
sys.dont_write_bytecode = True
from utils.const import HTML_PREFIX, HTML_SUFFIX, HTML_STYLE

parser = argparse.ArgumentParser()
parser.add_argument("-s", "--src", type=str, default="~/Downloads/src")
parser.add_argument("-d", "--dst", type=str, default="~/Downloads/dst")
parser.add_argument("-r", "--ref", type=str, default="~/Downloads/ref.json")
parser.add_argument("-m", "--raw", action="store_true")

args = parser.parse_args()
args_src = os.path.expanduser(args.src)
args_dst = os.path.expanduser(args.dst)
args_ref = os.path.expanduser(args.ref)
args_raw = args.raw

proper_list = []
if os.path.exists(args_ref):
    with open(args_ref, mode="r", encoding="utf-8") as readable:
        proper_list = json.load(readable)

MODEL_NAME = "sakura:latest"
BASE_URL = "http://127.0.0.1:11434/api/generate"

MAX_RETRY = 5
SEGMENT_UNIT = 128
SEGMENT_SIZE = 512
PREV_CONTEXT_SIZE = 256

ruby_reg = r'<rt>.*?</rt>|</?ruby>|</?rb>'
markdown = MarkdownIt()

def render_inline(text: str):
    text = markdown.render(text).strip()
    if text.startswith("<p>") and text.endswith("</p>"):
        text = text[3:-4]
    return text

def log(msg, level=0):
    print("  " * level + msg)

def pair(writable, zh_text, jp_text, origin):
    if args_raw:
        writable.write(zh_text + "  \n")
        writable.write(origin(jp_text) + "\n\n")

    else:
        writable.write(f"<p>{render_inline(zh_text)}</p>\n")
        writable.write(
            f"<p style=\"opacity: 0.72; font-size: 0.84em; top: -6px; \">\n"
            f"{render_inline(origin(jp_text))}\n"
            f"</p>\n"
        )

def segment_context(prev_lines, max_chars):
    lines = []
    for line in reversed(prev_lines):
        if len("\n".join(lines)) > max_chars:
            break
        lines.insert(0, line)
    return lines

def segment_text(lines, max_len):
    segments = []
    current = []
    length = 0

    for line in lines:
        if length + len(line) > max_len and current:
            segments.append(current)
            current = []
            length = 0
        current.append(line)
        length += len(line)

    if current:
        segments.append(current)
    return segments

def build_prompt(japanese, prev_text):
    gpt_list = []
    for item in proper_list:
        src = item["src"]
        dst = item["dst"]
        info = f" #{item['info']}" if "info" in item else ""
        single = f"{src}->{dst}" + info
        gpt_list.append(single)
    gpt_raw = "\n".join(gpt_list)

    system_prompt = (
        "你是一个轻小说翻译模型，可以流畅通顺地以日本轻小说的风格将日文翻译成简体中文，"
        "并联系上下文正确使用人称代词，不擅自添加原文中没有的代词。"
    )

    if proper_list:
        user_prompt = (
            "根据以下术语表（可以为空）：\n"
            + gpt_raw
            + "\n将下面的日文文本根据对应关系和备注翻译成中文：\n"
            + japanese
        )
    else:
        user_prompt = "将下面的日文文本翻译成中文：\n" + japanese

    prompt = (
        "<|im_start|>system\n" + system_prompt + "<|im_end|>\n"
        + "<|im_start|>user\n" + user_prompt + "<|im_end|>\n"
        + "<|im_start|>assistant\n"
    )

    if prev_text:
        prompt = (
            "<|im_start|>system\n" + system_prompt + "<|im_end|>\n"
            + "<|im_start|>assistant\n" + prev_text + "<|im_end|>\n"
            + "<|im_start|>user\n" + user_prompt + "<|im_end|>\n"
            + "<|im_start|>assistant\n"
        )

    return prompt

def call_sakura(prompt, depth):
    start = time.time()
    try:
        resp = requests.post(
            BASE_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "temperature": 0.2,
                "top_p": 0.9,
                "max_tokens": SEGMENT_SIZE * 2,
                "stream": False,
                "keep_alive": -1
            },
            timeout=30
        )

        resp.raise_for_status()
        data = resp.json()
        text = data["response"].strip()

        duration = time.time() - start
        line_count = len(text.split("\n"))
        log(f"[API] return time={duration:.2f}s lines={line_count}", depth)
        return text, None

    except KeyboardInterrupt:
        exit()

    except Exception as e:
        duration = time.time() - start
        log(f"[API] error time={duration:.2f}s err={repr(e)}", depth)
        return None, e

def load_progress(progress):
    if os.path.exists(progress):
        with open(progress, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data
    return {"line_index": 0, "prev_lines": []}

def save_progress(progress, processed, prev_lines):
    with open(progress, "w", encoding="utf-8") as f:
        json.dump({
            "line_index": processed,
            "prev_lines": segment_context(prev_lines, PREV_CONTEXT_SIZE)
        }, f, ensure_ascii=False, indent=2)

def translate_line(
    seg,
    writable,
    progress,
    processed,
    prev_lines,
    origin,
    depth
):
    results = []
    for jp_text in seg:
        zh_text = ""

        for i in range(MAX_RETRY):
            context = "\n".join(segment_context(
                [*prev_lines, *results],
                PREV_CONTEXT_SIZE
            ))
            messages = build_prompt(jp_text, context)
            zh_text, err = call_sakura(messages, depth)
            if zh_text is not None:
                zh_text = zh_text.replace("<|im_end|>", "").strip()

            if err is None and len(zh_text.split("\n")) == 1 and zh_text != "":
                log(f"[LNE] matched", depth)
                break

            else:
                log((
                    f"[LNE] mismatch with err={repr(err)} "
                    f"(retry {i+1}/{MAX_RETRY})"
                ), depth)

        if zh_text == "":
            log(f"[LNE] fallback to [N/A]", depth)
            zh_text = "[N/A]"
        zh_text = zh_text.split("\n")[0]
        results.append(zh_text)

        pair(writable, zh_text, jp_text, origin)
        writable.flush()

        prev_lines.append(zh_text)
        processed[0] += 1
        save_progress(progress, processed[0], prev_lines)

    return results

def translate_block(
    seg,
    writable,
    progress,
    processed,
    prev_lines,
    origin,
    depth
):
    japanese = "\n".join(seg)
    for i in range(MAX_RETRY):
        try:
            context = "\n".join(segment_context(prev_lines, PREV_CONTEXT_SIZE))
            messages = build_prompt(japanese, context)
            text, _ = call_sakura(messages, depth)
            lines = text.replace("<|im_end|>", "").split("\n")

            if len(lines) == len(seg):
                log(f"[BLK] matched {len(lines)}=={len(seg)}", depth)
                for jp_text, zh_text in zip(seg, lines):
                    pair(writable, zh_text, jp_text, origin)
                    prev_lines.append(zh_text)
                    processed[0] += 1
                    save_progress(progress, processed[0], prev_lines)

                writable.flush()
                return lines

            else:
                log((
                    f"[BLK] mismatch {len(lines)}!={len(seg)} "
                    f"(retry {i+1}/{MAX_RETRY})"
                ), depth)

        except Exception as e:
            log(f"[BLK] exception retry {i+1}/{MAX_RETRY}: {repr(e)}", depth)

    return None

def translate_segment(
    seg,
    writable,
    progress,
    processed,
    prev_lines,
    origin,
    depth=1,
    direction=0
):
    seg_len = len("".join(seg))
    direct_text = " left " if direction == -1 else \
        (" right " if direction == 1 else " ")

    log((
        f"[SEG] try{direct_text}block mode with "
        f"len={seg_len}, lines={len(seg)}"
    ), depth)
    res = translate_block(
        seg,
        writable,
        progress,
        processed,
        prev_lines,
        origin,
        depth
    )

    if res is not None:
        return res

    if seg_len <= SEGMENT_UNIT or len(seg) <= 1:
        log(f"[SEG] fallback to line mode with len={seg_len}", depth)
        return translate_line(
            seg,
            writable,
            progress,
            processed,
            prev_lines,
            origin,
            depth=depth+1
        )

    mid = len(seg) // 2
    log((
        f"[SEG] fallback to split block mode with "
        f"{len(left:=seg[:mid])} + {len(right:=seg[mid:])}"
    ), depth)
    translate_segment(
        left,
        writable,
        progress,
        processed,
        prev_lines,
        origin,
        depth=depth+1,
        direction=-1
    )
    translate_segment(
        right,
        writable,
        progress,
        processed,
        prev_lines,
        origin,
        depth=depth+1,
        direction=1
    )

def translate(lines, origin, writable, progress):
    progress_obj = load_progress(progress)
    line_index = progress_obj.get("line_index", 0)
    prev_lines = progress_obj.get("prev_lines", [])

    pure = lines[line_index:]
    segments = segment_text(pure, SEGMENT_SIZE)
    total = len(segments)
    processed = [line_index]

    for i, seg in enumerate(segments):
        print(f"\n=== SEGMENT {i+1}/{total} ===")
        translate_segment(
            seg,
            writable,
            progress,
            processed,
            prev_lines,
            origin
        )

def main(src, dst, progress, name):
    with open(src, mode="r", encoding="utf-8") as readable:
        raw_text = readable.read().strip()
        raw_list = [
            line.strip()
            for line in raw_text.splitlines()
            if line.strip() != ""
        ]

        pure_list = [
            re.sub(ruby_reg, "", line).strip()
            for line in raw_list
        ]
        origin = lambda line: raw_list[pure_list.index(line)]

    with open(dst, mode="a", encoding="utf-8") as writable:
        if os.path.exists(progress):
            print(f"\n[RESUME] found progress file: {progress}")

        else:
            print(f"\n[START] new translation task: {src}")
            if not args_raw:
                writable.write(HTML_PREFIX.format(
                    STYLE=HTML_STYLE(False),
                    TITLE=name
                ))
            writable.flush()
            save_progress(progress, 0, [])

        translate(pure_list, origin, writable, progress)
        if not args_raw:
            writable.write(HTML_SUFFIX)

if __name__ == "__main__":
    if os.path.isdir(args_src):
        os.makedirs(args_dst, exist_ok=True)
        for filename in os.listdir(args_src):
            pure = os.path.splitext(filename)[0]
            main(
                os.path.join(args_src, filename),
                os.path.join(args_dst, f"{pure}.{'md' if args_raw else 'html'}"),
                os.path.join(args_dst, f"{pure}.json"),
                pure
            )

    elif os.path.isfile(args_src):
        pure = os.path.splitext(os.path.split(args_src)[1])[0]
        main(
            args_src,
            args_dst,
            f"{os.path.splitext(args_dst)[0]}.json",
            pure
        )
