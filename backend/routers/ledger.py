import uuid
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from database import emission_records_collection, blockchain_ledger_collection
from schemas import LedgerRecordRequest, LedgerResponse, EmissionRecordResponse
from services.auth_service import get_current_user
from services.blockchain_service import record_on_blockchain
from typing import List

router = APIRouter(prefix="/ledger", tags=["Carbon Ledger"])

@router.post("/record", response_model=LedgerResponse)
async def record_emissions(
    request: LedgerRecordRequest,
    current_user: dict = Depends(get_current_user)
):
    """Record emission data on blockchain"""
    # Fetch emission records
    records = await emission_records_collection.find({
        "id": {"$in": request.emission_record_ids},
        "organization_id": request.organization_id
    }, {"_id": 0}).to_list(100)
    
    if not records:
        raise HTTPException(status_code=404, detail="No emission records found")
    
    # Prepare records for blockchain
    records_data = [
        {
            "id": r["id"],
            "energy_type": r["energy_type"],
            "quantity": r["quantity"],
            "unit": r["unit"],
            "scope_type": r.get("scope_type"),
            "co2_emissions_kg": r["co2_emissions_kg"],
            "invoice_date": datetime.fromisoformat(r["invoice_date"]) if r.get("invoice_date") else None,
        }
        for r in records
    ]
    
    # Record on blockchain
    blockchain_result = record_on_blockchain(records_data, request.organization_id)
    
    # Create ledger entry
    ledger_id = str(uuid.uuid4())
    ledger = {
        "id": ledger_id,
        "organization_id": request.organization_id,
        "data_hash": blockchain_result["data_hash"],
        "merkle_root": blockchain_result["merkle_root"],
        "transaction_hash": blockchain_result["transaction_hash"],
        "block_number": blockchain_result["block_number"],
        "verification_url": blockchain_result["verification_url"],
        "qr_code_path": blockchain_result["qr_code_path"],
        "is_verified": blockchain_result["is_verified"],
        "emission_record_ids": request.emission_record_ids,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await blockchain_ledger_collection.insert_one(ledger)
    
    # Mark records as verified
    await emission_records_collection.update_many(
        {"id": {"$in": request.emission_record_ids}},
        {"$set": {"is_verified": True}}
    )
    
    return ledger

@router.get("/{ledger_id}", response_model=LedgerResponse)
async def get_ledger_entry(
    ledger_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific ledger entry"""
    ledger = await blockchain_ledger_collection.find_one({"id": ledger_id}, {"_id": 0})
    
    if not ledger:
        raise HTTPException(status_code=404, detail="Ledger entry not found")
    
    return ledger

@router.get("", response_model=List[LedgerResponse])
async def get_ledger_entries(
    organization_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all ledger entries for an organization"""
    ledgers = await blockchain_ledger_collection.find(
        {"organization_id": organization_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return ledgers

@router.get("/emissions/{organization_id}", response_model=List[EmissionRecordResponse])
async def get_emission_records(
    organization_id: str,
    verified_only: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """Get emission records for an organization"""
    query = {"organization_id": organization_id}
    
    if verified_only:
        query["is_verified"] = True
    
    records = await emission_records_collection.find(
        query, {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return records
