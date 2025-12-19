"""
WebSocket API for Real-time Updates

Provides real-time communication for:
- Analysis progress updates
- Pipeline job status
- Live notifications
"""

import asyncio
import json
import logging
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


class ConnectionManager:
    """Manages WebSocket connections and broadcasting."""

    def __init__(self):
        # Active connections by channel
        self.active_connections: dict[str, list[WebSocket]] = {}
        # General broadcast connections
        self.broadcast_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket, channel: Optional[str] = None):
        """Accept a new WebSocket connection."""
        await websocket.accept()

        if channel:
            if channel not in self.active_connections:
                self.active_connections[channel] = []
            self.active_connections[channel].append(websocket)
            logger.info(f"WebSocket connected to channel: {channel}")
        else:
            self.broadcast_connections.append(websocket)
            logger.info("WebSocket connected to broadcast")

    def disconnect(self, websocket: WebSocket, channel: Optional[str] = None):
        """Remove a WebSocket connection."""
        if channel and channel in self.active_connections:
            if websocket in self.active_connections[channel]:
                self.active_connections[channel].remove(websocket)
                if not self.active_connections[channel]:
                    del self.active_connections[channel]
        elif websocket in self.broadcast_connections:
            self.broadcast_connections.remove(websocket)
        logger.info("WebSocket disconnected")

    async def send_to_channel(self, channel: str, message: dict):
        """Send a message to all connections in a channel."""
        if channel in self.active_connections:
            dead_connections = []
            for connection in self.active_connections[channel]:
                try:
                    await connection.send_json(message)
                except Exception:
                    dead_connections.append(connection)

            # Clean up dead connections
            for conn in dead_connections:
                self.disconnect(conn, channel)

    async def broadcast(self, message: dict):
        """Broadcast a message to all general connections."""
        dead_connections = []
        for connection in self.broadcast_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.append(connection)

        # Clean up dead connections
        for conn in dead_connections:
            self.disconnect(conn)

    async def send_personal(self, websocket: WebSocket, message: dict):
        """Send a message to a specific connection."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")


# Singleton connection manager
manager = ConnectionManager()


def get_connection_manager() -> ConnectionManager:
    """Get the singleton connection manager."""
    return manager


# =============================================================================
# WebSocket Endpoints
# =============================================================================

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    General WebSocket endpoint for broadcast messages.

    Receives system-wide notifications and updates.
    """
    await manager.connect(websocket)
    try:
        # Send welcome message
        await manager.send_personal(websocket, {
            "type": "connected",
            "message": "Connected to DSRP Canvas",
            "timestamp": datetime.utcnow().isoformat(),
        })

        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                # Handle ping/pong for keepalive
                if message.get("type") == "ping":
                    await manager.send_personal(websocket, {
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat(),
                    })
            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.websocket("/ws/analysis/{concept_id}")
async def analysis_websocket(websocket: WebSocket, concept_id: str):
    """
    WebSocket for tracking analysis progress on a specific concept.

    Sends updates like:
    - {"type": "progress", "stage": "extracting", "percent": 25}
    - {"type": "result", "data": {...}}
    - {"type": "error", "message": "..."}
    """
    channel = f"analysis:{concept_id}"
    await manager.connect(websocket, channel)

    try:
        await manager.send_personal(websocket, {
            "type": "subscribed",
            "channel": channel,
            "concept_id": concept_id,
            "timestamp": datetime.utcnow().isoformat(),
        })

        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await manager.send_personal(websocket, {"type": "pong"})
            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)


@router.websocket("/ws/job/{job_id}")
async def job_websocket(websocket: WebSocket, job_id: str):
    """
    WebSocket for tracking pipeline job progress.

    Sends updates like:
    - {"type": "progress", "stage": "parsing", "percent": 10, "message": "..."}
    - {"type": "chunk", "index": 5, "total": 20}
    - {"type": "complete", "result": {...}}
    - {"type": "error", "message": "..."}
    """
    channel = f"job:{job_id}"
    await manager.connect(websocket, channel)

    try:
        await manager.send_personal(websocket, {
            "type": "subscribed",
            "channel": channel,
            "job_id": job_id,
            "timestamp": datetime.utcnow().isoformat(),
        })

        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await manager.send_personal(websocket, {"type": "pong"})
            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)


# =============================================================================
# Helper Functions for Sending Updates
# =============================================================================

async def notify_analysis_progress(
    concept_id: str,
    stage: str,
    percent: int,
    message: Optional[str] = None,
):
    """Send analysis progress update to subscribers."""
    await manager.send_to_channel(f"analysis:{concept_id}", {
        "type": "progress",
        "stage": stage,
        "percent": percent,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
    })


async def notify_analysis_complete(concept_id: str, result: dict):
    """Send analysis completion to subscribers."""
    await manager.send_to_channel(f"analysis:{concept_id}", {
        "type": "complete",
        "result": result,
        "timestamp": datetime.utcnow().isoformat(),
    })


async def notify_analysis_error(concept_id: str, error: str):
    """Send analysis error to subscribers."""
    await manager.send_to_channel(f"analysis:{concept_id}", {
        "type": "error",
        "message": error,
        "timestamp": datetime.utcnow().isoformat(),
    })


async def notify_job_progress(
    job_id: str,
    stage: str,
    percent: int,
    message: Optional[str] = None,
    current: Optional[int] = None,
    total: Optional[int] = None,
):
    """Send job progress update to subscribers."""
    payload = {
        "type": "progress",
        "stage": stage,
        "percent": percent,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
    }
    if current is not None:
        payload["current"] = current
    if total is not None:
        payload["total"] = total

    await manager.send_to_channel(f"job:{job_id}", payload)


async def notify_job_complete(job_id: str, result: dict):
    """Send job completion to subscribers."""
    await manager.send_to_channel(f"job:{job_id}", {
        "type": "complete",
        "result": result,
        "timestamp": datetime.utcnow().isoformat(),
    })


async def notify_job_error(job_id: str, error: str):
    """Send job error to subscribers."""
    await manager.send_to_channel(f"job:{job_id}", {
        "type": "error",
        "message": error,
        "timestamp": datetime.utcnow().isoformat(),
    })


async def broadcast_notification(notification_type: str, data: dict):
    """Broadcast a notification to all connected clients."""
    await manager.broadcast({
        "type": "notification",
        "notification_type": notification_type,
        "data": data,
        "timestamp": datetime.utcnow().isoformat(),
    })
