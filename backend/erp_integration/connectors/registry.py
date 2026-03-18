"""Connector registry for dynamic ERP connector instantiation."""
from typing import Dict, Type, Optional
import logging

logger = logging.getLogger(__name__)

# Base connector class is always available
from .base import ERPBaseConnector, APIConnector, SQLConnector

# Lazy loading registry - connectors are imported only when needed
CONNECTOR_MODULES = {
    "odoo": ".odoo.OdooConnector",
    "syspro": ".syspro.SYSPROConnector",
    "sap_b1": ".sap_b1.SAPBusinessOneConnector",
    "erpnext": ".erpnext.ERPNextConnector",
    "sage_bc": ".sage_bc.SageBusinessCloudConnector",
    "dynamics365": ".dynamics365.Dynamics365BCConnector",
}

# Cache for successfully imported connectors
_connector_cache: Dict[str, Type[ERPBaseConnector]] = {}
# Track failed imports to avoid retrying
_failed_imports: set = set()


def _import_connector(erp_type: str) -> Optional[Type[ERPBaseConnector]]:
    """
    Lazily import connector class.
    
    Returns None if import fails (e.g., missing dependencies).
    """
    # Return cached if available
    if erp_type in _connector_cache:
        return _connector_cache[erp_type]
    
    # Skip if previously failed
    if erp_type in _failed_imports:
        return None
    
    # Get module path
    module_path = CONNECTOR_MODULES.get(erp_type)
    if not module_path:
        return None
    
    try:
        # Dynamic import
        module_name, class_name = module_path.rsplit(".", 1)
        from importlib import import_module
        module = import_module(module_name, package=__package__)
        connector_class = getattr(module, class_name)
        
        # Cache successful import
        _connector_cache[erp_type] = connector_class
        logger.info(f"Successfully imported connector: {erp_type}")
        
        return connector_class
        
    except ImportError as e:
        logger.warning(f"Failed to import connector {erp_type}: {e}")
        _failed_imports.add(erp_type)
        return None
    except Exception as e:
        logger.error(f"Unexpected error importing connector {erp_type}: {e}")
        _failed_imports.add(erp_type)
        return None


def get_available_connectors() -> Dict[str, Type[ERPBaseConnector]]:
    """
    Get all successfully importable connectors.
    
    Returns dictionary of erp_type -> connector_class.
    """
    available = {}
    for erp_type in CONNECTOR_MODULES.keys():
        connector = _import_connector(erp_type)
        if connector:
            available[erp_type] = connector
    return available


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
        ValueError: If ERP type not supported or failed to import
    """
    # Try to import connector
    connector_class = _import_connector(erp_type)
    
    if connector_class is None:
        available = list(get_available_connectors().keys())
        raise ValueError(
            f"ERP type '{erp_type}' is not available. "
            f"This may be due to missing dependencies. "
            f"Available connectors: {available}"
        )
    
    # Determine constructor signature based on base class
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


# For backward compatibility - expose registry
def get_connector_registry() -> Dict[str, Type[ERPBaseConnector]]:
    """Get registry of available connectors (lazy loaded)."""
    return get_available_connectors()


# Alias for backward compatibility
CONNECTOR_REGISTRY = get_connector_registry
