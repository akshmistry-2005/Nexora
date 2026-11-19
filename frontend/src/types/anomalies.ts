export type AnomalyDomain = 'sales' | 'transaction' | 'inventory' | 'marketing' | 'operations';
export type AnomalySeverity = 'low' | 'medium' | 'high' | 'critical';
export type AnomalyStatus = 'open' | 'acknowledged' | 'resolved' | 'dismissed';

export interface AnomalyAlert {
  id: number;
  organization_id: number | null;
  domain: AnomalyDomain;
  entity_identifier: string;
  metric_name: string;
  observed_value: number;
  baseline_value: number;
  deviation_amount: number;
  z_score: number;
  severity: AnomalySeverity;
  explanation: string;
  status: AnomalyStatus;
  acknowledged_at: string | null;
  acknowledged_by_id: number | null;
  detected_at: string;
  created_at: string;
}

export interface AnomalySummaryStats {
  total_alerts: number;
  open_alerts: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  acknowledged_count: number;
  by_domain: Record<string, number>;
}

export interface AnomalyAcknowledgeRequest {
  status: AnomalyStatus;
  notes?: string;
}

export interface AnomalyDetectionRunResponse {
  total_scanned_records: number;
  new_anomalies_detected: number;
  domains_scanned: string[];
  detector_algorithm: string;
  run_duration_ms: number;
}

export interface IsolationForestBenchmark {
  model_name: string;
  n_estimators: number;
  contamination: number;
  total_samples_evaluated: number;
  multivariate_anomalies_detected: number;
  univariate_anomalies_detected: number;
  overlap_count: number;
  multivariate_unique_count: number;
  univariate_unique_count: number;
  agreement_rate_pct: number;
  domain_distribution: Record<string, number>;
}
