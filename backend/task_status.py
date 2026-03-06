# Simple task status tracking with MongoDB persistence
from typing import Dict, Any
from datetime import datetime, timezone
from database import get_database

class TaskStore:
    def __init__(self):
        self.db = None
        self.tasks_collection = None
    
    async def _ensure_db(self):
        """Ensure database connection is initialized"""
        if self.db is None:
            self.db = await get_database()
            self.tasks_collection = self.db.tasks
    
    async def create_task(self, task_id: str, task_type: str, metadata: Dict[str, Any] = None):
        await self._ensure_db()
        task = {
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
        await self.tasks_collection.insert_one(task)
        return task
    
    async def update_task(self, task_id: str, status: str = None, progress: int = None, 
                    result: Any = None, error: str = None):
        await self._ensure_db()
        
        update_fields = {"updated_at": datetime.now(timezone.utc).isoformat()}
        
        if status:
            update_fields["status"] = status
        if progress is not None:
            update_fields["progress"] = progress
        if result is not None:
            update_fields["result"] = result
        if error is not None:
            update_fields["error"] = error
        
        await self.tasks_collection.update_one(
            {"task_id": task_id},
            {"$set": update_fields}
        )
        
        return await self.get_task(task_id)
    
    async def get_task(self, task_id: str):
        await self._ensure_db()
        task = await self.tasks_collection.find_one({"task_id": task_id}, {"_id": 0})
        return task
    
    async def delete_task(self, task_id: str):
        await self._ensure_db()
        await self.tasks_collection.delete_one({"task_id": task_id})

# Global task store
task_store = TaskStore()

