import React from 'react';
import { Download, FileText } from 'lucide-react';
import type { AnalysisResult } from '../types/analysis';
import { getRiskLabel, formatTimestamp } from '../utils/formatters';

interface Props {
  result: AnalysisResult;
}

export function ReportGenerator({ result }: Props) {
  const generateReport = () => {
    const lines: string[] = [];
    const now = new Date().toISOString();

    lines.push('═'.repeat(60));
    lines.push('  DEEPSHIELD — ANALYSIS REPORT');
    lines.push('  Multi-Layer Deepfake & Identity Verification');
    lines.push('  Team AI Warriors | Hackathon Prototype');
    lines.push('═'.repeat(60));
    lines.push('');
    lines.push(`Analysis ID : ${result.analysis_id}`);
    lines.push(`Date/Time   : ${now}`);
    lines.push(`Filename    : ${result.filename}`);
    if (result.is_demo) lines.push('** DEMO / SIMULATED RESULT — NOT A REAL PREDICTION **');
    lines.push('');
    lines.push('─'.repeat(40));
    lines.push('JOINT TRUST SCORE');
    lines.push('─'.repeat(40));
    lines.push(`Score      : ${result.trust_score} / 100`);
    lines.push(`Risk Level : ${getRiskLabel(result.risk_level)}`);
    lines.push(`Thresholds : 70+ LOW RISK · 40–69 SUSPICIOUS · <40 HIGH RISK (prototype)`);
    lines.push('');

    if (result.video_metadata) {
      lines.push('─'.repeat(40));
      lines.push('VIDEO METADATA');
      lines.push('─'.repeat(40));
      lines.push(`Duration   : ${result.video_metadata.duration}s`);
      lines.push(`Resolution : ${result.video_metadata.width}x${result.video_metadata.height}`);
      lines.push(`FPS        : ${result.video_metadata.fps}`);
      lines.push('');
    }

    lines.push('─'.repeat(40));
    lines.push('MODULE SCORES');
    lines.push('─'.repeat(40));
    for (const [key, mod] of Object.entries(result.module_scores)) {
      lines.push(`${mod.label.padEnd(28)}: ${mod.score.toFixed(1)}/100 [${mod.risk.toUpperCase()}] (confidence: ${Math.round(mod.confidence * 100)}%, weight: ${mod.weight}%)`);
    }
    lines.push('');

    if (result.evidence.length > 0) {
      lines.push('─'.repeat(40));
      lines.push('DETECTED ANOMALIES');
      lines.push('─'.repeat(40));
      for (const ev of result.evidence) {
        lines.push(`[${ev.module}] ${ev.text}`);
      }
      lines.push('');
    }

    if (result.timeline.length > 0) {
      lines.push('─'.repeat(40));
      lines.push('SUSPICIOUS TIMESTAMPS');
      lines.push('─'.repeat(40));
      for (const ev of result.timeline) {
        lines.push(`${formatTimestamp(ev.time)}  ${ev.module}  [${ev.risk.toUpperCase()}]`);
      }
      lines.push('');
    }

    if (result.explanation) {
      lines.push('─'.repeat(40));
      lines.push('EXPLANATION');
      lines.push('─'.repeat(40));
      lines.push(result.explanation.intro);
      lines.push('');
      lines.push(result.explanation.summary);
      lines.push('');
    }

    lines.push('─'.repeat(40));
    lines.push('DISCLAIMER');
    lines.push('─'.repeat(40));
    lines.push('This is a hackathon prototype risk assessment.');
    lines.push('Results should NOT be treated as definitive proof of media authenticity.');
    lines.push('DeepShield uses heuristic analysis, not a trained deepfake detection model.');
    lines.push('Thresholds are experimental and not validated on labeled datasets.');
    lines.push('');
    lines.push('═'.repeat(60));

    const blob = new Blob([lines.join('\n')], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `deepshield_report_${result.analysis_id}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <button
      onClick={generateReport}
      className="flex items-center gap-2 px-5 py-2.5 rounded-xl border border-violet-500/30 text-violet-400 hover:bg-violet-500/10 transition-all text-sm font-medium"
    >
      <Download size={15} />
      Generate Report
    </button>
  );
}
