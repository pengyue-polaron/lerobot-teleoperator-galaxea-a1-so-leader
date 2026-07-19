"""Auto-discovered LeRobot Teleoperator plugin for Galaxea A1."""

from .config_galaxea_a1_so_leader import GalaxeaA1SOLeaderConfig
from .galaxea_a1_so_leader import GalaxeaA1SOLeader

__all__ = ["GalaxeaA1SOLeader", "GalaxeaA1SOLeaderConfig"]
