---
title: Get Started With Pi05 Quickly
date: 2026-08-21
summary: 快速上手pi05, 包括数据采集、配置、微调、部署
draft: false
---

# Get Started With Pi05 Quickly

## 整体流程

```text
采集 LeRobot 数据集
↓
检查 LeRobot 数据集
↓
确定 state/action、夹爪和语言指令语义
↓
实现机器人输入输出 Policy Transform
↓
增加 DataConfig 和 TrainConfig
↓
加载或计算归一化统计
↓
验证完整数据 Pipeline
↓
加载 pi05_base 微调
↓
评估并选择 Checkpoint
↓
启动 Policy Server
↓
机器人端按训练频率执行 Action Chunk
```

## Collect Data

预先准备lerobot 2.1格式的数据集

## Fine-tune pi0.5

### 步骤 1：准备运行环境

参考[openpi](https://github.com/Physical-Intelligence/openpi)

如果使用 Weights & Biases：
```bash
uv run wandb login
```

如果不使用，需要在训练配置中设置[步骤 7：在 config.py 中增加 TrainConfig](#步骤%207：在%20config.py%20中增加%20TrainConfig)：
```python
wandb_enabled=False
```

可以通过以下变量修改 openpi 模型和资产的缓存目录：
```bash
export OPENPI_DATA_HOME=/data/openpi_cache
```

### 步骤 2：放置并加载 LeRobot 数据集

当前仓库固定的 LeRobot commit 为：
```text
0cf864870cf29f4738d3ade893e6fd13fbd7cdb5
```
该版本使用 LeRobot v2.1 格式，默认从下面的位置查找本地数据：
```text
$HF_LEROBOT_HOME/<repo_id>
```

例如，本地数据目录是：
```text
/data/lerobot/user_id/task_name
```
则设置：
```bash
export HF_LEROBOT_HOME=/data/lerobot
```
并在训练配置中写：
```python
repo_id="user_id/task_name"
```

如果数据位于 Hugging Face Hub，直接使用 Hub repo ID。私有数据集需要先登录：
```bash
uv run huggingface-cli login
```

### 步骤 3：校验数据结构和基础质量

训练前至少检查以下内容：
- FPS 是否正确；
- episode、frame 和 task 数量；
- 图像、state 和 action 字段名；
- state/action 维度、顺序和单位；
- 图像 shape、dtype 和通道顺序；
- 是否存在 NaN 或 Inf；
- 每个 episode 是否有正确语言任务；
- 图像、状态和动作是否在同一时间戳对齐。

可以使用以下命令：
```bash
uv run python - <<'PY'
import numpy as np
from lerobot.common.datasets.lerobot_dataset import (
	LeRobotDataset,
	LeRobotDatasetMetadata,
)

repo_id = "user_id/task_name"

meta = LeRobotDatasetMetadata(repo_id)
dataset = LeRobotDataset(repo_id)
sample = dataset[0]

print("fps:", meta.fps)
print("frames:", len(dataset))
print("episodes:", meta.total_episodes)
print("tasks:", meta.tasks)
print("features:")
for key, value in meta.info["features"].items():
	print(" ", key, value)

print("\nfirst sample:")
for key, value in sample.items():
	if hasattr(value, "shape"):
		array = np.asarray(value)
		print(
			key,
			array.shape,
			array.dtype,
			"finite:",
			np.isfinite(array).all(),
			)
	else:
		print(key, value)
PY
```

校验结果例如：
```text
fps: 30
frames: 9188
episodes: 20
tasks: {0: 'teleop'}
features:
  observation.state {'dtype': 'float32', 'shape': (14,), 'names': ['left_shoulder_pan', 'left_shoulder_lift', 'left_elbow', 'left_wrist_1', 'left_wrist_2', 'left_wrist_3', 'left_gripper', 'right_shoulder_pan', 'right_shoulder_lift', 'right_elbow', 'right_wrist_1', 'right_wrist_2', 'right_wrist_3', 'right_gripper']}
  action {'dtype': 'float32', 'shape': (14,), 'names': ['left_shoulder_pan', 'left_shoulder_lift', 'left_elbow', 'left_wrist_1', 'left_wrist_2', 'left_wrist_3', 'left_gripper', 'right_shoulder_pan', 'right_shoulder_lift', 'right_elbow', 'right_wrist_1', 'right_wrist_2', 'right_wrist_3', 'right_gripper']}
  observation.images.cam_high {'dtype': 'video', 'shape': (480, 640, 3), 'names': None, 'info': {'video.height': 480, 'video.width': 640, 'video.codec': 'av1', 'video.pix_fmt': 'yuv420p', 'video.is_depth_map': False, 'video.fps': 30, 'video.channels': 3, 'has_audio': False}}
  observation.images.cam_left_wrist {'dtype': 'video', 'shape': (480, 640, 3), 'names': None, 'info': {'video.height': 480, 'video.width': 640, 'video.codec': 'av1', 'video.pix_fmt': 'yuv420p', 'video.is_depth_map': False, 'video.fps': 30, 'video.channels': 3, 'has_audio': False}}
  observation.images.cam_right_wrist {'dtype': 'video', 'shape': (480, 640, 3), 'names': None, 'info': {'video.height': 480, 'video.width': 640, 'video.codec': 'av1', 'video.pix_fmt': 'yuv420p', 'video.is_depth_map': False, 'video.fps': 30, 'video.channels': 3, 'has_audio': False}}
  timestamp {'dtype': 'float32', 'shape': (1,), 'names': None}
  frame_index {'dtype': 'int64', 'shape': (1,), 'names': None}
  episode_index {'dtype': 'int64', 'shape': (1,), 'names': None}
  index {'dtype': 'int64', 'shape': (1,), 'names': None}
  task_index {'dtype': 'int64', 'shape': (1,), 'names': None}

first sample:
observation.images.cam_high (3, 480, 640) float32 finite: True
observation.images.cam_left_wrist (3, 480, 640) float32 finite: True
observation.images.cam_right_wrist (3, 480, 640) float32 finite: True
observation.state (14,) float32 finite: True
action (14,) float32 finite: True
timestamp () float32 finite: True
frame_index () int64 finite: True
episode_index () int64 finite: True
index () int64 finite: True
task_index () int64 finite: True
task teleop
```

单帧图像解码结果为：
```text
(3, 480, 640) float32
```

这说明：
- 数据结构适合双臂 ALOHA pipeline；
- 14 维顺序是左臂 6 关节、左夹爪、右臂 6 关节、右夹爪；
- 三路相机正好可映射到 $\pi_{0.5}$ 的三个图像槽位；
- Policy Transform 需要把 `CHW` 图像转成 `HWC`；
- float 图像需要转成 `uint8`；
- `task="teleop"` 没有任务语义，不能直接作为最终语言指令。

### 步骤 4：确定 action、夹爪和语言指令语义

必须明确 action 属于以下哪一种：
- 绝对关节目标；
- 相对当前 state 的关节 delta；
- 关节速度；
- 末端位姿或末端位姿增量。

如果 action 是绝对关节目标，可以在训练前将关节维度转换为相对当前 state 的 delta，推理输出时再转换回绝对值。夹爪通常保持绝对值。

还需要确认夹爪的数值定义：
- 是否在 `[0, 1]`；
- 0 表示闭合还是张开；
- 是否为角度、线性位置或编码器值。

> 如果统计确认 `action` 是绝对关节位置目标，则后续的配置需要使用：
> ```python
> use_delta_joint_actions=True
> ```
> 转换掩码为：
> ```python
> _transforms.make_bool_mask(6, -1, 6, -1)
> ```
> 含义是：
> ```text
> 左臂6关节：转 delta
> 左夹爪：保持绝对值
> 右臂6关节：转 delta
> 右夹爪：保持绝对值
> ```
> 如果 action 是速度或已经是 delta，则改成：
> ```python
> use_delta_joint_actions=False
> ```
> 
> 如果夹爪为标准 `[0,1]` ALOHA 定义，则后续的配置需要使用：
> ```python
> adapt_to_pi=True
> ```
> 如果 state/action 的夹爪值不是标准 `[0,1]` ALOHA 定义，先使用：
> ```python
> adapt_to_pi=False
> ```

可运行以下命令判断：
```bash
uv run python - <<'PY'
import numpy as np
from lerobot.common.datasets.lerobot_dataset import LeRobotDataset

repo_id = "<repo_id>"
ds = LeRobotDataset(repo_id)

states = np.stack(ds.hf_dataset["observation.state"])
actions = np.stack(ds.hf_dataset["action"])

np.set_printoptions(precision=4, suppress=True)

joint_indices = [0, 1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12]
gripper_indices = [6, 13]

print("state min:", states.min(axis=0))
print("state max:", states.max(axis=0))
print("action min:", actions.min(axis=0))
print("action max:", actions.max(axis=0))

print("\nmean |action-state|:")
print(np.mean(np.abs(actions - states), axis=0))

print("\njoint action mean/std:")
print(actions[:, joint_indices].mean(axis=0))
print(actions[:, joint_indices].std(axis=0))

print("\ngripper state range:")
print(states[:, gripper_indices].min(axis=0))
print(states[:, gripper_indices].max(axis=0))

print("\ngripper action range:")
print(actions[:, gripper_indices].min(axis=0))
print(actions[:, gripper_indices].max(axis=0))
PY
```

一般判断方式：
- action 与 state 范围相近，而且 `action-state` 较小：大概率是绝对关节目标；
- action 主要分布在 0 附近且量纲像 `rad/s`：大概率是速度；
- action 已经是小幅变化量：可能已经是 delta；
- 夹爪接近 `[0,1]` 且机器人是标准 Trossen ALOHA：通常可以启用 `adapt_to_pi=True`。

校验结果例如：
```text
state min: [-0.9181  0.1265 -1.1933 -0.6262  0.4674 -0.7664  0.0004  0.1362  0.
  0.      0.1     0.2957 -0.1128  0.0533]
state max: [-0.0321  1.9104 -0.3019  0.6231  1.2219  0.8165  0.061   0.1385  0.
  1.      0.1     0.2975 -0.1128  0.0533]
action min: [-0.9181  0.1265 -1.1933 -0.6262  0.4674 -0.7664  0.0004  0.1362  0.
  2.      0.1     0.2957 -0.1128  0.0533]
action max: [-0.0321  1.9104 -0.3019  0.6231  1.2219  0.8165  0.061   0.1385  0.
  3.      0.1     0.2975 -0.1128  0.0533]

mean |action-state|:
[0.0017 0.0094 0.0049 0.0036 0.0051 0.0044 0.0002 0.     0.     0.
 0.     0.     0.     0.    ]

joint action mean/std:
[-0.5962  1.294  -0.7856 -0.0255  0.8131  0.0884  0.1372  0.      0.
  0.1     0.2958 -0.1128]
[0.2148 0.4389 0.212  0.1844 0.137  0.3109 0.0012 0.     0.     0.
 0.0002 0.    ]

gripper state range:
[0.0004 0.0533]
[0.061  0.0533]

gripper action range:
[0.0004 0.0533]
[0.061  0.0533]
```

### 步骤 5：增加机器人 Policy Transform

Policy Transform 负责定义训练和推理时的机器人输入输出契约。它应完成：
- 把机器人图像映射到模型固定图像槽位；
- 把 float/CHW 图像转换为 uint8/HWC；
- 构造 `image_mask`；
- 提供 state、actions 和 prompt；
- 将模型的 32 维输出裁剪为机器人真实动作维度；
- 必要时完成机器人坐标系和夹爪定义转换。

$\pi_{0.5}$ 的三个图像槽位是：
```text
base_0_rgb
left_wrist_0_rgb
right_wrist_0_rgb
```

缺少某一路相机时，使用与主相机同 shape 的零图像，并将对应 `image_mask` 设为 `False`。

Policy Transform 中使用的数据字段应该是训练数据经过 `RepackTransform` 后的字段，同时也应该与机器人推理客户端发送的字段一致。

例如，新建：
```text
touch src/openpi/policies/task_name_policy.py
```

内容如下：
```python
"""Input/output transforms for the dual-arm ALOHA white-cube task."""

import dataclasses
from typing import ClassVar

import einops
import numpy as np

from openpi import transforms


def make_task_name_example() -> dict:
    """Create an example observation for testing policy inference."""
    return {
        "state": np.zeros((14,), dtype=np.float32),
        "images": {
            "cam_high": np.random.randint(
                256, size=(3, 480, 640), dtype=np.uint8
            ),
            "cam_left_wrist": np.random.randint(
                256, size=(3, 480, 640), dtype=np.uint8
            ),
            "cam_right_wrist": np.random.randint(
                256, size=(3, 480, 640), dtype=np.uint8
            ),
        },
        "prompt": "pick up the white cube",
    }


@dataclasses.dataclass(frozen=True)
class TaskNameInputs(transforms.DataTransformFn):
    """Convert dual-arm ALOHA data into openpi model inputs.

    Expected input:

    {
        "state": float32[14],
        "images": {
            "cam_high": image,
            "cam_left_wrist": image,
            "cam_right_wrist": image,
        },
        "actions": float32[action_horizon, 14],  # training only
        "prompt": str,
    }

    State/action order:

        left arm 6 joints
        left gripper
        right arm 6 joints
        right gripper
    """

    adapt_to_pi: bool = True

    EXPECTED_CAMERAS: ClassVar[tuple[str, ...]] = (
        "cam_high",
        "cam_left_wrist",
        "cam_right_wrist",
    )

    def __call__(self, data: dict) -> dict:
        state = np.asarray(
            data["state"],
            dtype=np.float32,
        ).copy()

        if state.shape[-1] != 14:
            raise ValueError(
                f"Expected 14-dimensional state, got {state.shape}"
            )

        if self.adapt_to_pi:
            state = _convert_state_to_pi(state)

        source_images = data["images"]

        unknown_cameras = (
            set(source_images) - set(self.EXPECTED_CAMERAS)
        )
        if unknown_cameras:
            raise ValueError(
                "Unexpected cameras: "
                f"{sorted(unknown_cameras)}. "
                f"Expected cameras: {self.EXPECTED_CAMERAS}"
            )

        if "cam_high" not in source_images:
            raise ValueError(
                'Required camera "cam_high" is missing'
            )

        base_image = _parse_image(
            source_images["cam_high"]
        )

        images = {
            "base_0_rgb": base_image,
        }
        image_masks = {
            "base_0_rgb": np.True_,
        }

        camera_mapping = {
            "left_wrist_0_rgb": "cam_left_wrist",
            "right_wrist_0_rgb": "cam_right_wrist",
        }

        for model_camera, dataset_camera in camera_mapping.items():
            if dataset_camera in source_images:
                images[model_camera] = _parse_image(
                    source_images[dataset_camera]
                )
                image_masks[model_camera] = np.True_
            else:
                images[model_camera] = np.zeros_like(
                    base_image
                )
                image_masks[model_camera] = np.False_

        result = {
            "state": state,
            "image": images,
            "image_mask": image_masks,
        }

        if "actions" in data:
            actions = np.asarray(
                data["actions"],
                dtype=np.float32,
            ).copy()

            if actions.shape[-1] != 14:
                raise ValueError(
                    "Expected actions with last dimension 14, "
                    f"got {actions.shape}"
                )

            if self.adapt_to_pi:
                actions = _convert_actions_to_pi(actions)

            result["actions"] = actions

        if "prompt" in data:
            prompt = data["prompt"]

            if isinstance(prompt, bytes):
                prompt = prompt.decode("utf-8")

            if isinstance(prompt, np.ndarray):
                prompt = prompt.item()

            result["prompt"] = str(prompt)

        return result


@dataclasses.dataclass(frozen=True)
class TaskNameOutputs(transforms.DataTransformFn):
    """Convert model output to 14-dimensional ALOHA actions."""

    adapt_to_pi: bool = True

    def __call__(self, data: dict) -> dict:
        actions = np.asarray(
            data["actions"][..., :14],
            dtype=np.float32,
        ).copy()

        if self.adapt_to_pi:
            actions = _convert_actions_from_pi(actions)

        return {
            "actions": actions,
        }


def _parse_image(image: np.ndarray) -> np.ndarray:
    """Convert an image to uint8 HWC RGB format."""
    image = np.asarray(image)

    if image.ndim != 3:
        raise ValueError(
            f"Expected a 3-dimensional image, got {image.shape}"
        )

    if np.issubdtype(image.dtype, np.floating):
        # LeRobot typically decodes video frames as float [0, 1].
        if image.size and float(np.nanmax(image)) <= 1.0 + 1e-6:
            image = image * 255.0

        image = np.clip(
            image,
            0,
            255,
        ).astype(np.uint8)

    elif image.dtype != np.uint8:
        image = np.clip(
            image,
            0,
            255,
        ).astype(np.uint8)

    # LeRobot sample shape is CHW: (3, 480, 640).
    if image.shape[0] == 3:
        image = einops.rearrange(
            image,
            "c h w -> h w c",
        )
    elif image.shape[-1] != 3:
        raise ValueError(
            "Expected CHW or HWC RGB image, "
            f"got {image.shape}"
        )

    return image


def _joint_flip_mask() -> np.ndarray:
    """Joint direction conversion between ALOHA and PI space."""
    return np.asarray(
        [
            1,
            -1,
            -1,
            1,
            1,
            1,
            1,
            1,
            -1,
            -1,
            1,
            1,
            1,
            1,
        ],
        dtype=np.float32,
    )


def _normalize(
    value: np.ndarray,
    minimum: float,
    maximum: float,
) -> np.ndarray:
    return (value - minimum) / (maximum - minimum)


def _unnormalize(
    value: np.ndarray,
    minimum: float,
    maximum: float,
) -> np.ndarray:
    return value * (maximum - minimum) + minimum


def _gripper_to_pi(value: np.ndarray) -> np.ndarray:
    """Convert normalized ALOHA gripper state to PI space."""
    linear_position = _unnormalize(
        value,
        minimum=0.01844,
        maximum=0.05800,
    )

    arm_length = 0.036
    horn_radius = 0.022

    denominator = (
        2.0 * horn_radius * linear_position
    )

    ratio = (
        horn_radius**2
        + linear_position**2
        - arm_length**2
    ) / denominator

    angle = np.arcsin(
        np.clip(ratio, -1.0, 1.0)
    )

    return _normalize(
        angle,
        minimum=0.5476,
        maximum=1.6296,
    )


def _gripper_from_pi(value: np.ndarray) -> np.ndarray:
    """Convert PI model gripper output to ALOHA space."""
    value = value + 0.5476

    return _normalize(
        value,
        minimum=-0.6213,
        maximum=1.4910,
    )


def _gripper_from_pi_inverse(
    value: np.ndarray,
) -> np.ndarray:
    """Convert ALOHA target gripper action into PI space."""
    value = _unnormalize(
        value,
        minimum=-0.6213,
        maximum=1.4910,
    )

    return value - 0.5476


def _convert_state_to_pi(
    state: np.ndarray,
) -> np.ndarray:
    state = state * _joint_flip_mask()

    state[..., [6, 13]] = _gripper_to_pi(
        state[..., [6, 13]]
    )

    return state


def _convert_actions_to_pi(
    actions: np.ndarray,
) -> np.ndarray:
    actions = actions * _joint_flip_mask()

    actions[..., [6, 13]] = (
        _gripper_from_pi_inverse(
            actions[..., [6, 13]]
        )
    )

    return actions


def _convert_actions_from_pi(
    actions: np.ndarray,
) -> np.ndarray:
    actions = actions * _joint_flip_mask()

    actions[..., [6, 13]] = _gripper_from_pi(
        actions[..., [6, 13]]
    )

    return actions
```

### 步骤 6：在 config.py 中增加 DataConfig

DataConfig 负责：
- 把 LeRobot 原始字段重组为 Policy Transform 所需字段；
- 指定训练和推理共用的 Policy Transform；
- 选择是否将绝对动作转换为 delta；
- 创建模型 tokenizer、resize 和 padding transforms；
- 指定构造未来 action chunk 的原始字段名。

`RepackTransform` 只作用于训练数据，不会自动作用于机器人推理请求。因此：
- 训练侧通过 Repack 把 LeRobot 字段变成 `state/images/actions`；
- 推理侧机器人客户端应直接发送 `state/images`；
- 二者进入 Policy Transform 时必须具有相同结构。

例如，编辑：
```text
src/openpi/training/config.py
```

在 policy imports 附近增加：
```python
import openpi.policies.task_name_policy as task_name_policy
```

在 `LeRobotAlohaDataConfig` 后增加：
```python
@dataclasses.dataclass(frozen=True)
class LeRobotTaskNameDataConfig(DataConfigFactory):
    """Data pipeline for the dual-arm ALOHA white-cube dataset."""

    # action 是绝对关节目标时设为 True。
    # action 已经是 delta 或速度时设为 False。
    use_delta_joint_actions: bool = True

    # 标准 Trossen ALOHA 数据通常设置为 True。
    adapt_to_pi: bool = True

    # 数据中的 task 是 "teleop"，因此使用具有真实语义的固定 prompt。
    default_prompt: str = "pick up the cube to the white area."

    @override
    def create(
        self,
        assets_dirs: pathlib.Path,
        model_config: _model.BaseModelConfig,
    ) -> DataConfig:
        # 只在读取 LeRobot 训练数据时执行。
        # 将 LeRobot 字段转换成 TaskNameInputs 所需结构。
        repack_transform = _transforms.Group(
            inputs=[
                _transforms.RepackTransform(
                    {
                        "images": {
                            "cam_high": (
                                "observation.images.cam_high"
                            ),
                            "cam_left_wrist": (
                                "observation.images.cam_left_wrist"
                            ),
                            "cam_right_wrist": (
                                "observation.images.cam_right_wrist"
                            ),
                        },
                        "state": "observation.state",
                        "actions": "action",
                    }
                )
            ]
        )

        # 训练和推理都会执行。
        data_transforms = _transforms.Group(
            inputs=[
                task_name_policy.TaskNameInputs(
                    adapt_to_pi=self.adapt_to_pi
                )
            ],
            outputs=[
                task_name_policy.TaskNameOutputs(
                    adapt_to_pi=self.adapt_to_pi
                )
            ],
        )

        if self.use_delta_joint_actions:
            # 14维动作顺序：
            #
            # 左臂6关节、左夹爪、右臂6关节、右夹爪。
            #
            # 两侧6个关节转为相对于当前状态的 delta；
            # 两个夹爪维度继续使用绝对值。
            delta_action_mask = _transforms.make_bool_mask(
                6,
                -1,
                6,
                -1,
            )

            data_transforms = data_transforms.push(
                inputs=[
                    _transforms.DeltaActions(
                        delta_action_mask
                    )
                ],
                outputs=[
                    _transforms.AbsoluteActions(
                        delta_action_mask
                    )
                ],
            )

        model_transforms = ModelTransformFactory(
            default_prompt=self.default_prompt
        )(model_config)

        return dataclasses.replace(
            self.create_base_config(
                assets_dirs,
                model_config,
            ),
            repack_transforms=repack_transform,
            data_transforms=data_transforms,
            model_transforms=model_transforms,

            # 必须是原始 LeRobot 数据集里的 action 字段名。
            action_sequence_keys=("action",),
        )

```

这里没有把 `task` 或 `prompt` 加入 Repack，因为案例数据的任务文本是无意义的 `teleop`。固定 prompt 将由 `ModelTransformFactory` 注入。

### 步骤 7：在 config.py 中增加 TrainConfig

TrainConfig 至少需要指定：
- 唯一配置名；
- $\pi_{0.5}$ 模型结构；
- 自定义 DataConfig；
- $\pi_{0.5}$ base checkpoint；
- batch size、训练步数和保存间隔；
- 学习率、优化器和 EMA；
- 是否启用 W&B。

$\pi_{0.5}$ base checkpoint 的动作头是 32 维。即使机器人动作只有 14 维，也应保持：
```python
action_dim=32
```

数据 pipeline 会将 14 维 state/action 补到 32 维，Policy 输出再裁剪回 14 维。将模型 `action_dim` 直接改成 14 会导致基础权重 shape 不匹配。

训练步数可以用以下公式估算：
```text
epochs ≈ num_train_steps × batch_size / 数据集总帧数
```

例如，在 `_CONFIGS` 的 ALOHA 微调区域增加：
```python
TrainConfig(
    name="pi05_task_name",

    model=pi0_config.Pi0Config(
        pi05=True,
        action_dim=32,
        action_horizon=50,
    ),

    data=LeRobotTaskNameDataConfig(
        repo_id="lv/put-cube-into-white",

        base_config=DataConfig(
            prompt_from_task=False,
        ),

        default_prompt="pick up the white cube",
        adapt_to_pi=True,
        use_delta_joint_actions=True,

        assets=AssetsConfig(
            assets_dir=(
                "gs://openpi-assets/checkpoints/"
                "pi05_base/assets"
            ),
            asset_id="trossen",
        ),
    ),

    weight_loader=weight_loaders.CheckpointWeightLoader(
        "gs://openpi-assets/checkpoints/pi05_base/params"
    ),

    batch_size=32,
    num_train_steps=5_000,

    log_interval=50,
    save_interval=500,
    keep_period=1_000,

    lr_schedule=_optimizer.CosineDecaySchedule(
        warmup_steps=500,
        peak_lr=5e-5,
        decay_steps=5_000,
        decay_lr=1e-5,
    ),

    optimizer=_optimizer.AdamW(
        clip_gradient_norm=1.0,
    ),

    ema_decay=0.999,
    wandb_enabled=True,
),
```

如果只有显存不够多，可以使用 JAX LoRA，代码为：
```python
TrainConfig(
    name="pi05_task_name_lora",

    model=pi0_config.Pi0Config(
        pi05=True,
        action_dim=32,
        action_horizon=50,
        paligemma_variant="gemma_2b_lora",
        action_expert_variant="gemma_300m_lora",
    ),

    data=LeRobotTaskNameDataConfig(
        repo_id="lv/put-cube-into-white",
        base_config=DataConfig(prompt_from_task=False),
        default_prompt="pick up the white cube",
        adapt_to_pi=True,
        use_delta_joint_actions=True,

        # LoRA 配置也必须保留归一化资产。
        assets=AssetsConfig(
            assets_dir=(
                "gs://openpi-assets/checkpoints/"
                "pi05_base/assets"
            ),
            asset_id="trossen",
        ),
    ),

    weight_loader=weight_loaders.CheckpointWeightLoader(
        "gs://openpi-assets/checkpoints/pi05_base/params"
    ),

    freeze_filter=pi0_config.Pi0Config(
        pi05=True,
        action_dim=32,
        action_horizon=50,
        paligemma_variant="gemma_2b_lora",
        action_expert_variant="gemma_300m_lora",
    ).get_freeze_filter(),

    batch_size=8,
    num_train_steps=5_000,
    log_interval=50,
    save_interval=500,
    keep_period=1_000,

    lr_schedule=_optimizer.CosineDecaySchedule(
        warmup_steps=500,
        peak_lr=5e-5,
        decay_steps=5_000,
        decay_lr=1e-5,
    ),
    optimizer=_optimizer.AdamW(clip_gradient_norm=1.0),

    # LoRA 不为全部基础参数维护 EMA 副本，可显著减少显存。
    ema_decay=None,
    wandb_enabled=False,
),
```

### 步骤 8：选择和验证归一化统计

训练和推理都必须使用相同的 state/action 归一化统计。可以选择：
1. 复用与目标机器人匹配的预训练统计；
2. 使用当前数据集重新计算统计。

如果显式配置了：
```python
assets=AssetsConfig(
    assets_dir="...",
    asset_id="...",
)
```

DataConfig 会优先从指定位置加载统计。在这种情况下，即使运行 `compute_norm_stats.py`，配置仍会继续使用显式指定的远程统计。

如果要使用自己的统计，应删除显式 `assets_dir` 配置，再运行：
```bash
uv run scripts/compute_norm_stats.py \
  --config-name <config_name>
```

需要检查 `norm_stats.json` 中的：
- `state.q01`、`state.q99`；
- `actions.q01`、`actions.q99`；
- `state.std`、`actions.std`；
- 是否存在某维 `q01≈q99` 或 `std≈0`。

如果数据确实使用标准 Trossen ALOHA 关节、符号和 `[0,1]` 夹爪定义，优先使用：
```python
assets=AssetsConfig(
    assets_dir="gs://openpi-assets/checkpoints/pi05_base/assets",
    asset_id="trossen",
)
```

这种方案不需要运行 `compute_norm_stats.py`。

全参数配置和 LoRA 配置是两个独立的 `TrainConfig`。即使 `pi05_task_name` 已经配置了 `trossen`，也不会自动传给 `pi05_task_name_lora`。LoRA 配置漏掉 `assets` 时，日志通常会先出现：
```text
Norm stats not found in
.../assets/pi05_task_name_lora/lv/put-cube-into-white,
skipping.
```

随后在创建 DataLoader 时终止：
```text
ValueError: Normalization stats not found. Make sure to run
scripts/compute_norm_stats.py --config-name=<your-config>.
```

这不是 CUDA、FSDP 或 LoRA 本身的错误，而是数据配置没有解析到归一化统计。对于本案例，修复方式是给 `pi05_task_name_lora` 的 `data` 增加与上面相同的 `AssetsConfig(..., asset_id="trossen")`。

如果机器人只是“类似 ALOHA”，但关节顺序、单位或夹爪定义不同，应：
1. 将 `adapt_to_pi` 设为符合实际情况的值；
2. 删除上述 `assets=AssetsConfig(...)`；
3. 计算自己的统计：
```bash
uv run scripts/compute_norm_stats.py \
  --config-name pi05_task_name_lora
```

计算完成后确认日志中已经加载本地统计，并检查实际文件：
```bash
find assets/pi05_task_name_lora \
  -name norm_stats.json \
  -print
```

注意不要同时保留指向 `trossen` 的显式远程 `assets`，又期待配置读取刚计算的本地统计。应在两种方案中选择一种，并让训练和部署始终使用同一份统计。

实践中可以训练两个实验，一个复用 `trossen`，一个使用新统计，再以真实机器人成功率选择。

### 步骤 9：验证代码和完整数据 Pipeline

正式训练前先验证：
- 新文件没有 Python 语法错误；
- 训练配置能被 `get_config()` 找到；
- 数据字段能够完成 Repack；
- 三路图像 shape 正确；
- state/action 被正确 padding；
- prompt 能成功 tokenize；
- 所有数值均为有限值。

先做语法检查：
```bash
cd openpi

uv run python -m compileall \
  src/openpi/policies/task_name_policy.py \
  src/openpi/training/config.py
```

检查配置注册：
```bash
uv run python - <<'PY'
from openpi.training import config

cfg = config.get_config("pi05_task_name")

print("name:", cfg.name)
print("repo_id:", cfg.data.repo_id)
print("model type:", cfg.model.model_type)
print("action dim:", cfg.model.action_dim)
print("action horizon:", cfg.model.action_horizon)
print("batch size:", cfg.batch_size)
print("train steps:", cfg.num_train_steps)
PY
```

准备进行 LoRA 训练时，还必须对 LoRA 配置单独执行同样检查：
```bash
uv run python - <<'PY'
from openpi.training import config
from openpi.training import data_loader

cfg = config.get_config("pi05_task_name_lora")
loader = data_loader.create_data_loader(
    cfg,
    shuffle=False,
    num_batches=1,
)
observation, actions = next(iter(loader))

print("config:", cfg.name)
print("state:", observation.state.shape)
print("actions:", actions.shape)
PY
```

更直接的方式是把上一段 Pipeline 脚本中的配置名改为 `pi05_task_name_lora`。LoRA 的 batch size 为 8 时，预期 batch 维也会从 32 变成 8；其余 state/action/image 最后几维保持不变。

预期关键输出：
```text
name: pi05_task_name
action dim: 32
action horizon: 50
batch size: 32
train steps: 5000
```

检查完整 Pipeline：
```bash
uv run python - <<'PY'
import numpy as np

from openpi.training import config
from openpi.training import data_loader

cfg = config.get_config("pi05_task_name")

loader = data_loader.create_data_loader(
    cfg,
    shuffle=False,
    num_batches=1,
)

observation, actions = next(iter(loader))

print("state:", observation.state.shape, observation.state.dtype)
print("actions:", actions.shape, actions.dtype)

for key, value in observation.images.items():
    print("image:", key, value.shape, value.dtype)

print("prompt tokens:", observation.tokenized_prompt.shape)
print("state finite:", np.isfinite(observation.state).all())
print("actions finite:", np.isfinite(actions).all())
PY
```

预期主要 shape：
```text
state:   (32, 32)
actions: (32, 50, 32)

base_0_rgb:        (32, 224, 224, 3)
left_wrist_0_rgb:  (32, 224, 224, 3)
right_wrist_0_rgb: (32, 224, 224, 3)
```

原始数据是 14 维，模型输入变成 32 维是正常的。出现以下情况时不要开始训练：
- 找不到某个相机字段；
- `Prompt is required`；
- action chunk timestamp 错误；
- state/action 包含 NaN；
- state/action 最后一维不是 32；
- 图像不是 224×224×3。

### 步骤 10：启动、覆盖和恢复训练

JAX 默认会预分配部分 GPU 显存，可以通过 `XLA_PYTHON_CLIENT_MEM_FRACTION` 调整。训练时需要为每次实验指定唯一 `exp-name`。

已有实验目录存在时：
- `--resume`：从最后 checkpoint 恢复；
- `--overwrite`：删除并覆盖已有实验；
- 两者不能同时使用。

全局 batch size 必须能被 GPU 数量整除。单机多卡可以通过 `--fsdp-devices` 启用 FSDP。

例如，两张 GPU 上首次进行 LoRA 训练：
```bash
export HF_LEROBOT_HOME=/data/lerobot

CUDA_VISIBLE_DEVICES=1,2 \
XLA_PYTHON_CLIENT_MEM_FRACTION=0.90 \
uv run scripts/train.py \
  pi05_task_name_lora \
  --exp-name=task_name_lora_run_01 \
  --fsdp-devices=2 \
  --no-wandb-enabled
```

这里的 `--fsdp-devices=2` 使用的是设置 `CUDA_VISIBLE_DEVICES` 后，JAX 实际可见的两张卡。训练前确认：
```bash
CUDA_VISIBLE_DEVICES=1,2 uv run python - <<'PY'
import jax

print("device count:", jax.device_count())
print("devices:", jax.devices())
PY
```

预期 `device count` 为 2，且全局 `batch_size` 能被 2 整除。

如果资源足够进行全参数微调，再改用：
```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 \
XLA_PYTHON_CLIENT_MEM_FRACTION=0.90 \
uv run scripts/train.py \
  pi05_task_name \
  --exp-name=task_name_run_01 \
  --fsdp-devices=4 \
  --no-wandb-enabled
```

两张约 24 GB GPU 通常不足以初始化 π₀.₅ 全参数 AdamW 训练状态。减小 batch size 主要减少 activation 和批数据显存，不会消除模型参数、Adam 一阶矩、Adam 二阶矩和 EMA 副本带来的初始化峰值；因此这类环境应使用 LoRA 和 `ema_decay=None`。

中断后恢复：
```bash
CUDA_VISIBLE_DEVICES=1,2 \
XLA_PYTHON_CLIENT_MEM_FRACTION=0.90 \
uv run scripts/train.py \
  pi05_task_name_lora \
  --exp-name=task_name_lora_run_01 \
  --fsdp-devices=2 \
  --no-wandb-enabled \
  --resume
```

确认要删除同名实验并重新训练时：
```bash
CUDA_VISIBLE_DEVICES=1,2 \
XLA_PYTHON_CLIENT_MEM_FRACTION=0.90 \
uv run scripts/train.py \
  pi05_task_name_lora \
  --exp-name=task_name_lora_run_01 \
  --fsdp-devices=2 \
  --no-wandb-enabled \
  --overwrite
```

checkpoint 目录为：
```text
checkpoints/pi05_task_name_lora/task_name_lora_run_01/<step>/
```

每个可部署 checkpoint 应至少包含：
```text
params/
assets/
```

### 步骤 11：评估并选择 Checkpoint

不能只根据训练 loss 选择模型。至少应比较：
- 未参与训练的初始位置；
- 不同方块位置和姿态；
- 不同背景和光照；
- 多个 checkpoint 的成功率；
- 动作抖动、漂移和越界情况；
- 夹爪开合方向和时机；
- 推理延迟；
- 语言指令变化后的行为。

小数据集通常可能出现训练 loss 持续下降，但真实 rollout 在后期 checkpoint 反而变差的情况。

## Deploy

### 步骤 12：启动 Policy Server

部署时必须使用：
- 与训练相同的 config；
- 对应 checkpoint 根目录；
- checkpoint 中保存的归一化统计；
- 与训练语义一致的 prompt。

Policy Server 默认监听 `0.0.0.0:8000`。第一次 JAX 推理包含编译开销，应在机器人开始运动前进行预热。

该服务默认不应直接暴露到公网，建议部署在机器人局域网、VPN 或受控容器网络中。

假设选择 LoRA checkpoint 3000：
```bash
uv run scripts/serve_policy.py \
  --port=8000 \
  policy:checkpoint \
  --policy.config=pi05_task_name_lora \
  --policy.dir=checkpoints/pi05_task_name_lora/task_name_lora_run_01/3000
```

配置中已有默认 prompt，因此客户端可以不传 prompt。也可以启动服务时覆盖：
```bash
uv run scripts/serve_policy.py \
  --port=8000 \
  policy:checkpoint \
  --policy.config=pi05_task_name_lora \
  --policy.dir=checkpoints/pi05_task_name_lora/task_name_lora_run_01/3000 \
  --default-prompt="pick up the white cube"
```

调试时记录推理请求和输出：
```bash
uv run scripts/serve_policy.py \
  --port=8000 \
  policy:checkpoint \
  --policy.config=pi05_task_name_lora \
  --policy.dir=checkpoints/pi05_task_name_lora/task_name_lora_run_01/3000 \
  --record
```

机器人接入前，先使用 `make_task_name_example()` 发送 2～3 次请求完成预热。

### 步骤 13：接入机器人客户端并匹配控制频率

机器人端只需要安装轻量客户端：
```bash
cd openpi/packages/openpi-client
pip install -e .
```

客户端发送的数据结构必须与 Policy Transform 在推理时期待的结构一致。对于当前 Policy，应发送：
```python
{
    "state": state_14d,
    "images": {
        "cam_high": image,
        "cam_left_wrist": image,
        "cam_right_wrist": image,
    },
    "prompt": task_instruction,
}
```

部署端必须保证：
- 图像是 RGB，不是 OpenCV 默认 BGR；
- state 维度、顺序和单位与训练数据一致；
- action 顺序、单位和 absolute/delta 语义一致；
- 控制频率与数据集 FPS 一致；
- action chunk 的执行步数不大于模型输出 horizon；
- 具备急停、关节限位、速度限制和通信超时保护。

模型可以一次预测较长 action chunk，但通常只执行前若干步，然后重新观测并规划，以提高闭环性。

例如，案例数据是 30 Hz，因此机器人控制循环也应使用：
```python
max_hz=30
```

仓库现有 ALOHA 示例在 `examples/aloha_real/main.py` 中默认使用 50 Hz，需要改成 30 Hz。

机器人端启动示例：
```bash
python -m examples.aloha_real.main \
  --host <server_ip> \
  --port 8000 \
  --action-horizon 10
```

这里：
- 模型输出 50 个未来动作；
- 机器人执行前 10 步；
- 执行约 `10/30≈0.33` 秒后重新请求模型；
- 如果动作响应不够及时，可以将执行 horizon 减少到 5；
- 如果网络和推理延迟较大，可以适当增加，但不应盲目执行全部 50 步。

直接使用 WebSocket 客户端时，核心结构为：
```python
from openpi_client import websocket_client_policy


policy = websocket_client_policy.WebsocketClientPolicy(
    host="<server_ip>",
    port=8000,
)

observation = {
    "state": robot_state,
    "images": {
        "cam_high": cam_high,
        "cam_left_wrist": cam_left_wrist,
        "cam_right_wrist": cam_right_wrist,
    },
    "prompt": "pick up the white cube",
}

result = policy.infer(observation)
action_chunk = result["actions"]

for action in action_chunk[:10]:
    safe_action = apply_robot_safety_limits(action)
    send_action_to_robot(safe_action)
    wait_for_next_30hz_tick()
```

快速测试
```shell
uv run python - <<'PY'
import numpy as np
from openpi_client.websocket_client_policy import WebsocketClientPolicy

SERVER_IP = "192.168.1.100"  # 改成服务端的局域网 IP

client = WebsocketClientPolicy(
    host=SERVER_IP,
    port=8000,
)

print("服务器 metadata:", client.get_server_metadata())

observation = {
    "state": np.zeros((14,), dtype=np.float32),
    "images": {
        "cam_high": np.random.randint(
            0, 256, (3, 480, 640), dtype=np.uint8
        ),
        "cam_left_wrist": np.random.randint(
            0, 256, (3, 480, 640), dtype=np.uint8
        ),
        "cam_right_wrist": np.random.randint(
            0, 256, (3, 480, 640), dtype=np.uint8
        ),
    },
    "prompt": "pick up the white cube",
}

result = client.infer(observation)

print("返回字段:", result.keys())
print("actions shape:", result["actions"].shape)
print("第一条 action:", result["actions"][0])
print("服务端耗时:", result.get("server_timing"))
print("策略耗时:", result.get("policy_timing"))
PY
```

