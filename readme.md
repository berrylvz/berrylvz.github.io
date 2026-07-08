# 个人博客系统

一个基于 Markdown、Python、Jinja2 和 GitHub Pages 的轻量级静态博客生成器。

当前版本的特点很明确：

- 首页只展示文章卡片
- 卡片只显示 `title` 和显式填写的 `summary`
- `summary` 为空时，首页不显示摘要
- 文章详情页展示正文内容，不额外显示标题摘要块
- 支持 GitHub Pages 自动部署

## 项目结构

```text
blog/
├── posts/                    # Markdown 文章
├── templates/                # Jinja2 模板
├── static/                   # CSS / JS 等静态资源
├── public/                   # 构建产物，不提交到仓库
├── config.yml                # 站点配置
├── build.py                  # 构建脚本
├── new.py                    # 新建文章脚本
├── requirements.txt          # Python 依赖
├── design.md                 # 设计文档
├── readme.md                 # 使用说明
└── .github/workflows/
    └── deploy.yml            # GitHub Pages 部署配置
```

## 环境准备

要求：

- Python 3.12 或兼容版本
- `uv`

安装依赖：

```bash
uv venv
uv pip install -r requirements.txt
```

## 站点配置

站点配置文件位于 [config.yml](./config.yml)。

当前使用到的字段：

```yaml
site_title: My Blog
base_url: /
author: Alice
timezone: Asia/Shanghai
```

字段说明：

- `site_title`：站点标题
- `base_url`：站点基础路径
- `author`：作者名
- `timezone`：时区

`base_url` 使用规则：

- 部署到 GitHub 用户主页站点时，使用 `/`
- 部署到仓库主页站点时，例如 `https://user.github.io/blog/`，使用 `/blog`

当前仓库是 `berrylvz/berrylvz.github.io`，属于 GitHub 用户主页仓库，因此应使用：

```yaml
base_url: /
```

## 写文章

文章放在 `posts/` 目录下，文件名格式固定为：

```text
YYYY-MM-DD-slug.md
```

例如：

```text
2026-07-08-hello-world.md
```

front matter 示例：

```markdown
---
title: 我的第一篇博客
date: 2026-07-08
summary: 这是一篇用于测试个人博客系统的文章。
draft: false
---

# 我的第一篇博客

这里是正文内容。
```

字段规则：

- `title`：必填，字符串
- `date`：必填，格式为 `YYYY-MM-DD`
- `summary`：可选；仅在首页卡片中显示
- `draft`：可选，布尔值；`true` 时不参与构建

注意：

- `summary` 为空时，首页不会显示摘要
- 系统不会再从正文自动提取摘要
- 文件名中的日期必须与 front matter 中的 `date` 一致
- `slug` 只允许小写字母、数字和连字符

## 新建文章

使用 [new.py](./new.py) 可以快速创建一篇新文章：

```bash
uv run python new.py -n hello-world
```

它会在 `posts/` 下生成当天日期命名的文件，例如：

```text
posts/2026-07-08-hello-world.md
```

生成内容默认包含：

- 自动填充的 `title`
- 当天日期
- 空的 `summary`
- `draft: true`

## 本地构建

执行：

```bash
uv run python build.py
```

构建成功后输出到：

```text
public/
├── index.html
├── posts/
└── static/
```

构建脚本会：

- 读取并校验 `config.yml`
- 校验文章文件名和 front matter
- 过滤草稿文章
- 将 Markdown 转换为 HTML
- 生成首页和文章详情页
- 复制静态资源到 `public/static/`

以下情况会导致构建失败：

- `config.yml` 缺失或格式错误
- 模板缺失
- 文件名不符合规范
- `title` 或 `date` 缺失
- `date`、`draft` 类型错误
- 输出路径冲突

## 本地预览

构建后可直接启动静态文件服务：

```bash
uv run python -m http.server 8000 --directory public
```

浏览器访问：

```text
http://localhost:8000
```

## 页面行为

首页行为：

- 只显示文章卡片列表
- 每张卡片整张都可点击
- 卡片只显示 `title` 和显式 `summary`

文章页行为：

- 显示正文内容
- 显示发布日期
- 不显示 tags
- 不显示额外的标题摘要块

模板入口：

- [templates/base.html](./templates/base.html)
- [templates/index.html](./templates/index.html)
- [templates/post.html](./templates/post.html)

样式入口：

- [static/css/style.css](./static/css/style.css)

## 部署到 GitHub Pages

部署配置位于 [.github/workflows/deploy.yml](./.github/workflows/deploy.yml)。

默认行为：

- push 到 `main` 分支时触发
- 安装 Python 3.12
- 安装依赖
- 执行 `python build.py`
- 上传 `public/`
- 发布到 GitHub Pages

使用前请确认：

1. 仓库已推送到 GitHub
2. GitHub Pages 已启用
3. 默认分支为 `main`
4. `config.yml` 里的 `base_url` 配置正确

访问地址说明：

- 博客站点地址：`https://berrylvz.github.io/`
- GitHub 仓库地址：`https://github.com/berrylvz/berrylvz.github.io`

如果你打开的是 GitHub 仓库地址，看到的是仓库页面和 `readme.md`，不是博客站点本身。

## 常见修改入口

- 修改站点标题：编辑 [config.yml](./config.yml)
- 新建文章：运行 [new.py](./new.py)
- 修改首页结构：编辑 [templates/index.html](./templates/index.html)
- 修改文章页结构：编辑 [templates/post.html](./templates/post.html)
- 修改全局布局：编辑 [templates/base.html](./templates/base.html)
- 修改样式：编辑 [static/css/style.css](./static/css/style.css)
- 修改构建逻辑：编辑 [build.py](./build.py)

## 当前未实现

当前还没有实现这些能力：

- 标签页
- 归档页
- RSS
- sitemap
- 评论系统
- 全文搜索

更完整的规划见 [design.md](./design.md)。
