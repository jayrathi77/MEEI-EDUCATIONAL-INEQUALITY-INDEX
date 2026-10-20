import axios from 'axios';

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({ baseURL: BASE, timeout: 30000 });

export const fetchHealth = () => api.get('/health').then(r => r.data);
export const fetchOverview = () => api.get('/overview').then(r => r.data);
export const fetchCoverage = () => api.get('/coverage').then(r => r.data);
export const fetchDistricts = (state?: string, page = 1, pageSize = 1000) =>
  api.get('/districts', { params: { state, page, page_size: pageSize } }).then(r => r.data);
export const fetchDistrict = (id: string) => api.get(`/districts/${id}`).then(r => r.data);
export const fetchIndexSummary = () => api.get('/index/summary').then(r => r.data);
export const fetchIndexDiagnostics = () => api.get('/index/diagnostics').then(r => r.data);
export const fetchIopSummary = () => api.get('/iop/summary').then(r => r.data);
export const fetchIopCircumstances = () => api.get('/iop/circumstances').then(r => r.data);
export const fetchModelComparison = () => api.get('/models/comparison').then(r => r.data);
export const fetchModelValidation = () => api.get('/models/validation').then(r => r.data);
export const fetchGlobalShap = () => api.get('/explainability/global').then(r => r.data);
export const fetchDistrictShap = (id: string) => api.get(`/explainability/district/${id}`).then(r => r.data);
export const fetchPriorities = (state?: string, page = 1, pageSize = 1000) =>
  api.get('/priorities', { params: { state, page, page_size: pageSize } }).then(r => r.data);
export const fetchMethodology = () => api.get('/methodology').then(r => r.data);
export const fetchDataSources = () => api.get('/data-sources').then(r => r.data);
export const exportPrioritiesUrl = (state?: string) =>
  `${BASE}/priorities/export${state ? `?state=${encodeURIComponent(state)}` : ''}`;
