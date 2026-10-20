// API types for MEEI platform

export interface OverviewData {
  synthetic_mode: boolean;
  n_districts: number;
  n_states: number;
  national_mean_meei: number;
  national_median_meei: number;
  sub_index_averages: Record<string, number>;
  top5_districts: DistrictSummary[];
  bottom5_districts: DistrictSummary[];
  state_averages: StateAverage[];
  data_source: string;
}

export interface DistrictSummary {
  district_id: string;
  district_name: string;
  state_name: string;
  meei: number | null;
  meei_rank: number | null;
}

export interface StateAverage {
  state_name: string;
  avg_meei: number;
}

export interface District {
  district_id: string;
  district_name: string;
  state_name: string;
  meei: number | null;
  meei_rank: number | null;
  perf_subindex: number | null;
  infra_subindex: number | null;
  equity_subindex: number | null;
  circ_subindex: number | null;
}

export interface DistrictProfile extends District {
  state_medians: Record<string, number | null>;
  national_medians: Record<string, number | null>;
  raw_indicators: Record<string, number | null>;
  is_synthetic: boolean;
  data_source: string;
}

export interface DistrictListResponse {
  total: number;
  page: number;
  page_size: number;
  districts: District[];
}

export interface IopSummary {
  status: string;
  estimation_level: string;
  warning: string;
  outcome_variable: string;
  n_districts: number;
  gini_overall: number;
  gini_predicted_types: number;
  iop_relative: number;
  iop_relative_pct: number;
  circumstance_importance: Record<string, { mean: number; std: number; rank: number }>;
  circumstances_used: string[];
}

export interface ModelResult {
  model: string;
  mean_rmse: number;
  mean_mae: number;
  mean_r2: number;
  mean_spearman: number;
  std_rmse: number;
  std_r2: number;
  is_best: boolean;
}

export interface ModelComparison {
  best_model: string;
  validation_strategy: string;
  evaluation_criterion: string;
  n_folds: number;
  note_cif: string;
  models: ModelResult[];
}

export interface ShapFeature {
  feature: string;
  label: string;
  mean_abs_shap: number;
  rank: number;
}

export interface GlobalShap {
  model_type: string;
  expected_value: number;
  n_districts: number;
  features: string[];
  global_importance: ShapFeature[];
  disclaimer: string;
}

export interface ShapDriver {
  feature: string;
  label: string;
  shap: number;
}

export interface LocalShap {
  district_id: string;
  district_name: string;
  state_name: string;
  predicted_equality: number;
  expected_value: number;
  shap_contributions: Record<string, number>;
  top_positive_drivers: ShapDriver[];
  top_negative_drivers: ShapDriver[];
}

export interface PriorityDistrict {
  priority_rank: number;
  district_id: string;
  district_name: string;
  state_name: string;
  priority_score: number;
  predicted_equality: number;
  meei: number | null;
  perf_subindex: number | null;
  infra_subindex: number | null;
  equity_subindex: number | null;
  circ_subindex: number | null;
  top_drivers: ShapDriver[];
  is_synthetic: boolean;
}

export interface PriorityResponse {
  total: number;
  page: number;
  page_size: number;
  prioritization_rule: Record<string, number>;
  note: string;
  districts: PriorityDistrict[];
}

export interface CoverageData {
  total_districts: number;
  districts_with_meei: number;
  coverage_pct: number;
  by_state: Record<string, { total: number; with_meei: number }>;
  data_source: string;
}

export interface IndexSummary {
  n_districts: number;
  distribution: Record<string, number>;
  sub_indices: Record<string, Record<string, number>>;
  data_source: string;
}

export interface HealthStatus {
  status: string;
  synthetic_mode: boolean;
  data_ready: Record<string, boolean>;
}
