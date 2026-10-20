import React, { useState } from 'react';
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip } from 'recharts';
import { useApi } from '../hooks/useApi';
import { fetchDistricts, fetchDistrict, fetchDistrictShap } from '../services/api';
import { LoadingState, ErrorState, ScoreBar, fmt, Badge } from '../components/ui/Common';
import type { DistrictListResponse, DistrictProfile, LocalShap } from '../types/api';

const INDICATOR_LABELS: Record<string, string> = {
  nas_math_cl3: 'Math Score Cl.3', nas_lang_cl3: 'Language Score Cl.3',
  nas_math_cl5: 'Math Score Cl.5', nas_lang_cl5: 'Language Score Cl.5',
  nas_math_cl8: 'Math Score Cl.8', nas_lang_cl8: 'Language Score Cl.8',
  pct_schools_electricity: 'Schools w/ Electricity (%)',
  pct_schools_drinking_water: 'Schools w/ Water (%)',
  pct_schools_toilets: 'Schools w/ Toilets (%)',
  pct_schools_computers: 'Schools w/ Computers (%)',
  pct_schools_library: 'Schools w/ Library (%)',
  pct_schools_permanent_building: 'Permanent Buildings (%)',
  pupil_teacher_ratio: 'Pupil-Teacher Ratio',
  pct_schools_medical_checkup: 'Medical Checkup Coverage (%)',
  pct_govt_schools: 'Government Schools (%)',
  gender_gap_math_cl5: 'Gender Gap (Math, Cl.5)',
  rural_urban_gap_math: 'Rural-Urban Gap (Math)',
  sc_gap_math_cl5: 'SC Achievement Gap (Math)',
  pct_literate_parents: 'Literate Parents (%)',
  pct_urban_hh: 'Urban Households (%)',
  pct_sc_st_population: 'SC/ST Population (%)',
  pct_professional_occupation: 'Professional Occupation (%)',
  hdi_proxy: 'HDI Proxy',
};

const SUB_COLORS: Record<string, string> = {
  perf_subindex: '#3b82f6',
  infra_subindex: '#10b981',
  equity_subindex: '#8b5cf6',
  circ_subindex: '#f59e0b',
};

export default function DistrictPage() {
  const [selectedState, setSelectedState] = useState('');
  const [selectedId, setSelectedId] = useState('');

  const { data: listData, loading: listLoading } = useApi<DistrictListResponse>(
    () => fetchDistricts(undefined, 1, 1000), []
  );

  const { data: profile, loading: profLoading, error: profError } = useApi<DistrictProfile>(
    () => fetchDistrict(selectedId),
    [selectedId]
  );

  const { data: shap } = useApi<LocalShap>(
    () => fetchDistrictShap(selectedId),
    [selectedId]
  );

  const allDistricts = listData?.districts || [];
  const states = [...new Set(allDistricts.map(d => d.state_name))].sort();
  const filteredDistricts = selectedState
    ? allDistricts.filter(d => d.state_name === selectedState)
    : allDistricts;

  const radarData = profile ? [
    { subject: 'Performance', value: (profile.perf_subindex ?? 0) * 100 },
    { subject: 'Infrastructure', value: (profile.infra_subindex ?? 0) * 100 },
    { subject: 'Equity', value: (profile.equity_subindex ?? 0) * 100 },
    { subject: 'Circumstances', value: (profile.circ_subindex ?? 0) * 100 },
  ] : [];

  return (
    <div>
      <div className="page-header">
        <h2>District Profile</h2>
        <p>Select a state and district to view its MEEI breakdown, sub-index scores, raw indicators, and model explanations.</p>
      </div>

      {/* Selectors */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 24 }}>
        <select
          className="select-input"
          value={selectedState}
          onChange={e => { setSelectedState(e.target.value); setSelectedId(''); }}
        >
          <option value="">— All States —</option>
          {states.map(s => <option key={s} value={s}>{s}</option>)}
        </select>

        <select
          className="select-input"
          value={selectedId}
          onChange={e => setSelectedId(e.target.value)}
          disabled={filteredDistricts.length === 0}
        >
          <option value="">— Select District —</option>
          {filteredDistricts.map(d => (
            <option key={d.district_id} value={d.district_id}>{d.district_name}</option>
          ))}
        </select>
      </div>

      {!selectedId && (
        <div className="card" style={{ textAlign: 'center', padding: 48, color: 'var(--clr-text-dim)' }}>
          Select a district above to view its profile.
        </div>
      )}

      {selectedId && profLoading && <LoadingState message="Loading district profile…" />}
      {selectedId && profError && <ErrorState message={profError} />}

      {profile && (
        <>
          {/* Header */}
          <div className="card" style={{ marginBottom: 20 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <h3 style={{ fontSize: 22, fontWeight: 700, marginBottom: 4 }}>{profile.district_name}</h3>
                <p style={{ color: 'var(--clr-text-dim)', fontSize: 14 }}>{profile.state_name}</p>
                <div style={{ marginTop: 8, display: 'flex', gap: 8 }}>
                  <Badge label="Synthetic Demo" type="amber" />
                  <Badge label={`Rank #${profile.meei_rank ?? '—'}`} type="blue" />
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: 12, color: 'var(--clr-text-muted)', marginBottom: 4 }}>MEEI Score</div>
                <div style={{ fontSize: 40, fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#3b82f6' }}>
                  {profile.meei != null ? (profile.meei * 100).toFixed(1) : '—'}
                </div>
                <div style={{ fontSize: 12, color: 'var(--clr-text-muted)' }}>out of 100</div>
              </div>
            </div>
          </div>

          <div className="section-grid cols-2">
            {/* Radar Chart */}
            <div className="card">
              <div className="card-header"><span className="card-title">Sub-Index Radar</span></div>
              <ResponsiveContainer width="100%" height={220}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#1e293b" />
                  <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                  <Radar dataKey="value" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.2} />
                  <Tooltip formatter={(v: any) => [Number(v ?? 0).toFixed(1) + '%', 'Score']}
                    contentStyle={{ background: '#1a2234', border: '1px solid #1e293b' }} />
                </RadarChart>
              </ResponsiveContainer>
            </div>

            {/* Sub-index bars with comparison */}
            <div className="card">
              <div className="card-header"><span className="card-title">Sub-Index Comparison</span></div>
              {(['perf_subindex', 'infra_subindex', 'equity_subindex', 'circ_subindex'] as const).map(key => {
                const labels: Record<string, string> = {
                  perf_subindex: 'Performance', infra_subindex: 'Infrastructure',
                  equity_subindex: 'Equity', circ_subindex: 'Circumstances',
                };
                return (
                  <div key={key} style={{ marginBottom: 12 }}>
                    <ScoreBar label={labels[key]} value={profile[key]} color={SUB_COLORS[key]} />
                    <div style={{ display: 'flex', gap: 16, fontSize: 11, color: 'var(--clr-text-muted)', paddingLeft: 4 }}>
                      <span>State median: {profile.state_medians[key] != null ? (profile.state_medians[key]! * 100).toFixed(1) + '%' : '—'}</span>
                      <span>National: {profile.national_medians[key] != null ? (profile.national_medians[key]! * 100).toFixed(1) + '%' : '—'}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Raw Indicators */}
          <div className="card" style={{ marginBottom: 20, marginTop: 20 }}>
            <div className="card-header"><span className="card-title">Raw Indicators</span></div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 12 }}>
              {Object.entries(profile.raw_indicators).map(([key, val]) => (
                <div key={key} style={{ background: 'var(--clr-surface-2)', borderRadius: 8, padding: '10px 14px' }}>
                  <div style={{ fontSize: 11, color: 'var(--clr-text-muted)', marginBottom: 4 }}>
                    {INDICATOR_LABELS[key] || key}
                  </div>
                  <div style={{ fontSize: 16, fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
                    {val != null ? fmt(val, 1) : <span style={{ color: 'var(--clr-text-muted)' }}>—</span>}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* SHAP */}
          {shap && (
            <div className="card">
              <div className="card-header"><span className="card-title">Model Explanation (SHAP)</span></div>
              <p style={{ fontSize: 12, color: 'var(--clr-text-muted)', marginBottom: 16 }}>
                Predicted equality: <strong style={{ color: '#3b82f6' }}>{fmt(shap.predicted_equality)}</strong> —
                SHAP contributions to prediction (not causal estimates).
              </p>
              <div className="section-grid cols-2">
                <div>
                  <p style={{ fontSize: 12, color: '#10b981', fontWeight: 600, marginBottom: 8 }}>↑ Top Positive Drivers</p>
                  {shap.top_positive_drivers.map(d => (
                    <div key={d.feature} style={{ display: 'flex', justifyContent: 'space-between', padding: '5px 0',
                      borderBottom: '1px solid var(--clr-border)', fontSize: 13 }}>
                      <span>{d.label}</span>
                      <span style={{ fontFamily: 'var(--font-mono)', color: '#10b981' }}>+{d.shap.toFixed(4)}</span>
                    </div>
                  ))}
                </div>
                <div>
                  <p style={{ fontSize: 12, color: '#ef4444', fontWeight: 600, marginBottom: 8 }}>↓ Top Negative Drivers</p>
                  {shap.top_negative_drivers.map(d => (
                    <div key={d.feature} style={{ display: 'flex', justifyContent: 'space-between', padding: '5px 0',
                      borderBottom: '1px solid var(--clr-border)', fontSize: 13 }}>
                      <span>{d.label}</span>
                      <span style={{ fontFamily: 'var(--font-mono)', color: '#ef4444' }}>{d.shap.toFixed(4)}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
