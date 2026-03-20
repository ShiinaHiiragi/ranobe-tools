
HTML_PREFIX = """<!doctype html>
<html>
<head>
<meta charset='UTF-8'><meta name='viewport' content='width=device-width initial-scale=1'>

<style type='text/css'>html {{overflow-x: initial !important;}}:root {{ --bg-color:#ffffff; --text-color:#333333; --select-text-bg-color:#B5D6FC; --select-text-font-color:auto; --monospace:"Lucida Console",Consolas,"Courier",monospace; --title-bar-height:20px; }}
.mac-os-11 {{ --title-bar-height:28px; }}
html {{ font-size: 14px; background-color: var(--bg-color); color: var(--text-color); font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased; }}
body {{ margin: 0px; padding: 0px; height: auto; inset: 0px; font-size: 1rem; line-height: 1.42857; overflow-x: hidden; background: inherit; tab-size: 4; }}
iframe {{ margin: auto; }}
a.url {{ word-break: break-all; }}
a:active, a:hover {{ outline: 0px; }}
.in-text-selection, ::selection {{ text-shadow: none; background: var(--select-text-bg-color); color: var(--select-text-font-color); }}
#write {{ margin: 0px auto; height: auto; width: inherit; word-break: normal; overflow-wrap: break-word; position: relative; white-space: normal; overflow-x: visible; padding-top: 36px; }}
#write.first-line-indent p {{ text-indent: 2em; }}
#write.first-line-indent li p, #write.first-line-indent p * {{ text-indent: 0px; }}
#write.first-line-indent li {{ margin-left: 2em; }}
.for-image #write {{ padding-left: 8px; padding-right: 8px; }}
body.typora-export {{ padding-left: 30px; padding-right: 30px; }}
.typora-export .footnote-line, .typora-export li, .typora-export p {{ white-space: normal; }}
.typora-export .task-list-item input {{ pointer-events: none; }}
@media screen and (max-width: 500px) {{
  body.typora-export {{ padding-left: 0px; padding-right: 0px; }}
  #write {{ padding-left: 20px; padding-right: 20px; }}
  .CodeMirror-sizer {{ margin-left: 0px !important; }}
  .CodeMirror-gutters {{ display: none !important; }}
}}
#write li > figure:last-child {{ margin-bottom: 0.5rem; }}
#write ol, #write ul {{ position: relative; }}
img {{ max-width: 100%; vertical-align: middle; image-orientation: from-image; }}
button, input, select, textarea {{ color: inherit; font: inherit; }}
input[type="checkbox"], input[type="radio"] {{ line-height: normal; padding: 0px; }}
*, ::after, ::before {{ box-sizing: border-box; }}
#write h1, #write h2, #write h3, #write h4, #write h5, #write h6, #write p, #write pre {{ width: inherit; }}
#write h1, #write h2, #write h3, #write h4, #write h5, #write h6, #write p {{ position: relative; }}
p {{ line-height: inherit; }}
h1, h2, h3, h4, h5, h6 {{ break-after: avoid-page; break-inside: avoid; orphans: 4; }}
p {{ orphans: 4; }}
h1 {{ font-size: 2rem; }}
h2 {{ font-size: 1.8rem; }}
h3 {{ font-size: 1.6rem; }}
h4 {{ font-size: 1.4rem; }}
h5 {{ font-size: 1.2rem; }}
h6 {{ font-size: 1rem; }}
.md-math-block, .md-rawblock, h1, h2, h3, h4, h5, h6, p {{ margin-top: 1rem; margin-bottom: 1rem; }}
.hidden {{ display: none; }}
.md-blockmeta {{ color: rgb(204, 204, 204); font-weight: 700; font-style: italic; }}
a {{ cursor: pointer; }}
sup.md-footnote {{ padding: 2px 4px; background-color: rgba(238, 238, 238, 0.7); color: rgb(85, 85, 85); border-radius: 4px; cursor: pointer; }}
sup.md-footnote a, sup.md-footnote a:hover {{ color: inherit; text-transform: inherit; text-decoration: inherit; }}
#write input[type="checkbox"] {{ cursor: pointer; width: inherit; height: inherit; }}
figure {{ overflow-x: auto; margin: 1.2em 0px; max-width: calc(100% + 16px); padding: 0px; }}
figure > table {{ margin: 0px; }}
tr {{ break-inside: avoid; break-after: auto; }}
thead {{ display: table-header-group; }}
table {{ border-collapse: collapse; border-spacing: 0px; width: 100%; overflow: auto; break-inside: auto; text-align: left; }}
table.md-table td {{ min-width: 32px; }}
.CodeMirror-gutters {{ border-right: 0px; background-color: inherit; }}
.CodeMirror-linenumber {{ user-select: none; }}
.CodeMirror {{ text-align: left; }}
.CodeMirror-placeholder {{ opacity: 0.3; }}
.CodeMirror pre {{ padding: 0px 4px; }}
.CodeMirror-lines {{ padding: 0px; }}
div.hr:focus {{ cursor: none; }}
#write pre {{ white-space: pre-wrap; }}
#write.fences-no-line-wrapping pre {{ white-space: pre; }}
#write pre.ty-contain-cm {{ white-space: normal; }}
.CodeMirror-gutters {{ margin-right: 4px; }}
.md-fences {{ font-size: 0.9rem; display: block; break-inside: avoid; text-align: left; overflow: visible; white-space: pre; background: inherit; position: relative !important; }}
.md-fences-adv-panel {{ width: 100%; margin-top: 10px; text-align: center; padding-top: 0px; padding-bottom: 8px; overflow-x: auto; }}
#write .md-fences.mock-cm {{ white-space: pre-wrap; }}
.md-fences.md-fences-with-lineno {{ padding-left: 0px; }}
#write.fences-no-line-wrapping .md-fences.mock-cm {{ white-space: pre; overflow-x: auto; }}
.md-fences.mock-cm.md-fences-with-lineno {{ padding-left: 8px; }}
.CodeMirror-line, twitterwidget {{ break-inside: avoid; }}
.footnotes {{ opacity: 0.8; font-size: 0.9rem; margin-top: 1em; margin-bottom: 1em; }}
.footnotes + .footnotes {{ margin-top: 0px; }}
.md-reset {{ margin: 0px; padding: 0px; border: 0px; outline: 0px; vertical-align: top; background: 0px 0px; text-decoration: none; text-shadow: none; float: none; position: static; width: auto; height: auto; white-space: nowrap; cursor: inherit; -webkit-tap-highlight-color: transparent; line-height: normal; font-weight: 400; text-align: left; box-sizing: content-box; direction: ltr; }}
li div {{ padding-top: 0px; }}
blockquote {{ margin: 1rem 0px; }}
li .mathjax-block, li p {{ margin: 0.5rem 0px; }}
li blockquote {{ margin: 1rem 0px; }}
li {{ margin: 0px; position: relative; }}
blockquote > :last-child {{ margin-bottom: 0px; }}
blockquote > :first-child, li > :first-child {{ margin-top: 0px; }}
.footnotes-area {{ color: rgb(136, 136, 136); margin-top: 0.714rem; padding-bottom: 0.143rem; white-space: normal; }}
#write .footnote-line {{ white-space: pre-wrap; }}
@media print {{
  body, html {{ border: 1px solid transparent; height: 99%; break-after: avoid; break-before: avoid; font-variant-ligatures: no-common-ligatures; }}
  #write {{ margin-top: 0px; padding-top: 0px; border-color: transparent !important; }}
  .typora-export * {{ -webkit-print-color-adjust: exact; }}
  .typora-export #write {{ break-after: avoid; }}
  .typora-export #write::after {{ height: 0px; }}
  .is-mac table {{ break-inside: avoid; }}
  .typora-export-show-outline .typora-export-sidebar {{ display: none; }}
}}
.footnote-line {{ margin-top: 0.714em; font-size: 0.7em; }}
a img, img a {{ cursor: pointer; }}
pre.md-meta-block {{ font-size: 0.8rem; min-height: 0.8rem; white-space: pre-wrap; background: rgb(204, 204, 204); display: block; overflow-x: hidden; }}
p > .md-image:only-child:not(.md-img-error) img, p > img:only-child {{ display: block; margin: auto; }}
#write.first-line-indent p > .md-image:only-child:not(.md-img-error) img {{ left: -2em; position: relative; }}
p > .md-image:only-child {{ display: inline-block; width: 100%; }}
#write .MathJax_Display {{ margin: 0.8em 0px 0px; }}
.md-math-block {{ width: 100%; }}
.md-math-block:not(:empty)::after {{ display: none; }}
.MathJax_ref {{ fill: currentcolor; }}
[contenteditable="true"]:active, [contenteditable="true"]:focus, [contenteditable="false"]:active, [contenteditable="false"]:focus {{ outline: 0px; box-shadow: none; }}
.md-task-list-item {{ position: relative; list-style-type: none; }}
.task-list-item.md-task-list-item {{ padding-left: 0px; }}
.md-task-list-item > input {{ position: absolute; top: 0px; left: 0px; margin-left: -1.2em; margin-top: calc(1em - 10px); border: none; }}
.math {{ font-size: 1rem; }}
.md-toc {{ min-height: 3.58rem; position: relative; font-size: 0.9rem; border-radius: 10px; }}
.md-toc-content {{ position: relative; margin-left: 0px; }}
.md-toc-content::after, .md-toc::after {{ display: none; }}
.md-toc-item {{ display: block; color: rgb(65, 131, 196); }}
.md-toc-item a {{ text-decoration: none; }}
.md-toc-inner:hover {{ text-decoration: underline; }}
.md-toc-inner {{ display: inline-block; cursor: pointer; }}
.md-toc-h1 .md-toc-inner {{ margin-left: 0px; font-weight: 700; }}
.md-toc-h2 .md-toc-inner {{ margin-left: 2em; }}
.md-toc-h3 .md-toc-inner {{ margin-left: 4em; }}
.md-toc-h4 .md-toc-inner {{ margin-left: 6em; }}
.md-toc-h5 .md-toc-inner {{ margin-left: 8em; }}
.md-toc-h6 .md-toc-inner {{ margin-left: 10em; }}
@media screen and (max-width: 48em) {{
  .md-toc-h3 .md-toc-inner {{ margin-left: 3.5em; }}
  .md-toc-h4 .md-toc-inner {{ margin-left: 5em; }}
  .md-toc-h5 .md-toc-inner {{ margin-left: 6.5em; }}
  .md-toc-h6 .md-toc-inner {{ margin-left: 8em; }}
}}
a.md-toc-inner {{ font-size: inherit; font-style: inherit; font-weight: inherit; line-height: inherit; }}
.footnote-line a:not(.reversefootnote) {{ color: inherit; }}
.md-attr {{ display: none; }}
.md-fn-count::after {{ content: "."; }}
code, pre, samp, tt {{ font-family: var(--monospace); }}
kbd {{ margin: 0px 0.1em; padding: 0.1em 0.6em; font-size: 0.8em; color: rgb(36, 39, 41); background: rgb(255, 255, 255); border: 1px solid rgb(173, 179, 185); border-radius: 3px; box-shadow: rgba(12, 13, 14, 0.2) 0px 1px 0px, rgb(255, 255, 255) 0px 0px 0px 2px inset; white-space: nowrap; vertical-align: middle; }}
.md-comment {{ color: rgb(162, 127, 3); opacity: 0.6; font-family: var(--monospace); }}
code {{ text-align: left; vertical-align: initial; }}
a.md-print-anchor {{ white-space: pre !important; border-width: initial !important; border-style: none !important; border-color: initial !important; display: inline-block !important; position: absolute !important; width: 1px !important; right: 0px !important; outline: 0px !important; background: 0px 0px !important; text-decoration: initial !important; text-shadow: initial !important; }}
.os-windows.monocolor-emoji .md-emoji {{ font-family: "Segoe UI Symbol", sans-serif; }}
.md-diagram-panel > svg {{ max-width: 100%; }}
[lang="flow"] svg, [lang="mermaid"] svg {{ max-width: 100%; height: auto; }}
[lang="mermaid"] .node text {{ font-size: 1rem; }}
table tr th {{ border-bottom: 0px; }}
video {{ max-width: 100%; display: block; margin: 0px auto; }}
iframe {{ max-width: 100%; width: 100%; border: none; }}
.highlight td, .highlight tr {{ border: 0px; }}
mark {{ background: rgb(255, 255, 0); color: rgb(0, 0, 0); }}
.md-html-inline .md-plain, .md-html-inline strong, mark .md-inline-math, mark strong {{ color: inherit; }}
.md-expand mark .md-meta {{ opacity: 0.3 !important; }}
mark .md-meta {{ color: rgb(0, 0, 0); }}
@media print {{
  .typora-export h1, .typora-export h2, .typora-export h3, .typora-export h4, .typora-export h5, .typora-export h6 {{ break-inside: avoid; }}
}}
.md-diagram-panel .messageText {{ stroke: none !important; }}
.md-diagram-panel .start-state {{ fill: var(--node-fill); }}
.md-diagram-panel .edgeLabel rect {{ opacity: 1 !important; }}
.md-fences.md-fences-math {{ font-size: 1em; }}
.md-fences-advanced:not(.md-focus) {{ padding: 0px; white-space: nowrap; border: 0px; }}
.md-fences-advanced:not(.md-focus) {{ background: inherit; }}
.typora-export-show-outline .typora-export-content {{ max-width: 1440px; margin: auto; display: flex; flex-direction: row; }}
.typora-export-sidebar {{ width: 300px; font-size: 0.8rem; margin-top: 80px; margin-right: 18px; }}
.typora-export-show-outline #write {{ --webkit-flex:2; flex: 2 1 0%; }}
.typora-export-sidebar .outline-content {{ position: fixed; top: 0px; max-height: 100%; overflow: hidden auto; padding-bottom: 30px; padding-top: 60px; width: 300px; }}
@media screen and (max-width: 1024px) {{
  .typora-export-sidebar, .typora-export-sidebar .outline-content {{ width: 240px; }}
}}
@media screen and (max-width: 800px) {{
  .typora-export-sidebar {{ display: none; }}
}}
.outline-content li, .outline-content ul {{ margin-left: 0px; margin-right: 0px; padding-left: 0px; padding-right: 0px; list-style: none; }}
.outline-content ul {{ margin-top: 0px; margin-bottom: 0px; }}
.outline-content strong {{ font-weight: 400; }}
.outline-expander {{ width: 1rem; height: 1.42857rem; position: relative; display: table-cell; vertical-align: middle; cursor: pointer; padding-left: 4px; }}
.outline-expander::before {{ content: ""; position: relative; font-family: Ionicons; display: inline-block; font-size: 8px; vertical-align: middle; }}
.outline-item {{ padding-top: 3px; padding-bottom: 3px; cursor: pointer; }}
.outline-expander:hover::before {{ content: ""; }}
.outline-h1 > .outline-item {{ padding-left: 0px; }}
.outline-h2 > .outline-item {{ padding-left: 1em; }}
.outline-h3 > .outline-item {{ padding-left: 2em; }}
.outline-h4 > .outline-item {{ padding-left: 3em; }}
.outline-h5 > .outline-item {{ padding-left: 4em; }}
.outline-h6 > .outline-item {{ padding-left: 5em; }}
.outline-label {{ cursor: pointer; display: table-cell; vertical-align: middle; text-decoration: none; color: inherit; }}
.outline-label:hover {{ text-decoration: underline; }}
.outline-item:hover {{ border-color: rgb(245, 245, 245); background-color: var(--item-hover-bg-color); }}
.outline-item:hover {{ margin-left: -28px; margin-right: -28px; border-left: 28px solid transparent; border-right: 28px solid transparent; }}
.outline-item-single .outline-expander::before, .outline-item-single .outline-expander:hover::before {{ display: none; }}
.outline-item-open > .outline-item > .outline-expander::before {{ content: ""; }}
.outline-children {{ display: none; }}
.info-panel-tab-wrapper {{ display: none; }}
.outline-item-open > .outline-children {{ display: block; }}
.typora-export .outline-item {{ padding-top: 1px; padding-bottom: 1px; }}
.typora-export .outline-item:hover {{ margin-right: -8px; border-right: 8px solid transparent; }}
.typora-export .outline-expander::before {{ content: "+"; font-family: inherit; top: -1px; }}
.typora-export .outline-expander:hover::before, .typora-export .outline-item-open > .outline-item > .outline-expander::before {{ content: "−"; }}
.typora-export-collapse-outline .outline-children {{ display: none; }}
.typora-export-collapse-outline .outline-item-open > .outline-children, .typora-export-no-collapse-outline .outline-children {{ display: block; }}
.typora-export-no-collapse-outline .outline-expander::before {{ content: "" !important; }}
.typora-export-show-outline .outline-item-active > .outline-item .outline-label {{ font-weight: 700; }}
.md-inline-math-container mjx-container {{ zoom: 0.95; }}

{STYLE}
</style><title>{TITLE}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@300;400;500;600;700&display=swap" rel="stylesheet">
</head>
<body class='typora-export os-windows'><div class='typora-export-content'>
<div id='write'  class=''>
<script>
    function setRealVh() {{
        document.documentElement.style.setProperty('--real-vh', window.innerHeight + 'px');
    }}
    window.addEventListener('resize', setRealVh);
    window.addEventListener('orientationchange', setRealVh);
    window.addEventListener('load', setRealVh);
</script>
"""

HTML_STYLE = lambda vertical: f""":root {{
    --primary-color: #0b6bcb;
}}

* {{
    box-sizing: border-box;
}}

html, body, #write {{
    font-family: 'ML Modern Roman', 'Noto Serif JP', 'Noto Serif SC', serif;{chr(10) + '    writing-mode: vertical-rl;' + chr(10) + '    text-orientation: mixed;' + chr(10) + '    overflow-x: auto;' if vertical else ''}
}}
{chr(10) + '#write > * {' + chr(10) + '    width: auto !important;' + chr(10) + '}' + chr(10) if vertical else ''}
h1, h2, h3, h4, h5, h6 {{
    font-family: 'ML Modern Roman', 'Noto Serif JP', 'Noto Serif SC', serif;
}}

h1 {{
    font-size: 1.8rem;
}}

h2 {{
    font-size: 1.6rem;
}}

h3 {{
    font-size: 1.4rem;
}}

h4 {{
    font-size: 1.2rem;
}}

h5 {{
    font-size: 1.0rem;
}}

h6 {{
    font-size: 0.8rem;
}}

html {{
    font-size: 16px;
}}

body, #write {{
    {'' if vertical else 'max-width: 920px;' + chr(10) + '    '}text-align: justify;
    display: block;
    margin: auto;
}}

p {{
    font-size: 1rem;
}}

a {{
    color: var(--primary-color);
}}

div#write {{
    padding: 36px 30px;
}}

/* Stuff */

sup.md-footnote {{
    background-color: transparent;
    color: var(--primary-color);
    padding: 1px;
    margin: 0;
}}

code, .md-fences, .sourceCode {{
    background: #f2f2f2;
}}

.md-fences, pre.sourceCode {{
    font-size: .9em;
    padding: .5rem;
}}

.show-fences-line-number .md-fences {{
    padding-left: .5rem;
}}

blockquote {{
    margin: .8rem .2rem;
    padding: .3rem .5rem;
    color: #6f6f6f;
    border-left: .3rem solid gray;
}}

blockquote .md-end-block {{
    padding: 0;
    margin-bottom: 4px;
}}

mark {{
    background: #f5503d26;
}}

figure {{
    margin: .5rem auto;
    max-width: 100%;
    display: block;
    margin: auto;
}}

figcaption {{
    text-align: center;
    margin: .5rem auto;
}}

img {{
    max-width: 100%;
    display: block;
    margin: auto;
}}

#write table {{
    border-top: 1.2pt solid;
    border-bottom: 1.2pt solid;
}}

#write thead {{
    border-bottom: 0.5pt solid;
}}

div#write {{
    padding: {'18px 36px' if vertical else '36px 30px'};
}}

ruby rt {{
    user-select: none;
}}

/* 
    Print Mode and page breaks.
    WkhtmlToPDF does not work on @print mode
*/

@media (max-width: 210mm) {{
    img {{
        max-height: 8cm;
    }}
    html {{
        font-size: 16px;
    }}
    div[title="pb"], page-break {{
        display: block;
        page-break-after: always;
        break-after: page;
    }}
    nav {{
        font-size: .9rem;
        page-break-after: always;
        page-break-before: always;
    }}
    nav a {{
        color: black;
    }}
    /* Move top-level headings to a new page on the right-hand side: */
    h1, h2 {{
        page-break-before: right;
        break-before: recto;
    }}
    /* Override the previous ruleset for the very first heading: */
    h1:first-of-type, section>h1:first-child {{
        page-break-before: avoid;
        break-before: avoid;
    }}
    /* Headings should not be the last paragraph on a page: */
    h1, h2, h3, h4, h5, h6 {{
        page-break-after: avoid;
    }}
    /* Consecutive headings with deepening level should not be split across pages: */
    h1+h2, h2+h3, h3+h4, h4+h5, h5+h6 {{
        page-break-before: avoid;
    }}
}}

@media print {{
    #write{{
        max-width: 100%;
    }}
    @page {{
        size: A4;
        margin: 20mm 16mm;
    }}
}}

.end-nav{{
    display: flex;
    justify-content: space-between;{chr(10) + '    margin: 16px;' if vertical else ''}
}}
"""

HTML_VERTEND = """
img {
    max-height: 100%;
}

@media screen and (max-width: 768px) {
    html, body {
        height: var(--real-vh);
        width: 100vw;
        overflow-y: hidden;
        margin: 0;
        padding: 0;
    }

    #write {
        min-width: var(--real-vh);
        min-height: 100vw;
        overflow-y: hidden;
        overflow-x: auto;
    }
}
"""

HTML_NAVLINK = """<div class="end-nav">
<style>
a.chapter {{ color: #0b6bcb; text-decoration: none; }}
a.chapter:visited {{ color: #0b6bcb; }}
</style>
<a class="chapter" target="_self" href="{PREV_LINK}">{PREV_TEXT}</a>
<a class="chapter" target="_self" href="{NEXT_LINK}">{NEXT_TEXT}</a>
</div>
"""

HTML_SUFFIX = """</div></div>
</body>
</html>
"""

LABELS = {
    "dengekibunko":       ("電撃文庫", "电击文库"),
    "fantasiabunko":      ("ファンタジア文庫", "富士见 Fantasia 文库"),
    "sneakerbunko":       ("角川スニーカー文庫", "角川 Sneaker 文库"),
    "mfbunkoj":           ("MF文庫J", "MF 文库 J"),
    "famitsubunko":       ("ファミ通文庫", "Fami 通文库"),
    "mwbunko":            ("メディアワークス文庫", "MediaWorks 文库"),
    "dengeki_shinbungei": ("電撃の新文芸", "电击新文艺"),
    "mfbooks":            ("MFブックス", "MF BOOKS"),
    "dragon_novels":      ("ドラゴンノベルス", "Dragon NOVELS"),
    "kadokawabooks":      ("カドカワBOOKS", "角川 BOOKS"),
    "nolabel_kadokawa":   ("KADOKAWA 単行本", "角川单行本"),
    "gagagabunko":        ("ガガガ文庫", "GAGAGA 文库"),
    "lanove_kodansha":    ("講談社ラノベ文庫", "讲谈社轻小说文库"),
    "klanove":            ("Kラノベブックス", "K BOOKS"),
    "ga":                 ("GA文庫", "GA 文库"),
    "ga_novel":           ("GAノベル", "GA NOVELS"),
    "dash_shueisha":      ("ダッシュエックス文庫", "DashX 文库"),
    "overlap":            ("オーバーラップ文庫", "Overlap 文库"),
    "overlap_novels":     ("オーバーラップノベルス", "Overlap NOVELS"),
    "hj":                 ("HJ文庫", "HJ 文库"),
    "hj_novels":          ("HJノベルス", "HJ NOVELS"),
    "gcn_bunko":          ("GCN文庫", "GCN 文库"),
    "gcn":                ("GCノベルズ", "GC NOVELS"),
    "to_bunko":           ("TO文庫", "TO 文库"),
    "to":                 ("TOブックス", "TO BOOKS"),
    "herobunko":          ("ヒーロー文庫", "HERO 文库"),
    "bravenovel":         ("ブレイブ文庫", "Brave 文库"),
    "es":                 ("アース・スターノベル", "Earth Star")
}

BRANDS = {
    "amazon": "Amazon",
    "rakuten": "Rakuten",
    "valuecommerce": "Yahoo",
    "yodobashi": "Yodobashi"
}
