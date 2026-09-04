"use client";

import React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  Play,
  Search,
  ChevronDown,
  Bell,
  CheckCircle2,
  Plus,
  Settings,
  Sparkles,
  ArrowUpRight,
  ArrowDownLeft,
  CreditCard,
  Building2,
  DollarSign,
} from "lucide-react";

export default function Hero() {
  return (
    <section className="relative w-full h-[calc(100vh-77px)] flex flex-col items-center overflow-hidden bg-background">
      {/* Background Video */}
      <video
        autoPlay
        muted
        loop
        playsInline
        preload="auto"
        className="absolute inset-0 w-full h-full object-cover z-0 opacity-40 mix-blend-multiply"
      >
        <source
          src="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260319_015952_e1deeb12-8fb7-4071-a42a-60779fc64ab6.mp4"
          type="video/mp4"
        />
      </video>

      {/* Subtle Background Gradient Mask */}
      <div className="absolute inset-0 bg-gradient-to-b from-background/90 via-background/60 to-background z-0 pointer-events-none" />

      {/* Content Wrapper */}
      <div className="relative z-10 flex flex-col items-center w-full max-w-7xl px-4 sm:px-6 pt-6 sm:pt-10 pb-0 flex-1 justify-between">
        
        {/* Top Text Group */}
        <div className="flex flex-col items-center text-center max-w-3xl mx-auto">
          
          {/* 1. Badge */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-1.5 rounded-full border border-border bg-background px-4 py-1.5 text-sm text-muted-foreground font-body shadow-sm mb-6"
          >
            <span>Now with GPT-5 support</span>
            <Sparkles className="w-3.5 h-3.5 text-accent animate-pulse" />
          </motion.div>

          {/* 2. Headline */}
          <motion.h1
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-center font-display text-5xl md:text-6xl lg:text-[5rem] leading-[0.95] tracking-tight text-foreground max-w-xl"
          >
            The Future of <span className="font-display italic font-normal">Smarter</span> Automation
          </motion.h1>

          {/* 3. Subheadline */}
          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="mt-4 text-center text-base md:text-lg text-muted-foreground max-w-[650px] leading-relaxed font-body"
          >
            Automate your busywork with intelligent agents that learn, adapt, and execute—so your team can focus on what matters most.
          </motion.p>

          {/* 4. CTA Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="mt-5 flex items-center gap-3"
          >
            <Link
              href="/dashboard"
              className="rounded-full px-6 py-2.5 text-sm font-medium font-body bg-primary text-primary-foreground hover:bg-primary/90 transition-all shadow-sm flex items-center gap-2"
            >
              <span>Book a demo</span>
            </Link>

            <Link
              href="/scenarios"
              className="h-11 w-11 rounded-full border-0 bg-background shadow-[0_2px_12px_rgba(0,0,0,0.08)] hover:bg-background/80 flex items-center justify-center transition-all group"
              aria-label="Play scenario preview video"
            >
              <Play className="h-4 w-4 fill-foreground text-foreground group-hover:scale-110 transition-transform" />
            </Link>
          </motion.div>

        </div>

        {/* 5. Dashboard Preview (custom coded, NOT an image) */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.5 }}
          className="mt-8 w-full max-w-5xl"
        >
          <div
            className="rounded-2xl overflow-hidden p-3 md:p-4 select-none pointer-events-none transition-all"
            style={{
              background: "rgba(255, 255, 255, 0.45)",
              border: "1px solid rgba(255, 255, 255, 0.6)",
              boxShadow: "var(--shadow-dashboard)",
              backdropFilter: "blur(12px)",
              WebkitBackdropFilter: "blur(12px)",
            }}
          >
            {/* Dashboard Mock Shell */}
            <div className="bg-background rounded-xl border border-border shadow-sm overflow-hidden text-[11px] text-foreground font-body">
              
              {/* Top Bar */}
              <div className="flex items-center justify-between px-4 py-2.5 border-b border-border bg-secondary/40">
                <div className="flex items-center space-x-2">
                  <div className="w-5 h-5 rounded bg-primary text-primary-foreground flex items-center justify-center font-bold text-[10px]">
                    N
                  </div>
                  <span className="font-semibold text-xs text-foreground">Nexora</span>
                  <ChevronDown className="w-3 h-3 text-muted-foreground" />
                </div>

                {/* Search Bar */}
                <div className="flex items-center space-x-2 bg-background border border-border rounded-md px-3 py-1 text-muted-foreground w-48 sm:w-64">
                  <Search className="w-3 h-3" />
                  <span className="text-[10px] flex-1">Search or type a command...</span>
                  <kbd className="bg-secondary px-1.5 py-0.5 rounded text-[9px] font-mono border border-border">⌘K</kbd>
                </div>

                {/* Right Profile & Actions */}
                <div className="flex items-center space-x-3">
                  <span className="bg-accent/10 text-accent font-medium px-2.5 py-0.5 rounded-full text-[10px]">
                    Move Money
                  </span>
                  <Bell className="w-3.5 h-3.5 text-muted-foreground" />
                  <div className="w-6 h-6 rounded-full bg-slate-800 text-white flex items-center justify-center text-[10px] font-medium">
                    JB
                  </div>
                </div>
              </div>

              {/* Body: Sidebar + Main Content */}
              <div className="flex min-h-[360px]">
                
                {/* Sidebar (w-40) */}
                <div className="w-40 border-r border-border p-3 space-y-4 bg-secondary/20 hidden sm:block">
                  <div className="space-y-1">
                    <div className="flex items-center justify-between px-2 py-1.5 bg-secondary text-foreground font-medium rounded-md">
                      <span>Home</span>
                    </div>
                    <div className="flex items-center justify-between px-2 py-1.5 text-muted-foreground rounded-md">
                      <span>Tasks</span>
                      <span className="bg-accent text-accent-foreground text-[9px] px-1.5 py-0.2 rounded-full font-semibold">10</span>
                    </div>
                    <div className="px-2 py-1.5 text-muted-foreground">Transactions</div>
                    <div className="flex items-center justify-between px-2 py-1.5 text-muted-foreground">
                      <span>Payments</span>
                      <ChevronDown className="w-3 h-3" />
                    </div>
                    <div className="px-2 py-1.5 text-muted-foreground">Cards</div>
                    <div className="px-2 py-1.5 text-muted-foreground">Capital</div>
                    <div className="flex items-center justify-between px-2 py-1.5 text-muted-foreground">
                      <span>Accounts</span>
                      <ChevronDown className="w-3 h-3" />
                    </div>
                  </div>

                  <div className="pt-2 border-t border-border space-y-1">
                    <div className="text-[10px] font-semibold text-muted-foreground px-2 uppercase tracking-wider mb-1">
                      Workflows
                    </div>
                    <div className="px-2 py-1 text-muted-foreground">Track routes</div>
                    <div className="px-2 py-1 text-muted-foreground">Payments</div>
                    <div className="px-2 py-1 text-muted-foreground">Notifications</div>
                    <div className="px-2 py-1 text-muted-foreground">Settings</div>
                  </div>
                </div>

                {/* Main Content Area */}
                <div className="flex-1 p-4 bg-secondary/30 space-y-4">
                  
                  {/* Greeting */}
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-foreground">Welcome, Jane</h3>
                    <span className="text-muted-foreground text-[10px]">Updated just now</span>
                  </div>

                  {/* Action Buttons Row */}
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="bg-primary text-primary-foreground px-3 py-1 rounded-full font-medium text-[10px]">Send</span>
                    <span className="bg-background border border-border text-foreground px-3 py-1 rounded-full font-medium text-[10px]">Request</span>
                    <span className="bg-background border border-border text-foreground px-3 py-1 rounded-full font-medium text-[10px]">Transfer</span>
                    <span className="bg-background border border-border text-foreground px-3 py-1 rounded-full font-medium text-[10px]">Deposit</span>
                    <span className="bg-background border border-border text-foreground px-3 py-1 rounded-full font-medium text-[10px]">Pay Bill</span>
                    <span className="bg-background border border-border text-foreground px-3 py-1 rounded-full font-medium text-[10px]">Create Invoice</span>
                    <span className="text-muted-foreground hover:text-foreground text-[10px] ml-auto cursor-pointer">+ Customize</span>
                  </div>

                  {/* Two Cards Side by Side */}
                  <div className="flex flex-col md:flex-row gap-3">
                    
                    {/* Balance Card */}
                    <div className="flex-1 basis-0 bg-background border border-border rounded-xl p-3.5 space-y-2 shadow-sm">
                      <div className="flex items-center justify-between text-muted-foreground">
                        <div className="flex items-center space-x-1.5">
                          <span className="font-medium text-foreground">Mercury Balance</span>
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 fill-emerald-100" />
                        </div>
                        <span className="text-[10px]">Last 30 Days</span>
                      </div>

                      <div className="text-xl font-bold text-foreground font-mono">
                        $8,450,190<span className="text-xs text-muted-foreground font-normal">.32</span>
                      </div>

                      <div className="flex items-center space-x-3 text-[10px]">
                        <span className="text-emerald-600 font-medium flex items-center">
                          <ArrowUpRight className="w-3 h-3 mr-0.5" /> +$1.8M
                        </span>
                        <span className="text-rose-500 font-medium flex items-center">
                          <ArrowDownLeft className="w-3 h-3 mr-0.5" /> -$900K
                        </span>
                      </div>

                      {/* SVG Area Chart (h-20 cubic Bézier) */}
                      <div className="pt-1">
                        <svg className="w-full h-16" viewBox="0 0 300 80" preserveAspectRatio="none">
                          <defs>
                            <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="0%" stopColor="hsl(239, 84%, 67%)" stopOpacity="0.2" />
                              <stop offset="100%" stopColor="hsl(239, 84%, 67%)" stopOpacity="0" />
                            </linearGradient>
                          </defs>
                          <path
                            d="M 0 60 C 40 50, 70 65, 100 35 C 130 5, 170 55, 210 25 C 250 -5, 270 30, 300 15 L 300 80 L 0 80 Z"
                            fill="url(#areaGradient)"
                          />
                          <path
                            d="M 0 60 C 40 50, 70 65, 100 35 C 130 5, 170 55, 210 25 C 250 -5, 270 30, 300 15"
                            fill="none"
                            stroke="hsl(239, 84%, 67%)"
                            strokeWidth="1.5"
                            strokeLinecap="round"
                          />
                        </svg>
                      </div>
                    </div>

                    {/* Accounts Card */}
                    <div className="flex-1 basis-0 bg-background border border-border rounded-xl p-3.5 space-y-3 shadow-sm">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-foreground">Accounts</span>
                        <div className="flex items-center space-x-1.5 text-muted-foreground">
                          <Plus className="w-3.5 h-3.5 cursor-pointer" />
                          <Settings className="w-3.5 h-3.5 cursor-pointer" />
                        </div>
                      </div>

                      <div className="divide-y divide-transparent">
                        <div className="py-2.5 flex items-center justify-between text-xs">
                          <div className="flex items-center space-x-2">
                            <CreditCard className="w-3.5 h-3.5 text-muted-foreground" />
                            <span className="font-medium text-foreground">Credit</span>
                          </div>
                          <span className="font-mono text-foreground">$98,125.50</span>
                        </div>

                        <div className="py-2.5 flex items-center justify-between text-xs">
                          <div className="flex items-center space-x-2">
                            <Building2 className="w-3.5 h-3.5 text-muted-foreground" />
                            <span className="font-medium text-foreground">Treasury</span>
                          </div>
                          <span className="font-mono text-foreground">$6,750,200.00</span>
                        </div>

                        <div className="py-2.5 flex items-center justify-between text-xs">
                          <div className="flex items-center space-x-2">
                            <DollarSign className="w-3.5 h-3.5 text-muted-foreground" />
                            <span className="font-medium text-foreground">Operations</span>
                          </div>
                          <span className="font-mono text-foreground">$1,592,864.82</span>
                        </div>
                      </div>
                    </div>

                  </div>

                  {/* Transactions Table */}
                  <div className="bg-background border border-border rounded-xl p-3.5 space-y-2 shadow-sm">
                    <h4 className="font-semibold text-xs text-foreground">Recent Transactions</h4>
                    <div className="w-full text-[10px]">
                      <div className="grid grid-cols-4 pb-1 text-muted-foreground font-medium border-b border-border">
                        <span>Date</span>
                        <span>Description</span>
                        <span>Amount</span>
                        <span className="text-right">Status</span>
                      </div>

                      <div className="divide-y divide-border/40">
                        <div className="grid grid-cols-4 py-1.5 items-center">
                          <span className="text-muted-foreground">Mar 19</span>
                          <span className="font-medium text-foreground">AWS Services</span>
                          <span className="font-mono text-foreground">-$5,200.00</span>
                          <span className="text-right font-medium text-amber-600 bg-amber-50 rounded px-1.5 py-0.5 w-max ml-auto">Pending</span>
                        </div>

                        <div className="grid grid-cols-4 py-1.5 items-center">
                          <span className="text-muted-foreground">Mar 18</span>
                          <span className="font-medium text-foreground">Client Payment</span>
                          <span className="font-mono text-emerald-600">+$125,000.00</span>
                          <span className="text-right font-medium text-emerald-600 bg-emerald-50 rounded px-1.5 py-0.5 w-max ml-auto">Completed</span>
                        </div>

                        <div className="grid grid-cols-4 py-1.5 items-center">
                          <span className="text-muted-foreground">Mar 17</span>
                          <span className="font-medium text-foreground">Global Payroll</span>
                          <span className="font-mono text-foreground">-$85,450.00</span>
                          <span className="text-right font-medium text-emerald-600 bg-emerald-50 rounded px-1.5 py-0.5 w-max ml-auto">Completed</span>
                        </div>

                        <div className="grid grid-cols-4 py-1.5 items-center">
                          <span className="text-muted-foreground">Mar 16</span>
                          <span className="font-medium text-foreground">Office Supplies</span>
                          <span className="font-mono text-foreground">-$1,200.00</span>
                          <span className="text-right font-medium text-emerald-600 bg-emerald-50 rounded px-1.5 py-0.5 w-max ml-auto">Completed</span>
                        </div>
                      </div>
                    </div>
                  </div>

                </div>

              </div>

            </div>

          </div>
        </motion.div>

      </div>
    </section>
  );
}
