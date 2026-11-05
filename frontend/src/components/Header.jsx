import React from 'react';
import { Sprout, MessageSquare, ShieldCheck, Activity, Smartphone } from 'lucide-react';

export default function Header({ activeTab, onTabChange, systemStatus }) {
  return (
    <header className="sticky top-0 z-30 bg-white/95 backdrop-blur-md border-b border-stone-200 shadow-sm">
      {/* Primary Channel Banner */}
      <div className="bg-emerald-800 text-emerald-100 text-xs px-4 py-1.5 flex items-center justify-between font-medium">
        <div className="flex items-center space-x-2">
          <Smartphone className="w-3.5 h-3.5 text-emerald-300" />
          <span className="font-semibold text-white">Production Note:</span>
          <span>WhatsApp is the primary farmer interface. This dashboard is for Admins, KVK Experts, and Pipeline Testing.</span>
        </div>
        <div className="flex items-center space-x-3 text-[11px]">
          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-bold ${
            systemStatus?.whatsapp_cloud_api_configured ? 'bg-emerald-700 text-white' : 'bg-emerald-950/60 text-amber-300'
          }`}>
            <span className={`w-1.5 h-1.5 rounded-full ${systemStatus?.whatsapp_cloud_api_configured ? 'bg-emerald-400' : 'bg-amber-400 animate-pulse'}`} />
            {systemStatus?.whatsapp_cloud_api_configured ? 'WhatsApp API Connected' : 'WhatsApp Demo Mode'}
          </span>
        </div>
      </div>

      {/* Main Navbar */}
      <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-agri-700 to-agri-500 flex items-center justify-center text-white shadow-md shadow-agri-500/20">
            <Sprout className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="font-bold text-lg text-stone-900 tracking-tight">KisanVani AI</h1>
              <span className="bg-stone-100 text-stone-700 text-[11px] font-bold px-2 py-0.5 rounded-md border border-stone-200">
                Admin & Demo Dashboard
              </span>
            </div>
            <p className="text-xs text-stone-500 font-medium">किसानवाणी • Multilingual Agricultural Assistant</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center space-x-1 bg-stone-100 p-1 rounded-xl border border-stone-200 text-xs font-semibold">
          <button
            onClick={() => onTabChange('test')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              activeTab === 'test'
                ? 'bg-white text-agri-800 shadow-sm'
                : 'text-stone-600 hover:text-stone-900'
            }`}
          >
            Voice & WhatsApp Tester
          </button>
          <button
            onClick={() => onTabChange('kvk')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              activeTab === 'kvk'
                ? 'bg-white text-agri-800 shadow-sm'
                : 'text-stone-600 hover:text-stone-900'
            }`}
          >
            KVK Expert Uploader
          </button>
          <button
            onClick={() => onTabChange('rag')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              activeTab === 'rag'
                ? 'bg-white text-agri-800 shadow-sm'
                : 'text-stone-600 hover:text-stone-900'
            }`}
          >
            RAG Knowledge Explorer
          </button>
          <button
            onClick={() => onTabChange('status')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              activeTab === 'status'
                ? 'bg-white text-agri-800 shadow-sm'
                : 'text-stone-600 hover:text-stone-900'
            }`}
          >
            System Status
          </button>
        </nav>
      </div>
    </header>
  );
}
