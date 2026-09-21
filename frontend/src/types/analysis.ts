export type RiskLevel = 'low' | 'medium' | 'suspicious' | 'high' | 'error';

export interface ModuleResult {
  label: string;
  score: number;
  confidence: number;
  risk: RiskLevel;
  evidence: string[];
  timestamps: number[];
  weight: number;
  detail?: Record<string, unknown>;
}

export interface TimelineEvent {
  time: number;
  module: string;
  risk: RiskLevel;
}

export interface EvidenceItem {
  module: string;
  text: string;
}

export interface Explanation {
  intro: string;
  findings: string[];
  passing_modules: string[];
  timeline_narrative: string[];
  summary: string;
  limitations: string[];
  note?: string;
}

export interface VideoMetadata {
  fps: number;
  frame_count: number;
  duration: number;
  width: number;
  height: number;
}

export interface AnalysisResult {
  analysis_id: string;
  filename: string;
  trust_score: number;
  risk_level: RiskLevel;
  module_scores: Record<string, ModuleResult>;
  evidence: EvidenceItem[];
  timeline: TimelineEvent[];
  explanation: Explanation;
  video_metadata?: VideoMetadata;
  processing_time_s?: number;
  is_demo: boolean;
  demo_note?: string;
  note?: string;
}

export interface AnalysisResponse {
  analysis_id: string;
  status: 'processing' | 'complete' | 'error';
  filename?: string;
  file_size?: number;
  result?: AnalysisResult;
}

export type PipelineStepStatus = 'pending' | 'processing' | 'complete' | 'failed';

export interface PipelineStep {
  id: string;
  label: string;
  icon: string;
  status: PipelineStepStatus;
}
