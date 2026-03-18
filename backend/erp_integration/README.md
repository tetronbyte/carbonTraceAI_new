# ERP Integration System - Complete Documentation

## Overview

This is a production-ready ERP data extraction system designed for CBAM compliance. It extracts energy, production, and procurement data from various ERP systems across African markets.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Application                      │
│  ┌────────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │  API Endpoints │  │  Webhooks    │  │  Job Status    │  │
│  └────────────────┘  └──────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │  Arq Job Queue    │
                    │  (Redis-backed)   │
                    └─────────┬─────────┘
                              │
                    ┌─────────▼──────────┐
                    │   Orchestrator     │
                    │  - Extraction      │
                    │  - Transformation  │
                    │  - Validation      │
                    └─────────┬──────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐   ┌───────▼────────┐   ┌───────▼────────┐
│ Odoo Connector │   │SYSPRO Connector│   │  MongoDB       │
│  (XML-RPC)     │   │  (SQL Server)  │   │  - Raw Data    │
└────────────────┘   └────────────────┘   │  - Normalized  │
                                            │  - Audit Logs  │
                                            └────────────────┘
```

## Directory Structure

```
/app/backend/erp_integration/
├── connectors/           # ERP-specific connectors
│   ├── base.py          # Abstract base classes
│   ├── odoo.py          # Odoo XML-RPC connector
│   ├── syspro.py        # SYSPRO SQL connector
│   └── registry.py      # Connector factory
├── models/              # Data models
│   ├── schemas.py       # MongoDB document schemas
│   └── credentials.py   # Credential encryption
├── services/            # Business logic
│   ├── database.py      # MongoDB operations
│   ├── orchestrator.py  # Extraction orchestration
│   └── transformer.py   # Data transformation
├── schemas/             # Pydantic models
│   ├── api_schemas.py   # API request/response
│   └── validators.py    # Validation logic
├── routers/             # API endpoints
│   ├── erp_router.py    # Main ERP endpoints
│   └── webhooks.py      # Webhook receivers
├── workers/             # Background jobs
│   └── extraction_worker.py  # Arq worker
└── config/              # Configuration
    └── field_mapping.json    # ERP field mappings
```

## Setup

### 1. Environment Variables

Add to `/app/backend/.env`:

```bash
# Generate key with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
CREDENTIAL_ENCRYPTION_KEY=your_fernet_key_here

# Existing MongoDB
MONGO_URL=mongodb://localhost:27017
DB_NAME=carbontraceai

# Redis for Arq (optional, defaults to localhost)
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 2. Start Arq Worker

```bash
cd /app/backend
arq erp_integration.workers.extraction_worker.WorkerSettings
```

### 3. Start Backend

```bash
cd /app/backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

## API Usage

### 1. Connect an ERP System

```bash
POST /api/erp/connections/{tenant_id}
Content-Type: application/json

{
  "erp_type": "odoo",
  "country": "KE",
  "cbam_sector": "cement",
  "base_url": "https://odoo.example.com",
  "credentials": {
    "database": "production",
    "username": "api_user",
    "password": "secure_password",
    "webhook_secret": "optional_webhook_secret"
  }
}
```

### 2. Trigger Data Extraction

```bash
POST /api/erp/extract/{tenant_id}
Content-Type: application/json

{
  "erp_type": "odoo",
  "modules": ["energy", "production", "procurement"],
  "from_date": "2024-01-01",
  "to_date": "2024-12-31",
  "force_full_sync": false
}
```

Response:
```json
{
  "job_id": "uuid",
  "status": "queued",
  "message": "Extraction job queued for 1 ERP system(s)"
}
```

### 3. Check Job Status

```bash
GET /api/erp/extract/status/{job_id}
```

Response:
```json
{
  "job_id": "uuid",
  "status": "processing",
  "progress": 45,
  "result": null,
  "error": null
}
```

### 4. Get Audit Logs

```bash
GET /api/erp/audit-logs/{tenant_id}?limit=100
```

### 5. Get Validation Failures

```bash
GET /api/erp/validation-failures/{tenant_id}?limit=100
```

## Supported ERPs

### Current

- ✅ **Odoo** (Kenya, Tanzania, Morocco) - API/XML-RPC
- ✅ **SYSPRO** (South Africa, Zimbabwe) - SQL Server

### Planned

- 🔄 **SAP Business One** (Egypt, South Africa) - SQL/HANA
- 🔄 **ERPNext** (Kenya, Tanzania) - REST API
- 🔄 **Sage Business Cloud** (Multi-region) - OData
- 🔄 **Microsoft Dynamics 365 BC** (Egypt, Morocco) - OData

## Data Flow

1. **Extraction**
   - Connector pulls data from ERP
   - Raw data stored in `erp_raw_extractions` collection
   - Watermark updated for incremental sync

2. **Transformation**
   - Fields mapped using `field_mapping.json`
   - Units converted to CBAM standards (tonne, kWh, GJ)
   - Emissions calculated using factor library

3. **Validation**
   - Pydantic models validate data
   - Sanity checks on quantities and emissions
   - Failures logged in `validation_failures` collection

4. **Storage**
   - Normalized data stored in `erp_normalized` collection
   - Linked to original raw record via `raw_extraction_id`
   - Ready for CBAM reporting

## MongoDB Collections

### tenant_erp_configs
- Stores ERP connection configurations
- Credentials encrypted with Fernet

### erp_raw_extractions
- Untouched raw data from ERP
- Idempotent upserts on unique key
- Audit trail preserved

### erp_normalized
- Transformed, validated data
- CBAM-ready emissions calculations
- Links back to raw extraction

### sync_watermarks
- Tracks last sync per tenant/ERP/module
- Enables incremental sync

### extraction_audit_logs
- Immutable audit trail
- Tracks job lifecycle (started, completed, failed)

### validation_failures
- Records that failed validation
- Allows manual review and resolution

## Adding a New ERP Connector

1. **Create Connector Class**

```python
# erp_integration/connectors/my_erp.py
from .base import APIConnector, RawERPRecord

class MyERPConnector(APIConnector):
    async def authenticate(self):
        # Implement authentication
        pass
    
    async def extract_energy_data(self, from_date, to_date):
        # Implement extraction
        return [RawERPRecord(...)]
    
    # ... implement other methods
```

2. **Register Connector**

```python
# erp_integration/connectors/registry.py
from .my_erp import MyERPConnector

CONNECTOR_REGISTRY = {
    "odoo": OdooConnector,
    "syspro": SYSPROConnector,
    "my_erp": MyERPConnector,  # Add here
}
```

3. **Add Field Mappings**

```json
// erp_integration/config/field_mapping.json
{
  "my_erp": {
    "accounts_payable": {
      "record_date": "invoice_date_field",
      "amount": "total_field",
      // ... map all fields
    }
  }
}
```

That's it! The rest of the pipeline (orchestration, transformation, validation, storage) works automatically.

## Webhooks

### Odoo

Configure webhook in Odoo:
1. Install `webhook` module
2. Create webhook subscription:
   - URL: `https://your-domain.com/api/webhooks/odoo/{tenant_id}`
   - Events: `account.move/create`, `mrp.production/write`
   - Secret: Use same as in credentials

### Dynamics 365 BC

1. Create webhook subscription via API
2. Point to: `https://your-domain.com/api/webhooks/dynamics/{tenant_id}`

### SYSPRO

SYSPRO doesn't have native webhooks. Options:
1. SQL Server triggers with HTTP call
2. Scheduled polling (default)

## Production Checklist

- [ ] Set `CREDENTIAL_ENCRYPTION_KEY` in production environment
- [ ] Configure Redis for Arq
- [ ] Start Arq worker as daemon
- [ ] Set up monitoring (Prometheus metrics)
- [ ] Configure alerts for consecutive job failures
- [ ] Backup MongoDB regularly
- [ ] Test connection to each ERP before onboarding
- [ ] Document ERP-specific requirements (ports, firewalls, etc.)

## Troubleshooting

### Connection Failures

Check:
1. Credentials are correct
2. Network access (firewall rules)
3. For SQL ERPs: ODBC driver installed
4. For API ERPs: API access enabled

### Validation Failures

Query:
```bash
GET /api/erp/validation-failures/{tenant_id}
```

Common issues:
- Unknown units → Add to `CONVERSIONS` in `transformer.py`
- Low emissions → Adjust sanity check thresholds
- Missing fields → Update field mappings

### Job Stuck

Check:
1. Arq worker is running
2. Redis is accessible
3. Job timeout not exceeded (30 min default)

Restart worker:
```bash
pkill -f "arq erp_integration"
arq erp_integration.workers.extraction_worker.WorkerSettings
```

## Contact

For issues or questions, check:
- `/api/erp/audit-logs/{tenant_id}` - Job history
- `/api/erp/validation-failures/{tenant_id}` - Data issues
- Arq worker logs - Background job errors
