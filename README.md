# Convertible Web

Landing page and SEO blog for [Convertible](https://convertibleapp.com), a privacy-first macOS file converter. Static HTML deployed on Cloudflare Pages.

## Layout

```
index.html              Landing page
privacy.html            Privacy policy
support.html            Support page
terms.html              Terms of service
blog.html               Auto-generated blog index
<slug>.html             Auto-generated article pages

assets/                 Images and video used across the site
blog/                   Article content (one JSON per post)
templates/              Shells used by the blog build
build-blog.py           Blog generator (Python 3, stdlib only)
```

The root pages (`index.html`, `privacy.html`, etc.) are hand-edited. Blog and article pages are generated and should not be edited directly.

## Blog

Articles live as JSON files in `blog/`. Each file describes one post: title, date, body sections, FAQ entries, and metadata. The build script renders them through `templates/blog-base.html` to produce one HTML file per post at the repo root, and regenerates `blog.html` as an index sorted newest first.

### Add a post

1. Copy an existing file in `blog/` to a new slug.
2. Edit the fields.
3. Run the build:

   ```sh
   python3 build-blog.py
   ```

URL convention:

- Conversion guides: `convert-{from}-to-{to}-mac.html`
- Compression guides: `compress-{format}-mac.html`

All article pages live flat at the repo root, no nested directories.

### Rebuild everything

After a template change, rerun the script. It regenerates every page from `blog/*.json`.

### Structured data

Each article page includes four JSON-LD blocks: `SoftwareApplication`, `BreadcrumbList`, `Article`, `FAQPage`. These are generated from the JSON content. Do not hand-edit them in the output HTML.

### Design

The article design lives in `templates/blog-base.html`. Per-page tweaks belong in the template, not the generated files, so all articles stay consistent.

## Writing style

No em dashes (—) anywhere: copy, comments, commit messages, docs. Use periods, commas, colons, or parentheses instead. The build script enforces this and exits non-zero if it finds an em dash in any content file.

## Deployment

Pushes to `main` deploy automatically via Cloudflare Pages. There is no separate build step beyond `build-blog.py`; commit the generated HTML alongside the JSON change.
