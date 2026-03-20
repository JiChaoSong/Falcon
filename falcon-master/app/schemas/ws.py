from typing import Dict, Set, List, Optional, Any

from pydantic import BaseModel
from fastapi import WebSocket

class WSMetricsData(BaseModel):
    task_id: str
    timestamp: float
    metrics: Dict[str, Any]
    channel: str = "metrics"


class WSStateData(BaseModel):
    task_id: str
    timestamp: float
    state: str
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    channel: str = "state"

class WSLogData(BaseModel):
    task_id: str
    timestamp: float
    level: str
    message: str
    source: Optional[str] = None
    channel: str = "log"

class WSConnectionInfo(BaseModel):
    websocket: WebSocket
    task_id: str
    channels: List[str]
    connected_at: float
    last_active: float
    client_info: Optional[Dict[str, Any]] = None


class WSConnectRequest(BaseModel):
    task_id: str
    channels: List[str] = ["metrics", "state", "log"]