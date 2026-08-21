import { NextRequest, NextResponse } from "next/server";
import { analyzeMerchant } from "@/lib/server/razorshield";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const merchantId = body.merchant_id || "M_101";
    const result = await analyzeMerchant(merchantId);
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
          message: "Failed to parse JSON request body.",
          details: err.message,
        },
      },
      { status: 400 }
    );
  }
}
