import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { Layout } from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Label } from '../components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Progress } from '../components/ui/progress';
import { 
  Upload, FileText, CheckCircle2, AlertCircle, Loader2, Cloud, 
  Trash2, Eye, MapPin, Calendar, DollarSign, Zap, Files, X,
  Building, Gauge, Receipt, TrendingUp
} from 'lucide-react';
import { toast } from 'sonner';

const COUNTRIES = [
  { value: 'default', label: 'Default (Global Average)' },
  { value: 'kenya', label: 'Kenya' },
  { value: 'nigeria', label: 'Nigeria' },
  { value: 'south_africa', label: 'South Africa' },
  { value: 'ghana', label: 'Ghana' },
  { value: 'ethiopia', label: 'Ethiopia' },
  { value: 'egypt', label: 'Egypt' },
  { value: 'morocco', label: 'Morocco' },
  { value: 'tanzania', label: 'Tanzania' },
];

const QUARTERS = [
  { value: 'Q1', label: 'Q1 (Jan-Mar)' },
  { value: 'Q2', label: 'Q2 (Apr-Jun)' },
  { value: 'Q3', label: 'Q3 (Jul-Sep)' },
  { value: 'Q4', label: 'Q4 (Oct-Dec)' },
];

export function InvoicesPage() {
  const { organization } = useAuth();
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [parseResult, setParseResult] = useState(null);
  const [batchResult, setBatchResult] = useState(null);
  const [selectedCountry, setSelectedCountry] = useState('default');
  const [selectedQuarter, setSelectedQuarter] = useState('');
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear().toString());
  const [uploadMode, setUploadMode] = useState('single');
  const [batchFiles, setBatchFiles] = useState([]);
  const [uploadProgress, setUploadProgress] = useState(0);

  useEffect(() => {
    if (organization?.id) {
      fetchInvoices();
    }
  }, [organization?.id]);

  const fetchInvoices = async () => {
    try {
      const response = await api.getInvoices(organization.id);
      setInvoices(response.data);
    } catch (error) {
      console.error('Error fetching invoices:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSingleUpload = async (file) => {
    if (!file) return;

    const allowedExtensions = ['jpg', 'jpeg', 'png', 'webp', 'pdf', 'txt'];
    const ext = file.name.split('.').pop().toLowerCase();
    
    if (!allowedExtensions.includes(ext)) {
      toast.error('Unsupported file type. Please upload JPG, PNG, WEBP, PDF, or TXT files.');
      return;
    }

    if (file.size > 25 * 1024 * 1024) {
      toast.error('File size exceeds 25MB limit.');
      return;
    }

    setUploading(true);
    setParseResult(null);
    setBatchResult(null);

    try {
      // Upload the file - returns immediately with task_id
      toast.info('Starting invoice upload...', { duration: 2000 });
      const response = await api.uploadInvoice(file, organization.id, selectedCountry);
      const { task_id, invoice_id } = response.data;
      
      toast.info(`AI is analyzing your invoice in background...`, {
        duration: 5000,
        id: 'ai-processing'
      });
      
      // Poll task status
      let attempts = 0;
      const maxAttempts = 120; // 120 × 3 sec = 6 minutes (enough for AI processing)
      
      while (attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 3000)); // Wait 3 seconds
        
        const statusResponse = await api.getUploadStatus(task_id);
        const taskStatus = statusResponse.data;
        
        // Log for debugging
        console.log(`Upload attempt ${attempts}: status=${taskStatus.status}, progress=${taskStatus.progress}`);
        
        if (taskStatus.status === 'completed') {
          toast.dismiss('ai-processing');
          
          // Fetch the completed invoice
          const invoiceResponse = await api.getInvoice(invoice_id);
          const invoice = invoiceResponse.data;
          setParseResult(invoice);
          
          if (invoice.extracted_data?.parse_error) {
            toast.warning('Invoice processed with some issues. Please review the data.');
          } else {
            toast.success('Invoice parsed successfully by AI!');
          }
          break;
        } else if (taskStatus.status === 'failed') {
          toast.dismiss('ai-processing');
          toast.error(`Failed to parse invoice: ${taskStatus.error || 'Unknown error'}`);
          break;
        } else if (taskStatus.status === 'processing' || taskStatus.status === 'queued') {
          // Show progress update every 10 attempts (30 seconds)
          if (attempts > 0 && attempts % 10 === 0) {
            const elapsed = Math.floor(attempts * 3 / 60);
            const progressMsg = taskStatus.status === 'queued' 
              ? `Waiting to start... (${elapsed} min elapsed)`
              : `AI processing... ${taskStatus.progress || 0}% complete (${elapsed} min elapsed)`;
            toast.info(progressMsg, {
              duration: 5000,
              id: 'ai-processing'
            });
          }
        }
        
        attempts++;
      }
      
      if (attempts >= maxAttempts) {
        toast.dismiss('ai-processing');
        toast.warning('Processing is taking longer than expected. Check the invoice list in a few minutes - it may still be processing.');
      }
      
      fetchInvoices();
    } catch (error) {
      toast.dismiss('ai-processing');
      toast.error(`Upload error: ${error.response?.data?.detail || error.message || 'Network error'}`);
    } finally {
      setUploading(false);
    }
  };

  const handleBatchUpload = async () => {
    if (batchFiles.length === 0) {
      toast.error('Please select files to upload');
      return;
    }

    setUploading(true);
    setParseResult(null);
    setBatchResult(null);
    setUploadProgress(10);
    
    toast.info(`Starting batch upload for ${batchFiles.length} files...`, {
      duration: 3000,
      id: 'batch-upload'
    });

    try {
      // Initiate async batch upload - returns immediately with task_id
      const response = await api.batchUploadInvoices(
        batchFiles,
        organization.id,
        selectedCountry,
        selectedQuarter === 'none' ? null : selectedQuarter || null,
        selectedYear || null
      );
      
      const { task_id, batch_id } = response.data;
      setUploadProgress(20);
      
      toast.info(`AI is processing ${batchFiles.length} files in background...`, {
        duration: 5000,
        id: 'batch-upload'
      });
      
      // Poll task status
      let attempts = 0;
      const maxAttempts = 150; // 150 × 3 sec = 7.5 minutes (enough for large batches)
      
      while (attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 3000)); // Wait 3 seconds
        
        const statusResponse = await api.getBatchUploadStatus(task_id);
        const taskStatus = statusResponse.data;
        
        // Log for debugging
        console.log(`Batch attempt ${attempts}: status=${taskStatus.status}, progress=${taskStatus.progress}`);
        
        setUploadProgress(20 + (taskStatus.progress || 0) * 0.7);
        
        if (taskStatus.status === 'completed') {
          toast.dismiss('batch-upload');
          const result = taskStatus.result;
          
          setUploadProgress(100);
          setBatchResult(result);
          setBatchFiles([]);
          
          if (result.failed > 0 && result.successful > 0) {
            toast.warning(`Batch Complete: ${result.successful} succeeded, ${result.failed} failed.`);
          } else if (result.failed > 0) {
            toast.error(`All ${result.failed} files failed to process.`);
          } else {
            toast.success(`Success! All ${result.successful} invoices processed!`);
          }
          break;
        } else if (taskStatus.status === 'failed') {
          toast.dismiss('batch-upload');
          toast.error(`Batch processing failed: ${taskStatus.error || 'Unknown error'}`);
          break;
        } else if (taskStatus.status === 'processing' || taskStatus.status === 'queued') {
          // Show progress update every 10 attempts (30 seconds)
          if (attempts > 0 && attempts % 10 === 0) {
            const elapsed = Math.floor(attempts * 3 / 60);
            const progressMsg = taskStatus.status === 'queued'
              ? `Waiting to start batch processing... (${elapsed} min elapsed)`
              : `AI Processing batch... ${taskStatus.progress || 0}% complete (${elapsed} min elapsed)`;
            toast.info(progressMsg, {
              duration: 5000,
              id: 'batch-upload'
            });
          }
        }
        
        attempts++;
      }
      
      if (attempts >= maxAttempts) {
        toast.dismiss('batch-upload');
        toast.warning('Batch processing is taking longer than expected. Check your invoices list in a few minutes - they may still be processing.');
      }
      
      fetchInvoices();
    } catch (error) {
      toast.dismiss('batch-upload');
      toast.error(`Batch upload error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    
    const droppedFiles = Array.from(e.dataTransfer.files);
    
    if (uploadMode === 'single' && droppedFiles.length > 0) {
      handleSingleUpload(droppedFiles[0]);
    } else if (uploadMode === 'batch') {
      const validFiles = droppedFiles.filter(f => {
        const ext = f.name.split('.').pop().toLowerCase();
        return ['jpg', 'jpeg', 'png', 'webp', 'pdf', 'txt'].includes(ext);
      });
      setBatchFiles(prev => [...prev, ...validFiles].slice(0, 20));
    }
  }, [uploadMode, organization?.id, selectedCountry]);

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    
    if (uploadMode === 'single' && files.length > 0) {
      handleSingleUpload(files[0]);
    } else if (uploadMode === 'batch') {
      const validFiles = files.filter(f => {
        const ext = f.name.split('.').pop().toLowerCase();
        return ['jpg', 'jpeg', 'png', 'webp', 'pdf', 'txt'].includes(ext);
      });
      setBatchFiles(prev => [...prev, ...validFiles].slice(0, 20));
    }
  };

  const removeFromBatch = (index) => {
    setBatchFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleDeleteInvoice = async (invoiceId) => {
    if (!window.confirm('Delete this invoice and its emission records?')) return;
    
    try {
      await api.deleteInvoice(invoiceId);
      toast.success('Invoice deleted');
      fetchInvoices();
    } catch (error) {
      toast.error('Error deleting invoice');
    }
  };

  const formatEmissions = (value) => {
    if (!value) return '0';
    if (value >= 1000) return `${(value / 1000).toFixed(2)}K`;
    return value.toFixed(2);
  };

  const getScopeColor = (scope) => {
    switch (scope) {
      case 'Scope1': return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
      case 'Scope2': return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      case 'Scope3': return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      default: return 'bg-muted text-muted-foreground';
    }
  };

  return (
    <Layout>
      <div className="space-y-8 animate-fade-in">
        {/* Header */}
        <div>
          <h1 className="text-3xl md:text-4xl font-bold font-['Outfit'] tracking-tight" data-testid="invoices-title">
            AI Invoice Intelligence
          </h1>
          <p className="text-muted-foreground mt-1">
            Upload energy invoices to automatically extract carbon emission data using VLM
          </p>
        </div>

        {/* Upload Zone */}
        <Card className="bg-card border-border">
          <CardContent className="p-6">
            <Tabs value={uploadMode} onValueChange={setUploadMode} className="w-full">
              <TabsList className="mb-6">
                <TabsTrigger value="single" className="flex items-center gap-2">
                  <FileText className="w-4 h-4" />
                  Single Invoice
                </TabsTrigger>
                <TabsTrigger value="batch" className="flex items-center gap-2">
                  <Files className="w-4 h-4" />
                  Batch Upload (Quarterly)
                </TabsTrigger>
              </TabsList>

              {/* Settings Row */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <div>
                  <Label className="text-xs text-muted-foreground">Country (Emission Factors)</Label>
                  <Select value={selectedCountry} onValueChange={setSelectedCountry}>
                    <SelectTrigger className="mt-1" data-testid="country-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {COUNTRIES.map((c) => (
                        <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                {uploadMode === 'batch' && (
                  <>
                    <div>
                      <Label className="text-xs text-muted-foreground">Quarter (Optional)</Label>
                      <Select value={selectedQuarter} onValueChange={setSelectedQuarter}>
                        <SelectTrigger className="mt-1">
                          <SelectValue placeholder="Select quarter" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="none">None</SelectItem>
                          {QUARTERS.map((q) => (
                            <SelectItem key={q.value} value={q.value}>{q.label}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label className="text-xs text-muted-foreground">Year (Optional)</Label>
                      <Select value={selectedYear} onValueChange={setSelectedYear}>
                        <SelectTrigger className="mt-1">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {[2024, 2025, 2026].map((y) => (
                            <SelectItem key={y} value={y.toString()}>{y}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </>
                )}
              </div>

              <TabsContent value="single">
                <div
                  className={`upload-zone rounded-xl p-10 text-center transition-all ${dragOver ? 'dragover' : ''}`}
                  onDrop={handleDrop}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  data-testid="upload-zone"
                >
                  {uploading ? (
                    <div className="space-y-4">
                      <Loader2 className="w-12 h-12 mx-auto text-primary animate-spin" />
                      <p className="text-lg font-medium">Processing with AI Vision...</p>
                      <p className="text-sm text-muted-foreground">
                        Extracting vendor, dates, energy usage, and calculating emissions
                      </p>
                    </div>
                  ) : (
                    <>
                      <Upload className="w-10 h-10 mx-auto text-muted-foreground mb-4" />
                      <p className="text-lg font-medium mb-2">Drop invoice here or click to browse</p>
                      <p className="text-sm text-muted-foreground mb-4">
                        Supports JPG, PNG, WEBP, PDF, TXT (max 25MB)
                      </p>
                      <input
                        type="file"
                        id="single-upload"
                        className="hidden"
                        accept=".jpg,.jpeg,.png,.webp,.pdf,.txt"
                        onChange={handleFileSelect}
                        data-testid="file-input"
                      />
                      <Button asChild className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-full px-8">
                        <label htmlFor="single-upload" className="cursor-pointer" data-testid="upload-btn">
                          Select File
                        </label>
                      </Button>
                    </>
                  )}
                </div>
              </TabsContent>

              <TabsContent value="batch">
                <div
                  className={`upload-zone rounded-xl p-8 text-center transition-all ${dragOver ? 'dragover' : ''}`}
                  onDrop={handleDrop}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                >
                  <Files className="w-10 h-10 mx-auto text-muted-foreground mb-4" />
                  <p className="text-lg font-medium mb-2">Drop multiple invoices for batch processing</p>
                  <p className="text-sm text-muted-foreground mb-4">
                    Upload all invoices from a quarter at once (max 20 files)
                  </p>
                  <input
                    type="file"
                    id="batch-upload"
                    className="hidden"
                    accept=".jpg,.jpeg,.png,.webp,.pdf,.txt"
                    multiple
                    onChange={handleFileSelect}
                  />
                  <Button asChild variant="outline" className="rounded-full px-6">
                    <label htmlFor="batch-upload" className="cursor-pointer">
                      Add Files
                    </label>
                  </Button>
                </div>

                {/* Batch Files List */}
                {batchFiles.length > 0 && (
                  <div className="mt-6 space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">{batchFiles.length} files selected</span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setBatchFiles([])}
                        className="text-muted-foreground"
                      >
                        Clear all
                      </Button>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2 max-h-48 overflow-y-auto">
                      {batchFiles.map((file, index) => (
                        <div
                          key={index}
                          className="flex items-center justify-between p-2 rounded-lg bg-muted/50 text-sm"
                        >
                          <span className="truncate flex-1 mr-2">{file.name}</span>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => removeFromBatch(index)}
                            className="h-6 w-6 p-0"
                          >
                            <X className="w-3 h-3" />
                          </Button>
                        </div>
                      ))}
                    </div>
                    
                    {uploading && (
                      <div className="space-y-2">
                        <Progress value={uploadProgress} className="h-2" />
                        <p className="text-xs text-muted-foreground text-center">Processing invoices with AI...</p>
                      </div>
                    )}
                    
                    <Button
                      onClick={handleBatchUpload}
                      disabled={uploading || batchFiles.length === 0}
                      className="w-full bg-primary text-primary-foreground hover:bg-primary/90 rounded-full"
                      data-testid="batch-upload-btn"
                    >
                      {uploading ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Processing {batchFiles.length} files...
                        </>
                      ) : (
                        <>
                          <Zap className="w-4 h-4 mr-2" />
                          Process {batchFiles.length} Invoices
                        </>
                      )}
                    </Button>
                  </div>
                )}
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        {/* Batch Result */}
        {batchResult && (
          <Card className="bg-card border-border neon-border animate-fade-in" data-testid="batch-result">
            <CardHeader>
              <CardTitle className="font-['Outfit'] flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-primary" />
                Batch Processing Complete
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Summary Stats */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 rounded-lg bg-muted/50 text-center">
                  <p className="text-2xl font-bold text-primary">{batchResult.successful}</p>
                  <p className="text-xs text-muted-foreground">Successful</p>
                </div>
                <div className="p-4 rounded-lg bg-muted/50 text-center">
                  <p className="text-2xl font-bold text-destructive">{batchResult.failed}</p>
                  <p className="text-xs text-muted-foreground">Failed</p>
                </div>
                <div className="p-4 rounded-lg bg-primary/10 border border-primary/20 text-center">
                  <p className="text-2xl font-bold text-primary">{formatEmissions(batchResult.total_emissions)}</p>
                  <p className="text-xs text-muted-foreground">Total kg CO2e</p>
                </div>
                <div className="p-4 rounded-lg bg-muted/50 text-center">
                  <p className="text-2xl font-bold">{batchResult.emission_records?.length || 0}</p>
                  <p className="text-xs text-muted-foreground">Records Created</p>
                </div>
              </div>

              {/* Scope Breakdown */}
              <div className="grid grid-cols-3 gap-4">
                <div className="p-4 rounded-lg bg-orange-500/10 border border-orange-500/20">
                  <p className="text-xs text-orange-400 mb-1">Scope 1 (Direct)</p>
                  <p className="text-xl font-bold">{formatEmissions(batchResult.scope1_emissions)} kg</p>
                </div>
                <div className="p-4 rounded-lg bg-blue-500/10 border border-blue-500/20">
                  <p className="text-xs text-blue-400 mb-1">Scope 2 (Energy)</p>
                  <p className="text-xl font-bold">{formatEmissions(batchResult.scope2_emissions)} kg</p>
                </div>
                <div className="p-4 rounded-lg bg-amber-500/10 border border-amber-500/20">
                  <p className="text-xs text-amber-400 mb-1">Scope 3 (Value Chain)</p>
                  <p className="text-xl font-bold">{formatEmissions(batchResult.scope3_emissions)} kg</p>
                </div>
              </div>

              {/* Processed Invoices */}
              <div>
                <h4 className="font-medium mb-3">Processed Invoices</h4>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {batchResult.invoices?.map((inv, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-3 rounded-lg bg-muted/50"
                    >
                      <div className="flex items-center gap-3">
                        {inv.status === 'completed' ? (
                          <CheckCircle2 className="w-4 h-4 text-primary" />
                        ) : (
                          <AlertCircle className="w-4 h-4 text-chart-3" />
                        )}
                        <div>
                          <p className="text-sm font-medium truncate max-w-[200px]">{inv.file_name}</p>
                          <p className="text-xs text-muted-foreground">
                            {inv.vendor_name || 'Unknown vendor'} • {inv.document_type || 'unknown'}
                          </p>
                        </div>
                      </div>
                      <span className="text-sm font-medium text-primary">
                        {formatEmissions(inv.total_emissions)} kg CO2e
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Single Parse Result */}
        {parseResult && !batchResult && (
          <Card className="bg-card border-border neon-border animate-fade-in" data-testid="parse-result">
            <CardHeader>
              <CardTitle className="font-['Outfit'] flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-primary" />
                AI Extraction Results
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Extracted Data Grid */}
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                <div className="p-3 rounded-lg bg-muted/50">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                    <Building className="w-3 h-3" /> Vendor
                  </div>
                  <p className="font-medium truncate">{parseResult.extracted_data?.vendor_name || 'Unknown'}</p>
                </div>
                <div className="p-3 rounded-lg bg-muted/50">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                    <Calendar className="w-3 h-3" /> Date
                  </div>
                  <p className="font-medium">
                    {parseResult.extracted_data?.invoice_date
                      ? new Date(parseResult.extracted_data.invoice_date).toLocaleDateString()
                      : 'N/A'}
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-muted/50">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                    <MapPin className="w-3 h-3" /> Location
                  </div>
                  <p className="font-medium capitalize">{parseResult.extracted_data?.location || 'N/A'}</p>
                </div>
                <div className="p-3 rounded-lg bg-muted/50">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                    <DollarSign className="w-3 h-3" /> Amount
                  </div>
                  <p className="font-medium">
                    {parseResult.extracted_data?.total_amount
                      ? `${parseResult.extracted_data.currency || ''} ${parseResult.extracted_data.total_amount.toLocaleString()}`
                      : 'N/A'}
                  </p>
                </div>
                {parseResult.extracted_data?.billing_period && (
                  <div className="p-3 rounded-lg bg-muted/50">
                    <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                      <Calendar className="w-3 h-3" /> Billing Period
                    </div>
                    <p className="font-medium text-sm">{parseResult.extracted_data.billing_period}</p>
                  </div>
                )}
                {parseResult.extracted_data?.meter_number && (
                  <div className="p-3 rounded-lg bg-muted/50">
                    <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                      <Gauge className="w-3 h-3" /> Meter
                    </div>
                    <p className="font-medium">{parseResult.extracted_data.meter_number}</p>
                  </div>
                )}
                {parseResult.extracted_data?.tariff_type && (
                  <div className="p-3 rounded-lg bg-muted/50">
                    <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                      <Receipt className="w-3 h-3" /> Tariff
                    </div>
                    <p className="font-medium">{parseResult.extracted_data.tariff_type}</p>
                  </div>
                )}
                <div className="p-3 rounded-lg bg-primary/10 border border-primary/20">
                  <div className="flex items-center gap-2 text-xs text-primary mb-1">
                    <Cloud className="w-3 h-3" /> Total CO2e
                  </div>
                  <p className="font-bold text-primary text-lg">
                    {formatEmissions(parseResult.extracted_data?.total_emissions)} kg
                  </p>
                </div>
              </div>

              {/* Additional Info */}
              {(parseResult.extracted_data?.customer_name || parseResult.extracted_data?.customer_account_number) && (
                <div className="p-3 rounded-lg bg-muted/30 border border-border">
                  <p className="text-xs text-muted-foreground mb-1">Customer</p>
                  <p className="font-medium">
                    {parseResult.extracted_data.customer_name}
                    {parseResult.extracted_data.customer_account_number && 
                      ` (Account: ${parseResult.extracted_data.customer_account_number})`}
                  </p>
                </div>
              )}

              {/* Notes */}
              {parseResult.extracted_data?.notes && (
                <div className="p-3 rounded-lg bg-chart-3/10 border border-chart-3/20 text-sm">
                  <span className="text-chart-3 font-medium">Note: </span>
                  {parseResult.extracted_data.notes}
                </div>
              )}

              {/* Emission Records */}
              <div>
                <h4 className="font-medium mb-4 flex items-center gap-2">
                  <Zap className="w-4 h-4 text-primary" />
                  Extracted Emission Records
                </h4>
                <div className="space-y-3">
                  {parseResult.emission_records?.map((record) => (
                    <div
                      key={record.id}
                      className="flex items-center justify-between p-4 rounded-lg bg-muted/50 border border-border"
                    >
                      <div className="flex items-center gap-4">
                        <Cloud className="w-8 h-8 text-primary" />
                        <div>
                          <p className="font-medium capitalize">{record.energy_type}</p>
                          <p className="text-sm text-muted-foreground">
                            {record.quantity} {record.unit}
                            {record.description && ` • ${record.description}`}
                          </p>
                        </div>
                      </div>
                      <div className="text-right flex items-center gap-4">
                        <div>
                          <p className="text-lg font-bold font-['Outfit'] text-primary">
                            {formatEmissions(record.co2_emissions_kg)}
                          </p>
                          <p className="text-xs text-muted-foreground">kg CO2e</p>
                        </div>
                        <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getScopeColor(record.scope_type)}`}>
                          {record.scope_type}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Total Summary */}
              <div className="flex items-center justify-between p-4 rounded-xl bg-primary/10 border border-primary/20">
                <div>
                  <span className="font-medium">Total Emissions</span>
                  <p className="text-xs text-muted-foreground">
                    Using {parseResult.extracted_data?.emission_country_used || 'default'} emission factors
                  </p>
                </div>
                <span className="text-2xl font-bold font-['Outfit'] text-primary">
                  {formatEmissions(parseResult.extracted_data?.total_emissions || 0)} kg CO2e
                </span>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Invoice History */}
        <Card className="bg-card border-border" data-testid="invoice-history">
          <CardHeader>
            <CardTitle className="font-['Outfit']">Invoice History</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-3">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="h-16 bg-muted/50 rounded-lg animate-pulse" />
                ))}
              </div>
            ) : invoices.length > 0 ? (
              <div className="space-y-3">
                {invoices.map((invoice) => (
                  <div
                    key={invoice.id}
                    className="flex items-center justify-between p-4 rounded-lg bg-muted/50 hover:bg-muted/70 transition-colors"
                  >
                    <div className="flex items-center gap-4">
                      <FileText className="w-8 h-8 text-muted-foreground" />
                      <div>
                        <p className="font-medium truncate max-w-[300px]">{invoice.file_name}</p>
                        <p className="text-sm text-muted-foreground">
                          {new Date(invoice.uploaded_at).toLocaleString()}
                          {invoice.extracted_data?.vendor_name && ` • ${invoice.extracted_data.vendor_name}`}
                          {invoice.extracted_data?.document_type && ` • ${invoice.extracted_data.document_type}`}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      {invoice.extracted_data?.total_emissions !== undefined && (
                        <span className="text-sm font-medium text-primary">
                          {formatEmissions(invoice.extracted_data.total_emissions)} kg CO2e
                        </span>
                      )}
                      <span
                        className={`flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${
                          invoice.status === 'completed'
                            ? 'bg-primary/20 text-primary'
                            : invoice.status === 'partial'
                            ? 'bg-chart-3/20 text-chart-3'
                            : invoice.status === 'processing'
                            ? 'bg-secondary/20 text-secondary'
                            : 'bg-destructive/20 text-destructive'
                        }`}
                      >
                        {invoice.status === 'completed' ? (
                          <CheckCircle2 className="w-3 h-3" />
                        ) : invoice.status === 'processing' ? (
                          <Loader2 className="w-3 h-3 animate-spin" />
                        ) : (
                          <AlertCircle className="w-3 h-3" />
                        )}
                        {invoice.status}
                      </span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setParseResult({ 
                            invoice, 
                            extracted_data: invoice.extracted_data,
                            emission_records: [] 
                          });
                          setBatchResult(null);
                        }}
                        className="rounded-full"
                      >
                        <Eye className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeleteInvoice(invoice.id)}
                        className="rounded-full text-destructive hover:text-destructive"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 text-muted-foreground">
                <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No invoices uploaded yet</p>
                <p className="text-sm mt-1">Upload your first invoice to get started</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
