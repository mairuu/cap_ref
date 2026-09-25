from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastapi.staticfiles import StaticFiles

from .config import settings
from .routes.control import router as control_router
from .routes.control import set_manager
from .routes.rest import router as rest_router
from .routes.stack import router as stack_router
from .routes.stack import set_supervisor
from .routes.websocket import router as ws_router
from .state import _app_state as app_state

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

_ros_manager = None
_supervisor = None
_control_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _ros_manager

    # Give the state access to this event loop so ROS callbacks can cross
    # the thread boundary via call_soon_threadsafe.
    app_state._event_loop = asyncio.get_running_loop()
    # Make the WS interval available to the websocket handler without
    # importing config there (keeps the handler testable).
    app_state._ws_interval_s = settings.state_ws_interval_ms / 1000.0

    if settings.mock:
        logger.info("Starting in mock mode (SEMANTIC_BRIDGE_MOCK=1)")
        from .mock_publisher import run_mock_publisher

        task = asyncio.create_task(run_mock_publisher(app_state))
    else:
        from .ros_node import RosManager

        _ros_manager = RosManager(app_state, settings)
        _ros_manager.start()

        # Driving and goals live on a SEPARATE node with its own executor
        # thread. RosManager spins single-threaded next to _on_map, which
        # base64-encodes a whole OccupancyGrid; a 20 Hz timer on the safety
        # path must not queue behind that.
        global _control_manager
        from .control_node import ControlManager

        _control_manager = ControlManager()
        _control_manager.start()
        set_manager(_control_manager)

    # The operator console. Only when there is a workspace to drive: a bridge
    # running against a bag replay, or in mock mode on a laptop, has no
    # business offering buttons that start motors.
    global _supervisor
    if settings.stack_enabled and not settings.mock and settings.cap_ws.is_dir():
        from .supervisor import Supervisor

        _supervisor = Supervisor(settings)
        set_supervisor(_supervisor)
        _supervisor.start_poller()
        logger.info("Stack console enabled (tmux session %r, workspace %s)",
                    settings.tmux_session, settings.cap_ws)
        if not os.environ.get("ROS_DOMAIN_ID"):
            # Not fatal -- the console still shows state. But starting anything
            # would land it on domain 0, invisible to everything else, so say
            # so once at boot rather than only at the first failed click.
            logger.warning(
                "ROS_DOMAIN_ID is unset: the console can show the stack but "
                "will refuse to start anything. Run the bridge from a login "
                "shell (`make bridge`).")
    else:
        logger.info("Stack console disabled (enabled=%s, mock=%s, cap_ws=%s)",
                    settings.stack_enabled, settings.mock, settings.cap_ws)

    yield

    if _supervisor is not None:
        await _supervisor.stop_poller()
    if _control_manager is not None:
        # Releases the teleop channel and lets the stop go out before the
        # process leaves.
        _control_manager.stop()

    if settings.mock:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    else:
        if _ros_manager is not None:
            _ros_manager.stop()


app = FastAPI(title="semantic_bridge", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rest_router, prefix="/api")
app.include_router(ws_router, prefix="/ws")
app.include_router(stack_router, prefix="/api/stack")
app.include_router(control_router, prefix="/api")
app.include_router(control_router, prefix="/ws")

# The built UI, served at /app as an ADDITION to the Vite dev server on 3000,
# not a replacement for it.
#
# Serving it only from here would couple the page's availability to this
# process and make every UI tweak a `npm run build` on a Jetson plus a bridge
# restart. /app is the one-port option -- useful from a phone, and immune to
# the VITE_BACKEND_URL staleness that has cost three debugging sessions -- and
# `make ui` stays the demo path.
#
# Mounted LAST so /api and /ws still route: a mount is matched after the
# routers above, but only because they are registered first.
if settings.ui_dist.is_dir():
    app.mount("/app", StaticFiles(directory=str(settings.ui_dist), html=True),
              name="ui")
else:
    logger.info("No UI build at %s -- /app not mounted (run `make ui-build`)",
                settings.ui_dist)


def run() -> None:
    uvicorn.run(
        "semantic_bridge.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )
