import React from 'react';
import { Upload, Cpu, ScanFace, AudioWaveform, Mic, Activity, Eye, GitMerge, Shield, Check, X, Loader } from 'lucide-react';
import type { PipelineStep } from '../types/analysis';
import clsx from 'clsx';

const ICON_MAP: Record<string, React.ReactNode> = {
  Upload: <Upload size={14} />,
  Cpu: <Cpu size={14} />,
  ScanFace: <ScanFace size={14} />,
  AudioWaveform: <AudioWaveform size={14} />,
  Mic: <Mic size={14} />,
  Activity: <Activity size={14} />,
  Eye: <Eye size={14} />,
  GitMerge: <GitMerge size={14} />,
  Shield: <Shield size={14} />,
};

interface Props {
  steps: PipelineStep[];
}

export function AnalysisPipeline({ steps }: Props) {
  return (
    <div className="glass rounded-2xl p-4">
      <p className="text-xs font-mono text-slate-500 mb-3 uppercase tracking-wider">Analysis Pipeline</p>
      <div className="space-y-1.5">
        {steps.map((step, i) => (
          <PipelineRow key={step.id} step={step} index={i} />
        ))}
      </div>
    </div>
  );
}

function PipelineRow({ step, index }: { step: PipelineStep; index: number }) {
  const isComplete = step.status === 'complete';
  const isProcessing = step.status === 'processing';
  const isFailed = step.status === 'failed';
  const isPending = step.status === 'pending';

  return (
    <div className={clsx(
      'flex items-center gap-3 px-3 py-2 rounded-xl transition-all duration-300',
      isProcessing && 'bg-violet-500/10 border border-violet-500/20',
      isComplete && 'bg-white/2',
      isFailed && 'bg-red-500/10 border border-red-500/20',
      isPending && 'opacity-40',
    )}>
      {/* Step number/status indicator */}
      <div className={clsx(
        'w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 transition-all',
        isComplete && 'bg-emerald-500/20 text-emerald-400',
        isProcessing && 'bg-violet-500/20 text-violet-400',
        isFailed && 'bg-red-500/20 text-red-400',
        isPending && 'bg-white/5 text-slate-600',
      )}>
        {isComplete ? <Check size={10} strokeWidth={3} /> :
         isProcessing ? <Loader size={10} className="animate-spin" /> :
         isFailed ? <X size={10} strokeWidth={3} /> :
         <span className="text-[9px] font-mono">{String(index + 1).padStart(2, '0')}</span>}
      </div>

      {/* Icon */}
      <div className={clsx(
        'transition-colors',
        isComplete && 'text-emerald-400',
        isProcessing && 'text-violet-400',
        isFailed && 'text-red-400',
        isPending && 'text-slate-600',
      )}>
        {ICON_MAP[step.icon]}
      </div>

      {/* Label */}
      <span className={clsx(
        'text-xs font-mono flex-1',
        isComplete && 'text-slate-300',
        isProcessing && 'text-violet-300',
        isFailed && 'text-red-300',
        isPending && 'text-slate-600',
      )}>
        {step.label}
      </span>

      {/* Status badge */}
      {isProcessing && (
        <span className="text-[10px] font-mono text-violet-400 animate-pulse">RUNNING</span>
      )}
      {isComplete && (
        <span className="text-[10px] font-mono text-emerald-400">DONE</span>
      )}
      {isFailed && (
        <span className="text-[10px] font-mono text-red-400">FAIL</span>
      )}
    </div>
  );
}
