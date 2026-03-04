import uuid
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from database import greenwashing_collection
from schemas import GreenwashingAnalyzeRequest, GreenwashingResponse
from services.auth_service import get_current_user
from services.greenwashing_service import analyze_greenwashing
from typing import List

router = APIRouter(prefix="/greenwashing", tags=["Greenwashing Detector"])

@router.post("/analyze", response_model=GreenwashingResponse)
async def analyze_document(
    request: GreenwashingAnalyzeRequest,
    current_user: dict = Depends(get_current_user)
):
    """Analyze a document for greenwashing"""
    if not request.document_text or len(request.document_text.strip()) < 50:
        raise HTTPException(
            status_code=400,
            detail="Document text must be at least 50 characters"
        )
    
    # Analyze document
    analysis_result = analyze_greenwashing(
        text=request.document_text,
        use_ai=request.use_ai_enhancement
    )
    
    # Create analysis record
    analysis_id = str(uuid.uuid4())
    analysis = {
        "id": analysis_id,
        "organization_id": request.organization_id,
        "document_name": request.document_name,
        "document_type": request.document_type,
        "document_text": request.document_text[:5000],
        "credibility_score": analysis_result["credibility_score"],
        "risk_level": analysis_result["risk_level"],
        "flags": analysis_result["flags"],
        "recommendations": analysis_result["recommendations"],
        "ai_insights": None,
        "evidence_score": analysis_result["evidence_score"],
        "specificity_score": analysis_result["specificity_score"],
        "transparency_score": analysis_result["transparency_score"],
        "sentiment_score": analysis_result["sentiment_score"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await greenwashing_collection.insert_one(analysis)
    
    return analysis

@router.get("/{analysis_id}", response_model=GreenwashingResponse)
async def get_analysis(
    analysis_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific greenwashing analysis"""
    analysis = await greenwashing_collection.find_one({"id": analysis_id}, {"_id": 0})
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return analysis

@router.get("", response_model=List[GreenwashingResponse])
async def get_analyses(
    organization_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all greenwashing analyses for an organization"""
    analyses = await greenwashing_collection.find(
        {"organization_id": organization_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return analyses
