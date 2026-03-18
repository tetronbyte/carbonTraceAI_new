"""Odoo ERP connector using XML-RPC."""
import xmlrpc.client
from typing import List, Dict, Any
from datetime import datetime, timezone
from .base import APIConnector, RawERPRecord


class OdooConnector(APIConnector):
    """Connector for Odoo ERP (Kenya, Tanzania, Morocco)."""
    
    def __init__(self, tenant_id: str, credentials: Dict[str, Any], base_url: str):
        super().__init__(tenant_id, credentials, base_url)
        self.uid = None
        self.models = None
        self.database = credentials.get("database")
        self.username = credentials.get("username")
        self.password = credentials.get("password")
    
    async def authenticate(self) -> None:
        """Authenticate with Odoo XML-RPC."""
        try:
            common = xmlrpc.client.ServerProxy(f"{self.base_url}/xmlrpc/2/common")
            self.uid = common.authenticate(self.database, self.username, self.password, {})
            
            if not self.uid:
                raise ConnectionError("Odoo authentication failed")
            
            self.models = xmlrpc.client.ServerProxy(f"{self.base_url}/xmlrpc/2/object")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Odoo: {str(e)}")
    
    def _search_read(self, model: str, domain: List, fields: List[str], limit: int = 500) -> List[Dict]:
        """Execute search_read on Odoo model."""
        return self.models.execute_kw(
            self.database, self.uid, self.password,
            model, "search_read",
            [domain],
            {"fields": fields, "limit": limit}
        )
    
    async def extract_energy_data(self, from_date: str, to_date: str) -> List[RawERPRecord]:
        """
        Extract energy invoices from Odoo account.move.
        
        Filters for:
        - Type: in_invoice (supplier invoice)
        - Product category: energy-related
        - Date range
        """
        if not self.uid:
            await self.authenticate()
        
        try:
            # Search for energy-related invoices
            invoices = self._search_read(
                "account.move",
                [
                    ["move_type", "=", "in_invoice"],
                    ["invoice_date", ">=", from_date],
                    ["invoice_date", "<=", to_date],
                    ["state", "=", "posted"],  # Only posted invoices
                ],
                [
                    "name", "invoice_date", "partner_id", "amount_total", 
                    "currency_id", "invoice_line_ids"
                ]
            )
            
            records = []
            for inv in invoices:
                # Get invoice lines
                if inv.get("invoice_line_ids"):
                    line_ids = inv["invoice_line_ids"]
                    lines = self._search_read(
                        "account.move.line",
                        [["id", "in", line_ids]],
                        ["product_id", "quantity", "product_uom_id", "price_subtotal"]
                    )
                    inv["_invoice_lines"] = lines
                
                records.append(RawERPRecord(
                    source_erp="odoo",
                    source_module="accounts_payable",
                    source_record_id=str(inv["id"]),
                    raw_payload=inv,
                    extracted_at=datetime.now(timezone.utc).isoformat()
                ))
            
            return records
        
        except Exception as e:
            raise RuntimeError(f"Failed to extract energy data from Odoo: {str(e)}")
    
    async def extract_production_output(self, from_date: str, to_date: str) -> List[RawERPRecord]:
        """
        Extract manufacturing orders from Odoo mrp.production.
        
        Filters for completed production orders in date range.
        """
        if not self.uid:
            await self.authenticate()
        
        try:
            orders = self._search_read(
                "mrp.production",
                [
                    ["state", "=", "done"],
                    ["date_finished", ">=", from_date],
                    ["date_finished", "<=", to_date]
                ],
                [
                    "name", "product_id", "product_qty", "product_uom_id",
                    "date_finished", "origin", "company_id"
                ]
            )
            
            return [
                RawERPRecord(
                    source_erp="odoo",
                    source_module="manufacturing",
                    source_record_id=str(order["id"]),
                    raw_payload=order,
                    extracted_at=datetime.now(timezone.utc).isoformat()
                )
                for order in orders
            ]
        
        except Exception as e:
            raise RuntimeError(f"Failed to extract production data from Odoo: {str(e)}")
    
    async def extract_procurement(self, from_date: str, to_date: str) -> List[RawERPRecord]:
        """
        Extract purchase orders from Odoo purchase.order.
        
        For CBAM Scope 3 upstream emissions.
        """
        if not self.uid:
            await self.authenticate()
        
        try:
            purchase_orders = self._search_read(
                "purchase.order",
                [
                    ["state", "in", ["purchase", "done"]],
                    ["date_approve", ">=", from_date],
                    ["date_approve", "<=", to_date]
                ],
                [
                    "name", "partner_id", "date_approve", "amount_total",
                    "currency_id", "order_line"
                ]
            )
            
            records = []
            for po in purchase_orders:
                if po.get("order_line"):
                    line_ids = po["order_line"]
                    lines = self._search_read(
                        "purchase.order.line",
                        [["id", "in", line_ids]],
                        ["product_id", "product_qty", "product_uom", "price_subtotal"]
                    )
                    po["_purchase_lines"] = lines
                
                records.append(RawERPRecord(
                    source_erp="odoo",
                    source_module="procurement",
                    source_record_id=str(po["id"]),
                    raw_payload=po,
                    extracted_at=datetime.now(timezone.utc).isoformat()
                ))
            
            return records
        
        except Exception as e:
            raise RuntimeError(f"Failed to extract procurement data from Odoo: {str(e)}")
