from __future__ import annotations

import pytest
from lerobot.motors import MotorNormMode
from lerobot.teleoperators.config import TeleoperatorConfig
from lerobot.teleoperators.utils import make_teleoperator_from_config

import lerobot_teleoperator_galaxea_a1_so_leader.galaxea_a1_so_leader as leader_module
from lerobot_teleoperator_galaxea_a1_so_leader import (
    GalaxeaA1SOLeader,
    GalaxeaA1SOLeaderConfig,
)


class FakeBus:
    instances: list["FakeBus"] = []

    def __init__(self, *, port: str, motors: dict, calibration: dict):
        self.port = port
        self.motors = motors
        self.calibration = calibration
        self.is_connected = False
        self.is_calibrated = True
        self.goal_writes: list[dict[str, float]] = []
        self.register_writes: list[tuple] = []
        FakeBus.instances.append(self)

    def connect(self) -> None:
        self.is_connected = True

    def disconnect(self) -> None:
        self.is_connected = False

    def disable_torque(self, **_kwargs) -> None: ...

    def enable_torque(self, **_kwargs) -> None: ...

    def configure_motors(self) -> None: ...

    def write(self, *args, **kwargs) -> None:
        self.register_writes.append((*args, kwargs))

    def sync_read(self, register: str) -> dict[str, float]:
        assert register == "Present_Position"
        return {name: float(index) for index, name in enumerate(self.motors)}

    def sync_write(self, register: str, values: dict[str, float]) -> None:
        assert register == "Goal_Position"
        self.goal_writes.append(values)


@pytest.fixture(autouse=True)
def fake_bus(monkeypatch: pytest.MonkeyPatch):
    FakeBus.instances.clear()
    monkeypatch.setattr(leader_module, "FeetechMotorsBus", FakeBus)


def test_plugin_registration_and_fixed_motor_topology() -> None:
    assert "galaxea_a1_so_leader" in TeleoperatorConfig.get_known_choices()
    leader = make_teleoperator_from_config(
        GalaxeaA1SOLeaderConfig(id="test", port="/dev/test-leader")
    )

    assert isinstance(leader, GalaxeaA1SOLeader)
    assert tuple(leader.bus.motors) == (
        "joint0",
        "joint1",
        "joint2",
        "joint3",
        "joint4",
        "joint5",
        "gripper",
    )
    assert [motor.id for motor in leader.bus.motors.values()] == list(range(7))
    assert all(
        leader.bus.motors[name].norm_mode is MotorNormMode.DEGREES
        for name in tuple(leader.bus.motors)[:6]
    )
    assert leader.bus.motors["gripper"].norm_mode is MotorNormMode.RANGE_0_100
    assert leader.bus.goal_writes == []


def test_read_feedback_and_disconnect_have_explicit_effects_only() -> None:
    leader = GalaxeaA1SOLeader(GalaxeaA1SOLeaderConfig(id="test", port="/dev/test-leader"))
    leader.connect(calibrate=False)

    assert leader.get_action() == {
        **{f"joint{index}.pos": float(index) for index in range(6)},
        "gripper.pos": 6.0,
    }
    leader.send_feedback({"joint0.pos": 1.5})
    assert leader.bus.goal_writes == [{"joint0": 1.5}]
    with pytest.raises(ValueError, match="finite"):
        leader.send_feedback({"joint0.pos": float("nan")})
    with pytest.raises(ValueError, match="unknown"):
        leader.send_feedback({"surprise.pos": 1.0})

    leader.disconnect()
    assert leader.bus.goal_writes == [{"joint0": 1.5}]
    assert leader.is_connected is False


def test_connect_failure_releases_the_serial_bus(monkeypatch: pytest.MonkeyPatch) -> None:
    leader = GalaxeaA1SOLeader(GalaxeaA1SOLeaderConfig(id="test", port="/dev/test-leader"))

    def fail_configure() -> None:
        raise RuntimeError("injected configuration failure")

    monkeypatch.setattr(leader, "configure", fail_configure)
    with pytest.raises(RuntimeError, match="injected configuration failure"):
        leader.connect(calibrate=False)
    assert leader.is_connected is False


def test_motor_write_retries_rejects_booleans() -> None:
    with pytest.raises(ValueError, match="positive integer"):
        GalaxeaA1SOLeaderConfig(
            id="test",
            port="/dev/test-leader",
            motor_write_retries=True,
        )
