"""MongoDB database service for ERP integration."""
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from database import get_database
from ..models.schemas import (
    TenantERPConfigDoc,
    ERPRawExtractionDoc,
    ERPNormalizedDoc,
    SyncWatermarkDoc,
    ExtractionAuditLogDoc,
    ValidationFailureDoc
)
from ..models.credentials import CredentialManager


class ERPDatabaseService:
    """Handles all MongoDB operations for ERP integration."""
    
    def __init__(self):
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.cred_manager = CredentialManager()
    
    async def _ensure_db(self):
        """Ensure database connection."""
        if self.db is None:
            self.db = await get_database()
    
    # ========== Tenant ERP Config ==========
    
    async def create_erp_config(self, config: TenantERPConfigDoc) -> str:
        """Create new ERP configuration for tenant."""
        await self._ensure_db()
        result = await self.db.tenant_erp_configs.insert_one(config.dict())
        return str(result.inserted_id)
    
    async def get_erp_config(
        self, 
        tenant_id: str, 
        erp_type: str = None
    ) -> Optional[TenantERPConfigDoc]:
        """Get ERP config for tenant."""
        await self._ensure_db()
        query = {"tenant_id": tenant_id, "is_active": True}
        if erp_type:
            query["erp_type"] = erp_type
        
        doc = await self.db.tenant_erp_configs.find_one(query)
        return TenantERPConfigDoc(**doc) if doc else None
    
    async def get_all_erp_configs(self, tenant_id: str) -> List[TenantERPConfigDoc]:
        """Get all active ERP configs for tenant."""
        await self._ensure_db()
        cursor = self.db.tenant_erp_configs.find(
            {"tenant_id": tenant_id, "is_active": True}
        )
        docs = await cursor.to_list(length=100)
        return [TenantERPConfigDoc(**doc) for doc in docs]
    
    async def update_last_synced(self, tenant_id: str, erp_type: str) -> None:
        """Update last_synced_at timestamp."""
        await self._ensure_db()
        await self.db.tenant_erp_configs.update_one(
            {"tenant_id": tenant_id, "erp_type": erp_type},
            {"$set": {
                "last_synced_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }}
        )
    
    async def deactivate_erp_config(self, tenant_id: str, erp_type: str) -> None:
        """Deactivate ERP configuration."""
        await self._ensure_db()
        await self.db.tenant_erp_configs.update_one(
            {"tenant_id": tenant_id, "erp_type": erp_type},
            {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc)}}
        )
    
    # ========== Raw Extractions ==========
    
    async def upsert_raw_extraction(self, record: ERPRawExtractionDoc) -> str:
        """Insert or update raw extraction (idempotent)."""
        await self._ensure_db()
        
        # Unique on tenant_id + source_erp + source_module + source_record_id
        filter_query = {
            "tenant_id": record.tenant_id,
            "source_erp": record.source_erp,
            "source_module": record.source_module,
            "source_record_id": record.source_record_id
        }
        
        result = await self.db.erp_raw_extractions.update_one(
            filter_query,
            {"$set": record.dict()},
            upsert=True
        )
        
        if result.upserted_id:
            return str(result.upserted_id)
        else:
            # Find and return existing ID
            doc = await self.db.erp_raw_extractions.find_one(filter_query)
            return str(doc["_id"])
    
    async def get_raw_extraction(self, extraction_id: str) -> Optional[ERPRawExtractionDoc]:
        """Get raw extraction by ID."""
        await self._ensure_db()
        from bson import ObjectId
        doc = await self.db.erp_raw_extractions.find_one({"_id": ObjectId(extraction_id)})
        return ERPRawExtractionDoc(**doc) if doc else None
    
    # ========== Normalized Data ==========
    
    async def insert_normalized_record(self, record: ERPNormalizedDoc) -> str:
        """Insert normalized record."""
        await self._ensure_db()
        result = await self.db.erp_normalized.insert_one(record.dict())
        return str(result.inserted_id)
    
    async def get_normalized_records(
        self,
        tenant_id: str,
        record_type: str = None,
        from_date: str = None,
        to_date: str = None,
        limit: int = 1000
    ) -> List[ERPNormalizedDoc]:
        """Query normalized records."""
        await self._ensure_db()
        query = {"tenant_id": tenant_id}
        
        if record_type:
            query["record_type"] = record_type
        if from_date or to_date:
            date_filter = {}
            if from_date:
                date_filter["$gte"] = from_date
            if to_date:
                date_filter["$lte"] = to_date
            query["activity_date"] = date_filter
        
        cursor = self.db.erp_normalized.find(query).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [ERPNormalizedDoc(**doc) for doc in docs]
    
    # ========== Sync Watermarks ==========
    
    async def get_watermark(
        self,
        tenant_id: str,
        erp_type: str,
        module: str
    ) -> Optional[datetime]:
        """Get last sync watermark."""
        await self._ensure_db()
        doc = await self.db.sync_watermarks.find_one({
            "tenant_id": tenant_id,
            "erp_type": erp_type,
            "module": module
        })
        return doc["last_synced_at"] if doc else None
    
    async def update_watermark(
        self,
        tenant_id: str,
        erp_type: str,
        module: str,
        timestamp: datetime,
        last_record_id: str = None
    ) -> None:
        """Update sync watermark."""
        await self._ensure_db()
        await self.db.sync_watermarks.update_one(
            {"tenant_id": tenant_id, "erp_type": erp_type, "module": module},
            {"$set": {
                "last_synced_at": timestamp,
                "last_record_id": last_record_id,
                "updated_at": datetime.now(timezone.utc)
            }},
            upsert=True
        )
    
    # ========== Audit Logs ==========
    
    async def log_extraction_event(self, log: ExtractionAuditLogDoc) -> str:
        """Log extraction event."""
        await self._ensure_db()
        result = await self.db.extraction_audit_logs.insert_one(log.dict())
        return str(result.inserted_id)
    
    async def get_audit_logs(
        self,
        tenant_id: str = None,
        job_id: str = None,
        limit: int = 100
    ) -> List[ExtractionAuditLogDoc]:
        """Get audit logs."""
        await self._ensure_db()
        query = {}
        if tenant_id:
            query["tenant_id"] = tenant_id
        if job_id:
            query["job_id"] = job_id
        
        cursor = self.db.extraction_audit_logs.find(query).sort("logged_at", -1).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [ExtractionAuditLogDoc(**doc) for doc in docs]
    
    async def get_failed_jobs_count(self, tenant_id: str, erp_type: str, limit: int = 3) -> int:
        """Get count of recent consecutive failures."""
        await self._ensure_db()
        cursor = self.db.extraction_audit_logs.find({
            "tenant_id": tenant_id,
            "erp_type": erp_type
        }).sort("logged_at", -1).limit(limit)
        
        logs = await cursor.to_list(length=limit)
        if len(logs) < limit:
            return 0
        
        # Check if all recent logs are failures
        failures = sum(1 for log in logs if log["event_type"] == "failed")
        return failures if failures == limit else 0
    
    # ========== Validation Failures ==========
    
    async def log_validation_failure(self, failure: ValidationFailureDoc) -> str:
        """Log validation failure."""
        await self._ensure_db()
        result = await self.db.validation_failures.insert_one(failure.dict())
        return str(result.inserted_id)
    
    async def get_unresolved_failures(
        self,
        tenant_id: str,
        limit: int = 100
    ) -> List[ValidationFailureDoc]:
        """Get unresolved validation failures."""
        await self._ensure_db()
        cursor = self.db.validation_failures.find({
            "tenant_id": tenant_id,
            "resolved": False
        }).sort("failed_at", -1).limit(limit)
        
        docs = await cursor.to_list(length=limit)
        return [ValidationFailureDoc(**doc) for doc in docs]


# Global singleton instance
db_service = ERPDatabaseService()
