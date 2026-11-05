import React from 'react';
import { Play, Pause, RotateCcw, Volume2, Gauge } from 'lucide-react';

export default function AudioPlayer({ isPlaying, onToggle, speed, onSpeedChange, onReplay }) {
  const speeds = [0.8, 1.0, 1.2];

  return (
    <div className="flex items-center justify-between bg-agri-900 text-white px-4 py-2.5 rounded-2xl shadow-lg border border-agri-800">
      <div className="flex items-center space-x-3">
        <button
          onClick={onToggle}
          className="w-9 h-9 rounded-full bg-agri-500 hover:bg-agri-400 text-white flex items-center justify-center transition-colors shadow"
          title={isPlaying ? 'Pause voice' : 'Play voice'}
        >
          {isPlaying ? <Pause className="w-4 h-4 fill-current" /> : <Play className="w-4 h-4 fill-current ml-0.5" />}
        </button>

        <div className="flex items-center space-x-2">
          <Volume2 className="w-4 h-4 text-agri-300 animate-pulse" />
          <span className="text-xs font-semibold text-agri-100">
            {isPlaying ? 'Playing KisanVani Voice...' : 'Listen Advisory'}
          </span>
        </div>
      </div>

      <div className="flex items-center space-x-2">
        {/* Speed Selector */}
        <div className="flex items-center space-x-1 bg-agri-800/80 rounded-lg p-0.5 border border-agri-700 text-[11px]">
          {speeds.map((s) => (
            <button
              key={s}
              onClick={() => onSpeedChange(s)}
              className={`px-2 py-0.5 rounded-md font-semibold transition-colors ${
                speed === s ? 'bg-agri-600 text-white' : 'text-agri-300 hover:text-white'
              }`}
            >
              {s}x
            </button>
          ))}
        </div>

        {/* Replay */}
        {onReplay && (
          <button
            onClick={onReplay}
            className="p-1.5 text-agri-300 hover:text-white rounded-lg hover:bg-agri-800 transition-colors"
            title="Replay from start"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
}
