#!/usr/bin/env python3
"""把指定 Markdown 文档渲染为自包含 HTML（内联 CSS，file:// 与 GitHub Pages 均可打开）。

用法：
    python3 scripts/build_md_html.py [md 路径 ...]
不传参数时转换下方 TARGETS 清单。
图片沿用 md 中的相对路径（与 html 同目录），不内联、不转外链。
"""
import sys
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent

# 默认转换清单（相对仓库根目录）
TARGETS = [
    "reports/2026-11-18/岗位技能分析报告.md",
    "reports/2026-11-15/岗位技能分析报告.md",
    "curriculum/ai_agent_transition_roadmap.md",
]

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
:root{
  --bg:#F5F6F8; --card:#FFFFFF; --line:#E6E8EC; --line-soft:#EEF0F3;
  --ink:#1A1D23; --ink-2:#5B616B; --ink-3:#8A9099;
  --accent:#2563A8; --accent-soft:#E8F0F9; --amber-soft:#FBF1E4;
  --code-bg:#F2F4F7; --radius:12px;
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei","Segoe UI",sans-serif;line-height:1.7;font-size:15px}
.wrap{max-width:880px;margin:0 auto;padding:32px 22px 72px}
.doc{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:34px 36px;box-shadow:0 1px 2px rgba(20,24,32,.06),0 4px 14px rgba(20,24,32,.05)}
.doc h1{font-size:25px;font-weight:700;letter-spacing:.2px;margin-bottom:18px;padding-bottom:14px;border-bottom:1px solid var(--line)}
.doc h2{font-size:19px;font-weight:600;margin:30px 0 14px;padding-top:6px}
.doc h3{font-size:16px;font-weight:600;margin:22px 0 10px;color:var(--ink)}
.doc p{margin:10px 0;color:var(--ink)}
.doc ul,.doc ol{margin:10px 0;padding-left:22px}
.doc li{margin:6px 0}
.doc strong{font-weight:600}
.doc a{color:var(--accent);text-decoration:none}
.doc a:hover{text-decoration:underline}
.doc blockquote{margin:14px 0;padding:12px 16px;background:var(--amber-soft);border-left:3px solid var(--amber-soft);border-radius:0 10px 10px 0;color:var(--ink-2);font-size:14px}
.doc blockquote p{margin:4px 0}
.doc code{font-family:"SF Mono",Menlo,Consolas,"Roboto Mono",monospace;font-size:13px;background:var(--code-bg);border-radius:5px;padding:1.5px 6px}
.doc pre{background:var(--code-bg);border:1px solid var(--line-soft);border-radius:10px;padding:14px 16px;overflow-x:auto;margin:14px 0}
.doc pre code{background:transparent;padding:0;font-size:13px;line-height:1.6}
.doc table{width:100%;min-width:560px;border-collapse:collapse;font-size:14px;margin:16px 0;display:block;overflow-x:auto}
.doc th,.doc td{padding:9px 12px;text-align:left;border-top:1px solid var(--line-soft);vertical-align:middle;white-space:nowrap}
.doc th{color:var(--ink-2);font-weight:600;font-size:12.5px;background:#FAFBFC;white-space:nowrap}
.doc td:first-child,.doc th:first-child{white-space:normal}
.doc img{max-width:100%;height:auto;border:1px solid var(--line-soft);border-radius:10px;margin:12px 0}
.doc hr{border:none;border-top:1px solid var(--line);margin:26px 0}
.back{display:inline-flex;align-items:center;gap:6px;margin-bottom:18px;color:var(--ink-2);font-size:13px;text-decoration:none}
.back:hover{color:var(--accent)}
footer{margin-top:26px;color:var(--ink-3);font-size:12.5px;line-height:1.7}
@media(max-width:640px){
  .wrap{padding:18px 14px 48px}
  .doc{padding:22px 18px}
  .doc h1{font-size:21px}
}
</style>
</head>
<body>
<div class="wrap">
  <a class="back" href="__BACK__">← 返回看板 / 首页</a>
  <article class="doc">
__BODY__
  </article>
  <footer>本页由 scripts/build_md_html.py 从同名 Markdown 渲染；修改原始 .md 后重跑脚本即可刷新。</footer>
</div>
</body>
</html>
"""


def render(md_path: Path) -> Path:
    text = md_path.read_text(encoding="utf-8")
    body = markdown.markdown(
        text,
        extensions=["tables", "fenced_code", "sane_lists"],
        output_format="html5",
    )
    # 取首个 h1 作为标题，缺省用文件名
    title = md_path.stem
    for line in text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break

    # 返回首页相对路径：按 md 所在目录层级回退到仓库根
    depth = len(md_path.relative_to(ROOT).parent.parts)
    back = "../" * depth if depth > 0 else "index.html"
    back = back + "index.html" if depth > 0 else back

    html = TEMPLATE.replace("__TITLE__", title).replace("__BACK__", back).replace("__BODY__", body)
    out = md_path.with_suffix(".html")
    out.write_text(html, encoding="utf-8")
    return out


def main():
    args = sys.argv[1:]
    rels = args or TARGETS
    for rel in rels:
        md_path = (ROOT / rel).resolve()
        if not md_path.exists():
            print(f"跳过（不存在）：{rel}")
            continue
        out = render(md_path)
        print(f"渲染 -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
