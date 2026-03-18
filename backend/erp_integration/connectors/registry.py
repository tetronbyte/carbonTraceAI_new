"""Connector registry for dynamic ERP connector instantiation."""
from typing import Dict, Type
from .base import ERPBaseConnector
from .odoo import OdooConnector
from .syspro import SYSPROConnector
from .sap_b1 import SAPBusinessOneConnector
from .erpnext import ERPNextConnector
from .sage_bc import SageBusinessCloudConnector
from .dynamics365 import Dynamics365BCConnector


CONNECTOR_REGISTRY: Dict[str, Type[ERPBaseConnector]] = {
    "odoo": OdooConnector,
    "syspro": SYSPROConnector,
    "sap_b1": SAPBusinessOneConnector,
    "erpnext": ERPNextConnector,
    "sage_bc": SageBusinessCloudConnector,
    "dynamics365": Dynamics365BCConnector,
}


def get_connector(
    erp_type: str,
    tenant_id: str,
    credentials: Dict,
    base_url: str = None,
    connection_string: str = None
) -> ERPBaseConnector:
    """
    Factory function to get appropriate ERP connector.
    
    Args:
        erp_type: Type of ERP ('odoo', 'syspro', etc.)
        tenant_id: Tenant identifier
        credentials: Decrypted credentials dict
        base_url: API base URL (for API-based ERPs)
        connection_string: DB connection string (for SQL-based ERPs)
    
    Returns:
        Instantiated connector
    
    Raises:
        ValueError: If ERP type not supported
    """
    if erp_type not in CONNECTOR_REGISTRY:
        raise ValueError(
            f"Unsupported ERP type: {erp_type}. "
            f"Supported types: {list(CONNECTOR_REGISTRY.keys())}"
        )
    
    connector_class = CONNECTOR_REGISTRY[erp_type]
    
    # Determine constructor signature based on base class
    from .base import APIConnector, SQLConnector
    
    if issubclass(connector_class, APIConnector):
        if not base_url:
            raise ValueError(f"{erp_type} requires base_url")
        return connector_class(tenant_id, credentials, base_url)
    
    elif issubclass(connector_class, SQLConnector):
        if not connection_string:
            raise ValueError(f"{erp_type} requires connection_string")
        return connector_class(tenant_id, credentials, connection_string)
    
    else:
        # Generic connector
        return connector_class(tenant_id, credentials)
