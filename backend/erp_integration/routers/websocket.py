"""WebSocket endpoint for real-time job progress updates."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import asyncio
import json
from task_status import job_store

router = APIRouter(tags=["WebSocket"])

# Store active WebSocket connections
active_connections: Dict[str, Set[WebSocket]] = {}


class ConnectionManager:
    """Manage WebSocket connections for job updates."""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, job_id: str, websocket: WebSocket):
        """Connect a WebSocket to a job."""
        await websocket.accept()
        
        if job_id not in self.active_connections:
            self.active_connections[job_id] = set()
        
        self.active_connections[job_id].add(websocket)
    
    def disconnect(self, job_id: str, websocket: WebSocket):
        """Disconnect a WebSocket."""
        if job_id in self.active_connections:
            self.active_connections[job_id].discard(websocket)
            
            # Clean up empty sets
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]
    
    async def broadcast_to_job(self, job_id: str, message: dict):
        """Broadcast message to all connections for a job."""
        if job_id not in self.active_connections:
            return
        
        # Send to all connected clients
        disconnected = set()
        for connection in self.active_connections[job_id]:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(job_id, connection)


manager = ConnectionManager()


@router.websocket("/ws/jobs/{job_id}")
async def websocket_job_updates(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint for real-time job progress.
    
    Client connects and receives updates whenever job status changes.
    
    Message format:
    {
        "job_id": "uuid",
        "status": "processing",
        "progress": 45,
        "message": "Processing module: energy",
        "result": null,
        "error": null
    }
    """
    await manager.connect(job_id, websocket)
    
    try:
        # Send initial job status
        job = await job_store.get_job(job_id)
        if job:
            await websocket.send_json({
                "type": "status",
                "job_id": job_id,
                "status": job["status"],
                "progress": job.get("progress", 0),
                "result": job.get("result"),
                "error": job.get("error")
            })
        else:
            await websocket.send_json({
                "type": "error",
                "message": "Job not found"
            })
            await websocket.close()
            return
        
        # Poll for updates and send to client
        last_status = job["status"]
        last_progress = job.get("progress", 0)
        
        while True:
            # Check if job is complete
            if last_status in ["completed", "failed"]:
                await websocket.send_json({
                    "type": "complete",
                    "job_id": job_id,
                    "status": last_status,
                    "progress": 100 if last_status == "completed" else last_progress,
                    "result": job.get("result"),
                    "error": job.get("error")
                })
                break
            
            # Wait and check for updates
            await asyncio.sleep(2)
            
            job = await job_store.get_job(job_id)
            if not job:
                break
            
            # Send update if status or progress changed
            if job["status"] != last_status or job.get("progress", 0) != last_progress:
                await websocket.send_json({
                    "type": "update",
                    "job_id": job_id,
                    "status": job["status"],
                    "progress": job.get("progress", 0),
                    "result": job.get("result"),
                    "error": job.get("error")
                })
                
                last_status = job["status"]
                last_progress = job.get("progress", 0)
    
    except WebSocketDisconnect:
        manager.disconnect(job_id, websocket)
    
    except Exception as e:
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass
        manager.disconnect(job_id, websocket)


async def notify_job_update(job_id: str, status: str, progress: int, message: str = None):
    """
    Helper function to notify all WebSocket clients about job update.
    
    Call this from orchestrator when job status changes.
    """
    await manager.broadcast_to_job(job_id, {
        "type": "update",
        "job_id": job_id,
        "status": status,
        "progress": progress,
        "message": message
    })
