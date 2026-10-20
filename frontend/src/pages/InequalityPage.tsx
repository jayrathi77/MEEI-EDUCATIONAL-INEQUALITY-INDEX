import React from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell,
} from 'recharts';
import { useApi } from '../hooks/useApi';
import { fetchIopSummary, fetchIopCircumstances, fetchGlobalShap } from '../services/api';
import { LoadingState, ErrorState, fmt, Tooltip as AppTooltip } from '../components/ui/Common';
import type { IopSummary, GlobalShap } from '../types/api';

export default function InequalityPage() {
  const { data: iop, loading: iopLoading, error: iopError } = useApi<IopSummary>(fetchIopSummary);
  const { data: shap, loading: shapLoading } = useApi<GlobalShap>(fetchGlobalShap);

  if (iopLoading) return <LoadingState message="Loading IOp estimates…" />;
  if (iopError) return <ErrorState message={iopError} />;

  const circumstances = iop?.circumstance_importance
    ? Object.entries(iop.circumstance_importance)
        .sort((a, b) => a[1].rank - b[1].rank)
        .map(([name, v]) => ({ name, ...v, nameShort: name.replace('pct_', '').replace(/_/g, ' ') }))
    : [];

  const shapData = shap?.global_importance?.slice(0, 10).map(f => ({
    label: f.label.length > 30 ? f.label.slice(0, 30) + '…' : f.label,
    value: +(f.mean_abs_shap * 100).toFixed(4),
  })) || [];

  return (
    <div>
      <div className="page-header">
        <h2>Drivers & Inequality of Opportunity</h2>
        <p>Gini-based IOp estimation and SHAP-driven feature importance for educational equality.</p>
      </div>



      {iop?.status === 'OK' && (
        <>
          {/* IOp KPIs */}
          <div className="stat-grid" style={{ marginBottom: 24 }}>
            <div className="stat-card">
              <div className="stat-label">Overall Gini G(y)</div>
              <div className="stat-value" style={{ fontSize: 32 }}>{fmt(iop.gini_overall, 4)}</div>
              <div className="stat-desc">Outcome inequality</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Type Gini G(m)</div>
              <div className="stat-value" style={{ fontSize: 32 }}>{fmt(iop.gini_predicted_types, 4)}</div>
              <div className="stat-desc">Predicted-type inequality</div>
            </div>
            <div className="stat-card">
              <div className="stat-icon amber" style={{ background: 'rgba(245,158,11,0.1)' }}>
                <span style={{ fontSize: 18, fontWeight: 700 }}>%</span>
              </div>
              <div className="stat-label">Relative IOp</div>
              <div className="stat-value" style={{ color: '#f59e0b' }}>{iop.iop_relative_pct?.toFixed(1)}%</div>
              <div className="stat-desc">G(m) / G(y) — district-level approx.</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Estimation Level</div>
              <div className="stat-value" style={{ fontSize: 18 }}>{iop.estimation_level}</div>
              <div className="stat-desc">District-level circumstance types</div>
            </div>
          </div>

          <div className="section-grid cols-2">
            {/* Circumstance Importance */}
            <div className="card">
              <div className="card-header">
                <span className="card-title">Circumstance Permutation Importance</span>
                <AppTooltip text="Conditional permutation importance: how much prediction accuracy drops when each circumstance is randomly shuffled.">
                  <span style={{ cursor: 'help', color: 'var(--clr-text-muted)', fontSize: 12 }}>ⓘ</span>
                </AppTooltip>
              </div>
              {circumstances.map((c, i) => (
                <div key={c.name} style={{ marginBottom: 10 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 3 }}>
                    <span style={{ color: 'var(--clr-text)' }}>
                      <span style={{ color: 'var(--clr-text-muted)', fontSize: 11, marginRight: 6 }}>#{c.rank}</span>
                      {c.nameShort}
                    </span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>{c.mean.toFixed(5)}</span>
                  </div>
                  <div style={{ height: 6, background: 'var(--clr-surface-2)', borderRadius: 99 }}>
                    <div style={{
                      height: '100%', borderRadius: 99, background: '#8b5cf6',
                      width: `${Math.min((c.mean / (circumstances[0]?.mean || 1)) * 100, 100)}%`,
                      transition: 'width 0.6s',
                    }} />
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--clr-text-muted)', marginTop: 2 }}>
                    ± {c.std.toFixed(5)}
                  </div>
                </div>
              ))}
            </div>

            {/* SHAP Global Importance */}
            <div className="card">
              <div className="card-header">
                <span className="card-title">SHAP Global Feature Importance</span>
                <AppTooltip text="Mean absolute SHAP values across all districts. Larger value = stronger average influence on predicted equality.">
                  <span style={{ cursor: 'help', color: 'var(--clr-text-muted)', fontSize: 12 }}>ⓘ</span>
                </AppTooltip>
              </div>
              {shapLoading ? (
                <div className="state-container" style={{ padding: 24 }}>
                  <div className="spinner" />
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={shapData} layout="vertical" margin={{ left: 10, right: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
                    <XAxis type="number" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                    <YAxis type="category" dataKey="label" width={160} tick={{ fontSize: 11, fill: '#94a3b8' }} />
                    <Tooltip
                      formatter={(v: any) => [Number(v ?? 0).toFixed(4), '|SHAP|']}
                      contentStyle={{ background: '#1a2234', border: '1px solid #1e293b' }}
                    />
                    <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                      {shapData.map((_, i) => (
                        <Cell key={i} fill={i === 0 ? '#3b82f6' : i < 3 ? '#6366f1' : '#475569'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
              {shap?.disclaimer && (
                <p style={{ fontSize: 11, color: 'var(--clr-text-muted)', marginTop: 12, lineHeight: 1.5 }}>
                  ⓘ {shap.disclaimer}
                </p>
              )}
            </div>
          </div>
        </>
      )}

      {iop?.status !== 'OK' && (
        <div className="card" style={{ textAlign: 'center', padding: 40 }}>
          <p style={{ color: 'var(--clr-text-dim)' }}>IOp data not available. Run estimate_iop.py first.</p>
        </div>
      )}
    </div>
  );
}
