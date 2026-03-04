import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { Layout } from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { FileBarChart, Download, Loader2, CheckCircle2, Eye } from 'lucide-react';
import { toast } from 'sonner';

const COMPLIANCE_STANDARDS = [
  { value: 'GRI', label: 'GRI - Global Reporting Initiative' },
  { value: 'TCFD', label: 'TCFD - Task Force on Climate-related Financial Disclosures' },
  { value: 'CDP', label: 'CDP - Carbon Disclosure Project' },
  { value: 'BRSR', label: 'BRSR - Business Responsibility and Sustainability Reporting' },
  { value: 'ISO14064', label: 'ISO 14064 - Greenhouse Gas Standard' },
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
  
  const [formData, setFormData] = useState({
    orgName: organization?.name || '',
    reportPeriod: new Date().getFullYear().toString(),
    reportType: 'Annual',
    complianceStandard: 'GRI',
    quarter: '',
  });

  useEffect(() => {
    if (organization?.id) {
      fetchReports();
      setFormData((prev) => ({ ...prev, orgName: organization.name }));
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

  const handleGenerate = async () => {
    if (!formData.orgName || !formData.reportPeriod || !formData.complianceStandard) {
      toast.error('Please fill in all required fields');
      return;
    }

    setGenerating(true);
    try {
      const response = await api.generateReport({
        organization_id: organization.id,
        org_name: formData.orgName,
        report_period: formData.reportPeriod,
        report_type: formData.reportType,
        compliance_standard: formData.complianceStandard,
        quarter: formData.quarter || null,
      });
      
      toast.success('Report generated successfully!');
      setPreviewReport(response.data);
      fetchReports();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to generate report');
    } finally {
      setGenerating(false);
    }
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
            ESG Reports
          </h1>
          <p className="text-muted-foreground mt-1">
            Generate ESG compliance reports for various standards
          </p>
        </div>

        {/* Report Generator */}
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="font-['Outfit']">Generate New Report</CardTitle>
          </CardHeader>
          <CardContent>
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
                <Label htmlFor="complianceStandard">Compliance Standard *</Label>
                <Select
                  value={formData.complianceStandard}
                  onValueChange={(value) => setFormData({ ...formData, complianceStandard: value })}
                >
                  <SelectTrigger data-testid="compliance-standard-select">
                    <SelectValue placeholder="Select standard" />
                  </SelectTrigger>
                  <SelectContent>
                    {COMPLIANCE_STANDARDS.map((standard) => (
                      <SelectItem key={standard.value} value={standard.value}>
                        {standard.label}
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
                    <SelectItem value="Annual">Annual Report</SelectItem>
                    <SelectItem value="Quarterly">Quarterly Report</SelectItem>
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
                        <SelectItem key={q.value} value={q.value}>
                          {q.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
            </div>

            <Button
              onClick={handleGenerate}
              disabled={generating}
              className="mt-6 bg-primary text-primary-foreground hover:bg-primary/90 rounded-full"
              data-testid="generate-report-btn"
            >
              {generating ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <FileBarChart className="w-4 h-4 mr-2" />
                  Generate Report
                </>
              )}
            </Button>
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
                  <p className="text-xs text-muted-foreground mb-1">Standard</p>
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
