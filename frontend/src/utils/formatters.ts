export function formatTimestamp(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m.toString().padStart(2, '0')}:${s.toFixed(1).padStart(4, '0')}`;
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

export function getRiskColor(risk: string): string {
  switch (risk) {
    case 'low': return 'text-emerald-400';
    case 'suspicious': case 'medium': return 'text-amber-400';
    case 'high': return 'text-red-400';
    default: return 'text-slate-400';
  }
}

export function getRiskBgColor(risk: string): string {
  switch (risk) {
    case 'low': return 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400';
    case 'suspicious': case 'medium': return 'bg-amber-500/10 border-amber-500/30 text-amber-400';
    case 'high': return 'bg-red-500/10 border-red-500/30 text-red-400';
    default: return 'bg-slate-500/10 border-slate-500/30 text-slate-400';
  }
}

export function getScoreColor(score: number): string {
  if (score >= 70) return '#10b981';
  if (score >= 40) return '#f59e0b';
  return '#ef4444';
}

export function getRiskLabel(risk: string): string {
  switch (risk) {
    case 'low': return 'LOW RISK';
    case 'suspicious': return 'SUSPICIOUS';
    case 'high': return 'HIGH RISK';
    case 'error': return 'ERROR';
    default: return risk.toUpperCase();
  }
}
