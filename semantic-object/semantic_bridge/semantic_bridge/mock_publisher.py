"""
Synthetic data publisher for SEMANTIC_BRIDGE_MOCK=1 mode.

Runs as an asyncio task inside the FastAPI event loop — no ROS2 required.
The robot traces a slow circle; three fixed landmarks are present from the start.
"""

from __future__ import annotations

import asyncio
import logging
import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .state import AppState

logger = logging.getLogger(__name__)

_MOCK_LANDMARKS_RAW = [
    {
        "id": "mock-chair-1",
        "class_label": "chair",
        "x": 1.5,
        "y": 2.0,
        "confidence": 0.92,
        "seen_count": 10,
        "stale": False,
    },
    {
        "id": "mock-table-1",
        "class_label": "table",
        "x": -1.0,
        "y": 1.5,
        "confidence": 0.85,
        "seen_count": 7,
        "stale": False,
    },
    {
        "id": "mock-door-1",
        "class_label": "door",
        "x": 3.0,
        "y": 0.0,
        "confidence": 0.78,
        "seen_count": 3,
        "stale": True,
    },
]


async def run_mock_publisher(state: AppState) -> None:
    from .models import Landmark, RobotPose, ScanSnapshot

    logger.info("Mock publisher started (SEMANTIC_BRIDGE_MOCK=1)")
    state.set_ros_connected(True)
    state.update_landmarks([Landmark(**lm) for lm in _MOCK_LANDMARKS_RAW])

    scan_rays = 180
    t = 0.0

    while True:
        # Robot traces a 2 m radius circle at 0.1 rad/s
        x = 2.0 * math.cos(t * 0.1)
        y = 2.0 * math.sin(t * 0.1)
        yaw = t * 0.1 + math.pi / 2
        state.update_pose(RobotPose(x=x, y=y, yaw=yaw))

        # Lidar: mostly uniform range with a gentle sine ripple
        ranges = [
            max(0.1, 2.0 + 0.2 * math.sin(i * 0.07 + t * 0.3))
            for i in range(scan_rays)
        ]
        state.update_scan(
            ScanSnapshot(
                angle_min=-math.pi,
                angle_increment=2 * math.pi / scan_rays,
                ranges=ranges,
            )
        )

        frame = _make_mock_frame(t)
        if frame:
            await state.broadcast_camera_async(frame)

        t += 0.1
        await asyncio.sleep(0.1)


def _make_mock_frame(t: float) -> bytes:
    try:
        import io

        from PIL import Image, ImageDraw, ImageFont

        r = int(128 + 127 * math.sin(t * 0.3))
        g = int(80 + 40 * math.cos(t * 0.2))
        img = Image.new("RGB", (320, 240), color=(r, g, 120))
        draw = ImageDraw.Draw(img)
        draw.text((8, 8), f"MOCK  t={t:.1f}s", fill=(255, 255, 255))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=70)
        return buf.getvalue()
    except ImportError:
        # Pillow not installed — camera stream stays silent in mock mode
        return b""
