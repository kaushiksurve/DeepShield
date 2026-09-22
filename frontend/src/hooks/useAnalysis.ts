import { useState, useCallback, useRef } from 'react';
import { uploadVideo, getAnalysis, getDemoResult } from '../services/api';
import type { AnalysisResult, PipelineStep, PipelineStepStatus } from '../types/analysis';

const PIPELINE_STEPS: PipelineStep[] = [
  { id: 'input',      label: '01  Media Input',        icon: 'Upload',        status: 'pending' },
  { id: 'preprocess', label: '02  Preprocessing',      icon: 'Cpu',           status: 'pending' },
  { id: 'face',       label: '03  Face Analysis',      icon: 'ScanFace',      status: 'pending' },
  { id: 'audio',      label: '04  Audio Analysis',     icon: 'AudioWaveform', status: 'pending' },
  { id: 'lipsync',    label: '05  Lip-Speech Analysis',icon: 'Mic',           status: 'pending' },
  { id: 'temporal',   label: '06  Temporal Analysis',  icon: 'Activity',      status: 'pending' },
  { id: 'liveness',   label: '07  Liveness Analysis',  icon: 'Eye',           status: 'pending' },
  { id: 'fusion',     label: '08  Cross-Modal Fusion', icon: 'GitMerge',      status: 'pending' },
  { id: 'verdict',    label: '09  Final Verdict',      icon: 'Shield',        status: 'pending' },
];

// ms per step for the visual animation (steps 1-8, step 0 is real upload)
const STEP_TIMING = [0, 800, 1800, 1500, 2000, 1200, 1000, 800, 600];

const MAX_POLL_ATTEMPTS = 60; // 60 × 3s = 3 minutes max

export function useAnalysis() {
  const [steps, setSteps] = useState<PipelineStep[]>(PIPELINE_STEPS.map(s => ({ ...s })));
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pollAttempts = useRef(0);

  const resetSteps = useCallback(() => {
    setSteps(PIPELINE_STEPS.map(s => ({ ...s, status: 'pending' as PipelineStepStatus })));
  }, []);

  const setStepStatus = useCallback((index: number, status: PipelineStepStatus) => {
    setSteps(prev => prev.map((s, i) => i === index ? { ...s, status } : s));
  }, []);

  /** Animate steps 1–8 while upload + analysis runs in the background. */
  const animateRemainingSteps = useCallback(async () => {
    for (let i = 1; i < PIPELINE_STEPS.length; i++) {
      setStepStatus(i, 'processing');
      await new Promise(r => setTimeout(r, STEP_TIMING[i]));
      setStepStatus(i, 'complete');
    }
  }, [setStepStatus]);

  const analyzeVideo = useCallback(async (file: File) => {
    setIsAnalyzing(true);
    setResult(null);
    setError(null);
    resetSteps();
    pollAttempts.current = 0;

    try {
      // Step 0: real upload
      setStepStatus(0, 'processing');
      const { analysis_id } = await uploadVideo(file);
      setStepStatus(0, 'complete');

      // Steps 1-8: visual animation (non-blocking, concurrent with polling)
      animateRemainingSteps();

      // Poll for completion
      const poll = async () => {
        pollAttempts.current += 1;
        if (pollAttempts.current > MAX_POLL_ATTEMPTS) {
          setError('Analysis timed out. The server may be busy — please try again.');
          setIsAnalyzing(false);
          setSteps(prev => prev.map(s => s.status === 'processing' ? { ...s, status: 'failed' as PipelineStepStatus } : s));
          return;
        }

        try {
          const { status, result: analysisResult } = await getAnalysis(analysis_id);
          if (status === 'complete' && analysisResult) {
            setResult(analysisResult);
            setIsAnalyzing(false);
            setSteps(PIPELINE_STEPS.map(s => ({ ...s, status: 'complete' as PipelineStepStatus })));
          } else if (status === 'error') {
            setError('Analysis failed on the server. Please try another video.');
            setIsAnalyzing(false);
            setSteps(prev => prev.map(s => s.status === 'processing' ? { ...s, status: 'failed' as PipelineStepStatus } : s));
          } else {
            pollRef.current = setTimeout(poll, 3000);
          }
        } catch {
          pollRef.current = setTimeout(poll, 4000);
        }
      };
      poll();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Upload failed';
      const axiosError = err as { response?: { data?: { detail?: string } } };
      setError(axiosError.response?.data?.detail || msg);
      setIsAnalyzing(false);
      setSteps(prev => prev.map((s, i) => i === 0 ? { ...s, status: 'failed' as PipelineStepStatus } : s));
    }
  }, [animateRemainingSteps, resetSteps, setStepStatus]);

  const loadDemoResult = useCallback(async (scenario: 'genuine' | 'suspicious' | 'high_risk') => {
    setIsAnalyzing(true);
    setResult(null);
    setError(null);
    resetSteps();

    for (let i = 0; i < PIPELINE_STEPS.length; i++) {
      setStepStatus(i, 'processing');
      await new Promise(r => setTimeout(r, 200));
      setStepStatus(i, 'complete');
    }

    try {
      const demoResult = await getDemoResult(scenario);
      setResult(demoResult);
    } catch {
      setError('Failed to load demo result.');
    } finally {
      setIsAnalyzing(false);
    }
  }, [resetSteps, setStepStatus]);

  const reset = useCallback(() => {
    if (pollRef.current) clearTimeout(pollRef.current);
    pollAttempts.current = 0;
    setIsAnalyzing(false);
    setResult(null);
    setError(null);
    resetSteps();
  }, [resetSteps]);

  return { steps, isAnalyzing, result, error, analyzeVideo, loadDemoResult, reset };
}
