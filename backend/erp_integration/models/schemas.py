"""MongoDB schema definitions for ERP integration."""
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class TenantERPConfigDoc(BaseModel):
    """Tenant ERP configuration document in MongoDB."""
    tenant_id: str
    erp_type: str  # 'odoo', 'syspro', 'sap_b1', 'erpnext', 'sage_bc', 'dynamics365'
    country: str  # 'ZA', 'KE', 'MA', 'EG', 'TZ', 'MZ', 'ZW'
    cbam_sector: str  # 'steel', 'cement', 'aluminum', 'fertilizer', 'hydrogen'
    credentials_enc: str  # Fernet-encrypted JSON blob
    base_url: Optional[str] = None  # For API-based ERPs
    connection_string: Optional[str] = None  # For SQL-based ERPs
    is_active: bool = True
    last_synced_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ERPRawExtractionDoc(BaseModel):
    """Raw, untouched ERP data extraction."""
    tenant_id: str
    source_erp: str
    source_module: str  # 'energy', 'production', 'procurement'
    source_record_id: str  # Original ERP primary key
    raw_payload: Dict[str, Any]
    extracted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ERPNormalizedDoc(BaseModel):
    """Normalized, analysis-ready ERP data."""
    raw_extraction_id: str
    tenant_id: str
    record_type: str  # 'energy', 'production_output', 'procurement', 'logistics'
    activity_date: str  # ISO date string
    quantity: float
    unit_normalized: str  # 'tonne', 'kwh', 'gj', 'litre', 'm3', 'kg'
    material_code: Optional[str] = None
    cbam_sector: str
    emission_factor_id: Optional[str] = None
    co2e_kg: Optional[float] = None
    currency_original: Optional[str] = None
    amount_eur: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SyncWatermarkDoc(BaseModel):
    """Tracks last sync timestamp per tenant/ERP/module."""
    tenant_id: str
    erp_type: str
    module: str
    last_synced_at: datetime
    last_record_id: Optional[str] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ExtractionAuditLogDoc(BaseModel):
    """Immutable audit trail for all extraction jobs."""
    job_id: str
    tenant_id: str
    event_type: str  # 'started', 'completed', 'failed', 'retried'
    erp_type: str
    module: Optional[str] = None
    records_count: Optional[int] = None
    error_detail: Optional[Dict[str, Any]] = None
    logged_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ValidationFailureDoc(BaseModel):
    """Records that failed validation."""
    raw_extraction_id: str
    tenant_id: str
    failure_reason: str
    raw_payload: Dict[str, Any]
    failed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved: bool = False
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
