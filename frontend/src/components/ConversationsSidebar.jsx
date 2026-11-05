import React from 'react';
import { PlusCircle, MessageSquare, UserCheck, X, Sparkles, Calendar, ChevronRight } from 'lucide-react';

export default function ConversationsSidebar({
  isOpen,
  onClose,
  conversations = [],
  activeSessionId,
  onSelectSession,
  onNewChat,
  onOpenProfile,
  farmerContext
}) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-40 bg-black/50 backdrop-blur-xs flex">
      {/* Sidebar Panel */}
      <div className="w-80 max-w-[85vw] bg-white h-full shadow-2xl flex flex-col animate-in slide-in-from-left duration-200">
        {/* Sidebar Header */}
        <div className="bg-emerald-800 text-white p-4 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <MessageSquare className="w-5 h-5 text-emerald-300" />
            <h2 className="font-bold text-sm">Chats & Conversations</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-emerald-700 rounded-full text-emerald-200"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* New Chat Button */}
        <div className="p-3 border-b border-stone-100">
          <button
            onClick={() => {
              onNewChat();
              onClose();
            }}
            className="w-full py-2.5 px-3 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 font-semibold text-xs rounded-xl flex items-center justify-center gap-2 border border-emerald-200 transition-colors"
          >
            <PlusCircle className="w-4 h-4 text-emerald-600" />
            <span>New Agriculture Question</span>
          </button>
        </div>

        {/* Farmer Profile Card */}
        <div className="p-3 border-b border-stone-100 bg-stone-50">
          <div className="flex items-center justify-between text-xs mb-1">
            <span className="font-bold text-stone-700 flex items-center gap-1">
              <UserCheck className="w-3.5 h-3.5 text-emerald-600" /> Farmer Context
            </span>
            <button
              onClick={() => {
                onOpenProfile();
                onClose();
              }}
              className="text-[11px] text-emerald-700 font-semibold hover:underline"
            >
              Edit
            </button>
          </div>
          <div className="text-[11px] text-stone-600 space-y-0.5">
            <p className="truncate"><strong>Crop:</strong> {farmerContext?.cropName || 'Cotton'}</p>
            <p><strong>State:</strong> {farmerContext?.state || 'Maharashtra'}</p>
            <p><strong>Land:</strong> {farmerContext?.landSize || 2.5} Acres</p>
          </div>
        </div>

        {/* Conversation List */}
        <div className="flex-1 overflow-y-auto p-2 space-y-1.5">
          <div className="px-2 py-1 text-[11px] font-bold uppercase tracking-wider text-stone-400">
            Recent Queries / इतिहास
          </div>

          {conversations.length === 0 ? (
            <div className="text-center py-8 text-stone-400 text-xs">
              No previous queries yet.
            </div>
          ) : (
            conversations.map((item, idx) => {
              const sid = item.session_id || idx;
              const isSelected = activeSessionId === sid;
              return (
                <button
                  key={idx}
                  onClick={() => {
                    onSelectSession(item);
                    onClose();
                  }}
                  className={`w-full text-left p-2.5 rounded-xl text-xs transition-all border flex items-start justify-between gap-2 ${
                    isSelected
                      ? 'bg-emerald-50/80 border-emerald-300 text-emerald-950 font-medium'
                      : 'border-transparent hover:bg-stone-100 text-stone-700'
                  }`}
                >
                  <div className="truncate flex-1">
                    <p className="truncate font-semibold text-stone-900">
                      {item.query_transcript || item.transcript || 'Voice query'}
                    </p>
                    <p className="truncate text-[11px] text-stone-500 mt-0.5">
                      {item.response_text || item.answer_text || ''}
                    </p>
                  </div>
                  <span className="text-[10px] font-mono uppercase bg-stone-200/80 text-stone-600 px-1 py-0.5 rounded shrink-0">
                    {item.detected_language || 'hi'}
                  </span>
                </button>
              );
            })
          )}
        </div>
      </div>

      {/* Outside click area */}
      <div className="flex-1" onClick={onClose} />
    </div>
  );
}
