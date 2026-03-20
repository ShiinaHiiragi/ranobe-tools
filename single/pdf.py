import os
import argparse
import statistics
import pdfplumber
import unicodedata

from tqdm import tqdm
from collections import Counter

parser = argparse.ArgumentParser()
parser.add_argument("-s", "--src", type=str, default="~/Downloads/src")
parser.add_argument("-d", "--dst", type=str, default="~/Downloads/dst")

args = parser.parse_args()
args_src = os.path.expanduser(args.src)
args_dst = os.path.expanduser(args.dst)

VERT_TOL =  0.25
DUP_RATIO = 0.8
SPLIT_FLAG = ("。", "」", "）")

def group_lines(chars):
    lines = []
    chars = sorted(chars, key=lambda c: -c["y1"])

    for c in chars:
        placed = False
        for line in lines:
            if abs(c["y1"] - line["y_mean"]) < VERT_TOL:
                line["chars"].append(c)
                line["y_mean"] = (
                    line["y_mean"] * (len(line["chars"]) - 1) + c["y1"]
                ) / len(line["chars"])
                placed = True
                break

        if not placed:
            lines.append({
                "y_mean": c["y1"],
                "chars": [c]
            })

    return [line["chars"] for line in lines]

def detect_headers(all_pages_lines):
    counter = Counter()
    total_pages = len(all_pages_lines)

    for lines in all_pages_lines:
        unique_lines = set(l.strip() for l in lines if l.strip())
        counter.update(unique_lines)

    headers = set()
    for line, count in counter.items():
        if count / total_pages >= DUP_RATIO:
            headers.add(line)
    return headers

def extract_text(pdf_path):
    all_pages_lines = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            chars = page.chars
            sizes = [c["size"] for c in chars]
            median_size = statistics.median(sizes)
            x_values = [c["x1"] for c in chars]
            x_center = (min(x_values) + max(x_values)) / 2

            filtered_chars = [
                c for c in chars
                if c["size"] >= 0.7 * median_size
            ]

            lines = []
            grouped_lines = group_lines(filtered_chars)
            for line_chars in grouped_lines:
                line_chars.sort(key=lambda c: c["x1"])
                first_x = line_chars[0]["x1"]
                if abs(first_x - x_center) < 20 and len(line_chars) <= 3:
                    continue

                text = "".join(c["text"] for c in line_chars)
                text = unicodedata.normalize("NFC", text)
                text = text.replace("゛", " ゙").replace("゜", " ゚")
                lines.append(text)

            all_pages_lines.append(lines)

    headers = detect_headers(all_pages_lines)
    paras = []
    para = ""

    for page_idx, lines in enumerate(all_pages_lines):
        lines = [l for l in lines if l.strip() not in headers]

        for line in lines:
            stripped = line.strip()
            if stripped == "":
                if para:
                    paras.append(para.rstrip())
                    para = ""
                paras.append("")
                continue

            if line.endswith(" "):
                para += line.rstrip()
                paras.append(para)
                para = ""
            else:
                para += line

        if page_idx < len(all_pages_lines) - 1:
            if para:
                if not para.endswith(SPLIT_FLAG):
                    continue
                else:
                    paras.append(para.rstrip())
                    para = ""

    if para:
        paras.append(para.rstrip())
    return paras

if __name__ == "__main__":
    for name in tqdm(os.listdir(args_src)):
        lines = extract_text(os.path.join(args_src, name))
        new_path = os.path.join(args_dst, f"{os.path.splitext(name)[0]}.txt")

        with open(new_path, mode="w", encoding="utf-8") as writable:
            for line in lines:
                writable.write(line + "\n")
