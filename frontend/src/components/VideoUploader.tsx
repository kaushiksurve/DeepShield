import React, { useState, useRef, useCallback, useEffect } from 'react';
import { Upload, Film, X, Play, AlertCircle } from 'lucide-react';
import { formatFileSize, formatDuration } from '../utils/formatters';
import clsx from 'clsx';

interface Props {
  onAnalyze: (file: File) => void;
  isAnalyzing: boolean;
  disabled?: boolean;
}

export function VideoUploader({ onAnalyze, isAnalyzing, disabled }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [duration, setDuration] = useState<number>(0);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  const ALLOWED = ['video/mp4', 'video/quicktime', 'video/webm', 'video/avi'];
  const MAX_MB = 100;

  const handleFile = useCallback((f: File) => {
    setError(null);
    if (!ALLOWED.includes(f.type) && !f.name.match(/\.(mp4|mov|webm|avi)$/i)) {
      setError('Unsupported format. Please upload MP4, MOV, WEBM, or AVI.');
      return;
    }
    if (f.size > MAX_MB * 1024 * 1024) {
      setError(`File too large. Maximum size is ${MAX_MB} MB.`);
      return;
    }
    setFile(f);
    const url = URL.createObjectURL(f);
    setPreviewUrl(url);
  }, []);

  useEffect(() => {
    return () => { if (previewUrl) URL.revokeObjectURL(previewUrl); };
  }, [previewUrl]);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  }, [handleFile]);

  const clear = () => {
    setFile(null);
    setPreviewUrl(null);
    setDuration(0);
    setError(null);
    if (inputRef.current) inputRef.current.value = '';
  };

  return (
    <div className="space-y-4">
      {!file ? (
        <div
          className={clsx(
            'relative border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all duration-300',
            dragOver
              ? 'border-violet-500 bg-violet-500/10 scale-[1.01]'
              : 'border-white/10 hover:border-violet-500/50 hover:bg-white/2',
          )}
          onDragOver={e => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
        >
          <input
            ref={inputRef}
            type="file"
            accept="video/mp4,video/quicktime,video/webm,video/avi,.mp4,.mov,.webm,.avi"
            className="hidden"
            onChange={e => { if (e.target.files?.[0]) handleFile(e.target.files[0]); }}
          />
          <div className="flex flex-col items-center gap-4">
            <div className={clsx(
              'w-16 h-16 rounded-2xl flex items-center justify-center transition-all',
              dragOver ? 'bg-violet-500/20 glow-purple' : 'bg-white/5'
            )}>
              <Upload size={28} className={dragOver ? 'text-violet-400' : 'text-slate-500'} />
            </div>
            <div>
              <p className="text-slate-300 font-medium">Drop video here or <span className="text-violet-400">browse</span></p>
              <p className="text-slate-600 text-sm mt-1">MP4 · MOV · WEBM · AVI — max {MAX_MB} MB</p>
            </div>
          </div>
        </div>
      ) : (
        <div className="glass rounded-2xl overflow-hidden">
          {/* Video Preview */}
          <div className="relative bg-black aspect-video">
            <video
              ref={videoRef}
              src={previewUrl || ''}
              className="w-full h-full object-contain"
              controls
              onLoadedMetadata={e => setDuration((e.target as HTMLVideoElement).duration)}
            />
            <button
              onClick={clear}
              className="absolute top-2 right-2 w-8 h-8 bg-black/60 backdrop-blur rounded-full flex items-center justify-center hover:bg-red-500/50 transition-colors"
            >
              <X size={14} className="text-white" />
            </button>
          </div>

          {/* File info */}
          <div className="p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-violet-500/10 rounded-xl flex items-center justify-center">
                <Film size={18} className="text-violet-400" />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-200 truncate max-w-[200px]">{file.name}</p>
                <p className="text-xs text-slate-500 font-mono">
                  {formatFileSize(file.size)}
                  {duration > 0 && ` · ${formatDuration(duration)}`}
                </p>
              </div>
            </div>
            <button
              onClick={() => onAnalyze(file)}
              disabled={isAnalyzing || !!disabled}
              className={clsx(
                'flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold text-sm transition-all',
                isAnalyzing
                  ? 'bg-violet-500/30 text-violet-300 cursor-not-allowed'
                  : 'bg-gradient-to-r from-violet-600 to-cyan-600 text-white hover:from-violet-500 hover:to-cyan-500 glow-purple hover:scale-105 active:scale-95'
              )}
            >
              {isAnalyzing ? (
                <><span className="w-4 h-4 border-2 border-violet-300/30 border-t-violet-300 rounded-full animate-spin" />Analyzing...</>
              ) : (
                <><Play size={15} />Analyze Video</>
              )}
            </button>
          </div>
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3">
          <AlertCircle size={16} />
          {error}
        </div>
      )}
    </div>
  );
}
