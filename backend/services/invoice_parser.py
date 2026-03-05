import os
import base64
import json
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
from ollama import Client
from config import settings
import fitz  # PyMuPDF for PDF text extraction (fallback)

# Country-specific emission factors (kg CO2 per unit)
EMISSION_FACTORS = {
    # African countries
    "kenya": {
        "electricity": 0.27,  # kg CO2/kWh
        "diesel": 2.68,  # kg CO2/liter
        "petrol": 2.31,
        "natural_gas": 2.0,  # kg CO2/m3
        "lpg": 1.51,  # kg CO2/kg
    },
    "nigeria": {
        "electricity": 0.43,
        "diesel": 2.68,
        "petrol": 2.31,
        "natural_gas": 2.0,
        "lpg": 1.51,
    },
    "south_africa": {
        "electricity": 0.93,  # High due to coal
        "diesel": 2.68,
        "petrol": 2.31,
        "natural_gas": 2.0,
        "lpg": 1.51,
    },
    "ghana": {
        "electricity": 0.35,
        "diesel": 2.68,
        "petrol": 2.31,
        "natural_gas": 2.0,
        "lpg": 1.51,
    },
    "ethiopia": {
        "electricity": 0.02,  # Mostly hydro
        "diesel": 2.68,
        "petrol": 2.31,
        "natural_gas": 2.0,
        "lpg": 1.51,
    },
    "egypt": {
        "electricity": 0.49,
        "diesel": 2.68,
        "petrol": 2.31,
        "natural_gas": 2.0,
        "lpg": 1.51,
    },
    "morocco": {
        "electricity": 0.62,
        "diesel": 2.68,
        "petrol": 2.31,
        "natural_gas": 2.0,
        "lpg": 1.51,
    },
    "tanzania": {
        "electricity": 0.32,
        "diesel": 2.68,
        "petrol": 2.31,
        "natural_gas": 2.0,
        "lpg": 1.51,
    },
    # Default/International
    "default": {
        "electricity": 0.45,
        "diesel": 2.68,
        "petrol": 2.31,
        "gasoline": 2.31,
        "natural_gas": 2.0,
        "lpg": 1.51,
        "coal": 2.42,
        "fuel_oil": 2.96,
        "kerosene": 2.52,
        "propane": 1.51,
        "aviation_fuel": 2.55,
        "shipping": 0.02,  # per tonne-km
        "transport": 0.15,  # per km
    }
}

# Scope classification rules
SCOPE_CLASSIFICATION = {
    "Scope1": ["diesel", "petrol", "gasoline", "natural_gas", "lpg", "coal", "fuel_oil", "kerosene", "propane", "generator", "boiler", "furnace"],
    "Scope2": ["electricity", "power", "kwh", "utility", "grid"],
    "Scope3": ["transport", "shipping", "logistics", "freight", "supplier", "aviation", "travel", "courier"]
}

def get_ollama_client() -> Client:
    """Get Ollama client configured for cloud API"""
    headers = {}
    if settings.OLLAMA_API_KEY:
        headers['Authorization'] = f'Bearer {settings.OLLAMA_API_KEY}'
    
    return Client(
        host=settings.OLLAMA_HOST,
        headers=headers
    )

def encode_image_to_base64(file_path: str) -> str:
    """Encode image file to base64"""
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF using PyMuPDF"""
    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        return ""

async def parse_invoice_with_vlm(file_path: str, file_type: str) -> Dict[str, Any]:
    """
    Parse invoice using Vision Language Model (VLM)
    Uses kimi-k2.5:cloud for document understanding
    """
    client = get_ollama_client()
    
    # Prepare the prompt for structured extraction
    extraction_prompt = """Analyze this invoice/receipt document and extract the following information in JSON format:

{
    "vendor_name": "Name of the vendor/company issuing the invoice",
    "invoice_number": "Invoice or receipt number",
    "date": "Date of the invoice (YYYY-MM-DD format)",
    "location": "Location/country if mentioned",
    "items": [
        {
            "description": "Description of item/service",
            "energy_type": "Type of energy (electricity/diesel/petrol/natural_gas/lpg/etc)",
            "quantity": 0.0,
            "unit": "Unit of measurement (kWh/liters/m3/kg/etc)",
            "cost": 0.0,
            "currency": "Currency code"
        }
    ],
    "total_amount": 0.0,
    "currency": "Currency code",
    "notes": "Any additional relevant information"
}

Be thorough in extracting energy consumption data like:
- Electricity usage (kWh)
- Fuel quantities (liters of diesel/petrol)
- Natural gas (m3 or cubic meters)
- LPG (kg)

If handwritten, carefully interpret the numbers. Return ONLY valid JSON."""

    try:
        if file_type.lower() in ["jpg", "jpeg", "png", "webp"]:
            # Use VLM for image analysis
            image_base64 = encode_image_to_base64(file_path)
            
            response = client.chat(
                model=settings.VLM_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": extraction_prompt,
                        "images": [image_base64]
                    }
                ]
            )
            result_text = response['message']['content']
            
        elif file_type.lower() == "pdf":
            # For PDFs, try to extract text first, then use LLM
            pdf_text = extract_text_from_pdf(file_path)
            
            if pdf_text.strip():
                # If we got text, use LLM to parse it
                response = client.chat(
                    model=settings.LLM_MODEL,
                    messages=[
                        {
                            "role": "user",
                            "content": f"{extraction_prompt}\n\nDocument text:\n{pdf_text[:8000]}"
                        }
                    ]
                )
                result_text = response['message']['content']
            else:
                # PDF might be scanned/image-based, try VLM if possible
                # For now, return empty result
                return create_empty_result("Could not extract text from PDF")
        
        elif file_type.lower() == "txt":
            # Read text file and use LLM
            with open(file_path, 'r', encoding='utf-8') as f:
                text_content = f.read()
            
            response = client.chat(
                model=settings.LLM_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": f"{extraction_prompt}\n\nDocument text:\n{text_content[:8000]}"
                    }
                ]
            )
            result_text = response['message']['content']
        else:
            return create_empty_result(f"Unsupported file type: {file_type}")
        
        # Parse the JSON response
        parsed_data = parse_vlm_response(result_text)
        return parsed_data
        
    except Exception as e:
        return create_empty_result(f"VLM parsing error: {str(e)}")

def parse_vlm_response(response_text: str) -> Dict[str, Any]:
    """Parse the VLM/LLM response to extract structured data"""
    try:
        # Try to extract JSON from the response
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            json_str = json_match.group()
            return json.loads(json_str)
    except json.JSONDecodeError:
        pass
    
    return create_empty_result("Could not parse VLM response")

def create_empty_result(error_msg: str = "") -> Dict[str, Any]:
    """Create empty result structure"""
    return {
        "vendor_name": "Unknown",
        "invoice_number": None,
        "date": None,
        "location": None,
        "items": [],
        "total_amount": 0.0,
        "currency": "USD",
        "notes": error_msg,
        "parse_error": True
    }

def classify_scope(energy_type: str, description: str = "") -> str:
    """Classify emission scope based on energy type and description"""
    combined_text = f"{energy_type} {description}".lower()
    
    for scope, keywords in SCOPE_CLASSIFICATION.items():
        for keyword in keywords:
            if keyword in combined_text:
                return scope
    
    return "Scope2"  # Default to Scope 2 for utilities

def get_emission_factor(energy_type: str, country: str = "default") -> float:
    """Get country-specific emission factor"""
    country = country.lower().replace(" ", "_") if country else "default"
    
    if country not in EMISSION_FACTORS:
        country = "default"
    
    factors = EMISSION_FACTORS[country]
    energy_type_lower = energy_type.lower()
    
    # Find matching factor
    for key, value in factors.items():
        if key in energy_type_lower or energy_type_lower in key:
            return value
    
    return factors.get("electricity", 0.45)  # Default

def normalize_unit(unit: str, energy_type: str) -> Tuple[str, float]:
    """Normalize units and return conversion factor"""
    unit_lower = unit.lower().strip()
    
    # Electricity
    if "mwh" in unit_lower:
        return "kWh", 1000.0
    if "kwh" in unit_lower or "kw.h" in unit_lower:
        return "kWh", 1.0
    
    # Volume
    if "gallon" in unit_lower or "gal" in unit_lower:
        return "liters", 3.785
    if "liter" in unit_lower or "litre" in unit_lower or unit_lower == "l":
        return "liters", 1.0
    
    # Mass
    if "tonne" in unit_lower or "ton" in unit_lower:
        return "kg", 1000.0
    if "kg" in unit_lower or "kilogram" in unit_lower:
        return "kg", 1.0
    
    # Gas
    if "m3" in unit_lower or "cubic" in unit_lower:
        return "m3", 1.0
    
    return unit, 1.0

def calculate_emissions(quantity: float, unit: str, energy_type: str, country: str = "default") -> float:
    """Calculate CO2 emissions based on quantity, unit, and energy type"""
    # Normalize unit
    normalized_unit, conversion = normalize_unit(unit, energy_type)
    normalized_quantity = quantity * conversion
    
    # Get emission factor
    emission_factor = get_emission_factor(energy_type, country)
    
    # Calculate emissions
    return normalized_quantity * emission_factor

def process_invoice_data(parsed_data: Dict[str, Any], country: str = "default") -> Dict[str, Any]:
    """Process parsed invoice data and calculate emissions"""
    emissions_data = []
    total_emissions = 0.0
    
    items = parsed_data.get("items", [])
    invoice_date = parsed_data.get("date")
    location = parsed_data.get("location") or country
    
    for item in items:
        energy_type = item.get("energy_type", "electricity")
        quantity = float(item.get("quantity", 0))
        unit = item.get("unit", "units")
        description = item.get("description", "")
        cost = float(item.get("cost", 0))
        
        if quantity <= 0:
            continue
        
        # Calculate emissions
        co2_emissions = calculate_emissions(quantity, unit, energy_type, location)
        
        # Classify scope
        scope = classify_scope(energy_type, description)
        
        # Normalize unit for storage
        normalized_unit, _ = normalize_unit(unit, energy_type)
        
        emissions_data.append({
            "energy_type": energy_type,
            "quantity": quantity,
            "unit": normalized_unit,
            "scope_type": scope,
            "co2_emissions_kg": round(co2_emissions, 2),
            "description": description,
            "cost": cost,
        })
        
        total_emissions += co2_emissions
    
    return {
        "vendor_name": parsed_data.get("vendor_name", "Unknown"),
        "invoice_number": parsed_data.get("invoice_number"),
        "invoice_date": invoice_date,
        "location": location,
        "total_amount": parsed_data.get("total_amount", 0),
        "currency": parsed_data.get("currency", "USD"),
        "emissions_data": emissions_data,
        "total_emissions": round(total_emissions, 2),
        "notes": parsed_data.get("notes", ""),
        "parse_error": parsed_data.get("parse_error", False)
    }

async def parse_invoice(file_path: str, file_type: str, country: str = "default") -> Dict[str, Any]:
    """
    Main function to parse invoice and extract carbon data
    Uses VLM for document understanding and calculates emissions
    """
    # Parse with VLM
    parsed_data = await parse_invoice_with_vlm(file_path, file_type)
    
    # Process and calculate emissions
    result = process_invoice_data(parsed_data, country)
    
    return result
