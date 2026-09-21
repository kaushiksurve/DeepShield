import React, { useEffect, useState } from 'react';
import { RadialBarChart, RadialBar, ResponsiveContainer, PolarAngleAxis } from 'recharts';
import type { AnalysisResult } from '../types/analysis';
import { getRiskLabel, getScoreColor } from '../utils/formatters';
import clsx from 'clsx';

interface Props {
  result: AnalysisResult;
}

export function TrustScoreGauge({ result }: Props) {
  const [animatedScore, setAnimatedScore] = useState(0);
  const target = result.trust_score;
  const color = getScoreColor(target);
  const riskLabel = getRiskLabel(result.risk_level);

  useEffect(() => {
    let current = 0;
    const step = target / 40;
    const timer = setInterval(() => {
      current = Math.min(current + step, target);
      setAnimatedScore(Math.round(current));
      if (current >= target) clearInterval(timer);
    }, 30);
    return () => clearInterval(timer);
  }, [target]);

  const data = [{ value: animatedScore, fill: color }];

  return (
    <div className="glass rounded-2xl p-6 text-center relative overflow-hidden">
      {/* Background glow */}
      <div
        className="absolute inset-0 opacity-5 rounded-2xl"
        style={{ background: `radial-gradient(circle at center, ${color}, transparent)` }}
      />

      {result.is_demo && (
        <div className="mb-3">
          <span className="text-[10px] font-mono bg-amber-500/20 text-amber-400 border border-amber-500/30 px-2 py-0.5 rounded-full">
            ⚠ DEMO / SIMULATED RESULT
          </span>
        </div>
      )}

      <p className="text-xs font-mono text-slate-500 uppercase tracking-widest mb-2">Joint Trust Score</p>

      <div className="relative w-48 h-48 mx-auto">
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart
            innerRadius="70%"
            outerRadius="100%"
            data={data}
            startAngle={90}
            endAngle={-270}
          >
            <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
            <RadialBar
              background={{ fill: 'rgba(255,255,255,0.04)' }}
              dataKey="value"
              cornerRadius={8}
              angleAxisId={0}
            />
          </RadialBarChart>
        </ResponsiveContainer>

        {/* Center content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span
            className="text-5xl font-bold tabular-nums"
            style={{ color }}
          >
            {animatedScore}
          </span>
          <span className="text-slate-500 text-xs font-mono">/ 100</span>
        </div>
      </div>

      <div className="mt-3">
        <span
          className={clsx(
            'inline-block px-4 py-1.5 rounded-full text-sm font-bold font-mono border',
            result.risk_level === 'low' && 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400',
            result.risk_level === 'suspicious' && 'bg-amber-500/10 border-amber-500/30 text-amber-400',
            result.risk_level === 'high' && 'bg-red-500/10 border-red-500/30 text-red-400',
          )}
        >
          {riskLabel}
        </span>
      </div>

      <p className="text-xs text-slate-600 mt-3 font-mono">
        Prototype thresholds: 70+ LOW · 40–69 SUSPICIOUS · &lt;40 HIGH RISK
      </p>
    </div>
  );
}
