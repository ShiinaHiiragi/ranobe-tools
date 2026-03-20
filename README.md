# 轻小说工具箱

## EPUB 转换

`single/epub.py` 用于将 EPUB 格式轻小说解析为 Markdown 或 HTML。相比直接使用 Pandoc，该脚本针对日文或中日对照文本做了专门优化：

1. 自动识别目录并拆分章节，同时支持手动配置分页规则
2. 适配大多数规范 EPUB，轻量提取正文并整理段落结构
3. 支持图片处理、纵排等进阶排版需求
4. 支持 ruby 处理、假名识别，优化双语阅读体验

### 配置

1. 安装所需包

    ```shell
    pip install tqdm beautifulsoup4 markdown-it-py
    ```

2. 由于配置较为复杂，推荐直接修改 `CONFIG` 变量（配置说明详见注释），或者在全局配置中通过 `path.src` 或 `local.path` 条目创建本地配置文件

### 用法

```shell
python single/epub.py
```

## NCode 下载

从[小説家になろう](https://syosetu.com/)上缓慢抓取小说，分卷写入本地文件

### 配置

1. 安装所需包

    ```shell
    pip install tqdm selenium
    ```

2. 命令行参数

    - `-n` / `--ncode`：小说 NCode
    - `-d` / `--dst`：输出目录
    - `-v` / `--vol`：首卷编号，如果第一卷是番外或设定则指定为 `0`

### 用法

```shell
python single/ncode.py -n ...
```

## PDF 转换

```shell
pip install tqdm pdfplumber
python single/pdf.py
```

## OCR 识别

```shell
pip install requests pyautogui tqdm pillow pycnnum
pip install pymupdf tencentcloud-sdk-python
python single/ocr.py
```

## Sakura 翻译

```shell
pip install requests markdown-it-py
python single/sakura.py
```

## Bangumi 新刊

```shell
pip install requests python-dotenv beautifulsoup4 rapidfuzz
python journal/init.py
python journal/post.py
python journal/meta.py
```
