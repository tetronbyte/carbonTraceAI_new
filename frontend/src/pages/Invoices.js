import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { Layout } from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Label } from '../components/ui/label';
import { 
  Upload, FileText, CheckCircle2, AlertCircle, Loader2, Cloud, 
  Trash2, Eye, MapPin, Calendar, DollarSign, Zap
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

export function InvoicesPage() {
  const { organization } = useAuth();
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [parseResult, setParseResult] = useState(null);
  const [selectedCountry, setSelectedCountry] = useState('default');
  const [selectedInvoice, setSelectedInvoice] = useState(null);

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

  const handleUpload = async (file) => {
    if (!file) return;

    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp', 'application/pdf', 'text/plain'];
    const allowedExtensions = ['jpg', 'jpeg', 'png', 'webp', 'pdf', 'txt'];
    const ext = file.name.split('.').pop().toLowerCase();
    
    if (!allowedTypes.includes(file.type) && !allowedExtensions.includes(ext)) {
      toast.error('Unsupported file type. Please upload JPG, PNG, WEBP, PDF, or TXT files.');
      return;
    }

    if (file.size > 25 * 1024 * 1024) {
      toast.error('File size exceeds 25MB limit.');
      return;
    }

    setUploading(true);
    setParseResult(null);

    try {
      const response = await api.uploadInvoice(file, organization.id, selectedCountry);
      setParseResult(response.data);
      
      if (response.data.extracted_data?.parse_error) {
        toast.warning('Invoice parsed with some issues. Please review the data.');
      } else {
        toast.success('Invoice parsed successfully!');
      }
      
      fetchInvoices();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error parsing invoice');
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    handleUpload(file);
  }, [organization?.id, selectedCountry]);

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    handleUpload(file);
  };

  const handleDeleteInvoice = async (invoiceId) => {
    if (!window.confirm('Delete this invoice and its emission records?')) return;
    
    try {
      await api.deleteInvoice(invoiceId);
      toast.success('Invoice deleted');
      fetchInvoices();
      if (selectedInvoice?.id === invoiceId) {
        setSelectedInvoice(null);
      }
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
            Upload energy invoices to automatically extract carbon emission data using AI
          </p>
        </div>

        {/* Upload Zone */}
        <Card className="bg-card border-border">
          <CardContent className="p-8">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
              <div className="md:col-span-1">
                <Label htmlFor="country" className="text-sm text-muted-foreground">
                  Country (for emission factors)
                </Label>
                <Select value={selectedCountry} onValueChange={setSelectedCountry}>
                  <SelectTrigger id="country" className="mt-2" data-testid="country-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {COUNTRIES.map((c) => (
                      <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <div
              className={`upload-zone rounded-xl p-12 text-center transition-all ${
                dragOver ? 'dragover' : ''
              }`}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              data-testid="upload-zone"
            >
              {uploading ? (
                <div className="space-y-4">
                  <Loader2 className="w-12 h-12 mx-auto text-primary animate-spin" />
                  <p className="text-lg font-medium">Processing invoice with AI...</p>
                  <p className="text-sm text-muted-foreground">
                    Extracting data and calculating emissions using Vision Language Model
                  </p>
                </div>
              ) : (
                <>
                  <Upload className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                  <p className="text-lg font-medium mb-2">
                    Drop your invoice here or click to browse
                  </p>
                  <p className="text-sm text-muted-foreground mb-2">
                    Supports JPG, PNG, WEBP, PDF, TXT files up to 25MB
                  </p>
                  <p className="text-xs text-muted-foreground mb-6">
                    Works with printed invoices, scans, and handwritten receipts
                  </p>
                  <input
                    type="file"
                    id="file-upload"
                    className="hidden"
                    accept=".jpg,.jpeg,.png,.webp,.pdf,.txt"
                    onChange={handleFileSelect}
                    data-testid="file-input"
                  />
                  <Button
                    asChild
                    className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-full px-8"
                  >
                    <label htmlFor="file-upload" className="cursor-pointer" data-testid="upload-btn">
                      Select File
                    </label>
                  </Button>
                </>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Parse Result */}
        {parseResult && (
          <Card className="bg-card border-border neon-border animate-fade-in" data-testid="parse-result">
            <CardHeader>
              <CardTitle className="font-['Outfit'] flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-primary" />
                AI Extraction Results
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Extracted Data Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                <div className="p-4 rounded-lg bg-muted/50">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                    <FileText className="w-3 h-3" /> Vendor
                  </div>
                  <p className="font-medium truncate">
                    {parseResult.extracted_data?.vendor_name || 'Unknown'}
                  </p>
                </div>
                <div className="p-4 rounded-lg bg-muted/50">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                    <Calendar className="w-3 h-3" /> Date
                  </div>
                  <p className="font-medium">
                    {parseResult.extracted_data?.invoice_date
                      ? new Date(parseResult.extracted_data.invoice_date).toLocaleDateString()
                      : 'N/A'}
                  </p>
                </div>
                <div className="p-4 rounded-lg bg-muted/50">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                    <MapPin className="w-3 h-3" /> Location
                  </div>
                  <p className="font-medium capitalize">
                    {parseResult.extracted_data?.location || 'N/A'}
                  </p>
                </div>
                <div className="p-4 rounded-lg bg-muted/50">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                    <DollarSign className="w-3 h-3" /> Amount
                  </div>
                  <p className="font-medium">
                    {parseResult.extracted_data?.total_amount
                      ? `${parseResult.extracted_data.currency || ''} ${parseResult.extracted_data.total_amount.toLocaleString()}`
                      : 'N/A'}
                  </p>
                </div>
                <div className="p-4 rounded-lg bg-muted/50">
                  <p className="text-xs text-muted-foreground mb-1">Invoice #</p>
                  <p className="font-medium truncate">
                    {parseResult.extracted_data?.invoice_number || 'N/A'}
                  </p>
                </div>
                <div className="p-4 rounded-lg bg-primary/10 border border-primary/20">
                  <div className="flex items-center gap-2 text-xs text-primary mb-1">
                    <Cloud className="w-3 h-3" /> Total CO2e
                  </div>
                  <p className="font-bold text-primary text-lg">
                    {formatEmissions(parseResult.extracted_data?.total_emissions)} kg
                  </p>
                </div>
              </div>

              {/* Notes/Errors */}
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
                <span className="font-medium">Total Emissions (CBAM-Ready)</span>
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
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      {invoice.extracted_data?.total_emissions && (
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
                        onClick={() => setParseResult({ 
                          invoice, 
                          extracted_data: invoice.extracted_data,
                          emission_records: [] 
                        })}
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
