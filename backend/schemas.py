from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class InvoiceStatusEnum(str, Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"

class ScopeTypeEnum(str, Enum):
    SCOPE1 = "Scope1"
    SCOPE2 = "Scope2"
    SCOPE3 = "Scope3"

class ReportStatusEnum(str, Enum):
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"

# Auth Schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[str] = None

# Organization Schemas
class OrganizationCreate(BaseModel):
    name: str
    industry: Optional[str] = None
    country: Optional[str] = None

class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    industry: Optional[str]
    country: Optional[str]
    created_at: Optional[str] = None

# Invoice Schemas
class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    organization_id: str
    file_name: str
    file_type: str
    status: str
    extracted_data: Optional[Dict[str, Any]] = None
    country: Optional[str] = None
    uploaded_at: Optional[str] = None

# Emission Record Schemas
class EmissionRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    organization_id: str
    invoice_id: Optional[str] = None
    energy_type: str
    quantity: float
    unit: str
    scope_type: str
    co2_emissions_kg: float
    description: Optional[str] = None
    invoice_date: Optional[str] = None
    vendor_name: Optional[str] = None
    location: Optional[str] = None
    cost: Optional[float] = None
    is_verified: bool = False
    created_at: Optional[str] = None

# Blockchain Ledger Schemas
class LedgerRecordRequest(BaseModel):
    organization_id: str
    emission_record_ids: List[str]

class LedgerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    organization_id: str
    data_hash: str
    merkle_root: str
    transaction_hash: Optional[str] = None
    block_number: Optional[int] = None
    verification_url: Optional[str] = None
    qr_code_path: Optional[str] = None
    is_verified: bool = False
    emission_record_ids: Optional[List[str]] = None
    created_at: Optional[str] = None

# ESG Report Schemas
class ESGReportGenerateRequest(BaseModel):
    organization_id: str
    org_name: str
    report_period: str
    report_type: Optional[str] = "Annual"
    compliance_standard: str
    quarter: Optional[str] = None
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None

class ESGReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    organization_id: str
    report_period: str
    report_type: Optional[str] = None
    compliance_standard: str
    total_emissions: Optional[float] = None
    scope1_emissions: Optional[float] = None
    scope2_emissions: Optional[float] = None
    scope3_emissions: Optional[float] = None
    pdf_path: Optional[str] = None
    status: str
    quarter: Optional[str] = None
    products: Optional[List[Dict]] = None
    created_at: Optional[str] = None

# Dashboard Schemas
class DashboardStats(BaseModel):
    total_emissions: float
    scope1_emissions: float
    scope2_emissions: float
    scope3_emissions: float
    invoice_count: int
    verified_records: int
    report_count: int

class EmissionsByScope(BaseModel):
    scope: str
    emissions: float

class EmissionTimeline(BaseModel):
    date: str
    emissions: float

class DashboardResponse(BaseModel):
    stats: DashboardStats
    emissions_by_scope: List[EmissionsByScope]
    emissions_timeline: List[EmissionTimeline]
    recent_invoices: List[InvoiceResponse]
    recent_reports: List[ESGReportResponse]
