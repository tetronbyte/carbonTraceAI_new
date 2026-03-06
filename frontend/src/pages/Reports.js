import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { Layout } from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { FileBarChart, Download, Loader2, CheckCircle2, Eye, Trash2, Plus, X } from 'lucide-react';
import { toast } from 'sonner';

const FRAMEWORKS = [
  { value: 'ISSB', label: 'ISSB - International Sustainability Standards Board', description: 'Global sustainability disclosure standards for investors' },
  { value: 'TCFD', label: 'TCFD - Climate Financial Disclosures', description: 'Climate-related financial risk reporting' },
  { value: 'GRI', label: 'GRI - Global Reporting Initiative', description: 'Comprehensive ESG impact reporting' },
  { value: 'CBAM', label: 'CBAM - Carbon Border Adjustment', description: 'EU export carbon compliance' },
];

const REPORT_TYPES = [
  { value: 'Annual', label: 'Annual Report' },
  { value: 'Quarterly', label: 'Quarterly Report' },
];

const QUARTERS = [
  { value: 'Q1', label: 'Q1 (Jan-Mar)' },
  { value: 'Q2', label: 'Q2 (Apr-Jun)' },
  { value: 'Q3', label: 'Q3 (Jul-Sep)' },
  { value: 'Q4', label: 'Q4 (Oct-Dec)' },
];

export function ReportsPage() {
  const { organization } = useAuth();
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [previewReport, setPreviewReport] = useState(null);
  const [activeTab, setActiveTab] = useState('standard');
  
  // Standard report form
  const [formData, setFormData] = useState({
    orgName: organization?.name || '',
    reportPeriod: new Date().getFullYear().toString(),
    reportType: 'Annual',
    complianceStandard: 'ISSB',
    quarter: '',
  });
  
  // CBAM report form
  const [cbamData, setCbamData] = useState({
    orgName: organization?.name || '',
    reportPeriod: new Date().getFullYear().toString(),
    products: [{ name: '', batch_id: '', quantity: 0, unit: 'units', emissions: 0 }]
  });

  useEffect(() => {
    if (organization?.id) {
      fetchReports();
      setFormData((prev) => ({ ...prev, orgName: organization.name }));
      setCbamData((prev) => ({ ...prev, orgName: organization.name }));
    }
  }, [organization?.id]);

  const fetchReports = async () => {
    try {
      const response = await api.getReports(organization.id);
      setReports(response.data);
    } catch (error) {
      console.error('Error fetching reports:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateStandard = async () => {
    if (!formData.orgName || !formData.reportPeriod || !formData.complianceStandard) {
      toast.error('Please fill in all required fields');
      return;
    }

    setGenerating(true);
    
    toast.info(`Starting ${formData.complianceStandard} report generation...`, {
      duration: 3000,
      id: 'report-generation'
    });
    
    try {
      // Initiate async report generation - returns immediately with job_id
      const response = await api.generateReport({
        organization_id: organization.id,
        org_name: formData.orgName,
        report_period: formData.reportPeriod,
        report_type: formData.reportType,
        compliance_standard: formData.complianceStandard,
        quarter: formData.reportType === 'Quarterly' ? formData.quarter : null,
      });
      
      const { job_id, report_id } = response.data;
      
      toast.info(`AI is generating your ${formData.complianceStandard} report in background...`, {
        duration: 5000,
        id: 'report-generation'
      });
      
      // Poll task status
      let attempts = 0;
      const maxAttempts = 180; // 180 × 3 sec = 9 minutes (enough for complex reports with multiple AI calls)
      
      while (attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 3000)); // Wait 3 seconds
        
        const statusResponse = await api.getReportGenerationStatus(job_id);
        const jobStatus = statusResponse.data;
        
        // Log for debugging
        console.log(`Report attempt ${attempts}: status=${jobStatus.status}, progress=${jobStatus.progress}`);
        
        if (jobStatus.status === 'completed') {
          toast.dismiss('report-generation');
          toast.success(`${formData.complianceStandard} report generated successfully!`);
          
          // Fetch the completed report
          const reportResponse = await api.getReport(report_id);
          setPreviewReport(reportResponse.data);
          fetchReports();
          break;
        } else if (jobStatus.status === 'failed') {
          toast.dismiss('report-generation');
          toast.error(`Report generation failed: ${jobStatus.error || 'Unknown error'}`);
          break;
        } else if (jobStatus.status === 'processing' || jobStatus.status === 'queued') {
          // Show progress update every 10 attempts (30 seconds)
          if (attempts > 0 && attempts % 10 === 0) {
            const elapsed = Math.floor(attempts * 3 / 60);
            const progressMsg = jobStatus.status === 'queued'
              ? `Waiting to start report generation... (${elapsed} min elapsed)`
              : `AI generating report... ${jobStatus.progress || 0}% complete (${elapsed} min elapsed)`;
            toast.info(progressMsg, {
              duration: 5000,
              id: 'report-generation'
            });
          }
        }
        
        attempts++;
      }
      
      if (attempts >= maxAttempts) {
        toast.dismiss('report-generation');
        toast.warning('Report generation is taking longer than expected. Check Report History in a few minutes - it may still be processing.');
      }
      
      fetchReports();
    } catch (error) {
      toast.dismiss('report-generation');
      const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
      toast.error(`Failed to generate report: ${errorMsg}`);
    } finally {
      setGenerating(false);
    }
  };

  const handleGenerateCBAM = async () => {
    if (!cbamData.orgName || !cbamData.reportPeriod || cbamData.products.length === 0) {
      toast.error('Please fill in all required fields and add at least one product');
      return;
    }

    const validProducts = cbamData.products.filter(p => p.name && p.emissions > 0);
    if (validProducts.length === 0) {
      toast.error('Please add at least one product with emissions data');
      return;
    }

    setGenerating(true);
    
    // Show processing message with estimated time
    toast.info(`🤖 AI is generating your CBAM report... This typically takes 2-4 minutes. Please stay on this page!`, {
      duration: 10000,
      id: 'cbam-generation'
    });
    
    try {
      const response = await api.generateCBAMReport({
        organization_id: organization.id,
        org_name: cbamData.orgName,
        report_period: cbamData.reportPeriod,
        products: validProducts,
      });
      
      toast.dismiss('cbam-generation');
      toast.success('CBAM report generated successfully!');
      setPreviewReport(response.data);
      fetchReports();
    } catch (error) {
      toast.dismiss('cbam-generation');
      const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
      
      if (error.code === 'ECONNABORTED' || errorMsg.includes('timeout')) {
        toast.warning('CBAM report generation is taking longer than expected. Please check Report History - it may complete shortly.');
      } else {
        toast.error(`Failed to generate CBAM report: ${errorMsg}`);
      }
    } finally {
      setGenerating(false);
    }
  };

  const addProduct = () => {
    setCbamData(prev => ({
      ...prev,
      products: [...prev.products, { name: '', batch_id: '', quantity: 0, unit: 'units', emissions: 0 }]
    }));
  };

  const removeProduct = (index) => {
    setCbamData(prev => ({
      ...prev,
      products: prev.products.filter((_, i) => i !== index)
    }));
  };

  const updateProduct = (index, field, value) => {
    setCbamData(prev => ({
      ...prev,
      products: prev.products.map((p, i) => i === index ? { ...p, [field]: value } : p)
    }));
  };

  const handleDownload = async (reportId) => {
    const token = localStorage.getItem('token');
    const url = `${process.env.REACT_APP_BACKEND_URL}/api/reports/${reportId}/download`;
    
    try {
      const response = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (!response.ok) throw new Error('Download failed');
      
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = `esg_report.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      toast.error('Failed to download report');
    }
  };

  const handlePreview = async (reportId) => {
    try {
      const response = await api.getReportHtml(reportId);
      const newWindow = window.open('', '_blank');
      newWindow.document.write(response.data);
      newWindow.document.close();
    } catch (error) {
      toast.error('Failed to preview report');
    }
  };

  const handleDelete = async (reportId) => {
    if (!window.confirm('Delete this report?')) return;
    
    try {
      await api.deleteReport(reportId);
      toast.success('Report deleted');
      fetchReports();
      if (previewReport?.id === reportId) {
        setPreviewReport(null);
      }
    } catch (error) {
      toast.error('Error deleting report');
    }
  };

  const formatEmissions = (value) => {
    if (!value) return '0';
    if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
    return value.toFixed(0);
  };

  return (
    <Layout>
      <div className="space-y-8 animate-fade-in">
        {/* Header */}
        <div>
          <h1 className="text-3xl md:text-4xl font-bold font-['Outfit'] tracking-tight" data-testid="reports-title">
            ESG Report Generator
          </h1>
          <p className="text-muted-foreground mt-1">
            Generate AI-powered ESG compliance reports for ISSB, TCFD, GRI, and EU CBAM
          </p>
        </div>

        {/* Report Generator */}
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="font-['Outfit']">Generate New Report</CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="mb-6">
                <TabsTrigger value="standard">Standard ESG Report</TabsTrigger>
                <TabsTrigger value="cbam">CBAM Product Declaration</TabsTrigger>
              </TabsList>
              
              <TabsContent value="standard" className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="orgName">Organization Name *</Label>
                    <Input
                      id="orgName"
                      value={formData.orgName}
                      onChange={(e) => setFormData({ ...formData, orgName: e.target.value })}
                      placeholder="Your Company Name"
                      data-testid="org-name-input"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="reportPeriod">Report Period *</Label>
                    <Input
                      id="reportPeriod"
                      value={formData.reportPeriod}
                      onChange={(e) => setFormData({ ...formData, reportPeriod: e.target.value })}
                      placeholder="e.g., 2024"
                      data-testid="report-period-input"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="complianceStandard">Framework *</Label>
                    <Select
                      value={formData.complianceStandard}
                      onValueChange={(value) => setFormData({ ...formData, complianceStandard: value })}
                    >
                      <SelectTrigger data-testid="compliance-standard-select">
                        <SelectValue placeholder="Select framework" />
                      </SelectTrigger>
                      <SelectContent>
                        {FRAMEWORKS.map((fw) => (
                          <SelectItem key={fw.value} value={fw.value}>
                            <div>
                              <div className="font-medium">{fw.value}</div>
                              <div className="text-xs text-muted-foreground">{fw.description}</div>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="reportType">Report Type</Label>
                    <Select
                      value={formData.reportType}
                      onValueChange={(value) => setFormData({ ...formData, reportType: value })}
                    >
                      <SelectTrigger data-testid="report-type-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {REPORT_TYPES.map((rt) => (
                          <SelectItem key={rt.value} value={rt.value}>{rt.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {formData.reportType === 'Quarterly' && (
                    <div className="space-y-2">
                      <Label htmlFor="quarter">Quarter</Label>
                      <Select
                        value={formData.quarter}
                        onValueChange={(value) => setFormData({ ...formData, quarter: value })}
                      >
                        <SelectTrigger data-testid="quarter-select">
                          <SelectValue placeholder="Select quarter" />
                        </SelectTrigger>
                        <SelectContent>
                          {QUARTERS.map((q) => (
                            <SelectItem key={q.value} value={q.value}>{q.label}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  )}
                </div>

                {/* Framework Info */}
                <div className="p-4 rounded-lg bg-muted/50 border border-border">
                  <p className="text-sm font-medium mb-2">
                    {FRAMEWORKS.find(f => f.value === formData.complianceStandard)?.label}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {FRAMEWORKS.find(f => f.value === formData.complianceStandard)?.description}
                  </p>
                </div>

                <Button
                  onClick={handleGenerateStandard}
                  disabled={generating}
                  className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-full"
                  data-testid="generate-report-btn"
                >
                  {generating ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Generating with AI...
                    </>
                  ) : (
                    <>
                      <FileBarChart className="w-4 h-4 mr-2" />
                      Generate {formData.complianceStandard} Report
                    </>
                  )}
                </Button>
              </TabsContent>
              
              <TabsContent value="cbam" className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label>Organization Name *</Label>
                    <Input
                      value={cbamData.orgName}
                      onChange={(e) => setCbamData({ ...cbamData, orgName: e.target.value })}
                      placeholder="Your Company Name"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Report Period *</Label>
                    <Input
                      value={cbamData.reportPeriod}
                      onChange={(e) => setCbamData({ ...cbamData, reportPeriod: e.target.value })}
                      placeholder="e.g., 2024"
                    />
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <Label className="text-base">Product Emissions Declaration</Label>
                    <Button variant="outline" size="sm" onClick={addProduct} className="rounded-full">
                      <Plus className="w-4 h-4 mr-1" /> Add Product
                    </Button>
                  </div>
                  
                  {cbamData.products.map((product, index) => (
                    <div key={index} className="grid grid-cols-1 md:grid-cols-6 gap-4 p-4 rounded-lg bg-muted/50 border border-border">
                      <div className="md:col-span-2">
                        <Label className="text-xs">Product Name</Label>
                        <Input
                          value={product.name}
                          onChange={(e) => updateProduct(index, 'name', e.target.value)}
                          placeholder="e.g., Steel Coil"
                        />
                      </div>
                      <div>
                        <Label className="text-xs">Batch ID</Label>
                        <Input
                          value={product.batch_id}
                          onChange={(e) => updateProduct(index, 'batch_id', e.target.value)}
                          placeholder="SC-001"
                        />
                      </div>
                      <div>
                        <Label className="text-xs">Quantity</Label>
                        <Input
                          type="number"
                          value={product.quantity}
                          onChange={(e) => updateProduct(index, 'quantity', parseFloat(e.target.value) || 0)}
                        />
                      </div>
                      <div>
                        <Label className="text-xs">CO2e (kg)</Label>
                        <Input
                          type="number"
                          value={product.emissions}
                          onChange={(e) => updateProduct(index, 'emissions', parseFloat(e.target.value) || 0)}
                        />
                      </div>
                      <div className="flex items-end">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeProduct(index)}
                          className="text-destructive hover:text-destructive"
                        >
                          <X className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>

                <Button
                  onClick={handleGenerateCBAM}
                  disabled={generating}
                  className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-full"
                >
                  {generating ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Generating CBAM Report...
                    </>
                  ) : (
                    <>
                      <FileBarChart className="w-4 h-4 mr-2" />
                      Generate CBAM Declaration
                    </>
                  )}
                </Button>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        {/* Latest Generated Report */}
        {previewReport && (
          <Card className="bg-card border-border neon-border animate-fade-in" data-testid="preview-report">
            <CardHeader>
              <CardTitle className="font-['Outfit'] flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-primary" />
                Report Generated Successfully
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="p-4 rounded-lg bg-muted/50">
                  <p className="text-xs text-muted-foreground mb-1">Framework</p>
                  <p className="font-medium">{previewReport.compliance_standard}</p>
                </div>
                <div className="p-4 rounded-lg bg-muted/50">
                  <p className="text-xs text-muted-foreground mb-1">Period</p>
                  <p className="font-medium">{previewReport.report_period}</p>
                </div>
                <div className="p-4 rounded-lg bg-muted/50">
                  <p className="text-xs text-muted-foreground mb-1">Total Emissions</p>
                  <p className="font-medium">{formatEmissions(previewReport.total_emissions)} kg CO2e</p>
                </div>
                <div className="p-4 rounded-lg bg-muted/50">
                  <p className="text-xs text-muted-foreground mb-1">Status</p>
                  <p className="font-medium text-primary">{previewReport.status}</p>
                </div>
              </div>
              <div className="flex gap-3">
                <Button
                  onClick={() => handlePreview(previewReport.id)}
                  variant="outline"
                  className="rounded-full"
                  data-testid="preview-btn"
                >
                  <Eye className="w-4 h-4 mr-2" />
                  Preview
                </Button>
                <Button
                  onClick={() => handleDownload(previewReport.id)}
                  className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-full"
                  data-testid="download-btn"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Download PDF
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Report History */}
        <Card className="bg-card border-border" data-testid="report-history">
          <CardHeader>
            <CardTitle className="font-['Outfit']">Report History</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-3">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="h-16 bg-muted/50 rounded-lg animate-pulse" />
                ))}
              </div>
            ) : reports.length > 0 ? (
              <div className="space-y-3">
                {reports.map((report) => (
                  <div
                    key={report.id}
                    className="flex items-center justify-between p-4 rounded-lg bg-muted/50 hover:bg-muted/70 transition-colors"
                  >
                    <div className="flex items-center gap-4">
                      <FileBarChart className="w-8 h-8 text-muted-foreground" />
                      <div>
                        <p className="font-medium">
                          {report.compliance_standard} - {report.report_period}
                          {report.quarter && ` (${report.quarter})`}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          {new Date(report.created_at).toLocaleString()} • {formatEmissions(report.total_emissions)} kg CO2e
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-medium ${
                          report.status === 'completed'
                            ? 'bg-primary/20 text-primary'
                            : 'bg-chart-3/20 text-chart-3'
                        }`}
                      >
                        {report.status}
                      </span>
                      {report.status === 'completed' && (
                        <>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handlePreview(report.id)}
                            className="rounded-full"
                          >
                            <Eye className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDownload(report.id)}
                            className="rounded-full"
                          >
                            <Download className="w-4 h-4" />
                          </Button>
                        </>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(report.id)}
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
                <FileBarChart className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No reports generated yet</p>
                <p className="text-sm mt-1">Generate your first ESG report above</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
