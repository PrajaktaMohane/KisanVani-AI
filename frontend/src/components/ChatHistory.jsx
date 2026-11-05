import React from 'react';
import { MessageSquare, Calendar } from 'lucide-react';

export default function ChatHistory({ history = [], onSelectHistoryItem }) {
  if (!history || history.length === 0) return null;

  return (
    <div className="mt-8 space-y-3">
      <h3 className="text-xs font-bold uppercase tracking-wider text-stone-500 flex items-center gap-1.5">
        <MessageSquare className="w-3.5 h-3.5" /> Recent Queries / पिछले सवाल
      </h3>
      <div className="space-y-2">
        {history.map((item, idx) => (
          <button
            key={idx}
            onClick={() => onSelectHistoryItem(item)}
            className="w-full text-left bg-white p-3 rounded-2xl border border-stone-200 hover:border-agri-400 hover:bg-agri-50/40 transition-all flex items-start justify-between gap-3 shadow-sm"
          >
            <div className="truncate">
              <p className="text-xs font-semibold text-stone-800 truncate">{item.transcript}</p>
              <p className="text-[11px] text-stone-500 truncate mt-0.5">{item.answer_text}</p>
            </div>
            <span className="text-[10px] font-mono text-stone-400 shrink-0 uppercase bg-stone-100 px-1.5 py-0.5 rounded">
              {item.detected_language}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
