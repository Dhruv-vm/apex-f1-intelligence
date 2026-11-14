'use client';

import React from 'react';

interface ReplayControlsProps {
  isPlaying: boolean;
  currentTimeMs: number;
  startMs: number;
  endMs: number;
  playbackSpeed: number;
  onTogglePlay: () => void;
  onSeek: (targetMs: number) => void;
  onChangeSpeed: (speed: number) => void;
  onStep: (deltaMs: number) => void;
}

export const ReplayControls: React.FC<ReplayControlsProps> = ({
  isPlaying,
  currentTimeMs,
  startMs,
  endMs,
  playbackSpeed,
  onTogglePlay,
  onSeek,
  onChangeSpeed,
  onStep,
}) => {
  const elapsedSec = Math.max(0, (currentTimeMs - startMs) / 1000);
  const totalSec = Math.max(0, (endMs - startMs) / 1000);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(1);
    return `${mins.toString().padStart(2, '0')}:${secs.padStart(4, '0')}`;
  };

  const speeds = [0.5, 1.0, 2.0, 5.0];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-xl flex flex-col gap-3">
      {/* Timeline Scrubber */}
      <div className="flex items-center gap-3">
        <span className="font-mono text-xs font-semibold text-amber-400 w-16">
          {formatTime(elapsedSec)}
        </span>
        <input
          type="range"
          min={startMs}
          max={endMs}
          step={100}
          value={currentTimeMs}
          onChange={(e) => onSeek(Number(e.target.value))}
          className="flex-1 h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-red-600 focus:outline-none"
        />
        <span className="font-mono text-xs text-slate-400 w-16 text-right">
          {formatTime(totalSec)}
        </span>
      </div>

      {/* Action Buttons & Speed Selector */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {/* Step Back */}
          <button
            onClick={() => onStep(-1000)}
            className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-mono border border-slate-700 transition"
            title="Step back 1s"
          >
            -1s
          </button>

          {/* Play / Pause */}
          <button
            onClick={onTogglePlay}
            className={`px-5 py-1.5 rounded-lg font-bold text-xs font-mono uppercase tracking-wider transition ${
              isPlaying
                ? 'bg-amber-500 hover:bg-amber-600 text-slate-950'
                : 'bg-red-600 hover:bg-red-500 text-white'
            }`}
          >
            {isPlaying ? 'Pause' : 'Play'}
          </button>

          {/* Step Forward */}
          <button
            onClick={() => onStep(1000)}
            className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-mono border border-slate-700 transition"
            title="Step forward 1s"
          >
            +1s
          </button>

          {/* Reset to Start */}
          <button
            onClick={() => onSeek(startMs)}
            className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 text-xs font-mono border border-slate-700 transition"
            title="Jump to Start"
          >
            Reset
          </button>
        </div>

        {/* Speed Selector */}
        <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800">
          {speeds.map((s) => (
            <button
              key={s}
              onClick={() => onChangeSpeed(s)}
              className={`px-2 py-0.5 rounded text-[11px] font-mono transition ${
                playbackSpeed === s
                  ? 'bg-red-600 text-white font-bold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {s}x
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
