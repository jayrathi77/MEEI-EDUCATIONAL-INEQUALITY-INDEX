import React, { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { Search, MapPin, ArrowUpDown } from 'lucide-react';
import { useApi } from '../hooks/useApi';
import { fetchDistricts } from '../services/api';
import { LoadingState, ErrorState, ScoreBar, fmt, Badge } from '../components/ui/Common';
import type { DistrictListResponse, District } from '../types/api';

type SortKey = 'district_name' | 'state_name' | 'meei' | 'meei_rank';
type SortDir = 'asc' | 'desc';

export default function DistrictExplorerPage() {
  const [selectedState, setSelectedState] = useState('');
  const [search, setSearch] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('meei_rank');
  const [sortDir, setSortDir] = useState<SortDir>('asc');

  const { data: listData, loading, error } = useApi<DistrictListResponse>(
    () => fetchDistricts(undefined, 1, 1000), []
  );

  const allDistricts = listData?.districts || [];
  const states = useMemo(
    () => [...new Set(allDistricts.map(d => d.state_name))].sort(),
    [allDistricts]
  );

  const filtered = useMemo(() => {
    let result = allDistricts;
    if (selectedState) {
      result = result.filter(d => d.state_name === selectedState);
    }
    if (search.trim()) {
      const q = search.trim().toLowerCase();
      result = result.filter(d =>
        d.district_name.toLowerCase().includes(q) ||
        d.state_name.toLowerCase().includes(q) ||
        d.district_id.toLowerCase().includes(q)
      );
    }
    return result;
  }, [allDistricts, selectedState, search]);

  const sorted = useMemo(() => {
    const arr = [...filtered];
    arr.sort((a, b) => {
      let cmp = 0;
      if (sortKey === 'district_name' || sortKey === 'state_name') {
        cmp = (a[sortKey] || '').localeCompare(b[sortKey] || '');
      } else {
        cmp = ((a[sortKey] as number) ?? 999) - ((b[sortKey] as number) ?? 999);
      }
      return sortDir === 'asc' ? cmp : -cmp;
    });
    return arr;
  }, [filtered, sortKey, sortDir]);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDir(key === 'meei' ? 'desc' : 'asc');
    }
  };

  if (loading) return <LoadingState message="Loading districts…" />;
  if (error) return <ErrorState message={error} />;

  const SortIcon = ({ col }: { col: SortKey }) => (
    <ArrowUpDown size={12} style={{
      opacity: sortKey === col ? 1 : 0.3,
      marginLeft: 4,
      transform: sortKey === col && sortDir === 'desc' ? 'scaleY(-1)' : undefined,
    }} />
  );

  const getMeeiColor = (meei: number | null) => {
    if (meei == null) return 'var(--clr-text-muted)';
    if (meei >= 0.7) return '#10b981';
    if (meei >= 0.5) return '#3b82f6';
    if (meei >= 0.3) return '#f59e0b';
    return '#ef4444';
  };

  return (
    <div>
      <div className="page-header">
        <h2>District Explorer</h2>
        <p>Browse and search all {allDistricts.length} districts. Click any district to view its full profile with indicators, scores, and AI explanations.</p>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap', alignItems: 'center' }}>
        <div style={{ position: 'relative', flex: '1 1 240px', maxWidth: 360 }}>
          <Search size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--clr-text-muted)' }} />
          <input
            type="text"
            placeholder="Search districts or states…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="select-input"
            style={{ paddingLeft: 36, width: '100%' }}
          />
        </div>

        <select
          className="select-input"
          value={selectedState}
          onChange={e => setSelectedState(e.target.value)}
        >
          <option value="">— All States —</option>
          {states.map(s => <option key={s} value={s}>{s}</option>)}
        </select>

        <span style={{ color: 'var(--clr-text-muted)', fontSize: 13, marginLeft: 'auto' }}>
          {sorted.length} of {allDistricts.length} districts
        </span>
      </div>

      {/* Table */}
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th style={{ cursor: 'pointer' }} onClick={() => handleSort('meei_rank')}>
                Rank <SortIcon col="meei_rank" />
              </th>
              <th style={{ cursor: 'pointer' }} onClick={() => handleSort('district_name')}>
                District <SortIcon col="district_name" />
              </th>
              <th style={{ cursor: 'pointer' }} onClick={() => handleSort('state_name')}>
                State <SortIcon col="state_name" />
              </th>
              <th style={{ cursor: 'pointer' }} onClick={() => handleSort('meei')}>
                MEEI <SortIcon col="meei" />
              </th>
              <th>Performance</th>
              <th>Infrastructure</th>
              <th>Equity</th>
              <th>Circumstances</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {sorted.map(d => (
              <tr key={d.district_id} style={{ cursor: 'pointer' }} onClick={() => {}}>
                <td>
                  <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--clr-text-dim)' }}>
                    {d.meei_rank != null ? `#${d.meei_rank}` : '—'}
                  </span>
                </td>
                <td>
                  <Link
                    to={`/district/${d.district_id}`}
                    style={{ color: '#60a5fa', fontWeight: 600, textDecoration: 'none' }}
                    onClick={e => e.stopPropagation()}
                  >
                    {d.district_name}
                  </Link>
                </td>
                <td style={{ color: 'var(--clr-text-dim)', fontSize: 12 }}>{d.state_name}</td>
                <td>
                  <span style={{
                    fontFamily: 'var(--font-mono)', fontWeight: 700,
                    color: getMeeiColor(d.meei),
                  }}>
                    {d.meei != null ? (d.meei * 100).toFixed(1) : '—'}
                  </span>
                </td>
                <td><MiniBar value={d.perf_subindex} color="#3b82f6" /></td>
                <td><MiniBar value={d.infra_subindex} color="#10b981" /></td>
                <td><MiniBar value={d.equity_subindex} color="#8b5cf6" /></td>
                <td><MiniBar value={d.circ_subindex} color="#f59e0b" /></td>
                <td>
                  <Link
                    to={`/district/${d.district_id}`}
                    className="btn btn-ghost"
                    style={{ fontSize: 12, padding: '4px 10px', textDecoration: 'none', whiteSpace: 'nowrap' }}
                    onClick={e => e.stopPropagation()}
                  >
                    <MapPin size={12} /> View Profile
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {sorted.length === 0 && (
        <div style={{ textAlign: 'center', padding: 48, color: 'var(--clr-text-dim)' }}>
          No districts match your search.
        </div>
      )}
    </div>
  );
}

function MiniBar({ value, color }: { value: number | null; color: string }) {
  if (value == null) return <span style={{ color: 'var(--clr-text-muted)', fontSize: 12 }}>—</span>;
  const pct = Math.round(value * 100);
  return (
    <div style={{ minWidth: 60 }}>
      <div style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color, marginBottom: 2 }}>{pct}%</div>
      <div style={{ height: 3, background: 'var(--clr-surface-2)', borderRadius: 99 }}>
        <div style={{ height: '100%', borderRadius: 99, background: color, width: `${pct}%`, transition: 'width 0.3s' }} />
      </div>
    </div>
  );
}
