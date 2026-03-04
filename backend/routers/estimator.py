import uuid
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from database import estimations_collection
from schemas import (
    EstimatorStartRequest, 
    EstimatorChatRequest, 
    EstimatorGenerateRequest,
    EstimatorSessionResponse,
    EstimatorResultResponse
)
from services.auth_service import get_current_user
from services.estimator_service import (
    extract_data_from_message,
    calculate_completeness,
    get_next_question,
    calculate_emissions,
    generate_ai_response,
    QUESTIONS
)
from typing import List

router = APIRouter(prefix="/estimator", tags=["Carbon Estimator"])

@router.post("/start", response_model=dict)
async def start_session(
    request: EstimatorStartRequest,
    current_user: dict = Depends(get_current_user)
):
    """Start a new carbon estimation session"""
    session_id = str(uuid.uuid4())
    
    # Initial message
    initial_message = {
        "role": "assistant",
        "content": f"Hello! I'm your Carbon Estimation Assistant. I'll help you estimate your organization's carbon footprint through a series of questions. Let's start!\n\n{QUESTIONS[0]['question']}",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    estimation_id = str(uuid.uuid4())
    estimation = {
        "id": estimation_id,
        "organization_id": request.organization_id,
        "session_id": session_id,
        "messages": [initial_message],
        "input_data": {},
        "scope1_emissions": None,
        "scope2_emissions": None,
        "scope3_emissions": None,
        "total_emissions": None,
        "confidence_interval": None,
        "data_completeness_score": 0.0,
        "assumptions": None,
        "is_complete": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await estimations_collection.insert_one(estimation)
    
    return {
        "session_id": session_id,
        "message": initial_message["content"],
        "data_completeness_score": 0.0
    }

@router.post("/chat", response_model=dict)
async def chat(
    request: EstimatorChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """Send a message in the estimation chat"""
    estimation = await estimations_collection.find_one(
        {"session_id": request.session_id}, {"_id": 0}
    )
    
    if not estimation:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get current question context
    input_data = estimation.get("input_data", {})
    asked_questions = list(input_data.keys())
    
    # Determine which question we're answering
    current_question = None
    for q in QUESTIONS:
        if q["id"] not in asked_questions:
            current_question = q
            break
    
    # Extract data from user message
    if current_question:
        extracted = extract_data_from_message(request.message, current_question["id"])
        input_data.update(extracted)
    
    # Add user message
    messages = estimation.get("messages", [])
    messages.append({
        "role": "user",
        "content": request.message,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    is_complete = estimation.get("is_complete", False)
    
    # Check if user wants to generate estimate
    if "yes" in request.message.lower() and calculate_completeness(input_data) >= 40:
        # Calculate emissions
        result_data = calculate_emissions(input_data)
        
        response_content = f"""Based on the information you provided, here's your estimated carbon footprint:

**Total Emissions: {result_data['total_emissions']:,.0f} kg CO2e/year**

- Scope 1 (Direct): {result_data['scope1_emissions']:,.0f} kg CO2e
- Scope 2 (Electricity): {result_data['scope2_emissions']:,.0f} kg CO2e
- Scope 3 (Value Chain): {result_data['scope3_emissions']:,.0f} kg CO2e

**Confidence: {result_data['confidence_interval']}**
**Data Completeness: {result_data['data_completeness_score']:.0f}%**

Assumptions used:
{chr(10).join('• ' + a for a in result_data['assumptions'])}

Would you like to save this estimate or refine it with more data?"""
        
        await estimations_collection.update_one(
            {"session_id": request.session_id},
            {"$set": {
                "scope1_emissions": result_data["scope1_emissions"],
                "scope2_emissions": result_data["scope2_emissions"],
                "scope3_emissions": result_data["scope3_emissions"],
                "total_emissions": result_data["total_emissions"],
                "confidence_interval": result_data["confidence_interval"],
                "assumptions": result_data["assumptions"],
                "is_complete": True
            }}
        )
        is_complete = True
    else:
        # Generate next response
        response_content = generate_ai_response(request.message, {"input_data": input_data})
    
    # Add assistant message
    messages.append({
        "role": "assistant",
        "content": response_content,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    completeness = calculate_completeness(input_data)
    
    # Update estimation
    await estimations_collection.update_one(
        {"session_id": request.session_id},
        {"$set": {
            "messages": messages,
            "input_data": input_data,
            "data_completeness_score": completeness
        }}
    )
    
    return {
        "session_id": request.session_id,
        "message": response_content,
        "data_completeness_score": completeness,
        "is_complete": is_complete
    }

@router.post("/generate", response_model=EstimatorResultResponse)
async def generate_estimate(
    request: EstimatorGenerateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Generate final carbon estimate"""
    estimation = await estimations_collection.find_one(
        {"session_id": request.session_id}, {"_id": 0}
    )
    
    if not estimation:
        raise HTTPException(status_code=404, detail="Session not found")
    
    input_data = estimation.get("input_data", {})
    
    if calculate_completeness(input_data) < 40:
        raise HTTPException(
            status_code=400,
            detail="Not enough data to generate estimate. Please answer more questions."
        )
    
    # Calculate emissions
    result_data = calculate_emissions(input_data)
    
    # Update estimation
    await estimations_collection.update_one(
        {"session_id": request.session_id},
        {"$set": {
            "scope1_emissions": result_data["scope1_emissions"],
            "scope2_emissions": result_data["scope2_emissions"],
            "scope3_emissions": result_data["scope3_emissions"],
            "total_emissions": result_data["total_emissions"],
            "confidence_interval": result_data["confidence_interval"],
            "data_completeness_score": result_data["data_completeness_score"],
            "assumptions": result_data["assumptions"],
            "is_complete": True
        }}
    )
    
    # Fetch updated
    estimation = await estimations_collection.find_one(
        {"session_id": request.session_id}, {"_id": 0}
    )
    
    return estimation

@router.get("/session/{session_id}", response_model=EstimatorSessionResponse)
async def get_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get estimation session details"""
    estimation = await estimations_collection.find_one(
        {"session_id": session_id}, {"_id": 0}
    )
    
    if not estimation:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return estimation

@router.get("/sessions/{organization_id}", response_model=List[EstimatorSessionResponse])
async def get_sessions(
    organization_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all estimation sessions for an organization"""
    estimations = await estimations_collection.find(
        {"organization_id": organization_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return estimations
