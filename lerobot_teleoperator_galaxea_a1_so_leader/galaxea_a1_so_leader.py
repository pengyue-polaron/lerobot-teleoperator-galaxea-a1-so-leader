"""Galaxea A1 SO-Leader implementation using LeRobot Feetech primitives."""

from __future__ import annotations

import logging
import math
import time
from typing import Any

from lerobot.motors import Motor, MotorCalibration, MotorNormMode
from lerobot.motors.feetech import FeetechMotorsBus, OperatingMode
from lerobot.teleoperators.teleoperator import Teleoperator
from lerobot.types import RobotAction
from lerobot.utils.decorators import check_if_already_connected, check_if_not_connected

from .config_galaxea_a1_so_leader import GalaxeaA1SOLeaderConfig

logger = logging.getLogger(__name__)

JOINT_NAMES = tuple(f"joint{index}" for index in range(6))
GRIPPER_NAME = "gripper"
MOTOR_NAMES = (*JOINT_NAMES, GRIPPER_NAME)


class GalaxeaA1SOLeader(Teleoperator):
    """Six degree-output leader joints at IDs 0..5 and gripper at ID 6."""

    config_class = GalaxeaA1SOLeaderConfig
    name = "galaxea_a1_so_leader"

    def __init__(self, config: GalaxeaA1SOLeaderConfig):
        super().__init__(config)
        self.config = config
        self.bus = FeetechMotorsBus(
            port=config.port,
            motors={
                **{
                    name: Motor(index, "sts3215", MotorNormMode.DEGREES)
                    for index, name in enumerate(JOINT_NAMES)
                },
                GRIPPER_NAME: Motor(6, "sts3215", MotorNormMode.RANGE_0_100),
            },
            calibration=self.calibration,
        )

    @property
    def action_features(self) -> dict[str, type]:
        return {f"{motor}.pos": float for motor in MOTOR_NAMES}

    @property
    def feedback_features(self) -> dict[str, type]:
        return self.action_features

    @property
    def is_connected(self) -> bool:
        return self.bus.is_connected

    @check_if_already_connected
    def connect(self, calibrate: bool = True) -> None:
        self.bus.connect()
        if not self.is_calibrated and calibrate:
            logger.info("No matching A1 SO-Leader calibration was found; starting calibration")
            self.calibrate()
        self.configure()
        logger.info("%s connected", self)

    @property
    def is_calibrated(self) -> bool:
        return self.bus.is_calibrated

    def calibrate(self) -> None:
        if self.calibration:
            answer = input(
                f"Use calibration for {self.id}: Enter=accept, c=recalibrate > "
            )
            if answer.strip().lower() != "c":
                self.bus.write_calibration(self.calibration)
                return

        self.bus.disable_torque(num_retry=self.config.motor_write_retries)
        for motor in MOTOR_NAMES:
            self.bus.write(
                "Operating_Mode",
                motor,
                OperatingMode.POSITION.value,
                num_retry=self.config.motor_write_retries,
            )
        input(f"Move {self} to the middle of its range, then press Enter > ")
        homing_offsets = self.bus.set_half_turn_homings()
        print(
            "Move all joints sequentially through their complete usable ranges. "
            "Press Enter to stop recording."
        )
        range_mins, range_maxes = self.bus.record_ranges_of_motion(list(MOTOR_NAMES))

        self.calibration = {
            motor: MotorCalibration(
                id=definition.id,
                drive_mode=0,
                homing_offset=homing_offsets[motor],
                range_min=range_mins[motor],
                range_max=range_maxes[motor],
            )
            for motor, definition in self.bus.motors.items()
        }
        self.bus.write_calibration(self.calibration)
        self._save_calibration()
        logger.info("Calibration saved to %s", self.calibration_fpath)

    def configure(self) -> None:
        retries = self.config.motor_write_retries
        self.bus.disable_torque(num_retry=retries)
        self.bus.configure_motors()
        for motor in MOTOR_NAMES:
            self.bus.write(
                "Operating_Mode",
                motor,
                OperatingMode.POSITION.value,
                num_retry=retries,
            )

    def enable_torque(self) -> None:
        self.bus.enable_torque(num_retry=self.config.motor_write_retries)

    def disable_torque(self) -> None:
        self.bus.disable_torque(num_retry=self.config.motor_write_retries)

    def setup_motors(self) -> None:
        for motor in reversed(MOTOR_NAMES):
            input(f"Connect only motor {motor}, then press Enter > ")
            self.bus.setup_motor(motor)
            logger.info("Motor %s ID set to %s", motor, self.bus.motors[motor].id)

    @check_if_not_connected
    def get_action(self) -> RobotAction:
        start = time.perf_counter()
        positions = self.bus.sync_read("Present_Position")
        action = {f"{motor}.pos": float(positions[motor]) for motor in MOTOR_NAMES}
        _validate_values(action, required=set(self.action_features), allow_partial=False)
        logger.debug("%s read action in %.1fms", self, (time.perf_counter() - start) * 1e3)
        return action

    @check_if_not_connected
    def send_feedback(self, feedback: dict[str, Any]) -> None:
        _validate_values(feedback, required=set(self.feedback_features), allow_partial=True)
        goals = {key.removesuffix(".pos"): float(value) for key, value in feedback.items()}
        if goals:
            self.bus.sync_write("Goal_Position", goals)

    @check_if_not_connected
    def disconnect(self) -> None:
        self.bus.disconnect()
        logger.info("%s disconnected", self)


def _validate_values(
    values: dict[str, Any],
    *,
    required: set[str],
    allow_partial: bool,
) -> None:
    unknown = set(values) - required
    missing = required - set(values)
    if unknown:
        raise ValueError(f"unknown SO-Leader features: {sorted(unknown)}")
    if missing and not allow_partial:
        raise ValueError(f"missing SO-Leader features: {sorted(missing)}")
    for key, value in values.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"SO-Leader feature {key!r} must be numeric")
        if not math.isfinite(float(value)):
            raise ValueError(f"SO-Leader feature {key!r} must be finite")
