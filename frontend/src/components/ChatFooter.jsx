import React, { useState, useRef } from 'react';
import { Mic, Square, Send, Sparkles, Loader2, Paperclip, Smile } from 'lucide-react';

export default function ChatFooter({
  isRecording,
  recordingDuration,
  onStartRecording,
  onStopRecording,
  onSendText,
  isLoading,
  selectedLang
}) {
  const [textInput, setTextInput] = useState('');

  const formatDuration = (sec) => {
    const mins = Math.floor(sec / 60);
    const secs = sec % 60;
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  const handleSend = (e) => {
    e.preventDefault();
    if (!textInput.trim() || isLoading || isRecording) return;
    onSendText(textInput);
    setTextInput('');
  };

  return (
    <footer className="bg-stone-100/95 border-t border-stone-200 p-2 sm:p-3 sticky bottom-0 z-20 backdrop-blur-md">
      <div className="max-w-3xl mx-auto">
        {/* If Recording is Active */}
        {isRecording ? (
          <div className="flex items-center justify-between bg-red-50 border border-red-200 px-4 py-2.5 rounded-full shadow-inner animate-in fade-in duration-200">
            <div className="flex items-center space-x-3">
              <span className="w-3 h-3 rounded-full bg-red-600 animate-ping" />
              <div className="flex items-center space-x-2">
                <span className="text-xs font-bold text-red-700">Recording Voice ({selectedLang.nativeName})...</span>
                <span className="text-xs font-mono text-stone-600 bg-white px-2 py-0.5 rounded border border-red-200">
                  {formatDuration(recordingDuration)}
                </span>
              </div>
            </div>

            <button
              onClick={onStopRecording}
              className="px-4 py-1.5 bg-red-600 hover:bg-red-700 text-white text-xs font-semibold rounded-full flex items-center gap-1.5 shadow transition-all transform active:scale-95"
            >
              <Square className="w-3.5 h-3.5 fill-current" />
              <span>Send Voice</span>
            </button>
          </div>
        ) : (
          /* Normal Input Form */
          <form onSubmit={handleSend} className="flex items-center space-x-2">
            {/* Text Input Container */}
            <div className="flex-1 bg-white border border-stone-300 rounded-full px-4 py-2.5 shadow-xs flex items-center space-x-2 focus-within:ring-2 focus-within:ring-emerald-500 focus-within:border-emerald-500">
              <input
                type="text"
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                placeholder={`Type or hold mic to speak in ${selectedLang.nativeName}...`}
                disabled={isLoading}
                className="w-full text-xs sm:text-sm bg-transparent outline-none text-stone-900 placeholder:text-stone-400"
              />
            </div>

            {/* If Text is entered, show Send Button; otherwise show Voice Mic Button */}
            {textInput.trim().length > 0 ? (
              <button
                type="submit"
                disabled={isLoading}
                className="w-10 h-10 rounded-full bg-emerald-600 hover:bg-emerald-700 disabled:bg-stone-300 text-white flex items-center justify-center shadow-md transition-all transform active:scale-95 shrink-0"
                title="Send Message"
              >
                {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4 ml-0.5" />}
              </button>
            ) : (
              <button
                type="button"
                onClick={onStartRecording}
                disabled={isLoading}
                className="w-11 h-11 rounded-full bg-emerald-600 hover:bg-emerald-700 disabled:bg-stone-300 text-white flex items-center justify-center shadow-md transition-all transform active:scale-95 hover:shadow-emerald-600/30 shrink-0"
                title="Press to Record Voice Query"
              >
                {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Mic className="w-5 h-5" />}
              </button>
            )}
          </form>
        )}
      </div>
    </footer>
  );
}
