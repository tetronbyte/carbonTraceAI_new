import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { Layout } from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Textarea } from '../components/ui/textarea';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Progress } from '../components/ui/progress';
import { Shield, AlertTriangle, CheckCircle2, Loader2, Flag, Lightbulb } from 'lucide-react';
import { toast } from 'sonner';

export function GreenwashingPage() {
  const { organization } = useAuth();
  const [analyses, setAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [documentText, setDocumentText] = useState('');
  const [documentName, setDocumentName] = useState('');
  const [result, setResult] = useState(null);

  useEffect(() => {
    if (organization?.id) {
      fetchAnalyses();
    }
  }, [organization?.id]);

  const fetchAnalyses = async () => {
    try {
      const response = await api.getGreenwashingAnalyses(organization.id);
      setAnalyses(response.data);
    } catch (error) {
      console.error('Error fetching analyses:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async () => {
    if (!documentText || documentText.length < 50) {
      toast.error('Please enter at least 50 characters of text');
      return;
    }

    if (!documentName) {
      toast.error('Please enter a document name');
      return;
    }

    setAnalyzing(true);
    try {
      const response = await api.analyzeGreenwashing(
        organization.id,
        documentText,
        documentName,
        'sustainability_report',
        false
      );
      setResult(response.data);
      toast.success('Analysis complete!');
      fetchAnalyses();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Analysis failed');
    } finally {
      setAnalyzing(false);
    }
  };

  const getRiskColor = (level) => {
    switch (level) {
      case 'low':
        return 'text-primary bg-primary/20';
      case 'medium':
        return 'text-chart-3 bg-chart-3/20';
      case 'high':
        return 'text-destructive bg-destructive/20';
      default:
        return 'text-muted-foreground bg-muted';
    }
  };

  const getScoreColor = (score) => {
    if (score >= 70) return 'text-primary';
    if (score >= 40) return 'text-chart-3';
    return 'text-destructive';
  };

  return (
    <Layout>
      <div className="space-y-8 animate-fade-in">
        {/* Header */}
        <div>
          <h1 className="text-3xl md:text-4xl font-bold font-['Outfit'] tracking-tight" data-testid="greenwashing-title">
            Greenwashing Detector
          </h1>
          <p className="text-muted-foreground mt-1">
            Analyze sustainability documents for misleading environmental claims
          </p>
        </div>

        {/* Input Section */}
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="font-['Outfit']">Analyze Document</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="documentName">Document Name</Label>
              <Input
                id="documentName"
                placeholder="e.g., 2024 Sustainability Report"
                value={documentName}
                onChange={(e) => setDocumentName(e.target.value)}
                data-testid="document-name-input"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="documentText">Document Text</Label>
              <Textarea
                id="documentText"
                placeholder="Paste your sustainability report, press release, or marketing material here..."
                value={documentText}
                onChange={(e) => setDocumentText(e.target.value)}
                className="min-h-[200px] resize-y"
                data-testid="document-text-input"
              />
              <p className="text-xs text-muted-foreground">
                {documentText.length} characters (minimum 50 required)
              </p>
            </div>
            <Button
              onClick={handleAnalyze}
              disabled={analyzing || documentText.length < 50}
              className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-full"
              data-testid="analyze-btn"
            >
              {analyzing ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Shield className="w-4 h-4 mr-2" />
                  Analyze Document
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {/* Analysis Result */}
        {result && (
          <Card className="bg-card border-border animate-fade-in" data-testid="analysis-result">
            <CardHeader>
              <CardTitle className="font-['Outfit'] flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <Shield className="w-5 h-5" />
                  Analysis Results: {result.document_name}
                </span>
                <span className={`px-4 py-2 rounded-full text-sm font-medium ${getRiskColor(result.risk_level)}`}>
                  {result.risk_level.toUpperCase()} RISK
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-8">
              {/* Credibility Score */}
              <div className="flex items-center gap-8">
                <div className="relative w-32 h-32">
                  <svg className="w-32 h-32 progress-ring" viewBox="0 0 120 120">
                    <circle
                      className="text-muted"
                      strokeWidth="12"
                      stroke="currentColor"
                      fill="transparent"
                      r="52"
                      cx="60"
                      cy="60"
                    />
                    <circle
                      className={`progress-ring-circle ${getScoreColor(result.credibility_score)}`}
                      strokeWidth="12"
                      stroke="currentColor"
                      fill="transparent"
                      r="52"
                      cx="60"
                      cy="60"
                      strokeDasharray={`${(result.credibility_score / 100) * 327} 327`}
                      strokeLinecap="round"
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className={`text-3xl font-bold font-['Outfit'] ${getScoreColor(result.credibility_score)}`}>
                      {Math.round(result.credibility_score)}
                    </span>
                  </div>
                </div>
                <div className="flex-1 space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Evidence Score</span>
                      <span>{Math.round(result.evidence_score)}%</span>
                    </div>
                    <Progress value={result.evidence_score} className="h-2" />
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Specificity Score</span>
                      <span>{Math.round(result.specificity_score)}%</span>
                    </div>
                    <Progress value={result.specificity_score} className="h-2" />
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Transparency Score</span>
                      <span>{Math.round(result.transparency_score)}%</span>
                    </div>
                    <Progress value={result.transparency_score} className="h-2" />
                  </div>
                </div>
              </div>

              {/* Flags */}
              {result.flags && result.flags.length > 0 && (
                <div>
                  <h4 className="font-medium flex items-center gap-2 mb-4">
                    <Flag className="w-4 h-4 text-destructive" />
                    Flagged Issues ({result.flags.length})
                  </h4>
                  <div className="space-y-3">
                    {result.flags.map((flag, index) => (
                      <div
                        key={index}
                        className="p-4 rounded-lg bg-destructive/5 border border-destructive/20"
                      >
                        <div className="flex items-start gap-3">
                          <AlertTriangle className={`w-5 h-5 mt-0.5 ${
                            flag.severity === 'high' ? 'text-destructive' : 'text-chart-3'
                          }`} />
                          <div>
                            <p className="font-medium capitalize">{flag.type.replace(/_/g, ' ')}</p>
                            <p className="text-sm text-muted-foreground mt-1">
                              Phrase: "{flag.phrase}"
                            </p>
                            <p className="text-sm mt-2">{flag.recommendation}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recommendations */}
              {result.recommendations && result.recommendations.length > 0 && (
                <div>
                  <h4 className="font-medium flex items-center gap-2 mb-4">
                    <Lightbulb className="w-4 h-4 text-primary" />
                    Recommendations
                  </h4>
                  <div className="space-y-2">
                    {result.recommendations.map((rec, index) => (
                      <div
                        key={index}
                        className="flex items-start gap-3 p-3 rounded-lg bg-primary/5"
                      >
                        <CheckCircle2 className="w-4 h-4 text-primary mt-0.5" />
                        <p className="text-sm">{rec}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Analysis History */}
        <Card className="bg-card border-border" data-testid="analysis-history">
          <CardHeader>
            <CardTitle className="font-['Outfit']">Analysis History</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-3">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="h-16 bg-muted/50 rounded-lg animate-pulse" />
                ))}
              </div>
            ) : analyses.length > 0 ? (
              <div className="space-y-3">
                {analyses.map((analysis) => (
                  <div
                    key={analysis.id}
                    className="flex items-center justify-between p-4 rounded-lg bg-muted/50 hover:bg-muted/70 transition-colors cursor-pointer"
                    onClick={() => setResult(analysis)}
                  >
                    <div className="flex items-center gap-4">
                      <Shield className={`w-8 h-8 ${
                        analysis.risk_level === 'low'
                          ? 'text-primary'
                          : analysis.risk_level === 'medium'
                          ? 'text-chart-3'
                          : 'text-destructive'
                      }`} />
                      <div>
                        <p className="font-medium">{analysis.document_name}</p>
                        <p className="text-sm text-muted-foreground">
                          {new Date(analysis.created_at).toLocaleString()}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className={`text-lg font-bold font-['Outfit'] ${getScoreColor(analysis.credibility_score)}`}>
                        {Math.round(analysis.credibility_score)}
                      </span>
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${getRiskColor(analysis.risk_level)}`}>
                        {analysis.risk_level}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 text-muted-foreground">
                <Shield className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No analyses yet</p>
                <p className="text-sm mt-1">Analyze your first document above</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
