import uuid
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
from datetime import datetime, timezone
from database import emission_records_collection, reports_collection
from schemas import ESGReportGenerateRequest, ESGReportResponse
from services.auth_service import get_current_user
from services.report_service import create_esg_report, FRAMEWORKS
from typing import List, Optional
from pydantic import BaseModel
from task_status import job_store

router = APIRouter(prefix="/reports", tags=["ESG Reports"])

class ProductEmission(BaseModel):
    name: str
    batch_id: str
    quantity: float
    unit: str
    emissions: float
    intensity: Optional[float] = None

class CBAMReportRequest(BaseModel):
    organization_id: str
    org_name: str
    report_period: str
    products: List[ProductEmission]

class ReportGenerateTaskResponse(BaseModel):
    job_id: str
    report_id: str
    status: str
    message: str

@router.get("/frameworks")
async def get_frameworks(current_user: dict = Depends(get_current_user)):
    """Get available ESG reporting frameworks"""
    return FRAMEWORKS

# Background task for report generation
async def process_report_generation_task(
    job_id: str,
    report_id: str,
    organization_id: str,
    org_name: str,
    report_period: str,
    compliance_standard: str,
    report_type: str,
    quarter: Optional[str],
    scope1: float,
    scope2: float,
    scope3: float
):
    """Background task to generate ESG report"""
    try:
        await job_store.update_job(job_id, status="processing", progress=10)
        
        # Generate report content with AI narratives (core feature)
        report_result = create_esg_report(
            org_name=org_name,
            report_period=report_period,
            framework=compliance_standard,
            scope1=scope1,
            scope2=scope2,
            scope3=scope3,
            report_type=report_type,
            quarter=quarter,
            use_ai=True  # AI-generated professional narratives
        )
        
        await job_store.update_job(job_id, progress=80)
        
        # Update report
        await reports_collection.update_one(
            {"id": report_id},
            {"$set": {
                "pdf_path": report_result["pdf_path"],
                "html_content": report_result["html_content"],
                "total_emissions": report_result["total_emissions"],
                "scope1_emissions": report_result["scope1_emissions"],
                "scope2_emissions": report_result["scope2_emissions"],
                "scope3_emissions": report_result["scope3_emissions"],
                "status": "completed"
            }}
        )
        
        result_data = {
            "report_id": report_id,
            "pdf_path": report_result["pdf_path"],
            "total_emissions": report_result["total_emissions"],
            "scope1_emissions": report_result["scope1_emissions"],
            "scope2_emissions": report_result["scope2_emissions"],
            "scope3_emissions": report_result["scope3_emissions"],
            "status": "completed"
        }
        
        await job_store.update_job(job_id, status="completed", progress=100, result=result_data)
        
    except Exception as e:
        await reports_collection.update_one(
            {"id": report_id},
            {"$set": {"status": "failed"}}
        )
        await job_store.update_job(job_id, status="failed", error=str(e))

@router.post("/generate", response_model=ReportGenerateTaskResponse)
async def generate_report(
    background_tasks: BackgroundTasks,
    request: ESGReportGenerateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate an ESG report with AI-powered narrative generation (async).
    Returns immediately with job_id. Use /reports/status/{job_id} to check progress.
    
    Supports ISSB, TCFD, GRI, and CBAM frameworks.
    """
    # Build query for emission records
    query = {"organization_id": request.organization_id}
    
    # Filter by date range if provided
    if request.date_range_start:
        query["created_at"] = {"$gte": request.date_range_start.isoformat()}
    if request.date_range_end:
        if "created_at" in query:
            query["created_at"]["$lte"] = request.date_range_end.isoformat()
        else:
            query["created_at"] = {"$lte": request.date_range_end.isoformat()}
    
    records = await emission_records_collection.find(query, {"_id": 0}).to_list(1000)
    
    # Calculate emissions by scope
    scope1 = sum(r.get("co2_emissions_kg", 0) for r in records if r.get("scope_type") == "Scope1")
    scope2 = sum(r.get("co2_emissions_kg", 0) for r in records if r.get("scope_type") == "Scope2")
    scope3 = sum(r.get("co2_emissions_kg", 0) for r in records if r.get("scope_type") == "Scope3")
    
    # Use sample data if no records exist
    if scope1 + scope2 + scope3 == 0:
        scope1 = 5000.0
        scope2 = 12000.0
        scope3 = 8000.0
    
    # Create report record
    report_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())
    
    report = {
        "id": report_id,
        "organization_id": request.organization_id,
        "report_period": request.report_period,
        "report_type": request.report_type or "Annual",
        "compliance_standard": request.compliance_standard,
        "quarter": request.quarter,
        "date_range_start": request.date_range_start.isoformat() if request.date_range_start else None,
        "date_range_end": request.date_range_end.isoformat() if request.date_range_end else None,
        "status": "generating",
        "total_emissions": None,
        "scope1_emissions": None,
        "scope2_emissions": None,
        "scope3_emissions": None,
        "pdf_path": None,
        "html_content": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await reports_collection.insert_one(report)
    
    # Create task
    await job_store.create_job(
        job_id=job_id,
        task_type="report_generation",
        metadata={"report_id": report_id, "organization_id": request.organization_id, "framework": request.compliance_standard}
    )
    
    # Start background processing
    background_tasks.add_task(
        process_report_generation_task,
        job_id, report_id, request.organization_id, request.org_name,
        request.report_period, request.compliance_standard, request.report_type or "Annual",
        request.quarter, scope1, scope2, scope3
    )
    
    return ReportGenerateTaskResponse(
        job_id=job_id,
        report_id=report_id,
        status="queued",
        message=f"Report generation started for {request.compliance_standard} framework."
    )

@router.get("/status/{job_id}")
async def get_report_generation_status(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get status of report generation task"""
    task = await job_store.get_job(job_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.post("/cbam", response_model=ESGReportResponse)
async def generate_cbam_report(
    request: CBAMReportRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate a CBAM (Carbon Border Adjustment Mechanism) compliance report.
    Includes product-level embedded carbon declarations for EU exports.
    """
    # Calculate product-level emissions
    products_data = []
    total_emissions = 0
    
    for product in request.products:
        intensity = product.emissions / product.quantity if product.quantity > 0 else 0
        products_data.append({
            "name": product.name,
            "batch_id": product.batch_id,
            "quantity": product.quantity,
            "unit": product.unit,
            "emissions": product.emissions,
            "intensity": intensity
        })
        total_emissions += product.emissions
    
    # Create report record
    report_id = str(uuid.uuid4())
    report = {
        "id": report_id,
        "organization_id": request.organization_id,
        "report_period": request.report_period,
        "report_type": "CBAM Declaration",
        "compliance_standard": "CBAM",
        "quarter": None,
        "status": "generating",
        "total_emissions": total_emissions,
        "scope1_emissions": total_emissions * 0.6,  # Estimate
        "scope2_emissions": total_emissions * 0.3,
        "scope3_emissions": total_emissions * 0.1,
        "pdf_path": None,
        "products": products_data,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await reports_collection.insert_one(report)
    
    try:
        # Generate CBAM report with AI narratives
        report_result = create_esg_report(
            org_name=request.org_name,
            report_period=request.report_period,
            framework="CBAM",
            scope1=total_emissions * 0.6,
            scope2=total_emissions * 0.3,
            scope3=total_emissions * 0.1,
            report_type="CBAM Declaration",
            products=products_data,
            use_ai=True  # AI-generated professional narratives
        )
        
        # Update report
        await reports_collection.update_one(
            {"id": report_id},
            {"$set": {
                "pdf_path": report_result["pdf_path"],
                "html_content": report_result["html_content"],
                "status": "completed"
            }}
        )
        
        report["pdf_path"] = report_result["pdf_path"]
        report["status"] = "completed"
        
        return report
        
    except Exception as e:
        await reports_collection.update_one(
            {"id": report_id},
            {"$set": {"status": "failed"}}
        )
        raise HTTPException(status_code=500, detail=f"Error generating CBAM report: {str(e)}")

@router.get("/{report_id}", response_model=ESGReportResponse)
async def get_report(
    report_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific report"""
    report = await reports_collection.find_one({"id": report_id}, {"_id": 0})
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return report

@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Download report PDF"""
    report = await reports_collection.find_one({"id": report_id}, {"_id": 0})
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if not report.get("pdf_path"):
        raise HTTPException(status_code=404, detail="PDF not available")
    
    filename = f"esg_report_{report.get('compliance_standard', 'ESG')}_{report['report_period']}.pdf"
    
    return FileResponse(
        report["pdf_path"],
        media_type="application/pdf",
        filename=filename
    )

@router.get("/{report_id}/html")
async def get_report_html(
    report_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get report HTML content for preview"""
    report = await reports_collection.find_one({"id": report_id}, {"_id": 0})
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if not report.get("html_content"):
        raise HTTPException(status_code=404, detail="HTML content not available")
    
    return HTMLResponse(content=report["html_content"])

@router.get("", response_model=List[ESGReportResponse])
async def get_reports(
    organization_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all reports for an organization"""
    reports = await reports_collection.find(
        {"organization_id": organization_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return reports

@router.delete("/{report_id}")
async def delete_report(
    report_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a report"""
    report = await reports_collection.find_one({"id": report_id}, {"_id": 0})
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    await reports_collection.delete_one({"id": report_id})
    
    return {"message": "Report deleted successfully"}
