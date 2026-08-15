---
title: Docker Container Template
date: 2026-08-15
summary: Docker 开发镜像 模板
draft: false
---

# Docker Container Template

在服务器等场景中进行开发，每次都要从一个非常基本的 docker 镜像开始开发，包括安装各种 package，package 管理工具等，这非常耗时，因此这里将各种必要的预备操作整理成一个 docker 镜像，后续可直接在这个镜像生成的容器上进行开发。

## Dockerfile Template

```dockerfile
FROM nvidia/cuda:12.8.1-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive

# uv 相关环境变量，root 用户使用 /root 目录
ENV UV_LINK_MODE=copy
ENV UV_CACHE_DIR=/root/.cache/uv
ENV PATH="/root/.local/bin:/usr/local/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    wget \
    vim \
    curl \
    ca-certificates \
    iputils-ping \
    openssh-client \
    build-essential \
    lsb-release \
    cmake \
    zip \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    ffmpeg \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv：从官方 uv 镜像复制二进制文件，避免 curl | sh
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /workspace

# 可选：预安装一个 Python 版本，避免第一次 uv run 时再下载
RUN uv python install 3.12

CMD ["/bin/bash"]
```

## build

```shell
docker build -t dev-env:128 .
```

## run with gpus

```shell
docker run -it --gpus all --name dev-env -v ./workspace:/workspace dev-env:128
```

## train with multi-gpus

```shell
docker run -it --gpus all --name dev-env --shm-size=16g -v ./workspace:/workspace dev-env:128
```
