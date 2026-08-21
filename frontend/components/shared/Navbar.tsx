"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Shield, ArrowRight, Menu, X } from "lucide-react";
import { cn } from "@/lib/utils";

export default function Navbar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  const navLinks = [
    { href: "/", label: "PRODUCT" },
    { href: "/dashboard", label: "DASHBOARD" },
    { href: "/scenarios", label: "SCENARIOS" },
    { href: "/evaluation", label: "EVALUATION" },
  ];

  return (
    <header className="sticky top-0 z-50 bg-brand-black/90 backdrop-blur-md border-b border-brand-border/60">
      <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
        {/* Brand Mark */}
        <Link href="/" className="flex items-center space-x-3 group">
          <div className="w-9 h-9 bg-brand-red flex items-center justify-center text-white transition-transform group-hover:scale-105">
            <Shield className="w-5 h-5 stroke-[2.5]" />
          </div>
          <div className="flex flex-col">
            <span className="font-sans font-bold text-lg tracking-wider text-white leading-none">
              RAZOR<span className="text-brand-red">SHIELD</span>
            </span>
            <span className="font-mono text-[10px] tracking-widest text-brand-muted uppercase mt-0.5">
              Risk Intelligence
            </span>
          </div>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center space-x-8">
          {navLinks.map((link) => {
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "font-mono text-xs tracking-widest uppercase transition-colors relative py-1",
                  isActive ? "text-white font-semibold" : "text-brand-muted hover:text-white"
                )}
              >
                {link.label}
                {isActive && (
                  <span className="absolute bottom-0 left-0 w-full h-[2px] bg-brand-red" />
                )}
              </Link>
            );
          })}
        </nav>

        {/* Desktop CTA */}
        <div className="hidden md:flex items-center">
          <Link
            href="/dashboard"
            className="group relative inline-flex items-center space-x-2 bg-brand-red hover:bg-brand-red-hover text-white font-mono text-xs tracking-widest uppercase px-6 py-3 transition-colors rounded-none"
          >
            <span>LAUNCH RAZORSHIELD</span>
            <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
          </Link>
        </div>

        {/* Mobile Burger Button */}
        <button
          type="button"
          className="md:hidden text-white p-2"
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label="Toggle Navigation"
        >
          {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* Mobile Burger Menu Overlay */}
      {mobileOpen && (
        <div className="md:hidden fixed inset-x-0 top-20 bg-brand-dark/95 backdrop-blur-xl border-b border-brand-border p-6 flex flex-col space-y-6">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              onClick={() => setMobileOpen(false)}
              className={cn(
                "font-mono text-sm tracking-widest uppercase py-2 border-b border-brand-border/40",
                pathname === link.href ? "text-brand-red font-bold" : "text-white"
              )}
            >
              {link.label}
            </Link>
          ))}
          <Link
            href="/dashboard"
            onClick={() => setMobileOpen(false)}
            className="w-full bg-brand-red text-center text-white font-mono text-xs tracking-widest uppercase py-4 flex items-center justify-center space-x-2 rounded-none"
          >
            <span>LAUNCH RAZORSHIELD</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      )}
    </header>
  );
}
