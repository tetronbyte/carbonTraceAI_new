# 🧮 Emission Calculation Formula - CarbonTraceAI

**Last Updated:** March 6, 2025

This document explains the exact formula and methodology used to calculate CO2 emissions in CarbonTraceAI.

---

## 📐 Core Formula

### **Basic Formula:**
```
CO2 Emissions (kg) = Quantity × Unit Conversion × Emission Factor
```

### **Step-by-Step Process:**

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Extract Data from Invoice                          │
├─────────────────────────────────────────────────────────────┤
│ - Quantity: 3,220                                           │
│ - Unit: kWh                                                 │
│ - Energy Type: Electricity                                  │
│ - Country: Kenya                                            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Normalize Unit                                      │
├─────────────────────────────────────────────────────────────┤
│ Function: normalize_unit(unit, energy_type)                 │
│                                                             │
│ Input: "kWh", "electricity"                                 │
│ Output: ("kWh", 1.0)  ← Unit conversion factor             │
│                                                             │
│ Normalized Quantity = 3,220 × 1.0 = 3,220 kWh             │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Get Emission Factor                                 │
├─────────────────────────────────────────────────────────────┤
│ Function: get_emission_factor(energy_type, country)         │
│                                                             │
│ Input: "electricity", "kenya"                               │
│ Output: 0.27 kg CO2/kWh                                     │
│                                                             │
│ Source: Country-specific emission factor database          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Calculate Emissions                                 │
├─────────────────────────────────────────────────────────────┤
│ Function: calculate_emissions(quantity, unit, type, country)│
│                                                             │
│ Formula:                                                    │
│   CO2 = Normalized Quantity × Emission Factor               │
│   CO2 = 3,220 kWh × 0.27 kg/kWh                            │
│   CO2 = 869.4 kg                                            │
│                                                             │
│ Rounded: 869.40 kg CO2e                                     │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: Classify Scope                                      │
├─────────────────────────────────────────────────────────────┤
│ Function: classify_scope(energy_type, description, category)│
│                                                             │
│ Input: "electricity"                                        │
│ Output: "Scope 2"                                           │
│                                                             │
│ Logic:                                                      │
│ - Electricity → Scope 2 (Indirect - Purchased Energy)      │
│ - Diesel/Petrol → Scope 1 (Direct Combustion)              │
│ - Water/Freight → Scope 3 (Other Indirect)                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 🌍 Emission Factors by Country

### **Kenya:**
```python
EMISSION_FACTORS["kenya"] = {
    "electricity": 0.27,  # kg CO2/kWh
    "diesel": 2.68,       # kg CO2/liter
    "petrol": 2.31,       # kg CO2/liter
    "gasoline": 2.31,     # kg CO2/liter
    "natural_gas": 2.0,   # kg CO2/m³
    "lpg": 1.51,          # kg CO2/kg
    "coal": 2.42,         # kg CO2/kg
    "generator": 2.68     # kg CO2/liter
}
```

### **Nigeria:**
```python
EMISSION_FACTORS["nigeria"] = {
    "electricity": 0.43,  # kg CO2/kWh
    "diesel": 2.68,
    "petrol": 2.31,
    # ... (same as Kenya for fuels)
}
```

### **South Africa:**
```python
EMISSION_FACTORS["south_africa"] = {
    "electricity": 0.93,  # HIGH - Coal-dominated grid
    "diesel": 2.68,
    "petrol": 2.31,
    "steel": 1.85,        # kg CO2/kg steel
    "aluminum": 8.5,      # kg CO2/kg aluminum
    "cement": 0.83        # kg CO2/kg cement
}
```

### **Default (if country not specified):**
```python
EMISSION_FACTORS["default"] = {
    "electricity": 0.50,  # Global average
    "diesel": 2.68,
    "petrol": 2.31,
    # ... standard factors
}
```

**Full List of Supported Countries:**
- Kenya, Nigeria, South Africa, Ghana, Ethiopia, Egypt
- Morocco, Tanzania, Algeria, Tunisia, Zambia, Uganda
- Rwanda, Cameroon, Ivory Coast, Senegal, Mozambique
- Zimbabwe, Botswana, Namibia, Malawi, Madagascar

---

## 🔄 Unit Conversion

### **Function:** `normalize_unit(unit, energy_type)`

**Purpose:** Convert various unit formats to standardized units

### **Electricity:**
```python
Input Units:     → Output:
"kWh"            → ("kWh", 1.0)
"kwh", "KWH"     → ("kWh", 1.0)
"MWh"            → ("kWh", 1000.0)  # 1 MWh = 1,000 kWh
"Wh"             → ("kWh", 0.001)   # 1 Wh = 0.001 kWh
```

**Example:**
```python
Quantity: 5 MWh
Conversion: 5 × 1,000 = 5,000 kWh
Emission Factor: 0.27 kg/kWh (Kenya)
CO2 = 5,000 × 0.27 = 1,350 kg
```

### **Volume (Fuels):**
```python
Input Units:     → Output:
"liters", "L"    → ("liters", 1.0)
"gallon", "gal"  → ("liters", 3.785)  # 1 gallon = 3.785 liters
"m³", "cubic m"  → ("m³", 1.0)
```

**Example:**
```python
Quantity: 50 gallons diesel
Conversion: 50 × 3.785 = 189.25 liters
Emission Factor: 2.68 kg/liter
CO2 = 189.25 × 2.68 = 507.19 kg
```

### **Mass:**
```python
Input Units:     → Output:
"kg"             → ("kg", 1.0)
"tonne", "ton"   → ("kg", 1000.0)   # 1 tonne = 1,000 kg
```

### **Gas:**
```python
Input Units:     → Output:
"m³"             → ("m³", 1.0)
"ccf"            → ("m³", 2.832)    # 100 cubic feet
"therm"          → ("m³", 2.832)
```

---

## 📊 Scope Classification

### **Function:** `classify_scope(energy_type, description, category)`

**Purpose:** Classify emissions into GHG Protocol scopes

### **Scope 1: Direct Emissions**
```
Energy Types:
- diesel
- petrol / gasoline
- natural_gas
- lpg
- coal
- generator
- company_vehicles
- owned_equipment

Examples:
✓ Diesel for company truck: Scope 1
✓ Natural gas for factory: Scope 1
✓ LPG for cooking: Scope 1
```

### **Scope 2: Indirect Energy Emissions**
```
Energy Types:
- electricity (purchased from grid)

Examples:
✓ Office electricity bill: Scope 2
✓ Factory power consumption: Scope 2
✓ HVAC system electricity: Scope 2
```

### **Scope 3: Other Indirect Emissions**
```
Energy Types:
- water
- freight
- transport (3rd party)
- waste
- business_travel
- employee_commute
- supply_chain

Examples:
✓ Water utility bill: Scope 3
✓ Freight/logistics invoice: Scope 3
✓ Business travel: Scope 3
```

---

## 🧪 Calculation Examples

### **Example 1: Kenya Power Electricity Bill**

**Invoice Data:**
```
Customer: EastAfrica Steel Components Ltd
Consumption: 3,220 kWh
Country: Kenya
```

**Calculation:**
```
STEP 1: Extract
  Quantity = 3,220
  Unit = kWh
  Energy Type = electricity
  Country = kenya

STEP 2: Normalize Unit
  Unit = kWh
  Conversion = 1.0
  Normalized Quantity = 3,220 × 1.0 = 3,220 kWh

STEP 3: Get Emission Factor
  Country = kenya
  Energy Type = electricity
  Emission Factor = 0.27 kg CO2/kWh

STEP 4: Calculate
  CO2 = 3,220 kWh × 0.27 kg/kWh
  CO2 = 869.4 kg

STEP 5: Classify Scope
  Energy Type = electricity
  Scope = Scope 2

RESULT:
  ✅ CO2 Emissions: 869.4 kg CO2e
  ✅ Scope: Scope 2
  ✅ Emission Factor Used: 0.27 kg/kWh
```

### **Example 2: Shell Diesel Receipt**

**Invoice Data:**
```
Fuel: Diesel
Quantity: 150 liters
Country: Kenya
```

**Calculation:**
```
STEP 1: Extract
  Quantity = 150
  Unit = liters
  Energy Type = diesel
  Country = kenya

STEP 2: Normalize Unit
  Unit = liters
  Conversion = 1.0
  Normalized Quantity = 150 × 1.0 = 150 liters

STEP 3: Get Emission Factor
  Country = kenya
  Energy Type = diesel
  Emission Factor = 2.68 kg CO2/liter

STEP 4: Calculate
  CO2 = 150 liters × 2.68 kg/liter
  CO2 = 402.0 kg

STEP 5: Classify Scope
  Energy Type = diesel
  Scope = Scope 1 (Direct combustion)

RESULT:
  ✅ CO2 Emissions: 402.0 kg CO2e
  ✅ Scope: Scope 1
  ✅ Emission Factor Used: 2.68 kg/liter
```

### **Example 3: Water Utility Bill**

**Invoice Data:**
```
Service: Water Supply
Consumption: 150 m³ (150,000 liters)
Country: Kenya
```

**Calculation:**
```
STEP 1: Extract
  Quantity = 150,000
  Unit = liters
  Energy Type = water
  Country = kenya

STEP 2: Normalize Unit
  Unit = liters
  Conversion = 1.0
  Normalized Quantity = 150,000 liters

STEP 3: Get Emission Factor
  Energy Type = water
  Emission Factor = 0.0003 kg CO2/liter

STEP 4: Calculate
  CO2 = 150,000 liters × 0.0003 kg/liter
  CO2 = 45.0 kg

STEP 5: Classify Scope
  Energy Type = water
  Scope = Scope 3 (Supply chain)

RESULT:
  ✅ CO2 Emissions: 45.0 kg CO2e
  ✅ Scope: Scope 3
  ✅ Emission Factor Used: 0.0003 kg/liter
```

### **Example 4: Natural Gas Bill**

**Invoice Data:**
```
Service: Natural Gas
Consumption: 50 m³
Country: Nigeria
```

**Calculation:**
```
STEP 1: Extract
  Quantity = 50
  Unit = m³
  Energy Type = natural_gas
  Country = nigeria

STEP 2: Normalize Unit
  Unit = m³
  Conversion = 1.0
  Normalized Quantity = 50 m³

STEP 3: Get Emission Factor
  Country = nigeria
  Energy Type = natural_gas
  Emission Factor = 2.0 kg CO2/m³

STEP 4: Calculate
  CO2 = 50 m³ × 2.0 kg/m³
  CO2 = 100.0 kg

STEP 5: Classify Scope
  Energy Type = natural_gas
  Scope = Scope 1 (Direct combustion)

RESULT:
  ✅ CO2 Emissions: 100.0 kg CO2e
  ✅ Scope: Scope 1
  ✅ Emission Factor Used: 2.0 kg/m³
```

---

## 🔬 Source Code Reference

### **File:** `/app/backend/services/invoice_parser.py`

**Key Functions:**

1. **`calculate_emissions(quantity, unit, energy_type, country)`** (Line 423)
   ```python
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
   ```

2. **`normalize_unit(unit, energy_type)`** (Line 379)
   - Converts various unit formats to standard units
   - Applies conversion factors

3. **`get_emission_factor(energy_type, country)`** (Line 280)
   - Retrieves country-specific emission factor
   - Falls back to default if not found

4. **`classify_scope(energy_type, description, category)`** (Line 311)
   - Classifies into Scope 1, 2, or 3
   - Based on GHG Protocol guidelines

---

## 📚 Standards & Compliance

### **Emission Factor Sources:**

1. **Electricity Factors:**
   - IEA (International Energy Agency) - 2024 Data
   - Country-specific grid emission factors

2. **Fuel Factors:**
   - IPCC Guidelines for National GHG Inventories
   - EPA Emission Factors for GHG Inventories

3. **Scope Classification:**
   - GHG Protocol Corporate Standard
   - ISO 14064-1:2018

### **Updates:**
Emission factors are reviewed annually and updated based on:
- Latest IEA country reports
- National energy mix changes
- IPCC updates

---

## 🎯 Why Kenya Uses 0.27 kg/kWh?

**Note:** In your test, you might expect 0.45 kg/kWh for Kenya (as mentioned in the original emission factors), but the **actual value in the code is 0.27 kg/kWh**.

### **Current Value:**
```python
EMISSION_FACTORS["kenya"]["electricity"] = 0.27  # kg CO2/kWh
```

### **Calculation with Current Factor:**
```
3,220 kWh × 0.27 kg/kWh = 869.4 kg CO2e
```

### **If Using 0.45 kg/kWh (Expected):**
```
3,220 kWh × 0.45 kg/kWh = 1,449.0 kg CO2e
```

**Difference:** 869.4 kg vs 1,449.0 kg (579.6 kg difference)

### **To Update Kenya's Electricity Factor:**

If you want to use 0.45 kg/kWh:

**File:** `/app/backend/services/invoice_parser.py`  
**Line:** 16

```python
# Change from:
"electricity": 0.27,

# To:
"electricity": 0.45,
```

**Reasoning for 0.45 kg/kWh:**
- Kenya's grid mix: Geothermal (45%), Hydro (30%), Thermal (25%)
- Thermal plants (diesel/HFO) increase the average
- Regional variations in grid intensity
- More conservative estimate for reporting

---

## 🔧 Customization

### **To Add New Country:**

```python
EMISSION_FACTORS["new_country"] = {
    "electricity": 0.xx,  # kg CO2/kWh
    "diesel": 2.68,       # Standard
    "petrol": 2.31,       # Standard
    "natural_gas": 2.0,   # Standard
    # Add country-specific factors
}
```

### **To Add New Energy Type:**

```python
EMISSION_FACTORS["country"]["new_energy_type"] = x.xx
```

Then update the scope classification logic if needed.

---

## ✅ Validation

All emission calculations are:
- ✅ Rounded to 2 decimal places
- ✅ Non-negative (min: 0.0)
- ✅ Stored with metadata (emission factor used, unit, quantity)
- ✅ Scope-classified automatically
- ✅ Country-specific when available

---

**Formula Summary:**
```
CO2 Emissions (kg) = Quantity × Unit Conversion × Emission Factor
```

**Example:**
```
3,220 kWh × 1.0 × 0.27 kg/kWh = 869.4 kg CO2e
```

**Version:** 1.0  
**Last Updated:** March 6, 2025
