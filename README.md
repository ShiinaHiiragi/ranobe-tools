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

2. 配置分为 `global`（全局配置）和 `local`（局部配置）
    - 全局配置：未找到局部配置时默认使用
        - 路径与环境设置

            | 项目         |    类型     | 默认值              | 说明                                                                                             |
            | :----------- | :---------: | :------------------ | :----------------------------------------------------------------------------------------------- |
            | `path.src`   |    `str`    | `"~/Downloads/src"` | EPUB 源文件存放目录录。                                                                          |
            | `path.dst`   |    `str`    | `"~/Downloads/dst"` | Markdown / HTML 文件的输出目录。                                                                 |
            | `path.tmp`   | `str/None`  | `None`              | 解压提取文件的临时目录。设为 `None` 时会自动创建并在运行后销毁；若指定路径，运行后将保留临时文件 |
            | `path.dbg`   | `str/None`  | `None`              | 调试目录。若指定，会将解析后的页面数据导出为 JSON 文件，用于排查解析错误                         |
            | `path.clear` |   `bool`    | `False`             | 运行前是否清空 `dst` / `tmp` / `dbg` 目录                                                        |
            | `local.path` | `List[str]` | `[]`                | 外部本地配置文件的路径列表，目标文件应为包含 JSON 数组的文件                                     |
            | `local.auto` |   `bool`    | `True`              | 是否自动将 `src` 目录下的 `.json` 文件作为 `local` 配置加载                                      |

        - 分页与内容提取

            | 项目         |  类型  | 默认值   | 说明                                                                                     |
            | :----------- | :----: | :------- | :--------------------------------------------------------------------------------------- |
            | `page.split` | `bool` | `True`   | 是否按书籍内置目录将内容拆分为多个章节文件                                               |
            | `page.front` | `bool` | `True`   | 是否保留目录的封面、彩插等，其索引从 `0` 开始                                            |
            | `page.clear` | `bool` | `True`   | 是否自动移除解析后产生的空段落                                                           |
            | `page.fill`  | `int`  | `-1`     | 拆分文件时的文件名前缀补零宽度（如设为 `3` 则为 `001.md`），负数表示根据总章节数自动计算 |
            | `page.min`   | `int`  | `2`      | 当 `page.fill` 设为负数时，文件名前缀补零的最小宽度                                      |
            | `break.text` | `str`  | `"\n\n"` | 将的 `<br>` 标签替换为指定的文本，默认替换为 Markdown 的段落换行                         |

        - 排版与样式处理

            | 项目          |    类型     | 默认值     | 说明                                                                                                   |
            | :------------ | :---------: | :--------- | :----------------------------------------------------------------------------------------------------- |
            | `fade.kana`   | `bool/None` | `True`     | 是否淡化交替文本：`True` 淡化包含假名的行；`False` 淡化不含假名的行；`None` 不淡化                     |
            | `fade.opaque` |    `str`    | `"0.72"`   | 被淡化文本的透明度（`opacity` 属性）                                                                   |
            | `fade.size`   |    `str`    | `"0.84em"` | 被淡化文本的字体大小（`font-size` 属性）                                                               |
            | `fade.top`    |    `str`    | `"-6px"`   | 被淡化文本的相对位置偏移（CSS `top` 属性）                                                             |
            | `image.show`  |   `bool`    | `True`     | 是否在输出文本中保留并显示图片                                                                         |
            | `image.width` | `str/None`  | `None`     | HTML / Markdown 中图片的展示宽度，设为 `None` 则保持原图尺寸                                           |
            | `image.alt`   |   `bool`    | `False`    | 当图片带有 `alt` 属性时，是否直接输出 `alt` 文本而不显示图片（常用于处理带浊点的假名外字，如「あ゛」） |
            | `image.spec`  |   `bool`    | `True`     | 是否自动推断图片为行内元素，`image.alt` 开启时无效                                                     |
            | `spec.pixel`  |    `int`    | `32768`    | 推断行内图片的像素面积上限（宽 × 高）                                                                  |
            | `spec.size`   |    `int`    | `8192`     | 推断行内图片的文件大小上限（单位：字节）                                                               |
            | `spec.hue`    |   `float`   | `4.0`      | 推断行内图片的色相均值上限；以上三个条件满足任意两个则推定为行内图片                                   |
            | `ruby.show`   |   `bool`    | `True`     | 是否保留显示 Ruby 振假名                                                                               |

        - 导出与 HTML 导航

            | 项目       |  类型  | 默认值     | 说明                                                                                       |
            | :--------- | :----: | :--------- | :----------------------------------------------------------------------------------------- |
            | `out.html` | `bool` | `True`     | 是否调用 `pandoc` 将 Markdown 自动转换为 HTML 格式输出（需要预先安装 pandoc）              |
            | `out.keep` | `bool` | `False`    | 当开启 HTML 导出时，是否保留原本生成的 Markdown 文件                                       |
            | `out.vert` | `bool` | `False`    | 导出的 HTML 是否使用竖排样式                                                               |
            | `nav.link` | `bool` | `True`     | 是否在导出的 HTML 底部添加「上一页 / 下一页」导航链接（需开启 `page.split` 与 `out.html`） |
            | `nav.prev` | `str`  | `"← 前へ"` | 「上一页」按钮的显示文本                                                                   |
            | `nav.next` | `str`  | `"次へ →"` | 「下一页」按钮的显示文本                                                                   |

    - 局部配置：使文件名为 `name` 的 EPUB 运用指定配置覆盖同名全局配置
        - `local` 可指定如下专有配置

            | 项目         | 类型         | 说明                                                                                                                               |
            | :----------- | :----------- | :--------------------------------------------------------------------------------------------------------------------------------- |
            | `name`       | `str`        | 不包含 `.epub` 后缀的文件名                                                                                                        |
            | `endpoint`   | `List[str]`  | 解析页面时的块级终点标签。例如 `["svg"]` 可以在遇到 `<svg>` 时停止深入解析，用于直接捕获被 SVG 包裹的图片                          |
            | `page.last`  | `int`        | 强制指定正文的最后一页的索引，仅在不拆分章节且自动识别目录失败时生效                                                               |
            | `page.split` | `List[dict]` | 忽略书籍自带的目录，强制按此处定义的规则拆分章节。列表内每个字典需包含 `title`（首行标题内容）与 `range`（提取页面的左闭右开区间） |

        - 局部配置的三种生效方式
            - 直接在脚本中修改 `local` 列表
            - 在 `src` 目录下新建 `.json` 文件（需开启 `local.auto`）
            - 在任意目录下新建 `.json` 文件，并在全局配置的 `local.path` 添加路径

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
    - `-c` / `--cli`：是否以无头模式启动 Selenium

### 用法示例

```shell
python single/ncode.py -n n7437dj
```

## Pixiv 下载

从 [Pixiv](https://www.pixiv.net/) 上缓慢抓取小说，按篇写入本地文件

### 配置

1. 安装所需包

    ```shell
    pip install selenium beautifulsoup4
    ```

2. 命令行参数
    - `-n` / `--uid`：作者 UID
    - `-s` / `--srt`：开始捕获的页码，默认为 `1`；省略也有一定限度的恢复功能
    - `-d` / `--dst`：输出目录路径
    - `-c` / `--cli`：是否以无头模式启动 Selenium；当 `-l` 设置时该选项无效
    - `-l` / `--login`：是否登录，用于加载被隐藏的文章

### 用法示例

```shell
python single/pixiv.py -u 2948941
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
    pip install tqdm pyautogui pillow python-dotenv requests pymupdf pycnnum
    ```

    使用腾讯云 SDK 需要额外安装 `pip install tencentcloud-sdk-python`

2. 环境参数：在项目根目录新建 `.env` 文件，填入如下环境变量（二者任选其一）
    - `ACCESS_TOKEN`：百度智能云的 API 临时授权凭证
    - `SECRET_ID` 与 `SECRET_KEY`：腾讯云的 API 密钥

3. 命令行参数
    - `-b` / `--base`：基础工作目录
    - `-s` / `--min`：第一张图的序号
    - `-d` / `--max`：最后一张图的序号加一，除了拍摄时都不能为零
    - `-v` / `--vol`：首卷编号，如果是番外或设定集则指定为 `0`
    - `-p` / `--pdf`：从 PDF 获取图片，默认从阅读器采集
    - `-o` / `--ocr`：可选 OCR 后端，包括 `baidu` 或 `tencent`
    - `--app-point`：阅读器在任务栏的坐标
    - `--nxt-point`：用于点击下一页的坐标
    - `--cht-point`：消息平台在任务栏的坐标
    - `--tag-point`：需要发送消息的对象在消息列表的坐标
    - `--box-point`：输入框的坐标
    - `--hnt-point`：发送按钮的坐标
    - `--chck-point`：检查这个位置的像素，以决定是否停止拍摄
    - `--halt-color`：被检查像素的目标颜色 RGB
    - `--send-color`：新章节线的颜色
    - `--line-length`：新章节线颜色的像素个数
    - `--chapter-lne`：新章节线在处理后图片所在的行数
    - `--rotat-angle`：横屏拍摄后需要旋转的角度
    - `--l-threshold`：判定为新一段的缩进临界值
    - `--shot-region`：拍摄的范围，前两个是坐标，后两个是长和宽
    - `--crop-region`：裁剪的范围，前后两个都是坐标

4. 可调节常量
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
  --line-length 1235 \
  --chapter-lne 76 \
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

1. 安装 [Ollama](https://ollama.com/download) 并配置 [`Sakura-14B-Qwen2.5-v1.0-GGUF`](https://huggingface.co/SakuraLLM/Sakura-14B-Qwen2.5-v1.0-GGUF)
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

- `journal/init.py`：收集当月轻小说新刊情报
- `journal/post.py`：将上述情报整理为可在 Bangumi 发布的日志
- `journal/meta.py`：在 Rakuten 收集并整理新刊相关信息，生成关联报表

### 配置

1. 安装所需包

    ```shell
    pip install requests python-dotenv beautifulsoup4 rapidfuzz
    ```

2. 通用命令行参数
    - `-y` / `--year`：目标年份，默认为当前年份
    - `-m` / `--month`：目标月份，默认为当前月份
    - `-d` / `--data`：输出数据目录，默认为仓库根目录的 `data/`

3. `journal/post.py` 附加命令行参数
    - `-p` / `--post`：前一月的日志编号，验证通过后加入当期日志链接
    - `-u` / `--update`：是否强制更新，当所有条目都被搜索过时，通过此项重新搜索缺失条目

4. 通用环境参数：在项目根目录新建 `.env` 文件，填入如下环境变量
    - `ACCESS_TOKEN`：从 https://next.bgm.tv/demo/access-token 获取
    - `USER_ID`：用户名
    - `USER_AGENT`：浏览器 UA

### 用法示例

```shell
python journal/init.py
python journal/post.py
python journal/meta.py
```
