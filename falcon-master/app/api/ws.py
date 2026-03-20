from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from sqlalchemy import Select, false

from app.core.security import verify_access_token
from app.db import SessionLocal
from app.decorators.audit import set_current_user
from app.models import Tasks
from app.services.access_control_service import AccessControlService
from app.services.task_runtime_ws_service import task_runtime_ws_manager


router = APIRouter(prefix="/ws", tags=["WebSocket"])


@router.websocket("/task/{task_id}")
async def task_runtime_socket(websocket: WebSocket, task_id: int) -> None:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")
        return

    payload = verify_access_token(token)
    if not payload:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        return

    db = SessionLocal()
    try:
        set_current_user(payload.id, payload.username)
        task = db.execute(
            Select(Tasks).where(
                Tasks.id == task_id,
                Tasks.is_deleted == false(),
            )
        ).scalar_one_or_none()
        if not task:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Task not found")
            return

        AccessControlService(db).ensure_project_view_access(task.project_id)
        await task_runtime_ws_manager.connect(task_id=task_id, websocket=websocket)
        await websocket.send_json(
            {
                "channel": "task_runtime",
                "event": "connected",
                "task_id": task_id,
                "timestamp": None,
                "data": {"task_run_id": None, "status": str(task.status)},
            }
        )

        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await task_runtime_ws_manager.disconnect(task_id=task_id, websocket=websocket)
        db.close()
