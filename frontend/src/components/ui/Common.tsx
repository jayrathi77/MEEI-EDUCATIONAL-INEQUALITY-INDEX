import React from 'react';
import { AlertTriangle, Loader2, Database } from 'lucide-react';

export function LoadingState({ message = 'Loading data…' }: { message?: string }) {
  return (
    <div className="state-container">
      <div className="spinner" />
      <p className="state-title">{message}</p>
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="state-container">
      <div className="state-icon" style={{ background: 'rgba(239,68,68,0.1)', color: '#f87171' }}>
        <AlertTriangle size={24} />
      </div>
      <p className="state-title">Unable to load data</p>
      <p className="state-desc">{message}</p>
      <p className="state-desc" style={{ marginTop: 8, fontSize: 12 }}>
        Ensure the backend is running and the pipeline has been executed.
      </p>
    </div>
  );
}

export function EmptyState({ message = 'No data available.', sub = '' }: { message?: string; sub?: string }) {
  return (
    <div className="state-container">
      <div className="state-icon">
        <Database size={24} />
      </div>
      <p className="state-title">{message}</p>
      {sub && <p className="state-desc">{sub}</p>}
    </div>
  );
}

export function ScoreBar({ label, value, color }: { label: string; value: number | null; color?: string }) {
  const pct = value != null ? Math.round(value * 100) : null;
  return (
    <div className="score-bar-wrap">
      <div className="score-bar-label">
        <span>{label}</span>
        <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
          {pct != null ? pct + '%' : '—'}
        </span>
      </div>
      <div className="score-bar-track">
        <div
          className="score-bar-fill"
          style={{
            width: pct != null ? pct + '%' : '0%',
            background: color || 'linear-gradient(90deg, var(--clr-primary), var(--clr-accent))',
          }}
        />
      </div>
    </div>
  );
}

export function Badge({ label, type = 'blue' }: { label: string; type?: 'blue' | 'green' | 'amber' | 'red' | 'purple' }) {
  return <span className={`badge badge-${type}`}>{label}</span>;
}

export function Tooltip({ text, children }: { text: string; children: React.ReactNode }) {
  return (
    <div className="tooltip-wrap">
      {children}
      <div className="tooltip-text">{text}</div>
    </div>
  );
}

export function fmt(val: number | null | undefined, decimals = 3): string {
  if (val == null) return '—';
  return val.toFixed(decimals);
}

export function fmtPct(val: number | null | undefined): string {
  if (val == null) return '—';
  return (val * 100).toFixed(1) + '%';
}
