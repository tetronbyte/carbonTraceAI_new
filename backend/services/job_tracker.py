"""
Unified job tracking system for all background tasks.

Combines the original task_status.py with ERP audit logging for a 
comprehensive job management system.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from database import get_database
import uuid


class UnifiedJobTracker:
    """
    Unified job tracking system supporting:
    - Original features: Invoice parsing, Report generation
    - ERP Integration: Data extraction, transformation
    """
    
    def __init__(self):
        self.db = None
        self.jobs_collection = None
        self.audit_collection = None
    
    async def _ensure_db(self):
        """Ensure database connection is initialized"""
        if self.db is None:
            self.db = await get_database()
            self.jobs_collection = self.db.jobs
            self.audit_collection = self.db.extraction_audit_logs
    
    # ========== Job Management (Original System) ==========
    
    async def create_job(
        self, 
        job_id: str, 
        job_type: str, 
        metadata: Dict[str, Any] = None,
        tenant_id: str = None
    ):
        """
        Create a new job with 'processing' status.
        
        Args:
            job_id: Unique job identifier
            job_type: Type of job (invoice_parse, report_generate, erp_extract, etc.)
            metadata: Additional metadata
            tenant_id: Optional tenant ID for multi-tenant jobs
        """
        await self._ensure_db()
        job = {
            "job_id": job_id,
            "job_type": job_type,
            "status": "processing",
            "progress": 0,
            "result": None,
            "error": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
            "metadata": metadata or {},
            "tenant_id": tenant_id
        }
        await self.jobs_collection.insert_one(job)
        
        # Create audit log for ERP jobs
        if job_type.startswith("erp_") and tenant_id:
            await self._create_audit_log(
                job_id=job_id,
                tenant_id=tenant_id,
                event_type="job_started",
                metadata=metadata
            )
        
        return job
    
    async def update_job(
        self, 
        job_id: str, 
        status: Optional[str] = None, 
        progress: Optional[int] = None, 
        result: Any = None, 
        error: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ):
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
        if metadata is not None:
            update_fields["metadata"] = metadata
        
        await self.jobs_collection.update_one(
            {"job_id": job_id},
            {"$set": update_fields}
        )
        
        # Update audit log for ERP jobs
        job = await self.get_job(job_id)
        if job and job.get("job_type", "").startswith("erp_"):
            event_type = "job_completed" if status == "completed" else "job_progress"
            if error:
                event_type = "job_failed"
            
            await self._create_audit_log(
                job_id=job_id,
                tenant_id=job.get("tenant_id"),
                event_type=event_type,
                metadata={
                    "progress": progress,
                    "status": status,
                    "error": error
                }
            )
        
        return await self.get_job(job_id)
    
    async def get_job(self, job_id: str):
        """Get job status"""
        await self._ensure_db()
        job = await self.jobs_collection.find_one({"job_id": job_id}, {"_id": 0})
        return job
    
    async def get_jobs_by_tenant(
        self, 
        tenant_id: str, 
        job_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """Get all jobs for a tenant"""
        await self._ensure_db()
        
        query = {"tenant_id": tenant_id}
        if job_type:
            query["job_type"] = job_type
        
        cursor = self.jobs_collection.find(
            query, 
            {"_id": 0}
        ).sort("created_at", -1).limit(limit)
        
        return await cursor.to_list(length=limit)
    
    async def delete_job(self, job_id: str):
        """Delete a job (soft delete - mark as archived)"""
        await self._ensure_db()
        await self.jobs_collection.update_one(
            {"job_id": job_id},
            {"$set": {"archived": True, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    
    async def cleanup_old_jobs(self, days: int = 30):
        """Archive jobs older than specified days"""
        await self._ensure_db()
        cutoff_date = datetime.now(timezone.utc)
        # Note: This would need proper date calculation
        # Placeholder for cleanup logic
        pass
    
    # ========== Audit Logging (ERP System) ==========
    
    async def _create_audit_log(
        self,
        job_id: str,
        tenant_id: str,
        event_type: str,
        metadata: Dict[str, Any] = None
    ):
        """Create audit log entry for ERP jobs"""
        await self._ensure_db()
        
        audit_log = {
            "audit_id": str(uuid.uuid4()),
            "job_id": job_id,
            "tenant_id": tenant_id,
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc),
            "metadata": metadata or {}
        }
        
        await self.audit_collection.insert_one(audit_log)
    
    async def get_audit_logs(
        self, 
        tenant_id: str = None, 
        job_id: str = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get audit logs with optional filters"""
        await self._ensure_db()
        
        query = {}
        if tenant_id:
            query["tenant_id"] = tenant_id
        if job_id:
            query["job_id"] = job_id
        
        cursor = self.audit_collection.find(
            query,
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit)
        
        return await cursor.to_list(length=limit)
    
    # ========== Statistics ==========
    
    async def get_job_statistics(self, tenant_id: str = None) -> Dict[str, Any]:
        """Get job statistics"""
        await self._ensure_db()
        
        query = {}
        if tenant_id:
            query["tenant_id"] = tenant_id
        
        total = await self.jobs_collection.count_documents(query)
        completed = await self.jobs_collection.count_documents({**query, "status": "completed"})
        failed = await self.jobs_collection.count_documents({**query, "status": "failed"})
        processing = await self.jobs_collection.count_documents({**query, "status": "processing"})
        
        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "processing": processing,
            "success_rate": (completed / total * 100) if total > 0 else 0
        }


# Global unified job tracker
job_tracker = UnifiedJobTracker()

# Backward compatibility: Keep the old interface
class JobStore:
    """
    Backward compatibility wrapper for existing code.
    Delegates to UnifiedJobTracker.
    """
    async def create_job(self, job_id: str, job_type: str, metadata: Dict[str, Any] = None):
        return await job_tracker.create_job(job_id, job_type, metadata)
    
    async def update_job(self, job_id: str, status: Optional[str] = None, 
                         progress: Optional[int] = None, result: Any = None, 
                         error: Optional[str] = None):
        return await job_tracker.update_job(job_id, status, progress, result, error)
    
    async def get_job(self, job_id: str):
        return await job_tracker.get_job(job_id)
    
    async def delete_job(self, job_id: str):
        return await job_tracker.delete_job(job_id)


# Global job store (backward compatibility)
job_store = JobStore()
