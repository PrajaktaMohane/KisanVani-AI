import React, { useState } from 'react';
import { Search, BookOpen, ShieldCheck, AlertTriangle, Loader2 } from 'lucide-react';
import api from '../services/api';

export default function RAGExplorer() {
  const [searchQuery, setSearchQuery] = useState('कापसावर गुलाबी बोंड अळी नियंत्रण');
  const [searchResults, setSearchResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setIsLoading(true);
    setError(null);
    try {
      const response = await api.get(`/api/v1/knowledge/search?query=${encodeURIComponent(searchQuery)}`);
      setSearchResults(response.data);
    } catch (err) {
      console.error('RAG Search failed:', err);
      setError('Failed to search knowledge base.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-3xl p-6 shadow-md border border-stone-200 space-y-5">
      <div className="flex items-center space-x-3 pb-4 border-b border-stone-100">
        <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-800 flex items-center justify-center">
          <BookOpen className="w-5 h-5" />
        </div>
        <div>
          <h2 className="text-base font-bold text-stone-900">FAISS Vector Search & RAG Grounding Explorer</h2>
          <p className="text-xs text-stone-500">Query the multilingual vector database to view retrieved ICAR/KVK chunks and similarity scores.</p>
        </div>
      </div>

      <form onSubmit={handleSearch} className="flex gap-2">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search query in Marathi, Hindi, or English (e.g. wheat yellow rust dosage)..."
          className="flex-1 text-xs rounded-xl border border-stone-200 p-3 bg-stone-50 focus:bg-white focus:ring-2 focus:ring-agri-500 outline-none"
        />
        <button
          type="submit"
          disabled={isLoading || !searchQuery.trim()}
          className="px-5 py-3 bg-agri-600 hover:bg-agri-700 disabled:bg-stone-300 text-white font-semibold text-xs rounded-xl flex items-center gap-1.5 shadow transition-all"
        >
          {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
          <span>Search Vector Store</span>
        </button>
      </form>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl">
          {error}
        </div>
      )}

      {searchResults && (
        <div className="space-y-4 pt-2">
          {/* Grounding Status Pill */}
          <div className="flex items-center justify-between bg-stone-50 p-3 rounded-2xl border border-stone-200 text-xs">
            <div className="flex items-center space-x-2">
              {searchResults.is_grounded ? (
                <span className="flex items-center gap-1.5 text-green-700 font-bold bg-green-100 px-2.5 py-1 rounded-full">
                  <ShieldCheck className="w-4 h-4" /> Grounded in Verified ICAR/KVK Records
                </span>
              ) : (
                <span className="flex items-center gap-1.5 text-amber-700 font-bold bg-amber-100 px-2.5 py-1 rounded-full">
                  <AlertTriangle className="w-4 h-4" /> Low Confidence / Fallback Triggered
                </span>
              )}
            </div>
            <span className="text-stone-500 text-[11px]">
              Retrieved Chunks: <strong>{searchResults.sources?.length || 0}</strong>
            </span>
          </div>

          {/* Retrieved Sources List */}
          <div className="space-y-3">
            {searchResults.sources?.map((src, idx) => (
              <div key={idx} className="bg-stone-50 rounded-2xl p-4 border border-stone-200 text-xs space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-stone-900">{src.title}</span>
                  <span className="bg-white px-2 py-0.5 rounded border text-[10px] font-mono text-stone-500">
                    Distance: {src.relevance_score}
                  </span>
                </div>
                <div className="text-agri-800 font-semibold text-[11px]">{src.category}</div>
                <p className="text-stone-700 leading-relaxed bg-white p-3 rounded-xl border border-stone-100">
                  {src.excerpt}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
