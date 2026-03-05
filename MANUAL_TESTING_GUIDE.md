# 🧪 CarbonTraceAI - Complete Manual Testing Guide

## 📋 Table of Contents
1. [Initial Setup](#initial-setup)
2. [User Registration](#user-registration)
3. [User Login](#user-login)
4. [Dashboard Overview](#dashboard-overview)
5. [Invoice Upload & AI Parsing](#invoice-upload--ai-parsing)
6. [Viewing Invoices & Emission Records](#viewing-invoices--emission-records)
7. [Carbon Ledger & Blockchain Verification](#carbon-ledger--blockchain-verification)
8. [ESG Report Generation](#esg-report-generation)
9. [Batch Invoice Upload](#batch-invoice-upload)
10. [Organization Management](#organization-management)
11. [Testing Different Invoice Types](#testing-different-invoice-types)

---

## 🌐 Initial Setup

### Application URL
```
https://f234f04a-ce0d-43b6-9cfe-74f80c24c0b1.preview.emergentagent.com
```

### Pre-created Test Accounts
**Account 1:**
- Email: `demo@carbontraceai.com`
- Password: `Demo123!`

**Account 2:**
- Email: `test@carbontrace.ai`
- Password: `testpass123`

---

## 1️⃣ User Registration

### Step-by-Step:

1. **Open the Application**
   - Navigate to: `https://f234f04a-ce0d-43b6-9cfe-74f80c24c0b1.preview.emergentagent.com`
   - You should see the login page with dark theme and green accents

2. **Click "Create one"**
   - Located at the bottom: "Don't have an account? Create one"
   - This navigates to the registration page

3. **Fill Registration Form**
   - **Full Name:** Your Name (e.g., "John Doe")
   - **Email:** Your email (e.g., "john@company.com")
   - **Password:** Create a password (min 6 characters)
   - **Confirm Password:** Re-enter the same password

4. **Click "Create Account" Button**
   - Green button at the bottom

5. **Expected Result:**
   - ✅ Success toast notification appears: "Account created successfully!"
   - ✅ Automatically logs you in
   - ✅ Redirects to Dashboard
   - ✅ Default organization is created automatically

---

## 2️⃣ User Login

### Step-by-Step:

1. **Open Login Page**
   - Navigate to the application URL
   - If already logged in, logout first (click user icon → Logout)

2. **Enter Credentials**
   - **Email:** `demo@carbontraceai.com`
   - **Password:** `Demo123!`

3. **Click "Sign In" Button**
   - Green button with arrow icon

4. **Expected Result:**
   - ✅ Success toast: "Welcome back!"
   - ✅ Redirects to Dashboard
   - ✅ User info loaded in header

### What to Check:
- ✅ No error messages
- ✅ Smooth transition to dashboard
- ✅ Green theme elements visible
- ✅ Navigation sidebar/menu appears

---

## 3️⃣ Dashboard Overview

### Step-by-Step:

1. **After Login, You're on Dashboard**
   - URL should be: `.../dashboard`

2. **Observe the Stats Cards** (Top Section)
   - **Total Emissions:** Shows total CO2e in kg
   - **Scope 1:** Direct emissions
   - **Scope 2:** Indirect energy emissions
   - **Scope 3:** Value chain emissions
   - **Invoice Count:** Number of uploaded invoices
   - **Verified Records:** Blockchain-verified records
   - **Report Count:** Generated reports

3. **Check Emissions by Scope Chart**
   - Pie chart showing Scope 1, 2, 3 breakdown
   - Colors: Orange (Scope 1), Blue (Scope 2), Yellow (Scope 3)

4. **View Emissions Timeline**
   - Line chart showing last 6 months of emissions
   - X-axis: Months, Y-axis: Emissions (kg CO2e)

5. **Recent Invoices Section**
   - Lists last 5 uploaded invoices
   - Shows: filename, date, status

6. **Recent Reports Section**
   - Lists last 5 generated reports
   - Shows: framework, date, status

### What to Check:
- ✅ All cards display properly
- ✅ Charts render correctly
- ✅ Numbers are formatted (commas for thousands)
- ✅ Dark theme with green accents
- ✅ Responsive layout

---

## 4️⃣ Invoice Upload & AI Parsing

### Step-by-Step:

1. **Navigate to Invoices Page**
   - Click "Invoices" in sidebar/navigation
   - Or use top menu

2. **Click "Upload Invoice" Button**
   - Green button at top-right

3. **Select Test Invoice File**
   - Use the test invoice I created: `/tmp/test_invoice.txt`
   - Or create your own (see sample below)

4. **Fill Upload Form**
   - **File:** Select file (JPG, PNG, PDF, TXT, WEBP)
   - **Country:** Select "Kenya" (or your country)
   - Click "Upload & Parse" button

5. **Wait for AI Processing**
   - Progress indicator shows
   - Usually takes 10-30 seconds
   - AI model (Kimi K2.5) analyzes the invoice

6. **View Results**
   - Success notification appears
   - Invoice appears in list with status "Completed"

### Expected AI Extraction:
For the test Kenya Power invoice:
- ✅ **Vendor:** KENYA POWER & LIGHTING COMPANY LIMITED
- ✅ **Customer:** Test Company Ltd
- ✅ **Account Number:** 12345678
- ✅ **Meter Number:** KE-567890
- ✅ **Billing Period:** 2024-01-01 to 2024-01-31
- ✅ **Consumption:** 3,220 kWh
- ✅ **Total Amount:** KES 84,332.00
- ✅ **Currency:** KES
- ✅ **Document Type:** electricity_bill
- ✅ **Total Emissions:** 1,449.45 kg CO2e

### Sample Test Invoice (Copy & Save as .txt):
```
KENYA POWER & LIGHTING COMPANY LIMITED
Electric Bill

Account Number: 12345678
Customer Name: Test Company Ltd
Service Address: Nairobi, Kenya
Meter Number: KE-567890

Bill Date: February 15, 2024
Due Date: March 10, 2024
Billing Period: January 1, 2024 - January 31, 2024

Previous Reading: 45,230 kWh
Current Reading: 48,450 kWh
Consumption: 3,220 kWh

CHARGES:
Energy Charge (3,220 kWh @ KES 22.50/kWh): KES 72,450.00
Fixed Charge: KES 250.00
VAT (16%): KES 11,632.00

Total Amount Due: KES 84,332.00

Please pay by the due date to avoid disconnection.
Thank you for choosing Kenya Power.
```

### What to Check:
- ✅ File uploads without errors
- ✅ AI parsing completes successfully
- ✅ Extracted data is accurate
- ✅ Emissions calculated correctly
- ✅ Scope classification is correct (electricity = Scope 2)
- ✅ Country-specific emission factor used (Kenya = 0.45 kg/kWh)

---

## 5️⃣ Viewing Invoices & Emission Records

### Step-by-Step:

1. **View Invoice List**
   - Navigate to "Invoices" page
   - See all uploaded invoices in a table

2. **Click on an Invoice**
   - Click any invoice row to view details

3. **Review Extracted Data**
   - **Vendor Information:** Name, address, contact
   - **Customer Information:** Name, account number
   - **Billing Details:** Period, dates, meter readings
   - **Financial Information:** Amount, currency, taxes
   - **Emissions Data:** Total emissions, scope classification

4. **View Emission Records**
   - Navigate to "Carbon Ledger" page
   - Or click "Emissions" tab on invoice detail

5. **Check Emission Record Details**
   - **Energy Type:** electricity, diesel, etc.
   - **Quantity:** Amount consumed
   - **Unit:** kWh, liters, m3, etc.
   - **Scope Type:** Scope 1, 2, or 3
   - **CO2 Emissions:** Calculated in kg
   - **Cost:** Associated cost
   - **Verification Status:** Verified or Not Verified

### What to Check:
- ✅ All invoices display in list
- ✅ Sorting/filtering works
- ✅ Detail view shows all extracted fields
- ✅ Emission records linked to invoice
- ✅ Calculations are correct
- ✅ Status badges show correctly (Completed, Processing, Failed)

---

## 6️⃣ Carbon Ledger & Blockchain Verification

### Step-by-Step:

1. **Navigate to Carbon Ledger Page**
   - Click "Ledger" or "Carbon Ledger" in navigation

2. **View Emission Records**
   - See list of all emission records
   - Filter by: All, Verified Only, Unverified

3. **Select Records for Verification**
   - Click checkboxes next to emission records
   - Select one or multiple records

4. **Click "Record on Blockchain" Button**
   - Green button at top

5. **Confirm Blockchain Recording**
   - Dialog appears
   - Click "Confirm"

6. **Wait for Processing**
   - System creates Merkle tree
   - Generates transaction hash
   - Creates QR code for verification

7. **View Blockchain Record**
   - Success notification appears
   - Record status changes to "Verified"
   - Click record to see details:
     - **Transaction Hash:** 0x... (64 characters)
     - **Block Number:** e.g., 1000123
     - **Data Hash:** SHA256 hash
     - **Merkle Root:** Hash of all records
     - **Verification URL:** Polygonscan link
     - **QR Code:** Scannable code

### What to Check:
- ✅ Records can be selected
- ✅ Blockchain recording completes
- ✅ Transaction hash is generated
- ✅ QR code is created
- ✅ Verification URL is valid format
- ✅ Status updates to "Verified"
- ✅ Green checkmark appears

---

## 7️⃣ ESG Report Generation

### Step-by-Step:

1. **Navigate to Reports Page**
   - Click "Reports" in navigation

2. **Click "Generate Report" Button**
   - Green button at top-right

3. **Fill Report Form**
   - **Report Framework:** Select one
     - ISSB (Investor-focused)
     - TCFD (Climate risk)
     - GRI (ESG impact)
     - CBAM (EU export compliance)
   - **Report Period:** e.g., "2024", "Q1 2024"
   - **Report Type:** Annual, Quarterly, Monthly
   - **Date Range:** Optional start/end dates

4. **Click "Generate Report" Button**

5. **Wait for AI Processing**
   - Progress indicator shows
   - AI generates narratives for each section
   - Takes 30-90 seconds
   - Creates PDF

6. **View Generated Report**
   - Success notification
   - Report appears in list with status "Completed"
   - Click to view details

7. **Preview Report (HTML)**
   - Click "Preview" button
   - Opens HTML version in new tab

8. **Download Report (PDF)**
   - Click "Download PDF" button
   - PDF opens/downloads

### Report Contents:

#### Cover Page:
- Organization name
- Report period
- Framework name
- Compliance badges

#### Sections:
1. **Executive Summary** (AI-generated)
2. **Emissions Overview**
   - Stats cards (Scope 1, 2, 3, Total)
   - Narrative
3. **Governance** (AI-generated)
4. **Strategy** (AI-generated)
5. **Risk Management** (AI-generated)
6. **Metrics & Targets**
   - Data table
   - Narrative
7. **CBAM Product Declaration** (if CBAM selected)
8. **Footer**
   - Generation timestamp
   - Blockchain verification badge
   - Compliance statement

### What to Check:
- ✅ All 4 frameworks available
- ✅ Form validation works
- ✅ AI generates professional narratives
- ✅ PDF is created successfully
- ✅ PDF has proper formatting (dark theme, green accents)
- ✅ All sections included
- ✅ Stats match dashboard
- ✅ Professional language
- ✅ No spelling/grammar errors in AI text
- ✅ Download works

---

## 8️⃣ Batch Invoice Upload

### Step-by-Step:

1. **Navigate to Invoices Page**

2. **Click "Batch Upload" Button**
   - Should be near "Upload Invoice" button

3. **Select Multiple Files**
   - Click file selector
   - Select 2-20 files (max limit)
   - Supported: JPG, PNG, PDF, TXT, WEBP

4. **Fill Batch Upload Form**
   - **Country:** Select country for emission factors
   - **Quarter:** Optional (Q1, Q2, Q3, Q4)
   - **Year:** Optional (e.g., 2024)

5. **Click "Upload Batch" Button**

6. **Monitor Progress**
   - Progress bar shows
   - Individual file status updates
   - AI processes each file

7. **View Batch Results**
   - Summary appears:
     - **Total Files:** Number uploaded
     - **Successful:** Files parsed successfully
     - **Failed:** Files that failed
     - **Total Emissions:** Aggregate across all
     - **Scope 1/2/3 Breakdown**
   - Individual invoice details listed

8. **Click Batch ID to View Details**
   - See all invoices in the batch
   - View aggregate emissions
   - Filter/sort batch invoices

### What to Check:
- ✅ Can upload multiple files
- ✅ Max 20 files enforced
- ✅ Each file processed individually
- ✅ Progress updates correctly
- ✅ Aggregate calculations correct
- ✅ Batch ID generated
- ✅ All invoices linked to batch
- ✅ Failed files reported with reasons

---

## 9️⃣ Organization Management

### Step-by-Step:

1. **View Current Organization**
   - Look at header/top-right
   - Shows current organization name

2. **Access Organization Settings**
   - Click user menu (top-right)
   - Click "Organizations" or similar

3. **View Organization List**
   - See all organizations you own
   - Default organization created on signup

4. **Create New Organization**
   - Click "Create Organization" button
   - Fill form:
     - **Name:** e.g., "Nairobi Operations"
     - **Industry:** e.g., "Manufacturing"
     - **Country:** e.g., "Kenya"
   - Click "Create"

5. **Switch Organization**
   - Click dropdown in header
   - Select different organization
   - Dashboard updates with that org's data

### What to Check:
- ✅ Default org created automatically
- ✅ Can create additional orgs
- ✅ Can switch between orgs
- ✅ Data isolated per organization
- ✅ Dashboard shows correct org data

---

## 🔟 Testing Different Invoice Types

### Test Different Document Types:

#### 1. **Electricity Bill**
```
Status: ✅ Working
Expected Scope: Scope 2
Expected Extraction: kWh consumption, meter readings
```

#### 2. **Diesel Fuel Receipt**
```
Status: ✅ Working  
Expected Scope: Scope 1 (direct combustion)
Expected Extraction: Liters, price per liter
Sample emission factor: 2.68 kg CO2/liter
```

Sample Diesel Receipt:
```
SHELL FUEL STATION
Nairobi, Kenya

Date: March 1, 2024
Transaction ID: SH-789456

DIESEL FUEL
Quantity: 150 liters
Price per liter: KES 135.00
Total: KES 20,250.00

Vehicle: KBX 123Y
```

#### 3. **Natural Gas Bill**
```
Status: ✅ Working
Expected Scope: Scope 1 (direct combustion)
Expected Extraction: m3 consumption
Sample emission factor: 2.0 kg CO2/m3
```

#### 4. **Water Bill**
```
Status: ✅ Working
Expected Scope: Scope 3 (indirect)
Expected Extraction: m3 or liters consumed
Sample emission factor: 0.0003 kg CO2/liter
```

#### 5. **Transport/Logistics Invoice**
```
Status: ✅ Working
Expected Scope: Scope 3 (value chain)
Expected Extraction: km traveled or delivery details
```

### What to Check:
- ✅ Different document types recognized
- ✅ Correct energy type identified
- ✅ Appropriate scope assigned
- ✅ Correct emission factor used
- ✅ Units properly normalized

---

## 📊 Complete Feature Checklist

### Authentication
- [ ] Registration works
- [ ] Login works
- [ ] Logout works
- [ ] Session persists on refresh
- [ ] Error messages clear

### Dashboard
- [ ] Stats cards display correctly
- [ ] Scope breakdown chart works
- [ ] Timeline chart shows data
- [ ] Recent items load
- [ ] Responsive design

### Invoice Upload
- [ ] Single upload works
- [ ] Batch upload works
- [ ] AI parsing extracts data
- [ ] File validation works
- [ ] Progress indicators show
- [ ] Error handling works

### Emission Records
- [ ] Records display in list
- [ ] Detail view shows all fields
- [ ] Filtering works
- [ ] Sorting works
- [ ] Calculations correct

### Carbon Ledger
- [ ] Record selection works
- [ ] Blockchain recording works
- [ ] Transaction hash generated
- [ ] QR code created
- [ ] Verification status updates

### Reports
- [ ] All 4 frameworks available
- [ ] Report generation works
- [ ] AI narratives generated
- [ ] PDF created correctly
- [ ] Preview works
- [ ] Download works
- [ ] Formatting correct

### UI/UX
- [ ] Dark theme throughout
- [ ] Green accent color consistent
- [ ] Navigation works
- [ ] Buttons responsive
- [ ] Forms validate
- [ ] Toasts/notifications show
- [ ] Loading states clear

---

## 🐛 Common Issues & Solutions

### Issue 1: Login Not Working
**Solution:** Check browser console for errors, verify email/password

### Issue 2: Invoice Upload Fails
**Solution:** 
- Check file size (max 25MB)
- Verify file format (JPG, PNG, PDF, TXT, WEBP)
- Check internet connection

### Issue 3: AI Parsing Returns Empty Data
**Solution:** 
- Invoice text might be unclear
- Try different file format
- Check Ollama API key is set

### Issue 4: Report Generation Times Out
**Solution:**
- AI generation takes time
- Wait 60-90 seconds
- Check backend logs

### Issue 5: Charts Not Showing
**Solution:**
- Upload some invoices first
- Refresh page
- Check browser console

---

## 📝 Testing Scenarios

### Scenario 1: Complete New User Flow
1. Register new account
2. Login
3. View empty dashboard
4. Upload first invoice
5. View emission record
6. Record on blockchain
7. Generate first report

### Scenario 2: Monthly Reporting Workflow
1. Upload all month's invoices (batch)
2. Review all emission records
3. Verify records on blockchain
4. Generate ISSB report
5. Download PDF
6. Share with stakeholders

### Scenario 3: Multi-Organization Setup
1. Create organization for each office
2. Upload invoices per organization
3. Switch between organizations
4. Compare emissions across locations

---

## 🎯 Expected Performance

- **Login:** < 2 seconds
- **Dashboard Load:** < 3 seconds
- **Invoice Upload:** < 5 seconds (file transfer)
- **AI Parsing:** 10-30 seconds per invoice
- **Batch Upload (10 files):** 2-5 minutes
- **Blockchain Recording:** < 5 seconds
- **Report Generation:** 30-90 seconds
- **PDF Download:** < 5 seconds

---

## ✅ Testing Complete!

If all features work as described, your CarbonTraceAI application is fully functional and ready for production use!

**Need Help?**
- Check backend logs: `sudo supervisorctl tail backend`
- Check frontend logs: `sudo supervisorctl tail frontend`
- MongoDB logs: `sudo journalctl -u mongodb`

---

**Version:** 1.0  
**Last Updated:** March 5, 2026  
**Tested Environment:** Emergent Preview Deployment
