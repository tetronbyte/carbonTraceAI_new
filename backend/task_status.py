# Simple in-memory task status tracking
# For production, use Redis or database

from typing import Dict, Any
from datetime import datetime, timezone

class TaskStore:
    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}
    
    def create_task(self, task_id: str, task_type: str, metadata: Dict[str, Any] = None):
        self.tasks[task_id] = {
            "task_id": task_id,
            "task_type": task_type,
            "status": "queued",
            "progress": 0,
            "result": None,
            "error": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {}
        }
        return self.tasks[task_id]
    
    def update_task(self, task_id: str, status: str = None, progress: int = None, 
                    result: Any = None, error: str = None):
        if task_id not in self.tasks:
            return None
        
        if status:
            self.tasks[task_id]["status"] = status
        if progress is not None:
            self.tasks[task_id]["progress"] = progress
        if result is not None:
            self.tasks[task_id]["result"] = result
        if error is not None:
            self.tasks[task_id]["error"] = error
        
        self.tasks[task_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
        return self.tasks[task_id]
    
    def get_task(self, task_id: str):
        return self.tasks.get(task_id)
    
    def delete_task(self, task_id: str):
        if task_id in self.tasks:
            del self.tasks[task_id]

# Global task store
task_store = TaskStore()
