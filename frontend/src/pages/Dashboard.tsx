import React, { useRef } from 'react';
import { Shield, Zap, Lock, Eye } from 'lucide-react';
import { VideoUploader } from '../components/VideoUploader';
import { AnalysisPipeline } from '../components/AnalysisPipeline';
import { TrustScoreGauge } from '../components/TrustScoreGauge';
import { ModuleScoreCard } from '../components/ModuleScoreCard';
import { SuspiciousTimeline } from '../components/SuspiciousTimeline';
import { ExplainabilityPanel } from '../components/ExplainabilityPanel';
import { ReportGenerator } from '../components/ReportGenerator';
import { useAnalysis } from '../hooks/useAnalysis';

const MODULE_ORDER = ['face', 'audio', 'lipsync', 'temporal', 'liveness', 'behavior'];

export function Dashboard() {
  const { steps, isAnalyzing, result, error, analyzeVideo, loadDemoResult, reset } = useAnalysis();
  const videoRef = useRef<HTMLVideoElement>(null);

  const handleSeek = (time: number) => {
    // For demo results there's no real video, but for real results the user has their video
    // We can't seek an uploaded video after analysis without re-storing it, so we skip
  };

  return (
    <div className="min-h-screen bg-navy-900">
      <div className="scan-line" />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-8">

        {/* Hero */}
        {!result && !isAnalyzing && (
          <div className="text-center py-8 animate-fade-in">
            <h2 className="text-4xl sm:text-5xl font-bold mb-4">
              <span className="gradient-text">Multi-Signal</span>
              <span className="text-slate-200"> Deepfake</span>
              <br />
              <span className="text-slate-200">Detection</span>
            </h2>
            <p className="text-slate-400 text-lg max-w-xl mx-auto">
              Six independent analysis channels fused into one transparent Joint Trust Score.
            </p>

            {/* Feature pills */}
            <div className="flex flex-wrap justify-center gap-3 mt-6">
              {[
                { icon: <Shield size={12} />, label: 'Face Analysis' },
                { icon: <Zap size={12} />, label: 'Audio Analysis' },
                { icon: <Eye size={12} />, label: 'Lip-Speech Sync' },
                { icon: <Lock size={12} />, label: 'Liveness Check' },
              ].map((f, i) => (
                <div key={i} className="flex items-center gap-1.5 text-xs text-slate-400 bg-white/3 border border-white/8 rounded-full px-3 py-1.5">
                  <span className="text-violet-400">{f.icon}</span>
                  {f.label}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Main grid */}
        <div className="grid lg:grid-cols-3 gap-6">

          {/* Left column: Upload + Pipeline */}
          <div className="lg:col-span-1 space-y-4">
            <div className="glass rounded-2xl p-5">
              <p className="text-xs font-mono text-slate-500 uppercase tracking-wider mb-4">Upload Video</p>
              <VideoUploader onAnalyze={analyzeVideo} isAnalyzing={isAnalyzing} />

              {/* Demo mode */}
              <div className="mt-5 border-t border-white/5 pt-4">
                <p className="text-xs font-mono text-slate-500 mb-3 uppercase tracking-wider">Demo Mode</p>
                <div className="grid grid-cols-3 gap-2">
                  {([
                    { id: 'genuine', label: 'Genuine', color: 'emerald' },
                    { id: 'suspicious', label: 'Suspicious', color: 'amber' },
                    { id: 'high_risk', label: 'High Risk', color: 'red' },
                  ] as const).map(s => (
                    <button
                      key={s.id}
                      onClick={() => loadDemoResult(s.id)}
                      disabled={isAnalyzing}
                      className={`text-xs py-2 px-2 rounded-xl border font-mono transition-all disabled:opacity-40
                        ${
                          s.color === 'emerald'
                            ? 'border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/10'
                            : s.color === 'amber'
                            ? 'border-amber-500/30 text-amber-400 hover:bg-amber-500/10'
                            : 'border-red-500/30 text-red-400 hover:bg-red-500/10'
                        }`}
                    >
                      {s.label}
                    </button>
                  ))}
                </div>
                <p className="text-[10px] font-mono text-slate-600 mt-2 text-center">
                  Demo results are simulated and clearly labeled
                </p>
              </div>
            </div>

            <AnalysisPipeline steps={steps} />
          </div>

          {/* Right column: Results */}
          <div className="lg:col-span-2 space-y-5">

            {/* Error */}
            {error && (
              <div className="glass rounded-2xl p-5 border border-red-500/20 bg-red-500/5">
                <p className="text-red-400 text-sm">⚠ {error}</p>
                <button onClick={reset} className="text-xs text-slate-500 hover:text-slate-400 mt-2">Try again</button>
              </div>
            )}

            {/* Processing placeholder */}
            {isAnalyzing && !result && (
              <div className="glass rounded-2xl p-10 text-center">
                <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-violet-500/10 flex items-center justify-center">
                  <Shield size={28} className="text-violet-400 animate-pulse" />
                </div>
                <p className="text-slate-300 font-medium">Analyzing video...</p>
                <p className="text-slate-600 text-sm mt-1">Running multi-layer verification pipeline</p>
              </div>
            )}

            {/* Results */}
            {result && (
              <div className="space-y-5 animate-fade-in">
                {/* Demo banner */}
                {result.is_demo && (
                  <div className="flex items-center gap-2 bg-amber-500/10 border border-amber-500/20 rounded-xl px-4 py-3">
                    <span className="text-amber-400 text-sm font-mono">⚠ DEMO / SIMULATED RESULT</span>
                    <span className="text-slate-500 text-xs">— Not a real AI prediction. For demonstration only.</span>
                  </div>
                )}

                {/* Score + Timeline */}
                <div className="grid sm:grid-cols-2 gap-5">
                  <TrustScoreGauge result={result} />
                  <SuspiciousTimeline events={result.timeline} onSeek={handleSeek} />
                </div>

                {/* Module scores */}
                <div>
                  <p className="text-xs font-mono text-slate-500 uppercase tracking-wider mb-3">Module Analysis</p>
                  <div className="space-y-2">
                    {MODULE_ORDER.map(key =>
                      result.module_scores[key] ? (
                        <ModuleScoreCard
                          key={key}
                          moduleKey={key}
                          result={result.module_scores[key]}
                        />
                      ) : null
                    )}
                  </div>
                </div>

                {/* Explainability */}
                {result.explanation && (
                  <ExplainabilityPanel explanation={result.explanation} />
                )}

                {/* Actions */}
                <div className="flex items-center justify-between">
                  <ReportGenerator result={result} />
                  <button
                    onClick={reset}
                    className="text-xs text-slate-500 hover:text-slate-400 transition-colors"
                  >
                    ← New Analysis
                  </button>
                </div>

                {/* Prototype note */}
                <p className="text-[10px] font-mono text-slate-700 text-center">
                  {result.note}
                </p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
