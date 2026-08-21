/**
 * types.ts
 * TypeScript interfaces matching RazorShield API Contract (docs/API_CONTRACT.md).
 */

export interface ResponseMetadata {
  request_id: string;
  request_sent_at: string;
  response_received_at: string;
  roundtrip_latency_ms: number;
  data_source: "LIVE HUGGING FACE BACKEND" | "CLIENT FALLBACK";
}

export interface BackendHealthStatus {
  status: "CONNECTING" | "CONNECTED" | "DEGRADED" | "OFFLINE";
  endpoint: string;
  last_sync_at: string | null;
  roundtrip_latency_ms: number | null;
  error?: string | null;
}

export interface LogEventItem {
  id: string;
  timestamp: string;
  event_type: "REQUEST_SENT" | "RESPONSE_RECEIVED" | "DECISION_GENERATED" | "EVIDENCE_UPDATED" | "EXPLANATION_GENERATED" | "SYSTEM_RESET";
  operation: string;
  merchant_id?: string;
  summary: string;
  latency_ms?: number;
  is_error?: boolean;
}

export interface TransactionApiInput {
  merchant_id: string;
  transaction_id: string;
  customer_id?: string;
  device_id?: string;
  event_time?: string;
  amount: number;
  payment_method?: string;
  transaction_type?: string;
  policy_mode?: "CONSERVATIVE" | "BALANCED" | "HIGH_SENSITIVITY";
}

export interface TransactionRisk {
  fraud_probability: number;
}

export interface MerchantRisk {
  spike_probability: number;
  fraud_excess_ratio: number;
  velocity_ratio: number;
  incident_state: "NORMAL" | "INVESTIGATE" | "ALERT";
  severity: "LOW" | "MEDIUM" | "HIGH";
  incident_score: number;
  suspicious_windows: number;
}

export interface CampaignInfo {
  active: boolean;
  campaign_name?: string | null;
}

export interface Decision {
  action: "APPROVE" | "VERIFY" | "ALERT";
  policy_mode: string;
}

export interface ExplanationOutput {
  title: string;
  summary: string;
  key_signals: string[];
  campaign_context: string;
  recommended_action: string;
  confidence_note: string;
}

export interface PerformanceMetrics {
  risk_engine_latency_ms: number;
  slm_latency_ms: number;
  total_latency_ms: number;
}

export interface AnalyzeTransactionResponse {
  transaction_id: string;
  merchant_id: string;
  transaction_risk: TransactionRisk;
  merchant_risk: MerchantRisk;
  campaign: CampaignInfo;
  decision: Decision;
  explanation: ExplanationOutput;
  performance: PerformanceMetrics;
  meta?: ResponseMetadata;
  error?: string;
  details?: string;
}

export interface MerchantStateQueryResponse {
  merchant_id: string;
  rolling_window: {
    rolling_txn_count_15m: number;
    baseline_txn_count_15m: number;
    velocity_ratio: number;
    estimated_fraud_count: number;
    expected_fraud_count: number;
    fraud_excess_ratio: number;
  };
  incident_state: {
    merchant_id: string;
    current_spike_probability: number;
    current_fraud_excess_ratio: number;
    current_velocity_ratio: number;
    suspicious_transaction_count: number;
    consecutive_suspicious_windows: number;
    campaign_active: boolean;
  };
  meta?: ResponseMetadata;
}

export interface ScenarioReplayResult {
  scenario_name: string;
  scenario_id: string;
  merchant_id: string;
  total_transactions: number;
  replay_time_ms: number;
  incident_state_distribution: {
    NORMAL: number;
    INVESTIGATE: number;
    ALERT: number;
  };
  final_incident_state: "NORMAL" | "INVESTIGATE" | "ALERT";
  final_severity: "LOW" | "MEDIUM" | "HIGH";
  explanation: ExplanationOutput;
  meta?: ResponseMetadata;
  error?: string;
}
