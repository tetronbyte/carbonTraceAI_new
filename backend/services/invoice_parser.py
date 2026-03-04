import re
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple
import os
from pathlib import Path

# Emission factors (kg CO2 per unit)
EMISSION_FACTORS = {
    "electricity": {"factor": 0.82, "unit": "kWh", "scope": "Scope2"},
    "diesel": {"factor": 2.68, "unit": "liters", "scope": "Scope1"},
    "petrol": {"factor": 2.31, "unit": "liters", "scope": "Scope1"},
    "gasoline": {"factor": 2.31, "unit": "liters", "scope": "Scope1"},
    "natural_gas": {"factor": 2.0, "unit": "m3", "scope": "Scope1"},
    "lpg": {"factor": 1.51, "unit": "kg", "scope": "Scope1"},
    "coal": {"factor": 2.42, "unit": "kg", "scope": "Scope1"},
    "fuel_oil": {"factor": 2.96, "unit": "liters", "scope": "Scope1"},
    "kerosene": {"factor": 2.52, "unit": "liters", "scope": "Scope1"},
    "propane": {"factor": 1.51, "unit": "kg", "scope": "Scope1"},
    "aviation_fuel": {"factor": 2.55, "unit": "liters", "scope": "Scope3"},
    "shipping": {"factor": 0.02, "unit": "tonne-km", "scope": "Scope3"},
    "transport": {"factor": 0.15, "unit": "km", "scope": "Scope3"},
}

ENERGY_PATTERNS = {
    "electricity": r"(?:electricity|electric|power|kwh|kilowatt|energy\s*consumption)",
    "diesel": r"(?:diesel|gasoil|gas\s*oil)",
    "petrol": r"(?:petrol|gasoline|gas|fuel)",
    "natural_gas": r"(?:natural\s*gas|lng|cng|methane)",
    "lpg": r"(?:lpg|liquefied\s*petroleum|propane|butane)",
}

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
        raise Exception(f"Error extracting text from PDF: {str(e)}")

def extract_text_from_image(file_path: str) -> str:
    """Extract text from image using Tesseract OCR"""
    try:
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        raise Exception(f"Error extracting text from image: {str(e)}")

def extract_text_from_txt(file_path: str) -> str:
    """Read text from txt file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        raise Exception(f"Error reading text file: {str(e)}")

def extract_text(file_path: str, file_type: str) -> str:
    """Extract text based on file type"""
    file_type = file_type.lower()
    
    if file_type == "pdf":
        return extract_text_from_pdf(file_path)
    elif file_type in ["jpg", "jpeg", "png"]:
        return extract_text_from_image(file_path)
    elif file_type == "txt":
        return extract_text_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

def extract_vendor_name(text: str) -> str:
    """Extract vendor name from invoice text"""
    patterns = [
        r"(?:from|vendor|supplier|company|issued\s*by)[:\s]*([A-Z][A-Za-z\s&\.]+(?:Ltd|LLC|Inc|Corp|Co\.?)?)",
        r"^([A-Z][A-Za-z\s&\.]+(?:Ltd|LLC|Inc|Corp|Co\.?)?)\s*$",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return "Unknown Vendor"

def extract_invoice_number(text: str) -> str:
    """Extract invoice number"""
    patterns = [
        r"(?:invoice|inv|bill|receipt)[\s#:no\.]*([A-Z0-9\-]+)",
        r"(?:ref|reference)[\s#:no\.]*([A-Z0-9\-]+)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return None

def extract_date(text: str) -> datetime:
    """Extract date from invoice"""
    date_patterns = [
        r"(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
        r"(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})",
        r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{2,4})",
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_str = match.group(1)
            try:
                for fmt in ["%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%d/%m/%y", "%d %B %Y", "%d %b %Y", "%B %d, %Y", "%b %d, %Y"]:
                    try:
                        return datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
                    except ValueError:
                        continue
            except:
                pass
    
    return datetime.now(timezone.utc)

def extract_quantity_and_unit(text: str, energy_type: str) -> Tuple[float, str]:
    """Extract quantity and unit for an energy type"""
    quantity_patterns = [
        r"(\d+[\d,\.]*)\s*(kwh|kw\.?h|kilowatt[\s\-]?hours?)",
        r"(\d+[\d,\.]*)\s*(lit(?:er|re)?s?|l\b|gal(?:lon)?s?)",
        r"(\d+[\d,\.]*)\s*(m3|cubic\s*met(?:er|re)?s?)",
        r"(\d+[\d,\.]*)\s*(kg|kilogram?s?)",
        r"(?:consumption|usage|quantity|total)[:\s]*(\d+[\d,\.]*)\s*(\w+)?",
        r"(\d+[\d,\.]*)\s*(?:units?)",
    ]
    
    for pattern in quantity_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            quantity = float(match.group(1).replace(",", ""))
            unit = match.group(2) if len(match.groups()) > 1 and match.group(2) else "units"
            
            # Normalize units
            unit = unit.lower().strip()
            if unit in ["kwh", "kw.h", "kilowatt hours", "kilowatt-hours"]:
                unit = "kWh"
            elif unit in ["liter", "liters", "litre", "litres", "l"]:
                unit = "liters"
            elif unit in ["m3", "cubic meters", "cubic metres"]:
                unit = "m3"
            elif unit in ["kg", "kilograms", "kilogram"]:
                unit = "kg"
            else:
                unit = "units"
            
            return quantity, unit
    
    return 0.0, "units"

def extract_cost(text: str) -> float:
    """Extract cost/amount from invoice"""
    patterns = [
        r"(?:total|amount|cost|price|due)[\s:]*[$€£₦]?\s*(\d+[\d,\.]*)",
        r"[$€£₦]\s*(\d+[\d,\.]*)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1).replace(",", ""))
    
    return 0.0

def detect_energy_types(text: str) -> List[str]:
    """Detect all energy types mentioned in the text"""
    detected = []
    text_lower = text.lower()
    
    for energy_type, pattern in ENERGY_PATTERNS.items():
        if re.search(pattern, text_lower):
            detected.append(energy_type)
    
    if not detected:
        detected = ["electricity"]  # Default assumption
    
    return detected

def calculate_emissions(quantity: float, energy_type: str) -> Tuple[float, str]:
    """Calculate CO2 emissions based on quantity and energy type"""
    energy_type = energy_type.lower()
    
    if energy_type in EMISSION_FACTORS:
        factor_data = EMISSION_FACTORS[energy_type]
        emissions = quantity * factor_data["factor"]
        scope = factor_data["scope"]
    else:
        emissions = quantity * 0.5  # Default factor
        scope = "Scope3"
    
    return emissions, scope

def parse_invoice(file_path: str, file_type: str) -> Dict[str, Any]:
    """Main function to parse invoice and extract all data"""
    text = extract_text(file_path, file_type)
    
    vendor_name = extract_vendor_name(text)
    invoice_number = extract_invoice_number(text)
    invoice_date = extract_date(text)
    cost = extract_cost(text)
    
    energy_types = detect_energy_types(text)
    
    emissions_data = []
    total_emissions = 0.0
    
    for energy_type in energy_types:
        quantity, unit = extract_quantity_and_unit(text, energy_type)
        if quantity > 0:
            co2_emissions, scope = calculate_emissions(quantity, energy_type)
            total_emissions += co2_emissions
            
            emissions_data.append({
                "energy_type": energy_type,
                "quantity": quantity,
                "unit": unit,
                "scope_type": scope,
                "co2_emissions_kg": co2_emissions,
            })
    
    # If no quantities found, create default record
    if not emissions_data:
        emissions_data.append({
            "energy_type": energy_types[0] if energy_types else "electricity",
            "quantity": 0.0,
            "unit": "units",
            "scope_type": "Scope2",
            "co2_emissions_kg": 0.0,
        })
    
    return {
        "vendor_name": vendor_name,
        "invoice_number": invoice_number,
        "invoice_date": invoice_date,
        "cost": cost,
        "raw_text": text[:2000],  # Truncate for storage
        "emissions_data": emissions_data,
        "total_emissions": total_emissions,
    }
