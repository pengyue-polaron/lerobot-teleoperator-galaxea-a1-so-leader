"""LeRobot configuration for the Galaxea A1 SO-Leader."""

from __future__ import annotations

from dataclasses import dataclass

from lerobot.teleoperators.config import TeleoperatorConfig


@TeleoperatorConfig.register_subclass("galaxea_a1_so_leader")
@dataclass
class GalaxeaA1SOLeaderConfig(TeleoperatorConfig):
    """The physical topology is fixed; only lifecycle identity and port vary."""

    port: str = "/dev/ttyACM0"
    motor_write_retries: int = 5

    def __post_init__(self) -> None:
        if not self.port.startswith("/dev/") or any(character.isspace() for character in self.port):
            raise ValueError("port must be a whitespace-free device path under /dev")
        if (
            isinstance(self.motor_write_retries, bool)
            or not isinstance(self.motor_write_retries, int)
            or self.motor_write_retries < 1
        ):
            raise ValueError("motor_write_retries must be a positive integer")
