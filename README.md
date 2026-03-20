# Toolkit for Light Novel

## EPUB Converter

```shell
pip install tqdm beautifulsoup4 markdown-it-py
python single/epub.py
```

## NCode Crawler

```shell
pip install tqdm selenium
python single/ncode.py -n n0770fw
```

## PDF Extractor

```shell
pip install tqdm pdfplumber
python single/pdf.py
```

## OCR Analyzer

```shell
pip install requests pyautogui tqdm pillow pycnnum
pip install pymupdf tencentcloud-sdk-python
python single/ocr.py
```

## Sakura Translator

```shell
pip install requests markdown-it-py
python single/sakura.py
```

## Bangumi Publisher

```shell
pip install requests python-dotenv beautifulsoup4 rapidfuzz
python journal/init.py
python journal/post.py
python journal/meta.py
```
