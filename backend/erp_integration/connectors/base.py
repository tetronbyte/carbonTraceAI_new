"""Base connector classes for ERP integrations."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class RawERPRecord:
    """Raw record extracted from ERP system."""
    source_erp: str          # "odoo", "sage_bc", "sap_b1", "syspro", etc.
    source_module: str       # "accounts_payable", "manufacturing", "inventory"
    source_record_id: str    # original ERP primary key
    raw_payload: dict        # untouched payload
    extracted_at: str        # ISO 8601 UTC


class ERPBaseConnector(ABC):
    """Abstract base class for all ERP connectors."""
    
    def __init__(self, tenant_id: str, credentials: Dict[str, Any]):
        self.tenant_id = tenant_id
        self.credentials = credentials
    
    @abstractmethod
    async def authenticate(self) -> None:
        """Authenticate with the ERP system."""
        pass
    
    @abstractmethod
    async def extract_energy_data(self, from_date: str, to_date: str) -> List[RawERPRecord]:
        """Extract energy consumption data (utility bills, meter readings)."""
        pass
    
    @abstractmethod
    async def extract_production_output(self, from_date: str, to_date: str) -> List[RawERPRecord]:
        """Extract production/manufacturing output data."""
        pass
    
    @abstractmethod
    async def extract_procurement(self, from_date: str, to_date: str) -> List[RawERPRecord]:
        """Extract procurement data (raw material purchases)."""
        pass
    
    async def health_check(self) -> bool:
        """Test connection to ERP. Override if ERP has ping endpoint."""
        try:
            await self.authenticate()
            return True
        except Exception:
            return False
    
    async def extract_module(self, module: str, from_date: str, to_date: str) -> List[RawERPRecord]:
        """Generic module extraction router."""
        if module == "energy":
            return await self.extract_energy_data(from_date, to_date)
        elif module == "production":
            return await self.extract_production_output(from_date, to_date)
        elif module == "procurement":
            return await self.extract_procurement(from_date, to_date)
        else:
            raise ValueError(f"Unknown module: {module}")


class APIConnector(ERPBaseConnector, ABC):
    """Base for all REST/GraphQL-based ERPs."""
    
    def __init__(self, tenant_id: str, credentials: Dict[str, Any], base_url: str):
        super().__init__(tenant_id, credentials)
        self.base_url = base_url
        self.session = None  # Will be httpx.AsyncClient


class SQLConnector(ERPBaseConnector, ABC):
    """Base for all direct-DB ERPs (SAP B1, SYSPRO)."""
    
    def __init__(self, tenant_id: str, credentials: Dict[str, Any], connection_string: str):
        super().__init__(tenant_id, credentials)
        self.connection_string = connection_string
        self.connection = None  # Will be DB connection
