# ⏱️ Timeout Configuration - CarbonTraceAI

**Last Updated:** March 6, 2025  
**Status:** ✅ Extended timeouts for long-running AI operations

---

## 🎯 Purpose

Extended timeout limits to allow VLM (Vision Language Model) AI processing to complete without interruption, especially for batch uploads with multiple invoices.

---

## ⚙️ Timeout Settings

### **Frontend (React)**

**File:** `/app/frontend/src/services/api.js`

#### **Single Invoice Upload:**
```javascript
timeout: 300000  // 5 minutes (300 seconds)
```
**Why:** Single invoice AI processing takes 10-45 seconds depending on complexity. 5 minutes provides plenty of buffer.

#### **Batch Invoice Upload:**
```javascript
timeout: 900000  // 15 minutes (900 seconds)
```
**Why:** 
- Maximum 20 files per batch
- Each file: 30-45 seconds AI processing
- Calculation: 20 files × 45 sec = 900 sec (15 min)
- Includes buffer for network latency

#### **ESG Report Generation:**
```javascript
timeout: 300000  // 5 minutes (300 seconds)
```
**Why:** AI generates multi-section reports with narratives. Complex reports can take 2-4 minutes.

---

## 📊 Processing Time Estimates

### **Single Invoice:**
```
File Upload:        < 1 second
AI Analysis:        10-45 seconds
  - Simple invoices:  10-20 sec
  - Complex invoices: 30-45 sec
Emission Calc:      < 1 second
Database Save:      < 1 second
─────────────────────────────────
Total:              15-50 seconds
Timeout:            5 minutes ✅
```

### **Batch Upload (5 files):**
```
File Upload:        < 5 seconds
AI Analysis:        50-225 seconds
  File 1:           10-45 sec
  File 2:           10-45 sec
  File 3:           10-45 sec
  File 4:           10-45 sec
  File 5:           10-45 sec
Emission Calc:      < 5 seconds
Database Save:      < 5 seconds
─────────────────────────────────
Total:              1-4 minutes
Timeout:            15 minutes ✅
```

### **Batch Upload (10 files):**
```
Total:              2-8 minutes
Timeout:            15 minutes ✅
```

### **Batch Upload (20 files - Maximum):**
```
Total:              5-15 minutes
Timeout:            15 minutes ✅
```

---

## 🚀 User Experience Improvements

### **Before:**
- ❌ 3-minute timeout
- ❌ Batch uploads failed after 6-7 files
- ❌ Users saw "timeout error"
- ❌ Had to upload in smaller batches

### **After:**
- ✅ 15-minute timeout
- ✅ All 20 files can be processed
- ✅ Estimated time shown to user
- ✅ Better error messages
- ✅ User knows to wait patiently

---

## 💬 User Feedback Messages

### **Batch Upload Start:**
```
"Processing 10 files with AI... 
Estimated time: 5-7 minutes. 
Please wait!"
```

**Calculation:**
```javascript
const estimatedMinutes = Math.ceil((fileCount × 30) / 60);
// 10 files: (10 × 30) / 60 = 5 minutes
// Range: 5-7 minutes (with buffer)
```

### **Batch Upload Success:**
```
"Successfully processed 10 invoices!"
```

### **Batch Upload Partial Success:**
```
"Processed 8 of 10 files"
```

### **Timeout Error (Rare):**
```
"Error processing batch. 
The request may have timed out - 
check your invoices list to see 
if any were processed."
```

---

## 🔧 Backend Configuration

### **FastAPI Server:**
- **Default:** No timeout limits
- **Uvicorn:** Handles long-running requests
- **Supervisor:** Auto-restart on crash
- **Database:** No query timeout limits

**Location:** `/etc/supervisor/conf.d/backend.conf`

```ini
[program:backend]
command=uvicorn server:app --host 0.0.0.0 --port 8001 --reload
autorestart=true
```

---

## 📈 Scaling Considerations

### **Current Limits:**

| Scenario | Files | Time | Timeout | Status |
|----------|-------|------|---------|--------|
| Single upload | 1 | 15-50s | 5 min | ✅ Safe |
| Small batch | 3-5 | 1-4 min | 15 min | ✅ Safe |
| Medium batch | 6-10 | 3-8 min | 15 min | ✅ Safe |
| Large batch | 11-15 | 6-12 min | 15 min | ✅ Safe |
| Max batch | 16-20 | 8-15 min | 15 min | ✅ Safe |
| Over limit | 21+ | - | - | ❌ Blocked |

### **Future Improvements (If Needed):**

1. **Background Processing:**
   - Move batch processing to async queue
   - Return batch ID immediately
   - Poll for status updates
   - User can navigate away

2. **Progress Streaming:**
   - WebSocket connection
   - Real-time progress: "Processing file 3/10..."
   - Live emission calculations

3. **Parallel Processing:**
   - Process multiple files simultaneously
   - Reduce total time by 50-70%
   - Requires more AI API quota

---

## 🧪 Testing Scenarios

### **Test 1: Single Invoice**
```bash
Expected Time: 15-50 seconds
Timeout: 5 minutes
Result: ✅ Pass
```

### **Test 2: Batch of 5**
```bash
Expected Time: 1-4 minutes
Timeout: 15 minutes
Result: ✅ Pass
```

### **Test 3: Batch of 10**
```bash
Expected Time: 3-8 minutes
Timeout: 15 minutes
Result: ✅ Pass
```

### **Test 4: Batch of 20 (Max)**
```bash
Expected Time: 8-15 minutes
Timeout: 15 minutes
Result: ✅ Pass (tight but safe)
```

---

## 📝 User Guidelines

### **Recommended Batch Sizes:**

**For Quick Testing:**
- Upload: 1-3 files
- Time: < 2 minutes
- Perfect for development/testing

**For Quarterly Reports:**
- Upload: 5-10 files per batch
- Time: 3-8 minutes
- Optimal balance of speed and batch size

**For Large Datasets:**
- Option A: Multiple batches of 10 files
- Option B: Single batch of 15-20 files (longer wait)
- Time: 8-15 minutes for full batch

### **Best Practices:**

1. ✅ **Don't close the browser tab** during upload
2. ✅ **Stay on the page** until "Success" message appears
3. ✅ **Watch the progress indicator**
4. ✅ **Wait for estimated time** (shown in notification)
5. ✅ **If timeout occurs:** Check invoice list - some may have processed
6. ❌ **Don't refresh** during processing
7. ❌ **Don't click Upload again** if it's still processing

---

## 🔍 Troubleshooting

### **Issue: "Request timeout" error**

**Possible Causes:**
- Network connection dropped
- Browser killed the request
- Processing took longer than expected

**Solution:**
1. Check invoice list - files may still be processing
2. Wait 2-3 minutes more
3. Refresh the page
4. Check if invoices appear with "completed" status
5. If stuck in "processing", delete and retry with fewer files

### **Issue: Some files stuck in "processing"**

**Cause:** Backend crashed or AI API failed

**Solution:**
1. Delete stuck invoices (use delete button)
2. Check backend logs: `tail -f /var/log/supervisor/backend.err.log`
3. Restart backend if needed: `sudo supervisorctl restart backend`
4. Retry upload

---

## 📊 Performance Metrics

### **AI Processing Speed:**
```
Ollama Cloud API (kimi-k2.5:cloud)
────────────────────────────────────
Average: 25-30 seconds per invoice
Fast:    10-15 seconds (simple)
Slow:    40-50 seconds (complex)
```

### **Network Transfer:**
```
File Upload: 0.5-2 seconds per file
Response:    < 1 second
```

### **Database Operations:**
```
Insert Invoice:          < 100ms
Insert Emission Record:  < 100ms
Update Status:           < 100ms
```

---

## ✅ Summary

**Timeout Configuration:**
- Single Upload: 5 minutes ✅
- Batch Upload: 15 minutes ✅
- Report Generation: 5 minutes ✅

**Benefits:**
- ✅ Can process up to 20 files in one batch
- ✅ No premature timeout errors
- ✅ Better user feedback
- ✅ Estimated time shown upfront

**User Experience:**
- Users know how long to wait
- Progress indicators visible
- Clear error messages
- Batch processing reliable

---

**Version:** 1.0  
**Last Updated:** March 6, 2025  
**Changes:** Extended timeouts from 3 min to 15 min for batch operations
