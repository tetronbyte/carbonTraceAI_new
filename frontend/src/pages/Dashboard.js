import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { Layout } from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Skeleton } from '../components/ui/skeleton';
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import {
  Cloud, FileText, CheckCircle2, FileBarChart, TrendingUp, TrendingDown
} from 'lucide-react';

const COLORS = ['hsl(145, 100%, 45%)', 'hsl(217, 100%, 58%)', 'hsl(37, 91%, 65%)'];

export function DashboardPage() {
  const { organization } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (organization?.id) {
      fetchDashboard();
    }
  }, [organization?.id]);

  const fetchDashboard = async () => {
    try {
      const response = await api.getDashboard(organization.id);
      setData(response.data);
    } catch (error) {
      console.error('Dashboard error:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatEmissions = (value) => {
    if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
    if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
    return value.toFixed(0);
  };

  if (loading) {
    return (
      <Layout>
        <div className="space-y-6">
          <Skeleton className="h-12 w-64" />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-32" />
            ))}
          </div>
        </div>
      </Layout>
    );
  }

  const pieData = data?.emissions_by_scope?.filter(s => s.emissions > 0) || [];

  return (
    <Layout>
      <div className="space-y-8 animate-fade-in">
        {/* Header */}
        <div>
          <h1 className="text-3xl md:text-4xl font-bold font-['Outfit'] tracking-tight" data-testid="dashboard-title">
            Dashboard
          </h1>
          <p className="text-muted-foreground mt-1">
            Overview of your carbon footprint and ESG performance
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card className="bg-card border-border card-hover" data-testid="stat-total-emissions">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <Cloud className="w-8 h-8 text-primary" />
                <span className="text-xs text-muted-foreground">Total</span>
              </div>
              <div className="mt-4">
                <p className="text-3xl font-bold font-['Outfit']">
                  {formatEmissions(data?.stats?.total_emissions || 0)}
                </p>
                <p className="text-sm text-muted-foreground">kg CO2e</p>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-card border-border card-hover" data-testid="stat-invoices">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <FileText className="w-8 h-8 text-secondary" />
                <span className="text-xs text-muted-foreground">Invoices</span>
              </div>
              <div className="mt-4">
                <p className="text-3xl font-bold font-['Outfit']">
                  {data?.stats?.invoice_count || 0}
                </p>
                <p className="text-sm text-muted-foreground">processed</p>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-card border-border card-hover" data-testid="stat-verified">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <CheckCircle2 className="w-8 h-8 text-chart-3" />
                <span className="text-xs text-muted-foreground">Verified</span>
              </div>
              <div className="mt-4">
                <p className="text-3xl font-bold font-['Outfit']">
                  {data?.stats?.verified_records || 0}
                </p>
                <p className="text-sm text-muted-foreground">records</p>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-card border-border card-hover" data-testid="stat-reports">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <FileBarChart className="w-8 h-8 text-chart-5" />
                <span className="text-xs text-muted-foreground">Reports</span>
              </div>
              <div className="mt-4">
                <p className="text-3xl font-bold font-['Outfit']">
                  {data?.stats?.report_count || 0}
                </p>
                <p className="text-sm text-muted-foreground">generated</p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Scope Breakdown */}
          <Card className="bg-card border-border" data-testid="chart-scope-breakdown">
            <CardHeader>
              <CardTitle className="font-['Outfit']">Emissions by Scope</CardTitle>
            </CardHeader>
            <CardContent>
              {pieData.length > 0 ? (
                <div className="flex items-center gap-8">
                  <ResponsiveContainer width={200} height={200}>
                    <PieChart>
                      <Pie
                        data={pieData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={90}
                        paddingAngle={2}
                        dataKey="emissions"
                      >
                        {pieData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{
                          background: 'hsl(0, 0%, 7%)',
                          border: '1px solid hsl(240, 4%, 16%)',
                          borderRadius: '8px'
                        }}
                        formatter={(value) => [`${formatEmissions(value)} kg CO2e`, '']}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="space-y-3">
                    {pieData.map((entry, index) => (
                      <div key={entry.scope} className="flex items-center gap-3">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: COLORS[index] }}
                        />
                        <div>
                          <p className="text-sm font-medium">{entry.scope}</p>
                          <p className="text-xs text-muted-foreground">
                            {formatEmissions(entry.emissions)} kg CO2e
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="h-[200px] flex items-center justify-center text-muted-foreground">
                  No emission data yet
                </div>
              )}
            </CardContent>
          </Card>

          {/* Timeline */}
          <Card className="bg-card border-border" data-testid="chart-timeline">
            <CardHeader>
              <CardTitle className="font-['Outfit']">Emissions Timeline</CardTitle>
            </CardHeader>
            <CardContent>
              {data?.emissions_timeline?.some(t => t.emissions > 0) ? (
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={data.emissions_timeline}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(240, 4%, 16%)" />
                    <XAxis
                      dataKey="date"
                      tick={{ fill: 'hsl(240, 5%, 65%)', fontSize: 12 }}
                      axisLine={{ stroke: 'hsl(240, 4%, 16%)' }}
                    />
                    <YAxis
                      tick={{ fill: 'hsl(240, 5%, 65%)', fontSize: 12 }}
                      axisLine={{ stroke: 'hsl(240, 4%, 16%)' }}
                      tickFormatter={formatEmissions}
                    />
                    <Tooltip
                      contentStyle={{
                        background: 'hsl(0, 0%, 7%)',
                        border: '1px solid hsl(240, 4%, 16%)',
                        borderRadius: '8px'
                      }}
                      formatter={(value) => [`${formatEmissions(value)} kg CO2e`, 'Emissions']}
                    />
                    <Bar dataKey="emissions" fill="hsl(145, 100%, 45%)" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[200px] flex items-center justify-center text-muted-foreground">
                  No timeline data yet
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Scope Breakdown Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="bg-card border-border neon-border" data-testid="scope1-card">
            <CardContent className="p-6">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-2 h-2 rounded-full bg-primary" />
                <span className="text-sm font-medium">Scope 1 - Direct</span>
              </div>
              <p className="text-2xl font-bold font-['Outfit']">
                {formatEmissions(data?.stats?.scope1_emissions || 0)}
                <span className="text-sm font-normal text-muted-foreground ml-1">kg CO2e</span>
              </p>
              <p className="text-xs text-muted-foreground mt-2">
                Company vehicles, on-site fuel combustion
              </p>
            </CardContent>
          </Card>

          <Card className="bg-card border-border" data-testid="scope2-card">
            <CardContent className="p-6">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-2 h-2 rounded-full bg-secondary" />
                <span className="text-sm font-medium">Scope 2 - Indirect</span>
              </div>
              <p className="text-2xl font-bold font-['Outfit']">
                {formatEmissions(data?.stats?.scope2_emissions || 0)}
                <span className="text-sm font-normal text-muted-foreground ml-1">kg CO2e</span>
              </p>
              <p className="text-xs text-muted-foreground mt-2">
                Purchased electricity, steam, heating
              </p>
            </CardContent>
          </Card>

          <Card className="bg-card border-border" data-testid="scope3-card">
            <CardContent className="p-6">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-2 h-2 rounded-full bg-chart-3" />
                <span className="text-sm font-medium">Scope 3 - Value Chain</span>
              </div>
              <p className="text-2xl font-bold font-['Outfit']">
                {formatEmissions(data?.stats?.scope3_emissions || 0)}
                <span className="text-sm font-normal text-muted-foreground ml-1">kg CO2e</span>
              </p>
              <p className="text-xs text-muted-foreground mt-2">
                Business travel, employee commuting
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Recent Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Invoices */}
          <Card className="bg-card border-border" data-testid="recent-invoices">
            <CardHeader>
              <CardTitle className="font-['Outfit']">Recent Invoices</CardTitle>
            </CardHeader>
            <CardContent>
              {data?.recent_invoices?.length > 0 ? (
                <div className="space-y-3">
                  {data.recent_invoices.map((invoice) => (
                    <div
                      key={invoice.id}
                      className="flex items-center justify-between p-3 rounded-lg bg-muted/50"
                    >
                      <div className="flex items-center gap-3">
                        <FileText className="w-5 h-5 text-muted-foreground" />
                        <div>
                          <p className="text-sm font-medium truncate max-w-[200px]">
                            {invoice.file_name}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {new Date(invoice.uploaded_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      <span
                        className={`text-xs px-2 py-1 rounded-full ${
                          invoice.status === 'completed'
                            ? 'bg-primary/20 text-primary'
                            : invoice.status === 'processing'
                            ? 'bg-chart-3/20 text-chart-3'
                            : 'bg-destructive/20 text-destructive'
                        }`}
                      >
                        {invoice.status}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center text-muted-foreground py-8">
                  No invoices yet
                </p>
              )}
            </CardContent>
          </Card>

          {/* Recent Reports */}
          <Card className="bg-card border-border" data-testid="recent-reports">
            <CardHeader>
              <CardTitle className="font-['Outfit']">Recent Reports</CardTitle>
            </CardHeader>
            <CardContent>
              {data?.recent_reports?.length > 0 ? (
                <div className="space-y-3">
                  {data.recent_reports.map((report) => (
                    <div
                      key={report.id}
                      className="flex items-center justify-between p-3 rounded-lg bg-muted/50"
                    >
                      <div className="flex items-center gap-3">
                        <FileBarChart className="w-5 h-5 text-muted-foreground" />
                        <div>
                          <p className="text-sm font-medium">
                            {report.compliance_standard} - {report.report_period}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {formatEmissions(report.total_emissions || 0)} kg CO2e
                          </p>
                        </div>
                      </div>
                      <span
                        className={`text-xs px-2 py-1 rounded-full ${
                          report.status === 'completed'
                            ? 'bg-primary/20 text-primary'
                            : 'bg-chart-3/20 text-chart-3'
                        }`}
                      >
                        {report.status}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center text-muted-foreground py-8">
                  No reports yet
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </Layout>
  );
}
