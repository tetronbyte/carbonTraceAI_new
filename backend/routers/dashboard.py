from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone, timedelta
from database import organizations_collection, invoices_collection, emission_records_collection, reports_collection
from schemas import DashboardResponse, DashboardStats, EmissionsByScope, EmissionTimeline, InvoiceResponse, ESGReportResponse
from services.auth_service import get_current_user
from typing import List

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/{organization_id}", response_model=DashboardResponse)
async def get_dashboard(
    organization_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get dashboard data for an organization"""
    # Verify organization ownership
    org = await organizations_collection.find_one({
        "id": organization_id,
        "owner_id": current_user["id"]
    }, {"_id": 0})
    
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Get emission records
    emissions = await emission_records_collection.find(
        {"organization_id": organization_id},
        {"_id": 0}
    ).to_list(1000)
    
    # Calculate stats
    total_emissions = sum(e.get("co2_emissions_kg", 0) for e in emissions)
    scope1 = sum(e.get("co2_emissions_kg", 0) for e in emissions if e.get("scope_type") == "Scope1")
    scope2 = sum(e.get("co2_emissions_kg", 0) for e in emissions if e.get("scope_type") == "Scope2")
    scope3 = sum(e.get("co2_emissions_kg", 0) for e in emissions if e.get("scope_type") == "Scope3")
    verified = sum(1 for e in emissions if e.get("is_verified"))
    
    # Get invoice count
    invoice_count = await invoices_collection.count_documents({"organization_id": organization_id})
    
    # Get report count
    report_count = await reports_collection.count_documents({"organization_id": organization_id})
    
    stats = DashboardStats(
        total_emissions=total_emissions,
        scope1_emissions=scope1,
        scope2_emissions=scope2,
        scope3_emissions=scope3,
        invoice_count=invoice_count,
        verified_records=verified,
        report_count=report_count
    )
    
    # Emissions by scope
    emissions_by_scope = [
        EmissionsByScope(scope="Scope 1", emissions=scope1),
        EmissionsByScope(scope="Scope 2", emissions=scope2),
        EmissionsByScope(scope="Scope 3", emissions=scope3),
    ]
    
    # Emissions timeline (last 6 months)
    timeline = []
    now = datetime.now(timezone.utc)
    for i in range(5, -1, -1):
        month_start = (now - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
        
        month_emissions = 0
        for e in emissions:
            try:
                created = datetime.fromisoformat(e.get("created_at", "").replace("Z", "+00:00"))
                if month_start <= created <= month_end:
                    month_emissions += e.get("co2_emissions_kg", 0)
            except:
                pass
        
        timeline.append(EmissionTimeline(
            date=month_start.strftime("%b %Y"),
            emissions=month_emissions
        ))
    
    # Recent invoices
    invoices = await invoices_collection.find(
        {"organization_id": organization_id},
        {"_id": 0}
    ).sort("uploaded_at", -1).limit(5).to_list(5)
    
    # Recent reports
    reports = await reports_collection.find(
        {"organization_id": organization_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(5).to_list(5)
    
    return DashboardResponse(
        stats=stats,
        emissions_by_scope=emissions_by_scope,
        emissions_timeline=timeline,
        recent_invoices=invoices,
        recent_reports=reports
    )
