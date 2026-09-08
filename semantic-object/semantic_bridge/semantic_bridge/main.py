from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routes.rest import router as rest_router
from .routes.websocket import router as ws_router
from .state import _app_state as app_state

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

_ros_manager = None


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

    yield

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


def run() -> None:
    uvicorn.run(
        "semantic_bridge.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )
