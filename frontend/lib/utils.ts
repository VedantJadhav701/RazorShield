import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function safeNumber(val: any, fallback: number = 0): number {
  if (val === undefined || val === null || isNaN(Number(val))) return fallback;
  return Number(val);
}

export function formatCurrency(amount: number | undefined | null): string {
  const num = safeNumber(amount, 0);
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(num);
}

export function formatPercent(value: number | undefined | null): string {
  const num = safeNumber(value, 0);
  return `${(num * 100).toFixed(1)}%`;
}

export function formatFixed(value: number | undefined | null, digits: number = 2): string {
  const num = safeNumber(value, 0);
  return num.toFixed(digits);
}
