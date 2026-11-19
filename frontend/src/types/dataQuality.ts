export interface QualityDimensionsScore {
  completeness: number;
  uniqueness: number;
  validity: number;
  consistency: number;
  timeliness: number;
  overall_score: number;
}

export interface QualityIssue extends Record<string, unknown> {
  row_number: number;
  field: string;
  issue_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  raw_value?: unknown;
}

export interface TransformationAudit extends Record<string, unknown> {
  row_number: number;
  field: string;
  rule: string;
  raw_value: unknown;
  cleaned_value: unknown;
}

export interface QualityEvaluationReport {
  target_entity: string;
  total_records: number;
  dimensions: QualityDimensionsScore;
  total_issues: number;
  issues_by_type: Record<string, number>;
  issues: QualityIssue[];
}

export interface TableQualityMetric extends Record<string, unknown> {
  table_name: string;
  total_records: number;
  completeness: number;
  validity: number;
  uniqueness: number;
  consistency: number;
  timeliness: number;
  overall_score: number;
}

export interface SystemQualitySummary {
  total_records: number;
  dimensions: QualityDimensionsScore;
  tables: TableQualityMetric[];
  last_evaluated_at: string;
}

export interface CleanStagingResponse {
  import_job_id: number;
  total_records: number;
  cleaned_records: number;
  invalid_records: number;
  total_transformations: number;
  dimensions: QualityDimensionsScore;
  transformations_sample: TransformationAudit[];
}

export interface ApproveCuratedResponse {
  import_job_id: number;
  target_entity: string;
  curated_rows_promoted: number;
  status: string;
  message: string;
}
