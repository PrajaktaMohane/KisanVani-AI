import React from 'react';
import { Mic, Square, Loader2, Volume2 } from 'lucide-react';

export default function VoiceRecorder({
  isRecording,
  onStart,
  onStop,
  isLoading,
  duration,
  selectedLang
}) {
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  return (
    <div className="flex flex-col items-center justify-center py-6">
      {/* Visual Ripple & Mic Button */}
      <div className="relative flex items-center justify-center">
        {isRecording && (
          <>
            <div className="absolute w-36 h-36 rounded-full bg-red-500/20 animate-ping pointer-events-none" />
            <div className="absolute w-28 h-28 rounded-full bg-red-500/30 animate-pulse pointer-events-none" />
          </>
        )}

        <button
          onClick={isRecording ? onStop : onStart}
          disabled={isLoading}
          className={`relative z-10 w-24 h-24 rounded-full flex flex-col items-center justify-center text-white shadow-xl transition-all transform active:scale-95 ${
            isLoading
              ? 'bg-stone-400 cursor-not-allowed'
              : isRecording
              ? 'bg-red-600 hover:bg-red-700 ring-4 ring-red-300 shadow-red-600/40'
              : 'bg-gradient-to-tr from-agri-700 via-agri-600 to-agri-500 hover:from-agri-800 hover:to-agri-600 shadow-agri-600/30'
          }`}
          aria-label={isRecording ? 'Stop Recording' : 'Start Recording'}
        >
          {isLoading ? (
            <Loader2 className="w-9 h-9 animate-spin text-white" />
          ) : isRecording ? (
            <Square className="w-8 h-8 fill-current text-white" />
          ) : (
            <Mic className="w-10 h-10 text-white stroke-[2.2]" />
          )}
        </button>
      </div>

      {/* Voice Status Text */}
      <div className="mt-4 text-center">
        {isLoading ? (
          <div className="flex items-center space-x-2 text-stone-600 text-sm font-medium">
            <span className="inline-block w-2 h-2 rounded-full bg-agri-500 animate-bounce" />
            <span className="inline-block w-2 h-2 rounded-full bg-agri-500 animate-bounce [animation-delay:0.2s]" />
            <span className="inline-block w-2 h-2 rounded-full bg-agri-500 animate-bounce [animation-delay:0.4s]" />
            <span>KisanVani is formulating grounded advice...</span>
          </div>
        ) : isRecording ? (
          <div className="space-y-1">
            <div className="flex items-center justify-center space-x-2 text-red-600 font-bold text-sm">
              <span className="w-2.5 h-2.5 rounded-full bg-red-600 animate-pulse" />
              <span>Listening in {selectedLang?.nativeName || 'Hindi'}...</span>
            </div>
            <p className="text-xs font-mono text-stone-500">{formatTime(duration)}</p>
          </div>
        ) : (
          <div className="space-y-1">
            <p className="text-sm font-bold text-stone-800">
              बोलने के लिए माइक दबाएं (Tap to Speak)
            </p>
            <p className="text-xs text-stone-500">
              Ask about pests, fertilizer doses, disease symptoms, or weather
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
