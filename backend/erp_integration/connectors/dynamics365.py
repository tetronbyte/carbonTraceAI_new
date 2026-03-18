"""Microsoft Dynamics 365 BC connector using OData."""
import httpx
from typing import List, Dict, Any
from datetime import datetime, timezone
from .base import APIConnector, RawERPRecord


class Dynamics365BCConnector(APIConnector):
    """Connector for Microsoft Dynamics 365 Business Central (Egypt, Morocco)."""
    
    def __init__(self, tenant_id: str, credentials: Dict[str, Any], base_url: str):
        super().__init__(tenant_id, credentials, base_url)
        self.client_id = credentials.get("client_id")
        self.client_secret = credentials.get("client_secret")
        self.azure_tenant_id = credentials.get("azure_tenant_id")
        self.access_token = None
        self.session = None
        self.company_id = None
    
    async def authenticate(self) -> None:
        """Authenticate using Azure AD OAuth2."""
        try:
            # Get access token from Azure AD
            auth_client = httpx.AsyncClient()
            token_response = await auth_client.post(
                f"https://login.microsoftonline.com/{self.azure_tenant_id}/oauth2/v2.0/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": "https://api.businesscentral.dynamics.com/.default"
                }
            )
            token_response.raise_for_status()
            self.access_token = token_response.json()["access_token"]
            await auth_client.aclose()
            
            # Create session
            self.session = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
            
            # Get company ID
            response = await self.session.get("/api/v2.0/companies")
            response.raise_for_status()
            companies = response.json().get("value", [])
            if companies:
                self.company_id = companies[0]["id"]
            else:
                raise ConnectionError("No companies found in Dynamics 365 BC")
        
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Dynamics 365 BC: {str(e)}")
    
    async def _odata_query(self, endpoint: str, filters: str = None) -> List[Dict]:
        """Execute OData query."""
        if not self.session or not self.company_id:
            await self.authenticate()
        
        url = f"/api/v2.0/companies({self.company_id})/{endpoint}"
        if filters:
            url += f"?$filter={filters}"
        
        response = await self.session.get(url)
        response.raise_for_status()
        return response.json().get("value", [])
    
    async def extract_energy_data(self, from_date: str, to_date: str) -> List[RawERPRecord]:
        """Extract purchase invoices from Dynamics 365 BC."""
        try:
            invoices = await self._odata_query(
                "purchaseInvoices",
                filters=f"postingDate ge {from_date} and postingDate le {to_date}"
            )
            
            records = []
            for inv in invoices:
                # Get line items
                lines = await self._odata_query(
                    f"purchaseInvoices({inv['id']})/purchaseInvoiceLines"
                )
                inv["_lines"] = lines
                
                records.append(RawERPRecord(
                    source_erp="dynamics365",
                    source_module="accounts_payable",
                    source_record_id=str(inv["id"]),
                    raw_payload=inv,
                    extracted_at=datetime.now(timezone.utc).isoformat()
                ))
            
            return records
        
        except Exception as e:
            raise RuntimeError(f"Failed to extract energy data from Dynamics 365 BC: {str(e)}")
    
    async def extract_production_output(self, from_date: str, to_date: str) -> List[RawERPRecord]:
        """Extract production orders from Dynamics 365 BC."""
        try:
            production_orders = await self._odata_query(
                "productionOrders",
                filters=f"endingDate ge {from_date} and endingDate le {to_date} and status eq 'Finished'"
            )
            
            return [
                RawERPRecord(
                    source_erp="dynamics365",
                    source_module="manufacturing",
                    source_record_id=str(po["id"]),
                    raw_payload=po,
                    extracted_at=datetime.now(timezone.utc).isoformat()
                )
                for po in production_orders
            ]
        
        except Exception as e:
            raise RuntimeError(f"Failed to extract production data from Dynamics 365 BC: {str(e)}")
    
    async def extract_procurement(self, from_date: str, to_date: str) -> List[RawERPRecord]:
        """Extract purchase orders from Dynamics 365 BC."""
        try:
            purchase_orders = await self._odata_query(
                "purchaseOrders",
                filters=f"orderDate ge {from_date} and orderDate le {to_date}"
            )
            
            records = []
            for po in purchase_orders:
                lines = await self._odata_query(
                    f"purchaseOrders({po['id']})/purchaseOrderLines"
                )
                po["_lines"] = lines
                
                records.append(RawERPRecord(
                    source_erp="dynamics365",
                    source_module="procurement",
                    source_record_id=str(po["id"]),
                    raw_payload=po,
                    extracted_at=datetime.now(timezone.utc).isoformat()
                ))
            
            return records
        
        except Exception as e:
            raise RuntimeError(f"Failed to extract procurement data from Dynamics 365 BC: {str(e)}")
    
    async def close(self):
        """Close HTTP session."""
        if self.session:
            await self.session.aclose()
