"""Driving and goals from the browser, with the gates that make them safe.

Three rules are enforced here rather than in the UI, because a UI check is a
suggestion:

  1. NOTHING DRIVES UNLESS `nav` IS READY. twist_mux and teleop_speed_guard are
     both launched by navigation.launch.py, so without it nothing subscribes to
     /cmd_vel_teleop_raw and the robot would not move anyway -- but worse, the
     clamp and the priority that make browser driving safe are the thing that
     is missing. The UI greys the pad out; this refuses it.

  2. ONE DRIVER. Two tabs each sending 20 Hz of {vx, wz} is last-writer-wins
     between two people who cannot see each other. The first socket holds
     control; the second is told so and gets nothing.

  3. NO GOALS WHILE `explore` IS RUNNING. explore_lite sends its own
     NavigateToPose goals continuously and will override a manual one within a
     second or two. From the UI the two are indistinguishable, so the goal
     looks accepted, nothing happens, and the robot wanders off.

Entering manual driving CANCELS any active goal first: manual is exclusive,
and a pad that fights an autonomous run is the `make teleop` mistake in a new
costume.
"""

from __future__ import annotations

import base64
import logging
import math

from fastapi import (APIRouter, Depends, HTTPException, WebSocket,
                     WebSocketDisconnect)
from pydantic import BaseModel

from ..config import settings
from ..state import AppState, get_state

logger = logging.getLogger(__name__)
router = APIRouter()

_manager = None          # ControlManager, set by main.py
_driver = None           # the WebSocket currently holding control


def set_manager(manager) -> None:
    global _manager
    _manager = manager


def _control():
    if _manager is None or _manager.control is None:
        raise HTTPException(status_code=503,
                            detail="control node unavailable (no ROS?)")
    if not settings.teleop_enabled:
        raise HTTPException(status_code=403,
                            detail="control is disabled (CAP_TELEOP_ENABLED=0)")
    return _manager.control


def _component_state(name: str) -> tuple[str, bool]:
    from .stack import _supervisor
    if _supervisor is None:
        return "unknown", False
    for comp in _supervisor.snapshot()["components"]:
        if comp["name"] == name:
            return comp["state"], bool(comp["ready"])
    return "stopped", False


def _require_nav() -> None:
    state, ready = _component_state("nav")
    if not ready:
        raise HTTPException(
            status_code=409,
            detail=(f"nav is {state}, not ready. twist_mux and "
                    "teleop_speed_guard live in navigation.launch.py, so "
                    "without it nothing receives a drive command and there is "
                    "no speed clamp and no priority over Nav2."))


class GoalRequest(BaseModel):
    x: float
    y: float
    yaw: float = 0.0


class LimitRequest(BaseModel):
    max_linear: float
    max_angular: float


@router.get("/control")
async def control_status() -> dict:
    nav_state, nav_ready = _component_state("nav")
    explore_state, _ = _component_state("explore")
    body = {
        "enabled": settings.teleop_enabled,
        "available": _manager is not None and _manager.control is not None,
        "nav_state": nav_state,
        "nav_ready": nav_ready,
        "explore_state": explore_state,
        "can_drive": nav_ready and settings.teleop_enabled,
        "can_goal": nav_ready and explore_state == "stopped",
        "held": _driver is not None,
    }
    if _manager is not None and _manager.control is not None:
        body.update(_manager.control.status())
    return body


@router.post("/control/limits")
async def set_limits(req: LimitRequest) -> dict:
    return _control().set_limits(req.max_linear, req.max_angular)


@router.post("/goal")
async def send_goal(req: GoalRequest, state: AppState = Depends(get_state)) -> dict:
    control = _control()
    _require_nav()

    explore_state, _ = _component_state("explore")
    if explore_state != "stopped":
        raise HTTPException(
            status_code=409,
            detail=("explore is running and sends its own goals continuously; "
                    "it would override this one within seconds. Stop explore "
                    "first."))

    _require_free_cell(state, req.x, req.y)
    try:
        return control.send_goal(req.x, req.y, req.yaw)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post("/goal/cancel")
async def cancel_goal() -> dict:
    return {"cancelled": _control().cancel_goal()}


def _require_free_cell(state: AppState, x: float, y: float) -> None:
    """Refuse a goal that is not on a known-free cell of the map we hold.

    Nav2 would refuse it too, eventually, after planning and a recovery
    behaviour or two -- by which point the operator has watched the robot spin
    for half a minute in front of an audience. The bridge already has the
    decoded grid, so this costs nothing.
    """
    grid = state.snapshot_map()
    if grid is None:
        raise HTTPException(status_code=409,
                            detail="no map yet -- is slam running?")
    cos_t, sin_t = math.cos(grid.origin.yaw), math.sin(grid.origin.yaw)
    dx, dy = x - grid.origin.x, y - grid.origin.y
    col = int((dx * cos_t + dy * sin_t) / grid.resolution)
    row = int((-dx * sin_t + dy * cos_t) / grid.resolution)
    if not (0 <= col < grid.width and 0 <= row < grid.height):
        raise HTTPException(status_code=409,
                            detail="that point is outside the mapped area")
    cells = base64.b64decode(grid.data)
    value = cells[row * grid.width + col]
    if value > 127:                       # int8 came through as unsigned
        value -= 256
    if value < 0:
        raise HTTPException(status_code=409,
                            detail="that cell is unmapped -- drive there first")
    if value >= 50:
        raise HTTPException(status_code=409,
                            detail="that cell is occupied")


@router.post("/estop")
async def estop() -> dict:
    """Stop `nav`, which is a designed-in safe state rather than a message.

    teleop_speed_guard's own docstring makes the argument: it has
    on_exit=Shutdown, so taking navigation down takes twist_mux,
    controller_server and velocity_smoother with it; nothing is left
    publishing to /diff_cont/cmd_vel_unstamped, and diff_drive_controller
    halts the wheels when commands stop arriving. That is stronger and more
    certain than any Twist this process can publish, and it cannot be undone
    by a stale message already in flight.

    It is still not THE e-stop. The e-stop is `make teleop-nav`, on a keyboard,
    on a wire.
    """
    from .stack import _supervisor
    if _manager is not None and _manager.control is not None:
        _manager.control.release()
    if _supervisor is None:
        raise HTTPException(status_code=503, detail="stack console unavailable")
    try:
        await _supervisor.stop("nav")
    except Exception as exc:                            # noqa: BLE001
        raise HTTPException(status_code=409, detail=str(exc))
    return {"status": "nav stopped",
            "note": "twist_mux and the speed guard went with it; the wheels "
                    "halt on diff_cont's cmd_vel_timeout."}


@router.websocket("/teleop")
async def ws_teleop(ws: WebSocket) -> None:
    global _driver
    await ws.accept()

    if _manager is None or _manager.control is None or not settings.teleop_enabled:
        await ws.send_json({"error": "control unavailable"})
        await ws.close()
        return

    _, nav_ready = _component_state("nav")
    if not nav_ready:
        await ws.send_json({"error": "nav is not ready; nothing would receive "
                                     "a drive command and there would be no "
                                     "speed clamp"})
        await ws.close()
        return

    if _driver is not None:
        await ws.send_json({"error": "someone else is driving"})
        await ws.close()
        return

    _driver = ws
    control = _manager.control
    # Manual is exclusive: a pad that fights an autonomous run is exactly the
    # `make teleop` mistake the Makefile warns about.
    control.cancel_goal()
    logger.info("teleop: control taken by %s", ws.client)

    try:
        await ws.send_json({"status": "driving", **control.status()})
        while True:
            msg = await ws.receive_json()
            if msg.get("stop"):
                control.release()
                await ws.send_json({"status": "released"})
                continue
            await ws.send_json(control.set_command(
                float(msg.get("vx", 0.0)), float(msg.get("wz", 0.0))))
    except WebSocketDisconnect:
        pass
    except Exception as exc:                            # noqa: BLE001
        logger.warning("/ws/teleop error: %s", exc)
    finally:
        # Do not wait out the 300 ms staleness timer: we KNOW the driver is
        # gone, so start stopping immediately.
        control.release()
        _driver = None
        logger.info("teleop: control released")
