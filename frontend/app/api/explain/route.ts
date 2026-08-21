import { NextRequest, NextResponse } from "next/server";
import { explainEvidence } from "@/lib/server/razorshield";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const evidenceJson = typeof body.evidence_json === "string" ? body.evidence_json : JSON.stringify(body);
    const result = await explainEvidence(evidenceJson);
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
          message: "Failed to parse JSON body for explanation.",
          details: err.message,
        },
      },
      { status: 400 }
    );
  }
}
