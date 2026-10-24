#!/usr/bin/env python3
"""Build 明律知境 static site from Markdown topics (法考 2027 备考)."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content" / "topics"
SRC = ROOT / "src"
DIST = ROOT / "dist"

try:
    import markdown as md_lib
except ImportError:
    md_lib = None


def ensure_markdown():
    global md_lib
    if md_lib is not None:
        return
    import subprocess
    import sys

    subprocess.check_call([sys.executable, "-m", "pip", "install", "markdown", "-q"])
    import markdown as md_lib  # noqa: F401


def escape_html(s: str) -> str:
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def parse_front_matter(raw: str) -> tuple[dict, str]:
    if not raw.startswith("---"):
        return {}, raw
    end = raw.find("\n---", 3)
    if end == -1:
        return {}, raw
    yaml = raw[3:end].strip()
    body = raw[end + 4 :].lstrip()
    meta: dict = {}
    for line in yaml.splitlines():
        m = re.match(r"^(\w+):\s*(.*)$", line)
        if not m:
            continue
        key, value = m.group(1), m.group(2).strip()
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1]
            meta[key] = [
                p.strip().strip("\"'")
                for p in inner.split(",")
                if p.strip()
            ]
        else:
            meta[key] = value.strip("\"'")
    return meta, body


def plain_text(md: str) -> str:
    text = re.sub(r"```[\s\S]*?```", " ", md)
    text = re.sub(r"`[^`]+`", " ", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", text)
    text = re.sub(r"\[[^\]]*\]\([^)]+\)", " ", text)
    text = re.sub(r"[#>*_\-|]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


_MATH_DISPLAY = re.compile(r"\\\[((?:.|\n)*?)\\\]")
_MATH_INLINE = re.compile(r"\\\(((?:.|\n)*?)\\\)")
_MATH_DOLLAR = re.compile(r"\$\$((?:.|\n)*?)\$\$")


def _extract_math(body: str) -> tuple[str, list[tuple[str, str]]]:
    slots: list[tuple[str, str]] = []

    def park(kind: str, tex: str) -> str:
        slots.append((kind, tex))
        return f"@@MATH{len(slots) - 1}@@"

    def park_display(m: re.Match) -> str:
        return park("display", m.group(1))

    def park_inline(m: re.Match) -> str:
        return park("inline", m.group(1))

    body = _MATH_DOLLAR.sub(park_display, body)
    body = _MATH_DISPLAY.sub(park_display, body)
    body = _MATH_INLINE.sub(park_inline, body)
    return body, slots


def _restore_math(html: str, slots: list[tuple[str, str]]) -> str:
    for i, (kind, tex) in enumerate(slots):
        token = f"@@MATH{i}@@"
        if kind == "display":
            repl = f"\\[{tex}\\]"
        else:
            repl = f"\\({tex}\\)"
        html = html.replace(token, repl)
        html = html.replace(f"<p>\\[{tex}\\]</p>", f"\\[{tex}\\]")
        html = html.replace(f"<p>\\[{tex}\\]<br />\n</p>", f"\\[{tex}\\]")
    return html


def render_md(body: str) -> str:
    ensure_markdown()
    body, math_slots = _extract_math(body)
    html = md_lib.markdown(body, extensions=["tables", "fenced_code", "nl2br"])
    html = _restore_math(html, math_slots)
    html = html.replace("../../src/assets/", "../assets/")
    html = html.replace("../src/assets/", "../assets/")
    return html


def render_tags(tags: list[str]) -> str:
    return "".join(f'<span class="tag">{escape_html(t)}</span>' for t in tags)


def topic_card(topic: dict, href_prefix: str = "topics/") -> str:
    if topic["cover"]:
        cover = (
            f'<div class="card-cover" style="background-image:url(\'{escape_html(topic["cover"])}\')"></div>'
        )
    else:
        cover = '<div class="card-cover card-cover--fallback"></div>'
    slug = sanitize_slug(topic["slug"])
    return f"""
    <a class="topic-card" href="{href_prefix}{escape_html(slug)}.html" data-title="{escape_html(topic['title'])}" data-tags="{escape_html(' '.join(topic['tags']))}" data-summary="{escape_html(topic['summary'])}">
      {cover}
      <div class="card-body">
        <div class="card-meta">
          <time datetime="{escape_html(topic['date'])}">{escape_html(topic['date'])}</time>
          <div class="tags">{render_tags(topic['tags'])}</div>
        </div>
        <h3>{escape_html(topic['title'])}</h3>
        <p>{escape_html(topic['summary'])}</p>
      </div>
    </a>"""


def sanitize_slug(slug: str) -> str:
    slug = slug.strip().replace(" ", "-")
    slug = re.sub(r"[^\w\-.\u4e00-\u9fff]+", "-", slug)
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug or "topic"


# 法考八科系统精讲路线图（按建议学习顺序）
LAW_ROADMAP_ORDER = [
    "minfa",        # 民法
    "xingfa",       # 刑法
    "minsusong",    # 民诉
    "xingsusong",   # 刑诉
    "xingzhengfa",  # 行政法
    "shangjing",    # 商经
    "lilunfa",      # 理论法
    "sanguofa",     # 三国法
]


ROADMAP_FLOATS = [
    {
        "id": "law",
        "title": "法考八科系统精讲路线图",
        "aria": "法考八科系统精讲路线图",
        "hint": "按序精讲：民法 → 刑法 → 民诉 → 刑诉 → 行政法 → 商经 → 理论法 → 三国法",
        "order": LAW_ROADMAP_ORDER,
        "variant": "law",
    },
]


def roadmap_items(order: list[str], topics: list[dict]) -> str:
    by_slug = {t["slug"]: t for t in topics}
    rows = []
    n = 0
    for slug in order:
        topic = by_slug.get(slug)
        if not topic:
            continue
        n += 1
        title = topic["title"]
        short = re.split(r"[:：]", title, maxsplit=1)[0].strip()
        rows.append(
            f'<a class="roadmap-item" href="topics/{escape_html(slug)}.html" '
            f'data-slug="{escape_html(slug)}" '
            f'data-title="{escape_html(title)}" title="{escape_html(title)}">'
            f'<input type="checkbox" class="roadmap-check" '
            f'aria-label="标记「{escape_html(short)}」为已学完" />'
            f'<span class="roadmap-index">{n:02d}</span>'
            f'<span class="roadmap-label">{escape_html(short)}</span>'
            f"</a>"
        )
    return "\n".join(rows)


def roadmap_float(topics: list[dict], href_prefix: str = "topics/", cfg: dict | None = None) -> str:
    cfg = cfg or ROADMAP_FLOATS[0]
    slug_id = cfg["id"]
    items = roadmap_items(cfg["order"], topics).replace(
        'href="topics/', f'href="{href_prefix}'
    )
    count = sum(1 for s in cfg["order"] if any(t["slug"] == s for t in topics))
    variant_cls = f' roadmap-float--{cfg["variant"]}' if cfg.get("variant") else ""
    return f"""
    <div class="roadmap-float{variant_cls}" id="roadmap-float-{slug_id}">
      <button
        type="button"
        class="roadmap-toggle"
        id="roadmap-toggle-{slug_id}"
        aria-expanded="false"
        aria-controls="roadmap-panel-{slug_id}"
      >
        <span class="roadmap-toggle-dot" aria-hidden="true"></span>
        <span class="roadmap-toggle-text">{escape_html(cfg["title"])}</span>
        <span class="roadmap-toggle-count" data-count-total="{count}">0/{count}</span>
        <span class="roadmap-chevron" aria-hidden="true"></span>
      </button>
      <div class="roadmap-progress" aria-hidden="true">
        <div class="roadmap-progress-bar"></div>
      </div>
      <div class="roadmap-panel" id="roadmap-panel-{slug_id}" role="menu" aria-label="{escape_html(cfg["aria"])}">
        <p class="roadmap-hint">{escape_html(cfg["hint"])}</p>
        <div class="roadmap-list">
          {items}
        </div>
      </div>
    </div>"""


def roadmap_floats(topics: list[dict], href_prefix: str = "topics/") -> str:
    return "\n".join(
        roadmap_float(topics, href_prefix=href_prefix, cfg=cfg) for cfg in ROADMAP_FLOATS
    )


# 子专题在父页内的展示顺序（按建议学习脉络），未在表内的排在末尾
SUBORDER: dict[str, list[str]] = {
    "minfa": ["minfa-zongze", "minfa-wuquan-bian", "minfa-danbao", "minfa-wuquan-qita",
              "minfa-hetong", "minfa-renggequan", "minfa-hunyin-jicheng", "minfa-qinquan"],
    "xingfa": ["xingfa-zongze", "xingfa-renshen", "xingfa-caichan", "xingfa-tanwu",
               "xingfa-gonggong", "xingfa-jingji-zuzhi", "xingfa-duzhi"],
    "minsusong": ["minsusong-guanxia", "minsusong-dangshiren", "minsusong-zhengju",
                  "minsusong-chengxu", "minsusong-zhixing", "minsusong-zhongcai"],
    "xingsusong": ["xingsusong-yuanze", "xingsusong-bianhu", "xingsusong-zhengju",
                   "xingsusong-qiangzhi", "xingsusong-chengxu", "xingsusong-zhixing"],
    "xingzhengfa": ["xingzhengfa-zonglun", "xingzhengfa-xingwei", "xingzhengfa-xinxi",
                    "xingzhengfa-fuyi", "xingzhengfa-susong", "xingzhengfa-peichang"],
    "shangjing": ["shangjing-gongsi", "shangjing-hehuo-pochan", "shangjing-zhengquan",
                  "shangjing-jingji", "shangjing-laodong", "shangjing-huanjing"],
    "lilunfa": ["lilunfa-fazhisi", "lilunfa-falixue", "lilunfa-xianfa", "lilunfa-sifa"],
    "sanguofa": ["sanguofa-gongfa", "sanguofa-sifa", "sanguofa-jingjifa"],
}


def subtopics_section(topic: dict, all_topics: list[dict]) -> str:
    children = [t for t in all_topics if t.get("parent") == topic["slug"]]
    if not children:
        return ""
    order = SUBORDER.get(topic["slug"], [])
    children.sort(key=lambda t: order.index(t["slug"]) if t["slug"] in order else 999)
    cards = "".join(topic_card(c, href_prefix="") for c in children)
    return (
        '<section class="subtopics"><div class="subtopics-head">'
        f'<h2>本章子专题</h2><span class="subtopics-count">{len(children)} 篇</span>'
        '</div><div class="related-grid">'
        f"{cards}"
        "</div></section>"
    )


def load_topics() -> list[dict]:
    if not CONTENT.exists():
        return []
    topics = []
    for path in CONTENT.glob("*.md"):
        raw = path.read_text(encoding="utf-8")
        meta, body = parse_front_matter(raw)
        slug = sanitize_slug(meta.get("slug") or path.stem)
        tags = meta.get("tags") or []
        if isinstance(tags, str):
            tags = [tags]
        text = plain_text(body)
        summary = meta.get("summary") or text[:120]
        topics.append(
            {
                "slug": slug,
                "title": meta.get("title") or slug,
                "date": meta.get("date") or "",
                "tags": tags,
                "summary": summary,
                "cover": meta.get("cover") or "",
                "parent": meta.get("parent") or "",
                "body": body,
                "html": render_md(body),
                "text": text,
            }
        )
    topics.sort(key=lambda t: t["date"], reverse=True)
    return topics


def copy_assets():
    src_assets = SRC / "assets"
    dest_assets = DIST / "assets"
    if dest_assets.exists():
        shutil.rmtree(dest_assets)
    shutil.copytree(src_assets, dest_assets)


def build() -> None:
    DIST.mkdir(parents=True, exist_ok=True)
    (DIST / "topics").mkdir(parents=True, exist_ok=True)
    copy_assets()

    topics = load_topics()
    index_tpl = (SRC / "index.html").read_text(encoding="utf-8")
    topic_tpl = (SRC / "topic.html").read_text(encoding="utf-8")

    cards = "\n".join(topic_card(t) for t in topics) or (
        '<p class="empty">暂无专题，在 <code>content/topics/</code> 添加 Markdown 即可。</p>'
    )
    index_html = (
        index_tpl.replace("{{TOPIC_COUNT}}", str(len(topics)))
        .replace("{{TOPIC_CARDS}}", cards)
        .replace("{{LAW_ROADMAP_FLOAT}}", roadmap_floats(topics, href_prefix="topics/"))
    )
    (DIST / "index.html").write_text(index_html, encoding="utf-8")

    for topic in topics:
        related = [
            t
            for t in topics
            if t["slug"] != topic["slug"]
            and set(t["tags"]).intersection(topic["tags"])
        ][:3]
        related_html = ""
        if related:
            related_html = (
                '<section class="related"><h2>相关专题</h2>'
                f'<div class="related-grid">{"".join(topic_card(t, href_prefix="") for t in related)}</div>'
                "</section>"
            )

        subtopics_html = subtopics_section(topic, topics)

        cover_block = (
            f'<div class="topic-hero-media" style="background-image:url(\'{escape_html(topic["cover"])}\')"></div>'
            if topic["cover"]
            else '<div class="topic-hero-media topic-hero-media--fallback"></div>'
        )

        html = topic_tpl
        replacements = {
            "{{TITLE}}": escape_html(topic["title"]),
            "{{DATE}}": escape_html(topic["date"]),
            "{{TAGS}}": render_tags(topic["tags"]),
            "{{SUMMARY}}": escape_html(topic["summary"]),
            "{{COVER}}": escape_html(topic["cover"]),
            "{{COVER_BLOCK}}": cover_block,
            "{{CONTENT}}": topic["html"],
            "{{RELATED}}": related_html,
            "{{SUBTOPICS}}": subtopics_html,
            "{{LAW_ROADMAP_FLOAT}}": roadmap_floats(topics, href_prefix="../topics/"),
        }
        for k, v in replacements.items():
            html = html.replace(k, v)
        (DIST / "topics" / f"{topic['slug']}.html").write_text(html, encoding="utf-8")

    search_index = [
        {
            "slug": t["slug"],
            "title": t["title"],
            "date": t["date"],
            "tags": t["tags"],
            "summary": t["summary"],
            "text": t["text"][:4000],
            "url": f"topics/{t['slug']}.html",
        }
        for t in topics
    ]
    (DIST / "search-index.json").write_text(
        json.dumps(search_index, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Built {len(topics)} topics → dist/")


if __name__ == "__main__":
    build()
