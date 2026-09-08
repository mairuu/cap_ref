from __future__ import annotations

import asyncio
import logging
import math
import time

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from ..models import StateMessage
from ..state import AppState, get_state

logger = logging.getLogger(__name__)
router = APIRouter()

def sanitize_floats(obj):
    if isinstance(obj, float):
        if math.isinf(obj) or math.isnan(obj):
            return 1000 # sentinel
    if isinstance(obj, dict):
        return {k: sanitize_floats(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_floats(v) for v in obj]
    return obj

@router.websocket("/state")
async def ws_state(ws: WebSocket, state: AppState = Depends(get_state)) -> None:
    await ws.accept()
    logger.info("Client connected: /ws/state  remote=%s", ws.client)
    interval = state._ws_interval_s if hasattr(state, "_ws_interval_s") else 0.2

    try:
        while True:
            tick_start = asyncio.get_event_loop().time()
            snap = state.snapshot()
            msg = StateMessage(
                timestamp=time.time(),
                robot_pose=snap["pose"],
                landmarks=snap["landmarks"],
                scan=snap["scan"],
            )
            await ws.send_json(sanitize_floats(msg.model_dump()))
            elapsed = asyncio.get_event_loop().time() - tick_start
            await asyncio.sleep(max(0.0, interval - elapsed))
    except WebSocketDisconnect:
        logger.info("Client disconnected: /ws/state  remote=%s", ws.client)
    except Exception as exc:
        logger.warning("/ws/state error: %s", exc)


@router.websocket("/camera")
async def ws_camera(ws: WebSocket, state: AppState = Depends(get_state)) -> None:
    await ws.accept()
    logger.info("Client connected: /ws/camera  remote=%s", ws.client)

    # maxsize=2: hold at most the two newest frames; older frames are dropped
    # when the client is slower than the source (see state.broadcast_camera).
    q: asyncio.Queue[bytes] = asyncio.Queue(maxsize=2)
    state.register_camera_queue(q)

    try:
        while True:
            frame = await q.get()
            await ws.send_bytes(frame)
    except WebSocketDisconnect:
        logger.info("Client disconnected: /ws/camera  remote=%s", ws.client)
    except Exception as exc:
        logger.warning("/ws/camera error: %s", exc)
    finally:
        state.unregister_camera_queue(q)
