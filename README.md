<h1 align="center">Galaxea A1 SO-Leader for LeRobot</h1>

<p align="center">
  A third-party LeRobot Teleoperator plugin for the modified A1 leader arm.
</p>

<p align="center">
  <a href="https://huggingface.co/docs/lerobot/v0.6.0/en/integrate_hardware"><img alt="LeRobot 0.6" src="https://img.shields.io/badge/LeRobot-0.6-FFD21E"></a>
  <a href="LICENSE"><img alt="Apache-2.0 License" src="https://img.shields.io/badge/License-Apache--2.0-blue.svg"></a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/pengyue-polaron/galaxea-a1-runtime/main/assets/images/a1-teleoperation-setup.png" width="760" alt="Modified six-axis SO-101 leader paired with a Galaxea A1 follower">
</p>

This package registers the LeRobot Teleoperator type
`galaxea_a1_so_leader`. It owns the leader's serial bus, calibration, setup,
action reads, optional feedback, and connection lifecycle. It does not import
ROS, start an A1 Runtime, record datasets, or map leader values into robot
coordinates.

## Install

```bash
python -m pip install lerobot_teleoperator_galaxea_a1_so_leader
```

## LeRobot integration

| Convention | Value |
| --- | --- |
| Distribution | `lerobot_teleoperator_galaxea_a1_so_leader` |
| Type | `galaxea_a1_so_leader` |
| Config | `GalaxeaA1SOLeaderConfig` |
| Teleoperator | `GalaxeaA1SOLeader` |
| Supported LeRobot | `>=0.6,<0.7` |

The distribution prefix, module layout, config registration, class names, and
package exports follow LeRobot's
[third-party hardware conventions](https://huggingface.co/docs/lerobot/v0.6.0/en/integrate_hardware).
LeRobot CLI entrypoints discover the plugin after installation.

## Hardware contract

| Channel | Hardware | Reported value |
| --- | --- | --- |
| `joint0` ... `joint5` | Feetech STS3215 IDs 0...5 | degrees |
| `gripper` | Feetech STS3215 ID 6 | calibrated `RANGE_0_100` |

The seven-motor topology is fixed. The config supplies lifecycle identity,
serial port, and write retries; it does not redefine motor IDs or units.

To calibrate the leader by itself:

```bash
lerobot-calibrate \
  --teleop.type=galaxea_a1_so_leader \
  --teleop.id=a1-leader \
  --teleop.port=/dev/serial/by-id/your-device
```

This command opens the serial device. Run it only with the leader connected
and its workspace clear.

## Pairing with Galaxea A1

Leader outputs are not A1 commands. The leader reports degrees and its
calibrated gripper range; the A1 Robot plugin accepts radians and a normalized
`0..1` gripper target.

Use `make_galaxea_a1_processors()` from
[lerobot-robot-galaxea-a1](https://github.com/pengyue-polaron/lerobot-robot-galaxea-a1)
with LeRobot's programmatic APIs, or use the tracked
[Galaxea A1 Runtime](https://github.com/pengyue-polaron/galaxea-a1-runtime)
workflow. Do not pair these devices through the identity processor in the
generic LeRobot 0.6 CLI.

## Development

```bash
uv sync --dev
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv build
```
