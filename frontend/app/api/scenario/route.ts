import { NextRequest, NextResponse } from "next/server";
import { runScenario } from "@/lib/server/razorshield";

export const maxDuration = 60;
export const dynamic = "force-dynamic";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const scenarioName = body.scenario_name || "FRAUD_SPIKE";
    const policyMode = body.policy_mode || "BALANCED";
    const result = await runScenario(scenarioName, policyMode);
    if (!result.success) {
      return NextResponse.json(result, { status: 500 });
    }
    return NextResponse.json(result, { status: 200 });
  } catch (err: any) {
    return NextResponse.json(
      {
        success: false,
        error: {
          code: "INVALID_REQUEST",
          message: "Failed to parse JSON body for scenario replay.",
          details: err.message,
        },
      },
      { status: 400 }
    );
  }
}
