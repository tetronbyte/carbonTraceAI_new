import uuid
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from config import settings

# Industry emission benchmarks (kg CO2 per employee per year)
INDUSTRY_BENCHMARKS = {
    "manufacturing": {"scope1": 5000, "scope2": 8000, "scope3": 12000},
    "technology": {"scope1": 500, "scope2": 3000, "scope3": 5000},
    "retail": {"scope1": 1000, "scope2": 4000, "scope3": 15000},
    "agriculture": {"scope1": 8000, "scope2": 2000, "scope3": 6000},
    "transport": {"scope1": 15000, "scope2": 1000, "scope3": 8000},
    "services": {"scope1": 800, "scope2": 2500, "scope3": 4000},
    "construction": {"scope1": 6000, "scope2": 3000, "scope3": 10000},
    "mining": {"scope1": 20000, "scope2": 5000, "scope3": 15000},
    "default": {"scope1": 2000, "scope2": 3000, "scope3": 6000},
}

# Estimation factors
ELECTRICITY_FACTOR = 0.82  # kg CO2 per kWh
VEHICLE_FACTOR = 2.31  # kg CO2 per liter petrol
FLIGHT_FACTOR = 0.255  # kg CO2 per km (economy class)

QUESTIONS = [
    {
        "id": "industry",
        "question": "What industry is your company in? (e.g., manufacturing, technology, retail, agriculture, transport, services)",
        "type": "text",
        "required": True,
    },
    {
        "id": "employee_count",
        "question": "How many employees does your company have?",
        "type": "number",
        "required": True,
    },
    {
        "id": "electricity_usage",
        "question": "What is your approximate monthly electricity usage in kWh? (Enter 0 if unknown)",
        "type": "number",
        "required": False,
    },
    {
        "id": "fleet_size",
        "question": "How many vehicles does your company operate? (Enter 0 if none)",
        "type": "number",
        "required": False,
    },
    {
        "id": "monthly_fuel",
        "question": "What is your approximate monthly fuel consumption in liters? (Enter 0 if unknown)",
        "type": "number",
        "required": False,
    },
    {
        "id": "annual_flights",
        "question": "Approximately how many kilometers do your employees fly for business annually? (Enter 0 if unknown)",
        "type": "number",
        "required": False,
    },
    {
        "id": "office_area",
        "question": "What is your total office space area in square meters? (Enter 0 if unknown)",
        "type": "number",
        "required": False,
    },
]

def extract_data_from_message(message: str, current_question_id: str) -> Dict[str, Any]:
    """Extract structured data from user message"""
    message_lower = message.lower().strip()
    
    if current_question_id == "industry":
        for industry in INDUSTRY_BENCHMARKS.keys():
            if industry in message_lower:
                return {"industry": industry}
        return {"industry": message_lower}
    
    # Try to extract numbers
    import re
    numbers = re.findall(r'\d+(?:\.\d+)?', message)
    if numbers:
        return {current_question_id: float(numbers[0])}
    
    # Handle yes/no or zero responses
    if any(word in message_lower for word in ["no", "none", "zero", "0"]):
        return {current_question_id: 0}
    
    return {}

def calculate_completeness(input_data: Dict[str, Any]) -> float:
    """Calculate data completeness score"""
    required_fields = ["industry", "employee_count"]
    optional_fields = ["electricity_usage", "fleet_size", "monthly_fuel", "annual_flights", "office_area"]
    
    required_complete = sum(1 for f in required_fields if input_data.get(f))
    optional_complete = sum(1 for f in optional_fields if input_data.get(f) and input_data.get(f) > 0)
    
    required_score = (required_complete / len(required_fields)) * 60
    optional_score = (optional_complete / len(optional_fields)) * 40
    
    return required_score + optional_score

def get_next_question(input_data: Dict[str, Any], asked_questions: List[str]) -> Optional[Dict[str, Any]]:
    """Get the next question to ask"""
    for question in QUESTIONS:
        if question["id"] not in asked_questions:
            if question["required"] or calculate_completeness(input_data) < 60:
                return question
    return None

def calculate_emissions(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate emissions based on collected data"""
    industry = input_data.get("industry", "default")
    employees = input_data.get("employee_count", 1)
    
    benchmarks = INDUSTRY_BENCHMARKS.get(industry, INDUSTRY_BENCHMARKS["default"])
    
    # Calculate Scope 1 (Direct emissions)
    scope1 = 0
    assumptions_scope1 = []
    
    monthly_fuel = input_data.get("monthly_fuel", 0)
    if monthly_fuel > 0:
        scope1 = monthly_fuel * 12 * VEHICLE_FACTOR
        assumptions_scope1.append(f"Based on {monthly_fuel}L monthly fuel consumption")
    else:
        fleet_size = input_data.get("fleet_size", 0)
        if fleet_size > 0:
            estimated_fuel = fleet_size * 200 * 12  # 200L per vehicle per month
            scope1 = estimated_fuel * VEHICLE_FACTOR
            assumptions_scope1.append(f"Estimated from {fleet_size} vehicles (200L/vehicle/month)")
        else:
            scope1 = benchmarks["scope1"] * employees
            assumptions_scope1.append(f"Based on industry benchmark for {industry}")
    
    # Calculate Scope 2 (Indirect - electricity)
    scope2 = 0
    assumptions_scope2 = []
    
    electricity = input_data.get("electricity_usage", 0)
    if electricity > 0:
        scope2 = electricity * 12 * ELECTRICITY_FACTOR
        assumptions_scope2.append(f"Based on {electricity} kWh monthly electricity")
    else:
        office_area = input_data.get("office_area", 0)
        if office_area > 0:
            estimated_kwh = office_area * 15 * 12  # 15 kWh per sqm per month
            scope2 = estimated_kwh * ELECTRICITY_FACTOR
            assumptions_scope2.append(f"Estimated from {office_area} sqm office space")
        else:
            scope2 = benchmarks["scope2"] * employees
            assumptions_scope2.append(f"Based on industry benchmark for {industry}")
    
    # Calculate Scope 3 (Value chain)
    scope3 = 0
    assumptions_scope3 = []
    
    annual_flights = input_data.get("annual_flights", 0)
    if annual_flights > 0:
        flight_emissions = annual_flights * FLIGHT_FACTOR
        scope3 = flight_emissions + (benchmarks["scope3"] * employees * 0.5)
        assumptions_scope3.append(f"Includes {annual_flights} km of business flights")
    else:
        scope3 = benchmarks["scope3"] * employees
        assumptions_scope3.append(f"Based on industry benchmark for {industry}")
    
    total = scope1 + scope2 + scope3
    
    # Calculate confidence interval
    completeness = calculate_completeness(input_data)
    if completeness > 80:
        confidence = "±10%"
    elif completeness > 50:
        confidence = "±25%"
    else:
        confidence = "±50%"
    
    return {
        "scope1_emissions": round(scope1, 2),
        "scope2_emissions": round(scope2, 2),
        "scope3_emissions": round(scope3, 2),
        "total_emissions": round(total, 2),
        "confidence_interval": confidence,
        "data_completeness_score": completeness,
        "assumptions": assumptions_scope1 + assumptions_scope2 + assumptions_scope3,
    }

def generate_ai_response(message: str, context: Dict[str, Any]) -> str:
    """Generate contextual response (simplified for demo)"""
    input_data = context.get("input_data", {})
    completeness = calculate_completeness(input_data)
    
    next_question = get_next_question(input_data, list(input_data.keys()))
    
    if next_question:
        return next_question["question"]
    elif completeness >= 40:
        return "I have enough information to generate an estimate. Would you like me to calculate your carbon emissions now? (Reply 'yes' to proceed)"
    else:
        return "Thank you for the information. Let me know if you have any other data about your operations."
