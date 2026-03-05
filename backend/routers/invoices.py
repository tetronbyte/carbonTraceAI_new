import os
import uuid
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from datetime import datetime, timezone
from database import invoices_collection, emission_records_collection
from schemas import InvoiceResponse, EmissionRecordResponse
from services.auth_service import get_current_user
from services.invoice_parser import parse_invoice, parse_multiple_invoices
from config import settings
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/invoices", tags=["Invoice Parser"])

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "pdf", "txt", "webp"}
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB
MAX_BATCH_FILES = 20  # Maximum files in batch upload

class BatchUploadResponse(BaseModel):
    batch_id: str
    total_files: int
    successful: int
    failed: int
    total_emissions: float
    scope1_emissions: float
    scope2_emissions: float
    scope3_emissions: float
    invoices: List[dict]
    emission_records: List[dict]
    failed_files: List[str]

@router.post("/upload", response_model=dict)
async def upload_invoice(
    file: UploadFile = File(...),
    organization_id: str = Form(...),
    country: Optional[str] = Form("default"),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload and parse a single invoice using AI Vision Language Model.
    Extracts comprehensive energy consumption data and calculates carbon emissions.
    
    Supported formats: JPG, PNG, WEBP, PDF, TXT
    """
    # Validate file extension
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Supported: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Read file content
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds 25MB limit")
    
    # Save file
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_id = uuid.uuid4().hex[:8]
    file_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}_{file.filename}")
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Create invoice record
    invoice_id = str(uuid.uuid4())
    invoice = {
        "id": invoice_id,
        "organization_id": organization_id,
        "file_name": file.filename,
        "file_type": file_ext,
        "file_path": file_path,
        "status": "processing",
        "extracted_data": None,
        "country": country,
        "batch_id": None,
        "uploaded_at": datetime.now(timezone.utc).isoformat()
    }
    await invoices_collection.insert_one(invoice)
    
    try:
        # Parse invoice with VLM
        parsed_data = await parse_invoice(file_path, file_ext, country)
        
        # Create emission records
        emission_records = []
        for emission_data in parsed_data.get("emissions_data", []):
            record_id = str(uuid.uuid4())
            record = {
                "id": record_id,
                "organization_id": organization_id,
                "invoice_id": invoice_id,
                "energy_type": emission_data.get("energy_type", "electricity"),
                "quantity": emission_data.get("quantity", 0),
                "unit": emission_data.get("unit", "units"),
                "scope_type": emission_data.get("scope_type", "Scope2"),
                "co2_emissions_kg": emission_data.get("co2_emissions_kg", 0),
                "description": emission_data.get("description", ""),
                "category": emission_data.get("category", ""),
                "cost": emission_data.get("cost", 0),
                "unit_price": emission_data.get("unit_price", 0),
                "emission_factor_used": emission_data.get("emission_factor_used", 0),
                "invoice_date": parsed_data.get("invoice_date"),
                "billing_period_start": parsed_data.get("billing_period_start"),
                "billing_period_end": parsed_data.get("billing_period_end"),
                "vendor_name": parsed_data.get("vendor_name"),
                "location": parsed_data.get("location"),
                "facility_name": parsed_data.get("facility_name"),
                "meter_number": parsed_data.get("meter_number"),
                "is_verified": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await emission_records_collection.insert_one(record)
            emission_records.append(record)
        
        # Build comprehensive extracted data
        extracted_data = {
            # Basic info
            "vendor_name": parsed_data.get("vendor_name"),
            "vendor_address": parsed_data.get("vendor_address"),
            "vendor_contact": parsed_data.get("vendor_contact"),
            "invoice_number": parsed_data.get("invoice_number"),
            "invoice_date": parsed_data.get("invoice_date"),
            "due_date": parsed_data.get("due_date"),
            
            # Customer info
            "customer_name": parsed_data.get("customer_name"),
            "customer_account_number": parsed_data.get("customer_account_number"),
            
            # Location
            "location": parsed_data.get("location"),
            "facility_name": parsed_data.get("facility_name"),
            
            # Billing period
            "billing_period_start": parsed_data.get("billing_period_start"),
            "billing_period_end": parsed_data.get("billing_period_end"),
            "billing_period": parsed_data.get("billing_period"),
            
            # Meter/readings
            "meter_number": parsed_data.get("meter_number"),
            "previous_reading": parsed_data.get("previous_reading"),
            "current_reading": parsed_data.get("current_reading"),
            
            # Financial
            "total_amount": parsed_data.get("total_amount"),
            "currency": parsed_data.get("currency"),
            "taxes": parsed_data.get("taxes"),
            
            # Utility-specific
            "tariff_type": parsed_data.get("tariff_type"),
            "peak_usage": parsed_data.get("peak_usage"),
            "off_peak_usage": parsed_data.get("off_peak_usage"),
            "power_factor": parsed_data.get("power_factor"),
            "maximum_demand": parsed_data.get("maximum_demand"),
            
            # Carbon info
            "carbon_content": parsed_data.get("carbon_content"),
            "renewable_percentage": parsed_data.get("renewable_percentage"),
            
            # Document type
            "document_type": parsed_data.get("document_type"),
            
            # Emissions
            "total_emissions": parsed_data.get("total_emissions"),
            "emission_country_used": parsed_data.get("emission_country_used"),
            
            # Notes
            "notes": parsed_data.get("notes"),
            "parse_error": parsed_data.get("parse_error", False)
        }
        
        status = "completed" if not parsed_data.get("parse_error") else "partial"
        
        await invoices_collection.update_one(
            {"id": invoice_id},
            {"$set": {"status": status, "extracted_data": extracted_data}}
        )
        
        invoice["status"] = status
        invoice["extracted_data"] = extracted_data
        
        return {
            "invoice": {
                "id": invoice_id,
                "organization_id": organization_id,
                "file_name": file.filename,
                "file_type": file_ext,
                "status": status,
                "extracted_data": extracted_data,
                "uploaded_at": invoice["uploaded_at"]
            },
            "emission_records": [{
                "id": r["id"],
                "organization_id": r["organization_id"],
                "invoice_id": r["invoice_id"],
                "energy_type": r["energy_type"],
                "quantity": r["quantity"],
                "unit": r["unit"],
                "scope_type": r["scope_type"],
                "co2_emissions_kg": r["co2_emissions_kg"],
                "description": r.get("description", ""),
                "category": r.get("category", ""),
                "invoice_date": r["invoice_date"],
                "billing_period_start": r.get("billing_period_start"),
                "billing_period_end": r.get("billing_period_end"),
                "vendor_name": r["vendor_name"],
                "cost": r.get("cost", 0),
                "is_verified": r["is_verified"],
                "created_at": r["created_at"]
            } for r in emission_records],
            "extracted_data": extracted_data
        }
        
    except Exception as e:
        await invoices_collection.update_one(
            {"id": invoice_id},
            {"$set": {"status": "failed", "extracted_data": {"error": str(e), "parse_error": True}}}
        )
        raise HTTPException(status_code=500, detail=f"Error parsing invoice: {str(e)}")

@router.post("/batch-upload", response_model=BatchUploadResponse)
async def batch_upload_invoices(
    files: List[UploadFile] = File(...),
    organization_id: str = Form(...),
    country: Optional[str] = Form("default"),
    quarter: Optional[str] = Form(None),
    year: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload and parse multiple invoices in a batch.
    Ideal for quarterly CBAM reporting - upload all invoices from a quarter at once.
    
    Returns aggregated emissions data across all invoices.
    """
    if len(files) > MAX_BATCH_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {MAX_BATCH_FILES} files allowed per batch"
        )
    
    batch_id = str(uuid.uuid4())
    files_data = []
    saved_invoices = []
    
    # Save all files first
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    for file in files:
        file_ext = file.filename.split(".")[-1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            continue
        
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            continue
        
        file_id = uuid.uuid4().hex[:8]
        file_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}_{file.filename}")
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        files_data.append({
            "file_path": file_path,
            "file_type": file_ext,
            "file_name": file.filename
        })
        
        # Create invoice record
        invoice_id = str(uuid.uuid4())
        invoice = {
            "id": invoice_id,
            "organization_id": organization_id,
            "file_name": file.filename,
            "file_type": file_ext,
            "file_path": file_path,
            "status": "processing",
            "extracted_data": None,
            "country": country,
            "batch_id": batch_id,
            "quarter": quarter,
            "year": year,
            "uploaded_at": datetime.now(timezone.utc).isoformat()
        }
        await invoices_collection.insert_one(invoice)
        saved_invoices.append(invoice)
    
    if not files_data:
        raise HTTPException(status_code=400, detail="No valid files to process")
    
    # Parse all invoices
    batch_results = await parse_multiple_invoices(files_data, country)
    
    # Process results and create emission records
    all_emission_records = []
    processed_invoices = []
    
    for i, result in enumerate(batch_results.get("individual_results", [])):
        if i >= len(saved_invoices):
            break
            
        invoice = saved_invoices[i]
        invoice_id = invoice["id"]
        
        # Create emission records for this invoice
        for emission_data in result.get("emissions_data", []):
            record_id = str(uuid.uuid4())
            record = {
                "id": record_id,
                "organization_id": organization_id,
                "invoice_id": invoice_id,
                "batch_id": batch_id,
                "energy_type": emission_data.get("energy_type", "electricity"),
                "quantity": emission_data.get("quantity", 0),
                "unit": emission_data.get("unit", "units"),
                "scope_type": emission_data.get("scope_type", "Scope2"),
                "co2_emissions_kg": emission_data.get("co2_emissions_kg", 0),
                "description": emission_data.get("description", ""),
                "category": emission_data.get("category", ""),
                "cost": emission_data.get("cost", 0),
                "invoice_date": result.get("invoice_date"),
                "billing_period_start": result.get("billing_period_start"),
                "billing_period_end": result.get("billing_period_end"),
                "vendor_name": result.get("vendor_name"),
                "location": result.get("location"),
                "source_file": result.get("file_name"),
                "quarter": quarter,
                "year": year,
                "is_verified": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await emission_records_collection.insert_one(record)
            all_emission_records.append(record)
        
        # Update invoice status
        status = "completed" if not result.get("parse_error") else "partial" if result.get("emissions_data") else "failed"
        extracted_data = {
            "vendor_name": result.get("vendor_name"),
            "invoice_number": result.get("invoice_number"),
            "invoice_date": result.get("invoice_date"),
            "billing_period": result.get("billing_period"),
            "location": result.get("location"),
            "total_amount": result.get("total_amount"),
            "currency": result.get("currency"),
            "total_emissions": result.get("total_emissions"),
            "document_type": result.get("document_type"),
            "notes": result.get("notes"),
            "parse_error": result.get("parse_error", False)
        }
        
        await invoices_collection.update_one(
            {"id": invoice_id},
            {"$set": {"status": status, "extracted_data": extracted_data}}
        )
        
        processed_invoices.append({
            "id": invoice_id,
            "file_name": invoice["file_name"],
            "status": status,
            "total_emissions": result.get("total_emissions", 0),
            "vendor_name": result.get("vendor_name"),
            "document_type": result.get("document_type")
        })
    
    aggregate = batch_results.get("aggregate", {})
    
    return BatchUploadResponse(
        batch_id=batch_id,
        total_files=len(files),
        successful=aggregate.get("successful_parses", 0),
        failed=aggregate.get("failed_parses", 0),
        total_emissions=aggregate.get("total_emissions", 0),
        scope1_emissions=aggregate.get("scope1_emissions", 0),
        scope2_emissions=aggregate.get("scope2_emissions", 0),
        scope3_emissions=aggregate.get("scope3_emissions", 0),
        invoices=processed_invoices,
        emission_records=[{
            "id": r["id"],
            "energy_type": r["energy_type"],
            "quantity": r["quantity"],
            "unit": r["unit"],
            "scope_type": r["scope_type"],
            "co2_emissions_kg": r["co2_emissions_kg"],
            "source_file": r.get("source_file", "")
        } for r in all_emission_records],
        failed_files=aggregate.get("failed_files", [])
    )

@router.get("/batch/{batch_id}")
async def get_batch_invoices(
    batch_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all invoices from a batch upload"""
    invoices = await invoices_collection.find(
        {"batch_id": batch_id},
        {"_id": 0}
    ).to_list(100)
    
    if not invoices:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    # Get emission records for this batch
    emission_records = await emission_records_collection.find(
        {"batch_id": batch_id},
        {"_id": 0}
    ).to_list(1000)
    
    # Calculate totals
    total_emissions = sum(r.get("co2_emissions_kg", 0) for r in emission_records)
    scope1 = sum(r.get("co2_emissions_kg", 0) for r in emission_records if r.get("scope_type") == "Scope1")
    scope2 = sum(r.get("co2_emissions_kg", 0) for r in emission_records if r.get("scope_type") == "Scope2")
    scope3 = sum(r.get("co2_emissions_kg", 0) for r in emission_records if r.get("scope_type") == "Scope3")
    
    return {
        "batch_id": batch_id,
        "invoices": invoices,
        "emission_records": emission_records,
        "summary": {
            "total_invoices": len(invoices),
            "total_emissions": round(total_emissions, 2),
            "scope1_emissions": round(scope1, 2),
            "scope2_emissions": round(scope2, 2),
            "scope3_emissions": round(scope3, 2)
        }
    }

@router.get("", response_model=List[InvoiceResponse])
async def get_invoices(
    organization_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all invoices for an organization"""
    invoices = await invoices_collection.find(
        {"organization_id": organization_id},
        {"_id": 0}
    ).sort("uploaded_at", -1).to_list(100)
    return invoices

@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific invoice with full extracted data"""
    invoice = await invoices_collection.find_one({"id": invoice_id}, {"_id": 0})
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    return invoice

@router.get("/{invoice_id}/emissions", response_model=List[EmissionRecordResponse])
async def get_invoice_emissions(
    invoice_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get emission records for a specific invoice"""
    records = await emission_records_collection.find(
        {"invoice_id": invoice_id},
        {"_id": 0}
    ).to_list(100)
    return records

@router.delete("/{invoice_id}")
async def delete_invoice(
    invoice_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete an invoice and its emission records"""
    invoice = await invoices_collection.find_one({"id": invoice_id}, {"_id": 0})
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Delete emission records
    await emission_records_collection.delete_many({"invoice_id": invoice_id})
    
    # Delete invoice
    await invoices_collection.delete_one({"id": invoice_id})
    
    # Delete file if exists
    if invoice.get("file_path") and os.path.exists(invoice["file_path"]):
        os.remove(invoice["file_path"])
    
    return {"message": "Invoice deleted successfully"}
