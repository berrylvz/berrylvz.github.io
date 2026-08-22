---
title: 使用 rsync 部署开发项目
date: 2026-07-26
summary: 使用过滤规则和 dry-run，将本地项目安全地增量同步到远程服务器。
draft: false
---

# 使用 rsync 部署开发项目

`rsync` 只传输发生变化的文件，适合将本地代码频繁同步到远程开发服务器。下面通过过滤规则和部署脚本，实现预览、确认和正式同步。

## 解决的问题

在远程开发或测试时，手动上传代码通常会遇到这些问题：

- 使用 `scp` 重复上传整个项目，速度慢、浪费带宽；
- 容易把 `.git`、虚拟环境和缓存等无关文件一起上传；
- 本地已经删除的文件仍残留在服务器，导致新旧代码混用；
- 直接使用 `--delete` 存在误删远程数据的风险；
- 每次手写同步命令，容易填错源目录或目标目录。

本文的方案通过增量传输、统一过滤规则、删除保护和执行前预览，让日常同步更快，也更不容易出错。它适合个人项目的远程开发、测试环境更新，以及不需要复杂 CI/CD 流程的小型部署。

## 配置过滤规则

在项目根目录创建 `.rsync-filter`：

```text
# 不上传
- /.git/***
- /.venv/***
- /outputs/***
- **/__pycache__/***
- **/*.pyc

# 保护远程目录，避免被删除
P /.venv/***
P /outputs/***
```

其中，`-` 表示不上传匹配的文件，`P` 表示保护远程已有内容。项目如果还会在远程生成日志、数据库或上传文件，也应将对应目录加入过滤规则。

## 创建部署脚本

在项目根目录创建 `deploy.sh`：

```bash
#!/usr/bin/env bash

set -euo pipefail

# 修改为实际的服务器和项目目录
REMOTE_HOST="${REMOTE_HOST:-server}"
REMOTE_DIR="${REMOTE_DIR:-/home/deploy/workspace/my-project}"

# 始终以脚本所在目录作为项目根目录
PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
RSYNC_FILTER="${PROJECT_ROOT}/.rsync-filter"

if [[ ! -f "${RSYNC_FILTER}" ]]; then
    echo "错误：未找到 ${RSYNC_FILTER}" >&2
    exit 1
fi

RSYNC_OPTIONS=(
    --archive
    --verbose
    --compress
    --delete-delay
    --itemize-changes
    --filter="merge ${RSYNC_FILTER}"
)

echo "本地目录：${PROJECT_ROOT}/"
echo "远程目录：${REMOTE_HOST}:${REMOTE_DIR}/"
echo "开始预览同步……"

rsync \
    "${RSYNC_OPTIONS[@]}" \
    --dry-run \
    "${PROJECT_ROOT}/" \
    "${REMOTE_HOST}:${REMOTE_DIR}/"

echo
read -r -p "确认执行正式部署？[y/N] " CONFIRM

if [[ "${CONFIRM}" != "y" && "${CONFIRM}" != "Y" ]]; then
    echo "已取消部署。"
    exit 0
fi

rsync \
    "${RSYNC_OPTIONS[@]}" \
    "${PROJECT_ROOT}/" \
    "${REMOTE_HOST}:${REMOTE_DIR}/"

echo "部署完成。"
```

脚本会先使用 `--dry-run` 预览变更，确认后才正式同步。`--delete-delay` 会删除远程存在但本地已经移除的文件，因此确认前需要留意预览结果中的 `*deleting`。

源目录末尾的 `/` 也不能省略，它表示同步项目目录中的内容，而不是在远程再创建一层同名目录。

## 执行部署

为脚本添加执行权限并运行：

```bash
chmod +x ./deploy.sh
./deploy.sh
```

也可以临时指定其他环境：

```bash
REMOTE_HOST=staging \
REMOTE_DIR=/srv/my-project \
./deploy.sh
```

## Docker 项目注意事项

如果应用运行在 Docker 容器中，`REMOTE_DIR` 应指向宿主机目录，再通过 volume 挂载到容器。不要直接同步到容器内部，否则容器重建后文件会丢失，也更容易遇到权限问题。

虚拟环境、运行产物和其他持久化数据最好与代码分开存放，并确保部署用户对目标目录具有写权限。
