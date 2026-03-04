import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS
from config import settings

# ESG Report Templates
COMPLIANCE_STANDARDS = {
    "GRI": {
        "name": "Global Reporting Initiative",
        "sections": ["Organizational Profile", "Material Topics", "Emissions Data", "Governance"],
    },
    "TCFD": {
        "name": "Task Force on Climate-related Financial Disclosures",
        "sections": ["Governance", "Strategy", "Risk Management", "Metrics and Targets"],
    },
    "CDP": {
        "name": "Carbon Disclosure Project",
        "sections": ["Introduction", "Governance", "Risks & Opportunities", "Emissions Data", "Verification"],
    },
    "BRSR": {
        "name": "Business Responsibility and Sustainability Reporting",
        "sections": ["General Disclosures", "Management & Process", "Principle Wise Performance"],
    },
    "ISO14064": {
        "name": "ISO 14064 Greenhouse Gas Standard",
        "sections": ["Organization Boundaries", "GHG Inventory", "Quantification", "Reporting"],
    },
}

def generate_executive_summary(org_name: str, total_emissions: float, period: str) -> str:
    """Generate executive summary"""
    return f"""
This Environmental, Social, and Governance (ESG) Report presents the carbon emissions data 
for {org_name} for the reporting period {period}. Our organization has measured and reported 
a total of {total_emissions:,.2f} kg CO2 equivalent emissions across all operational scopes.

This report demonstrates our commitment to environmental transparency and sustainable 
business practices. We have implemented robust carbon accounting methodologies to ensure 
accuracy and compliance with international reporting standards.
"""

def generate_emissions_overview(scope1: float, scope2: float, scope3: float, total: float) -> str:
    """Generate emissions overview section"""
    scope1_pct = (scope1 / total * 100) if total > 0 else 0
    scope2_pct = (scope2 / total * 100) if total > 0 else 0
    scope3_pct = (scope3 / total * 100) if total > 0 else 0
    
    return f"""
Our total greenhouse gas (GHG) emissions for this reporting period amount to {total:,.2f} kg CO2e.

Scope 1 (Direct Emissions): {scope1:,.2f} kg CO2e ({scope1_pct:.1f}%)
These emissions result from sources owned or controlled by our organization, including 
company vehicles, on-site fuel combustion, and direct process emissions.

Scope 2 (Indirect - Energy): {scope2:,.2f} kg CO2e ({scope2_pct:.1f}%)
These emissions are from purchased electricity, steam, heating, and cooling consumed 
by our operations.

Scope 3 (Value Chain): {scope3:,.2f} kg CO2e ({scope3_pct:.1f}%)
These emissions occur in our value chain, including business travel, employee commuting, 
and upstream/downstream activities.
"""

def generate_governance_section(org_name: str) -> str:
    """Generate governance section"""
    return f"""
{org_name} has established a comprehensive governance framework for managing climate-related 
risks and opportunities. Our Board of Directors maintains oversight of climate-related matters, 
with dedicated committees responsible for environmental strategy and performance monitoring.

Key governance measures include:
- Regular board-level review of carbon emissions data
- Integration of climate considerations into strategic planning
- Stakeholder engagement on environmental matters
- Third-party verification of emissions data through blockchain technology
"""

def generate_risk_section() -> str:
    """Generate risk analysis section"""
    return """
Climate-related risks have been identified and assessed across our operations:

Physical Risks:
- Acute risks from extreme weather events
- Chronic risks from changing climate patterns

Transition Risks:
- Policy and regulatory changes
- Market shifts toward low-carbon alternatives
- Reputational considerations

We are actively working to mitigate these risks through our decarbonization strategy 
and continuous monitoring of our carbon footprint.
"""

def create_html_report(
    org_name: str,
    report_period: str,
    compliance_standard: str,
    scope1: float,
    scope2: float,
    scope3: float,
    total: float,
    quarter: Optional[str] = None,
) -> str:
    """Create HTML content for the report"""
    
    standard_info = COMPLIANCE_STANDARDS.get(compliance_standard, COMPLIANCE_STANDARDS["GRI"])
    
    executive_summary = generate_executive_summary(org_name, total, report_period)
    emissions_overview = generate_emissions_overview(scope1, scope2, scope3, total)
    governance_section = generate_governance_section(org_name)
    risk_section = generate_risk_section()
    
    report_title = f"ESG Report - {report_period}"
    if quarter:
        report_title = f"ESG Report - {quarter} {report_period}"
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{report_title}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap');
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'DM Sans', sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #1a1a1a;
            background: white;
        }}
        
        .cover {{
            height: 100vh;
            background: linear-gradient(135deg, #0A0A0A 0%, #1a1a1a 100%);
            color: white;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            page-break-after: always;
        }}
        
        .cover h1 {{
            font-size: 42pt;
            font-weight: 700;
            margin-bottom: 20px;
            color: #00E676;
        }}
        
        .cover h2 {{
            font-size: 24pt;
            font-weight: 400;
            margin-bottom: 40px;
        }}
        
        .cover .org-name {{
            font-size: 28pt;
            font-weight: 500;
            margin-bottom: 10px;
        }}
        
        .cover .period {{
            font-size: 18pt;
            color: #888;
        }}
        
        .cover .standard {{
            margin-top: 60px;
            font-size: 12pt;
            color: #00E676;
            border: 1px solid #00E676;
            padding: 10px 20px;
            border-radius: 20px;
        }}
        
        .content {{
            padding: 60px 80px;
        }}
        
        h2 {{
            color: #00E676;
            font-size: 20pt;
            margin-top: 40px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #00E676;
        }}
        
        h3 {{
            color: #1a1a1a;
            font-size: 14pt;
            margin-top: 25px;
            margin-bottom: 15px;
        }}
        
        p {{
            margin-bottom: 15px;
            text-align: justify;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin: 30px 0;
        }}
        
        .stat-card {{
            background: #f5f5f5;
            padding: 25px;
            border-radius: 12px;
            border-left: 4px solid #00E676;
        }}
        
        .stat-card.scope1 {{ border-left-color: #FF6B35; }}
        .stat-card.scope2 {{ border-left-color: #2979FF; }}
        .stat-card.scope3 {{ border-left-color: #FFB74D; }}
        .stat-card.total {{ border-left-color: #00E676; }}
        
        .stat-label {{
            font-size: 10pt;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .stat-value {{
            font-size: 24pt;
            font-weight: 700;
            color: #1a1a1a;
            margin-top: 5px;
        }}
        
        .stat-unit {{
            font-size: 10pt;
            color: #888;
        }}
        
        .footer {{
            margin-top: 60px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            font-size: 9pt;
            color: #888;
            text-align: center;
        }}
        
        .blockchain-badge {{
            background: #0A0A0A;
            color: #00E676;
            padding: 10px 20px;
            border-radius: 8px;
            display: inline-block;
            margin-top: 20px;
            font-size: 10pt;
        }}
        
        @page {{
            size: A4;
            margin: 0;
        }}
        
        @page :not(:first) {{
            margin: 40px;
        }}
    </style>
</head>
<body>
    <div class="cover">
        <h1>ESG Report</h1>
        <h2>Environmental, Social & Governance</h2>
        <div class="org-name">{org_name}</div>
        <div class="period">{report_period}</div>
        <div class="standard">Compliant with {standard_info['name']}</div>
    </div>
    
    <div class="content">
        <h2>Executive Summary</h2>
        <p>{executive_summary}</p>
        
        <h2>Emissions Overview</h2>
        <div class="stats-grid">
            <div class="stat-card scope1">
                <div class="stat-label">Scope 1 Emissions</div>
                <div class="stat-value">{scope1:,.0f}</div>
                <div class="stat-unit">kg CO2e</div>
            </div>
            <div class="stat-card scope2">
                <div class="stat-label">Scope 2 Emissions</div>
                <div class="stat-value">{scope2:,.0f}</div>
                <div class="stat-unit">kg CO2e</div>
            </div>
            <div class="stat-card scope3">
                <div class="stat-label">Scope 3 Emissions</div>
                <div class="stat-value">{scope3:,.0f}</div>
                <div class="stat-unit">kg CO2e</div>
            </div>
            <div class="stat-card total">
                <div class="stat-label">Total Emissions</div>
                <div class="stat-value">{total:,.0f}</div>
                <div class="stat-unit">kg CO2e</div>
            </div>
        </div>
        <p>{emissions_overview}</p>
        
        <h2>Governance</h2>
        <p>{governance_section}</p>
        
        <h2>Risk Analysis</h2>
        <p>{risk_section}</p>
        
        <div class="footer">
            <p>Generated by CarbonTraceAI | Blockchain-Verified Carbon Accounting</p>
            <div class="blockchain-badge">Data Verified on Polygon Blockchain</div>
            <p style="margin-top: 20px;">Report generated on {datetime.now(timezone.utc).strftime('%B %d, %Y')}</p>
        </div>
    </div>
</body>
</html>
"""
    return html_content

def generate_pdf_report(html_content: str, output_path: str) -> str:
    """Generate PDF from HTML content"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    HTML(string=html_content).write_pdf(output_path)
    
    return output_path

def create_esg_report(
    org_name: str,
    report_period: str,
    compliance_standard: str,
    scope1: float,
    scope2: float,
    scope3: float,
    quarter: Optional[str] = None,
) -> Dict[str, Any]:
    """Main function to create ESG report"""
    total = scope1 + scope2 + scope3
    
    # Generate HTML
    html_content = create_html_report(
        org_name=org_name,
        report_period=report_period,
        compliance_standard=compliance_standard,
        scope1=scope1,
        scope2=scope2,
        scope3=scope3,
        total=total,
        quarter=quarter,
    )
    
    # Generate PDF
    report_id = uuid.uuid4().hex[:8]
    pdf_filename = f"esg_report_{report_id}.pdf"
    pdf_path = os.path.join(settings.REPORTS_DIR, pdf_filename)
    
    generate_pdf_report(html_content, pdf_path)
    
    return {
        "html_content": html_content,
        "pdf_path": pdf_path,
        "total_emissions": total,
        "scope1_emissions": scope1,
        "scope2_emissions": scope2,
        "scope3_emissions": scope3,
    }
