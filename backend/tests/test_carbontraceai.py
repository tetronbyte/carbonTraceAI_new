"""
CarbonTraceAI Backend API Tests
Testing: Invoice Upload (single & batch), ESG Reports, Invoice History
"""
import pytest
import requests
import os
import uuid
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test user credentials
TEST_EMAIL = f"TEST_user_{uuid.uuid4().hex[:8]}@carbontest.com"
TEST_PASSWORD = "TestPass123!"
TEST_FULL_NAME = "Test User Carbon"


@pytest.fixture(scope="module")
def api_session():
    """Create a requests session for all tests"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def test_user(api_session):
    """Register a test user and return the user data"""
    response = api_session.post(f"{BASE_URL}/api/auth/register", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "full_name": TEST_FULL_NAME
    })
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 400 and "already registered" in response.text.lower():
        # User already exists, just return minimal info
        return {"email": TEST_EMAIL}
    else:
        pytest.skip(f"Could not create test user: {response.text}")


@pytest.fixture(scope="module")
def auth_token(api_session, test_user):
    """Login and get authentication token"""
    response = api_session.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Authentication failed: {response.text}")


@pytest.fixture(scope="module")
def authenticated_session(api_session, auth_token):
    """Session with authentication header"""
    api_session.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_session


@pytest.fixture(scope="module")
def organization_id(authenticated_session):
    """Get the organization ID for the test user"""
    response = authenticated_session.get(f"{BASE_URL}/api/auth/organizations")
    if response.status_code == 200 and len(response.json()) > 0:
        return response.json()[0]["id"]
    pytest.skip("Could not get organization ID")


# =============================================================================
# HEALTH CHECK TESTS
# =============================================================================

class TestHealthCheck:
    """Basic health check tests"""
    
    def test_api_health(self, api_session):
        """Test API health endpoint"""
        response = api_session.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "CarbonTraceAI"
        print("✓ API health check passed")
    
    def test_api_root(self, api_session):
        """Test API root endpoint"""
        response = api_session.get(f"{BASE_URL}/api")
        assert response.status_code == 200
        data = response.json()
        assert "CarbonTraceAI" in data["message"]
        assert "version" in data
        print("✓ API root endpoint passed")


# =============================================================================
# AUTHENTICATION TESTS
# =============================================================================

class TestAuthentication:
    """Authentication flow tests"""
    
    def test_register_user(self, api_session):
        """Test user registration"""
        unique_email = f"TEST_reg_{uuid.uuid4().hex[:8]}@carbontest.com"
        response = api_session.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": "TestPass123!",
            "full_name": "Registration Test"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == unique_email
        assert "id" in data
        print(f"✓ User registration passed: {unique_email}")
    
    def test_login_user(self, api_session, test_user):
        """Test user login"""
        response = api_session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        print("✓ User login passed")
    
    def test_login_invalid_credentials(self, api_session):
        """Test login with invalid credentials"""
        response = api_session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("✓ Invalid credentials correctly rejected")
    
    def test_get_current_user(self, authenticated_session):
        """Test getting current user info"""
        response = authenticated_session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == TEST_EMAIL
        assert "id" in data
        print("✓ Get current user passed")
    
    def test_get_organizations(self, authenticated_session):
        """Test getting user organizations"""
        response = authenticated_session.get(f"{BASE_URL}/api/auth/organizations")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "id" in data[0]
        assert "name" in data[0]
        print(f"✓ Get organizations passed: {len(data)} org(s)")


# =============================================================================
# SINGLE INVOICE UPLOAD TESTS
# =============================================================================

class TestSingleInvoiceUpload:
    """Single invoice upload endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def create_test_invoice_file(self, tmp_path):
        """Create a test invoice file for upload"""
        self.test_file = tmp_path / "test_invoice.txt"
        self.test_file.write_text("""
Kenya Power Invoice
Invoice Number: KP-2025-12345
Date: 2025-12-15
Customer: Test SME Ltd
Account Number: 123456789
Billing Period: Dec 1-31, 2025

Electricity Consumption:
- Peak Usage: 450 kWh @ KES 18.50 = KES 8,325
- Off-Peak Usage: 300 kWh @ KES 12.00 = KES 3,600

Subtotal: KES 11,925
VAT (16%): KES 1,908
Total: KES 13,833

Payment Due: 2025-01-15
Meter Number: MTR-2345678
Location: Nairobi, Kenya
""")
        return self.test_file
    
    def test_single_upload_success(self, authenticated_session, organization_id, create_test_invoice_file):
        """Test successful single invoice upload"""
        with open(create_test_invoice_file, "rb") as f:
            files = {"file": ("test_invoice.txt", f, "text/plain")}
            data = {
                "organization_id": organization_id,
                "country": "kenya"
            }
            # Remove JSON header for multipart
            headers = {"Authorization": authenticated_session.headers.get("Authorization")}
            response = requests.post(
                f"{BASE_URL}/api/invoices/upload",
                files=files,
                data=data,
                headers=headers
            )
        
        print(f"Single upload response status: {response.status_code}")
        assert response.status_code == 200
        result = response.json()
        
        # Validate response structure
        assert "invoice" in result
        assert "emission_records" in result
        assert "extracted_data" in result
        
        # Validate invoice data
        invoice = result["invoice"]
        assert invoice["organization_id"] == organization_id
        assert invoice["file_name"] == "test_invoice.txt"
        assert invoice["status"] in ["completed", "partial"]
        
        print(f"✓ Single invoice upload passed: {invoice['id']}")
        return result
    
    def test_single_upload_invalid_file_type(self, authenticated_session, organization_id, tmp_path):
        """Test upload with invalid file type"""
        test_file = tmp_path / "invalid.exe"
        test_file.write_text("invalid content")
        
        with open(test_file, "rb") as f:
            files = {"file": ("invalid.exe", f, "application/octet-stream")}
            data = {"organization_id": organization_id}
            headers = {"Authorization": authenticated_session.headers.get("Authorization")}
            response = requests.post(
                f"{BASE_URL}/api/invoices/upload",
                files=files,
                data=data,
                headers=headers
            )
        
        assert response.status_code == 400
        assert "not allowed" in response.text.lower()
        print("✓ Invalid file type correctly rejected")
    
    def test_single_upload_missing_org_id(self, authenticated_session, tmp_path):
        """Test upload without organization_id"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        with open(test_file, "rb") as f:
            files = {"file": ("test.txt", f, "text/plain")}
            headers = {"Authorization": authenticated_session.headers.get("Authorization")}
            response = requests.post(
                f"{BASE_URL}/api/invoices/upload",
                files=files,
                data={},  # Missing organization_id
                headers=headers
            )
        
        assert response.status_code == 422  # Validation error
        print("✓ Missing organization_id correctly rejected")


# =============================================================================
# BATCH INVOICE UPLOAD TESTS
# =============================================================================

class TestBatchInvoiceUpload:
    """Batch invoice upload endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def create_batch_files(self, tmp_path):
        """Create multiple test files for batch upload"""
        self.batch_files = []
        
        # Electricity invoice
        electricity_file = tmp_path / "electricity_invoice.txt"
        electricity_file.write_text("""
Electricity Bill - Kenya Power
Invoice: ELEC-2025-001
Date: 2025-11-30
Customer: Carbon Test SME
Consumption: 500 kWh
Unit Price: 15.00 KES/kWh
Total: 7,500 KES
Location: Nairobi, Kenya
""")
        self.batch_files.append(electricity_file)
        
        # Fuel receipt
        fuel_file = tmp_path / "fuel_receipt.txt"
        fuel_file.write_text("""
Fuel Receipt - Shell Kenya
Receipt: FUEL-2025-002
Date: 2025-11-25
Diesel: 200 liters
Price per liter: 150.00 KES
Total: 30,000 KES
Vehicle: Company Truck
""")
        self.batch_files.append(fuel_file)
        
        # Gas bill
        gas_file = tmp_path / "gas_bill.txt"
        gas_file.write_text("""
Gas Bill - Kenya Gas
Invoice: GAS-2025-003
Date: 2025-11-20
Consumption: 50 m3
Unit Price: 80.00 KES/m3
Total: 4,000 KES
Type: Natural Gas
Location: Mombasa, Kenya
""")
        self.batch_files.append(gas_file)
        
        return self.batch_files
    
    def test_batch_upload_success(self, authenticated_session, organization_id, create_batch_files):
        """Test successful batch invoice upload"""
        files = []
        for file_path in create_batch_files:
            with open(file_path, "rb") as f:
                files.append(("files", (file_path.name, f.read(), "text/plain")))
        
        data = {
            "organization_id": organization_id,
            "country": "kenya",
            "quarter": "Q4",
            "year": "2025"
        }
        headers = {"Authorization": authenticated_session.headers.get("Authorization")}
        
        response = requests.post(
            f"{BASE_URL}/api/invoices/batch-upload",
            files=files,
            data=data,
            headers=headers
        )
        
        print(f"Batch upload response status: {response.status_code}")
        if response.status_code != 200:
            print(f"Batch upload error: {response.text}")
        
        assert response.status_code == 200
        result = response.json()
        
        # Validate response structure
        assert "batch_id" in result
        assert "total_files" in result
        assert "successful" in result
        assert "failed" in result
        assert "total_emissions" in result
        assert "scope1_emissions" in result
        assert "scope2_emissions" in result
        assert "scope3_emissions" in result
        assert "invoices" in result
        assert "emission_records" in result
        
        # Validate counts
        assert result["total_files"] == 3
        assert result["successful"] + result["failed"] == result["total_files"]
        
        print(f"✓ Batch upload passed: {result['successful']}/{result['total_files']} successful")
        print(f"  Batch ID: {result['batch_id']}")
        print(f"  Total emissions: {result['total_emissions']} kg CO2e")
        print(f"  Scope 1: {result['scope1_emissions']}, Scope 2: {result['scope2_emissions']}, Scope 3: {result['scope3_emissions']}")
        
        return result
    
    def test_batch_upload_with_none_quarter(self, authenticated_session, organization_id, create_batch_files):
        """Test batch upload with quarter set to 'none' (as per UI fix)"""
        files = []
        # Use only one file for faster test
        with open(create_batch_files[0], "rb") as f:
            files.append(("files", (create_batch_files[0].name, f.read(), "text/plain")))
        
        data = {
            "organization_id": organization_id,
            "country": "default"
            # quarter not included (simulates 'none' option from UI)
        }
        headers = {"Authorization": authenticated_session.headers.get("Authorization")}
        
        response = requests.post(
            f"{BASE_URL}/api/invoices/batch-upload",
            files=files,
            data=data,
            headers=headers
        )
        
        assert response.status_code == 200
        print("✓ Batch upload without quarter passed")
    
    def test_batch_upload_too_many_files(self, authenticated_session, organization_id, tmp_path):
        """Test batch upload with more than 20 files (should fail)"""
        files = []
        for i in range(25):
            test_file = tmp_path / f"test_{i}.txt"
            test_file.write_text(f"Test invoice {i}")
            with open(test_file, "rb") as f:
                files.append(("files", (f"test_{i}.txt", f.read(), "text/plain")))
        
        data = {"organization_id": organization_id}
        headers = {"Authorization": authenticated_session.headers.get("Authorization")}
        
        response = requests.post(
            f"{BASE_URL}/api/invoices/batch-upload",
            files=files,
            data=data,
            headers=headers
        )
        
        assert response.status_code == 400
        assert "Maximum" in response.text or "20" in response.text
        print("✓ Exceeded file limit correctly rejected")


# =============================================================================
# INVOICE HISTORY TESTS
# =============================================================================

class TestInvoiceHistory:
    """Invoice history and retrieval tests"""
    
    def test_get_invoices(self, authenticated_session, organization_id):
        """Test getting invoice list"""
        response = authenticated_session.get(
            f"{BASE_URL}/api/invoices?organization_id={organization_id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            invoice = data[0]
            assert "id" in invoice
            assert "file_name" in invoice
            assert "status" in invoice
            assert "uploaded_at" in invoice
        
        print(f"✓ Get invoices passed: {len(data)} invoice(s)")
    
    def test_get_invoice_by_id(self, authenticated_session, organization_id):
        """Test getting a specific invoice"""
        # First get list of invoices
        list_response = authenticated_session.get(
            f"{BASE_URL}/api/invoices?organization_id={organization_id}"
        )
        
        if list_response.status_code == 200 and len(list_response.json()) > 0:
            invoice_id = list_response.json()[0]["id"]
            
            response = authenticated_session.get(f"{BASE_URL}/api/invoices/{invoice_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == invoice_id
            print(f"✓ Get invoice by ID passed: {invoice_id}")
        else:
            pytest.skip("No invoices available for testing")
    
    def test_get_invoice_not_found(self, authenticated_session):
        """Test getting non-existent invoice"""
        response = authenticated_session.get(
            f"{BASE_URL}/api/invoices/non-existent-id-12345"
        )
        assert response.status_code == 404
        print("✓ Non-existent invoice correctly returns 404")


# =============================================================================
# ESG REPORT GENERATION TESTS
# =============================================================================

class TestESGReportGeneration:
    """ESG Report generation tests"""
    
    def test_get_frameworks(self, authenticated_session):
        """Test getting available ESG frameworks"""
        response = authenticated_session.get(f"{BASE_URL}/api/reports/frameworks")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate all frameworks are present
        assert "ISSB" in data
        assert "TCFD" in data
        assert "GRI" in data
        assert "CBAM" in data
        
        # Validate framework structure
        for framework_key in ["ISSB", "TCFD", "GRI", "CBAM"]:
            framework = data[framework_key]
            assert "name" in framework
            assert "description" in framework
            assert "sections" in framework
        
        print("✓ Get frameworks passed: ISSB, TCFD, GRI, CBAM available")
    
    def test_generate_issb_report(self, authenticated_session, organization_id):
        """Test ISSB report generation"""
        response = authenticated_session.post(
            f"{BASE_URL}/api/reports/generate",
            json={
                "organization_id": organization_id,
                "org_name": "Test Carbon SME",
                "report_period": "2025",
                "report_type": "Annual",
                "compliance_standard": "ISSB"
            }
        )
        
        print(f"ISSB report response status: {response.status_code}")
        
        # Report generation may take time with AI, but should complete
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert data["compliance_standard"] == "ISSB"
        assert data["status"] in ["completed", "generating"]
        assert "total_emissions" in data
        
        print(f"✓ ISSB report generation passed: {data['id']}")
        return data
    
    def test_generate_tcfd_report(self, authenticated_session, organization_id):
        """Test TCFD report generation"""
        response = authenticated_session.post(
            f"{BASE_URL}/api/reports/generate",
            json={
                "organization_id": organization_id,
                "org_name": "Test Carbon SME",
                "report_period": "2025",
                "report_type": "Annual",
                "compliance_standard": "TCFD"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["compliance_standard"] == "TCFD"
        print(f"✓ TCFD report generation passed: {data['id']}")
    
    def test_generate_gri_report(self, authenticated_session, organization_id):
        """Test GRI report generation"""
        response = authenticated_session.post(
            f"{BASE_URL}/api/reports/generate",
            json={
                "organization_id": organization_id,
                "org_name": "Test Carbon SME",
                "report_period": "2025",
                "report_type": "Annual",
                "compliance_standard": "GRI"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["compliance_standard"] == "GRI"
        print(f"✓ GRI report generation passed: {data['id']}")
    
    def test_generate_cbam_report(self, authenticated_session, organization_id):
        """Test CBAM report generation"""
        response = authenticated_session.post(
            f"{BASE_URL}/api/reports/generate",
            json={
                "organization_id": organization_id,
                "org_name": "Test Carbon SME",
                "report_period": "2025",
                "report_type": "Quarterly",
                "quarter": "Q4",
                "compliance_standard": "CBAM"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["compliance_standard"] == "CBAM"
        print(f"✓ CBAM report generation passed: {data['id']}")
    
    def test_get_reports(self, authenticated_session, organization_id):
        """Test getting list of reports"""
        response = authenticated_session.get(
            f"{BASE_URL}/api/reports?organization_id={organization_id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            report = data[0]
            assert "id" in report
            assert "compliance_standard" in report
            assert "status" in report
        
        print(f"✓ Get reports passed: {len(data)} report(s)")
    
    def test_generate_cbam_product_report(self, authenticated_session, organization_id):
        """Test CBAM product-level report generation"""
        response = authenticated_session.post(
            f"{BASE_URL}/api/reports/cbam",
            json={
                "organization_id": organization_id,
                "org_name": "Test Carbon SME",
                "report_period": "2025",
                "products": [
                    {
                        "name": "Steel Rods",
                        "batch_id": "BATCH-001",
                        "quantity": 1000,
                        "unit": "kg",
                        "emissions": 2500.0
                    },
                    {
                        "name": "Aluminum Sheets",
                        "batch_id": "BATCH-002",
                        "quantity": 500,
                        "unit": "kg",
                        "emissions": 1200.0
                    }
                ]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["compliance_standard"] == "CBAM"
        assert data["total_emissions"] == 3700.0
        print(f"✓ CBAM product report generation passed: {data['id']}")


# =============================================================================
# EMISSION RECORDS TESTS
# =============================================================================

class TestEmissionRecords:
    """Emission records tests"""
    
    def test_get_emission_records(self, authenticated_session, organization_id):
        """Test getting emission records for organization"""
        response = authenticated_session.get(
            f"{BASE_URL}/api/ledger/emissions/{organization_id}?verified_only=false"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            record = data[0]
            assert "id" in record
            assert "energy_type" in record or "co2_emissions_kg" in record
        
        print(f"✓ Get emission records passed: {len(data)} record(s)")


# =============================================================================
# CLEANUP
# =============================================================================

@pytest.fixture(scope="module", autouse=True)
def cleanup(request, authenticated_session, organization_id):
    """Cleanup test data after all tests"""
    yield
    # Cleanup invoices created during testing
    try:
        response = authenticated_session.get(
            f"{BASE_URL}/api/invoices?organization_id={organization_id}"
        )
        if response.status_code == 200:
            invoices = response.json()
            for inv in invoices:
                if inv.get("file_name", "").startswith("test") or inv.get("file_name", "").startswith("electricity") or inv.get("file_name", "").startswith("fuel") or inv.get("file_name", "").startswith("gas"):
                    authenticated_session.delete(f"{BASE_URL}/api/invoices/{inv['id']}")
        print("✓ Cleanup completed")
    except Exception as e:
        print(f"Cleanup warning: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
