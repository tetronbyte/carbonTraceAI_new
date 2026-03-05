import os
import base64
import json
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
from ollama import Client
from config import settings
import fitz  # PyMuPDF for PDF text extraction

# Country-specific emission factors (kg CO2 per unit)
EMISSION_FACTORS = {
    # African countries
    "kenya": {
        "electricity": 0.27,  # kg CO2/kWh
        "diesel": 2.68,  # kg CO2/liter
        "petrol": 2.31,
        "gasoline": 2.31,
        "natural_gas": 2.0,  # kg CO2/m3
        "lpg": 1.51,  # kg CO2/kg
        "coal": 2.42,
        "generator": 2.68,
    },
    "nigeria": {
        "electricity": 0.43,
        "diesel": 2.68,
        "petrol": 2.31,
        "gasoline": 2.31,
        "natural_gas": 2.0,
        "lpg": 1.51,
        "generator": 2.68,
    },
    "south_africa": {
        "electricity": 0.93,  # High due to coal
        "diesel": 2.68,
        "petrol": 2.31,
        "gasoline": 2.31,
        "natural_gas": 2.0,
        "lpg": 1.51,
        "coal": 2.42,
    },
    "ghana": {
        "electricity": 0.35,
        "diesel": 2.68,
        "petrol": 2.31,
        "gasoline": 2.31,
        "natural_gas": 2.0,
        "lpg": 1.51,
    },
    "ethiopia": {
        "electricity": 0.02,  # Mostly hydro
        "diesel": 2.68,
        "petrol": 2.31,
        "gasoline": 2.31,
        "natural_gas": 2.0,
        "lpg": 1.51,
    },
    "egypt": {
        "electricity": 0.49,
        "diesel": 2.68,
        "petrol": 2.31,
        "gasoline": 2.31,
        "natural_gas": 2.0,
        "lpg": 1.51,
    },
    "morocco": {
        "electricity": 0.62,
        "diesel": 2.68,
        "petrol": 2.31,
        "gasoline": 2.31,
        "natural_gas": 2.0,
        "lpg": 1.51,
    },
    "tanzania": {
        "electricity": 0.32,
        "diesel": 2.68,
        "petrol": 2.31,
        "gasoline": 2.31,
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
        "generator": 2.68,
        "water": 0.0003,  # kg CO2/liter (treatment)
    }
}

# Scope classification rules
SCOPE_CLASSIFICATION = {
    "Scope1": ["diesel", "petrol", "gasoline", "natural_gas", "lpg", "coal", "fuel_oil", "kerosene", "propane", "generator", "boiler", "furnace", "combustion", "fuel"],
    "Scope2": ["electricity", "power", "kwh", "utility", "grid", "energy"],
    "Scope3": ["transport", "shipping", "logistics", "freight", "supplier", "aviation", "travel", "courier", "delivery", "water"]
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

def get_enhanced_extraction_prompt() -> str:
    """Get comprehensive prompt for extracting all useful invoice data"""
    return """Analyze this invoice/receipt/bill document thoroughly and extract ALL available information in JSON format.

Extract the following data:
{
    "vendor_name": "Name of the vendor/company/utility provider",
    "vendor_address": "Full address of the vendor if available",
    "vendor_contact": "Phone, email, or website of vendor",
    "customer_name": "Name of the customer/account holder",
    "customer_address": "Customer address if shown",
    "customer_account_number": "Account number or customer ID",
    "invoice_number": "Invoice or receipt number",
    "date": "Invoice date (YYYY-MM-DD format)",
    "due_date": "Payment due date if shown",
    "billing_period_start": "Start of billing period (YYYY-MM-DD)",
    "billing_period_end": "End of billing period (YYYY-MM-DD)",
    "location": "Location/country/region",
    "facility_name": "Name of facility or site if mentioned",
    "meter_number": "Meter number or equipment ID",
    "previous_reading": "Previous meter reading",
    "current_reading": "Current meter reading",
    "items": [
        {
            "description": "Full description of the item/service",
            "energy_type": "Type: electricity/diesel/petrol/natural_gas/lpg/water/etc",
            "category": "Category: utility/fuel/transport/supplier/etc",
            "quantity": 0.0,
            "unit": "Unit: kWh/liters/m3/kg/gallons/etc",
            "unit_price": 0.0,
            "subtotal": 0.0,
            "tax": 0.0,
            "total": 0.0
        }
    ],
    "subtotal": 0.0,
    "taxes": [
        {
            "name": "Tax name (VAT, GST, etc)",
            "rate": "Tax rate percentage",
            "amount": 0.0
        }
    ],
    "discounts": 0.0,
    "total_amount": 0.0,
    "currency": "Currency code (KES, NGN, ZAR, USD, EUR, etc)",
    "payment_method": "Payment method if shown",
    "payment_status": "Paid/Unpaid/Partial",
    "tariff_type": "Tariff or rate plan name",
    "peak_usage": "Peak hour consumption if shown",
    "off_peak_usage": "Off-peak consumption if shown",
    "power_factor": "Power factor if shown",
    "maximum_demand": "Maximum demand (kW/kVA) if shown",
    "carbon_content": "Any carbon/CO2 information already on the invoice",
    "renewable_percentage": "Renewable energy percentage if stated",
    "notes": "Any other relevant information, warnings, or special items",
    "document_type": "Type: electricity_bill/fuel_receipt/gas_bill/water_bill/transport_invoice/supplier_invoice/other"
}

IMPORTANT INSTRUCTIONS:
1. Extract ALL line items, not just the first one
2. For electricity bills, look for kWh consumption, maximum demand, power factor
3. For fuel receipts, look for liters/gallons, fuel type (diesel/petrol/gasoline)
4. For gas bills, look for m3 or cubic meters consumption
5. If handwritten, carefully interpret all numbers
6. Extract billing period dates to understand the timeframe
7. Look for any existing carbon/CO2 information already provided
8. Identify multiple energy types if the invoice covers different services
9. Extract meter readings if available (helps verify consumption)
10. Note any renewable energy mentions

Return ONLY valid JSON, no other text."""

async def parse_invoice_with_vlm(file_path: str, file_type: str) -> Dict[str, Any]:
    """
    Parse invoice using Vision Language Model (VLM)
    Uses kimi-k2.5:cloud for comprehensive document understanding
    """
    client = get_ollama_client()
    extraction_prompt = get_enhanced_extraction_prompt()
    
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
            # For PDFs, extract text and use LLM
            pdf_text = extract_text_from_pdf(file_path)
            
            if pdf_text.strip():
                response = client.chat(
                    model=settings.LLM_MODEL,
                    messages=[
                        {
                            "role": "user",
                            "content": f"{extraction_prompt}\n\nDocument text:\n{pdf_text[:12000]}"
                        }
                    ]
                )
                result_text = response['message']['content']
            else:
                return create_empty_result("Could not extract text from PDF - may be scanned image")
        
        elif file_type.lower() == "txt":
            with open(file_path, 'r', encoding='utf-8') as f:
                text_content = f.read()
            
            response = client.chat(
                model=settings.LLM_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": f"{extraction_prompt}\n\nDocument text:\n{text_content[:12000]}"
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
        "parse_error": True,
        "document_type": "unknown"
    }

def classify_scope(energy_type: str, description: str = "", category: str = "") -> str:
    """Classify emission scope based on energy type, description, and category"""
    combined_text = f"{energy_type} {description} {category}".lower()
    
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
    unit_lower = unit.lower().strip() if unit else ""
    
    # Electricity
    if "mwh" in unit_lower:
        return "kWh", 1000.0
    if "kwh" in unit_lower or "kw.h" in unit_lower or "kilowatt" in unit_lower:
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
    if "ccf" in unit_lower:  # 100 cubic feet
        return "m3", 2.832
    if "therm" in unit_lower:
        return "m3", 2.832  # Approximate
    
    return unit or "units", 1.0

def calculate_emissions(quantity: float, unit: str, energy_type: str, country: str = "default") -> float:
    """Calculate CO2 emissions based on quantity, unit, and energy type"""
    if quantity <= 0:
        return 0.0
    
    # Normalize unit
    normalized_unit, conversion = normalize_unit(unit, energy_type)
    normalized_quantity = quantity * conversion
    
    # Get emission factor
    emission_factor = get_emission_factor(energy_type, country)
    
    # Calculate emissions
    return normalized_quantity * emission_factor

def process_invoice_data(parsed_data: Dict[str, Any], country: str = "default") -> Dict[str, Any]:
    """Process parsed invoice data and calculate emissions with enhanced metadata"""
    emissions_data = []
    total_emissions = 0.0
    
    items = parsed_data.get("items", [])
    invoice_date = parsed_data.get("date")
    location = parsed_data.get("location") or country
    
    # Enhanced metadata
    billing_period = None
    if parsed_data.get("billing_period_start") and parsed_data.get("billing_period_end"):
        billing_period = f"{parsed_data.get('billing_period_start')} to {parsed_data.get('billing_period_end')}"
    
    for item in items:
        energy_type = item.get("energy_type", "electricity")
        quantity = float(item.get("quantity", 0) or 0)
        unit = item.get("unit", "units")
        description = item.get("description", "")
        category = item.get("category", "")
        cost = float(item.get("total", 0) or item.get("subtotal", 0) or 0)
        unit_price = float(item.get("unit_price", 0) or 0)
        
        if quantity <= 0:
            continue
        
        # Calculate emissions
        co2_emissions = calculate_emissions(quantity, unit, energy_type, location)
        
        # Classify scope
        scope = classify_scope(energy_type, description, category)
        
        # Normalize unit for storage
        normalized_unit, _ = normalize_unit(unit, energy_type)
        
        emissions_data.append({
            "energy_type": energy_type,
            "quantity": quantity,
            "unit": normalized_unit,
            "scope_type": scope,
            "co2_emissions_kg": round(co2_emissions, 2),
            "description": description,
            "category": category,
            "cost": cost,
            "unit_price": unit_price,
            "emission_factor_used": get_emission_factor(energy_type, location),
        })
        
        total_emissions += co2_emissions
    
    # Build comprehensive result
    result = {
        # Basic info
        "vendor_name": parsed_data.get("vendor_name", "Unknown"),
        "vendor_address": parsed_data.get("vendor_address"),
        "vendor_contact": parsed_data.get("vendor_contact"),
        "invoice_number": parsed_data.get("invoice_number"),
        "invoice_date": invoice_date,
        "due_date": parsed_data.get("due_date"),
        
        # Customer info
        "customer_name": parsed_data.get("customer_name"),
        "customer_address": parsed_data.get("customer_address"),
        "customer_account_number": parsed_data.get("customer_account_number"),
        
        # Location & facility
        "location": location,
        "facility_name": parsed_data.get("facility_name"),
        
        # Billing period
        "billing_period_start": parsed_data.get("billing_period_start"),
        "billing_period_end": parsed_data.get("billing_period_end"),
        "billing_period": billing_period,
        
        # Meter/readings
        "meter_number": parsed_data.get("meter_number"),
        "previous_reading": parsed_data.get("previous_reading"),
        "current_reading": parsed_data.get("current_reading"),
        
        # Financial
        "subtotal": parsed_data.get("subtotal"),
        "taxes": parsed_data.get("taxes"),
        "discounts": parsed_data.get("discounts"),
        "total_amount": parsed_data.get("total_amount", 0),
        "currency": parsed_data.get("currency", "USD"),
        
        # Utility-specific
        "tariff_type": parsed_data.get("tariff_type"),
        "peak_usage": parsed_data.get("peak_usage"),
        "off_peak_usage": parsed_data.get("off_peak_usage"),
        "power_factor": parsed_data.get("power_factor"),
        "maximum_demand": parsed_data.get("maximum_demand"),
        
        # Carbon info from invoice
        "carbon_content": parsed_data.get("carbon_content"),
        "renewable_percentage": parsed_data.get("renewable_percentage"),
        
        # Document classification
        "document_type": parsed_data.get("document_type", "unknown"),
        
        # Calculated data
        "emissions_data": emissions_data,
        "total_emissions": round(total_emissions, 2),
        "emission_country_used": location,
        
        # Notes and errors
        "notes": parsed_data.get("notes", ""),
        "parse_error": parsed_data.get("parse_error", False)
    }
    
    return result

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

async def parse_multiple_invoices(files_data: List[Dict], country: str = "default") -> Dict[str, Any]:
    """
    Parse multiple invoices and aggregate results
    Used for batch/quarterly processing
    """
    results = []
    total_emissions = 0.0
    scope1_total = 0.0
    scope2_total = 0.0
    scope3_total = 0.0
    all_emission_records = []
    failed_files = []
    
    for file_info in files_data:
        file_path = file_info.get("file_path")
        file_type = file_info.get("file_type")
        file_name = file_info.get("file_name", "unknown")
        
        try:
            result = await parse_invoice(file_path, file_type, country)
            result["file_name"] = file_name
            results.append(result)
            
            if not result.get("parse_error"):
                total_emissions += result.get("total_emissions", 0)
                
                for record in result.get("emissions_data", []):
                    record["source_file"] = file_name
                    all_emission_records.append(record)
                    
                    if record.get("scope_type") == "Scope1":
                        scope1_total += record.get("co2_emissions_kg", 0)
                    elif record.get("scope_type") == "Scope2":
                        scope2_total += record.get("co2_emissions_kg", 0)
                    else:
                        scope3_total += record.get("co2_emissions_kg", 0)
            else:
                failed_files.append(file_name)
                
        except Exception as e:
            failed_files.append(file_name)
            results.append({
                "file_name": file_name,
                "parse_error": True,
                "notes": str(e)
            })
    
    return {
        "individual_results": results,
        "aggregate": {
            "total_invoices": len(files_data),
            "successful_parses": len(files_data) - len(failed_files),
            "failed_parses": len(failed_files),
            "failed_files": failed_files,
            "total_emissions": round(total_emissions, 2),
            "scope1_emissions": round(scope1_total, 2),
            "scope2_emissions": round(scope2_total, 2),
            "scope3_emissions": round(scope3_total, 2),
            "emission_records": all_emission_records,
            "country_used": country
        }
    }
