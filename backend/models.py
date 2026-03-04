from sqlalchemy import Column, String, Float, DateTime, Integer, Boolean, Text, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timezone
import uuid
import enum

def generate_uuid():
    return str(uuid.uuid4())

def utcnow():
    return datetime.now(timezone.utc)

class InvoiceStatus(str, enum.Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ScopeType(str, enum.Enum):
    SCOPE1 = "Scope1"
    SCOPE2 = "Scope2"
    SCOPE3 = "Scope3"

class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class ReportStatus(str, enum.Enum):
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    
    organizations = relationship("Organization", back_populates="owner")

class Organization(Base):
    __tablename__ = "organizations"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    industry = Column(String, nullable=True)
    country = Column(String, nullable=True)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    
    owner = relationship("User", back_populates="organizations")
    invoices = relationship("Invoice", back_populates="organization")
    emission_records = relationship("EmissionRecord", back_populates="organization")
    ledger_entries = relationship("BlockchainLedger", back_populates="organization")
    greenwashing_analyses = relationship("GreenwashingAnalysis", back_populates="organization")
    carbon_estimations = relationship("CarbonEstimation", back_populates="organization")
    esg_reports = relationship("ESGReport", back_populates="organization")

class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    file_name = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_path = Column(String, nullable=True)
    status = Column(SQLEnum(InvoiceStatus), default=InvoiceStatus.PROCESSING)
    extracted_data = Column(JSON, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), default=utcnow)
    
    organization = relationship("Organization", back_populates="invoices")
    emission_records = relationship("EmissionRecord", back_populates="invoice")

class EmissionRecord(Base):
    __tablename__ = "emission_records"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    invoice_id = Column(String, ForeignKey("invoices.id"), nullable=True)
    energy_type = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    scope_type = Column(SQLEnum(ScopeType), nullable=False)
    co2_emissions_kg = Column(Float, nullable=False)
    invoice_date = Column(DateTime(timezone=True), nullable=True)
    vendor_name = Column(String, nullable=True)
    cost = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    is_verified = Column(Boolean, default=False)
    
    organization = relationship("Organization", back_populates="emission_records")
    invoice = relationship("Invoice", back_populates="emission_records")

class BlockchainLedger(Base):
    __tablename__ = "blockchain_ledger"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    data_hash = Column(String, nullable=False)
    merkle_root = Column(String, nullable=False)
    transaction_hash = Column(String, nullable=True)
    block_number = Column(Integer, nullable=True)
    verification_url = Column(String, nullable=True)
    qr_code_path = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)
    emission_record_ids = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    
    organization = relationship("Organization", back_populates="ledger_entries")

class GreenwashingAnalysis(Base):
    __tablename__ = "greenwashing_analyses"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    document_name = Column(String, nullable=False)
    document_type = Column(String, nullable=True)
    document_text = Column(Text, nullable=True)
    credibility_score = Column(Float, nullable=False)
    risk_level = Column(SQLEnum(RiskLevel), nullable=False)
    flags = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    ai_insights = Column(Text, nullable=True)
    evidence_score = Column(Float, nullable=True)
    specificity_score = Column(Float, nullable=True)
    transparency_score = Column(Float, nullable=True)
    sentiment_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    
    organization = relationship("Organization", back_populates="greenwashing_analyses")

class CarbonEstimation(Base):
    __tablename__ = "carbon_estimations"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    session_id = Column(String, nullable=False, index=True)
    input_data = Column(JSON, nullable=True)
    messages = Column(JSON, nullable=True)
    scope1_emissions = Column(Float, nullable=True)
    scope2_emissions = Column(Float, nullable=True)
    scope3_emissions = Column(Float, nullable=True)
    total_emissions = Column(Float, nullable=True)
    confidence_interval = Column(String, nullable=True)
    data_completeness_score = Column(Float, nullable=True)
    assumptions = Column(JSON, nullable=True)
    is_complete = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    
    organization = relationship("Organization", back_populates="carbon_estimations")

class ESGReport(Base):
    __tablename__ = "esg_reports"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    report_period = Column(String, nullable=False)
    report_type = Column(String, nullable=True)
    compliance_standard = Column(String, nullable=False)
    total_emissions = Column(Float, nullable=True)
    scope1_emissions = Column(Float, nullable=True)
    scope2_emissions = Column(Float, nullable=True)
    scope3_emissions = Column(Float, nullable=True)
    pdf_path = Column(String, nullable=True)
    html_content = Column(Text, nullable=True)
    status = Column(SQLEnum(ReportStatus), default=ReportStatus.GENERATING)
    quarter = Column(String, nullable=True)
    date_range_start = Column(DateTime(timezone=True), nullable=True)
    date_range_end = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    
    organization = relationship("Organization", back_populates="esg_reports")
