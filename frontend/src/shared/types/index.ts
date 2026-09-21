export type JobStatus =
  | "QUEUED"
  | "CLONING"
  | "INDEXING"
  | "STATIC_ANALYSIS"
  | "DEFECT_PREDICTION"
  | "AI_REVIEW"
  | "AGGREGATING"
  | "COMPLETED"
  | "FAILED"
  | "CANCELLED";

export type FindingSeverity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INFO";
export type FindingCategory = "SECURITY" | "CODE_SMELL" | "BUG_RISK" | "PERFORMANCE" | "MAINTAINABILITY" | "ARCHITECTURE";
export type RiskTier = "CRITICAL" | "HIGH" | "MODERATE" | "LOW";

export interface Repository {
  id: string;
  url: string;
  name: string;
  description?: string;
  default_branch: string;
  primary_language?: string;
  languages: Record<string, number>;
  disk_size_bytes: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AnalysisJob {
  id: string;
  repository_id: string;
  branch: string;
  commit_sha?: string;
  status: JobStatus;
  current_stage: string;
  progress_percent: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface Issue {
  id: string;
  rule_id: string;
  category: FindingCategory;
  severity: FindingSeverity;
  file_path: string;
  line_start: number;
  line_end: number;
  title: string;
  description: string;
  snippet?: string;
  remediation?: string;
  cwe_id?: string;
}

export interface FileMetric {
  id: string;
  file_path: string;
  language?: string;
  sloc: number;
  cyclomatic_complexity: number;
  cognitive_complexity: number;
  function_count: number;
  class_count: number;
  maintainability_index: number;
  halstead_metrics: Record<string, any>;
}

export interface ShapFactor {
  feature_name: string;
  display_name: string;
  feature_value: number;
  shap_value: number;
  impact_direction: "INCREASES_RISK" | "DECREASES_RISK";
  percentage: number;
  remediation: string;
}

export interface ShapExplanation {
  base_value: number;
  predicted_probability: number;
  dominant_factor: string;
  summary: string;
  factors: ShapFactor[];
}

export interface DefectSummary {
  total_files_analyzed: number;
  critical_count: number;
  high_count: number;
  moderate_count: number;
  low_count: number;
  average_defect_probability: number;
  highest_risk_file?: string;
  highest_risk_probability: number;
}

export interface DefectPrediction {
  id: string;
  file_path: string;
  defect_probability: number;
  risk_tier: RiskTier;
  model_version: string;
  shap_factors: ShapExplanation | Record<string, any>;
}

export type CommentStatus = "PENDING" | "ACCEPTED" | "DISMISSED";

export interface ReviewComment {
  id: string;
  report_id: string;
  file_path: string;
  line_number: number;
  comment: string;
  suggested_patch?: string;
  status: CommentStatus;
  created_at: string;
}

export interface AnalysisReport {
  id: string;
  job_id: string;
  overall_score: number;
  maintainability_score: number;
  security_score: number;
  testing_score: number;
  architecture_score: number;
  total_files: number;
  total_lines_of_code: number;
  total_functions: number;
  total_classes: number;
  technical_debt_minutes: number;
  summary_metadata: Record<string, any>;
  created_at: string;
  issues: Issue[];
  file_metrics: FileMetric[];
  defect_predictions: DefectPrediction[];
  review_comments?: ReviewComment[];
}

export interface RadarAxisPoint {
  axis: string;
  value: number;
  benchmark_value: number;
}

export interface PillarScore {
  name: string;
  score: number;
  weight: number;
  weighted_contribution: number;
  grade: "A" | "B" | "C" | "D" | "F";
  benchmark_percentile: number;
  summary: string;
}

export interface RecommendationItem {
  rank: number;
  pillar: string;
  title: string;
  description: string;
  effort_minutes: number;
  potential_score_impact: number;
}

export interface RadarScorecardResponse {
  report_id: string;
  overall_score: number;
  grade: "A" | "B" | "C" | "D" | "F";
  radar_data: RadarAxisPoint[];
  pillars: PillarScore[];
  technical_debt_minutes: number;
  recommendations: RecommendationItem[];
  false_positives_suppressed: number;
  calculated_at: string;
}

export interface ScorecardTrendPoint {
  report_id: string;
  commit_hash?: string;
  analyzed_at: string;
  overall_score: number;
  maintainability_score: number;
  security_score: number;
  architecture_score: number;
  testing_score: number;
}

export interface ScorecardTrendResponse {
  repository_id: string;
  repository_name: string;
  points: ScorecardTrendPoint[];
  trend_direction: "IMPROVING" | "STABLE" | "DEGRADING";
  delta_since_previous: number;
}

export interface BenchmarkExperimentRQ1 {
  description: string;
  hybrid_precision: number;
  hybrid_recall: number;
  hybrid_f1_score: number;
  static_baseline_precision: number;
  static_baseline_recall: number;
  static_baseline_f1_score: number;
  f1_gain_percentage: number;
}

export interface BenchmarkExperimentRQ2 {
  description: string;
  total_files: number;
  total_loc: number;
  recall_at_top_20_percent_loc: number;
  random_baseline_recall: number;
  cost_effectiveness_multiplier: number;
}

export interface BenchmarkExperimentRQ3 {
  description: string;
  benign_test_fixture_alerts_total: number;
  false_positives_suppressed_count: number;
  false_positive_suppression_rate: number;
  critical_security_vulnerabilities_total: number;
  critical_vulnerabilities_retained_count: number;
  critical_vulnerability_retention_rate: number;
}

export interface BenchmarkSuiteResult {
  evaluation_timestamp: string;
  corpus_size: number;
  total_loc_evaluated: number;
  rq1_triangulation_accuracy: BenchmarkExperimentRQ1;
  rq2_effort_aware_ranking: BenchmarkExperimentRQ2;
  rq3_false_positive_suppression: BenchmarkExperimentRQ3;
  conclusion: string;
}

