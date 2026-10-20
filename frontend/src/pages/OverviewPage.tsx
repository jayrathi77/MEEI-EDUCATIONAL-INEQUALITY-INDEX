import React from 'react';
import { Link } from 'react-router-dom';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, CartesianGrid, Legend,
} from 'recharts';
import { MapPin, TrendingUp, Building2, Users, BookOpen, BarChart2 } from 'lucide-react';
import { useApi } from '../hooks/useApi';
import { fetchOverview, fetchDistricts } from '../services/api';
import { LoadingState, ErrorState, ScoreBar, fmt } from '../components/ui/Common';
import type { OverviewData, District } from '../types/api';

const SUB_LABELS: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
  perf_subindex:  { label: 'Performance',     color: '#3b82f6', icon: <BookOpen size={16} /> },
  infra_subindex: { label: 'Infrastructure',  color: '#10b981', icon: <Building2 size={16} /> },
  equity_subindex:{ label: 'Equity',          color: '#8b5cf6', icon: <Users size={16} /> },
  circ_subindex:  { label: 'Circumstances',   color: '#f59e0b', icon: <MapPin size={16} /> },
};

export default function OverviewPage() {
  const { data: overview, loading, error } = useApi<OverviewData>(fetchOverview);
  const { data: distList } = useApi<{ districts: District[] }>(() => fetchDistricts(undefined, 1, 1000));

  if (loading) return <LoadingState message="Loading national overview…" />;
  if (error) return <ErrorState message={error} />;
  if (!overview) return null;

  const stateChartData = (overview.state_averages || []).slice(0, 20).map(s => ({
    name: s.state_name.length > 12 ? s.state_name.slice(0, 12) + '…' : s.state_name,
    meei: +(s.avg_meei * 100).toFixed(1),
  }));

  const distData = (distList?.districts || [])
    .filter(d => d.meei != null)
    .map(d => ({ name: d.district_name, meei: +(( d.meei! ) * 100).toFixed(1), state: d.state_name }))
    .sort((a, b) => b.meei - a.meei);

  return (
    <div>
      <div className="page-header">
        <h2>National Overview</h2>
        <p>District-level educational equality across India — MEEI composite index (higher = better equality).</p>
      </div>

      {/* KPI Cards */}
      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-icon cyan"><BarChart2 size={20} /></div>
          <div className="stat-label">Districts Covered</div>
          <div className="stat-value">{overview.n_districts}</div>
          <div className="stat-desc">{overview.n_states} states</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon"><TrendingUp size={20} /></div>
          <div className="stat-label">National Mean MEEI</div>
          <div className="stat-value">{fmt(overview.national_mean_meei)}</div>
          <div className="stat-desc">Scale: 0–1 (higher = more equal)</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon green"><BookOpen size={20} /></div>
          <div className="stat-label">Mean Performance</div>
          <div className="stat-value">{fmt(overview.sub_index_averages?.perf_subindex)}</div>
          <div className="stat-desc">Performance sub-index</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon purple"><Users size={20} /></div>
          <div className="stat-label">Mean Equity</div>
          <div className="stat-value">{fmt(overview.sub_index_averages?.equity_subindex)}</div>
          <div className="stat-desc">Equity sub-index</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon amber"><Building2 size={20} /></div>
          <div className="stat-label">Mean Infrastructure</div>
          <div className="stat-value">{fmt(overview.sub_index_averages?.infra_subindex)}</div>
          <div className="stat-desc">Infrastructure sub-index</div>
        </div>
      </div>

      {/* Sub-index averages bars */}
      <div className="section-grid cols-2" style={{ marginBottom: 24 }}>
        <div className="card">
          <div className="card-header">
            <span className="card-title">Sub-Index Averages (National)</span>
          </div>
          {Object.entries(SUB_LABELS).map(([key, meta]) => (
            <ScoreBar
              key={key}
              label={meta.label}
              value={overview.sub_index_averages?.[key] ?? null}
              color={meta.color}
            />
          ))}
        </div>

        <div className="card">
          <div className="card-header">
            <span className="card-title">Top 5 Highest Equality Districts</span>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>#</th><th>District</th><th>State</th><th>MEEI</th></tr>
              </thead>
              <tbody>
                {overview.top5_districts.map((d, i) => (
                  <tr key={d.district_id}>
                    <td style={{ color: '#10b981', fontWeight: 700 }}>{i + 1}</td>
                    <td>
                      <Link to={`/district/${d.district_id}`} style={{ color: '#60a5fa', textDecoration: 'none', fontWeight: 500 }}>
                        {d.district_name}
                      </Link>
                    </td>
                    <td style={{ color: 'var(--clr-text-dim)', fontSize: 12 }}>{d.state_name}</td>
                    <td style={{ fontFamily: 'var(--font-mono)', color: '#3b82f6' }}>{fmt(d.meei)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* State Bar Chart */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-header">
          <span className="card-title">State-Average MEEI (Top 20 States)</span>
        </div>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={stateChartData} margin={{ top: 10, right: 10, left: -10, bottom: 60 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#94a3b8' }} angle={-35} textAnchor="end" interval={0} />
            <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} domain={[0, 100]} unit="%" />
            <Tooltip
              formatter={(v: any) => [Number(v ?? 0).toFixed(1) + '%', 'Avg MEEI']}
              contentStyle={{ background: '#1a2234', border: '1px solid #1e293b', borderRadius: 8 }}
              labelStyle={{ color: '#f1f5f9' }}
            />
            <Bar dataKey="meei" fill="#3b82f6" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Bottom 5 */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">5 Lowest Equality Districts (need attention)</span>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Rank</th><th>District</th><th>State</th><th>MEEI</th></tr>
            </thead>
            <tbody>
              {overview.bottom5_districts.map((d, i) => (
                <tr key={d.district_id}>
                  <td style={{ color: '#ef4444', fontWeight: 700 }}>{d.meei_rank ?? '—'}</td>
                  <td>
                    <Link to={`/district/${d.district_id}`} style={{ color: '#60a5fa', textDecoration: 'none', fontWeight: 500 }}>
                      {d.district_name}
                    </Link>
                  </td>
                  <td style={{ color: 'var(--clr-text-dim)', fontSize: 12 }}>{d.state_name}</td>
                  <td style={{ fontFamily: 'var(--font-mono)', color: '#ef4444' }}>{fmt(d.meei)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
