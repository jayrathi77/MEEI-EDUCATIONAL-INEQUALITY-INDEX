import React from 'react';
import { Routes, Route, NavLink, useNavigate, useLocation, Navigate } from 'react-router-dom';
import {
  LayoutDashboard, MapPin, TrendingUp, Target, BarChart2,
  BookOpen,
} from 'lucide-react';
import OverviewPage from '../pages/OverviewPage';
import DistrictExplorerPage from '../pages/DistrictExplorerPage';
import DistrictProfilePage from '../pages/DistrictProfilePage';
import InequalityPage from '../pages/InequalityPage';
import PriorityPage from '../pages/PriorityPage';
import ModelsPage from '../pages/ModelsPage';
import MethodologyPage from '../pages/MethodologyPage';

interface NavItem {
  path: string;
  label: string;
  icon: React.ReactNode;
  section?: string;
}

const NAV: NavItem[] = [
  { path: '/',             label: 'National Overview',  icon: <LayoutDashboard size={16} />, section: 'Research' },
  { path: '/districts',    label: 'District Explorer',  icon: <MapPin size={16} /> },
  { path: '/inequality',   label: 'Drivers & IOp',      icon: <TrendingUp size={16} /> },
  { path: '/priorities',   label: 'Priority Districts',  icon: <Target size={16} /> },
  { path: '/models',       label: 'Model Comparison',   icon: <BarChart2 size={16} />, section: 'Analysis' },
  { path: '/methodology',  label: 'Methodology & Data', icon: <BookOpen size={16} />, section: 'Documentation' },
];

export default function AppLayout() {
  const location = useLocation();

  let lastSection = '';

  // Check if current path matches a nav item (exact or starts-with for district profiles)
  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/';
    if (path === '/districts') return location.pathname === '/districts' || location.pathname.startsWith('/district/');
    return location.pathname.startsWith(path);
  };

  return (
    <div className="app-shell">
        {/* Sidebar */}
        <aside className="sidebar">
          <div className="sidebar-logo">
            <h1>MEEI Platform</h1>
            <span>Educational Equality ML</span>
          </div>

          <nav className="sidebar-nav">
            {NAV.map(item => {
              const showSection = item.section && item.section !== lastSection;
              if (item.section) lastSection = item.section;
              return (
                <React.Fragment key={item.path}>
                  {showSection && (
                    <div className="nav-section-label">{item.section}</div>
                  )}
                  <NavLink
                    to={item.path}
                    className={`nav-item ${isActive(item.path) ? 'active' : ''}`}
                  >
                    {item.icon}
                    {item.label}
                  </NavLink>
                </React.Fragment>
              );
            })}
          </nav>

          <div style={{ padding: '16px 20px', borderTop: '1px solid var(--clr-border)' }}>
            <div style={{ fontSize: 11, color: 'var(--clr-text-muted)', lineHeight: 1.6 }}>
              <strong style={{ color: 'var(--clr-text-dim)', display: 'block', marginBottom: 4 }}>
                MEEI v1.0 — Demo Mode
              </strong>
              Multidimensional Educational Equality Index
            </div>
          </div>
        </aside>

        {/* Main */}
        <main className="main-content">
          <Routes>
            <Route path="/" element={<OverviewPage />} />
            <Route path="/districts" element={<DistrictExplorerPage />} />
            <Route path="/district/:districtId" element={<DistrictProfilePage />} />
            <Route path="/inequality" element={<InequalityPage />} />
            <Route path="/priorities" element={<PriorityPage />} />
            <Route path="/models" element={<ModelsPage />} />
            <Route path="/methodology" element={<MethodologyPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
  );
}
