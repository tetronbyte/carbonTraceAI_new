"""Arq worker for background ERP extraction jobs."""
import asyncio
from arq import create_pool
from arq.connections import RedisSettings
from typing import Dict, Any
from ..services.orchestrator import orchestrator


async def run_erp_extraction(
    ctx: Dict,
    job_id: str,
    tenant_id: str,
    erp_type: str,
    modules: list,
    from_date: str = None,
    to_date: str = None,
    force_full_sync: bool = False
) -> Dict[str, Any]:
    """
    Background task to run ERP extraction.
    
    This is called by Arq worker.
    """
    try:
        result = await orchestrator.run_extraction(
            job_id=job_id,
            tenant_id=tenant_id,
            erp_type=erp_type,
            modules=modules,
            from_date=from_date,
            to_date=to_date,
            force_full_sync=force_full_sync
        )
        return result
    except Exception as e:
        # Job will be marked as failed in orchestrator
        raise


class WorkerSettings:
    """Arq worker configuration."""
    
    functions = [run_erp_extraction]
    
    # Redis connection
    redis_settings = RedisSettings(
        host="localhost",
        port=6379,
        database=0
    )
    
    # Worker settings
    max_jobs = 5  # Process up to 5 extractions concurrently
    job_timeout = 1800  # 30 minutes timeout
    keep_result = 3600  # Keep result for 1 hour


async def enqueue_extraction(
    job_id: str,
    tenant_id: str,
    erp_type: str,
    modules: list,
    from_date: str = None,
    to_date: str = None,
    force_full_sync: bool = False
) -> str:
    """
    Enqueue an extraction job.
    
    Returns:
        Arq job ID
    """
    redis = await create_pool(WorkerSettings.redis_settings)
    job = await redis.enqueue_job(
        "run_erp_extraction",
        job_id,
        tenant_id,
        erp_type,
        modules,
        from_date,
        to_date,
        force_full_sync
    )
    return job.job_id
