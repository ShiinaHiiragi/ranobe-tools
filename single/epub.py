import sys
import os
import re
import json
import shutil
import zipfile
import tempfile
import subprocess
import itertools

import numpy
from tqdm import tqdm
from typing import Any, List, Dict, Tuple

from PIL import Image
from bs4 import BeautifulSoup
from markdown_it import MarkdownIt

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
sys.dont_write_bytecode = True
from utils.const import HTML_PREFIX, HTML_SUFFIX, HTML_STYLE
from utils.const import HTML_VERTEND, HTML_NAVLINK

CONFIG = {
    # global field is required
    # type: Dict[str, Any]
    "global": {
        # home dir can be used in "path.*"
        # dir path for epub files
        # type: str
        "path.src": "~/Downloads/src",
        # dir path for md output
        # type: str
        "path.dst": "~/Downloads/dst",
        # dir path for temp file
        # auto generate one if None
        # will not be removed if set
        # type: Optional[str]
        "path.tmp": None,
        # dump parsed_pages to file
        # to check correctness of parsing
        # type: Optional[str]
        "path.dbg": None,
        # whether to clear dst (and tmp/dbg)
        # at the very beginning
        # type: bool
        "path.clear": False,
        # manually specify local setting
        # should be a list of pathlike str
        # target file should be an json Array
        # type: List[str]
        "local.path": [],
        # automatically include json under src
        # increase persistency of local config
        # target file should be an json Array
        # type: bool
        "local.auto": True,
        # whether split by chapter
        # type: bool
        "page.split": True,
        # whether to include front pages
        # whose index starts from zero
        # type: bool
        "page.front": True,
        # remove empty para tag
        # type: bool
        "page.clear": True,
        # width of page title when splitted
        # negative numbers stand for auto
        # e.g. 2 -> 01.md, 02.md, ...
        # type: int
        "page.fill": -1,
        # min page.fill when set to -1
        # type: int
        "page.min": 2,
        # whether to show nav link in html
        # require page.split to be set
        # require out.html to be set
        # type: bool
        "nav.link": True,
        # caption for prev link
        # no effect when links are disabled
        # type: str
        "nav.prev": "← 前へ",
        # caption for next link
        # no effect when links are disabled
        # type: str
        "nav.next": "次へ →",
        # fade out either of bilingual text
        # True -> kana; False -> none kana
        # type: Optional[bool]
        "fade.kana": True,
        # opacity attr of faded text
        # type: str
        "fade.opaque": "0.72",
        # font-size attr of faded text
        # type: str
        "fade.size": "0.84em",
        # top attr of faded text
        # type: str
        "fade.top": "-6px",
        # show image tag in output
        # type: bool
        "image.show": True,
        # width attr of img tag
        # take no effects if not shown
        # invalid for inline img
        # type: Optional[str]
        "image.width": None,
        # switch to alt if img possess
        # inline img only if image.spec enabled
        # type: bool
        "image.alt": True,
        # whether to judge inline img
        # seconds of delay might be caused
        # type: bool
        "image.spec": True,
        # pixel count for possible inline
        # type: int
        "spec.pixel": 32768,
        # img size for possible inline
        # unit: bytes
        # type: int
        "spec.size": 8192,
        # hue for possible inline
        # type: float
        "spec.hue": 4.0,
        # show ruby in output
        # type: bool
        "ruby.show": True,
        # replace br tag into text
        # type: str
        "break.text": "",
        # convert md to html using pandoc
        # seconds of delay might be caused
        # type: bool
        "out.html": True,
        # whether to preserve md file
        # when out.html is set to True
        # type: bool
        "out.keep": False,
        # whether to output vertical text
        # type: bool
        "out.vert": False
    },
    # local field is required
    # the list can be stored in json array
    # and auto loaded by "local.*" config
    # type: List[Dict[str, Any]]
    "local": [
        {
            # name of epub file without extname
            # type: str
            "name": "レジンキャストミルク",
            # temp endpoint for extraction
            # e.g. to capture svg>image tag
            # type: List[str]
            "endpoint": ["svg"],
            # first page out of main body
            # ignored if page.split is set
            # type: int
            "page.last": 25,
            # completely ignore auto generated split
            # will only follow this list
            # type: List[Dict[Any]]
            "page.split": [
                {
                    # title of first line
                    # type: Optional[str]
                    "title": "### プロローグ",
                    # ranges of pages [left, right)
                    # type: List[int]
                    "range": [11, 12]
                },
                {
                    "title": None,
                    "range": [12, 14]
                }
            ],
            # disabled when page.split is set
            # type: bool
            "page.front": False,
            # special treatment for specific file
            # same type as mentioned in global
            # type: bool
            "page.clear": False,
            # type: int
            "page.fill": 2,
            # type: int
            "page.min": 1,
            # type: bool
            "nav.link": False,
            # type: str
            "nav.prev": "← Previous",
            # type: str
            "nav.next": "Next →",
            # type: Optional[bool]
            "fade.kana": True,
            # type: str
            "fade.opaque": "1",
            # type: str
            "fade.size": "1em",
            # type: str
            "fade.top": "6px",
            # type: bool
            "image.show": False,
            # type: Optional[str]
            "image.width": "50%",
            # type: bool
            "image.alt": False,
            # type: bool
            "image.spec": False,
            # type: int
            "spec.pixel": 24576,
            # type: int
            "spec.size": 5120,
            # type: float
            "spec.hue": 1.0,
            # type: bool
            "ruby.show": False,
            # type: str
            "break.text": "\n\n",
            # type: bool
            "out.html": False,
            # type: bool
            "out.keep": True,
            # type: bool
            "out.vert": True
        }
    ]
}

# tag constant
# endpoint (block-level elements)
div_tag = ("div",)
para_tag = ("p",)
header_tag = ("h1", "h2", "h3", "h4", "h5", "h6")
image_tag = ("img", "image")

# inline (inline-level elements)
link_tag = ("a",)
break_tag = ("br",)
ruby_tag = ("ruby",)
rt_tag = ("rt",)
rb_tag = ("rb",)
span_tag = ("span",)

# kana regexp where `・` is removed
kana = (rf'['
    rf'ぁあぃいぅうぇえぉおかがきぎくぐけげこごさざしじすずせぜそぞた'
    rf'だちぢっつづてでとどなにぬねのはばぱひびぴふぶぷへべぺほぼぽま'
    rf'みむめもゃやゅゆょよらりるれろゎわゐゑをんゔゕゖ゛゜ゝゞゟ゠ァ'
    rf'アィイゥウェエォオカガキギクグケゲコゴサザシジスズセゼソゾタダ'
    rf'チヂッツヅテデトドナニヌネノハバパヒビピフブプヘベペホボポマミ'
    rf'ムメモャヤュユョヨラリルレロヮワヰヱヲンヴヵヶヷヸヹヺーヽヾヿ'
rf']')

# util lambda functions
getitem = lambda obj, item, default: obj[item] if item in obj else default
is_pathlike = lambda obj: type(obj) in (str, bytes, os.PathLike)
extract_href = lambda img: getitem(
    img.attrs,
    "src",
    getitem(img.attrs, "xlink:href", "")
).split("#")[0]

def tagged_image(src, width, inline=False):
    tag = f'<img src="assets/{src}"'
    if inline:
        tag += f' style="display: inline; height: 1em; width: auto; vertical-align: middle;"'
    # only works for block-level img
    elif width:
        tag += f' width="{width}"'
    return tag + f'/>'

def is_endpoint(tag, endpoint=(), map={}):
    if tag.name in image_tag:
        raw_src = extract_href(tag)
        return not map[os.path.split(raw_src)[1]]["inline"]

    return tag.name in (
        *para_tag,
        *header_tag,
        *endpoint
    )

markdown = MarkdownIt()
def render_inline(text: str):
    text = markdown.render(text).strip()
    if text.startswith("<p>") and text.endswith("</p>"):
        text = text[3:-4]
    return text

# load global config
assert "global" in CONFIG, CONFIG
global_config: Dict[str, Any] = CONFIG["global"]

config_src_dir_path  = getitem(global_config,    "path.src", "~/Downloads/src")
config_dst_dir_path  = getitem(global_config,    "path.dst", "~/Downloads/dst")
config_tmp_dir_path  = getitem(global_config,    "path.tmp",              None)
config_dbg_dir_path  = getitem(global_config,    "path.dbg",              None)
config_clear_path    = getitem(global_config,  "path.clear",             False)
config_local_path    = getitem(global_config,  "local.path",                [])
config_local_auto    = getitem(global_config,  "local.auto",              True)
config_split_chapter = getitem(global_config,  "page.split",              True)
config_front_page    = getitem(global_config,  "page.front",              True)
config_clear_page    = getitem(global_config,  "page.clear",              True)
config_fill_page     = getitem(global_config,   "page.fill",                -1)
config_min_page      = getitem(global_config,    "page.min",                 2)
config_nav_link      = getitem(global_config,    "nav.link",              True)
config_nav_prev      = getitem(global_config,    "nav.prev",           "← 前へ")
config_nav_next      = getitem(global_config,    "nav.next",           "次へ →")
config_fade_kana     = getitem(global_config,   "fade.kana",              True)
config_fade_opaque   = getitem(global_config, "fade.opaque",            "0.72")
config_fade_size     = getitem(global_config,   "fade.size",          "0.84em")
config_fade_top      = getitem(global_config,    "fade.top",            "-6px")
config_show_image    = getitem(global_config,  "image.show",              True)
config_image_width   = getitem(global_config, "image.width",              None)
config_image_alt     = getitem(global_config,   "image.alt",              True)
config_image_spec    = getitem(global_config,  "image.spec",              True)
config_spec_pixel    = getitem(global_config,  "spec.pixel",             32768)
config_spec_size     = getitem(global_config,   "spec.size",              8192)
config_spec_hue      = getitem(global_config,    "spec.hue",               4.0)
config_show_ruby     = getitem(global_config,   "ruby.show",              True)
config_break_text    = getitem(global_config,  "break.text",                "")
config_output_html   = getitem(global_config,    "out.html",              True)
config_output_keep   = getitem(global_config,    "out.keep",             False)
config_output_vert   = getitem(global_config,    "out.vert",             False)

# process path
assert is_pathlike(config_src_dir_path), config_src_dir_path
assert is_pathlike(config_dst_dir_path), config_dst_dir_path
assert is_pathlike(config_tmp_dir_path) \
    or config_tmp_dir_path == None, config_tmp_dir_path
assert is_pathlike(config_dbg_dir_path) \
    or config_dbg_dir_path == None, config_dbg_dir_path
for config_file_path in config_local_path:
    assert is_pathlike(config_file_path), config_file_path

# expand home path
config_src_dir_path = os.path.expanduser(config_src_dir_path)
config_dst_dir_path = os.path.expanduser(config_dst_dir_path)
config_tmp_dir_path = os.path.expanduser(config_tmp_dir_path) \
    if config_tmp_dir_path != None else None
config_dbg_dir_path = os.path.expanduser(config_dbg_dir_path) \
    if config_dbg_dir_path != None else None
config_local_path = [
    os.path.expanduser(config_file_path)
    for config_file_path in config_local_path
]

# load local config
assert "local" in CONFIG, CONFIG
local_config: List[Dict[str, Any]] = CONFIG["local"]

def load_local_config(file_path):
    global local_config
    config_obj = []
    try:
        with open(file_path, mode="r", encoding="utf-8") as readable:
            config_obj = json.load(readable)
    except: ...

    if isinstance(config_obj, list):
        for item in config_obj:
            if not isinstance(item, dict):
                return
        local_config += config_obj

if config_local_path:
    for config_file_path in config_local_path:
        load_local_config(config_file_path)

# process directory
assert os.path.exists(config_src_dir_path), config_src_dir_path
if config_clear_path:
    if os.path.exists(config_dst_dir_path):
        shutil.rmtree(config_dst_dir_path)
    if is_pathlike(config_tmp_dir_path) and os.path.exists(config_tmp_dir_path):
        shutil.rmtree(config_tmp_dir_path)
    if is_pathlike(config_dbg_dir_path) and os.path.exists(config_dbg_dir_path):
        shutil.rmtree(config_dbg_dir_path)
os.makedirs(config_dst_dir_path, exist_ok=True)

def image_info(raw_dir_path, image_suffix, config):
    local_image_spec = getitem(config, "image.spec", config_image_spec)
    local_spec_pixel = getitem(config, "spec.pixel", config_spec_pixel)
    local_spec_size  = getitem(config,  "spec.size",  config_spec_size)
    local_spec_hue   = getitem(config,   "spec.hue",   config_spec_hue)
    image_map = {}

    for suffix in image_suffix:
        image_path = os.path.join(raw_dir_path, suffix)
        image_name = os.path.split(suffix)[1]
        entry = {
            "width": None,
            "height": None,
            "size": None,
            "color": None,
            "inline": False
        }

        if local_image_spec and os.path.exists(image_path):
            entry["size"] = os.path.getsize(image_path)

            with Image.open(image_path) as img:
                entry["width"] = img.width
                entry["height"] = img.height

                rgb = img.convert("RGB")
                red, green, blue = rgb.split()
                colors = [
                    numpy.array(red, dtype=float),
                    numpy.array(green, dtype=float),
                    numpy.array(blue, dtype=float)
                ]
                sat = numpy.max(colors, axis=0) - numpy.min(colors, axis=0)
                entry["color"] = round(float(numpy.mean(sat)), 2)

        entry["inline"] = [
            entry["width"] is not None and entry["height"] is not None \
                and entry["width"] * entry["height"] < local_spec_pixel,
            entry["size"] is not None and entry["size"] < local_spec_size,
            entry["color"] is not None and entry["color"] < local_spec_hue,
        ].count(True) >= 2
        image_map[image_name] = entry

    return image_map

# recursive functions
def cruise_source(base_dir_path, dir_infix=""):
    epub_list = []
    current_dir_path = os.path.join(config_src_dir_path, dir_infix)
    for unknown_name in os.listdir(current_dir_path):
        unknown_path = os.path.join(current_dir_path, unknown_name)
        if os.path.isdir(unknown_path):
            epub_list += cruise_source(
                base_dir_path,
                dir_infix=os.path.join(dir_infix, unknown_name)
            )

        elif unknown_name.endswith(".epub"):
            epub_list.append({
                "name": unknown_name,
                "infix": dir_infix
            })

        elif unknown_name.endswith(".json") and config_local_auto:
            load_local_config(unknown_path)

    return epub_list

def check_purity(soup: BeautifulSoup, endpoint=(), map={}):
    if soup.name == None:
        return True

    for soup_content in soup.contents:
        if not check_purity(soup_content, endpoint, map):
            return False

    return not is_endpoint(soup, endpoint, map)

def cruise_tag(soup: BeautifulSoup, tag_set: Tuple[str], terminal=True):
    result: List[BeautifulSoup] = []
    if soup.name == None:
        return result

    if soup.name in tag_set:
        result.append(soup)
        if terminal:
            return result

    for soup_content in soup.contents:
        result += cruise_tag(soup_content, tag_set, terminal)

    return result

def cruise_endpoint(soup: BeautifulSoup, endpoint=(), map={}):
    result: List[BeautifulSoup] = []
    if soup.name == None:
        if len(soup.strip()) > 0:
            result.append(soup)
        return result

    for soup_content in soup.contents:
        if not check_purity(soup_content, endpoint, map):
            for soup_content in soup.contents:
                result += cruise_endpoint(soup_content, endpoint, map)
            return result

    result.append(soup)
    return result

def wrap_inline(page: List[BeautifulSoup], endpoint=(), map={}):
    result: List[BeautifulSoup] = []
    last_inline = False
    new_element = None

    for soup in page:
        if is_endpoint(soup, endpoint, map):
            if last_inline:
                result.append(new_element)
                new_element = None
            result.append(soup)
            last_inline = False

        else:
            if not last_inline:
                new_element = BeautifulSoup("<p></p>", "html.parser").p
            new_element.append(soup)
            last_inline = True

    # check last one
    if last_inline:
        result.append(new_element)
    return result

def parse_inline(content: BeautifulSoup, config):
    local_image_width = getitem(config, "image.width", config_image_width)
    local_image_alt   = getitem(config,   "image.alt",   config_image_alt)
    local_show_ruby   = getitem(config,   "ruby.show",   config_show_ruby)
    local_break_text  = getitem(config,  "break.text",  config_break_text)

    parsed: List[str] = []
    images: List[str] = []
    if content.name == None:
        parsed.append(str(content).strip())

    # potential replacement for <br>
    elif content.name in break_tag:
        parsed.append(local_break_text)

    # potential removal for <ruby>
    elif content.name in ruby_tag:
        if local_show_ruby:
            parsed.append("<ruby>")
        for sub_content in content.contents:
            if local_show_ruby or sub_content.name not in rt_tag:
                if not local_show_ruby and sub_content.name in rb_tag:
                    for sub_sub_content in sub_content.contents:
                        pair = parse_inline(sub_sub_content, config)
                        parsed += pair[0]
                        images += pair[1]
                else:
                    pair = parse_inline(sub_content, config)
                    parsed += pair[0]
                    images += pair[1]
        if local_show_ruby:
            parsed.append("</ruby>")

    # inline image such as gaiji
    elif content.name in image_tag:
        raw_src = extract_href(content)
        alt = getitem(content.attrs, "alt", "")
        if local_image_alt and len(alt) > 0:
            parsed.append(alt)
        else:
            parsed.append(tagged_image(
                os.path.split(raw_src)[1],
                local_image_width,
                inline=True
            ))
            images.append(raw_src)

    # for <a> or <span> and other tags
    # such as <em> ... </em> or <hr>
    else:
        not_link_span = not content.name in (*link_tag, *span_tag)
        if not_link_span:
            parsed.append(f"<{content.name}>")
        for sub_content in content.contents:
            pair = parse_inline(sub_content, config)
            parsed += pair[0]
            images += pair[1]
        if not_link_span and len(content.contents) > 0:
            parsed.append(f"</{content.name}>")

    return parsed, images

# non-recursive functions
def parse_endpoint(page: List[BeautifulSoup], config):
    local_show_image  = getitem(config,  "image.show",  config_show_image)
    local_image_width = getitem(config, "image.width", config_image_width)
    local_image_alt   = getitem(config,   "image.alt",   config_image_alt)
    local_image_spec  = getitem(config,  "image.spec",  config_image_spec)
    local_clear_page  = getitem(config,  "page.clear",  config_clear_page)

    parsed: List[List[str]] = []
    images: List[str] = []
    for endpoint in page:
        parsed.append([])
        if endpoint.name in header_tag:
            repeat_times = int(endpoint.name[1:]) + 2
            parsed[-1].append("#" * repeat_times + " ")

        elif endpoint.name in image_tag:
            if local_show_image:
                raw_src = extract_href(endpoint)
                alt = getitem(endpoint.attrs, "alt", "")

                # alt are often used for voiced kana such as 「あ゛」
                if local_image_alt and not local_image_spec and len(alt) > 0:
                    parsed[-1].append(alt)
                else:
                    parsed[-1].append(tagged_image(
                        os.path.split(raw_src)[1],
                        local_image_width,
                        inline=False
                    ))
                    images.append(raw_src)

        for content in endpoint.contents:
            pair = parse_inline(content, config)
            parsed[-1] += pair[0]
            images += pair[1]

        if local_clear_page and len(parsed[-1]) == 0:
            del parsed[-1]

    return parsed, images

# main function
def main(temp_dir_path):
    missing = []
    for epub_info in tqdm(cruise_source(config_src_dir_path)):
        epub_infix = epub_info["infix"]
        epub_filename = epub_info["name"]

        # get file/dir name and path
        raw_filename = re.sub(r'\.epub$', r'', epub_filename)
        assert not raw_filename.endswith(" "), \
            "Trailing spaces detected before extension"

        md_filename = raw_filename + ".md"
        html_filename = raw_filename + ".html"
        zip_filename = raw_filename + ".zip"
        out_filename = raw_filename + ".json"

        direct_src_dir_path = os.path.join(config_src_dir_path, epub_infix)
        direct_temp_dir_path = os.path.join(temp_dir_path, epub_infix)
        direct_dst_dir_path = os.path.join(config_dst_dir_path, epub_infix)

        epub_file_path = os.path.join(direct_src_dir_path, epub_filename)
        zip_file_path = os.path.join(direct_temp_dir_path, zip_filename)

        raw_dir_path = os.path.join(direct_temp_dir_path, raw_filename)
        md_dir_path = os.path.join(direct_dst_dir_path, raw_filename)

        os.makedirs(direct_temp_dir_path, exist_ok=True)
        os.makedirs(md_dir_path, exist_ok=True)

        # copy and extract zip
        shutil.copy(epub_file_path, zip_file_path)
        with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
            zip_ref.extractall(raw_dir_path)

        # find text and images dir automatically
        container_file_path = os.path.join(
            raw_dir_path,
            "META-INF",
            "container.xml"
        )

        # run `pip install lxml` if bs4 raise FeatureNotFound error
        container = BeautifulSoup(open(
            container_file_path,
            mode="r",
            encoding="utf-8"
        ).read(), "xml").container

        root_file_suffix = container.rootfiles.rootfile.attrs["full-path"]
        root_file_path = os.path.join(raw_dir_path, root_file_suffix)
        root_file_infix = os.path.split(root_file_suffix)[0]

        content_opf = BeautifulSoup(open(
            root_file_path,
            mode="r",
            encoding="utf-8"
        ).read(), "xml")
        content_manifest = content_opf.manifest
        content_spine = content_opf.spine

        # extract text file sequence
        text_suffix = []
        image_suffix = []
        manifest_map = {}
        for item in content_manifest:
            if item.name is None:
                continue

            item_id = item.attrs.get("id", "")
            media_type = item.attrs.get("media-type", "")

            if any([
                media_type.startswith(mtype)
                for mtype in ("application/xhtml+xml", "text/html")
            ]) and (
                "properties" not in item.attrs \
                    or item.attrs["properties"] != "nav"
            ):
                text_suffix.append(suffix := os.path.normpath(os.path.join(
                    root_file_infix,
                    item.attrs["href"]
                )))
                manifest_map[item_id] = suffix

            elif media_type.startswith("image/"):
                image_suffix.append(os.path.normpath(os.path.join(
                    root_file_infix,
                    item.attrs["href"]
                )))

        # extract sequence in spine
        # fall back to manifest if missing
        if content_spine is not None:
            text_suffix = []
            for itemref in content_spine:
                if itemref.name is None:
                    continue
                idref = itemref.attrs.get("idref", "")
                if idref in manifest_map:
                    text_suffix.append(manifest_map[idref])

        # load local config
        filter_config = list(filter(
            lambda item: item["name"] == raw_filename,
            local_config
        ))

        # choose the first matched in response to overlapping
        if len(filter_config) > 0:
            filter_config = filter_config[0]

        # config extraction
        get_filter = lambda key, default : getitem(filter_config, key, default)
        local_split_page  = get_filter( "page.split",               None)
        local_front_page  = get_filter( "page.front",  config_front_page)
        local_fill_page   = get_filter(  "page.fill",   config_fill_page)
        local_min_page    = get_filter(   "page.min",    config_min_page)
        local_nav_link    = get_filter(   "nav.link",    config_nav_link)
        local_nav_prev    = get_filter(   "nav.prev",    config_nav_prev)
        local_nav_next    = get_filter(   "nav.next",    config_nav_next)
        local_endpoint    = get_filter(   "endpoint",                 ())
        local_fade_kana   = get_filter(  "fade.kana",   config_fade_kana)
        local_fade_opaque = get_filter("fade.opaque", config_fade_opaque)
        local_fade_size   = get_filter(  "fade.size",   config_fade_size)
        local_fade_top    = get_filter(   "fade.top",    config_fade_top)
        local_last_page   = get_filter(  "page.last",   len(text_suffix))
        local_output_html = get_filter(   "out.html", config_output_html)
        local_output_keep = get_filter(   "out.keep", config_output_keep)
        local_output_vert = get_filter(   "out.vert", config_output_vert)

        local_fill_page = max(local_fill_page, local_min_page)

        if local_output_html:
            with open(os.devnull, "wb") as devnull:
                subprocess.check_call(
                    ["pandoc", "-h"],
                    stdout=devnull,
                    stderr=subprocess.STDOUT
                )

        # simple image (e.g. img version of '~' char)
        # will be viewed as inline in purity check
        image_map = image_info(raw_dir_path, image_suffix, filter_config)

        # start to parse xhtml contents
        # read and process xhtml text
        xhtml_raw_text = [open(
            os.path.join(raw_dir_path, xhtml_filename),
            mode="r",
            encoding="utf-8"
        ).read() for xhtml_filename in text_suffix]

        xhtml_soup = [
            BeautifulSoup(raw_text, 'html.parser').body
            for raw_text in xhtml_raw_text
        ]

        # find toc automatically
        href_occurence = [
            [
                soup.attrs["href"].split("#")[0]
                for soup in filter(lambda soup: "href" in soup.attrs, page)
            ]
            for page in [
                cruise_tag(soup, link_tag, False)
                for soup in xhtml_soup
            ]
        ]
        href_occurence_count = [len(item) for item in href_occurence]

        toc_indices = []
        if len(href_occurence_count) != 0:
            toc_index = href_occurence_count.index(max(href_occurence_count))
            toc_infix = os.path.split(text_suffix[toc_index])[0]
            toc_indices = sorted(list(set([
                text_suffix.index(os.path.normpath(os.path.join(toc_infix, filename)))
                for filename in href_occurence[toc_index]
            ])))

        if len(toc_indices) == 0:
            toc_indices = list(range(local_last_page))

        start_from_one = True
        toc_indices.append(local_last_page)
        if local_front_page and local_split_page == None and toc_indices[0] != 0:
            toc_indices.insert(0, 0)
            start_from_one = False

        # parse and merge pages
        pages = [wrap_inline(
            cruise_endpoint(soup, local_endpoint, image_map),
            local_endpoint,
            image_map
        ) for soup in xhtml_soup]

        parsed_endpoint = [parse_endpoint(page, filter_config) for page in pages]
        parsed_pages = [item[0] for item in parsed_endpoint]
        parsed_images = [[os.path.normpath(os.path.join(
            os.path.split(text_suffix[index])[0], sub_item
        )) for sub_item in item] for index, item in enumerate(
            [item[1] for item in parsed_endpoint]
        )]

        if config_dbg_dir_path != None:
            direct_dbg_dir_path = os.path.join(config_dbg_dir_path, epub_infix)
            os.makedirs(direct_dbg_dir_path, exist_ok=True)
            dbg_file_path = os.path.join(direct_dbg_dir_path, out_filename)
            with open(dbg_file_path, mode="w", encoding="utf-8") as _writable:
                json.dump(parsed_pages, _writable, ensure_ascii=False, indent=4)

        lined_pages = [["".join(para) for para in page] for page in parsed_pages]
        marked_pages = [[(
            line,
            re.search(kana, line) is not None
        ) for line in page] for page in lined_pages]

        faded_pages = [[((
                f"<p style=\""
                f"opacity: {local_fade_opaque}; "
                f"font-size: {local_fade_size}; "
                f"top: {local_fade_top}; "
                f"\">{render_inline(line)}</p>"
            ) if local_fade_kana == is_jp else line
        ) for line, is_jp in page] for page in marked_pages]
        merged_pages = ["\n\n".join(page) for page in faded_pages]

        image_subset = set()
        volume_text = []

        def convert_md(src_file_path, dst_file_path, title, prev=None, next=None):
            subprocess.run([
                "pandoc", src_file_path,
                "-o", dst_file_path,
                "-f", "markdown+hard_line_breaks"
            ], check=True)

            with open(dst_file_path, mode="r", encoding="utf-8") as readable:
                text = readable.read()

            with open(dst_file_path, mode="w", encoding="utf-8") as writable:
                vert_end = '\n' + HTML_VERTEND if local_output_vert else ''
                writable.write(HTML_PREFIX.format(
                    STYLE=HTML_STYLE(local_output_vert) + vert_end,
                    TITLE=title
                ))
                writable.write(text)

                if local_nav_link:
                    writable.write(HTML_NAVLINK.format(
                        PREV_LINK=("" if prev is None else f"{prev}.html"),
                        NEXT_LINK=("" if next is None else f"{next}.html"),
                        PREV_TEXT=(local_nav_prev if prev else ""),
                        NEXT_TEXT=(local_nav_next if next else "")
                    ))
                writable.write(HTML_SUFFIX)

            if not local_output_keep:
                os.remove(src_file_path)

        # used by following codes
        # return iterable detected images
        def merge_chapter(index, left, right, images, last, title=None):
            chapter_text = "\n\n".join(merged_pages[left:right])
            if config_split_chapter:
                format_title = lambda index: f"{index+int(start_from_one):0{local_fill_page}d}"
                raw_title = format_title(index)
                prev_title = format_title(index - 1) if index > 0 else None
                next_title = format_title(index + 1) if not last else None
                md_file_path = os.path.join(md_dir_path, f"{raw_title}.md")
                html_file_path = os.path.join(md_dir_path, f"{raw_title}.html")

                with open(md_file_path, mode="w", encoding="utf-8") as writable:
                    if title != None:
                        writable.write(title + "\n\n")
                    writable.write(chapter_text + "\n")

                if local_output_html:
                    convert_md(
                        md_file_path,
                        html_file_path,
                        raw_title,
                        prev_title,
                        next_title
                    )

            else:
                if title != None:
                    volume_text.append(title)
                volume_text.append(chapter_text)
            return itertools.chain(*images[left:right])

        # write output and copy images
        # if local pages.split are specified
        if local_split_page != None:
            page_size = len(local_split_page)
            local_fill_page = len(str(page_size - bool(not start_from_one))) \
                if local_fill_page < 0 else local_fill_page
            for meta_index, split_info in enumerate(local_split_page):
                assert "range" in split_info \
                    and len(split_info["range"]) == 2, split_info
                split_title = getitem(split_info, "title", None)
                extracted_images_iter = merge_chapter(
                    meta_index,
                    *split_info["range"],
                    parsed_images,
                    meta_index + 1 == page_size,
                    title=split_title
                )
                image_subset = image_subset.union(extracted_images_iter)

        # if local pages.split are not specified
        else:
            # equivalent to len(toc_indices[:-1])
            page_size = len(toc_indices) - 1
            local_fill_page = len(str(page_size - bool(not start_from_one))) \
                if local_fill_page < 0 else local_fill_page

            for meta_index, index in enumerate(toc_indices[:-1]):
                next_index = toc_indices[meta_index + 1]
                extracted_images_iter = merge_chapter(
                    meta_index,
                    index,
                    next_index,
                    parsed_images,
                    meta_index + 1 == page_size
                )
                image_subset = image_subset.union(extracted_images_iter)

        if len(image_subset) > 0:
            assets_dir_path = os.path.join(md_dir_path, "assets")
            os.makedirs(assets_dir_path, exist_ok=True)
            for image_filename in image_subset:
                image_file_path = os.path.join(raw_dir_path, image_filename)
                if os.path.exists(image_file_path):
                    shutil.copy(image_file_path, assets_dir_path)
                else:
                    missing.append(os.path.join(
                        epub_infix,
                        epub_filename,
                        image_filename
                    ))

        # if global chapter.split are not specified
        # chapters will be recorded in volume_text
        # instead of being written in merge_chapter()
        # and will be written at this point
        if not config_split_chapter:
            md_file_path = os.path.join(md_dir_path, md_filename)
            html_file_path = os.path.join(md_dir_path, html_filename)
            with open(md_file_path, mode="w", encoding="utf-8") as writable:
                writable.write("\n\n".join(volume_text) + "\n")
            if local_output_html:
                convert_md(md_file_path, html_file_path, raw_filename)

    if len(missing) > 0:
        print(f"Missing assets: {', '.join(missing)}")

# entrance point
if __name__ == "__main__":
    if config_tmp_dir_path == None:
        with tempfile.TemporaryDirectory() as temp_dir_path:
            main(temp_dir_path)

    else:
        os.makedirs(config_tmp_dir_path, exist_ok=True)
        main(config_tmp_dir_path)
