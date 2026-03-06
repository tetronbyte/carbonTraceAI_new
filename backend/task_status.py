# Job/Task tracking system with MongoDB persistence
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from database import get_database

class JobStore:
    """Manages background job status tracking"""
    
    def __init__(self):
        self.db = None
        self.jobs_collection = None
    
    async def _ensure_db(self):
        """Ensure database connection is initialized"""
        if self.db is None:
            self.db = await get_database()
            self.jobs_collection = self.db.jobs
    
    async def create_job(self, job_id: str, job_type: str, metadata: Dict[str, Any] = None):
        """Create a new job with 'processing' status"""
        await self._ensure_db()
        job = {
            "job_id": job_id,
            "job_type": job_type,
            "status": "processing",  # Start as processing immediately
            "progress": 0,
            "result": None,
            "error": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
            "metadata": metadata or {}
        }
        await self.jobs_collection.insert_one(job)
        return job
    
    async def update_job(self, job_id: str, status: Optional[str] = None, progress: Optional[int] = None, 
                         result: Any = None, error: Optional[str] = None):
        """Update job status and data"""
        await self._ensure_db()
        
        update_fields = {"updated_at": datetime.now(timezone.utc).isoformat()}
        
        if status:
            update_fields["status"] = status
            if status == "completed":
                update_fields["completed_at"] = datetime.now(timezone.utc).isoformat()
        if progress is not None:
            update_fields["progress"] = progress
        if result is not None:
            update_fields["result"] = result
        if error is not None:
            update_fields["error"] = error
        
        await self.jobs_collection.update_one(
            {"job_id": job_id},
            {"$set": update_fields}
        )
        
        return await self.get_job(job_id)
    
    async def get_job(self, job_id: str):
        """Get job status"""
        await self._ensure_db()
        job = await self.jobs_collection.find_one({"job_id": job_id}, {"_id": 0})
        return job
    
    async def delete_job(self, job_id: str):
        """Delete a job"""
        await self._ensure_db()
        await self.jobs_collection.delete_one({"job_id": job_id})

# Global job store
job_store = JobStore()

