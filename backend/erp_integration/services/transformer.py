"""Data transformation service for ERP records."""
import json
from typing import Dict, Any, Optional
from functools import reduce
from decimal import Decimal
from pathlib import Path


class FieldMapper:
    """Maps ERP-specific fields to normalized schema."""
    
    def __init__(self):
        config_path = Path(__file__).parent.parent / "config" / "field_mapping.json"
        with open(config_path) as f:
            self.mappings = json.load(f)
    
    def resolve_field(self, payload: Dict, path: str) -> Any:
        """Resolve dot-notation paths like 'currency_id.name' from nested dict."""
        if not path:
            return None
        
        # Handle array notation like 'invoice_line_ids[]'
        if '[]' in path:
            array_path, rest = path.split('[]', 1)
            array = self.resolve_field(payload, array_path)
            if not array or not isinstance(array, list):
                return []
            if rest:
                return [self.resolve_field(item, rest.lstrip('.')) for item in array]
            return array
        
        # Handle dot notation
        parts = path.split(".")
        try:
            return reduce(
                lambda d, k: d.get(k) if isinstance(d, dict) else None,
                parts,
                payload
            )
        except (KeyError, TypeError, AttributeError):
            return None
    
    def map_record(self, erp_type: str, module: str, raw: Dict) -> Dict[str, Any]:
        """Map raw ERP record to normalized field names."""
        if erp_type not in self.mappings:
            raise ValueError(f"No mapping for ERP type: {erp_type}")
        
        if module not in self.mappings[erp_type]:
            raise ValueError(f"No mapping for module {module} in {erp_type}")
        
        mapping = self.mappings[erp_type][module]
        mapped = {}
        
        for field, path in mapping.items():
            value = self.resolve_field(raw, path)
            if value is not None:
                mapped[field] = value
        
        return mapped


class UnitConverter:
    """Converts various units to normalized CBAM units."""
    
    # Unit conversion factors to base units
    CONVERSIONS = {
        # Weight/Mass to kg
        "tonne": ("kg", 1000),
        "ton": ("kg", 1000),
        "mt": ("kg", 1000),
        "kg": ("kg", 1),
        "g": ("kg", 0.001),
        "lb": ("kg", 0.453592),
        "long ton": ("kg", 1016.05),
        
        # Energy to kWh
        "kwh": ("kwh", 1),
        "mwh": ("kwh", 1000),
        "gj": ("kwh", 277.778),
        "mj": ("kwh", 0.277778),
        "kj": ("kwh", 0.000277778),
        "btu": ("kwh", 0.000293071),
        "therm": ("kwh", 29.3071),
        
        # Volume to litre
        "litre": ("litre", 1),
        "liter": ("litre", 1),
        "l": ("litre", 1),
        "m3": ("litre", 1000),
        "gallon": ("litre", 3.78541),
        "gal": ("litre", 3.78541),
    }
    
    def convert(self, quantity: float, from_unit: str, to_unit: str = None) -> tuple[float, str]:
        """
        Convert quantity from one unit to normalized unit.
        
        Returns:
            (converted_quantity, normalized_unit)
        """
        from_unit = from_unit.lower().strip()
        
        if from_unit not in self.CONVERSIONS:
            # Try to infer - if it's weight-like, assume kg
            if any(w in from_unit for w in ["kg", "ton", "mt"]):
                return quantity, "kg"
            elif any(e in from_unit for e in ["kwh", "mwh", "gj"]):
                return quantity, "kwh"
            else:
                return quantity, from_unit  # Return as-is
        
        base_unit, factor = self.CONVERSIONS[from_unit]
        converted = quantity * factor
        
        # Convert to preferred CBAM unit
        if base_unit == "kg" and converted >= 1000:
            return converted / 1000, "tonne"
        
        return converted, base_unit
    
    def normalize_for_cbam(self, quantity: float, unit: str, cbam_sector: str) -> tuple[float, str]:
        """
        Normalize to CBAM-preferred units based on sector.
        
        - Cement, Steel, Aluminum: tonnes
        - Energy: kWh or GJ
        - Fertilizer: tonnes
        """
        converted_qty, base_unit = self.convert(quantity, unit)
        
        # Sector-specific normalization
        if cbam_sector in {"cement", "steel", "aluminum", "fertilizer", "iron"}:
            if base_unit == "kg":
                return converted_qty / 1000, "tonne"
            elif base_unit == "tonne":
                return converted_qty, "tonne"
        
        return converted_qty, base_unit


class CurrencyConverter:
    """Convert currencies to EUR for CBAM reporting."""
    
    # Simplified static rates - in production, use real-time API
    RATES_TO_EUR = {
        "EUR": 1.0,
        "USD": 0.92,
        "GBP": 1.16,
        "ZAR": 0.049,  # South African Rand
        "KES": 0.0071,  # Kenyan Shilling
        "TZS": 0.00035,  # Tanzanian Shilling
        "MAD": 0.092,  # Moroccan Dirham
        "EGP": 0.019,  # Egyptian Pound
        "MZN": 0.015,  # Mozambican Metical
        "ZWL": 0.0028,  # Zimbabwean Dollar
    }
    
    def convert_to_eur(self, amount: float, from_currency: str) -> Optional[float]:
        """Convert amount to EUR."""
        currency = from_currency.upper().strip()
        rate = self.RATES_TO_EUR.get(currency)
        
        if not rate:
            return None
        
        return amount * rate


class EmissionFactorMapper:
    """Map materials/activities to emission factors."""
    
    # Simplified emission factors (kg CO2e per unit)
    # In production, load from database
    FACTORS = {
        # Energy (kg CO2e per kWh)
        "electricity_grid_za": 0.95,  # South Africa (coal-heavy)
        "electricity_grid_ke": 0.45,  # Kenya (renewable mix)
        "electricity_grid_ma": 0.72,  # Morocco
        "electricity_grid_eg": 0.58,  # Egypt
        "natural_gas": 0.18,  # per kWh
        "diesel": 0.27,  # per litre
        
        # Production (kg CO2e per tonne output)
        "cement_production": 900,
        "steel_production": 1800,
        "aluminum_production": 11000,
        "fertilizer_ammonia": 2500,
        
        # Materials (kg CO2e per tonne)
        "iron_ore": 50,
        "limestone": 45,
        "coke": 3500,
    }
    
    def get_factor(self, material_code: str, cbam_sector: str, country: str = None) -> Optional[float]:
        """Get emission factor for material/activity."""
        # Try exact match
        if material_code in self.FACTORS:
            return self.FACTORS[material_code]
        
        # Try sector-based defaults
        if cbam_sector == "cement":
            return self.FACTORS.get("cement_production")
        elif cbam_sector in {"steel", "iron"}:
            return self.FACTORS.get("steel_production")
        elif cbam_sector == "aluminum":
            return self.FACTORS.get("aluminum_production")
        elif cbam_sector == "fertilizer":
            return self.FACTORS.get("fertilizer_ammonia")
        
        # Try country-specific electricity
        if country and "electricity" in material_code.lower():
            grid_key = f"electricity_grid_{country.lower()}"
            return self.FACTORS.get(grid_key)
        
        return None
    
    def calculate_emissions(
        self, 
        quantity: float, 
        unit: str, 
        material_code: str,
        cbam_sector: str,
        country: str = None
    ) -> Optional[float]:
        """
        Calculate CO2e emissions.
        
        Returns:
            CO2e in kg, or None if no factor available
        """
        factor = self.get_factor(material_code, cbam_sector, country)
        if not factor:
            return None
        
        # Factor is per normalized unit
        # Ensure quantity is in correct unit
        converter = UnitConverter()
        normalized_qty, normalized_unit = converter.normalize_for_cbam(quantity, unit, cbam_sector)
        
        return normalized_qty * factor
