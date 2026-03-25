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
os.makedirs(args_dst, exist_ok=True)

VERT_TOL_RATIO = 0.3
DUP_RATIO = 0.8
SPLIT_FLAG = ("。", "」", "）")

def group_lines(chars, vert_tol):
    lines = []
    chars = sorted(chars, key=lambda c: -c["y1"])

    for c in chars:
        placed = False
        for line in lines:
            if abs(c["y1"] - line["y_mean"]) < vert_tol:
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
            if not chars:
                continue

            sizes = [c["size"] for c in chars]
            median_size = statistics.median(sizes)
            x_values = [c["x0"] for c in chars]
            x_center = (min(x_values) + max(x_values)) / 2

            filtered_chars = [
                c for c in chars
                if c["size"] >= 0.7 * median_size
            ]

            lines = []
            vert_tol = median_size * VERT_TOL_RATIO
            grouped_lines = group_lines(filtered_chars, vert_tol)
            for line_chars in grouped_lines:
                line_chars.sort(key=lambda c: c["x0"])
                first_x = line_chars[0]["x0"]
                if abs(first_x - x_center) < 20 and len(line_chars) <= 3:
                    continue

                text = "".join(c["text"] for c in line_chars)
                text = text.replace("゛", "゙").replace("゜", "゚")
                text = unicodedata.normalize("NFC", text)
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
    for name in tqdm(
        f for f in os.listdir(args_src)
        if f.lower().endswith(".pdf")
    ):
        lines = extract_text(os.path.join(args_src, name))
        new_path = os.path.join(args_dst, f"{os.path.splitext(name)[0]}.txt")

        with open(new_path, mode="w", encoding="utf-8") as writable:
            for line in lines:
                writable.write(line + "\n")
