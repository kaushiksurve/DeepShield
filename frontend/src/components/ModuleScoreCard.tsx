import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import type { ModuleResult } from '../types/analysis';
import { getRiskBgColor, getScoreColor } from '../utils/formatters';
import clsx from 'clsx';

interface Props {
  moduleKey: string;
  result: ModuleResult;
}

export function ModuleScoreCard({ moduleKey, result }: Props) {
  const [expanded, setExpanded] = useState(false);
  const scoreColor = getScoreColor(result.score);
  const riskStyle = getRiskBgColor(result.risk);

  return (
    <div className={clsx(
      'glass rounded-xl overflow-hidden border transition-all duration-200',
      result.risk === 'high' && 'border-red-500/20',
      result.risk === 'medium' && 'border-amber-500/20',
      result.risk === 'low' && 'border-white/5',
    )}>
      <button
        className="w-full p-4 text-left"
        onClick={() => setExpanded(e => !e)}
      >
        <div className="flex items-center gap-3">
          {/* Score circle */}
          <div className="relative w-12 h-12 flex-shrink-0">
            <svg viewBox="0 0 36 36" className="w-12 h-12 -rotate-90">
              <circle cx="18" cy="18" r="15" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="3" />
              <circle
                cx="18" cy="18" r="15" fill="none"
                stroke={scoreColor}
                strokeWidth="3"
                strokeDasharray={`${(result.score / 100) * 94.25} 94.25`}
                strokeLinecap="round"
                style={{ filter: `drop-shadow(0 0 4px ${scoreColor}60)` }}
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-xs font-bold font-mono" style={{ color: scoreColor }}>
                {Math.round(result.score)}
              </span>
            </div>
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <p className="text-sm font-semibold text-slate-200">{result.label}</p>
              <div className="flex items-center gap-2">
                <span className={clsx('text-[10px] font-mono px-2 py-0.5 rounded-full border', riskStyle)}>
                  {result.risk.toUpperCase()}
                </span>
                {expanded ? <ChevronUp size={14} className="text-slate-500" /> : <ChevronDown size={14} className="text-slate-500" />}
              </div>
            </div>
            <div className="flex items-center gap-3 mt-1">
              <div className="flex-1 h-1 bg-white/5 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-700"
                  style={{ width: `${result.score}%`, background: scoreColor, boxShadow: `0 0 8px ${scoreColor}60` }}
                />
              </div>
              <span className="text-[10px] font-mono text-slate-500">{Math.round(result.confidence * 100)}% conf</span>
              <span className="text-[10px] font-mono text-slate-600">{result.weight}% weight</span>
            </div>
          </div>
        </div>
      </button>

      {expanded && result.evidence.length > 0 && (
        <div className="px-4 pb-4 border-t border-white/5 pt-3 space-y-2">
          {result.evidence.map((ev, i) => (
            <div key={i} className="flex items-start gap-2 text-xs text-slate-400">
              <span className="text-slate-600 mt-0.5">•</span>
              <span>{ev}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
