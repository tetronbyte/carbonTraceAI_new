# CarbonTraceAI PRD (Product Requirements Document)

## Overview
CarbonTraceAI is an AI-powered carbon accounting and verification platform for African SMEs, helping companies convert energy invoices into carbon emission data, verify them on blockchain, and generate ESG compliance reports.

## Original Problem Statement
Build a production-quality SaaS web platform that:
- Converts paper/digital invoices into carbon emissions data
- Verifies emissions on Polygon blockchain
- Generates ESG compliance reports (ISSB, TCFD, GRI, CBAM)
- Supports African exporters complying with EU CBAM regulations

## User Personas
1. **African SME Owner/Manager** - Needs to track carbon footprint for EU exports
2. **Sustainability Officer** - Manages ESG reporting and compliance
3. **Financial Controller** - Processes invoices and needs carbon data
4. **EU Importer** - Verifies supplier carbon claims via blockchain QR codes

## Core Requirements (Static)
- JWT-based authentication
- Organization management
- MongoDB database
- Dark theme with green accents (#00E676)
- Mobile responsive design

## Tech Stack
- **Frontend**: React + TypeScript-compatible, Vanilla CSS with Tailwind, Recharts
- **Backend**: Python FastAPI, MongoDB
- **AI**: Ollama Cloud Models (kimi-k2.5:cloud for VLM, deepseek-v3.2:cloud for LLM)
- **Blockchain**: Mock Polygon (demo mode)

---

## What's Been Implemented (v2.0 - March 2026)

### Feature 1: AI Invoice Intelligence
- [x] VLM-powered invoice parsing (kimi-k2.5:cloud)
- [x] Support for JPG, PNG, WEBP, PDF, TXT formats
- [x] Country-specific emission factors (Kenya, Nigeria, South Africa, Ghana, Ethiopia, Egypt, Morocco, Tanzania)
- [x] Automatic scope classification (Scope 1/2/3)
- [x] Extracted data: vendor, date, location, energy type, quantity, cost
- [x] Carbon emissions calculation

### Feature 2: Blockchain Carbon Ledger
- [x] Select emission records for verification
- [x] Mock blockchain transaction (Polygon demo)
- [x] Merkle tree hash generation
- [x] QR code generation for verification
- [x] Transaction hash and block number display
- [x] Verification history

### Feature 3: ESG Report Generator
- [x] ISSB framework support
- [x] TCFD framework support  
- [x] GRI framework support
- [x] CBAM product declaration support
- [x] Annual and Quarterly reports
- [x] AI-powered narrative generation (deepseek-v3.2:cloud)
- [x] PDF export with professional styling
- [x] HTML preview

### Feature 4: Dashboard
- [x] Total emissions overview
- [x] Scope breakdown (Scope 1/2/3)
- [x] Emissions timeline chart
- [x] Recent invoices list
- [x] Recent reports list

### Authentication & UI
- [x] User registration/login
- [x] Organization auto-creation
- [x] Dark theme with green accents
- [x] Responsive sidebar navigation

---

## Prioritized Backlog

### P0 (Critical - Blocked)
- [ ] Ollama API key integration (waiting for user)
- [ ] Real Polygon blockchain integration (for production)

### P1 (High Priority)
- [ ] Batch invoice upload
- [ ] Invoice template detection (electricity bill, fuel receipt, etc.)
- [ ] Export emission data as CSV/Excel
- [ ] Email notifications for report completion

### P2 (Medium Priority)
- [ ] Multi-organization support
- [ ] Team member roles (Admin, Viewer)
- [ ] Dashboard date range filtering
- [ ] Emission reduction targets tracking
- [ ] Compare reports across periods

### P3 (Nice to Have)
- [ ] Mobile app (React Native)
- [ ] API for third-party integrations
- [ ] Supplier carbon footprint tracking
- [ ] Carbon offset marketplace integration

---

## Next Tasks
1. **Obtain Ollama API Key** - User to provide OLLAMA_API_KEY for VLM/LLM features
2. **Test with real invoices** - Upload actual energy bills to verify extraction
3. **Generate first ESG report** - Create an ISSB or CBAM report
4. **Verify on blockchain** - Test the blockchain verification flow

---

## Configuration Required
Add to `/app/backend/.env`:
```
OLLAMA_API_KEY=your_ollama_api_key_here
```

## API Endpoints
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/organizations` - Get user organizations
- `POST /api/invoices/upload` - Upload and parse invoice
- `GET /api/invoices` - Get invoices
- `POST /api/ledger/record` - Record on blockchain
- `GET /api/ledger/emissions/{org_id}` - Get emission records
- `POST /api/reports/generate` - Generate ESG report
- `POST /api/reports/cbam` - Generate CBAM declaration
- `GET /api/reports/{id}/download` - Download PDF report
- `GET /api/dashboard/{org_id}` - Get dashboard data
