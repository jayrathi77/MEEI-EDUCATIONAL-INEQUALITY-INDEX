import React from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ErrorBar, Legend,
} from 'recharts';
import { CheckCircle, AlertTriangle } from 'lucide-react';
import { useApi } from '../hooks/useApi';
import { fetchModelComparison, fetchIndexDiagnostics } from '../services/api';
import { LoadingState, ErrorState, fmt, Badge } from '../components/ui/Common';
import type { ModelComparison } from '../types/api';

const METRIC_LABELS: Record<string, string> = {
  mean_rmse: 'Mean RMSE ↓', mean_mae: 'Mean MAE ↓',
  mean_r2: 'Mean R² ↑', mean_spearman: 'Spearman ρ ↑',
};

export default function ModelsPage() {
  const { data: comparison, loading, error } = useApi<ModelComparison>(fetchModelComparison);
  const { data: diagnostics } = useApi(fetchIndexDiagnostics);

  if (loading) return <LoadingState message="Loading model evaluation…" />;
  if (error) return <ErrorState message={error} />;

  const models = comparison?.models || [];

  const chartData = models.map(m => ({
    model: m.model.replace(' (approx)', '').replace('Conditional Inference Forest', 'CIF (approx)'),
    RMSE: m.mean_rmse,
    MAE: m.mean_mae,
    isBest: m.is_best,
  }));

  const r2Data = models.map(m => ({
    model: m.model.replace(' (approx)', '').replace('Conditional Inference Forest', 'CIF (approx)'),
    R2: m.mean_r2,
    Spearman: m.mean_spearman,
  }));

  return (
    <div>
      <div className="page-header">
        <h2>Model Comparison & Validation</h2>
        <p>State-grouped k-fold cross-validation results. All metrics are out-of-fold averages.</p>
      </div>

      {/* Validation info */}
      <div style={{ marginBottom: 24, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        {comparison?.validation_strategy && (
          <div style={{ padding: '8px 14px', background: 'rgba(59,130,246,0.08)',
            border: '1px solid rgba(59,130,246,0.2)', borderRadius: 8, fontSize: 12, color: '#93c5fd' }}>
            📊 {comparison.validation_strategy}
          </div>
        )}
        {comparison?.evaluation_criterion && (
          <div style={{ padding: '8px 14px', background: 'rgba(16,185,129,0.08)',
            border: '1px solid rgba(16,185,129,0.2)', borderRadius: 8, fontSize: 12, color: '#6ee7b7' }}>
            🎯 Criterion: {comparison.evaluation_criterion}
          </div>
        )}
        {comparison?.best_model && (
          <div style={{ padding: '8px 14px', background: 'rgba(245,158,11,0.08)',
            border: '1px solid rgba(245,158,11,0.2)', borderRadius: 8, fontSize: 12, color: '#fcd34d' }}>
            🏆 Best: {comparison.best_model}
          </div>
        )}
      </div>

      {/* CIF Note */}
      {comparison?.note_cif && (
        <div style={{ marginBottom: 20, padding: '10px 14px',
          background: 'rgba(139,92,246,0.08)', border: '1px solid rgba(139,92,246,0.3)',
          borderRadius: 8, fontSize: 12, color: '#c4b5fd', display: 'flex', gap: 8 }}>
          <AlertTriangle size={14} style={{ flexShrink: 0, marginTop: 1 }} />
          <span>{comparison.note_cif}</span>
        </div>
      )}

      {/* Metric Table */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-header"><span className="card-title">Cross-Validation Results</span></div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Model</th>
                <th>RMSE ↓</th>
                <th>MAE ↓</th>
                <th>R² ↑</th>
                <th>Spearman ρ ↑</th>
                <th>RMSE Std</th>
              </tr>
            </thead>
            <tbody>
              {models.map(m => (
                <tr key={m.model}>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      {m.is_best && <CheckCircle size={14} color="#10b981" />}
                      <span style={{ fontWeight: m.is_best ? 700 : 400 }}>{m.model}</span>
                      {m.is_best && <Badge label="Best" type="green" />}
                    </div>
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', color: m.is_best ? '#10b981' : undefined }}>
                    {fmt(m.mean_rmse, 4)}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{fmt(m.mean_mae, 4)}</td>
                  <td style={{ fontFamily: 'var(--font-mono)', color: m.mean_r2 > 0.5 ? '#10b981' : m.mean_r2 > 0 ? '#f59e0b' : '#ef4444' }}>
                    {fmt(m.mean_r2, 4)}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{fmt(m.mean_spearman, 4)}</td>
                  <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--clr-text-muted)' }}>
                    ±{fmt(m.std_rmse, 4)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="section-grid cols-2">
        {/* RMSE / MAE chart */}
        <div className="card">
          <div className="card-header"><span className="card-title">RMSE and MAE by Model</span></div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={chartData} margin={{ left: -10, right: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="model" tick={{ fontSize: 10, fill: '#94a3b8' }} />
              <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} />
              <Tooltip contentStyle={{ background: '#1a2234', border: '1px solid #1e293b' }} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="RMSE" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              <Bar dataKey="MAE" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* R² / Spearman chart */}
        <div className="card">
          <div className="card-header"><span className="card-title">R² and Spearman ρ by Model</span></div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={r2Data} margin={{ left: -10, right: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="model" tick={{ fontSize: 10, fill: '#94a3b8' }} />
              <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} domain={[0, 1]} />
              <Tooltip contentStyle={{ background: '#1a2234', border: '1px solid #1e293b' }} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="R2" fill="#10b981" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Spearman" fill="#f59e0b" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* PCA Diagnostics */}
      {diagnostics && diagnostics['Performance'] && (
        <div className="card" style={{ marginTop: 24 }}>
          <div className="card-header"><span className="card-title">PCA Diagnostics (Performance Sub-index)</span></div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 12 }}>
            {[
              { label: 'KMO Measure', val: fmt(diagnostics['Performance']?.kmo, 3) },
              { label: 'Bartlett χ²', val: fmt(diagnostics['Performance']?.bartlett_chi2, 2) },
              { label: 'Bartlett p', val: fmt(diagnostics['Performance']?.bartlett_p, 4) },
              { label: 'Components Retained', val: diagnostics['Performance']?.retained_components },
              { label: 'Explained Variance', val: fmt(diagnostics['Performance']?.total_explained_variance, 3) },
            ].map(item => (
              <div key={item.label} style={{ background: 'var(--clr-surface-2)', borderRadius: 8, padding: '10px 14px' }}>
                <div style={{ fontSize: 11, color: 'var(--clr-text-muted)', marginBottom: 4 }}>{item.label}</div>
                <div style={{ fontSize: 16, fontWeight: 700, fontFamily: 'var(--font-mono)' }}>{item.val}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
