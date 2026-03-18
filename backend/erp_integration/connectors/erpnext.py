"""ERPNext connector using REST API."""
import httpx
from typing import List, Dict, Any
from datetime import datetime, timezone
from .base import APIConnector, RawERPRecord


class ERPNextConnector(APIConnector):
    """Connector for ERPNext (Kenya, Tanzania)."""
    
    def __init__(self, tenant_id: str, credentials: Dict[str, Any], base_url: str):
        super().__init__(tenant_id, credentials, base_url)
        self.api_key = credentials.get("api_key")
        self.api_secret = credentials.get("api_secret")
        self.session = None
    
    async def authenticate(self) -> None:
        """Authenticate with ERPNext API."""
        try:
            self.session = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"token {self.api_key}:{self.api_secret}",
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
            
            # Test connection
            response = await self.session.get("/api/method/frappe.auth.get_logged_user")
            if response.status_code != 200:
                raise ConnectionError("ERPNext authentication failed")
        
        except Exception as e:
            raise ConnectionError(f"Failed to connect to ERPNext: {str(e)}")
    
    async def _get_resource(self, doctype: str, filters: Dict = None, fields: List[str] = None) -> List[Dict]:
        """Get resources from ERPNext."""
        if not self.session:
            await self.authenticate()
        
        params = {"doctype": doctype}
        if filters:
            params["filters"] = str(filters)
        if fields:
            params["fields"] = str(fields)
        
        response = await self.session.get("/api/resource/" + doctype, params=params)
        response.raise_for_status()
        return response.json().get("data", [])
    
    async def extract_energy_data(self, from_date: str, to_date: str) -> List[RawERPRecord]:
        """
        Extract energy invoices from ERPNext.
        
        Doctypes:
        - Purchase Invoice: Supplier invoices
        """
        try:
            invoices = await self._get_resource(
                "Purchase Invoice",
                filters={
                    "docstatus": 1,  # Submitted
                    "posting_date": ["between", [from_date, to_date]]
                },
                fields=["name", "supplier", "posting_date", "grand_total", "currency", "items"]
            )
            
            records = []
            for inv in invoices:
                # Get line items
                items = await self._get_resource(
                    "Purchase Invoice Item",
                    filters={"parent": inv["name"]},
                    fields=["item_code", "item_name", "qty", "uom", "amount"]
                )
                inv["_items"] = items
                
                records.append(RawERPRecord(
                    source_erp="erpnext",
                    source_module="accounts_payable",
                    source_record_id=inv["name"],
                    raw_payload=inv,
                    extracted_at=datetime.now(timezone.utc).isoformat()
                ))
            
            return records
        
        except Exception as e:
            raise RuntimeError(f"Failed to extract energy data from ERPNext: {str(e)}")
    
    async def extract_production_output(self, from_date: str, to_date: str) -> List[RawERPRecord]:
        """
        Extract production data from ERPNext.
        
        Doctypes:
        - Work Order: Manufacturing orders
        """
        try:
            work_orders = await self._get_resource(
                "Work Order",
                filters={
                    "docstatus": 1,
                    "actual_end_date": ["between", [from_date, to_date]]
                },
                fields=["name", "production_item", "qty", "produced_qty", "stock_uom", "actual_end_date"]
            )
            
            return [
                RawERPRecord(
                    source_erp="erpnext",
                    source_module="manufacturing",
                    source_record_id=wo["name"],
                    raw_payload=wo,
                    extracted_at=datetime.now(timezone.utc).isoformat()
                )
                for wo in work_orders
            ]
        
        except Exception as e:
            raise RuntimeError(f"Failed to extract production data from ERPNext: {str(e)}")
    
    async def extract_procurement(self, from_date: str, to_date: str) -> List[RawERPRecord]:
        """Extract purchase orders from ERPNext."""
        try:
            purchase_orders = await self._get_resource(
                "Purchase Order",
                filters={
                    "docstatus": 1,
                    "transaction_date": ["between", [from_date, to_date]]
                },
                fields=["name", "supplier", "transaction_date", "grand_total", "currency"]
            )
            
            records = []
            for po in purchase_orders:
                items = await self._get_resource(
                    "Purchase Order Item",
                    filters={"parent": po["name"]},
                    fields=["item_code", "item_name", "qty", "uom", "amount"]
                )
                po["_items"] = items
                
                records.append(RawERPRecord(
                    source_erp="erpnext",
                    source_module="procurement",
                    source_record_id=po["name"],
                    raw_payload=po,
                    extracted_at=datetime.now(timezone.utc).isoformat()
                ))
            
            return records
        
        except Exception as e:
            raise RuntimeError(f"Failed to extract procurement data from ERPNext: {str(e)}")
    
    async def close(self):
        """Close HTTP session."""
        if self.session:
            await self.session.aclose()
