import React from 'react';
import { X, Check } from 'lucide-react';
import { SUPPORTED_LANGUAGES } from '../utils/constants';

export default function LanguageSelector({ isOpen, onClose, selectedLang, onSelectLang }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border border-stone-100 animate-in fade-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between pb-4 border-b border-stone-100">
          <div>
            <h3 className="font-bold text-lg text-stone-900">Select Language / भाषा चुनें</h3>
            <p className="text-xs text-stone-500">Choose your preferred vernacular dialect</p>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-stone-100 flex items-center justify-center text-stone-500 hover:bg-stone-200"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="grid grid-cols-2 gap-3 mt-5">
          {SUPPORTED_LANGUAGES.map((lang) => {
            const isSelected = selectedLang?.code === lang.code;
            return (
              <button
                key={lang.code}
                onClick={() => {
                  onSelectLang(lang);
                  onClose();
                }}
                className={`flex flex-col items-start p-3.5 rounded-2xl border text-left transition-all ${
                  isSelected
                    ? 'border-agri-600 bg-agri-50/70 text-agri-950 font-semibold ring-2 ring-agri-500/20'
                    : 'border-stone-200 hover:border-stone-300 hover:bg-stone-50 text-stone-700'
                }`}
              >
                <div className="flex items-center justify-between w-full">
                  <span className="text-base font-bold text-stone-900">{lang.nativeName}</span>
                  {isSelected && <Check className="w-4 h-4 text-agri-600" />}
                </div>
                <span className="text-xs text-stone-500 mt-0.5">{lang.name}</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
