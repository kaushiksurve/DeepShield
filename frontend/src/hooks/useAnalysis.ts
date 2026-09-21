import { useState, useCallback, useRef } from 'react';
import { uploadVideo, getAnalysis, getDemoResult } from '../services/api';
import type { AnalysisResult, PipelineStep, PipelineStepStatus } from '../types/analysis';

const PIPELINE_STEPS: PipelineStep[] = [
  { id: 'input', label: '01  Media Input', icon: 'Upload', status: 'pending' },
  { id: 'preprocess', label: '02  Preprocessing', icon: 'Cpu', status: 'pending' },
  { id: 'face', label: '03  Face Analysis', icon: 'ScanFace', status: 'pending' },
  { id: 'audio', label: '04  Audio Analysis', icon: 'AudioWaveform', status: 'pending' },
  { id: 'lipsync', label: '05  Lip-Speech Analysis', icon: 'Mic', status: 'pending' },
  { id: 'temporal', label: '06  Temporal Analysis', icon: 'Activity', status: 'pending' },
  { id: 'liveness', label: '07  Liveness Analysis', icon: 'Eye', status: 'pending' },
  { id: 'fusion', label: '08  Cross-Modal Fusion', icon: 'GitMerge', status: 'pending' },
  { id: 'verdict', label: '09  Final Verdict', icon: 'Shield', status: 'pending' },
];

const STEP_TIMING = [400, 800, 1800, 1500, 2000, 1200, 1000, 800, 600]; // ms per step

export function useAnalysis() {
  const [steps, setSteps] = useState<PipelineStep[]>(PIPELINE_STEPS.map(s => ({ ...s })));
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const resetSteps = useCallback(() => {
    setSteps(PIPELINE_STEPS.map(s => ({ ...s, status: 'pending' as PipelineStepStatus })));
  }, []);

  const setStepStatus = useCallback((index: number, status: PipelineStepStatus) => {
    setSteps(prev => prev.map((s, i) => i === index ? { ...s, status } : s));
  }, []);

  const animatePipeline = useCallback(async () => {
    for (let i = 0; i < PIPELINE_STEPS.length; i++) {
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

    try {
      // Start pipeline animation
      setStepStatus(0, 'processing');
      const { analysis_id } = await uploadVideo(file);
      setStepStatus(0, 'complete');

      // Animate remaining steps while polling
      animatePipeline();

      // Poll for completion
      const poll = async () => {
        try {
          const { status, result: analysisResult } = await getAnalysis(analysis_id);
          if (status === 'complete' && analysisResult) {
            setResult(analysisResult);
            setIsAnalyzing(false);
            // Mark all steps complete
            setSteps(PIPELINE_STEPS.map(s => ({ ...s, status: 'complete' as PipelineStepStatus })));
          } else if (status === 'error') {
            setError('Analysis failed. Please try another video.');
            setIsAnalyzing(false);
            setSteps(prev => prev.map(s => s.status === 'processing' ? { ...s, status: 'failed' as PipelineStepStatus } : s));
          } else {
            pollRef.current = setTimeout(poll, 2000);
          }
        } catch {
          pollRef.current = setTimeout(poll, 3000);
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
  }, [animatePipeline, resetSteps, setStepStatus]);

  const loadDemoResult = useCallback(async (scenario: 'genuine' | 'suspicious' | 'high_risk') => {
    setIsAnalyzing(true);
    setResult(null);
    setError(null);
    resetSteps();

    // Fast demo animation
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
    setIsAnalyzing(false);
    setResult(null);
    setError(null);
    resetSteps();
  }, [resetSteps]);

  return { steps, isAnalyzing, result, error, analyzeVideo, loadDemoResult, reset };
}
