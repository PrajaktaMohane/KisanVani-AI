import React, { useState } from 'react';
import { ShieldAlert, BookOpen, ThumbsUp, ThumbsDown, CheckCircle2, ChevronDown, ChevronUp } from 'lucide-react';
import AudioPlayer from './AudioPlayer';

export default function AdvisoryCard({
  queryText,
  detectedLanguage,
  answerText,
  audioBase64,
  sources = [],
  latencyMetrics,
  isPlaying,
  playbackSpeed,
  onToggleAudio,
  onChangeSpeed,
  onFeedback
}) {
  const [showSources, setShowSources] = useState(false);
  const [feedbackGiven, setFeedbackGiven] = useState(null);

  const handleFeedback = (isHelpful) => {
    setFeedbackGiven(isHelpful);
    if (onFeedback) onFeedback(isHelpful);
  };

  return (
    <div className="bg-white rounded-3xl p-5 shadow-xl border border-stone-200/80 space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-300">
      {/* Farmer Query Badge */}
      <div className="bg-stone-50 rounded-2xl p-3.5 border border-stone-200">
        <div className="flex items-center justify-between text-xs text-stone-500 mb-1">
          <span className="font-semibold uppercase tracking-wider text-agri-700">Farmer Voice Query</span>
          <span className="bg-stone-200/80 px-2 py-0.5 rounded-md font-mono text-[10px] uppercase">
            {detectedLanguage || 'HI'}
          </span>
        </div>
        <p className="text-stone-800 text-sm font-medium italic">"{queryText}"</p>
      </div>

      {/* Audio Playback Bar if voice response available */}
      {audioBase64 && (
        <AudioPlayer
          isPlaying={isPlaying}
          onToggle={onToggleAudio}
          speed={playbackSpeed}
          onSpeedChange={onChangeSpeed}
        />
      )}

      {/* Answer Content */}
      <div className="prose prose-stone max-w-none text-stone-800 text-sm leading-relaxed whitespace-pre-line font-normal">
        {answerText}
      </div>

      {/* Grounded Sources Accordion */}
      {sources && sources.length > 0 && (
        <div className="border-t border-stone-100 pt-3">
          <button
            onClick={() => setShowSources(!showSources)}
            className="flex items-center justify-between w-full text-xs font-semibold text-agri-700 hover:text-agri-800"
          >
            <div className="flex items-center space-x-1.5">
              <BookOpen className="w-3.5 h-3.5" />
              <span>Grounded Agricultural References ({sources.length})</span>
            </div>
            {showSources ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>

          {showSources && (
            <div className="mt-2 space-y-2">
              {sources.map((src, idx) => (
                <div key={idx} className="bg-agri-50/50 rounded-xl p-2.5 text-xs border border-agri-100">
                  <div className="font-bold text-agri-900">{src.title}</div>
                  <div className="text-stone-600 text-[11px] mt-0.5">{src.excerpt}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Feedback & Metrics Footer */}
      <div className="flex items-center justify-between pt-2 border-t border-stone-100 text-xs text-stone-500">
        <div className="flex items-center space-x-2">
          <span>Was this helpful?</span>
          <button
            onClick={() => handleFeedback(true)}
            className={`p-1.5 rounded-lg border transition-colors ${
              feedbackGiven === true
                ? 'bg-green-100 border-green-300 text-green-700'
                : 'hover:bg-stone-100 border-stone-200'
            }`}
            title="Helpful"
          >
            <ThumbsUp className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => handleFeedback(false)}
            className={`p-1.5 rounded-lg border transition-colors ${
              feedbackGiven === false
                ? 'bg-red-100 border-red-300 text-red-700'
                : 'hover:bg-stone-100 border-stone-200'
            }`}
            title="Needs improvement"
          >
            <ThumbsDown className="w-3.5 h-3.5" />
          </button>
        </div>

        {latencyMetrics?.total_ms && (
          <span className="text-[10px] text-stone-400 font-mono">
            {latencyMetrics.total_ms} ms
          </span>
        )}
      </div>
    </div>
  );
}
