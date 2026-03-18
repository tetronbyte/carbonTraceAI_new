"""API endpoints for ERP integration."""
import uuid
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List
from ..schemas.api_schemas import (
    ERPConnectionRequest,
    ERPConnectionResponse,
    ExtractionRequest,
    ExtractionResponse,
    JobStatusResponse,
    AuditLogResponse
)
from ..models.schemas import TenantERPConfigDoc
from ..models.credentials import CredentialManager
from ..services.database import db_service
from ..workers.extraction_worker import enqueue_extraction
from task_status import job_store
from services.auth_service import get_current_user
from services.rate_limiter import (
    limiter,
    erp_connection_rate_limit,
    erp_extraction_rate_limit,
    health_check_rate_limit,
    general_rate_limit
)

router = APIRouter(prefix="/api/erp", tags=["ERP Integration"])


@router.post("/connections/{tenant_id}", response_model=ERPConnectionResponse)
@limiter.limit("20/minute")
async def connect_erp(
    request: Request,
    tenant_id: str,
    payload: ERPConnectionRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Connect a new ERP system for tenant.
    
    Steps:
    1. Encrypt credentials
    2. Test connection
    3. Store config
    """
    try:
        # Encrypt credentials
        cred_manager = CredentialManager()
        encrypted_creds = cred_manager.encrypt_credentials(payload.credentials)
        
        # Create config
        config = TenantERPConfigDoc(
            tenant_id=tenant_id,
            erp_type=payload.erp_type,
            country=payload.country,
            cbam_sector=payload.cbam_sector,
            credentials_enc=encrypted_creds,
            base_url=payload.base_url,
            connection_string=payload.connection_string
        )
        
        # Test connection
        from ..connectors.registry import get_connector
        connector = get_connector(
            erp_type=payload.erp_type,
            tenant_id=tenant_id,
            credentials=payload.credentials,
            base_url=payload.base_url,
            connection_string=payload.connection_string
        )
        
        is_healthy = await connector.health_check()
        if not is_healthy:
            raise HTTPException(
                status_code=400,
                detail="ERP connection test failed. Check credentials and connectivity."
            )
        
        # Store config
        await db_service.create_erp_config(config)
        
        return ERPConnectionResponse(
            status="connected",
            erp_type=payload.erp_type,
            message=f"Successfully connected {payload.erp_type} ERP"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connections/{tenant_id}")
async def get_erp_connections(
    tenant_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all ERP connections for tenant."""
    configs = await db_service.get_all_erp_configs(tenant_id)
    
    return [{
        "erp_type": config.erp_type,
        "country": config.country,
        "cbam_sector": config.cbam_sector,
        "is_active": config.is_active,
        "last_synced_at": config.last_synced_at.isoformat() if config.last_synced_at else None
    } for config in configs]


@router.post("/extract/{tenant_id}", response_model=ExtractionResponse)
@limiter.limit("5/minute")
async def trigger_extraction(
    request: Request,
    tenant_id: str,
    payload: ExtractionRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Trigger ERP data extraction.
    
    This enqueues a background job and returns immediately.
    """
    try:
        # Get ERP configs
        if payload.erp_type:
            configs = [await db_service.get_erp_config(tenant_id, payload.erp_type)]
        else:
            configs = await db_service.get_all_erp_configs(tenant_id)
        
        if not configs or not configs[0]:
            raise HTTPException(
                status_code=404,
                detail=f"No ERP configuration found for tenant {tenant_id}"
            )
        
        # Create job
        job_id = str(uuid.uuid4())
        await job_store.create_job(
            job_id=job_id,
            job_type="erp_extraction",
            metadata={
                "tenant_id": tenant_id,
                "erp_type": payload.erp_type or "all",
                "modules": payload.modules
            }
        )
        
        # Enqueue extraction for each ERP config
        for config in configs:
            if config:
                await enqueue_extraction(
                    job_id=job_id,
                    tenant_id=tenant_id,
                    erp_type=config.erp_type,
                    modules=payload.modules,
                    from_date=payload.from_date,
                    to_date=payload.to_date,
                    force_full_sync=payload.force_full_sync
                )
        
        return ExtractionResponse(
            job_id=job_id,
            status="queued",
            message=f"Extraction job queued for {len([c for c in configs if c])} ERP system(s)"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/extract/status/{job_id}", response_model=JobStatusResponse)
async def get_extraction_status(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get status of extraction job."""
    job = await job_store.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatusResponse(
        job_id=job["job_id"],
        status=job["status"],
        progress=job.get("progress", 0),
        result=job.get("result"),
        error=job.get("error")
    )


@router.get("/audit-logs/{tenant_id}", response_model=List[AuditLogResponse])
async def get_audit_logs(
    tenant_id: str,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """Get audit logs for tenant."""
    logs = await db_service.get_audit_logs(tenant_id=tenant_id, limit=limit)
    
    return [
        AuditLogResponse(
            job_id=log.job_id,
            tenant_id=log.tenant_id,
            event_type=log.event_type,
            erp_type=log.erp_type,
            module=log.module,
            records_count=log.records_count,
            logged_at=log.logged_at
        )
        for log in logs
    ]


@router.get("/validation-failures/{tenant_id}")
async def get_validation_failures(
    tenant_id: str,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """Get unresolved validation failures for tenant."""
    failures = await db_service.get_unresolved_failures(tenant_id, limit)
    
    return [{
        "raw_extraction_id": f.raw_extraction_id,
        "failure_reason": f.failure_reason,
        "failed_at": f.failed_at.isoformat(),
        "raw_payload": f.raw_payload
    } for f in failures]


@router.delete("/connections/{tenant_id}/{erp_type}")
async def disconnect_erp(
    tenant_id: str,
    erp_type: str,
    current_user: dict = Depends(get_current_user)
):
    """Disconnect (deactivate) an ERP connection."""
    await db_service.deactivate_erp_config(tenant_id, erp_type)
    
    return {"status": "disconnected", "erp_type": erp_type}




@router.get("/health/{tenant_id}")
@limiter.limit("30/minute")
async def check_tenant_health(
    request: Request,
    tenant_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Check health of all ERP connectors for a tenant.
    
    Returns status of each configured ERP connection.
    """
    from ..services.health_check import health_check_service
    
    try:
        results = await health_check_service.check_tenant_connectors(tenant_id)
        
        # Calculate overall health
        healthy_count = sum(1 for r in results if r["status"] == "healthy")
        total_count = len(results)
        
        return {
            "tenant_id": tenant_id,
            "overall_status": "healthy" if healthy_count == total_count else "degraded",
            "healthy_connectors": healthy_count,
            "total_connectors": total_count,
            "connectors": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connectors/capabilities")
async def get_connector_capabilities(
    current_user: dict = Depends(get_current_user)
):
    """
    Get capabilities of all available ERP connectors.
    
    Returns metadata about supported ERP systems.
    """
    from ..services.health_check import health_check_service
    
    try:
        capabilities = await health_check_service.get_all_connector_capabilities()
        return {
            "total_connectors": len(capabilities),
            "connectors": capabilities
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connectors/capabilities/{erp_type}")
async def get_specific_connector_capabilities(
    erp_type: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get capabilities of a specific ERP connector.
    """
    from ..services.health_check import health_check_service
    
    try:
        capability = await health_check_service.get_connector_capabilities(erp_type)
        if capability.get("status") == "not_found":
            raise HTTPException(status_code=404, detail=f"ERP type '{erp_type}' not found")
        return capability
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{tenant_id}")
@limiter.limit("30/minute")
async def get_tenant_jobs(
    request: Request,
    tenant_id: str,
    erp_type: str = None,
    status: str = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all extraction jobs for a tenant.
    
    Optional filters:
    - erp_type: Filter by ERP system type
    - status: Filter by job status (completed, failed, processing)
    """
    from services.job_tracker import job_tracker
    
    try:
        # Get jobs for tenant
        jobs = await job_tracker.get_jobs_by_tenant(
            tenant_id=tenant_id,
            job_type=f"erp_extract_{erp_type}" if erp_type else None,
            limit=100
        )
        
        # Filter by status if provided
        if status:
            jobs = [j for j in jobs if j.get("status") == status]
        
        return {
            "tenant_id": tenant_id,
            "total": len(jobs),
            "jobs": jobs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}/status")
@limiter.limit("60/minute")
async def get_job_status(
    request: Request,
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get detailed status of a specific extraction job."""
    try:
        job = await job_store.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return job
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data/raw/{tenant_id}")
@limiter.limit("30/minute")
async def get_raw_data(
    request: Request,
    tenant_id: str,
    job_id: str = None,
    module: str = None,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """
    Get raw extracted data for a tenant.
    
    Optional filters:
    - job_id: Filter by specific extraction job
    - module: Filter by module (energy, production, etc.)
    - limit: Max records to return (default 100)
    """
    try:
        query = {"tenant_id": tenant_id}
        
        if job_id:
            # Get records for specific job by checking extraction_audit_logs
            query["job_id"] = job_id
        
        if module:
            query["module"] = module
        
        records = await db_service.get_raw_extractions(
            tenant_id=tenant_id,
            limit=limit
        )
        
        return {
            "tenant_id": tenant_id,
            "total": len(records),
            "records": records
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data/normalized/{tenant_id}")
@limiter.limit("30/minute")
async def get_normalized_data(
    request: Request,
    tenant_id: str,
    job_id: str = None,
    module: str = None,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """
    Get normalized CBAM-ready data for a tenant.
    
    Optional filters:
    - job_id: Filter by specific extraction job
    - module: Filter by module (energy, production, etc.)
    - limit: Max records to return (default 100)
    """
    try:
        records = await db_service.get_normalized_records(
            tenant_id=tenant_id,
            limit=limit
        )
        
        # Filter by module if specified
        if module:
            records = [r for r in records if r.get("module") == module]
        
        return {
            "tenant_id": tenant_id,
            "total": len(records),
            "records": records
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/cbam/{tenant_id}")
@limiter.limit("10/minute")
async def export_to_cbam_xml(
    request: Request,
    tenant_id: str,
    payload: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Export normalized data to CBAM-compliant XML format.
    
    Note: This is a placeholder endpoint. Full CBAM XML generation
    will be implemented in P2.
    """
    raise HTTPException(
        status_code=501,
        detail="CBAM XML export feature is under development. Coming in P2!"
    )
