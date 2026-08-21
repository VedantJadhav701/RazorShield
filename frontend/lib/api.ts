/**
 * api.ts
 * Browser-Side API Client.
 * Communicates ONLY with same-origin Next.js Server Route Handlers (/api/...).
 * The browser never connects directly to Hugging Face Spaces.
 */

import {
  AnalyzeTransactionResponse,
  BackendHealthStatus,
  MerchantStateQueryResponse,
  ResponseMetadata,
  ScenarioReplayResult,
  TransactionApiInput,
} from "./types";

function generateRequestId(): string {
  return `REQ_${Math.random().toString(36).substring(2, 8).toUpperCase()}`;
}

/**
 * Health check probe via /api/health
 */
export async function checkBackendHealth(): Promise<BackendHealthStatus> {
  const start = performance.now();
  const sentAt = new Date().toISOString();
  try {
    const res = await fetch("/api/health", { cache: "no-store" });
    const latency = Math.round(performance.now() - start);
    if (res.ok) {
      return {
        status: "CONNECTED",
        endpoint: "/api/health (Vercel Server Proxy)",
        last_sync_at: new Date().toISOString(),
        roundtrip_latency_ms: latency,
      };
    }
  } catch (err: any) {
    console.warn("Health check error via /api/health:", err);
  }

  return {
    status: "OFFLINE",
    endpoint: "/api/health",
    last_sync_at: sentAt,
    roundtrip_latency_ms: null,
    error: "Server-side RazorShield proxy unreachable",
  };
}

/**
 * Analyzes transaction via POST /api/transaction
 */
export async function analyzeTransaction(
  input: TransactionApiInput
): Promise<AnalyzeTransactionResponse> {
  const reqId = generateRequestId();
  const sentAt = new Date().toISOString();
  const start = performance.now();

  const res = await fetch("/api/transaction", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });

  const roundtrip = Math.round(performance.now() - start);
  const json = await res.json();

  if (!res.ok || !json.success || !json.data) {
    throw new Error(json?.error?.message || `Transaction analysis failed with HTTP ${res.status}`);
  }

  const parsed: AnalyzeTransactionResponse = json.data;
  parsed.meta = {
    request_id: reqId,
    request_sent_at: sentAt,
    response_received_at: new Date().toISOString(),
    roundtrip_latency_ms: roundtrip,
    data_source: "LIVE HUGGING FACE BACKEND",
  };

  return parsed;
}

/**
 * Replays scenario via POST /api/scenario
 */
export async function runScenarioReplay(
  scenarioName: string,
  policyMode: string = "BALANCED"
): Promise<ScenarioReplayResult> {
  const reqId = generateRequestId();
  const sentAt = new Date().toISOString();
  const start = performance.now();

  const res = await fetch("/api/scenario", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ scenario_name: scenarioName, policy_mode: policyMode }),
  });

  const roundtrip = Math.round(performance.now() - start);
  const json = await res.json();

  if (!res.ok || !json.success || !json.data) {
    throw new Error(json?.error?.message || `Scenario replay failed with HTTP ${res.status}`);
  }

  const parsed: ScenarioReplayResult = json.data;
  parsed.meta = {
    request_id: reqId,
    request_sent_at: sentAt,
    response_received_at: new Date().toISOString(),
    roundtrip_latency_ms: roundtrip,
    data_source: "LIVE HUGGING FACE BACKEND",
  };

  return parsed;
}

/**
 * Queries merchant state via POST /api/merchant
 */
export async function queryMerchantState(merchantId: string): Promise<MerchantStateQueryResponse> {
  const reqId = generateRequestId();
  const sentAt = new Date().toISOString();
  const start = performance.now();

  const res = await fetch("/api/merchant", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ merchant_id: merchantId }),
  });

  const roundtrip = Math.round(performance.now() - start);
  const json = await res.json();

  if (!res.ok || !json.success || !json.data) {
    throw new Error(json?.error?.message || `Merchant query failed with HTTP ${res.status}`);
  }

  const parsed: MerchantStateQueryResponse = json.data;
  parsed.meta = {
    request_id: reqId,
    request_sent_at: sentAt,
    response_received_at: new Date().toISOString(),
    roundtrip_latency_ms: roundtrip,
    data_source: "LIVE HUGGING FACE BACKEND",
  };

  return parsed;
}

/**
 * Explains evidence via POST /api/explain
 */
export async function explainEvidencePayload(evidenceJson: string): Promise<any> {
  const res = await fetch("/api/explain", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ evidence_json: evidenceJson }),
  });

  const json = await res.json();
  if (!res.ok || !json.success) {
    throw new Error(json?.error?.message || `Explanation failed with HTTP ${res.status}`);
  }

  return json.data;
}

/**
 * Resets demo state via POST /api/reset
 */
export async function resetDemoState(): Promise<{ status: string; message: string; meta?: ResponseMetadata }> {
  const reqId = generateRequestId();
  const sentAt = new Date().toISOString();
  const start = performance.now();

  const res = await fetch("/api/reset", {
    method: "POST",
  });

  const roundtrip = Math.round(performance.now() - start);
  const json = await res.json();

  if (!res.ok || !json.success || !json.data) {
    throw new Error(json?.error?.message || `Reset demo state failed with HTTP ${res.status}`);
  }

  const parsed = json.data;
  parsed.meta = {
    request_id: reqId,
    request_sent_at: sentAt,
    response_received_at: new Date().toISOString(),
    roundtrip_latency_ms: roundtrip,
    data_source: "LIVE HUGGING FACE BACKEND",
  };

  return parsed;
}
