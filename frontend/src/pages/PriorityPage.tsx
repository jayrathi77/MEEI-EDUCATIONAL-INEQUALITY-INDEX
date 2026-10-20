import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Download, ChevronDown } from 'lucide-react';
import { useApi } from '../hooks/useApi';
import { fetchPriorities, fetchDistricts, exportPrioritiesUrl } from '../services/api';
import { LoadingState, ErrorState, ScoreBar, fmt, Badge } from '../components/ui/Common';
import type { PriorityResponse } from '../types/api';

function PriorityBar({ value, label }: { value: number | null; label: string }) {
  if (value == null) return <span style={{ color: 'var(--clr-text-muted)' }}>—</span>;
  const pct = Math.round(value * 100);
  const color = value < 0.4 ? '#ef4444' : value < 0.6 ? '#f59e0b' : '#10b981';
  return (
    <div style={{ minWidth: 80 }}>
      <div style={{ fontSize: 13, fontFamily: 'var(--font-mono)', color, marginBottom: 2 }}>{pct}%</div>
      <div style={{ height: 4, background: 'var(--clr-surface-2)', borderRadius: 99 }}>
        <div style={{ height: '100%', borderRadius: 99, background: color, width: `${pct}%` }} />
      </div>
    </div>
  );
}

export default function PriorityPage() {
  const [selectedState, setSelectedState] = useState('');

  const { data: listData } = useApi(() => fetchDistricts(undefined, 1, 1000), []);
  const { data: priorities, loading, error } = useApi<PriorityResponse>(
    () => fetchPriorities(selectedState || undefined, 1, 1000),
    [selectedState]
  );

  const states: string[] = Array.from<string>(
    new Set((listData?.districts || []).map((d: { state_name: string }) => d.state_name))
  ).sort();

  if (loading) return <LoadingState message="Loading priority districts…" />;
  if (error) return <ErrorState message={error} />;

  const districts = priorities?.districts || [];

  return (
    <div>
      <div className="page-header">
        <h2>Priority Districts</h2>
        <p>
          Districts ranked by predicted disadvantage.
          Priority Score = 0.5×(1−predicted equality) + 0.3×(1−infrastructure) + 0.2×(1−equity).
        </p>
      </div>

      {/* Controls */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20, alignItems: 'center' }}>
        <select
          className="select-input"
          value={selectedState}
          onChange={e => setSelectedState(e.target.value)}
        >
          <option value="">— All States —</option>
          {states.map((s: string) => <option key={s} value={s}>{s}</option>)}
        </select>

        <a
          href={exportPrioritiesUrl(selectedState || undefined)}
          download
          className="btn btn-ghost"
          style={{ display: 'flex', alignItems: 'center', gap: 6, textDecoration: 'none' }}
        >
          <Download size={14} /> Export CSV
        </a>

        <span style={{ color: 'var(--clr-text-muted)', fontSize: 13, marginLeft: 'auto' }}>
          {priorities?.total} districts
        </span>
      </div>

      {/* Priority note */}
      {priorities?.note && (
        <div style={{ marginBottom: 16, padding: '10px 14px', background: 'rgba(59,130,246,0.06)',
          border: '1px solid rgba(59,130,246,0.2)', borderRadius: 8, fontSize: 12, color: '#93c5fd' }}>
          ℹ️ {priorities.note}
        </div>
      )}

      {/* Table */}
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Rank</th>
              <th>District</th>
              <th>State</th>
              <th>Priority Score</th>
              <th>Pred. Equality</th>
              <th>Infrastructure</th>
              <th>Equity</th>
              <th>MEEI</th>
              <th>Top Drivers</th>
            </tr>
          </thead>
          <tbody>
            {districts.map(d => (
              <tr key={d.district_id}>
                <td>
                  <span style={{
                    fontWeight: 700, fontFamily: 'var(--font-mono)',
                    color: d.priority_rank <= 10 ? '#ef4444' : d.priority_rank <= 30 ? '#f59e0b' : '#94a3b8',
                  }}>
                    #{d.priority_rank}
                  </span>
                </td>
                <td style={{ fontWeight: 500 }}>
                  <Link to={`/district/${d.district_id}`} style={{ color: '#60a5fa', textDecoration: 'none', fontWeight: 500 }}>
                    {d.district_name}
                  </Link>
                </td>
                <td style={{ color: 'var(--clr-text-dim)', fontSize: 12 }}>{d.state_name}</td>
                <td>
                  <span style={{
                    fontFamily: 'var(--font-mono)', fontWeight: 700,
                    color: d.priority_score > 0.6 ? '#ef4444' : d.priority_score > 0.4 ? '#f59e0b' : '#10b981',
                  }}>
                    {d.priority_score.toFixed(3)}
                  </span>
                </td>
                <td><PriorityBar value={d.predicted_equality} label="eq" /></td>
                <td><PriorityBar value={d.infra_subindex} label="infra" /></td>
                <td><PriorityBar value={d.equity_subindex} label="equity" /></td>
                <td><PriorityBar value={d.meei} label="meei" /></td>
                <td style={{ fontSize: 11, color: 'var(--clr-text-muted)', maxWidth: 160 }}>
                  {d.top_drivers.slice(0, 2).map(dr => (
                    <div key={dr.feature}>{dr.label}</div>
                  ))}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {districts.length === 0 && (
        <div style={{ textAlign: 'center', padding: 40, color: 'var(--clr-text-dim)' }}>
          No priority data available. Run build_priority_list.py first.
        </div>
      )}
    </div>
  );
}
