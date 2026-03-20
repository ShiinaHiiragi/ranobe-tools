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

2. 由于配置较为复杂，推荐直接修改 `CONFIG` 变量
    - 配置说明详见脚本内注释
    - 也可在全局配置中通过 `path.src` 或 `local.path` 条目创建本地配置文件

### 用法示例

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
    - `-d` / `--dst`：输出目录路径
    - `-v` / `--vol`：首卷编号，如果是番外或设定集则指定为 `0`

### 用法示例

```shell
python single/ncode.py -n n7437dj
```

## PDF 转换

将文字 PDF 小说转换为 txt 纯文本

1. 去除页眉/页脚及 ruby 小字，自动识别分段
2. **仅适用部分性质良好的 PDF，一般不推荐使用**

### 配置

1. 安装所需包

    ```shell
    pip install tqdm pdfplumber
    ```

2. 命令行参数
    - `-s` / `--src`：输入目录路径，将所有待处理 PDF 文件置于其中
    - `-d` / `--dst`：输出目录路径

### 用法示例

```shell
python single/pdf.py
```

## OCR 识别

将图片小说或转换为 txt 文字

1. 提取图片 PDF 文件的图片，或对仅支持阅读器访问的小说实现模拟翻页、截图并通过 OCR 转换为文字
2. **后者仅适用部分流程相似的阅读器，一般不推荐使用**

### 配置

1. 安装所需包

    ```shell
    pip install tqdm pyautogui pillow requests pymupdf pycnnum
    ```

    使用腾讯云 SDK 需要额外安装 `pip install tencentcloud-sdk-python`

2. 命令行参数
    - `-b` / `--base`：
    - `-s` / `--min`：第一张图的序号
    - `-d` / `--max`：最后一张图的序号加一，除了拍摄时都不能为零
    - `-v` / `--vol`：首卷编号，如果是番外或设定集则指定为 `0`
    - `--app-point`：阅读器在任务栏的坐标
    - `--nxt-point`：用于点击下一页的坐标
    - `--cht-point`：消息平台在任务栏的坐标
    - `--tag-point`：需要发送消息的对象在消息列表的坐标
    - `--box-point`：输入框的坐标
    - `--hnt-point`：发送按钮的坐标
    - `--chck-point`：检查这个位置的像素，以决定是否停止拍摄
    - `--halt-color`：被检查像素的目标颜色 RGB
    - `--send-color`：新章节线的颜色
    - `--chapter-lne`：新章节线在处理后图片所在的行数
    - `--line-length`：新章节线颜色的像素个数
    - `--rotat-angle`：横屏拍摄后需要旋转的角度
    - `--l-threshold`：判定为新一段的缩进临界值
    - `--shot-region`：拍摄的范围，前两个是坐标，后两个是长和宽
    - `--crop-region`：裁剪的范围，前后两个都是坐标

3. 可调节常量
    - `CHAPTERS`：章节序号标注方式
    - `REPLACE_REG`：替换章节序号的正则表达式
    - `VOLUME_REG`：匹配卷首章节的正则表达式；若无法按预期分卷，可临时添加标志
    - `NORM_INTERVAL`：通用单次操作标准等待时间
    - `SHRT_INTERVAL`：单次操作较短等待时间
    - `LONG_INTERVAL`：单次操作较长等待时间

### 用法示例

```shell
python single/ocr.py \
  --base ~/Downloads \
  --vol 0 \
  --min 0 \
  --max 255 \
  --app-point 110 1400 \
  --nxt-point 180 1280 \
  --cht-point 180 1400 \
  --tag-point 300 150 \
  --box-point 800 1200 \
  --hnt-point 2440 1320 \
  --chck-point 2350 1200 \
  --halt-color 255 99 72 \
  --send-color 122 122 122 \
  --chapter-lne 76 \
  --line-length 1235 \
  --rotat-angle 90 \
  --l-threshold 40 \
  --shot-region 85 50 2340 1315 \
  --crop-region 50 30 2240 1276
```

## Sakura 翻译

将日文小说翻译为中文并输出 Markdown 或 HTML 格式的对照文本
1. 支持使用术语表控制专有名词的翻译，推荐使用 [KeywordGacha](https://github.com/neavo/KeywordGacha) 自动化 NER
2. 按块翻译文本，当中文行数与原文不匹配时二分重试，直到退化为单行翻译

### 配置

1. 下载 Ollama 并配置 `Sakura-14B-Qwen2.5-v1.0-GGUF`
    - 新建 `Modelfile` 文件并指定模型文件路径

        ```plaintext
        FROM /data/models/sakura-14b-qwen2.5-v1.0-q6k.gguf
        ```

    - 通过 `ollama serve` 启动后端，创建并运行模型

        ```shell
        ollama create sakura -f Modelfile
        ollama run sakura
        ```

    - 指定 `keep_alive` 以使模型长期驻留于显存

        ```shell
        curl http://localhost:11434/api/generate -d '{
            "model": "sakura",
            "prompt": "",
            "keep_alive": -1
        }'
        ```

2. 安装所需包

    ```shell
    pip install requests markdown-it-py
    ```

3. 命令行参数
    - `-s` / `--src`：输入目录路径，将所有待处理文本文件置于其中
    - `-d` / `--dst`：输出目录路径
    - `-r` / `--ref`：术语表文件路径
    - `-m` / `--raw`：以 Markdown 形式输出结果，默认以 HTML 形式输出

4. 可调节常量
    - `MODEL_NAME`：模型名称
    - `BASE_URL`：模型 API 路径
    - `MAX_RETRY`：同一语段 API 调用最大重试次数
    - `SEGMENT_UNIT`：语段最小长度
    - `SEGMENT_SIZE`：语段最大长度
    - `PREV_CONTEXT_SIZE`：上下文最大长度

### 用法示例

```shell
python single/sakura.py
```

## Bangumi 新刊

```shell
pip install requests python-dotenv beautifulsoup4 rapidfuzz
python journal/init.py
python journal/post.py
python journal/meta.py
```
