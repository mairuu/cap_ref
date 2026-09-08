from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..models import HealthResponse, LandmarkList, MapData
from ..state import AppState, get_state

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health(state: AppState = Depends(get_state)) -> HealthResponse:
    snap = state.snapshot()
    return HealthResponse(
        ros_connected=snap["ros_connected"],
        last_landmark_msg=snap["last_landmark_msg"],
        landmark_count=snap["landmark_count"],
        robot_pose=snap["pose"],
    )


@router.get("/landmarks", response_model=LandmarkList)
async def landmarks(state: AppState = Depends(get_state)) -> LandmarkList:
    snap = state.snapshot()
    return LandmarkList(landmarks=snap["landmarks"])


@router.get("/map", response_model=MapData)
async def map_snapshot(state: AppState = Depends(get_state)) -> MapData:
    map_data = state.snapshot_map()
    if map_data is None:
        raise HTTPException(status_code=503, detail="Map not yet received from ROS")
    return map_data


@router.post("/clear")
async def clear_landmarks(state: AppState = Depends(get_state)) -> dict:
    snap = state.snapshot()
    if not snap["ros_connected"]:
        raise HTTPException(status_code=503, detail="ROS not connected")
    success = await state.call_clear_service()
    if not success:
        raise HTTPException(
            status_code=503, detail="clear_landmarks service unavailable or timed out"
        )
    return {"status": "ok"}
