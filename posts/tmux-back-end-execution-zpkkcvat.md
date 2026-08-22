---
title: 用 tmux 后台运行训练任务
date: 2026-07-28
summary: 使用 tmux 保持训练任务在 SSH 断开后继续运行，并实时保存和查看训练日志。
draft: false
---

# 使用 tmux 后台运行深度学习训练并实时保存日志

## 需求

训练 PyTorch / TensorFlow 模型时，希望：

* SSH 断开后训练仍继续运行；
* 训练日志实时保存到 `log.txt`；
* 随时查看训练进度；
* 保留历史实验日志。

## 操作步骤

### 1. 创建 tmux 会话

```bash
tmux new -s train
```

进入独立训练环境。

### 2. 启动训练并保存日志

执行：

```bash
python -u train.py 2>&1 | tee -a log.txt
```

说明：

* `python -u`
  * 禁用 Python 输出缓冲；
  * 日志实时写入。
* `2>&1`
  * 合并普通输出和错误信息。
* `tee -a log.txt`
  * 屏幕显示日志；
  * 同时追加保存到 `log.txt`；
  * `-a` 表示不覆盖旧日志。

### 3. 转入后台运行

训练启动后退出 tmux：

```text
Ctrl + B
```

然后：

```text
D
```

即：

```text
Ctrl+B → D
```

训练会继续运行。

### 4. 查看训练进度

实时查看日志：

```bash
tail -f log.txt
```

退出查看：

```text
Ctrl+C
```

不会停止训练。

查看最近 100 行日志：

```bash
tail -n 100 log.txt
```

### 5. 重新进入训练环境

查看现有 tmux 会话：

```bash
tmux ls
```

进入：

```bash
tmux attach -t train
```

### 6. 停止训练

进入 tmux：

```bash
tmux attach -t train
```

停止：

```text
Ctrl+C
```

或直接关闭会话：

```bash
tmux kill-session -t train
```

## 整体流程

```bash
# 创建会话
tmux new -s train

# 启动训练
python -u train.py 2>&1 | tee -a log.txt

# 后台运行
Ctrl+B → D

# 查看日志
tail -f log.txt

# 恢复训练窗口
tmux attach -t train
```

适用于 PyTorch、TensorFlow 等长时间训练任务。
