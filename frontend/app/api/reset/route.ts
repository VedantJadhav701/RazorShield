import { NextResponse } from "next/server";
import { resetDemoState } from "@/lib/server/razorshield";

export async function POST() {
  const result = await resetDemoState();
  if (!result.success) {
    return NextResponse.json(result, { status: 500 });
  }
  return NextResponse.json(result, { status: 200 });
}
