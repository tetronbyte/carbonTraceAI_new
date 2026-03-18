"""Prometheus metrics for ERP integration monitoring."""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import APIRouter, Response
from datetime import datetime, timezone
from ..services.database import db_service

router = APIRouter(prefix="/api/metrics", tags=["Metrics"])

# Metrics definitions
erp_jobs_total = Counter(
    'erp_extraction_jobs_total',
    'Total number of ERP extraction jobs',
    ['tenant_id', 'erp_type', 'status']
)

erp_duration_seconds = Histogram(
    'erp_extraction_duration_seconds',
    'Duration of ERP extraction jobs in seconds',
    ['tenant_id', 'erp_type']
)

erp_records_extracted = Counter(
    'erp_records_extracted_total',
    'Total number of records extracted',
    ['tenant_id', 'erp_type', 'module']
)

erp_validation_failures = Counter(
    'erp_validation_failures_total',
    'Total number of validation failures',
    ['tenant_id', 'erp_type', 'reason']
)

erp_last_sync_timestamp = Gauge(
    'erp_last_sync_timestamp_seconds',
    'Timestamp of last successful sync',
    ['tenant_id', 'erp_type', 'module']
)

erp_sync_lag_seconds = Gauge(
    'erp_last_sync_lag_seconds',
    'Time since last successful sync in seconds',
    ['tenant_id', 'erp_type', 'module']
)


class MetricsCollector:
    """Collect and expose metrics."""
    
    @staticmethod
    def record_job_started(tenant_id: str, erp_type: str):
        """Record job start."""
        erp_jobs_total.labels(tenant_id=tenant_id, erp_type=erp_type, status='started').inc()
    
    @staticmethod
    def record_job_completed(tenant_id: str, erp_type: str, duration: float, records_count: int):
        """Record job completion."""
        erp_jobs_total.labels(tenant_id=tenant_id, erp_type=erp_type, status='completed').inc()
        erp_duration_seconds.labels(tenant_id=tenant_id, erp_type=erp_type).observe(duration)
    
    @staticmethod
    def record_job_failed(tenant_id: str, erp_type: str):
        """Record job failure."""
        erp_jobs_total.labels(tenant_id=tenant_id, erp_type=erp_type, status='failed').inc()
    
    @staticmethod
    def record_records_extracted(tenant_id: str, erp_type: str, module: str, count: int):
        """Record extracted records."""
        erp_records_extracted.labels(tenant_id=tenant_id, erp_type=erp_type, module=module).inc(count)
    
    @staticmethod
    def record_validation_failure(tenant_id: str, erp_type: str, reason: str):
        """Record validation failure."""
        erp_validation_failures.labels(tenant_id=tenant_id, erp_type=erp_type, reason=reason).inc()
    
    @staticmethod
    async def update_sync_metrics():
        """Update sync lag metrics from database."""
        # Get all tenant ERP configs
        from ..models.schemas import TenantERPConfigDoc
        configs = []  # Would need to query all configs
        
        for config in configs:
            for module in ['energy', 'production', 'procurement']:
                watermark = await db_service.get_watermark(
                    config.tenant_id,
                    config.erp_type,
                    module
                )
                
                if watermark:
                    timestamp = watermark.timestamp()
                    erp_last_sync_timestamp.labels(
                        tenant_id=config.tenant_id,
                        erp_type=config.erp_type,
                        module=module
                    ).set(timestamp)
                    
                    # Calculate lag
                    now = datetime.now(timezone.utc)
                    lag = (now - watermark).total_seconds()
                    erp_sync_lag_seconds.labels(
                        tenant_id=config.tenant_id,
                        erp_type=config.erp_type,
                        module=module
                    ).set(lag)


@router.get("")
async def metrics():
    """
    Prometheus metrics endpoint.
    
    Returns metrics in Prometheus exposition format.
    """
    # Update sync metrics before returning
    await MetricsCollector.update_sync_metrics()
    
    # Generate Prometheus format
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Global metrics collector instance
metrics_collector = MetricsCollector()
