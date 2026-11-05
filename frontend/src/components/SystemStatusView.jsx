import React from 'react';
import { Activity, CheckCircle2, XCircle, AlertCircle, Database, Server, Smartphone, Cpu, ShieldCheck } from 'lucide-react';

export default function SystemStatusView({ systemStatus, knowledgeStatus }) {
  const cards = [
    {
      title: 'WhatsApp Cloud API',
      status: systemStatus?.whatsapp_cloud_api_configured,
      detail: systemStatus?.whatsapp_cloud_api_configured
        ? `Meta Graph API ${systemStatus?.whatsapp_api_version || 'v20.0'} Connected`
        : 'Running in Local Demo / Simulation Mode',
      icon: Smartphone,
      color: systemStatus?.whatsapp_cloud_api_configured ? 'emerald' : 'amber'
    },
    {
      title: 'Google Gemini LLM Reasoning',
      status: systemStatus?.gemini_api_configured,
      detail: systemStatus?.gemini_api_configured
        ? `Model: ${systemStatus?.gemini_model || 'gemini-1.5-flash'} (Krishi Mitra Guardrails Active)`
        : 'Requires GEMINI_API_KEY in .env (Inspection mode active)',
      icon: Cpu,
      color: systemStatus?.gemini_api_configured ? 'emerald' : 'amber'
    },
    {
      title: 'FAISS Vector Database',
      status: knowledgeStatus?.faiss_index_exists,
      detail: knowledgeStatus?.faiss_index_exists
        ? `Indexed ${knowledgeStatus?.total_documents || 0} agricultural docs (${knowledgeStatus?.embedding_model?.split('/')[1] || 'multilingual'})`
        : 'Run python -m app.rag.ingest to index raw documents',
      icon: Database,
      color: knowledgeStatus?.faiss_index_exists ? 'emerald' : 'red'
    },
    {
      title: 'Speech-to-Text (STT)',
      status: true,
      detail: `Engine: Whisper (${systemStatus?.whisper_model_size || 'base'}) with Auto-Language Detection`,
      icon: Server,
      color: 'emerald'
    }
  ];

  return (
    <div className="bg-white rounded-3xl p-6 shadow-md border border-stone-200 space-y-6">
      <div className="flex items-center space-x-3 pb-4 border-b border-stone-100">
        <div className="w-10 h-10 rounded-xl bg-blue-100 text-blue-800 flex items-center justify-center">
          <Activity className="w-5 h-5" />
        </div>
        <div>
          <h2 className="text-base font-bold text-stone-900">System Health & Service Integrations</h2>
          <p className="text-xs text-stone-500">Live connectivity overview for backend pipelines, database, and Meta Webhook.</p>
        </div>
      </div>

      {/* Integration Status Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {cards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div key={idx} className="p-4 rounded-2xl border border-stone-200 bg-stone-50/70 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Icon className="w-4 h-4 text-stone-700" />
                  <span className="text-xs font-bold text-stone-900">{card.title}</span>
                </div>
                {card.status ? (
                  <span className="flex items-center gap-1 text-[11px] font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Ready
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-[11px] font-bold text-amber-800 bg-amber-100 px-2 py-0.5 rounded-full">
                    <AlertCircle className="w-3.5 h-3.5" /> Setup Needed
                  </span>
                )}
              </div>
              <p className="text-xs text-stone-600 font-medium">{card.detail}</p>
            </div>
          );
        })}
      </div>

      {/* Agricultural Knowledge Breakdown */}
      {knowledgeStatus?.category_breakdown && (
        <div className="pt-2">
          <h3 className="text-xs font-bold text-stone-700 uppercase tracking-wider mb-3">
            Ingested Agricultural Knowledge Breakdown
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            {Object.entries(knowledgeStatus.category_breakdown).map(([cat, count]) => (
              <div key={cat} className="p-3 bg-agri-50/70 rounded-xl border border-agri-200/60">
                <div className="text-[11px] text-agri-800 font-bold uppercase truncate">{cat.replace('_', ' ')}</div>
                <div className="text-lg font-bold text-agri-950 mt-1">{count} <span className="text-xs font-normal text-stone-500">docs</span></div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Meta WhatsApp Webhook Setup Guide */}
      <div className="p-4 bg-stone-900 text-stone-100 rounded-2xl text-xs space-y-2 font-mono">
        <div className="text-emerald-400 font-bold font-sans">Meta WhatsApp Cloud API Webhook URL:</div>
        <div className="bg-black/50 p-2.5 rounded-lg select-all text-[11px] text-emerald-300 break-all">
          https://&lt;your-public-domain-or-ngrok&gt;/api/v1/whatsapp/webhook
        </div>
        <p className="text-[11px] text-stone-400 font-sans">
          In Meta App Dashboard &gt; WhatsApp &gt; Configuration: Subscribe to `messages` event with your WHATSAPP_VERIFY_TOKEN.
        </p>
      </div>
    </div>
  );
}
