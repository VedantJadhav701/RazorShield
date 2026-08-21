import { NextRequest, NextResponse } from "next/server";
import { analyzeTransaction } from "@/lib/server/razorshield";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const result = await analyzeTransaction(body);
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
          message: "Failed to parse JSON body or invalid transaction payload.",
          details: err.message,
        },
      },
      { status: 400 }
    );
  }
}
