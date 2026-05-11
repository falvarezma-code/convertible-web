#!/usr/bin/env python3
"""
Build blog HTML pages from JSON content files.

Reads:
  templates/blog-base.html   shared article template
  templates/blog-index.html  shared index template
  blog/*.json                one file per post

Writes:
  <slug>.html                one per post, at repo root
  blog.html                  index page listing all posts (sorted newest first)

Usage:
  python3 build-blog.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TEMPLATES = ROOT / "templates"
BLOG_DIR = ROOT / "blog"
SITE_BASE = "https://getconvertible.app"


def load_template(name):
    return (TEMPLATES / name).read_text(encoding="utf-8")


def load_posts():
    posts = []
    for path in sorted(BLOG_DIR.glob("*.json")):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        validate_post(data, path)
        posts.append(data)
    return posts


REQUIRED_FIELDS = [
    "slug", "date", "title", "meta_title", "meta_description",
    "meta_keywords", "category", "breadcrumb_name", "dek", "index_dek",
    "body", "faqs",
]

CATEGORY_ORDER = ["Image", "Video", "Audio", "Document"]


def validate_post(post, path):
    for field in REQUIRED_FIELDS:
        if field not in post:
            sys.exit(f"[error] {path.name}: missing required field '{field}'")
    if not isinstance(post["faqs"], list) or not post["faqs"]:
        sys.exit(f"[error] {path.name}: 'faqs' must be a non-empty list")
    for faq in post["faqs"]:
        if "question" not in faq or "answer" not in faq:
            sys.exit(f"[error] {path.name}: each faq needs 'question' and 'answer'")
    check_no_em_dashes(post, path)


def check_no_em_dashes(post, path):
    for field in ("title", "dek", "index_dek", "body", "meta_title", "meta_description"):
        if "—" in post.get(field, ""):
            sys.exit(f"[error] {path.name}: em dash found in '{field}' (style rule)")
    for faq in post["faqs"]:
        if "—" in faq["question"] or "—" in faq["answer"]:
            sys.exit(f"[error] {path.name}: em dash found in FAQ (style rule)")


def build_breadcrumb_schema(post):
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home",
             "item": SITE_BASE},
            {"@type": "ListItem", "position": 2, "name": "Blog",
             "item": f"{SITE_BASE}/blog.html"},
            {"@type": "ListItem", "position": 3, "name": post["breadcrumb_name"],
             "item": f"{SITE_BASE}/{post['slug']}.html"},
        ],
    }, indent=2)


def build_article_schema(post):
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": post["title"],
        "description": post["meta_description"],
        "datePublished": post["date"],
        "dateModified": post.get("date_modified", post["date"]),
        "author": {"@type": "Organization", "name": "Convertible"},
        "publisher": {
            "@type": "Organization",
            "name": "Convertible",
            "logo": {
                "@type": "ImageObject",
                "url": f"{SITE_BASE}/assets/images/convertible-logo.png",
            },
        },
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": f"{SITE_BASE}/{post['slug']}.html",
        },
        "image": f"{SITE_BASE}/assets/images/og-image.png",
    }, indent=2)


def build_faq_schema(post):
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": faq["question"],
                "acceptedAnswer": {"@type": "Answer", "text": faq["answer"]},
            }
            for faq in post["faqs"]
        ],
    }, indent=2)


def build_faq_section(post):
    parts = []
    for faq in post["faqs"]:
        parts.append(
            f"  <h3>{faq['question']}</h3>\n"
            f"  <p>\n    {faq['answer']}\n  </p>"
        )
    return "\n".join(parts)


def build_video_figure(post):
    video = post.get("video")
    if not video:
        return ""
    return (
        '\n  <figure class="article-video">\n'
        '    <video autoplay muted loop playsinline preload="metadata"\n'
        f'           poster="{video["poster"]}"\n'
        f'           width="{video["width"]}" height="{video["height"]}">\n'
        f'      <source src="{video["src"]}" type="video/mp4" />\n'
        '    </video>\n'
        f'    <figcaption>\n      {video["caption"]}\n    </figcaption>\n'
        '  </figure>\n'
    )


def render_post(post, template):
    replacements = {
        "{{META_TITLE}}": post["meta_title"],
        "{{META_DESCRIPTION}}": post["meta_description"],
        "{{META_KEYWORDS}}": post["meta_keywords"],
        "{{CANONICAL_URL}}": f"{SITE_BASE}/{post['slug']}.html",
        "{{OG_TITLE}}": post.get("og_title", post["meta_title"].split(" | ")[0]),
        "{{OG_DESCRIPTION}}": post.get("og_description", post["meta_description"]),
        "{{TWITTER_TITLE}}": post.get("twitter_title", post.get("og_title", post["meta_title"].split(" | ")[0])),
        "{{TWITTER_DESCRIPTION}}": post.get("twitter_description", post.get("og_description", post["meta_description"])),
        "{{BREADCRUMB_NAME}}": post["breadcrumb_name"],
        "{{TITLE}}": post["title"],
        "{{DEK}}": post["dek"],
        "{{VIDEO_FIGURE}}": build_video_figure(post),
        "{{BODY}}": post["body"],
        "{{FAQ_SECTION}}": build_faq_section(post),
        "{{BREADCRUMB_SCHEMA}}": build_breadcrumb_schema(post),
        "{{ARTICLE_SCHEMA}}": build_article_schema(post),
        "{{FAQ_SCHEMA}}": build_faq_schema(post),
    }
    out = template
    for k, v in replacements.items():
        out = out.replace(k, v)
    return out


def render_index(posts, template):
    by_category = {}
    for post in posts:
        by_category.setdefault(post["category"], []).append(post)
    for cat in by_category:
        if cat not in CATEGORY_ORDER:
            sys.exit(f"[error] unknown category '{cat}' (allowed: {CATEGORY_ORDER})")

    sections = []
    for cat in CATEGORY_ORDER:
        if cat not in by_category:
            continue
        items = []
        for post in sorted(by_category[cat], key=lambda p: p["date"], reverse=True):
            items.append(
                '      <li>\n'
                f'        <a href="/{post["slug"]}.html">\n'
                f'          <div class="post-title">{post["title"]}</div>\n'
                f'          <div class="post-dek">{post["index_dek"]}</div>\n'
                '        </a>\n'
                '      </li>'
            )
        sections.append(
            f'    <h2 class="post-category">{cat}</h2>\n'
            '    <ul class="post-list">\n'
            + "\n".join(items) + "\n"
            '    </ul>'
        )
    return template.replace("{{POST_SECTIONS}}", "\n".join(sections))


def main():
    if not BLOG_DIR.exists():
        sys.exit(f"[error] blog directory not found: {BLOG_DIR}")

    posts = load_posts()
    if not posts:
        sys.exit("[error] no posts found in blog/")

    base_tmpl = load_template("blog-base.html")
    index_tmpl = load_template("blog-index.html")

    for post in posts:
        out_path = ROOT / f"{post['slug']}.html"
        out_path.write_text(render_post(post, base_tmpl), encoding="utf-8")
        print(f"  wrote {out_path.name}")

    posts_for_index = sorted(posts, key=lambda p: p["date"], reverse=True)
    (ROOT / "blog.html").write_text(render_index(posts_for_index, index_tmpl), encoding="utf-8")
    print(f"  wrote blog.html ({len(posts)} posts)")


if __name__ == "__main__":
    main()
