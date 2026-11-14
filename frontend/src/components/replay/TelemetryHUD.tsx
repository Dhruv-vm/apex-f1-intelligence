'use client';

import React from 'react';
import { ReplayDriver, CarState } from '../../types/replay';

interface TelemetryHUDProps {
  driver: ReplayDriver | null;
  carState: CarState | null;
}

export const TelemetryHUD: React.FC<TelemetryHUDProps> = ({ driver, carState }) => {
  if (!driver) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-xl flex items-center justify-center text-slate-500 font-mono text-xs">
        Select a driver to view telemetry telemetry HUD
      </div>
    );
  }

  const speed = carState?.speed ?? 0;
  const throttle = carState?.throttle ?? 0;
  const brake = carState?.brake ?? 0;
  const gear = carState?.gear ?? 0;
  const rpm = carState?.rpm ?? 0;
  const drs = carState?.drs ?? 0;

  // DRS states in OpenF1: 0, 1 = off/eligible, 10, 12, 14 = open
  const isDrsOpen = drs >= 10;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-xl flex flex-col gap-4">
      {/* Header: Driver Info */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-3">
          <div
            className="w-3.5 h-10 rounded"
            style={{ backgroundColor: driver.color }}
          />
          <div>
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold font-mono text-white">{driver.name}</span>
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                #{driver.driver_number}
              </span>
            </div>
            <span className="text-xs font-mono text-slate-400">{driver.team}</span>
          </div>
        </div>

        {/* DRS Pill */}
        <div
          className={`px-3 py-1 rounded text-xs font-mono font-bold tracking-wider uppercase border transition ${
            isDrsOpen
              ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/50 shadow-lg shadow-emerald-500/20'
              : 'bg-slate-800 text-slate-500 border-slate-700'
          }`}
        >
          DRS {isDrsOpen ? 'ACTIVE' : 'OFF'}
        </div>
      </div>

      {/* Main Gauges: Speed & Gear */}
      <div className="grid grid-cols-2 gap-4">
        {/* Speedometer */}
        <div className="bg-slate-950 p-3 rounded-lg border border-slate-800/80 flex flex-col items-center">
          <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">
            Vehicle Speed
          </span>
          <div className="flex items-baseline gap-1 mt-1">
            <span className="text-3xl font-mono font-black text-amber-400 tracking-tight">
              {speed}
            </span>
            <span className="text-xs font-mono text-slate-500">km/h</span>
          </div>
        </div>

        {/* Current Gear */}
        <div className="bg-slate-950 p-3 rounded-lg border border-slate-800/80 flex flex-col items-center">
          <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">
            Current Gear
          </span>
          <div className="mt-1">
            <span className="text-3xl font-mono font-black text-white">
              {gear > 0 ? gear : gear === 0 ? 'N' : 'R'}
            </span>
          </div>
        </div>
      </div>

      {/* Throttle & Brake Pedals */}
      <div className="flex flex-col gap-2 bg-slate-950 p-3 rounded-lg border border-slate-800/80">
        {/* Throttle */}
        <div>
          <div className="flex justify-between text-[11px] font-mono mb-1">
            <span className="text-emerald-400 font-semibold">THROTTLE</span>
            <span className="text-slate-400">{throttle}%</span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-2.5 overflow-hidden">
            <div
              className="bg-emerald-500 h-2.5 rounded-full transition-all duration-75"
              style={{ width: `${Math.min(100, Math.max(0, throttle))}%` }}
            />
          </div>
        </div>

        {/* Brake */}
        <div>
          <div className="flex justify-between text-[11px] font-mono mb-1">
            <span className="text-red-500 font-semibold">BRAKE</span>
            <span className="text-slate-400">{brake}%</span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-2.5 overflow-hidden">
            <div
              className="bg-red-600 h-2.5 rounded-full transition-all duration-75"
              style={{ width: `${Math.min(100, Math.max(0, brake))}%` }}
            />
          </div>
        </div>
      </div>

      {/* RPM Readout */}
      <div className="flex items-center justify-between bg-slate-950 px-3 py-2 rounded-lg border border-slate-800/80 text-xs font-mono">
        <span className="text-slate-500 uppercase tracking-wider text-[10px]">Engine RPM</span>
        <span className="text-slate-200 font-bold">{rpm ? `${rpm.toLocaleString()} RPM` : '—'}</span>
      </div>
    </div>
  );
};
