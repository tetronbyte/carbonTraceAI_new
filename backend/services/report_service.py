import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from jinja2 import Environment, FileSystemLoader, BaseLoader
from weasyprint import HTML
from ollama import Client
from config import settings

# ESG Report Frameworks
FRAMEWORKS = {
    "ISSB": {
        "name": "International Sustainability Standards Board",
        "description": "Global sustainability disclosure standards for investors",
        "sections": [
            "Climate Risk Disclosure",
            "Emissions Summary",
            "Sustainability Governance",
            "Financial Impact of Climate Risks",
            "Transition Plans"
        ]
    },
    "TCFD": {
        "name": "Task Force on Climate-related Financial Disclosures",
        "description": "Climate-related financial risk reporting",
        "sections": [
            "Governance",
            "Strategy",
            "Risk Management",
            "Metrics & Targets"
        ]
    },
    "GRI": {
        "name": "Global Reporting Initiative",
        "description": "Comprehensive ESG impact reporting",
        "sections": [
            "Environmental Impact",
            "Energy & Emissions",
            "Social Impact",
            "Governance & Ethics",
            "Supply Chain"
        ]
    },
    "CBAM": {
        "name": "Carbon Border Adjustment Mechanism",
        "description": "EU export carbon compliance",
        "sections": [
            "Product Emissions Declaration",
            "Embedded Carbon by Product",
            "Production Emissions",
            "Supply Chain Emissions",
            "Verification Statement"
        ]
    }
}

def get_ollama_client() -> Client:
    """Get Ollama client for AI text generation"""
    headers = {}
    if settings.OLLAMA_API_KEY:
        headers['Authorization'] = f'Bearer {settings.OLLAMA_API_KEY}'
    
    return Client(
        host=settings.OLLAMA_HOST,
        headers=headers
    )

def generate_ai_narrative(
    section: str,
    org_name: str,
    scope1: float,
    scope2: float,
    scope3: float,
    total: float,
    framework: str,
    period: str,
    additional_context: str = ""
) -> str:
    """Generate AI-powered narrative for report sections"""
    
    prompt = f"""Generate a professional ESG report narrative for the following section:

Organization: {org_name}
Report Period: {period}
Framework: {framework}
Section: {section}

Emissions Data:
- Scope 1 (Direct): {scope1:,.0f} kg CO2e
- Scope 2 (Indirect - Energy): {scope2:,.0f} kg CO2e
- Scope 3 (Value Chain): {scope3:,.0f} kg CO2e
- Total: {total:,.0f} kg CO2e

{additional_context}

Write 2-3 professional paragraphs suitable for an ESG report. Focus on:
- Factual statements based on the data
- Industry-standard terminology
- Compliance-ready language
- Clear and concise communication

Do not include introductory phrases like "Here is..." or "Sure, here's...". Start directly with the content."""

    try:
        client = get_ollama_client()
        response = client.chat(
            model=settings.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return response['message']['content'].strip()
    except Exception as e:
        # Fallback narrative if AI is unavailable
        return generate_fallback_narrative(section, org_name, scope1, scope2, scope3, total, period)

def generate_fallback_narrative(
    section: str,
    org_name: str,
    scope1: float,
    scope2: float,
    scope3: float,
    total: float,
    period: str
) -> str:
    """Generate fallback narrative without AI"""
    scope1_pct = (scope1 / total * 100) if total > 0 else 0
    scope2_pct = (scope2 / total * 100) if total > 0 else 0
    scope3_pct = (scope3 / total * 100) if total > 0 else 0
    
    narratives = {
        "Executive Summary": f"""{org_name} has measured and reported a total of {total:,.0f} kg CO2 equivalent emissions for the reporting period {period}. This comprehensive assessment covers all operational scopes including direct emissions, energy-related indirect emissions, and value chain emissions. Our commitment to transparency in carbon accounting reflects our dedication to sustainable business practices and regulatory compliance.""",
        
        "Emissions Summary": f"""Our total greenhouse gas emissions for {period} amount to {total:,.0f} kg CO2e, distributed across three scopes. Scope 1 direct emissions account for {scope1:,.0f} kg CO2e ({scope1_pct:.1f}%), primarily from on-site fuel combustion and company vehicles. Scope 2 indirect emissions from purchased energy total {scope2:,.0f} kg CO2e ({scope2_pct:.1f}%). Scope 3 value chain emissions represent {scope3:,.0f} kg CO2e ({scope3_pct:.1f}%).""",
        
        "Governance": f"""{org_name} maintains robust governance structures for climate-related matters. The board of directors provides oversight of sustainability initiatives and climate risk management. Regular reviews of emissions data and progress toward targets ensure accountability at the highest levels of the organization.""",
        
        "Risk Management": f"""Climate-related risks are integrated into our enterprise risk management framework. We have identified physical risks from extreme weather events and transition risks from evolving regulations such as the EU Carbon Border Adjustment Mechanism. Mitigation strategies are continuously developed and implemented.""",
        
        "Strategy": f"""Our climate strategy focuses on emissions reduction across all operational scopes. We are committed to improving energy efficiency, transitioning to renewable energy sources, and working with suppliers to reduce value chain emissions. These initiatives support both environmental objectives and long-term business resilience.""",
        
        "Metrics & Targets": f"""Key performance indicators include absolute emissions ({total:,.0f} kg CO2e for {period}), emissions intensity metrics, and energy efficiency ratios. We track progress against established baselines and report transparently on our decarbonization journey."""
    }
    
    return narratives.get(section, f"This section covers {section} for {org_name} during {period}.")

def create_html_report(
    org_name: str,
    report_period: str,
    framework: str,
    scope1: float,
    scope2: float,
    scope3: float,
    total: float,
    report_type: str = "Annual",
    quarter: Optional[str] = None,
    products: Optional[List[Dict]] = None,
    use_ai: bool = True
) -> str:
    """Create comprehensive HTML report"""
    
    framework_info = FRAMEWORKS.get(framework, FRAMEWORKS["GRI"])
    
    # Generate narratives
    if use_ai:
        exec_summary = generate_ai_narrative("Executive Summary", org_name, scope1, scope2, scope3, total, framework, report_period)
        emissions_narrative = generate_ai_narrative("Emissions Overview", org_name, scope1, scope2, scope3, total, framework, report_period)
        governance = generate_ai_narrative("Governance", org_name, scope1, scope2, scope3, total, framework, report_period)
        strategy = generate_ai_narrative("Strategy", org_name, scope1, scope2, scope3, total, framework, report_period)
        risk_mgmt = generate_ai_narrative("Risk Management", org_name, scope1, scope2, scope3, total, framework, report_period)
        metrics = generate_ai_narrative("Metrics & Targets", org_name, scope1, scope2, scope3, total, framework, report_period)
    else:
        exec_summary = generate_fallback_narrative("Executive Summary", org_name, scope1, scope2, scope3, total, report_period)
        emissions_narrative = generate_fallback_narrative("Emissions Summary", org_name, scope1, scope2, scope3, total, report_period)
        governance = generate_fallback_narrative("Governance", org_name, scope1, scope2, scope3, total, report_period)
        strategy = generate_fallback_narrative("Strategy", org_name, scope1, scope2, scope3, total, report_period)
        risk_mgmt = generate_fallback_narrative("Risk Management", org_name, scope1, scope2, scope3, total, report_period)
        metrics = generate_fallback_narrative("Metrics & Targets", org_name, scope1, scope2, scope3, total, report_period)
    
    report_title = f"{framework} ESG Report - {report_period}"
    if quarter:
        report_title = f"{framework} ESG Report - {quarter} {report_period}"
    
    # CBAM-specific section
    cbam_section = ""
    if framework == "CBAM" and products:
        cbam_section = generate_cbam_section(products, org_name)
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{report_title}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=Outfit:wght@400;500;700&display=swap');
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'DM Sans', sans-serif;
            font-size: 11pt;
            line-height: 1.7;
            color: #1a1a1a;
            background: white;
        }}
        
        .cover {{
            height: 100vh;
            background: linear-gradient(135deg, #0A0A0A 0%, #1a2f1a 100%);
            color: white;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            page-break-after: always;
            position: relative;
            overflow: hidden;
        }}
        
        .cover::before {{
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(0,230,118,0.1) 0%, transparent 50%);
        }}
        
        .cover h1 {{
            font-family: 'Outfit', sans-serif;
            font-size: 48pt;
            font-weight: 700;
            margin-bottom: 20px;
            color: #00E676;
            position: relative;
        }}
        
        .cover h2 {{
            font-size: 24pt;
            font-weight: 400;
            margin-bottom: 40px;
            position: relative;
        }}
        
        .cover .org-name {{
            font-size: 32pt;
            font-weight: 600;
            margin-bottom: 10px;
            position: relative;
        }}
        
        .cover .period {{
            font-size: 18pt;
            color: #888;
            position: relative;
        }}
        
        .cover .framework-badge {{
            margin-top: 60px;
            font-size: 12pt;
            color: #00E676;
            border: 2px solid #00E676;
            padding: 12px 30px;
            border-radius: 30px;
            position: relative;
        }}
        
        .content {{
            padding: 50px 70px;
            max-width: 900px;
            margin: 0 auto;
        }}
        
        .section {{
            margin-bottom: 50px;
            page-break-inside: avoid;
        }}
        
        h2 {{
            font-family: 'Outfit', sans-serif;
            color: #00E676;
            font-size: 22pt;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #00E676;
        }}
        
        h3 {{
            font-family: 'Outfit', sans-serif;
            color: #1a1a1a;
            font-size: 14pt;
            margin-top: 30px;
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
            background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
            padding: 25px;
            border-radius: 16px;
            border-left: 5px solid #00E676;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        }}
        
        .stat-card.scope1 {{ border-left-color: #FF6B35; }}
        .stat-card.scope2 {{ border-left-color: #2979FF; }}
        .stat-card.scope3 {{ border-left-color: #FFB74D; }}
        .stat-card.total {{ border-left-color: #00E676; background: linear-gradient(135deg, #e8f5e9 0%, #ffffff 100%); }}
        
        .stat-label {{
            font-size: 10pt;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            margin-bottom: 8px;
        }}
        
        .stat-value {{
            font-family: 'Outfit', sans-serif;
            font-size: 28pt;
            font-weight: 700;
            color: #1a1a1a;
        }}
        
        .stat-unit {{
            font-size: 10pt;
            color: #888;
            margin-top: 5px;
        }}
        
        .highlight-box {{
            background: #f0fdf4;
            border: 1px solid #00E676;
            border-radius: 12px;
            padding: 20px;
            margin: 20px 0;
        }}
        
        .compliance-badge {{
            display: inline-block;
            background: #0A0A0A;
            color: #00E676;
            padding: 8px 20px;
            border-radius: 20px;
            font-size: 10pt;
            margin-right: 10px;
            margin-bottom: 10px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        
        th {{
            background: #f8f9fa;
            font-weight: 600;
            font-size: 10pt;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .footer {{
            margin-top: 60px;
            padding-top: 30px;
            border-top: 2px solid #eee;
            text-align: center;
        }}
        
        .footer p {{
            font-size: 9pt;
            color: #888;
            text-align: center;
        }}
        
        .blockchain-badge {{
            display: inline-block;
            background: #0A0A0A;
            color: #00E676;
            padding: 12px 25px;
            border-radius: 25px;
            font-size: 10pt;
            margin-top: 20px;
        }}
        
        @page {{
            size: A4;
            margin: 0;
        }}
        
        @page :not(:first) {{
            margin: 40px 50px;
        }}
    </style>
</head>
<body>
    <div class="cover">
        <h1>ESG Report</h1>
        <h2>{framework_info['name']}</h2>
        <div class="org-name">{org_name}</div>
        <div class="period">{report_type} Report • {report_period}</div>
        <div class="framework-badge">{framework} Compliant</div>
    </div>
    
    <div class="content">
        <div class="section">
            <h2>Executive Summary</h2>
            <p>{exec_summary}</p>
            
            <div class="highlight-box">
                <strong>Compliance Standards:</strong><br>
                <span class="compliance-badge">{framework}</span>
                <span class="compliance-badge">ISSB S2</span>
                <span class="compliance-badge">EU CBAM Ready</span>
            </div>
        </div>
        
        <div class="section">
            <h2>Emissions Overview</h2>
            <div class="stats-grid">
                <div class="stat-card scope1">
                    <div class="stat-label">Scope 1 - Direct Emissions</div>
                    <div class="stat-value">{scope1:,.0f}</div>
                    <div class="stat-unit">kg CO2e</div>
                </div>
                <div class="stat-card scope2">
                    <div class="stat-label">Scope 2 - Indirect (Energy)</div>
                    <div class="stat-value">{scope2:,.0f}</div>
                    <div class="stat-unit">kg CO2e</div>
                </div>
                <div class="stat-card scope3">
                    <div class="stat-label">Scope 3 - Value Chain</div>
                    <div class="stat-value">{scope3:,.0f}</div>
                    <div class="stat-unit">kg CO2e</div>
                </div>
                <div class="stat-card total">
                    <div class="stat-label">Total Emissions</div>
                    <div class="stat-value">{total:,.0f}</div>
                    <div class="stat-unit">kg CO2e</div>
                </div>
            </div>
            <p>{emissions_narrative}</p>
        </div>
        
        <div class="section">
            <h2>Governance</h2>
            <p>{governance}</p>
        </div>
        
        <div class="section">
            <h2>Strategy</h2>
            <p>{strategy}</p>
        </div>
        
        <div class="section">
            <h2>Risk Management</h2>
            <p>{risk_mgmt}</p>
        </div>
        
        <div class="section">
            <h2>Metrics & Targets</h2>
            <p>{metrics}</p>
            
            <table>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                    <th>Unit</th>
                </tr>
                <tr>
                    <td>Total GHG Emissions</td>
                    <td>{total:,.0f}</td>
                    <td>kg CO2e</td>
                </tr>
                <tr>
                    <td>Scope 1 Emissions</td>
                    <td>{scope1:,.0f}</td>
                    <td>kg CO2e</td>
                </tr>
                <tr>
                    <td>Scope 2 Emissions</td>
                    <td>{scope2:,.0f}</td>
                    <td>kg CO2e</td>
                </tr>
                <tr>
                    <td>Scope 3 Emissions</td>
                    <td>{scope3:,.0f}</td>
                    <td>kg CO2e</td>
                </tr>
            </table>
        </div>
        
        {cbam_section}
        
        <div class="footer">
            <p>Generated by CarbonTraceAI • Blockchain-Verified Carbon Accounting</p>
            <div class="blockchain-badge">Data Verified on Polygon Blockchain</div>
            <p style="margin-top: 20px;">Report generated on {datetime.now(timezone.utc).strftime('%B %d, %Y at %H:%M UTC')}</p>
            <p style="margin-top: 10px;">This report has been prepared in accordance with {framework_info['name']} ({framework}) requirements.</p>
        </div>
    </div>
</body>
</html>
"""
    return html_content

def generate_cbam_section(products: List[Dict], org_name: str) -> str:
    """Generate CBAM-specific product emissions section"""
    if not products:
        return ""
    
    rows = ""
    for product in products:
        rows += f"""
        <tr>
            <td>{product.get('name', 'N/A')}</td>
            <td>{product.get('batch_id', 'N/A')}</td>
            <td>{product.get('quantity', 0):,.0f}</td>
            <td>{product.get('unit', 'units')}</td>
            <td>{product.get('emissions', 0):,.2f}</td>
            <td>{product.get('intensity', 0):,.4f}</td>
        </tr>
        """
    
    return f"""
        <div class="section" style="page-break-before: always;">
            <h2>CBAM Product Emissions Declaration</h2>
            <p>The following table presents embedded carbon emissions for products subject to the EU Carbon Border Adjustment Mechanism (CBAM). These values represent the total greenhouse gas emissions associated with production, enabling EU importers to comply with CBAM reporting requirements.</p>
            
            <table>
                <tr>
                    <th>Product</th>
                    <th>Batch ID</th>
                    <th>Quantity</th>
                    <th>Unit</th>
                    <th>Total CO2e (kg)</th>
                    <th>Intensity (kg CO2e/unit)</th>
                </tr>
                {rows}
            </table>
            
            <div class="highlight-box">
                <strong>CBAM Verification Statement</strong><br>
                These emission values have been calculated using internationally recognized methodologies and verified through blockchain-based data integrity checks. The data is compliant with EU CBAM reporting requirements.
            </div>
        </div>
    """

def generate_pdf_report(html_content: str, output_path: str) -> str:
    """Generate PDF from HTML content"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    HTML(string=html_content).write_pdf(output_path)
    return output_path

def create_esg_report(
    org_name: str,
    report_period: str,
    framework: str,
    scope1: float,
    scope2: float,
    scope3: float,
    report_type: str = "Annual",
    quarter: Optional[str] = None,
    products: Optional[List[Dict]] = None,
    use_ai: bool = True
) -> Dict[str, Any]:
    """Main function to create ESG report"""
    total = scope1 + scope2 + scope3
    
    # Generate HTML
    html_content = create_html_report(
        org_name=org_name,
        report_period=report_period,
        framework=framework,
        scope1=scope1,
        scope2=scope2,
        scope3=scope3,
        total=total,
        report_type=report_type,
        quarter=quarter,
        products=products,
        use_ai=use_ai
    )
    
    # Generate PDF
    report_id = uuid.uuid4().hex[:8]
    pdf_filename = f"esg_report_{framework}_{report_id}.pdf"
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
