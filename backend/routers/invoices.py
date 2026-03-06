import os
import uuid
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, BackgroundTasks
from datetime import datetime, timezone
from database import invoices_collection, emission_records_collection
from schemas import InvoiceResponse, EmissionRecordResponse
from services.auth_service import get_current_user
from services.invoice_parser import parse_invoice, parse_multiple_invoices
from config import settings
from typing import List, Optional
from pydantic import BaseModel
from task_status import job_store

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

class BatchUploadTaskResponse(BaseModel):
    job_id: str
    batch_id: str
    status: str
    message: str
    total_files: int

class SingleUploadTaskResponse(BaseModel):
    job_id: str
    invoice_id: str
    status: str
    message: str

# Background task for single invoice processing
async def process_single_upload_task(
    job_id: str,
    invoice_id: str,
    file_content: bytes,
    file_name: str,
    file_ext: str,
    country: str,
    organization_id: str
):
    """Background task to process single invoice upload"""
    try:
        await job_store.update_job(job_id, status="processing", progress=10)
        
        # Save file (moved to background to avoid blocking the response)
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        file_id = uuid.uuid4().hex[:8]
        file_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}_{file_name}")
        
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Update invoice with file path
        await invoices_collection.update_one(
            {"id": invoice_id},
            {"$set": {"file_path": file_path}}
        )
        
        await job_store.update_job(job_id, progress=20)
        
        # Parse invoice with VLM
        parsed_data = await parse_invoice(file_path, file_ext, country)
        
        await job_store.update_job(job_id, progress=60)
        
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
        
        await job_store.update_job(job_id, progress=80)
        
        # Build extracted data
        extracted_data = {
            "vendor_name": parsed_data.get("vendor_name"),
            "invoice_number": parsed_data.get("invoice_number"),
            "invoice_date": parsed_data.get("invoice_date"),
            "billing_period_start": parsed_data.get("billing_period_start"),
            "billing_period_end": parsed_data.get("billing_period_end"),
            "total_amount": parsed_data.get("total_amount"),
            "currency": parsed_data.get("currency"),
            "location": parsed_data.get("location"),
            "facility_name": parsed_data.get("facility_name"),
            "meter_number": parsed_data.get("meter_number"),
            "tariff_type": parsed_data.get("tariff_type"),
            "total_emissions": parsed_data.get("total_emissions"),
            "emission_country_used": parsed_data.get("emission_country_used"),
            "document_type": parsed_data.get("document_type"),
            "notes": parsed_data.get("notes"),
            "parse_error": parsed_data.get("parse_error", False)
        }
        
        status = "completed" if not parsed_data.get("parse_error") else "partial"
        
        await invoices_collection.update_one(
            {"id": invoice_id},
            {"$set": {"status": status, "extracted_data": extracted_data}}
        )
        
        result_data = {
            "invoice_id": invoice_id,
            "status": status,
            "extracted_data": extracted_data,
            "emission_records": [{
                "id": r["id"],
                "energy_type": r["energy_type"],
                "quantity": r["quantity"],
                "co2_emissions_kg": r["co2_emissions_kg"],
                "scope_type": r["scope_type"]
            } for r in emission_records]
        }
        
        await job_store.update_job(job_id, status="completed", progress=100, result=result_data)
        
    except Exception as e:
        await invoices_collection.update_one(
            {"id": invoice_id},
            {"$set": {"status": "failed", "extracted_data": {"error": str(e), "parse_error": True}}}
        )
        await job_store.update_job(job_id, status="failed", error=str(e))

@router.post("/upload", response_model=SingleUploadTaskResponse)
async def upload_invoice(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    organization_id: str = Form(...),
    country: Optional[str] = Form("default"),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload and parse a single invoice using AI Vision Language Model (async).
    Returns immediately with job_id. Use /upload/status/{job_id} to check progress.
    
    Supported formats: JPG, PNG, WEBP, PDF, TXT
    """
    # Validate file extension
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Supported: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Read file content quickly
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds 25MB limit")
    
    # Create IDs and minimal invoice record (fast operations only)
    invoice_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())
    
    invoice = {
        "id": invoice_id,
        "organization_id": organization_id,
        "file_name": file.filename,
        "file_type": file_ext,
        "file_path": None,  # Will be set by background task
        "status": "processing",
        "extracted_data": None,
        "country": country,
        "batch_id": None,
        "uploaded_at": datetime.now(timezone.utc).isoformat()
    }
    await invoices_collection.insert_one(invoice)
    
    # Create task
    await job_store.create_job(
        job_id=job_id,
        task_type="single_upload",
        metadata={"invoice_id": invoice_id, "organization_id": organization_id, "file_name": file.filename}
    )
    
    # Start background processing (file saving moved here to avoid blocking)
    background_tasks.add_task(
        process_single_upload_task,
        job_id, invoice_id, content, file.filename, file_ext, country, organization_id
    )
    
    return SingleUploadTaskResponse(
        job_id=job_id,
        invoice_id=invoice_id,
        status="queued",
        message=f"Invoice upload started for {file.filename}"
    )

@router.get("/upload/status/{job_id}")
async def get_upload_status(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get status of single upload task"""
    task = await job_store.get_job(job_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


# Background task for batch processing
async def process_batch_upload_task(
    job_id: str,
    batch_id: str,
    files_data: List[dict],
    saved_invoices: List[dict],
    organization_id: str,
    country: str,
    quarter: Optional[str],
    year: Optional[str]
):
    """Background task to process batch upload"""
    try:
        await job_store.update_job(job_id, status="processing", progress=10)
        
        # Parse all invoices
        batch_results = await parse_multiple_invoices(files_data, country)
        await job_store.update_job(job_id, progress=60)
        
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
        
        await job_store.update_job(job_id, progress=90)
        
        aggregate = batch_results.get("aggregate", {})
        
        result_data = {
            "batch_id": batch_id,
            "total_files": len(files_data),
            "successful": aggregate.get("successful_parses", 0),
            "failed": aggregate.get("failed_parses", 0),
            "total_emissions": aggregate.get("total_emissions", 0),
            "scope1_emissions": aggregate.get("scope1_emissions", 0),
            "scope2_emissions": aggregate.get("scope2_emissions", 0),
            "scope3_emissions": aggregate.get("scope3_emissions", 0),
            "invoices": processed_invoices,
            "emission_records": [{
                "id": r["id"],
                "energy_type": r["energy_type"],
                "quantity": r["quantity"],
                "unit": r["unit"],
                "scope_type": r["scope_type"],
                "co2_emissions_kg": r["co2_emissions_kg"]
            } for r in all_emission_records],
            "failed_files": []
        }
        
        await job_store.update_job(job_id, status="completed", progress=100, result=result_data)
        
    except Exception as e:
        await job_store.update_job(job_id, status="failed", error=str(e))

@router.post("/batch-upload", response_model=BatchUploadTaskResponse)
async def batch_upload_invoices(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    organization_id: str = Form(...),
    country: Optional[str] = Form("default"),
    quarter: Optional[str] = Form(None),
    year: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload and parse multiple invoices in a batch (async).
    Returns immediately with job_id. Use /batch-upload/status/{job_id} to check progress.
    
    Ideal for quarterly CBAM reporting - upload all invoices from a quarter at once.
    """
    if len(files) > MAX_BATCH_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {MAX_BATCH_FILES} files allowed per batch"
        )
    
    batch_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())
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
    
    # Create task
    await job_store.create_job(
        job_id=job_id,
        task_type="batch_upload",
        metadata={"batch_id": batch_id, "organization_id": organization_id, "total_files": len(files_data)}
    )
    
    # Start background processing
    background_tasks.add_task(
        process_batch_upload_task,
        job_id, batch_id, files_data, saved_invoices, organization_id, country, quarter, year
    )
    
    return BatchUploadTaskResponse(
        job_id=job_id,
        batch_id=batch_id,
        status="queued",
        message=f"Batch upload started. {len(files_data)} files queued for processing.",
        total_files=len(files_data)
    )

@router.get("/batch-upload/status/{job_id}")
async def get_batch_upload_status(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get status of batch upload task"""
    task = await job_store.get_job(job_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

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
