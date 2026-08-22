/**
 * razorshield.ts
 * Server-Side RazorShield API Client.
 * Runs exclusively on the Vercel Node.js Server.
 * Communicates server-to-server with Hugging Face Space backend (Gradio 5+ API).
 */

import {
  AnalyzeTransactionResponse,
  MerchantStateQueryResponse,
  ScenarioReplayResult,
  TransactionApiInput,
} from "../types";

const BACKEND_URL =
  process.env.RAZORSHIELD_BACKEND_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "https://vedantjadhav701-razorshield-api.hf.space";

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: string;
  };
}

/**
 * Low-level server-to-server execution helper calling Gradio 5+ /gradio_api/call endpoints.
 */
async function callGradioApi<T = any>(apiName: string, data: any[]): Promise<T> {
  const cleanUrl = BACKEND_URL.replace(/\/$/, "");
  const postUrl = `${cleanUrl}/gradio_api/call/${apiName}`;

  // Step 1: Initiate execution
  const postRes = await fetch(postUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ data }),
    cache: "no-store",
  });

  if (!postRes.ok) {
    throw new Error(`Gradio POST to ${apiName} failed with HTTP ${postRes.status}`);
  }

  const { event_id } = await postRes.json();
  if (!event_id) {
    throw new Error(`Gradio POST to ${apiName} did not return an event_id`);
  }

  // Step 2: Retrieve stream result
  const getUrl = `${cleanUrl}/gradio_api/call/${apiName}/${event_id}`;
  const getRes = await fetch(getUrl, { cache: "no-store" });

  if (!getRes.ok) {
    throw new Error(`Gradio GET stream for ${apiName} failed with HTTP ${getRes.status}`);
  }

  const text = await getRes.text();
  const lines = text.split("\n");
  for (const line of lines) {
    if (line.startsWith("data: ")) {
      const rawDataStr = line.substring(6).trim();
      const parsedArray = JSON.parse(rawDataStr);
      const rawResult = Array.isArray(parsedArray) ? parsedArray[0] : parsedArray;
      if (typeof rawResult === "string") {
        try {
          return JSON.parse(rawResult) as T;
        } catch {
          return rawResult as unknown as T;
        }
      }
      return rawResult as T;
    }
  }

  throw new Error(`No complete data stream received for Gradio API ${apiName}`);
}

/**
 * Server-side Health Check
 */
export async function healthCheck(): Promise<ApiResponse<{ status: string; service: string; model: string; slm_loaded: boolean; policy_mode: string }>> {
  try {
    const start = performance.now();
    const res = await callGradioApi("analyze_merchant", ["M_HEALTH_CHECK"]);
    const latency = Math.round(performance.now() - start);

    if ((res as any)?.error) {
      return {
        success: false,
        error: {
          code: "BACKEND_ERROR",
          message: (res as any).error,
          details: (res as any).details || (res as any).error,
        },
      };
    }

    return {
      success: true,
      data: {
        status: "ok",
        service: "RazorShield Risk Intelligence",
        model: "Qwen/Qwen2.5-0.5B-Instruct",
        slm_loaded: true,
        policy_mode: "BALANCED",
      },
    };
  } catch (err: any) {
    console.error("Server-side healthCheck failed:", err.message || err);
    return {
      success: false,
      error: {
        code: "BACKEND_UNREACHABLE",
        message: "Hugging Face Space backend is unreachable or offline.",
        details: err.message,
      },
    };
  }
}

/**
 * Server-side Transaction Analysis
 */
export async function analyzeTransaction(
  input: TransactionApiInput
): Promise<ApiResponse<AnalyzeTransactionResponse>> {
  try {
    const mId = input.merchant_id || "M_101";
    const txId = input.transaction_id || `TX_${Date.now().toString().slice(-6)}`;
    const custId = input.customer_id || "C_1048";
    const devId = input.device_id || "D_882";
    const eventTime = input.event_time || new Date().toISOString();
    const amount = input.amount || 100.0;
    const pm = input.payment_method || "card";
    const tt = input.transaction_type || "sale";
    const policyMode = input.policy_mode || "BALANCED";

    const parsed = await callGradioApi<AnalyzeTransactionResponse>("analyze_transaction", [
      mId,
      txId,
      custId,
      devId,
      eventTime,
      amount,
      pm,
      tt,
      policyMode,
    ]);

    if ((parsed as any)?.error) {
      return {
        success: false,
        error: {
          code: "BACKEND_ERROR",
          message: (parsed as any).error,
          details: (parsed as any).details || (parsed as any).error,
        },
      };
    }

    return {
      success: true,
      data: parsed,
    };
  } catch (err: any) {
    console.error("Server-side analyzeTransaction failed:", err.message || err);
    return {
      success: false,
      error: {
        code: "TRANSACTION_ANALYSIS_FAILED",
        message: err.message || "Failed to evaluate transaction through backend risk engine.",
        details: err.message,
      },
    };
  }
}

/**
 * Server-side Merchant State Query
 */
export async function analyzeMerchant(
  merchantId: string
): Promise<ApiResponse<MerchantStateQueryResponse>> {
  try {
    const parsed = await callGradioApi<MerchantStateQueryResponse>("analyze_merchant", [merchantId]);

    if ((parsed as any)?.error) {
      return {
        success: false,
        error: {
          code: "BACKEND_ERROR",
          message: (parsed as any).error,
          details: (parsed as any).details || (parsed as any).error,
        },
      };
    }

    return {
      success: true,
      data: parsed,
    };
  } catch (err: any) {
    console.error("Server-side analyzeMerchant failed:", err.message || err);
    return {
      success: false,
      error: {
        code: "MERCHANT_QUERY_FAILED",
        message: err.message || "Failed to query merchant incident state from backend.",
        details: err.message,
      },
    };
  }
}

/**
 * Server-side Scenario Replay Execution
 */
export async function runScenario(
  scenarioName: string,
  policyMode: string = "BALANCED"
): Promise<ApiResponse<ScenarioReplayResult>> {
  try {
    const parsed = await callGradioApi<ScenarioReplayResult>("run_scenario", [scenarioName, policyMode]);

    if ((parsed as any)?.error) {
      return {
        success: false,
        error: {
          code: "BACKEND_ERROR",
          message: (parsed as any).error,
          details: (parsed as any).details || (parsed as any).error,
        },
      };
    }

    return {
      success: true,
      data: parsed,
    };
  } catch (err: any) {
    console.error("Server-side runScenario failed:", err.message || err);
    return {
      success: false,
      error: {
        code: "SCENARIO_REPLAY_FAILED",
        message: err.message || "Failed to execute scenario replay through backend.",
        details: err.message,
      },
    };
  }
}

/**
 * Server-side Evidence Explanation
 */
export async function explainEvidence(
  evidenceJson: string
): Promise<ApiResponse<any>> {
  try {
    const parsed = await callGradioApi("explain_evidence", [evidenceJson]);

    if ((parsed as any)?.error) {
      return {
        success: false,
        error: {
          code: "BACKEND_ERROR",
          message: (parsed as any).error,
          details: (parsed as any).details || (parsed as any).error,
        },
      };
    }

    return {
      success: true,
      data: parsed,
    };
  } catch (err: any) {
    console.error("Server-side explainEvidence failed:", err.message || err);
    return {
      success: false,
      error: {
        code: "EXPLANATION_GENERATION_FAILED",
        message: err.message || "Failed to generate explanation for evidence.",
        details: err.message,
      },
    };
  }
}

/**
 * Server-side Reset Demo State
 */
export async function resetDemoState(): Promise<ApiResponse<{ status: string; message: string }>> {
  try {
    const parsed = await callGradioApi<{ status: string; message: string }>("reset_demo_state", []);

    if ((parsed as any)?.error) {
      return {
        success: false,
        error: {
          code: "BACKEND_ERROR",
          message: (parsed as any).error,
          details: (parsed as any).details || (parsed as any).error,
        },
      };
    }

    return {
      success: true,
      data: parsed,
    };
  } catch (err: any) {
    console.error("Server-side resetDemoState failed:", err.message || err);
    return {
      success: false,
      error: {
        code: "RESET_FAILED",
        message: err.message || "Failed to reset demo state on backend.",
        details: err.message,
      },
    };
  }
}
