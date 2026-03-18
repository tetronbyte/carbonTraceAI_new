import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard,
  FileText,
  Link2,
  FileBarChart,
  LogOut,
  Leaf,
  Menu,
  X,
  Database
} from 'lucide-react';
import { useState } from 'react';

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/invoices', icon: FileText, label: 'Invoice Parser' },
  { to: '/ledger', icon: Link2, label: 'Carbon Ledger' },
  { to: '/reports', icon: FileBarChart, label: 'ESG Reports' },
  { to: '/erp', icon: Database, label: 'ERP Integrations' },
];

export function Sidebar() {
  const { user, organization, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const NavContent = () => (
    <>
      <div className="p-4 border-b border-border">
        <div className="flex items-center gap-3">
          <div className="w-14 h-14 flex items-center justify-center">
            <img src="/logo.png" alt="CarbonTraceAI Logo" className="w-full h-full object-contain" />
          </div>
          <div>
            <h1 className="font-bold text-lg text-foreground font-['Outfit']">CarbonTraceAI</h1>
            <p className="text-xs text-muted-foreground truncate max-w-[140px]">
              {organization?.name || 'Select Organization'}
            </p>
          </div>
        </div>
      </div>

      <nav className="flex-1 p-4 space-y-1">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            onClick={() => setMobileOpen(false)}
            className={({ isActive }) =>
              `sidebar-link flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium ${
                isActive ? 'active bg-accent text-accent-foreground' : 'text-muted-foreground hover:text-foreground'
              }`
            }
            data-testid={`nav-${label.toLowerCase().replace(/\s/g, '-')}`}
          >
            <Icon className="w-5 h-5" strokeWidth={1.5} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-border">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-9 h-9 rounded-full bg-primary/20 flex items-center justify-center">
            <span className="text-sm font-medium text-primary">
              {user?.full_name?.[0] || user?.email?.[0] || 'U'}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{user?.full_name || 'User'}</p>
            <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-xl bg-muted hover:bg-destructive/10 hover:text-destructive transition-colors text-sm"
          data-testid="logout-btn"
        >
          <LogOut className="w-4 h-4" />
          Logout
        </button>
      </div>
    </>
  );

  return (
    <>
      {/* Mobile menu button */}
      <button
        className="md:hidden fixed top-4 left-4 z-50 p-2 rounded-lg bg-card border border-border"
        onClick={() => setMobileOpen(!mobileOpen)}
        data-testid="mobile-menu-btn"
      >
        {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
      </button>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="md:hidden fixed inset-0 bg-black/60 z-40"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed left-0 top-0 h-full w-64 bg-card border-r border-border flex flex-col z-50 transform transition-transform md:translate-x-0 ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <NavContent />
      </aside>
    </>
  );
}

export function Layout({ children }) {
  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <main className="md:ml-64 min-h-screen p-4 md:p-6 lg:p-8">
        {children}
      </main>
    </div>
  );
}
