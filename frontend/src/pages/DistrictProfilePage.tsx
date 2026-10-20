import React from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip,
  BarChart, Bar, XAxis, YAxis, Cell, ReferenceLine, CartesianGrid,
} from 'recharts';
import { ArrowLeft, AlertTriangle, MapPin, Brain, BarChart2, Info } from 'lucide-react';
import { useApi } from '../hooks/useApi';
import { fetchDistrict, fetchDistrictShap } from '../services/api';
import { LoadingState, ErrorState, ScoreBar, fmt, Badge } from '../components/ui/Common';
import type { DistrictProfile, LocalShap } from '../types/api';

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

export default function DistrictProfilePage() {
  const { districtId } = useParams<{ districtId: string }>();
  const navigate = useNavigate();

  // Only fetch when we have a valid districtId
  const { data: profile, loading: profLoading, error: profError } = useApi<DistrictProfile>(
    () => {
      if (!districtId) return Promise.reject(new Error('No district ID provided'));
      return fetchDistrict(districtId);
    },
    [districtId]
  );

  const { data: shap, loading: shapLoading, error: shapError } = useApi<LocalShap>(
    () => {
      if (!districtId) return Promise.reject(new Error('No district ID'));
      return fetchDistrictShap(districtId);
    },
    [districtId]
  );

  // ── Loading State ──
  if (profLoading) {
    return (
      <div>
        <BackButton />
        <LoadingState message={`Loading profile for ${districtId}…`} />
      </div>
    );
  }

  // ── Not Found / Error State ──
  if (profError) {
    const is404 = profError.toLowerCase().includes('404') ||
      profError.toLowerCase().includes('not found');
    return (
      <div>
        <BackButton />
        <div className="state-container">
          <div className="state-icon" style={{
            background: is404 ? 'rgba(245,158,11,0.1)' : 'rgba(239,68,68,0.1)',
            color: is404 ? '#fbbf24' : '#f87171',
          }}>
            {is404 ? <MapPin size={24} /> : <AlertTriangle size={24} />}
          </div>
          <p className="state-title">
            {is404 ? 'District Not Found' : 'Error Loading District'}
          </p>
          <p className="state-desc">
            {is404
              ? `No district with ID "${districtId}" exists in the database.`
              : profError}
          </p>
          <div style={{ marginTop: 16 }}>
            <Link to="/districts" className="btn btn-ghost" style={{ textDecoration: 'none' }}>
              <ArrowLeft size={14} /> Back to District Explorer
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (!profile) return null;

  // ── Radar data ──
  const radarData = [
    { subject: 'Performance', value: (profile.perf_subindex ?? 0) * 100 },
    { subject: 'Infrastructure', value: (profile.infra_subindex ?? 0) * 100 },
    { subject: 'Equity', value: (profile.equity_subindex ?? 0) * 100 },
    { subject: 'Circumstances', value: (profile.circ_subindex ?? 0) * 100 },
  ];

  // ── SHAP waterfall data ──
  const waterfallData = shap ? buildWaterfallData(shap) : null;

  return (
    <div>
      <BackButton />

      {/* Header Card */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
          <div>
            <h3 style={{ fontSize: 24, fontWeight: 700, marginBottom: 4 }}>{profile.district_name}</h3>
            <p style={{ color: 'var(--clr-text-dim)', fontSize: 14, marginBottom: 8 }}>{profile.state_name}</p>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {profile.is_synthetic && <Badge label="Synthetic Demo" type="amber" />}
              <Badge label={`Rank #${profile.meei_rank ?? '—'}`} type="blue" />
              <Badge label={`ID: ${districtId}`} type="purple" />
            </div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: 12, color: 'var(--clr-text-muted)', marginBottom: 4 }}>MEEI Score</div>
            <div style={{ fontSize: 44, fontWeight: 800, fontFamily: 'var(--font-mono)', color: getMeeiColor(profile.meei) }}>
              {profile.meei != null ? (profile.meei * 100).toFixed(1) : '—'}
            </div>
            <div style={{ fontSize: 12, color: 'var(--clr-text-muted)' }}>out of 100</div>
          </div>
        </div>
      </div>

      {/* Sub-Index Section */}
      <div className="section-grid cols-2">
        {/* Radar Chart */}
        <div className="card">
          <div className="card-header"><span className="card-title">Sub-Index Radar</span></div>
          <ResponsiveContainer width="100%" height={240}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#1e293b" />
              <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 12 }} />
              <Radar dataKey="value" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.2} />
              <Tooltip
                formatter={(v: any) => [Number(v ?? 0).toFixed(1) + '%', 'Score']}
                contentStyle={{ background: '#1a2234', border: '1px solid #1e293b', borderRadius: 8 }}
              />
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
            const stateMedian = profile.state_medians?.[key];
            const nationalMedian = profile.national_medians?.[key];
            return (
              <div key={key} style={{ marginBottom: 12 }}>
                <ScoreBar label={labels[key]} value={profile[key]} color={SUB_COLORS[key]} />
                <div style={{ display: 'flex', gap: 16, fontSize: 11, color: 'var(--clr-text-muted)', paddingLeft: 4 }}>
                  <span>State median: {stateMedian != null ? (stateMedian * 100).toFixed(1) + '%' : '—'}</span>
                  <span>National: {nationalMedian != null ? (nationalMedian * 100).toFixed(1) + '%' : '—'}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Raw Indicators */}
      <div className="card" style={{ marginBottom: 20, marginTop: 20 }}>
        <div className="card-header"><span className="card-title">Raw Indicators</span></div>
        {profile.raw_indicators && Object.keys(profile.raw_indicators).length > 0 ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 12 }}>
            {Object.entries(profile.raw_indicators).map(([key, val]) => (
              <div key={key} style={{ background: 'var(--clr-surface-2)', borderRadius: 8, padding: '10px 14px' }}>
                <div style={{ fontSize: 11, color: 'var(--clr-text-muted)', marginBottom: 4 }}>
                  {INDICATOR_LABELS[key] || key}
                </div>
                <div style={{ fontSize: 16, fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
                  {val != null ? fmt(val, 1) : <span style={{ color: 'var(--clr-text-muted)' }}>Data unavailable</span>}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ padding: 24, textAlign: 'center', color: 'var(--clr-text-muted)', fontSize: 13 }}>
            <Info size={16} style={{ marginRight: 6, verticalAlign: 'middle' }} />
            Raw indicator data is not available for this district.
          </div>
        )}
      </div>

      {/* SHAP / Explainable AI Section */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-header">
          <span className="card-title"><Brain size={16} style={{ marginRight: 6, verticalAlign: 'middle' }} />Model Explanation (Explainable AI)</span>
        </div>

        {shapLoading && (
          <div style={{ padding: 24, textAlign: 'center', color: 'var(--clr-text-muted)' }}>
            Loading SHAP explanations…
          </div>
        )}

        {shapError && !shapLoading && (
          <div style={{ padding: 24 }}>
            <div style={{
              padding: '12px 16px', background: 'rgba(245,158,11,0.06)',
              border: '1px solid rgba(245,158,11,0.2)', borderRadius: 8,
              fontSize: 13, color: '#fbbf24',
            }}>
              <Info size={14} style={{ marginRight: 6, verticalAlign: 'middle' }} />
              SHAP explanation data is not available for this district.
              This may happen if the ML pipeline has not been run, or if this district was excluded from modeling.
            </div>
          </div>
        )}

        {shap && !shapLoading && (
          <>
            {/* Prediction summary */}
            <div style={{
              padding: '12px 16px', marginBottom: 16,
              background: 'rgba(59,130,246,0.06)', border: '1px solid rgba(59,130,246,0.15)',
              borderRadius: 8, fontSize: 13, color: '#93c5fd',
            }}>
              <strong>Predicted educational equality:</strong>{' '}
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#3b82f6', fontSize: 16 }}>
                {fmt(shap.predicted_equality, 4)}
              </span>
              <span style={{ marginLeft: 8, fontSize: 11, color: 'var(--clr-text-muted)' }}>
                (Expected baseline: {fmt(shap.expected_value, 4)})
              </span>
              <div style={{ marginTop: 6, fontSize: 11, color: 'var(--clr-text-muted)' }}>
                The model predicts how educationally equal this district is based on its circumstances and infrastructure.
                SHAP values show how each feature contributed to pushing the prediction above or below the baseline.
                These are <em>prediction explanations</em>, not causal effects.
              </div>
            </div>

            <div className="section-grid cols-2">
              {/* SHAP Waterfall Chart */}
              <div>
                <p style={{ fontSize: 12, fontWeight: 600, color: 'var(--clr-text-dim)', marginBottom: 12 }}>
                  <BarChart2 size={14} style={{ marginRight: 4, verticalAlign: 'middle' }} />
                  SHAP Waterfall — Feature Contributions
                </p>
                {waterfallData && waterfallData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={Math.max(220, waterfallData.length * 28 + 40)}>
                    <BarChart data={waterfallData} layout="vertical" margin={{ top: 5, right: 30, left: 120, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
                      <XAxis
                        type="number"
                        tick={{ fill: '#94a3b8', fontSize: 11 }}
                        tickFormatter={(v: number) => v.toFixed(3)}
                      />
                      <YAxis
                        type="category"
                        dataKey="label"
                        tick={{ fill: '#94a3b8', fontSize: 11 }}
                        width={115}
                      />
                      <Tooltip
                        formatter={(v: any, name: any) => [Number(v).toFixed(4), 'SHAP Value']}
                        contentStyle={{ background: '#1a2234', border: '1px solid #1e293b', borderRadius: 8, fontSize: 12 }}
                        labelStyle={{ color: '#f1f5f9' }}
                      />
                      <ReferenceLine x={0} stroke="#475569" />
                      <Bar dataKey="shap" radius={[0, 4, 4, 0]}>
                        {waterfallData.map((entry, idx) => (
                          <Cell key={idx} fill={entry.shap >= 0 ? '#10b981' : '#ef4444'} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div style={{ padding: 24, color: 'var(--clr-text-muted)', fontSize: 13 }}>
                    No SHAP contributions available.
                  </div>
                )}
              </div>

              {/* Top Drivers */}
              <div>
                <div style={{ marginBottom: 16 }}>
                  <p style={{ fontSize: 12, color: '#10b981', fontWeight: 600, marginBottom: 8 }}>↑ Top Positive Drivers</p>
                  <p style={{ fontSize: 11, color: 'var(--clr-text-muted)', marginBottom: 8 }}>
                    Features pushing the prediction <em>higher</em> (toward better equality)
                  </p>
                  {shap.top_positive_drivers.length > 0 ? shap.top_positive_drivers.map(d => (
                    <div key={d.feature} style={{
                      display: 'flex', justifyContent: 'space-between', padding: '6px 0',
                      borderBottom: '1px solid var(--clr-border)', fontSize: 13,
                    }}>
                      <span>{d.label}</span>
                      <span style={{ fontFamily: 'var(--font-mono)', color: '#10b981', fontWeight: 600 }}>+{d.shap.toFixed(4)}</span>
                    </div>
                  )) : (
                    <div style={{ color: 'var(--clr-text-muted)', fontSize: 12 }}>No positive drivers found</div>
                  )}
                </div>

                <div>
                  <p style={{ fontSize: 12, color: '#ef4444', fontWeight: 600, marginBottom: 8 }}>↓ Top Negative Drivers</p>
                  <p style={{ fontSize: 11, color: 'var(--clr-text-muted)', marginBottom: 8 }}>
                    Features pushing the prediction <em>lower</em> (toward less equality)
                  </p>
                  {shap.top_negative_drivers.length > 0 ? shap.top_negative_drivers.map(d => (
                    <div key={d.feature} style={{
                      display: 'flex', justifyContent: 'space-between', padding: '6px 0',
                      borderBottom: '1px solid var(--clr-border)', fontSize: 13,
                    }}>
                      <span>{d.label}</span>
                      <span style={{ fontFamily: 'var(--font-mono)', color: '#ef4444', fontWeight: 600 }}>{d.shap.toFixed(4)}</span>
                    </div>
                  )) : (
                    <div style={{ color: 'var(--clr-text-muted)', fontSize: 12 }}>No negative drivers found</div>
                  )}
                </div>
              </div>
            </div>

            {/* Natural language explanation */}
            <div style={{
              marginTop: 16, padding: '12px 16px',
              background: 'var(--clr-surface-2)', borderRadius: 8,
              fontSize: 13, color: 'var(--clr-text-dim)', lineHeight: 1.6,
            }}>
              <strong style={{ color: 'var(--clr-text)' }}>Why this prediction?</strong>{' '}
              {generateExplanation(shap, profile)}
            </div>

            {/* Disclaimer */}
            <div style={{ marginTop: 12, fontSize: 11, color: 'var(--clr-text-muted)', lineHeight: 1.5 }}>
              <strong>Limitations:</strong> SHAP values explain model predictions, not real-world causal relationships.
              The model was trained on {profile.is_synthetic ? 'synthetic (randomly generated)' : 'observed'} data.
              {profile.is_synthetic && ' Results are for demonstration only and must not be used for policy decisions.'}
              Feature contributions assume model accuracy — check the Model Comparison page for validation metrics.
            </div>
          </>
        )}
      </div>
    </div>
  );
}


// ── Helper Components ──

function BackButton() {
  return (
    <div style={{ marginBottom: 16 }}>
      <Link
        to="/districts"
        className="btn btn-ghost"
        style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: 6 }}
      >
        <ArrowLeft size={14} /> Back to District Explorer
      </Link>
    </div>
  );
}


// ── Helper Functions ──

function getMeeiColor(meei: number | null): string {
  if (meei == null) return 'var(--clr-text-muted)';
  if (meei >= 0.7) return '#10b981';
  if (meei >= 0.5) return '#3b82f6';
  if (meei >= 0.3) return '#f59e0b';
  return '#ef4444';
}

function buildWaterfallData(shap: LocalShap) {
  // Combine all contributions and sort by absolute value
  const entries = Object.entries(shap.shap_contributions || {})
    .map(([feature, value]) => ({
      feature,
      label: INDICATOR_LABELS[feature] || feature.replace(/_/g, ' '),
      shap: value,
      absShap: Math.abs(value),
    }))
    .sort((a, b) => b.absShap - a.absShap)
    .slice(0, 12); // Top 12 most impactful

  return entries;
}

function generateExplanation(shap: LocalShap, profile: DistrictProfile): string {
  const posDrivers = shap.top_positive_drivers.slice(0, 3);
  const negDrivers = shap.top_negative_drivers.slice(0, 3);
  const pred = shap.predicted_equality;
  const baseline = shap.expected_value;
  const diff = pred - baseline;

  let explanation = '';

  if (diff > 0.02) {
    explanation += `The model predicts ${profile.district_name} has higher educational equality than the average district (${(pred * 100).toFixed(1)} vs baseline ${(baseline * 100).toFixed(1)}).`;
  } else if (diff < -0.02) {
    explanation += `The model predicts ${profile.district_name} has lower educational equality than the average district (${(pred * 100).toFixed(1)} vs baseline ${(baseline * 100).toFixed(1)}).`;
  } else {
    explanation += `The model predicts ${profile.district_name}'s educational equality is close to the national average (${(pred * 100).toFixed(1)} vs baseline ${(baseline * 100).toFixed(1)}).`;
  }

  if (posDrivers.length > 0) {
    explanation += ` Factors that positively contribute include ${posDrivers.map(d => d.label).join(', ')}.`;
  }
  if (negDrivers.length > 0) {
    explanation += ` Factors that negatively impact the prediction include ${negDrivers.map(d => d.label).join(', ')}.`;
  }

  return explanation;
}
