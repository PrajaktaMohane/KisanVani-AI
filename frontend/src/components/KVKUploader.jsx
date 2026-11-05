import React, { useState } from 'react';
import { Upload, CheckCircle2, AlertCircle, Loader2, BookPlus } from 'lucide-react';
import api from '../services/api';
import { MAJOR_CROPS, INDIAN_STATES } from '../utils/constants';

export default function KVKUploader({ onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [crop, setCrop] = useState('Cotton');
  const [category, setCategory] = useState('Pest and Disease');
  const [state, setState] = useState('Maharashtra');
  const [language, setLanguage] = useState('mr');
  const [sourceOrg, setSourceOrg] = useState('Krishi Vigyan Kendra (KVK)');
  
  const [isUploading, setIsUploading] = useState(false);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a .txt or .pdf advisory file.');
      return;
    }

    setIsUploading(true);
    setMessage(null);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('crop', crop);
    formData.append('category', category);
    formData.append('state', state);
    formData.append('language', language);
    formData.append('source_org', sourceOrg);

    try {
      const response = await api.post('/api/v1/knowledge/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setMessage(response.data.message || 'Advisory uploaded and FAISS vector index re-indexed successfully!');
      setFile(null);
      if (onUploadSuccess) onUploadSuccess();
    } catch (err) {
      console.error('KVK upload error:', err);
      setError(err.response?.data?.detail || 'Failed to upload advisory.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="bg-white rounded-3xl p-6 shadow-md border border-stone-200">
      <div className="flex items-center space-x-3 mb-4 pb-4 border-b border-stone-100">
        <div className="w-10 h-10 rounded-xl bg-agri-100 text-agri-700 flex items-center justify-center">
          <BookPlus className="w-5 h-5" />
        </div>
        <div>
          <h2 className="text-base font-bold text-stone-900">KVK Agricultural Expert Document Ingestion</h2>
          <p className="text-xs text-stone-500">Upload verified ICAR/KVK advisories to ground the Gemini reasoning engine.</p>
        </div>
      </div>

      {message && (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 text-green-800 text-xs rounded-xl flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-green-600 shrink-0" />
          <span>{message}</span>
        </div>
      )}

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-800 text-xs rounded-xl flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4 text-xs">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Crop */}
          <div>
            <label className="block font-semibold text-stone-700 mb-1">Target Crop / संबंधित पीक</label>
            <select
              value={crop}
              onChange={(e) => setCrop(e.target.value)}
              className="w-full text-xs rounded-xl border border-stone-200 p-2.5 bg-stone-50 focus:bg-white focus:ring-2 focus:ring-agri-500 outline-none"
            >
              {MAJOR_CROPS.map((c) => (
                <option key={c} value={c.split(' ')[0]}>{c}</option>
              ))}
            </select>
          </div>

          {/* Category */}
          <div>
            <label className="block font-semibold text-stone-700 mb-1">Category / वर्ग</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full text-xs rounded-xl border border-stone-200 p-2.5 bg-stone-50 focus:bg-white focus:ring-2 focus:ring-agri-500 outline-none"
            >
              <option value="Pest and Disease">Pest and Disease (कीड व रोग)</option>
              <option value="Fertilizer and Soil">Fertilizer and Soil (खते व माती)</option>
              <option value="Irrigation and Weather">Irrigation and Weather (सिंचन व हवामान)</option>
              <option value="Government Scheme">Government Scheme (सरकारी योजना)</option>
            </select>
          </div>

          {/* State */}
          <div>
            <label className="block font-semibold text-stone-700 mb-1">Applicable State / राज्य</label>
            <select
              value={state}
              onChange={(e) => setState(e.target.value)}
              className="w-full text-xs rounded-xl border border-stone-200 p-2.5 bg-stone-50 focus:bg-white focus:ring-2 focus:ring-agri-500 outline-none"
            >
              {INDIAN_STATES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>

          {/* Language */}
          <div>
            <label className="block font-semibold text-stone-700 mb-1">Document Language / भाषा</label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="w-full text-xs rounded-xl border border-stone-200 p-2.5 bg-stone-50 focus:bg-white focus:ring-2 focus:ring-agri-500 outline-none"
            >
              <option value="mr">Marathi (मराठी)</option>
              <option value="hi">Hindi (हिन्दी)</option>
              <option value="en">English</option>
            </select>
          </div>
        </div>

        {/* Source Organization */}
        <div>
          <label className="block font-semibold text-stone-700 mb-1">Source / Issuing Organization</label>
          <input
            type="text"
            value={sourceOrg}
            onChange={(e) => setSourceOrg(e.target.value)}
            placeholder="e.g. Krishi Vigyan Kendra Baramati / ICAR-CICR Nagpur"
            className="w-full text-xs rounded-xl border border-stone-200 p-2.5 bg-stone-50 focus:bg-white focus:ring-2 focus:ring-agri-500 outline-none"
          />
        </div>

        {/* File Input */}
        <div>
          <label className="block font-semibold text-stone-700 mb-1">Advisory Document File (.txt or .pdf)</label>
          <input
            type="file"
            accept=".txt,.pdf"
            onChange={(e) => setFile(e.target.files[0])}
            className="w-full text-xs rounded-xl border border-stone-200 p-2.5 bg-stone-50 focus:bg-white file:mr-4 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-agri-600 file:text-white hover:file:bg-agri-700"
          />
        </div>

        <button
          type="submit"
          disabled={isUploading}
          className="w-full py-3 bg-agri-600 hover:bg-agri-700 disabled:bg-stone-300 text-white font-semibold rounded-xl flex items-center justify-center gap-2 shadow-md transition-all"
        >
          {isUploading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Embedding & Re-indexing FAISS...</span>
            </>
          ) : (
            <>
              <Upload className="w-4 h-4" />
              <span>Upload Advisory & Update Vector Index</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
}
