from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).parent.resolve()
POSTS_DIR = ROOT / "posts"
SLUG_RE = re.compile(r"^[a-z0-9-]+$")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a new Markdown post under posts/ using today's date."
    )
    parser.add_argument(
        "-n",
        "--name",
        required=True,
        help="Post slug, using lowercase letters, numbers, and hyphens.",
    )
    return parser


def validate_slug(slug: str) -> str:
    slug = slug.strip()
    if not slug:
        raise ValueError("slug cannot be empty")
    if not SLUG_RE.fullmatch(slug):
        raise ValueError("slug must contain only lowercase letters, numbers, and hyphens")
    return slug


def render_template(today: str, slug: str) -> str:
    title = slug.replace("-", " ").title()
    return f"""---
title: {title}
date: {today}
summary:
draft: true
---

# {title}

在这里开始写作。
"""


def create_post(slug: str) -> Path:
    validated_slug = validate_slug(slug)
    today = date.today().isoformat()
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    path = POSTS_DIR / f"{today}-{validated_slug}.md"
    if path.exists():
        raise FileExistsError(f"post already exists: {path.name}")
    path.write_text(render_template(today, validated_slug), encoding="utf-8")
    return path


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        path = create_post(args.name)
    except (ValueError, FileExistsError) as exc:
        print(f"Create failed: {exc}", file=sys.stderr)
        return 1

    print(f"Created: {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
