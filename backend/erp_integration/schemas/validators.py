"""Pydantic validation models for normalized ERP data."""
from pydantic import BaseModel, validator, Field
from typing import Optional
from decimal import Decimal
from datetime import date

VALID_UNITS = {"tonne", "kwh", "gj", "litre", "m3", "kg", "mwh"}
VALID_SECTORS = {"aluminum", "steel", "iron", "cement", "fertilizer", "hydrogen"}
VALID_RECORD_TYPES = {"energy", "production_output", "procurement", "logistics"}


class NormalizedRecord(BaseModel):
    """Validated normalized record before storage."""
    tenant_id: str
    raw_extraction_id: str
    record_type: str
    activity_date: date
    quantity: Decimal = Field(gt=0)  # Must be positive
    unit_normalized: str
    material_code: Optional[str] = None
    cbam_sector: str
    emission_factor_id: Optional[str] = None
    co2e_kg: Optional[Decimal] = Field(None, ge=0)
    currency_original: Optional[str] = None
    amount_eur: Optional[Decimal] = Field(None, ge=0)
    
    @validator("unit_normalized")
    def unit_must_be_known(cls, v):
        if v.lower() not in VALID_UNITS:
            raise ValueError(f"Unknown unit '{v}'. Must be one of {VALID_UNITS}")
        return v.lower()
    
    @validator("cbam_sector")
    def sector_must_be_cbam(cls, v):
        if v.lower() not in VALID_SECTORS:
            raise ValueError(f"Sector '{v}' not in CBAM scope")
        return v.lower()
    
    @validator("record_type")
    def type_must_be_valid(cls, v):
        if v.lower() not in VALID_RECORD_TYPES:
            raise ValueError(f"Record type '{v}' not valid")
        return v.lower()
    
    @validator("co2e_kg")
    def sanity_check_emissions(cls, v, values):
        """Flag suspiciously low emissions for cement/steel."""
        if v and values.get("cbam_sector") in {"cement", "steel", "aluminum"}:
            if values.get("unit_normalized") == "tonne" and v < 10:
                raise ValueError(
                    f"co2e_kg={v} per tonne is implausibly low for {values['cbam_sector']}"
                )
        return v
    
    @validator("quantity")
    def quantity_must_be_reasonable(cls, v, values):
        """Check for unreasonably large quantities."""
        if v > 1000000:  # 1 million units
            raise ValueError(f"Quantity {v} seems unreasonably large")
        return v
    
    class Config:
        json_encoders = {
            Decimal: float,
            date: lambda v: v.isoformat()
        }


class ValidationResult(BaseModel):
    """Result of validation."""
    is_valid: bool
    record: Optional[NormalizedRecord] = None
    errors: list[str] = []
