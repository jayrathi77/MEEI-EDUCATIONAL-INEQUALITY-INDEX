import React from 'react';
import { useApi } from '../hooks/useApi';
import { fetchMethodology, fetchDataSources } from '../services/api';
import { LoadingState, ErrorState } from '../components/ui/Common';

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="card" style={{ marginBottom: 20 }}>
      <h3 style={{ fontSize: 15, fontWeight: 700, color: '#3b82f6', marginBottom: 12 }}>{title}</h3>
      {children}
    </div>
  );
}

function Item({ label, value }: { label: string; value: string | number }) {
  return (
    <div style={{ display: 'flex', gap: 12, marginBottom: 10, fontSize: 13 }}>
      <span style={{ minWidth: 160, color: 'var(--clr-text-muted)', fontWeight: 600 }}>{label}</span>
      <span style={{ color: 'var(--clr-text)', lineHeight: 1.5 }}>{value}</span>
    </div>
  );
}

export default function MethodologyPage() {
  const { data: method, loading, error } = useApi(fetchMethodology);
  const { data: sources } = useApi(fetchDataSources);

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;

  return (
    <div>
      <div className="page-header">
        <h2>Methodology & Data Sources</h2>
        <p>Complete documentation of the MEEI analytical framework, data provenance, and limitations.</p>
      </div>

      {method && (
        <>
          <Section title="MEEI Index Construction">
            <Item label="Stage 1" value={method.index_construction?.stage1} />
            <Item label="Stage 2" value={method.index_construction?.stage2} />
            <Item label="Rescaling" value={method.index_construction?.rescaling} />
          </Section>

          <Section title="Inequality of Opportunity (IOp)">
            <Item label="Method" value={method.iop?.method} />
            <Item label="Gini" value={method.iop?.gini} />
            <Item label="Estimation Level" value={method.iop?.level} />
            <div style={{ background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.3)',
              borderRadius: 8, padding: '10px 14px', marginTop: 8, fontSize: 12, color: '#fcd34d' }}>
              ⚠️ {method.iop?.caveat}
            </div>
          </Section>

          <Section title="Predictive Models">
            {Object.entries(method.models || {}).map(([k, v]) => (
              <Item key={k} label={k.toUpperCase()} value={v as string} />
            ))}
          </Section>

          <Section title="Validation Strategy">
            <p style={{ fontSize: 13, color: 'var(--clr-text)', lineHeight: 1.7 }}>{method.validation}</p>
          </Section>

          <Section title="Explainability">
            <p style={{ fontSize: 13, color: 'var(--clr-text)', lineHeight: 1.7 }}>{method.explainability}</p>
          </Section>

          <Section title="Priority District Rule">
            <p style={{ fontSize: 13, color: 'var(--clr-text)', lineHeight: 1.7, fontFamily: 'var(--font-mono)' }}>
              {method.priority_rule}
            </p>
          </Section>
        </>
      )}

      {sources && (
        <Section title="Data Sources">
          <div style={{ marginBottom: 12, padding: '8px 12px',
            background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.3)',
            borderRadius: 8, fontSize: 12, color: '#fca5a5' }}>
            ⚠️ Current Status: <strong>{sources.current_data}</strong> — {sources.warning}
          </div>
          {sources.sources?.map((s: { name: string; publisher: string; url: string; variables: string[]; status: string }) => (
            <div key={s.name} style={{ marginBottom: 16, paddingBottom: 16, borderBottom: '1px solid var(--clr-border)' }}>
              <div style={{ fontWeight: 600, marginBottom: 4 }}>{s.name}</div>
              <div style={{ fontSize: 12, color: 'var(--clr-text-muted)', marginBottom: 4 }}>{s.publisher}</div>
              <a href={s.url} target="_blank" rel="noopener noreferrer" style={{ fontSize: 12, color: '#60a5fa' }}>{s.url}</a>
              <div style={{ fontSize: 12, color: 'var(--clr-text-dim)', marginTop: 6 }}>
                <strong>Variables:</strong> {s.variables?.join(', ')}
              </div>
              <div style={{ marginTop: 4 }}>
                <span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 999,
                  background: 'rgba(245,158,11,0.15)', color: '#fcd34d' }}>{s.status}</span>
              </div>
            </div>
          ))}
        </Section>
      )}

      <Section title="Limitations">
        <ul style={{ fontSize: 13, color: 'var(--clr-text)', lineHeight: 1.8, paddingLeft: 20 }}>
          <li>All current results use <strong>synthetic demo data</strong>. No real government statistics are presented.</li>
          <li>The Conditional Inference Forest is approximated by ExtraTreesRegressor. A genuine CIF requires R's <code>partykit</code> package.</li>
          <li>IOp is estimated at district level from aggregated circumstance means, not individual microdata.</li>
          <li>SHAP values describe model prediction contributions — they are NOT causal policy estimates.</li>
          <li>PCA sign convention: higher MEEI = better equality, validated by correlation with performance sub-index.</li>
          <li>District boundary changes across census years are not fully harmonised in demo mode.</li>
        </ul>
      </Section>
    </div>
  );
}
