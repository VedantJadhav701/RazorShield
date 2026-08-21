import { NextResponse } from "next/server";
import { healthCheck } from "@/lib/server/razorshield";

export async function GET() {
  const result = await healthCheck();
  if (!result.success) {
    return NextResponse.json(result, { status: 503 });
  }
  return NextResponse.json(result, { status: 200 });
}
