import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { Layout } from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Checkbox } from '../components/ui/checkbox';
import { Link2, CheckCircle2, Cloud, Loader2, ExternalLink, QrCode } from 'lucide-react';
import { toast } from 'sonner';

export function LedgerPage() {
  const { organization } = useAuth();
  const [records, setRecords] = useState([]);
  const [ledgerEntries, setLedgerEntries] = useState([]);
  const [selectedRecords, setSelectedRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(false);
  const [latestVerification, setLatestVerification] = useState(null);

  useEffect(() => {
    if (organization?.id) {
      fetchData();
    }
  }, [organization?.id]);

  const fetchData = async () => {
    try {
      const [recordsRes, ledgerRes] = await Promise.all([
        api.getEmissionRecords(organization.id),
        api.getLedgerEntries(organization.id)
      ]);
      setRecords(recordsRes.data);
      setLedgerEntries(ledgerRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectRecord = (recordId) => {
    setSelectedRecords((prev) =>
      prev.includes(recordId)
        ? prev.filter((id) => id !== recordId)
        : [...prev, recordId]
    );
  };

  const handleSelectAll = () => {
    const unverifiedIds = records.filter((r) => !r.is_verified).map((r) => r.id);
    if (selectedRecords.length === unverifiedIds.length) {
      setSelectedRecords([]);
    } else {
      setSelectedRecords(unverifiedIds);
    }
  };

  const handleVerify = async () => {
    if (selectedRecords.length === 0) {
      toast.error('Please select records to verify');
      return;
    }

    setVerifying(true);
    try {
      const response = await api.recordOnBlockchain(organization.id, selectedRecords);
      setLatestVerification(response.data);
      toast.success('Records verified on blockchain!');
      setSelectedRecords([]);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Verification failed');
    } finally {
      setVerifying(false);
    }
  };

  const formatEmissions = (value) => {
    if (value >= 1000) return `${(value / 1000).toFixed(2)}K`;
    return value.toFixed(2);
  };

  const unverifiedRecords = records.filter((r) => !r.is_verified);

  return (
    <Layout>
      <div className="space-y-8 animate-fade-in">
        {/* Header */}
        <div>
          <h1 className="text-3xl md:text-4xl font-bold font-['Outfit'] tracking-tight" data-testid="ledger-title">
            Carbon Ledger
          </h1>
          <p className="text-muted-foreground mt-1">
            Verify emission records on blockchain for tamper-proof reporting
          </p>
        </div>

        {/* Verification Result */}
        {latestVerification && (
          <Card className="bg-card border-border neon-border animate-fade-in" data-testid="verification-result">
            <CardHeader>
              <CardTitle className="font-['Outfit'] flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-primary" />
                Blockchain Verification Complete
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">Transaction Hash</p>
                    <p className="font-mono text-sm break-all bg-muted/50 p-3 rounded-lg">
                      {latestVerification.transaction_hash}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">Data Hash</p>
                    <p className="font-mono text-sm break-all bg-muted/50 p-3 rounded-lg">
                      {latestVerification.data_hash}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">Merkle Root</p>
                    <p className="font-mono text-sm break-all bg-muted/50 p-3 rounded-lg">
                      {latestVerification.merkle_root}
                    </p>
                  </div>
                  <div className="flex items-center gap-4">
                    <div>
                      <p className="text-xs text-muted-foreground mb-1">Block Number</p>
                      <p className="font-medium">{latestVerification.block_number}</p>
                    </div>
                    <a
                      href={latestVerification.verification_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 text-primary hover:underline"
                    >
                      View on PolygonScan
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  </div>
                </div>
                <div className="flex items-center justify-center p-8 bg-white rounded-xl">
                  <div className="text-center">
                    <QrCode className="w-32 h-32 mx-auto text-black" />
                    <p className="text-xs text-black mt-4">Scan to verify on blockchain</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Unverified Records */}
        <Card className="bg-card border-border" data-testid="unverified-records">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="font-['Outfit']">
              Emission Records ({unverifiedRecords.length} unverified)
            </CardTitle>
            <div className="flex items-center gap-4">
              {unverifiedRecords.length > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleSelectAll}
                  className="rounded-full"
                  data-testid="select-all-btn"
                >
                  {selectedRecords.length === unverifiedRecords.length ? 'Deselect All' : 'Select All'}
                </Button>
              )}
              <Button
                onClick={handleVerify}
                disabled={selectedRecords.length === 0 || verifying}
                className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-full"
                data-testid="verify-btn"
              >
                {verifying ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Verifying...
                  </>
                ) : (
                  <>
                    <Link2 className="w-4 h-4 mr-2" />
                    Verify on Blockchain ({selectedRecords.length})
                  </>
                )}
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-3">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="h-16 bg-muted/50 rounded-lg animate-pulse" />
                ))}
              </div>
            ) : records.length > 0 ? (
              <div className="space-y-3">
                {records.map((record) => (
                  <div
                    key={record.id}
                    className={`flex items-center gap-4 p-4 rounded-lg transition-colors ${
                      record.is_verified
                        ? 'bg-primary/5 border border-primary/20'
                        : 'bg-muted/50 hover:bg-muted/70'
                    }`}
                  >
                    {!record.is_verified && (
                      <Checkbox
                        checked={selectedRecords.includes(record.id)}
                        onCheckedChange={() => handleSelectRecord(record.id)}
                        data-testid={`record-checkbox-${record.id}`}
                      />
                    )}
                    <Cloud className={`w-8 h-8 ${record.is_verified ? 'text-primary' : 'text-muted-foreground'}`} />
                    <div className="flex-1">
                      <p className="font-medium capitalize">{record.energy_type}</p>
                      <p className="text-sm text-muted-foreground">
                        {record.quantity} {record.unit} • {record.vendor_name || 'Unknown vendor'}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-bold font-['Outfit']">
                        {formatEmissions(record.co2_emissions_kg)} kg CO2e
                      </p>
                      <p className="text-xs text-muted-foreground">{record.scope_type}</p>
                    </div>
                    {record.is_verified ? (
                      <span className="flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium bg-primary/20 text-primary">
                        <CheckCircle2 className="w-3 h-3" />
                        Verified
                      </span>
                    ) : (
                      <span className="px-3 py-1 rounded-full text-xs font-medium bg-muted text-muted-foreground">
                        Pending
                      </span>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 text-muted-foreground">
                <Cloud className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No emission records yet</p>
                <p className="text-sm mt-1">Upload invoices to create emission records</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Ledger History */}
        <Card className="bg-card border-border" data-testid="ledger-history">
          <CardHeader>
            <CardTitle className="font-['Outfit']">Verification History</CardTitle>
          </CardHeader>
          <CardContent>
            {ledgerEntries.length > 0 ? (
              <div className="space-y-3">
                {ledgerEntries.map((entry) => (
                  <div
                    key={entry.id}
                    className="flex items-center justify-between p-4 rounded-lg bg-muted/50"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
                        <Link2 className="w-5 h-5 text-primary" />
                      </div>
                      <div>
                        <p className="font-mono text-sm truncate max-w-[300px]">
                          {entry.transaction_hash}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Block #{entry.block_number} • {new Date(entry.created_at).toLocaleString()}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="text-sm text-muted-foreground">
                        {entry.emission_record_ids?.length || 0} records
                      </span>
                      <a
                        href={entry.verification_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-2 hover:bg-muted rounded-lg transition-colors"
                      >
                        <ExternalLink className="w-4 h-4 text-primary" />
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 text-muted-foreground">
                <Link2 className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No blockchain verifications yet</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
