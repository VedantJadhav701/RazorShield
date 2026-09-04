"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, X, ArrowRight, Shield } from "lucide-react";
import { cn } from "@/lib/utils";

export default function Navbar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  const navLinks = [
    { href: "/", label: "Home" },
    { href: "/dashboard", label: "Dashboard" },
    { href: "/scenarios", label: "Scenarios" },
    { href: "/evaluation", label: "Evaluation" },
  ];

  return (
    <header className="sticky top-0 z-50 bg-background/80 backdrop-blur-md border-b border-border/60">
      <div className="flex items-center justify-between px-6 md:px-12 lg:px-20 py-5 font-body max-w-7xl mx-auto w-full">
        {/* Left: Logo */}
        <Link href="/" className="flex items-center space-x-2.5 group">
          <div className="w-8 h-8 rounded-lg bg-primary text-primary-foreground flex items-center justify-center shadow-sm group-hover:scale-105 transition-transform">
            <Shield className="w-4 h-4 text-white stroke-[2.5]" />
          </div>
          <div className="flex items-baseline space-x-1.5">
            <span className="text-xl font-semibold tracking-tight text-foreground font-body">
              RazorShield
            </span>
            <span className="text-[10px] font-mono text-muted-foreground uppercase tracking-widest hidden sm:inline-block">
              / AI Risk Engine
            </span>
          </div>
        </Link>

        {/* Right (hidden on mobile): Nav links */}
        <nav className="hidden md:flex items-center gap-8">
          {navLinks.map((link) => {
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.label}
                href={link.href}
                className={cn(
                  "text-sm font-medium transition-colors font-body",
                  isActive
                    ? "text-foreground font-semibold"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>

        {/* CTA Button & Mobile Toggle */}
        <div className="flex items-center space-x-4">
          <Link
            href="/dashboard"
            className="rounded-full px-5 py-2 text-sm font-medium bg-primary text-primary-foreground hover:bg-primary/90 transition-all shadow-sm font-body hidden sm:inline-flex items-center space-x-1.5"
          >
            <span>Launch Console</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>

          <button
            type="button"
            className="md:hidden text-foreground p-2 rounded-lg hover:bg-secondary"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Toggle Navigation"
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {mobileOpen && (
        <div className="md:hidden border-b border-border bg-background px-6 py-4 flex flex-col space-y-3 font-body shadow-lg animate-in slide-in-from-top-2">
          {navLinks.map((link) => (
            <Link
              key={link.label}
              href={link.href}
              onClick={() => setMobileOpen(false)}
              className={cn(
                "text-sm font-medium py-2 text-muted-foreground hover:text-foreground",
                pathname === link.href && "text-foreground font-semibold"
              )}
            >
              {link.label}
            </Link>
          ))}
          <Link
            href="/dashboard"
            onClick={() => setMobileOpen(false)}
            className="w-full rounded-full px-5 py-2.5 text-center text-sm font-medium bg-primary text-primary-foreground hover:bg-primary/90 transition-colors shadow-sm mt-2 block"
          >
            Launch Console
          </Link>
        </div>
      )}
    </header>
  );
}
