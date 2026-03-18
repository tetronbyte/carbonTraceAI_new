"""Integration test for ERP system backend."""
import asyncio
import sys
from datetime import datetime, timezone

# Test imports
print("Testing imports...")
try:
    from erp_integration.models.credentials import CredentialManager
    from erp_integration.models.schemas import TenantERPConfigDoc
    from erp_integration.services.database import db_service
    from erp_integration.connectors.registry import get_connector
    print("✅ All imports successful")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)


async def test_credential_encryption():
    """Test credential encryption/decryption."""
    print("\n🔐 Testing Credential Encryption...")
    try:
        cred_manager = CredentialManager()
        test_creds = {"username": "test", "password": "secret123"}
        
        # Encrypt
        encrypted = cred_manager.encrypt_credentials(test_creds)
        print(f"  ✅ Encrypted: {encrypted[:50]}...")
        
        # Decrypt
        decrypted = cred_manager.decrypt_credentials(encrypted)
        assert decrypted == test_creds, "Decryption mismatch!"
        print(f"  ✅ Decrypted successfully: {decrypted}")
        
        return True
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False


async def test_database_connection():
    """Test MongoDB connection."""
    print("\n💾 Testing Database Connection...")
    try:
        await db_service._ensure_db()
        print("  ✅ Database connection established")
        return True
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False


async def test_connector_registry():
    """Test connector registry."""
    print("\n🔌 Testing Connector Registry...")
    try:
        from erp_integration.connectors.registry import CONNECTOR_REGISTRY
        connectors = ["odoo", "syspro", "sap_b1", "erpnext", "sage_bc", "dynamics365"]
        for erp_type in connectors:
            connector_class = CONNECTOR_REGISTRY.get(erp_type)
            if connector_class:
                print(f"  ✅ {erp_type}: {connector_class.__name__}")
            else:
                print(f"  ❌ {erp_type}: Not found in registry")
                return False
        return True
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False


async def test_tenant_config_crud():
    """Test tenant configuration CRUD operations."""
    print("\n📋 Testing Tenant Config CRUD...")
    try:
        # Create test config
        test_config = TenantERPConfigDoc(
            tenant_id="test-tenant-999",
            erp_type="odoo",
            country="Test Country",
            cbam_sector="Test Sector",
            credentials_enc="encrypted_test_creds",
            base_url="https://test.odoo.com",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Save
        config_id = await db_service.create_erp_config(test_config)
        print(f"  ✅ Created config: {config_id}")
        
        # Read
        retrieved = await db_service.get_erp_config("test-tenant-999", "odoo")
        assert retrieved is not None, "Failed to retrieve config"
        print(f"  ✅ Retrieved config: {retrieved.tenant_id}")
        
        # Update
        await db_service.update_last_synced("test-tenant-999", "odoo")
        print(f"  ✅ Updated last_synced_at")
        
        # Deactivate (soft delete)
        await db_service.deactivate_erp_config("test-tenant-999", "odoo")
        print(f"  ✅ Deactivated config")
        
        # Verify deactivation
        active_config = await db_service.get_erp_config("test-tenant-999", "odoo")
        assert active_config is None, "Config should be inactive"
        print(f"  ✅ Verified deactivation")
        
        return True
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_redis_connection():
    """Test Redis connection for Arq."""
    print("\n🔴 Testing Redis Connection...")
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        ping_result = r.ping()
        print(f"  ✅ Redis PING: {ping_result}")
        
        # Test set/get
        r.set('test_key', 'test_value')
        value = r.get('test_key')
        print(f"  ✅ Redis SET/GET: {value.decode()}")
        r.delete('test_key')
        
        return True
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("🧪 ERP Integration Backend Test Suite")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Credential Encryption", await test_credential_encryption()))
    results.append(("Database Connection", await test_database_connection()))
    results.append(("Connector Registry", await test_connector_registry()))
    results.append(("Tenant Config CRUD", await test_tenant_config_crud()))
    results.append(("Redis Connection", await test_redis_connection()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("=" * 60)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️ Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
