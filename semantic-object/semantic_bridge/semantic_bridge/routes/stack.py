"""Operator console: the stack's state, its logs, and the few things you may
do to it from a browser.

Every mutating route is a thin wrapper over supervisor.py, which is a thin
wrapper over tmux. Nothing here owns a process.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect

from ..supervisor import SupervisorError

logger = logging.getLogger(__name__)
router = APIRouter()

# Set by main.py's lifespan. None means the console is not available (mock
# mode, or a bridge running somewhere without the workspace).
_supervisor = None


def set_supervisor(sup) -> None:
    global _supervisor
    _supervisor = sup


def _sup():
    if _supervisor is None:
        raise HTTPException(status_code=503,
                            detail="stack console unavailable in this bridge")
    return _supervisor


@router.get("")
async def stack_state() -> dict:
    sup = _sup()
    return await sup.refresh()


@router.get("/profiles")
async def profiles() -> dict:
    sup = _sup()
    out = {}
    for name in ("demo", "mapping", "bench"):
        try:
            out[name] = await sup.profile(name)
        except SupervisorError:
            pass
    return {"profiles": out}


@router.post("/up")
async def stack_up(profile: str = Query("demo")) -> dict:
    """Ordered, gated bring-up. Returns at once; watch /ws/stack for progress.

    It is a background task rather than a blocking call because a cold `demo`
    profile is a minute and a half of starting and gating, and an HTTP request
    that hangs that long is one the browser, a proxy, or an impatient operator
    will kill halfway through -- leaving a half-started stack and no progress
    anywhere.
    """
    sup = _sup()
    try:
        await sup.profile(profile)
    except SupervisorError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    asyncio.create_task(_guarded(sup.start_profile(profile)))
    return {"status": "starting", "profile": profile}


@router.post("/down")
async def stack_down(profile: str = Query("demo")) -> dict:
    sup = _sup()
    asyncio.create_task(_guarded(sup.stop_profile(profile)))
    return {"status": "stopping", "profile": profile}


async def _guarded(coro) -> None:
    try:
        await coro
    except Exception as exc:                            # noqa: BLE001
        logger.exception("stack task failed: %s", exc)


@router.post("/{name}/{action}")
async def component_action(name: str, action: str) -> dict:
    sup = _sup()
    if action not in ("start", "stop", "restart"):
        raise HTTPException(status_code=404, detail=f"no action {action!r}")
    try:
        return await getattr(sup, action)(name)
    except SupervisorError as exc:
        # 409: the request was well-formed, the stack simply is not in a state
        # where it makes sense -- "already running", "not restartable".
        raise HTTPException(status_code=409, detail=str(exc))


@router.get("/{name}/logs")
async def component_logs(name: str, lines: int = Query(200, ge=1, le=2000)) -> dict:
    sup = _sup()
    return {"component": name, "text": await sup.logs(name, lines)}


@router.websocket("/ws")
async def ws_stack(ws: WebSocket) -> None:
    """Pushes the whole snapshot whenever the poller produces one."""
    await ws.accept()
    if _supervisor is None:
        await ws.send_json({"error": "stack console unavailable"})
        await ws.close()
        return

    q: asyncio.Queue = asyncio.Queue(maxsize=2)
    _supervisor.register(q)
    try:
        await ws.send_json(_supervisor.snapshot())
        while True:
            await ws.send_json(await q.get())
    except WebSocketDisconnect:
        pass
    except Exception as exc:                            # noqa: BLE001
        logger.warning("/ws/stack error: %s", exc)
    finally:
        _supervisor.unregister(q)


@router.websocket("/ws/logs")
async def ws_logs(ws: WebSocket, component: str = Query(...)) -> None:
    """Tail one component.

    Sends the whole visible buffer, but only when it has actually changed --
    a pane that is quiet costs nothing, and a pane that is scrolling costs one
    send per second rather than one per line. Diffing tmux's scrollback
    properly is not worth it for a few hundred lines.
    """
    await ws.accept()
    if _supervisor is None:
        await ws.send_json({"error": "stack console unavailable"})
        await ws.close()
        return

    last = None
    try:
        while True:
            text = await _supervisor.logs(component)
            digest = hashlib.sha1(text.encode("utf-8", "replace")).hexdigest()
            if digest != last:
                await ws.send_json({"component": component, "text": text})
                last = digest
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        pass
    except Exception as exc:                            # noqa: BLE001
        logger.warning("/ws/logs error: %s", exc)
