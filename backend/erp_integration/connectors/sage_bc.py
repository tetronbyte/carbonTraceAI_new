"""Sage Business Cloud connector using OData."""
import httpx
from typing import List, Dict, Any
from datetime import datetime, timezone
from .base import APIConnector, RawERPRecord


class SageBusinessCloudConnector(APIConnector):
    """Connector for Sage Business Cloud (Multi-region)."""
    
    def __init__(self, tenant_id: str, credentials: Dict[str, Any], base_url: str):
        super().__init__(tenant_id, credentials, base_url)
        self.client_id = credentials.get("client_id")
        self.client_secret = credentials.get("client_secret")
        self.access_token = None
        self.session = None
    
    async def authenticate(self) -> None:
        """Authenticate using OAuth2 client credentials."""
        try:
            # Get access token
            auth_client = httpx.AsyncClient()
            token_response = await auth_client.post(
                "https://oauth.accounting.sage.com/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": "full_access"
                }
            )
            token_response.raise_for_status()
            self.access_token = token_response.json()["access_token"]
            await auth_client.aclose()
            
            # Create session with token
            self.session = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
            
            # Test connection
            response = await self.session.get("/v3.1/companies")
            if response.status_code != 200:
                raise ConnectionError("Sage BC connection test failed")
        
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Sage BC: {str(e)}")
    
    async def _odata_query(self, endpoint: str, filters: str = None) -> List[Dict]:
        """Execute OData query."""
        if not self.session:
            await self.authenticate()
        
        url = endpoint
        if filters:
            url += f"?$filter={filters}"
        
        response = await self.session.get(url)
        response.raise_for_status()
        return response.json().get("value", [])
    
    async def extract_energy_data(self, from_date: str, to_date: str) -> List[RawERPRecord]:
        """Extract purchase invoices from Sage BC."""
        try:
            invoices = await self._odata_query(
                "/v3.1/purchase_invoices",
                filters=f"date ge '{from_date}' and date le '{to_date}' and ledger_account/nominal_code eq '5000'"
            )
            
            return [
                RawERPRecord(
                    source_erp="sage_bc",
                    source_module="accounts_payable",
                    source_record_id=str(inv["id"]),
                    raw_payload=inv,
                    extracted_at=datetime.now(timezone.utc).isoformat()
                )
                for inv in invoices
            ]
        
        except Exception as e:
            raise RuntimeError(f"Failed to extract energy data from Sage BC: {str(e)}")
    
    async def extract_production_output(self, from_date: str, to_date: str) -> List[RawERPRecord]:
        """
        Extract stock movements (production output proxy).
        
        Note: Sage BC Manufacturing addon required for full production data.
        """
        try:
            stock_movements = await self._odata_query(
                "/v3.1/stock_movements",
                filters=f"date ge '{from_date}' and date le '{to_date}' and movement_type eq 'PRODUCTION'"
            )
            
            return [
                RawERPRecord(
                    source_erp="sage_bc",
                    source_module="manufacturing",
                    source_record_id=str(sm["id"]),
                    raw_payload=sm,
                    extracted_at=datetime.now(timezone.utc).isoformat()
                )
                for sm in stock_movements
            ]
        
        except Exception as e:
            raise RuntimeError(f"Failed to extract production data from Sage BC: {str(e)}")
    
    async def extract_procurement(self, from_date: str, to_date: str) -> List[RawERPRecord]:
        """Extract purchase orders from Sage BC."""
        try:
            purchase_orders = await self._odata_query(
                "/v3.1/purchase_orders",
                filters=f"date ge '{from_date}' and date le '{to_date}'"
            )
            
            return [
                RawERPRecord(
                    source_erp="sage_bc",
                    source_module="procurement",
                    source_record_id=str(po["id"]),
                    raw_payload=po,
                    extracted_at=datetime.now(timezone.utc).isoformat()
                )
                for po in purchase_orders
            ]
        
        except Exception as e:
            raise RuntimeError(f"Failed to extract procurement data from Sage BC: {str(e)}")
    
    async def close(self):
        """Close HTTP session."""
        if self.session:
            await self.session.aclose()
