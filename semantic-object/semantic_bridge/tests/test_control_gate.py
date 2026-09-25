"""The goal gate's map arithmetic. No ROS, no network, no rclpy.

Worth its own file because the failure is silent and geometric: a row/column
swap or a sign error still returns "free" for SOME points, so it passes a
casual click test and then refuses goals on one half of the room, or accepts
one into a wall. OccupancyGrid is row-major with row 0 at the ORIGIN, i.e. the
bottom, which is the part people get backwards.
"""

from __future__ import annotations

import base64

import pytest
from fastapi import HTTPException

from semantic_bridge.models import MapData, MapOrigin
from semantic_bridge.routes.control import _require_free_cell
from semantic_bridge.state import AppState


def make_state(cells: list[int], width: int, height: int,
               res: float = 1.0, ox: float = -2.0, oy: float = -1.0) -> AppState:
    state = AppState()
    state.update_map(MapData(
        width=width, height=height, resolution=res,
        origin=MapOrigin(x=ox, y=oy, yaw=0.0),
        data=base64.b64encode(bytes(c & 0xFF for c in cells)).decode(),
    ))
    return state


#   row2 (y in [1,2)):  -1  -1  -1  -1     unknown
#   row1 (y in [0,1)):   0   0 100   0     one obstacle
#   row0 (y in [-1,0)):  0   0   0   0     free
GRID = [0, 0, 0, 0,  0, 0, 100, 0,  -1, -1, -1, -1]


@pytest.fixture
def state() -> AppState:
    return make_state(GRID, width=4, height=3)


@pytest.mark.parametrize("x,y", [(-1.5, -0.5), (1.5, -0.5), (-1.5, 0.5)])
def test_free_cells_accepted(state: AppState, x: float, y: float) -> None:
    _require_free_cell(state, x, y)          # must not raise


def test_occupied_cell_refused(state: AppState) -> None:
    with pytest.raises(HTTPException) as exc:
        _require_free_cell(state, 0.5, 0.5)
    assert exc.value.status_code == 409
    assert "occupied" in exc.value.detail


def test_unknown_cell_refused(state: AppState) -> None:
    """-1 is unknown. Sending Nav2 there is how a demo goal times out."""
    with pytest.raises(HTTPException) as exc:
        _require_free_cell(state, -1.5, 1.5)
    assert "unmapped" in exc.value.detail


@pytest.mark.parametrize("x,y", [(9.0, 0.0), (-9.0, 0.0), (0.0, 9.0), (0.0, -9.0)])
def test_outside_the_grid_refused(state: AppState, x: float, y: float) -> None:
    with pytest.raises(HTTPException) as exc:
        _require_free_cell(state, x, y)
    assert "outside" in exc.value.detail


def test_no_map_refused() -> None:
    with pytest.raises(HTTPException) as exc:
        _require_free_cell(AppState(), 0.0, 0.0)
    assert "no map" in exc.value.detail


def test_rows_are_not_transposed() -> None:
    """A width != height grid catches a row/col swap; a square one cannot.

    3 wide, 2 tall, obstacle at row 0 col 2 -> world (0.5, -0.5). If the
    indexing were transposed the obstacle would appear somewhere else and this
    point would read free.
    """
    cells = [0, 0, 100,
             0, 0, 0]
    state = make_state(cells, width=3, height=2, ox=-2.0, oy=-1.0)
    with pytest.raises(HTTPException) as exc:
        _require_free_cell(state, 0.5, -0.5)
    assert "occupied" in exc.value.detail
    _require_free_cell(state, 0.5, 0.5)      # the transposed spot IS free
