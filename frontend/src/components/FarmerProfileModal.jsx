import React, { useState } from 'react';
import { X, MapPin, Sprout, Layers, Save } from 'lucide-react';
import { INDIAN_STATES, MAJOR_CROPS, SOIL_TYPES } from '../utils/constants';

export default function FarmerProfileModal({ isOpen, onClose, context, onSaveContext }) {
  const [formData, setFormData] = useState({
    state: context.state || 'Maharashtra',
    district: context.district || '',
    cropName: context.cropName || 'Cotton (कपास)',
    soilType: context.soilType || 'Black Soil (काली मिट्टी)',
    landSize: context.landSize || 2.5,
  });

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    onSaveContext(formData);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl max-w-lg w-full p-6 shadow-2xl border border-stone-100 animate-in fade-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between pb-4 border-b border-stone-100">
          <div>
            <h3 className="font-bold text-lg text-stone-900">Farm Context & Profile / खेत की जानकारी</h3>
            <p className="text-xs text-stone-500">Helps Gemini tailor specific dosages for your land</p>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-stone-100 flex items-center justify-center text-stone-500 hover:bg-stone-200"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          {/* State */}
          <div>
            <label className="block text-xs font-semibold text-stone-700 mb-1 flex items-center gap-1.5">
              <MapPin className="w-3.5 h-3.5 text-agri-600" /> State / राज्य
            </label>
            <select
              value={formData.state}
              onChange={(e) => setFormData({ ...formData, state: e.target.value })}
              className="w-full text-sm rounded-xl border border-stone-200 p-2.5 bg-stone-50 focus:bg-white focus:ring-2 focus:ring-agri-500 outline-none"
            >
              {INDIAN_STATES.map((st) => (
                <option key={st} value={st}>{st}</option>
              ))}
            </select>
          </div>

          {/* Crop */}
          <div>
            <label className="block text-xs font-semibold text-stone-700 mb-1 flex items-center gap-1.5">
              <Sprout className="w-3.5 h-3.5 text-agri-600" /> Current Crop / मुख्य फसल
            </label>
            <select
              value={formData.cropName}
              onChange={(e) => setFormData({ ...formData, cropName: e.target.value })}
              className="w-full text-sm rounded-xl border border-stone-200 p-2.5 bg-stone-50 focus:bg-white focus:ring-2 focus:ring-agri-500 outline-none"
            >
              {MAJOR_CROPS.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          {/* Soil Type */}
          <div>
            <label className="block text-xs font-semibold text-stone-700 mb-1 flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-agri-600" /> Soil Type / मिट्टी का प्रकार
            </label>
            <select
              value={formData.soilType}
              onChange={(e) => setFormData({ ...formData, soilType: e.target.value })}
              className="w-full text-sm rounded-xl border border-stone-200 p-2.5 bg-stone-50 focus:bg-white focus:ring-2 focus:ring-agri-500 outline-none"
            >
              {SOIL_TYPES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>

          {/* Land Size */}
          <div>
            <label className="block text-xs font-semibold text-stone-700 mb-1">
              Land Holding (Acres) / जमीन (एकड़ में)
            </label>
            <input
              type="number"
              step="0.5"
              min="0.1"
              value={formData.landSize}
              onChange={(e) => setFormData({ ...formData, landSize: parseFloat(e.target.value) || 1 })}
              className="w-full text-sm rounded-xl border border-stone-200 p-2.5 bg-stone-50 focus:bg-white focus:ring-2 focus:ring-agri-500 outline-none"
            />
          </div>

          <div className="pt-3">
            <button
              type="submit"
              className="w-full py-3 bg-agri-600 hover:bg-agri-700 text-white font-semibold text-sm rounded-xl flex items-center justify-center gap-2 shadow-md shadow-agri-600/20 transition-all"
            >
              <Save className="w-4 h-4" /> Save Preferences / सहेजें
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
