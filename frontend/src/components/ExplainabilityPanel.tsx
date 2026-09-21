import React, { useState } from 'react';
import { ChevronDown, ChevronUp, HelpCircle, CheckCircle, XCircle, Info } from 'lucide-react';
import type { Explanation } from '../types/analysis';

interface Props {
  explanation: Explanation;
}

export function ExplainabilityPanel({ explanation }: Props) {
  const [showLimitations, setShowLimitations] = useState(false);

  return (
    <div className="glass rounded-2xl p-6 space-y-5">
      <div className="flex items-center gap-2">
        <HelpCircle size={16} className="text-violet-400" />
        <h3 className="text-sm font-semibold text-slate-200">Why did DeepShield produce this result?</h3>
      </div>

      {/* Intro */}
      <p className="text-slate-300 text-sm leading-relaxed">{explanation.intro}</p>

      {/* Findings */}
      {explanation.findings.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-mono text-slate-500 uppercase tracking-wider">Detected Anomalies</p>
          {explanation.findings.map((f, i) => (
            <div key={i} className="flex items-start gap-2.5 bg-red-500/5 border border-red-500/15 rounded-xl px-3 py-2">
              <XCircle size={14} className="text-red-400 flex-shrink-0 mt-0.5" />
              <p className="text-xs text-slate-300">{f}</p>
            </div>
          ))}
        </div>
      )}

      {/* Passing modules */}
      {explanation.passing_modules.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-mono text-slate-500 uppercase tracking-wider">Passed Checks</p>
          <div className="flex flex-wrap gap-2">
            {explanation.passing_modules.map((m, i) => (
              <div key={i} className="flex items-center gap-1.5 bg-emerald-500/5 border border-emerald-500/20 rounded-full px-3 py-1">
                <CheckCircle size={11} className="text-emerald-400" />
                <span className="text-xs text-emerald-300">{m}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Timeline narrative */}
      {explanation.timeline_narrative.length > 0 && (
        <div className="space-y-1.5">
          <p className="text-xs font-mono text-slate-500 uppercase tracking-wider">Event Sequence</p>
          {explanation.timeline_narrative.map((line, i) => (
            <p key={i} className="text-xs text-slate-400 font-mono pl-3 border-l border-violet-500/20">{line}</p>
          ))}
        </div>
      )}

      {/* Summary */}
      <div className="bg-white/3 rounded-xl px-4 py-3">
        <p className="text-xs text-slate-300">{explanation.summary}</p>
      </div>

      {/* Limitations toggle */}
      <button
        className="flex items-center gap-2 text-xs text-slate-500 hover:text-slate-400 transition-colors"
        onClick={() => setShowLimitations(l => !l)}
      >
        <Info size={12} />
        System Limitations
        {showLimitations ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
      </button>

      {showLimitations && (
        <div className="bg-amber-500/5 border border-amber-500/15 rounded-xl p-4 space-y-2">
          {explanation.limitations.map((l, i) => (
            <p key={i} className="text-xs text-amber-200/70 flex items-start gap-2">
              <span className="text-amber-500 mt-0.5">⚠</span>
              {l}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}
