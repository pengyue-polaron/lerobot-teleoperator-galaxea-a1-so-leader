# LeRobot Teleoperator plugin for the Galaxea A1 SO-Leader

This package provides the auto-discovered LeRobot teleoperator type
`galaxea_a1_so_leader` for the Galaxea A1 tabletop leader arm.

The hardware topology is intentionally fixed:

```text
joint0 .. joint5  Feetech STS3215 IDs 0..5, output in degrees
gripper           Feetech STS3215 ID 6, calibrated RANGE_0_100 output
```

The plugin owns only the serial bus, calibration, setup, truthful raw actions, optional
feedback, and connection lifecycle. It does not import ROS, start an A1 runtime, map
leader values to robot coordinates, record datasets, or publish robot commands.

## Install

```bash
python -m pip install lerobot_teleoperator_galaxea_a1_so_leader
```

LeRobot discovers the exact `lerobot_teleoperator_` distribution prefix:

```bash
lerobot-teleoperate \
  --teleop.type=galaxea_a1_so_leader \
  --teleop.id=a1-leader \
  --teleop.port=/dev/serial/by-id/your-device
```

## Pairing with Galaxea A1

Raw leader actions are not valid A1 robot commands. The joints use degrees and the
gripper reports its calibrated leader range, while the A1 Robot plugin accepts absolute
radians and a normalized `0..1` gripper target.

Use `make_galaxea_a1_processors()` from
[`lerobot-robot-galaxea-a1`](https://github.com/pengyue-polaron/lerobot-robot-galaxea-a1)
with LeRobot's programmatic `teleoperate` or `record` API. The processor anchors leader
deltas to the startup A1 pose and applies the explicit tracked sign, scale, bias, limit,
and gripper range contract.

Do not use the raw leader and A1 Robot together through the identity processor in the
generic LeRobot 0.6 CLI.

## Development

```bash
uv sync --dev
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv build
```

CI replaces the Feetech bus with a fake and never opens a serial device.

## License

Apache-2.0
