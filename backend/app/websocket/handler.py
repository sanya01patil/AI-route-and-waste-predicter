from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import asyncio
from datetime import datetime

router = APIRouter(tags=["websockets"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

@router.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    await websocket.send_json({
        "type": "connection",
        "message": "Connected to EcoChain AI Live Traffic Stream",
        "timestamp": datetime.utcnow().timestamp() * 1000
    })
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def live_traffic_simulator():
    import random
    events = [
        {"type": "alert", "icon": "🚧", "area": "Highway A1", "desc": "Lane closure due to maintenance", "severity": "moderate"},
        {"type": "alert", "icon": "🛑", "area": "Downtown Intersection", "desc": "Recent accident reported", "severity": "high"},
        {"type": "alert", "icon": "☔", "area": "City Limits", "desc": "Wet road conditions", "severity": "low"},
        {"type": "clear", "icon": "✅", "area": "Expressway South", "desc": "Traffic cleared", "severity": "low"}
    ]
    while True:
        await asyncio.sleep(random.randint(15, 30))
        event = random.choice(events)
        event["timestamp"] = datetime.utcnow().timestamp() * 1000
        await manager.broadcast(json.dumps(event))
