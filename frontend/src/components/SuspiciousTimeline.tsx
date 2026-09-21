import React from 'react';
import { AlertTriangle, Clock } from 'lucide-react';
import type { TimelineEvent } from '../types/analysis';
import { formatTimestamp } from '../utils/formatters';
import clsx from 'clsx';

interface Props {
  events: TimelineEvent[];
  onSeek?: (time: number) => void;
}

export function SuspiciousTimeline({ events, onSeek }: Props) {
  if (events.length === 0) {
    return (
      <div className="glass rounded-2xl p-6 text-center">
        <div className="w-10 h-10 bg-emerald-500/10 rounded-xl flex items-center justify-center mx-auto mb-3">
          <Clock size={18} className="text-emerald-400" />
        </div>
        <p className="text-slate-400 text-sm">No suspicious timestamps detected.</p>
      </div>
    );
  }

  return (
    <div className="glass rounded-2xl p-4">
      <p className="text-xs font-mono text-slate-500 uppercase tracking-wider mb-4">Risk Timeline</p>
      <div className="space-y-2">
        {events.map((ev, i) => (
          <button
            key={i}
            className={clsx(
              'w-full flex items-center gap-3 p-3 rounded-xl border text-left transition-all hover:scale-[1.01]',
              ev.risk === 'high'
                ? 'bg-red-500/5 border-red-500/20 hover:bg-red-500/10'
                : 'bg-amber-500/5 border-amber-500/15 hover:bg-amber-500/10',
            )}
            onClick={() => onSeek?.(ev.time)}
          >
            <AlertTriangle
              size={14}
              className={ev.risk === 'high' ? 'text-red-400 flex-shrink-0' : 'text-amber-400 flex-shrink-0'}
            />
            <span className="font-mono text-sm text-slate-200 flex-shrink-0">
              {formatTimestamp(ev.time)}
            </span>
            <span className="text-xs text-slate-400 truncate">{ev.module}</span>
            <span className={clsx(
              'ml-auto text-[10px] font-mono px-1.5 py-0.5 rounded border flex-shrink-0',
              ev.risk === 'high' ? 'text-red-400 border-red-500/30 bg-red-500/10' : 'text-amber-400 border-amber-500/30 bg-amber-500/10'
            )}>
              {ev.risk.toUpperCase()}
            </span>
          </button>
        ))}
      </div>
      {onSeek && (
        <p className="text-[10px] font-mono text-slate-600 mt-3 text-center">Click event to seek video</p>
      )}
    </div>
  );
}
