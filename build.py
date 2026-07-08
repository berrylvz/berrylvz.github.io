from __future__ import annotations

import re
import shutil
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

try:
    import markdown
    import yaml
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except ImportError as exc:
    missing = getattr(exc, "name", "dependency")
    raise SystemExit(
        f"Missing dependency: {missing}. Install requirements with "
        f"`pip install -r requirements.txt` before running build.py."
    ) from exc


ROOT = Path(__file__).parent.resolve()
CONFIG_PATH = ROOT / "config.yml"
POSTS_DIR = ROOT / "posts"
TEMPLATES_DIR = ROOT / "templates"
STATIC_DIR = ROOT / "static"
OUTPUT_DIR = ROOT / "public"
OUTPUT_POSTS_DIR = OUTPUT_DIR / "posts"

POST_NAME_RE = re.compile(r"^(?P<date>\d{4}-\d{2}-\d{2})-(?P<slug>[a-z0-9-]+)\.md$")
REQUIRED_TEMPLATES = ("base.html", "index.html", "post.html")
class BuildError(Exception):
    pass


@dataclass
class Post:
    title: str
    date: str
    tags: list[str]
    summary: str
    draft: bool
    content: str
    url: str
    output_path: Path
    source_path: Path


def read_yaml_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise BuildError(f"Required file not found: {path.relative_to(ROOT)}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise BuildError(f"Invalid YAML in {path.relative_to(ROOT)}: {exc}") from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise BuildError(f"{path.relative_to(ROOT)} must contain a mapping at top level")
    return data


def normalize_base_url(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BuildError("`base_url` must be a non-empty string")
    value = value.strip()
    if value == "/":
        return "/"
    return "/" + value.strip("/")


def load_site_config() -> dict[str, Any]:
    config = read_yaml_file(CONFIG_PATH)
    required_fields = {
        "site_title": str,
        "base_url": str,
        "author": str,
        "timezone": str,
    }
    for key, expected_type in required_fields.items():
        value = config.get(key)
        if not isinstance(value, expected_type) or not value.strip():
            raise BuildError(f"`{key}` in config.yml must be a non-empty string")

    site_description = config.get("site_description", "")
    if site_description is None:
        site_description = ""
    if not isinstance(site_description, str):
        raise BuildError("`site_description` in config.yml must be a string when provided")
    config["site_description"] = site_description.strip()

    config["base_url"] = normalize_base_url(config["base_url"])

    navigation = config.get("navigation", [])
    if navigation is None:
        navigation = []
    if not isinstance(navigation, list):
        raise BuildError("`navigation` in config.yml must be a list")

    validated_navigation = []
    for idx, item in enumerate(navigation):
        if not isinstance(item, dict):
            raise BuildError(f"`navigation[{idx}]` must be an object")
        title = item.get("title")
        url = item.get("url")
        if not isinstance(title, str) or not title.strip():
            raise BuildError(f"`navigation[{idx}].title` must be a non-empty string")
        if not isinstance(url, str) or not url.strip():
            raise BuildError(f"`navigation[{idx}].url` must be a non-empty string")
        validated_navigation.append({"title": title.strip(), "url": url.strip()})
    config["navigation"] = validated_navigation
    return config


def ensure_required_inputs() -> None:
    if not POSTS_DIR.is_dir():
        raise BuildError("Required directory not found: posts/")
    if not TEMPLATES_DIR.is_dir():
        raise BuildError("Required directory not found: templates/")
    if not STATIC_DIR.is_dir():
        raise BuildError("Required directory not found: static/")

    missing_templates = [name for name in REQUIRED_TEMPLATES if not (TEMPLATES_DIR / name).is_file()]
    if missing_templates:
        raise BuildError(f"Missing templates: {', '.join(missing_templates)}")


def split_front_matter(text: str, source_name: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        raise BuildError(f"{source_name} is missing front matter")
    parts = text.split("---\n", 2)
    if len(parts) < 3:
        raise BuildError(f"{source_name} has malformed front matter delimiters")
    _, raw_front_matter, body = parts
    try:
        front_matter = yaml.safe_load(raw_front_matter) or {}
    except yaml.YAMLError as exc:
        raise BuildError(f"Invalid front matter YAML in {source_name}: {exc}") from exc
    if not isinstance(front_matter, dict):
        raise BuildError(f"Front matter in {source_name} must be a mapping")
    return front_matter, body.strip()


def validate_tags(tags: Any, source_name: str) -> list[str]:
    if tags is None:
        return []
    if not isinstance(tags, list) or any(not isinstance(tag, str) or not tag.strip() for tag in tags):
        raise BuildError(f"`tags` in {source_name} must be a list of non-empty strings")
    return [tag.strip() for tag in tags]


def validate_date(date_value: Any, source_name: str) -> str:
    if isinstance(date_value, datetime):
        normalized = date_value.strftime("%Y-%m-%d")
    elif isinstance(date_value, date):
        normalized = date_value.isoformat()
    elif isinstance(date_value, str):
        normalized = date_value
    else:
        raise BuildError(f"`date` in {source_name} must use YYYY-MM-DD format")

    try:
        datetime.strptime(normalized, "%Y-%m-%d")
    except ValueError as exc:
        raise BuildError(f"`date` in {source_name} must use YYYY-MM-DD format") from exc
    return normalized


def render_markdown(body: str) -> str:
    return markdown.markdown(
        body,
        extensions=[
            "fenced_code",
            "tables",
            "pymdownx.tilde",
        ],
    )


def load_posts(site_config: dict[str, Any]) -> list[Post]:
    del site_config
    posts: list[Post] = []
    seen_output_paths: set[str] = set()

    for path in sorted(POSTS_DIR.glob("*.md")):
        match = POST_NAME_RE.match(path.name)
        if not match:
            raise BuildError(f"Invalid post filename: {path.name}. Expected YYYY-MM-DD-slug.md")

        text = path.read_text(encoding="utf-8")
        front_matter, body = split_front_matter(text, path.name)

        title = front_matter.get("title")
        if not isinstance(title, str) or not title.strip():
            raise BuildError(f"`title` in {path.name} must be a non-empty string")

        date_value = validate_date(front_matter.get("date"), path.name)
        if date_value != match.group("date"):
            raise BuildError(f"Filename date and front matter date mismatch in {path.name}")

        tags = validate_tags(front_matter.get("tags"), path.name)

        draft = front_matter.get("draft", False)
        if not isinstance(draft, bool):
            raise BuildError(f"`draft` in {path.name} must be a boolean")

        summary = front_matter.get("summary")
        if summary is None:
            summary = ""
        elif not isinstance(summary, str):
            raise BuildError(f"`summary` in {path.name} must be a string")

        source_stem = path.stem
        url = f"/posts/{source_stem}.html"
        output_path = OUTPUT_POSTS_DIR / f"{source_stem}.html"
        output_key = output_path.as_posix()
        if output_key in seen_output_paths:
            raise BuildError(f"Duplicate output path detected: {output_key}")
        seen_output_paths.add(output_key)

        posts.append(
            Post(
                title=title.strip(),
                date=date_value,
                tags=tags,
                summary=summary.strip(),
                draft=draft,
                content=render_markdown(body),
                url=url,
                output_path=output_path,
                source_path=path,
            )
        )

    posts = [post for post in posts if not post.draft]
    posts.sort(key=lambda item: item.date, reverse=True)
    return posts


def clean_output_dir() -> None:
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_POSTS_DIR.mkdir(parents=True, exist_ok=True)


def join_base_url(base_url: str, path: str) -> str:
    normalized = "/" + path.lstrip("/")
    if base_url == "/":
        return normalized
    return f"{base_url}{normalized}"


def build_environment(base_url: str) -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    env.globals["base_url"] = base_url
    env.globals["static_url"] = lambda path: join_base_url(base_url, f"/static/{path.lstrip('/')}")
    env.globals["page_url"] = lambda path: join_base_url(base_url, path)
    return env


def render_index(env: Environment, site: dict[str, Any], posts: list[Post]) -> None:
    template = env.get_template("index.html")
    html = template.render(site=site, base_url=site["base_url"], posts=posts)
    (OUTPUT_DIR / "index.html").write_text(html, encoding="utf-8")


def render_posts(env: Environment, site: dict[str, Any], posts: list[Post]) -> None:
    template = env.get_template("post.html")
    for post in posts:
        html = template.render(site=site, base_url=site["base_url"], post=post)
        post.output_path.write_text(html, encoding="utf-8")


def copy_static() -> None:
    shutil.copytree(STATIC_DIR, OUTPUT_DIR / "static", dirs_exist_ok=True)


def build_site() -> None:
    ensure_required_inputs()
    site = load_site_config()
    clean_output_dir()
    posts = load_posts(site)
    env = build_environment(site["base_url"])
    render_posts(env, site, posts)
    render_index(env, site, posts)
    copy_static()


def main() -> int:
    try:
        build_site()
    except BuildError as exc:
        print(f"Build failed: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover
        print(f"Unexpected build failure: {exc}", file=sys.stderr)
        return 1
    print("Build succeeded: public/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
