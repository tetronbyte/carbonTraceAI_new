from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class InvoiceStatusEnum(str, Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ScopeTypeEnum(str, Enum):
    SCOPE1 = "Scope1"
    SCOPE2 = "Scope2"
    SCOPE3 = "Scope3"

class RiskLevelEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

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
    created_at: datetime

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
    created_at: datetime

# Invoice Schemas
class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    organization_id: str
    file_name: str
    file_type: str
    status: InvoiceStatusEnum
    extracted_data: Optional[Dict[str, Any]]
    uploaded_at: datetime

class InvoiceParseResult(BaseModel):
    invoice: InvoiceResponse
    emission_records: List["EmissionRecordResponse"]

# Emission Record Schemas
class EmissionRecordCreate(BaseModel):
    organization_id: str
    energy_type: str
    quantity: float
    unit: str
    scope_type: ScopeTypeEnum
    co2_emissions_kg: float
    invoice_date: Optional[datetime] = None
    vendor_name: Optional[str] = None
    cost: Optional[float] = None

class EmissionRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    organization_id: str
    invoice_id: Optional[str]
    energy_type: str
    quantity: float
    unit: str
    scope_type: ScopeTypeEnum
    co2_emissions_kg: float
    invoice_date: Optional[datetime]
    vendor_name: Optional[str]
    cost: Optional[float]
    is_verified: bool
    created_at: datetime

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
    transaction_hash: Optional[str]
    block_number: Optional[int]
    verification_url: Optional[str]
    qr_code_path: Optional[str]
    is_verified: bool
    emission_record_ids: Optional[List[str]]
    created_at: datetime

# Greenwashing Analysis Schemas
class GreenwashingAnalyzeRequest(BaseModel):
    organization_id: str
    document_text: str
    document_name: str
    document_type: Optional[str] = None
    use_ai_enhancement: bool = False

class GreenwashingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    organization_id: str
    document_name: str
    document_type: Optional[str]
    credibility_score: float
    risk_level: RiskLevelEnum
    flags: Optional[List[Dict[str, Any]]]
    recommendations: Optional[List[str]]
    ai_insights: Optional[str]
    evidence_score: Optional[float]
    specificity_score: Optional[float]
    transparency_score: Optional[float]
    sentiment_score: Optional[float]
    created_at: datetime

# Carbon Estimator Schemas
class EstimatorStartRequest(BaseModel):
    organization_id: str

class EstimatorChatRequest(BaseModel):
    session_id: str
    message: str

class EstimatorGenerateRequest(BaseModel):
    session_id: str

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[datetime] = None

class EstimatorSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    session_id: str
    organization_id: str
    messages: Optional[List[Dict[str, Any]]]
    input_data: Optional[Dict[str, Any]]
    data_completeness_score: Optional[float]
    is_complete: bool
    created_at: datetime

class EstimatorResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    session_id: str
    organization_id: str
    scope1_emissions: Optional[float]
    scope2_emissions: Optional[float]
    scope3_emissions: Optional[float]
    total_emissions: Optional[float]
    confidence_interval: Optional[str]
    assumptions: Optional[List[str]]
    data_completeness_score: Optional[float]

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
    report_type: Optional[str]
    compliance_standard: str
    total_emissions: Optional[float]
    scope1_emissions: Optional[float]
    scope2_emissions: Optional[float]
    scope3_emissions: Optional[float]
    pdf_path: Optional[str]
    status: ReportStatusEnum
    quarter: Optional[str]
    created_at: datetime

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
