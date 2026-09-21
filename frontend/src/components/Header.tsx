import React, { useEffect, useState } from 'react';
import { Shield, Activity, Wifi, WifiOff } from 'lucide-react';
import { checkHealth } from '../services/api';

export function Header() {
  const [online, setOnline] = useState<boolean | null>(null);

  useEffect(() => {
    const check = async () => {
      const ok = await checkHealth();
      setOnline(ok);
    };
    check();
    const interval = setInterval(check, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="sticky top-0 z-50 border-b border-white/5 bg-navy-900/80 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-600 to-cyan-500 flex items-center justify-center glow-purple">
                <Shield size={20} className="text-white" />
              </div>
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-emerald-400 rounded-full border-2 border-navy-900 animate-pulse" />
            </div>
            <div>
              <div className="flex items-baseline gap-2">
                <h1 className="text-xl font-bold gradient-text">DeepShield</h1>
                <span className="text-xs font-mono text-slate-500 hidden sm:block">v1.0</span>
              </div>
              <p className="text-xs text-slate-500 hidden sm:block">Multi-Layer Deepfake & Identity Verification</p>
            </div>
          </div>

          {/* Center tagline */}
          <div className="hidden md:block text-center">
            <p className="text-xs font-mono text-slate-400 border border-violet-500/20 rounded-full px-4 py-1 bg-violet-500/5">
              "Don't trust one check. Verify everything."
            </p>
          </div>

          {/* Status */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              {online === null ? (
                <Activity size={14} className="text-slate-500 animate-pulse" />
              ) : online ? (
                <><Wifi size={14} className="text-emerald-400" /><span className="text-xs text-emerald-400 font-mono hidden sm:block">Engine Online</span></>
              ) : (
                <><WifiOff size={14} className="text-red-400" /><span className="text-xs text-red-400 font-mono hidden sm:block">Engine Offline</span></>
              )}
            </div>
            <div className="hidden sm:flex items-center gap-1.5 text-xs font-mono text-slate-500">
              <span className="w-1.5 h-1.5 bg-violet-500 rounded-full animate-pulse" />
              AI Warriors
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
