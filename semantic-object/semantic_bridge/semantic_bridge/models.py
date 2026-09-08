from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Landmark(BaseModel):
    id: str
    class_label: str
    x: float
    y: float
    confidence: float
    seen_count: int
    stale: bool


class RobotPose(BaseModel):
    x: float
    y: float
    yaw: float


class ScanSnapshot(BaseModel):
    angle_min: float
    angle_increment: float
    ranges: list[float]


class MapOrigin(BaseModel):
    x: float
    y: float
    yaw: float


class MapData(BaseModel):
    width: int
    height: int
    resolution: float
    origin: MapOrigin
    data: str  # base64-encoded int8 array (-1=unknown, 0=free, 100=occupied)


class StateMessage(BaseModel):
    timestamp: float
    robot_pose: Optional[RobotPose]
    landmarks: list[Landmark]
    scan: Optional[ScanSnapshot]


class HealthResponse(BaseModel):
    ros_connected: bool
    last_landmark_msg: Optional[datetime]
    landmark_count: int
    robot_pose: Optional[RobotPose]


class LandmarkList(BaseModel):
    landmarks: list[Landmark]
