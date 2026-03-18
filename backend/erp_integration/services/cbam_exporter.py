"""
CBAM XML Export Service

Generates CBAM-compliant XML files from normalized ERP data.
Based on EU CBAM reporting requirements.
"""
from typing import List, Dict, Any
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
from xml.dom import minidom
from ..services.database import db_service


class CBAMXMLExporter:
    """Generate CBAM-compliant XML exports."""
    
    def __init__(self):
        self.version = "1.0"
        self.schema_version = "1.0.0"
    
    async def generate_cbam_xml(
        self,
        tenant_id: str,
        job_id: str = None,
        from_date: str = None,
        to_date: str = None
    ) -> str:
        """
        Generate CBAM XML report from normalized data.
        
        Args:
            tenant_id: Tenant identifier
            job_id: Optional job ID to filter records
            from_date: Optional start date filter
            to_date: Optional end date filter
        
        Returns:
            XML string formatted according to CBAM specifications
        """
        # Fetch normalized records
        records = await db_service.get_normalized_records(
            tenant_id=tenant_id,
            from_date=from_date,
            to_date=to_date,
            limit=10000
        )
        
        # Get tenant ERP config for metadata
        configs = await db_service.get_all_erp_configs(tenant_id)
        
        # Build XML
        root = ET.Element("CBAMReport")
        root.set("version", self.schema_version)
        root.set("xmlns", "http://ec.europa.eu/cbam/reporting")
        
        # Header
        header = ET.SubElement(root, "Header")
        ET.SubElement(header, "ReportingPeriod").text = self._get_reporting_period(from_date, to_date)
        ET.SubElement(header, "ReportDate").text = datetime.now(timezone.utc).isoformat()
        ET.SubElement(header, "TenantID").text = tenant_id
        
        if configs:
            ET.SubElement(header, "Country").text = configs[0].country
            ET.SubElement(header, "Sector").text = configs[0].cbam_sector
        
        # Goods section
        goods = ET.SubElement(root, "Goods")
        ET.SubElement(goods, "TotalGoods").text = str(len(records))
        
        # Group records by item_code
        grouped_records = self._group_records_by_item(records)
        
        for item_code, item_records in grouped_records.items():
            good = ET.SubElement(goods, "Good")
            ET.SubElement(good, "GoodID").text = item_code or "UNKNOWN"
            ET.SubElement(good, "CNCode").text = item_code or "0000.00.00"
            
            # Aggregate emissions
            total_co2 = sum(r.get("co2_kg_estimate", 0) for r in item_records)
            total_quantity = sum(r.get("quantity", 0) for r in item_records)
            
            emissions_elem = ET.SubElement(good, "Emissions")
            ET.SubElement(emissions_elem, "TotalCO2").text = f"{total_co2:.2f}"
            ET.SubElement(emissions_elem, "Unit").text = "kg CO2"
            
            quantity_elem = ET.SubElement(good, "Quantity")
            ET.SubElement(quantity_elem, "Value").text = f"{total_quantity:.2f}"
            ET.SubElement(quantity_elem, "Unit").text = item_records[0].get("unit_normalized", "kg") if item_records else "kg"
            
            # Production processes
            processes = ET.SubElement(good, "ProductionProcesses")
            
            for record in item_records:
                process = ET.SubElement(processes, "Process")
                ET.SubElement(process, "ProcessType").text = record.get("module", "production")
                ET.SubElement(process, "ActivityDate").text = record.get("activity_date", "")
                ET.SubElement(process, "CO2Emissions").text = f"{record.get('co2_kg_estimate', 0):.2f}"
                
                # Add source information
                source = ET.SubElement(process, "DataSource")
                ET.SubElement(source, "ERPSystem").text = record.get("source_erp", "unknown")
                ET.SubElement(source, "RecordID").text = record.get("raw_extraction_id", "")
        
        # Footer with summary
        footer = ET.SubElement(root, "Summary")
        total_emissions = sum(r.get("co2_kg_estimate", 0) for r in records)
        ET.SubElement(footer, "TotalEmissions").text = f"{total_emissions:.2f}"
        ET.SubElement(footer, "EmissionsUnit").text = "kg CO2"
        ET.SubElement(footer, "RecordCount").text = str(len(records))
        ET.SubElement(footer, "GeneratedBy").text = "CarbonTraceAI ERP Integration"
        
        # Convert to pretty XML string
        xml_str = self._prettify_xml(root)
        return xml_str
    
    def _get_reporting_period(self, from_date: str = None, to_date: str = None) -> str:
        """Get reporting period string."""
        if from_date and to_date:
            return f"{from_date} to {to_date}"
        elif from_date:
            return f"From {from_date}"
        elif to_date:
            return f"Until {to_date}"
        else:
            current_year = datetime.now().year
            return f"Q1 {current_year}"
    
    def _group_records_by_item(self, records: List[Dict]) -> Dict[str, List[Dict]]:
        """Group records by item_code."""
        grouped = {}
        for record in records:
            # Convert Pydantic model to dict if needed
            if hasattr(record, 'dict'):
                record_dict = record.dict()
            else:
                record_dict = record
            
            item_code = record_dict.get("item_code", "UNKNOWN")
            if item_code not in grouped:
                grouped[item_code] = []
            grouped[item_code].append(record_dict)
        
        return grouped
    
    def _prettify_xml(self, elem: ET.Element) -> str:
        """Return a pretty-printed XML string."""
        rough_string = ET.tostring(elem, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")
    
    async def validate_cbam_export(
        self,
        xml_content: str
    ) -> Dict[str, Any]:
        """
        Validate CBAM XML against basic requirements.
        
        Returns validation result with any errors/warnings.
        """
        try:
            # Parse XML
            root = ET.fromstring(xml_content)
            
            validation_result = {
                "valid": True,
                "errors": [],
                "warnings": []
            }
            
            # Check required elements
            if root.find("Header") is None:
                validation_result["errors"].append("Missing required element: Header")
                validation_result["valid"] = False
            
            if root.find("Goods") is None:
                validation_result["errors"].append("Missing required element: Goods")
                validation_result["valid"] = False
            
            if root.find("Summary") is None:
                validation_result["warnings"].append("Missing recommended element: Summary")
            
            # Check goods have required data
            goods = root.find("Goods")
            if goods is not None:
                good_elements = goods.findall("Good")
                if len(good_elements) == 0:
                    validation_result["warnings"].append("No goods found in report")
                
                for good in good_elements:
                    if good.find("Emissions") is None:
                        good_id = good.find('GoodID')
                        good_id_text = good_id.text if good_id is not None else "Unknown"
                        validation_result["errors"].append(f"Good {good_id_text} missing Emissions data")
                        validation_result["valid"] = False
            
            return validation_result
            
        except ET.ParseError as e:
            return {
                "valid": False,
                "errors": [f"XML parsing error: {str(e)}"],
                "warnings": []
            }


# Global exporter instance
cbam_exporter = CBAMXMLExporter()
