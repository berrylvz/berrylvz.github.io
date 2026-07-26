---
title: Markdown Syntax
date: 2026-07-08
summary: An Examle of Markdown Syntax
draft: false
---

# Markdown Syntax

Markdown Syntax

## 小节标题

- 支持 Markdown 正文
- 支持 front matter
- 支持生成文章详情页

### 有序列表

1. 初始化站点配置
2. 编写 Markdown 文章
3. 执行构建脚本
4. 发布到 GitHub Pages

### 引用

> Markdown 适合写技术博客，因为它足够简单，也足够通用。

### 强调与行内代码

你可以使用 **粗体**、*斜体*、~~删除线~~，也可以插入行内代码，例如 `uv run python build.py`。

### 链接

- 项目主页可以放在 [GitHub](https://github.com/)
- 也可以链接到站内页面，例如 [返回首页](/)

### 表格

| 功能 | 当前状态 | 说明 |
| ---- | ---- | ---- |
| 首页生成 | 已实现 | 生成文章列表页 |
| 文章详情页 | 已实现 | 渲染单篇文章内容 |
| 标签页 | 未实现 | 预留后续扩展 |
| RSS | 未实现 | 预留后续扩展 |

### 分隔线

---

### 代码块

```python
print("hello blog")
```

```bash
uv venv
uv pip install -r requirements.txt
uv run python build.py
```

### 公式

行内公式示例：$E = mc^2$

块级公式示例：

$$
\sum_{i=1}^{n} i = \frac{n(n+1)}{2}
$$

### 任务列表

- [x] 完成基础目录结构
- [x] 支持 Markdown 转 HTML
- [ ] 支持标签归档页
- [ ] 支持 RSS 输出
