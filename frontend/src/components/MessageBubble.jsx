import React, { useState } from 'react';
import { Play, Pause, RotateCcw, Volume2, BookOpen, ShieldCheck, AlertTriangle, ThumbsUp, ThumbsDown, Check, CheckCheck, ChevronDown, ChevronUp, Mic } from 'lucide-react';
import { base64ToAudioUrl } from '../utils/audioHelpers';

export default function MessageBubble({
  message,
  isPlaying,
  activeAudioMsgId,
  playbackSpeed,
  onTogglePlay,
  onChangeSpeed,
  onFeedback
}) {
  const isFarmer = message.role === 'farmer';
  const [showSources, setShowSources] = useState(false);
  const [feedbackGiven, setFeedbackGiven] = useState(null);

  const formatTime = (ts) => {
    if (!ts) return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const date = new Date(typeof ts === 'number' && ts < 10000000000 ? ts * 1000 : ts);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const isCurrentAudioPlaying = isPlaying && activeAudioMsgId === message.id;

  const handleFeedback = (val) => {
    setFeedbackGiven(val);
    if (onFeedback) onFeedback(message.id, val);
  };

  if (isFarmer) {
    return (
      <div className="flex justify-end mb-3.5 animate-in fade-in slide-in-from-bottom-2 duration-200">
        <div className="bg-emerald-100/90 text-emerald-950 rounded-2xl rounded-tr-xs px-3.5 py-2.5 max-w-[85%] sm:max-w-md shadow-xs border border-emerald-200/60 space-y-1">
          {message.isVoice && (
            <div className="flex items-center space-x-2 text-xs font-semibold text-emerald-800 pb-1 border-b border-emerald-200/60">
              <Mic className="w-3.5 h-3.5 text-emerald-600 animate-pulse" />
              <span>Voice Question ({message.duration || '0:05'})</span>
            </div>
          )}
          <p className="text-xs sm:text-sm font-medium leading-relaxed">
            {message.content}
          </p>
          <div className="flex items-center justify-end space-x-1 text-[10px] text-emerald-700/80 pt-0.5">
            <span>{formatTime(message.timestamp)}</span>
            <CheckCheck className="w-3.5 h-3.5 text-emerald-600" />
          </div>
        </div>
      </div>
    );
  }

  // KisanVani AI Response Bubble
  return (
    <div className="flex justify-start mb-4 animate-in fade-in slide-in-from-bottom-3 duration-200">
      <div className="bg-white text-stone-900 rounded-2xl rounded-tl-xs p-3.5 sm:p-4 max-w-[92%] sm:max-w-lg shadow-sm border border-stone-200/90 space-y-3">
        {/* Header Tag */}
        <div className="flex items-center justify-between pb-2 border-b border-stone-100 text-xs">
          <div className="flex items-center space-x-1.5 font-bold text-emerald-800">
            <span>🌱 KisanVani AI</span>
            <span className="bg-emerald-50 text-emerald-700 text-[10px] font-semibold px-1.5 py-0.2 rounded border border-emerald-200 uppercase">
              {message.language || 'hi'}
            </span>
          </div>

          {message.is_grounded !== false ? (
            <span className="flex items-center gap-1 text-[10px] text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full font-medium">
              <ShieldCheck className="w-3 h-3 text-emerald-600" /> Verified Context
            </span>
          ) : (
            <span className="flex items-center gap-1 text-[10px] text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full font-medium">
              <AlertTriangle className="w-3 h-3 text-amber-600" /> Fallback Mode
            </span>
          )}
        </div>

        {/* Audio Player Bar (Inside Bubble) */}
        {message.audio_base64 && (
          <div className="flex items-center justify-between bg-emerald-950 text-white px-3 py-2 rounded-xl shadow-xs">
            <div className="flex items-center space-x-2.5">
              <button
                onClick={() => onTogglePlay(message.id, message.audio_base64)}
                className="w-8 h-8 rounded-full bg-emerald-500 hover:bg-emerald-400 text-white flex items-center justify-center transition-colors shadow"
                title={isCurrentAudioPlaying ? 'Pause Audio' : 'Play Audio Answer'}
              >
                {isCurrentAudioPlaying ? (
                  <Pause className="w-3.5 h-3.5 fill-current" />
                ) : (
                  <Play className="w-3.5 h-3.5 fill-current ml-0.5" />
                )}
              </button>
              <div className="flex items-center space-x-1 text-[11px] font-medium text-emerald-200">
                <Volume2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>{isCurrentAudioPlaying ? 'Playing Voice...' : 'Listen in Native Voice'}</span>
              </div>
            </div>

            {/* Speed Control */}
            <div className="flex items-center space-x-1 bg-emerald-900 rounded-lg p-0.5 text-[10px]">
              {[0.8, 1.0, 1.2].map((spd) => (
                <button
                  key={spd}
                  onClick={() => onChangeSpeed(spd)}
                  className={`px-1.5 py-0.5 rounded font-semibold transition-colors ${
                    playbackSpeed === spd ? 'bg-emerald-600 text-white' : 'text-emerald-300 hover:text-white'
                  }`}
                >
                  {spd}x
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Text Advisory Answer */}
        <div className="text-xs sm:text-sm text-stone-800 leading-relaxed whitespace-pre-line font-normal">
          {message.content}
        </div>

        {/* Grounded ICAR/KVK Sources Accordion */}
        {message.sources && message.sources.length > 0 && (
          <div className="pt-2 border-t border-stone-100 text-xs">
            <button
              onClick={() => setShowSources(!showSources)}
              className="flex items-center justify-between w-full text-emerald-800 font-semibold hover:text-emerald-900"
            >
              <span className="flex items-center gap-1.5">
                <BookOpen className="w-3.5 h-3.5 text-emerald-600" />
                <span>Verified Agricultural Sources ({message.sources.length})</span>
              </span>
              {showSources ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>

            {showSources && (
              <div className="mt-2 space-y-2">
                {message.sources.map((src, idx) => (
                  <div key={idx} className="bg-stone-50 rounded-xl p-2.5 text-[11px] border border-stone-200">
                    <div className="font-bold text-stone-900">{src.title}</div>
                    <div className="text-stone-600 mt-0.5">{src.excerpt}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Footer & Feedback */}
        <div className="flex items-center justify-between pt-1 border-t border-stone-100 text-[11px] text-stone-400">
          <div className="flex items-center space-x-1.5">
            <span className="text-[10px]">Helpful?</span>
            <button
              onClick={() => handleFeedback(true)}
              className={`p-1 rounded transition-colors ${feedbackGiven === true ? 'text-green-600 bg-green-50' : 'hover:text-stone-600'}`}
              title="Helpful advice"
            >
              <ThumbsUp className="w-3 h-3" />
            </button>
            <button
              onClick={() => handleFeedback(false)}
              className={`p-1 rounded transition-colors ${feedbackGiven === false ? 'text-red-600 bg-red-50' : 'hover:text-stone-600'}`}
              title="Needs improvement"
            >
              <ThumbsDown className="w-3 h-3" />
            </button>
          </div>

          <span>{formatTime(message.timestamp)}</span>
        </div>
      </div>
    </div>
  );
}
