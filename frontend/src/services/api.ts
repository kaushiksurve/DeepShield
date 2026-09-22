import axios from 'axios';
import type { AnalysisResult } from '../types/analysis';

// Call Render backend directly — Vercel's proxy corrupts multipart file uploads.
// CORS is open on the backend (allow_origins=["*"]).
const RENDER_URL = 'https://deepshield-64ic.onrender.com';

const api = axios.create({
  baseURL: `${RENDER_URL}/api`,
  timeout: 300_000, // 5 minutes for large videos
});

export async function uploadVideo(file: File): Promise<{ analysis_id: string; status: string }> {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await api.post('/analyze', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function getAnalysis(analysisId: string): Promise<{ status: string; result?: AnalysisResult }> {
  const { data } = await api.get(`/analysis/${analysisId}`);
  return {
    status: data.status,
    result: data.result as AnalysisResult | undefined,
  };
}

export async function getDemoResult(scenario: 'genuine' | 'suspicious' | 'high_risk'): Promise<AnalysisResult> {
  const { data } = await api.get(`/demo/${scenario}`);
  return data as AnalysisResult;
}

export async function checkHealth(): Promise<boolean> {
  try {
    const { data } = await api.get('/health');
    return data.status === 'ok';
  } catch {
    return false;
  }
}
