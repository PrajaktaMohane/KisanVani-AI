import React from 'react';
import { Sprout, Menu, Settings, Languages, User, ShieldCheck, Sparkles } from 'lucide-react';

export default function ChatHeader({
  onToggleSidebar,
  onOpenAdmin,
  onOpenLang,
  onOpenProfile,
  currentLang,
  farmerContext
}) {
  return (
    <header className="bg-emerald-800 text-white px-3 sm:px-4 py-2.5 flex items-center justify-between shadow-md z-20 sticky top-0">
      {/* Left: Sidebar Toggle + Avatar + Title */}
      <div className="flex items-center space-x-2.5">
        <button
          onClick={onToggleSidebar}
          className="p-1.5 hover:bg-emerald-700/80 rounded-full transition-colors text-emerald-100"
          title="Conversation History"
          aria-label="Toggle Conversation History"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-full bg-emerald-600 flex items-center justify-center text-white border-2 border-emerald-400/40 shadow-inner">
          <Sprout className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
        </div>

        <div>
          <div className="flex items-center space-x-1.5">
            <h1 className="font-bold text-sm sm:text-base text-white tracking-tight">KisanVani AI</h1>
            <span className="bg-emerald-950/70 text-emerald-300 text-[10px] font-semibold px-1.5 py-0.5 rounded flex items-center gap-1">
              <Sparkles className="w-2.5 h-2.5 text-amber-300" />
              Krishi Mitra
            </span>
          </div>
          <p className="text-[11px] text-emerald-200 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            AI Agricultural Voice Assistant
          </p>
        </div>
      </div>

      {/* Right: Language Pill + Crop Badge + Admin Toggle */}
      <div className="flex items-center space-x-1.5 sm:space-x-2">
        {/* Language Selector */}
        <button
          onClick={onOpenLang}
          className="flex items-center space-x-1 px-2.5 py-1 text-xs font-semibold bg-emerald-900/60 hover:bg-emerald-700 text-emerald-100 rounded-full border border-emerald-700/80 transition-colors"
          title="Change Language"
        >
          <Languages className="w-3.5 h-3.5 text-emerald-300" />
          <span>{currentLang?.nativeName || 'हिन्दी'}</span>
        </button>

        {/* Farmer Crop Context */}
        <button
          onClick={onOpenProfile}
          className="hidden sm:flex items-center space-x-1 px-2.5 py-1 text-xs font-medium bg-emerald-900/60 hover:bg-emerald-700 text-emerald-100 rounded-full border border-emerald-700/80 transition-colors"
          title="Farmer Context"
        >
          <User className="w-3.5 h-3.5 text-emerald-300" />
          <span className="truncate max-w-[100px]">{farmerContext?.cropName?.split(' ')[0] || 'Crop'}</span>
        </button>

        {/* Admin & Knowledge Base Modal Trigger */}
        <button
          onClick={onOpenAdmin}
          className="p-1.5 hover:bg-emerald-700/80 rounded-full transition-colors text-emerald-200 hover:text-white"
          title="Admin & RAG Knowledge Hub"
          aria-label="Open Admin Hub"
        >
          <Settings className="w-5 h-5" />
        </button>
      </div>
    </header>
  );
}
