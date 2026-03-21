# CarbonTraceAI - Quick Reference Guide

## 🚀 Quick Start (5 Minutes)

### 1. Create Account
→ Register → Enter details → Auto-login

### 2. Upload Invoice
→ Invoice Parser → Upload → Wait 30-60s → View results

### 3. Connect ERP (Optional)
→ ERP Integrations → Add Connection → 2-Step Wizard → Test & Connect

### 4. Generate Report
→ ESG Reports → Generate → Select type → Download PDF

---

## 📋 Feature Checklist

### Carbon Accounting
- [ ] Register & Login
- [ ] Upload first invoice
- [ ] View extracted data
- [ ] Add manual ledger entry
- [ ] Generate first ESG report

### ERP Integration
- [ ] Connect ERP system
- [ ] Test connection health
- [ ] Trigger data extraction
- [ ] View normalized data
- [ ] Export CBAM XML

---

## 🔑 Key Endpoints

**Frontend:** http://localhost:3000  
**Backend API:** Check `.env` REACT_APP_BACKEND_URL  
**API Docs:** `/docs` (Swagger UI)  
**Metrics:** `/api/metrics` (Prometheus)

---

## 📊 Supported ERP Systems

1. ✅ **Odoo** (API) - Most popular open-source
2. ✅ **SYSPRO** (SQL) - Manufacturing focus
3. ✅ **SAP Business One** (API) - Enterprise SME
4. ✅ **ERPNext** (API) - Open-source alternative
5. ✅ **Sage Business Cloud** (API) - Accounting focus
6. ✅ **Dynamics 365 BC** (API) - Microsoft stack

---

## 🎯 Common Use Cases

### Use Case 1: Monthly Carbon Report
**Steps:**
1. Upload all invoices from the month
2. System auto-calculates emissions
3. Generate TCFD report
4. Download and share with stakeholders

**Time:** 10 minutes

---

### Use Case 2: CBAM Export Compliance
**Steps:**
1. Connect production ERP (e.g., Odoo)
2. Extract production + energy data
3. View normalized records
4. Export CBAM XML
5. Submit to EU customs

**Time:** 15 minutes (excluding ERP setup)

---

### Use Case 3: ESG Due Diligence
**Steps:**
1. Add all emission records to ledger
2. Verify blockchain hashes
3. Generate GRI sustainability report
4. Share with investors/auditors

**Time:** 20 minutes

---

## 🔧 Troubleshooting

### Issue: ERP Connection Failed
**Solutions:**
- Check ERP credentials are correct
- Verify ERP server is accessible
- Test network connectivity
- Check firewall rules
- Review error message in health check

### Issue: Invoice Parsing Slow
**Possible Causes:**
- Large PDF file (>10MB)
- High server load
- Ollama API rate limits

**Solutions:**
- Compress PDF before upload
- Wait for current jobs to complete
- Check job status endpoint

### Issue: Export Button Disabled
**Reason:** No normalized data available

**Solution:**
- Ensure extraction job completed successfully
- Check data viewer shows records
- Verify job status is "Completed"

### Issue: WebSocket Not Updating
**Reason:** Currently using polling (5s intervals)

**Solution:**
- WebSocket infrastructure ready but not yet replacing polling
- Refresh browser if status seems stale

---

## 📈 Data Limits

| Feature | Limit | Notes |
|---------|-------|-------|
| Single Invoice Upload | 50MB | Larger files may timeout |
| Batch Upload | 10 files | Process in parallel |
| ERP Extraction | 10,000 records | Per job |
| Data Viewer | 100 records | Default pagination |
| API Rate Limit | 60/min | General endpoints |
| ERP Extraction Rate | 5/min | Heavy operations |

---

## 🔐 Security Best Practices

1. **Change default passwords** after first login
2. **Use strong ERP credentials** (20+ characters)
3. **Rotate API keys** every 90 days
4. **Enable 2FA** (future feature)
5. **Review audit logs** monthly
6. **Limit user permissions** (use RBAC when available)

---

## 📞 Support Resources

**Documentation:** `/app/COMPLETE_DOCUMENTATION.md`  
**API Reference:** Backend `/docs` endpoint  
**Test Reports:** `/app/test_reports/`  
**Logs:** `/var/log/supervisor/`

---

## 🎓 Learning Path

### Beginner (Week 1)
- Day 1: Registration, upload 1 invoice
- Day 2: Explore dashboard, view ledger
- Day 3: Generate first report
- Day 4: Understand Scope 1/2/3
- Day 5: Add manual ledger entries

### Intermediate (Week 2)
- Day 1: Connect first ERP system
- Day 2: Trigger extraction, view data
- Day 3: Understand field mappings
- Day 4: Export CBAM XML
- Day 5: Schedule regular extractions

### Advanced (Week 3)
- Day 1: Use API endpoints directly
- Day 2: Set up monitoring (Prometheus)
- Day 3: Customize field mappings
- Day 4: Integrate with external systems
- Day 5: Automate workflows

---

## 📦 Data Export Options

1. **CBAM XML** - EU compliance (from Data Viewer)
2. **ESG Reports PDF** - Stakeholder reporting
3. **CSV Export** - Future feature (raw data)
4. **API Access** - Programmatic data retrieval

---

## 🏆 Success Metrics

Track your carbon accounting maturity:

**Level 1: Getting Started**
- ✅ 10+ invoices uploaded
- ✅ First report generated
- ✅ Ledger has 20+ entries

**Level 2: Regular User**
- ✅ 1 ERP connected
- ✅ Monthly extraction schedule
- ✅ Quarterly reports generated

**Level 3: Power User**
- ✅ 2+ ERPs connected
- ✅ CBAM exports regular
- ✅ Blockchain verification used
- ✅ API integration set up

---

## 🌟 Pro Tips

1. **Batch uploads save time** - Upload 5-10 invoices at once
2. **Name files clearly** - Use "Supplier_Month_Year.pdf" format
3. **Regular extractions** - Weekly ERP syncs prevent data gaps
4. **Verify before export** - Check normalized data accuracy
5. **Use filters** - Data viewer filters help find specific records
6. **Bookmark common tasks** - Save URLs for frequent actions
7. **Monitor health** - Weekly health checks on ERP connections
8. **Document customizations** - If you modify field mappings

---

## 🔄 Update Schedule

**Platform Updates:** Monthly
**Security Patches:** As needed
**Feature Releases:** Quarterly
**ERP Connector Additions:** On-demand

---

## 🌍 Regional Considerations

**East Africa (Kenya, Tanzania, Uganda)**
- High Odoo adoption
- Grid emission factors vary significantly
- Consider hydropower vs. diesel generation

**South Africa**
- Strong SAP presence
- Mature ESG reporting requirements
- High coal emissions

**West Africa (Nigeria, Ghana)**
- Growing SME digitalization
- Mix of ERPs (QuickBooks, Zoho, custom)
- Grid instability - diesel backup common

**North Africa**
- French-speaking markets
- Need multi-language support
- Strong EU trade ties - CBAM critical

---

*Quick Reference v2.0.0 - March 2026*
