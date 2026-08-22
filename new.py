from __future__ import annotations

import argparse
import re
import secrets
import string
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).parent.resolve()
POSTS_DIR = ROOT / "posts"
NAME_RE = re.compile(r"^[a-z0-9-]+$")
RANDOM_SUFFIX_LENGTH = 8
RANDOM_SUFFIX_ALPHABET = string.ascii_lowercase + string.digits


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a new Markdown post under posts/ with a random suffix."
    )
    parser.add_argument(
        "-n",
        "--name",
        required=True,
        help="Post name, using lowercase letters, numbers, and hyphens.",
    )
    return parser


def validate_name(name: str) -> str:
    name = name.strip()
    if not name:
        raise ValueError("name cannot be empty")
    if not NAME_RE.fullmatch(name):
        raise ValueError("name must contain only lowercase letters, numbers, and hyphens")
    return name


def render_template(today: str, name: str) -> str:
    title = name.replace("-", " ").title()
    return f"""---
title: {title}
date: {today}
summary:
draft: true
---

# {title}

在这里开始写作。
"""


def generate_random_suffix() -> str:
    return "".join(
        secrets.choice(RANDOM_SUFFIX_ALPHABET) for _ in range(RANDOM_SUFFIX_LENGTH)
    )


def create_post(name: str) -> Path:
    validated_name = validate_name(name)
    today = date.today().isoformat()
    POSTS_DIR.mkdir(parents=True, exist_ok=True)

    while True:
        path = POSTS_DIR / f"{validated_name}-{generate_random_suffix()}.md"
        if not path.exists():
            break

    path.write_text(render_template(today, validated_name), encoding="utf-8")
    return path


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        path = create_post(args.name)
    except ValueError as exc:
        print(f"Create failed: {exc}", file=sys.stderr)
        return 1

    print(f"Created: {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
