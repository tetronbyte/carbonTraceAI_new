import os
import uuid
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from datetime import datetime, timezone
from database import invoices_collection, emission_records_collection
from schemas import InvoiceResponse, EmissionRecordResponse
from services.auth_service import get_current_user
from services.invoice_parser import parse_invoice
from config import settings
from typing import List, Optional

router = APIRouter(prefix="/invoices", tags=["Invoice Parser"])

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "pdf", "txt", "webp"}
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB

@router.post("/upload", response_model=dict)
async def upload_invoice(
    file: UploadFile = File(...),
    organization_id: str = Form(...),
    country: Optional[str] = Form("default"),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload and parse an invoice using AI Vision Language Model.
    Extracts energy consumption data and calculates carbon emissions.
    
    Supported formats: JPG, PNG, PDF, TXT, WEBP
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
                "cost": emission_data.get("cost", 0),
                "invoice_date": parsed_data.get("invoice_date"),
                "vendor_name": parsed_data.get("vendor_name"),
                "location": parsed_data.get("location"),
                "is_verified": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await emission_records_collection.insert_one(record)
            emission_records.append(record)
        
        # Update invoice status
        extracted_data = {
            "vendor_name": parsed_data.get("vendor_name"),
            "invoice_number": parsed_data.get("invoice_number"),
            "invoice_date": parsed_data.get("invoice_date"),
            "location": parsed_data.get("location"),
            "total_amount": parsed_data.get("total_amount"),
            "currency": parsed_data.get("currency"),
            "total_emissions": parsed_data.get("total_emissions"),
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
                "invoice_date": r["invoice_date"],
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
            {"$set": {"status": "failed", "extracted_data": {"error": str(e)}}}
        )
        raise HTTPException(status_code=500, detail=f"Error parsing invoice: {str(e)}")

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
    """Get a specific invoice"""
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
