"""Orchestration layer for ERP extraction jobs."""
import uuid
from typing import List, Dict, Any
from datetime import datetime, timezone
from pydantic import ValidationError
from ..connectors.registry import get_connector
from ..models.schemas import (
    ERPRawExtractionDoc,
    ERPNormalizedDoc,
    ExtractionAuditLogDoc,
    ValidationFailureDoc
)
from ..services.database import db_service
from ..services.transformer import FieldMapper, UnitConverter, EmissionFactorMapper, CurrencyConverter
from ..schemas.validators import NormalizedRecord
from task_status import job_store


class ExtractionContext:
    """Context manager for extraction jobs with audit logging."""
    
    def __init__(
        self,
        job_id: str,
        tenant_id: str,
        erp_type: str,
        module: str
    ):
        self.job_id = job_id
        self.tenant_id = tenant_id
        self.erp_type = erp_type
        self.module = module
        self.records_extracted = 0
    
    async def __aenter__(self):
        """Log job start."""
        await db_service.log_extraction_event(
            ExtractionAuditLogDoc(
                job_id=self.job_id,
                tenant_id=self.tenant_id,
                event_type="started",
                erp_type=self.erp_type,
                module=self.module
            )
        )
        await job_store.update_job(self.job_id, status="processing", progress=0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Log job completion or failure."""
        if exc_type:
            # Job failed
            await db_service.log_extraction_event(
                ExtractionAuditLogDoc(
                    job_id=self.job_id,
                    tenant_id=self.tenant_id,
                    event_type="failed",
                    erp_type=self.erp_type,
                    module=self.module,
                    error_detail={"error": str(exc_val), "type": exc_type.__name__}
                )
            )
            await job_store.update_job(self.job_id, status="failed", error=str(exc_val))
            
            # Check for consecutive failures
            fail_count = await db_service.get_failed_jobs_count(self.tenant_id, self.erp_type)
            if fail_count >= 3:
                # TODO: Send alert
                pass
        else:
            # Job succeeded
            await db_service.log_extraction_event(
                ExtractionAuditLogDoc(
                    job_id=self.job_id,
                    tenant_id=self.tenant_id,
                    event_type="completed",
                    erp_type=self.erp_type,
                    module=self.module,
                    records_count=self.records_extracted
                )
            )
            await job_store.update_job(
                self.job_id,
                status="completed",
                progress=100,
                result={"records_extracted": self.records_extracted}
            )
        
        return False  # Don't suppress exceptions


class ERPOrchestrator:
    """Orchestrates ERP data extraction, transformation, and storage."""
    
    def __init__(self):
        self.field_mapper = FieldMapper()
        self.unit_converter = UnitConverter()
        self.emission_mapper = EmissionFactorMapper()
        self.currency_converter = CurrencyConverter()
    
    async def run_extraction(
        self,
        job_id: str,
        tenant_id: str,
        erp_type: str,
        modules: List[str],
        from_date: str = None,
        to_date: str = None,
        force_full_sync: bool = False
    ) -> Dict[str, Any]:
        """
        Run complete extraction pipeline for tenant.
        
        Args:
            job_id: Unique job identifier
            tenant_id: Tenant to extract for
            erp_type: Type of ERP ('odoo', 'syspro', etc.)
            modules: List of modules to extract ('energy', 'production', 'procurement')
            from_date: Start date (ISO format)
            to_date: End date (ISO format)
            force_full_sync: Ignore watermark and do full sync
        
        Returns:
            Summary of extraction results
        """
        # Get tenant ERP config
        config = await db_service.get_erp_config(tenant_id, erp_type)
        if not config:
            raise ValueError(f"No ERP config found for tenant {tenant_id}, ERP {erp_type}")
        
        # Decrypt credentials
        from ..models.credentials import CredentialManager
        cred_manager = CredentialManager()
        credentials = cred_manager.decrypt_credentials(config.credentials_enc)
        
        # Initialize connector
        connector = get_connector(
            erp_type=erp_type,
            tenant_id=tenant_id,
            credentials=credentials,
            base_url=config.base_url,
            connection_string=config.connection_string
        )
        
        # Test connection
        if not await connector.health_check():
            raise ConnectionError(f"Failed to connect to {erp_type} for tenant {tenant_id}")
        
        total_records = 0
        
        # Process each module
        for module in modules:
            async with ExtractionContext(job_id, tenant_id, erp_type, module) as ctx:
                # Determine date range (use watermark if not forcing full sync)
                if not force_full_sync and not from_date:
                    watermark = await db_service.get_watermark(tenant_id, erp_type, module)
                    from_date = watermark.isoformat() if watermark else "2024-01-01"
                
                if not to_date:
                    to_date = datetime.now(timezone.utc).isoformat()
                
                # Extract raw data
                await job_store.update_job(job_id, progress=10)
                raw_records = await connector.extract_module(module, from_date, to_date)
                
                # Store raw extractions
                await job_store.update_job(job_id, progress=30)
                for raw_record in raw_records:
                    extraction_id = await self._store_raw_extraction(tenant_id, raw_record)
                    
                    # Transform and normalize
                    await self._transform_and_store(
                        tenant_id=tenant_id,
                        extraction_id=extraction_id,
                        raw_record=raw_record,
                        erp_type=erp_type,
                        cbam_sector=config.cbam_sector,
                        country=config.country
                    )
                
                # Update watermark
                await job_store.update_job(job_id, progress=90)
                await db_service.update_watermark(
                    tenant_id=tenant_id,
                    erp_type=erp_type,
                    module=module,
                    timestamp=datetime.fromisoformat(to_date)
                )
                
                ctx.records_extracted = len(raw_records)
                total_records += len(raw_records)
        
        # Update tenant's last_synced_at
        await db_service.update_last_synced(tenant_id, erp_type)
        
        return {
            "job_id": job_id,
            "tenant_id": tenant_id,
            "erp_type": erp_type,
            "modules": modules,
            "total_records": total_records,
            "from_date": from_date,
            "to_date": to_date
        }
    
    async def _store_raw_extraction(
        self,
        tenant_id: str,
        raw_record
    ) -> str:
        """Store raw extraction record."""
        doc = ERPRawExtractionDoc(
            tenant_id=tenant_id,
            source_erp=raw_record.source_erp,
            source_module=raw_record.source_module,
            source_record_id=raw_record.source_record_id,
            raw_payload=raw_record.raw_payload,
            extracted_at=datetime.fromisoformat(raw_record.extracted_at)
        )
        return await db_service.upsert_raw_extraction(doc)
    
    async def _transform_and_store(
        self,
        tenant_id: str,
        extraction_id: str,
        raw_record,
        erp_type: str,
        cbam_sector: str,
        country: str
    ) -> None:
        """Transform raw record and store normalized version."""
        try:
            # Map fields
            mapped = self.field_mapper.map_record(
                erp_type,
                raw_record.source_module,
                raw_record.raw_payload
            )
            
            # Extract key fields
            record_date = mapped.get("record_date")
            quantity = mapped.get("quantity", 0)
            unit = mapped.get("unit", "")
            material_code = mapped.get("item_code", "")
            amount = mapped.get("amount")
            currency = mapped.get("currency")
            
            # Convert units
            normalized_qty, normalized_unit = self.unit_converter.normalize_for_cbam(
                float(quantity) if quantity else 0,
                str(unit) if unit else "kg",
                cbam_sector
            )
            
            # Calculate emissions
            co2e_kg = self.emission_mapper.calculate_emissions(
                normalized_qty,
                normalized_unit,
                str(material_code) if material_code else "",
                cbam_sector,
                country
            )
            
            # Convert currency
            amount_eur = None
            if amount and currency:
                amount_eur = self.currency_converter.convert_to_eur(float(amount), str(currency))
            
            # Create normalized record
            record = NormalizedRecord(
                tenant_id=tenant_id,
                raw_extraction_id=extraction_id,
                record_type=raw_record.source_module,
                activity_date=datetime.fromisoformat(record_date).date() if record_date else datetime.now(timezone.utc).date(),
                quantity=normalized_qty,
                unit_normalized=normalized_unit,
                material_code=material_code,
                cbam_sector=cbam_sector,
                co2e_kg=co2e_kg,
                currency_original=currency,
                amount_eur=amount_eur
            )
            
            # Validate
            # (Pydantic will validate on instantiation)
            
            # Store
            doc = ERPNormalizedDoc(**record.dict())
            await db_service.insert_normalized_record(doc)
        
        except ValidationError as e:
            # Log validation failure
            await db_service.log_validation_failure(
                ValidationFailureDoc(
                    raw_extraction_id=extraction_id,
                    tenant_id=tenant_id,
                    failure_reason=str(e),
                    raw_payload=raw_record.raw_payload
                )
            )
        except Exception as e:
            # Log other errors
            await db_service.log_validation_failure(
                ValidationFailureDoc(
                    raw_extraction_id=extraction_id,
                    tenant_id=tenant_id,
                    failure_reason=f"Transformation error: {str(e)}",
                    raw_payload=raw_record.raw_payload
                )
            )


# Global orchestrator instance
orchestrator = ERPOrchestrator()
