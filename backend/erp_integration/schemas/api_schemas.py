"""Pydantic schemas for API requests/responses."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ERPConnectionRequest(BaseModel):
    """Request to connect a new ERP."""
    erp_type: str = Field(..., description="ERP type: odoo, syspro, sap_b1, etc.")
    country: str = Field(..., description="ISO country code: ZA, KE, MA, etc.")
    cbam_sector: str = Field(..., description="CBAM sector: steel, cement, aluminum, etc.")
    base_url: Optional[str] = Field(None, description="API base URL (for API-based ERPs)")
    connection_string: Optional[str] = Field(None, description="DB connection string (for SQL ERPs)")
    credentials: Dict[str, Any] = Field(..., description="ERP credentials (will be encrypted)")


class ERPConnectionResponse(BaseModel):
    """Response after connecting ERP."""
    status: str
    erp_type: str
    message: str


class ExtractionRequest(BaseModel):
    """Request to trigger extraction."""
    erp_type: Optional[str] = Field(None, description="Specific ERP to extract (or all if None)")
    modules: List[str] = Field(default=["energy", "production", "procurement"])
    from_date: Optional[str] = Field(None, description="Start date (ISO format)")
    to_date: Optional[str] = Field(None, description="End date (ISO format)")
    force_full_sync: bool = Field(False, description="Ignore watermark and do full sync")


class ExtractionResponse(BaseModel):
    """Response after triggering extraction."""
    job_id: str
    status: str
    message: str


class JobStatusResponse(BaseModel):
    """Job status response."""
    job_id: str
    status: str
    progress: int
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class AuditLogResponse(BaseModel):
    """Audit log entry."""
    job_id: str
    tenant_id: str
    event_type: str
    erp_type: str
    module: Optional[str]
    records_count: Optional[int]
    logged_at: datetime
