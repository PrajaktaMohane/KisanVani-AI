import React, { useState } from 'react';
import { X, BookPlus, Search, Activity, ShieldCheck } from 'lucide-react';
import KVKUploader from './KVKUploader';
import RAGExplorer from './RAGExplorer';
import SystemStatusView from './SystemStatusView';

export default function AdminModal({ isOpen, onClose, systemStatus, knowledgeStatus, onRefreshStatus }) {
  const [tab, setTab] = useState('status'); // 'status', 'kvk', 'rag'

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-3 sm:p-4">
      <div className="bg-white rounded-3xl max-w-2xl w-full max-h-[90vh] shadow-2xl flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Modal Header */}
        <div className="bg-stone-900 text-white p-4 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <div>
              <h2 className="font-bold text-sm">Admin & KVK Knowledge Hub</h2>
              <p className="text-[11px] text-stone-400">RAG Monitoring, Advisory Uploads & System Health</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-stone-800 rounded-full text-stone-300"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center border-b border-stone-200 bg-stone-50 px-4 pt-2 text-xs font-semibold space-x-2">
          <button
            onClick={() => setTab('status')}
            className={`pb-2.5 px-3 border-b-2 flex items-center gap-1.5 transition-all ${
              tab === 'status'
                ? 'border-emerald-600 text-emerald-800 font-bold'
                : 'border-transparent text-stone-500 hover:text-stone-800'
            }`}
          >
            <Activity className="w-3.5 h-3.5" /> System Status
          </button>
          <button
            onClick={() => setTab('kvk')}
            className={`pb-2.5 px-3 border-b-2 flex items-center gap-1.5 transition-all ${
              tab === 'kvk'
                ? 'border-emerald-600 text-emerald-800 font-bold'
                : 'border-transparent text-stone-500 hover:text-stone-800'
            }`}
          >
            <BookPlus className="w-3.5 h-3.5" /> KVK Advisory Uploader
          </button>
          <button
            onClick={() => setTab('rag')}
            className={`pb-2.5 px-3 border-b-2 flex items-center gap-1.5 transition-all ${
              tab === 'rag'
                ? 'border-emerald-600 text-emerald-800 font-bold'
                : 'border-transparent text-stone-500 hover:text-stone-800'
            }`}
          >
            <Search className="w-3.5 h-3.5" /> RAG Explorer
          </button>
        </div>

        {/* Tab Content Area */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 bg-stone-100/50">
          {tab === 'status' && (
            <SystemStatusView
              systemStatus={systemStatus}
              knowledgeStatus={knowledgeStatus}
            />
          )}

          {tab === 'kvk' && (
            <KVKUploader onUploadSuccess={onRefreshStatus} />
          )}

          {tab === 'rag' && (
            <RAGExplorer />
          )}
        </div>
      </div>
    </div>
  );
}
