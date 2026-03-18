"""
Health check service for ERP connectors.

Provides functionality to test ERP connections and monitor connector health.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import asyncio
from ..connectors.registry import get_connector, CONNECTOR_REGISTRY
from ..models.credentials import CredentialManager
from ..services.database import db_service


class ConnectorHealthCheck:
    """Health check service for ERP connectors."""
    
    def __init__(self):
        self.cred_manager = CredentialManager()
    
    async def check_connector_health(
        self,
        tenant_id: str,
        erp_type: str,
        credentials: Dict[str, Any],
        base_url: str = None,
        connection_string: str = None,
        timeout: int = 10
    ) -> Dict[str, Any]:
        """
        Perform health check on a specific ERP connector.
        
        Args:
            tenant_id: Tenant identifier
            erp_type: Type of ERP system
            credentials: Decrypted credentials
            base_url: API base URL (for API-based ERPs)
            connection_string: DB connection string (for SQL-based ERPs)
            timeout: Timeout in seconds
        
        Returns:
            Health check result with status and details
        """
        start_time = datetime.now(timezone.utc)
        
        try:
            # Get connector instance
            connector = get_connector(
                erp_type=erp_type,
                tenant_id=tenant_id,
                credentials=credentials,
                base_url=base_url,
                connection_string=connection_string
            )
            
            # Test connection with timeout
            test_result = await asyncio.wait_for(
                connector.test_connection(),
                timeout=timeout
            )
            
            end_time = datetime.now(timezone.utc)
            response_time = (end_time - start_time).total_seconds()
            
            return {
                "status": "healthy" if test_result else "unhealthy",
                "erp_type": erp_type,
                "tenant_id": tenant_id,
                "response_time_seconds": response_time,
                "timestamp": end_time.isoformat(),
                "details": {
                    "connection_successful": test_result,
                    "connector_class": connector.__class__.__name__
                }
            }
        
        except asyncio.TimeoutError:
            end_time = datetime.now(timezone.utc)
            return {
                "status": "timeout",
                "erp_type": erp_type,
                "tenant_id": tenant_id,
                "response_time_seconds": timeout,
                "timestamp": end_time.isoformat(),
                "error": f"Connection timeout after {timeout} seconds"
            }
        
        except Exception as e:
            end_time = datetime.now(timezone.utc)
            response_time = (end_time - start_time).total_seconds()
            
            return {
                "status": "error",
                "erp_type": erp_type,
                "tenant_id": tenant_id,
                "response_time_seconds": response_time,
                "timestamp": end_time.isoformat(),
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def check_tenant_connectors(
        self,
        tenant_id: str
    ) -> List[Dict[str, Any]]:
        """
        Check health of all ERP connectors for a tenant.
        
        Args:
            tenant_id: Tenant identifier
        
        Returns:
            List of health check results for each connector
        """
        results = []
        
        # Get all active ERP configs for tenant
        configs = await db_service.get_all_erp_configs(tenant_id)
        
        for config in configs:
            # Decrypt credentials
            credentials = self.cred_manager.decrypt_credentials(
                config.credentials_enc
            )
            
            # Perform health check
            health_result = await self.check_connector_health(
                tenant_id=tenant_id,
                erp_type=config.erp_type,
                credentials=credentials,
                base_url=config.base_url,
                connection_string=config.connection_string
            )
            
            results.append(health_result)
        
        return results
    
    async def get_connector_capabilities(
        self,
        erp_type: str
    ) -> Dict[str, Any]:
        """
        Get capabilities and metadata for a connector type.
        
        Args:
            erp_type: Type of ERP system
        
        Returns:
            Connector capabilities and metadata
        """
        from ..connectors.registry import _import_connector
        
        connector_class = _import_connector(erp_type)
        
        if connector_class is None:
            return {
                "status": "not_found",
                "erp_type": erp_type,
                "error": "Connector not available (may have missing dependencies)"
            }
        
        # Determine connector type
        from ..connectors.base import APIConnector, SQLConnector
        
        connector_type = "generic"
        if issubclass(connector_class, APIConnector):
            connector_type = "api"
        elif issubclass(connector_class, SQLConnector):
            connector_type = "sql"
        
        return {
            "erp_type": erp_type,
            "connector_class": connector_class.__name__,
            "connector_type": connector_type,
            "supported_modules": ["energy", "production", "procurement", "accounts_payable", "manufacturing"],
            "requires_base_url": connector_type == "api",
            "requires_connection_string": connector_type == "sql",
            "supports_webhooks": erp_type in ["odoo", "erpnext"],
            "supports_incremental_sync": True
        }
    
    async def get_all_connector_capabilities(self) -> List[Dict[str, Any]]:
        """Get capabilities for all registered connectors."""
        from ..connectors.registry import get_available_connectors
        
        capabilities = []
        available_connectors = get_available_connectors()
        
        for erp_type in available_connectors.keys():
            cap = await self.get_connector_capabilities(erp_type)
            capabilities.append(cap)
        
        return capabilities


# Global health check service
health_check_service = ConnectorHealthCheck()
