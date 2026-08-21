"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, ShieldAlert } from "lucide-react";

export default function Hero() {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    setPrefersReducedMotion(mediaQuery.matches);
    const handleChange = () => setPrefersReducedMotion(mediaQuery.matches);
    mediaQuery.addEventListener("change", handleChange);
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, []);

  return (
    <section className="relative min-h-[calc(100vh-80px)] bg-brand-black flex items-center overflow-hidden border-b border-brand-border/60">
      {/* Background Grid Pattern */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1a1a1a_1px,transparent_1px),linear-gradient(to_bottom,#1a1a1a_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] opacity-20 pointer-events-none" />

      <div className="max-w-7xl mx-auto px-6 w-full py-16 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center relative z-10">
        {/* Left Column: Left-Locked Typography */}
        <div className="lg:col-span-7 flex flex-col items-start text-left">
          <div className="inline-flex items-center space-x-2 bg-brand-red/10 border border-brand-red/30 px-3 py-1 mb-6 font-mono text-[11px] uppercase tracking-widest text-brand-red">
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>AUTHORITATIVE AI RISK ENGINE</span>
          </div>

          <h1 className="font-sans font-bold text-4xl sm:text-6xl xl:text-7xl text-white tracking-tight leading-[1.05] mb-6">
            Fraud detection <br />
            <span className="text-white">without false alarms.</span>
          </h1>

          <p className="font-sans text-base sm:text-xl text-brand-muted max-w-2xl leading-relaxed mb-10">
            Detect persistent merchant fraud while separating real attacks from legitimate surges like flash sales and bulk orders.
          </p>

          {/* Actions */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4 w-full sm:w-auto">
            <Link
              href="/dashboard"
              className="group relative inline-flex items-center justify-center space-x-3 bg-brand-red hover:bg-brand-red-hover text-white font-mono text-sm tracking-widest uppercase px-8 py-4 transition-colors rounded-none"
            >
              <span>LAUNCH RAZORSHIELD</span>
              <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
            </Link>

            <Link
              href="/scenarios"
              className="inline-flex items-center justify-center space-x-2 border border-brand-border hover:border-white text-brand-muted hover:text-white font-mono text-sm tracking-widest uppercase px-8 py-4 transition-colors rounded-none"
            >
              <span>SEE HOW IT WORKS</span>
            </Link>
          </div>
        </div>

        {/* Right Column: Atmospheric Looping CloudFront Video Atmosphere */}
        <div className="lg:col-span-5 relative w-full h-[380px] sm:h-[450px] border border-brand-border bg-brand-dark overflow-hidden group">
          {!prefersReducedMotion ? (
            <video
              autoPlay
              muted
              loop
              playsInline
              preload="auto"
              className="w-full h-full object-cover opacity-60 mix-blend-luminosity filter contrast-125"
            >
              <source
                src="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260809_132544_b6ef0174-ed95-45ad-9a2f-ccb8acfbdce8.mp4"
                type="video/mp4"
              />
            </video>
          ) : (
            <div className="w-full h-full bg-brand-card flex items-center justify-center p-6 text-center">
              <span className="font-mono text-xs text-brand-muted">
                Atmospheric visual paused for reduced motion
              </span>
            </div>
          )}

          {/* Dark Overlay Mask */}
          <div className="absolute inset-0 bg-gradient-to-t from-brand-black via-transparent to-brand-black/40 pointer-events-none" />

          {/* Overlay Status Box */}
          <div className="absolute bottom-6 left-6 right-6 p-4 bg-brand-black/90 border border-brand-border/80 backdrop-blur-md">
            <div className="flex items-center justify-between font-mono text-xs">
              <span className="text-brand-muted">REAL-TIME MONITORING</span>
              <span className="flex items-center space-x-1.5 text-emerald-400">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span>ACTIVE</span>
              </span>
            </div>
            <div className="font-mono text-sm text-white font-semibold mt-2">
              Persistent Merchant State • Zero-Shot SLM
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
