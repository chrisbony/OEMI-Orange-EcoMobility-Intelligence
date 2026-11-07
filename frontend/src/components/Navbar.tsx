"use client";

import React from "react";
import { ShieldCheck, Database, Activity, Sparkles } from "lucide-react";

interface NavbarProps {
  backendConnected: boolean;
}

export default function Navbar({ backendConnected }: NavbarProps) {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-800 bg-slate-950/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Left: Brand & Title */}
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-orange-500 to-amber-600 flex items-center justify-center shadow-lg shadow-orange-500/20">
            <span className="text-white font-black text-lg">O</span>
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-slate-100 tracking-tight text-base sm:text-lg">
                Orange EcoMobility Intelligence
              </span>
              <span className="hidden sm:inline-block px-2 py-0.5 text-[10px] font-semibold bg-orange-500/10 text-orange-400 border border-orange-500/30 rounded-full">
                OEMI MVP 1.0
              </span>
            </div>
            <p className="text-[11px] text-slate-400 hidden sm:block">
              District d&apos;Abidjan • Cocody • Yopougon • Marcory
            </p>
          </div>
        </div>

        {/* Right: Badges & Connectivity */}
        <div className="flex items-center space-x-3">
          {/* Regulatory k-anonymity badge */}
          <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-950/40 border border-emerald-500/30 text-emerald-400 text-xs">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span className="hidden md:inline font-medium">Loi CI n° 2013-450</span>
            <span className="font-bold">k ≥ 15</span>
          </div>

          {/* PostGIS / Neon Status */}
          <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-slate-300 text-xs">
            <Database className="w-3.5 h-3.5 text-sky-400" />
            <span className="hidden md:inline">PostGIS 3.6</span>
            <span className="w-2 h-2 rounded-full bg-sky-400" />
          </div>

          {/* Backend Status Probe */}
          <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-slate-300 text-xs">
            <Activity className="w-3.5 h-3.5 text-orange-400" />
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          </div>
        </div>
      </div>
    </header>
  );
}

