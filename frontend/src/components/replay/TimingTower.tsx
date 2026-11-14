'use client';

import React from 'react';
import { ReplayDriver, CarState } from '../../types/replay';

interface TimingTowerProps {
  drivers: Record<number, ReplayDriver>;
  cars: Record<string, CarState>;
  selectedDriverNumber: number | null;
  onSelectDriver: (driverNumber: number) => void;
}

export const TimingTower: React.FC<TimingTowerProps> = ({
  drivers,
  cars,
  selectedDriverNumber,
  onSelectDriver,
}) => {
  // Sort drivers: if we have cars, sort by speed descending or driver number
  const driverList = Object.values(drivers);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl flex flex-col h-[650px] w-72">
      <div className="bg-slate-950 px-4 py-3 border-b border-slate-800 flex items-center justify-between">
        <h3 className="text-xs font-mono font-bold tracking-wider uppercase text-slate-300">
          Timing Tower
        </h3>
        <span className="text-[11px] font-mono text-slate-500">
          {Object.keys(cars).length} Active
        </span>
      </div>

      <div className="overflow-y-auto flex-1 divide-y divide-slate-800/60 custom-scrollbar">
        {driverList.map((driver, idx) => {
          const car = cars[driver.driver_number.toString()];
          const isSelected = selectedDriverNumber === driver.driver_number;
          const speed = car?.speed ?? null;
          const gear = car?.gear ?? null;

          return (
            <div
              key={driver.driver_number}
              onClick={() => onSelectDriver(driver.driver_number)}
              className={`flex items-center px-3 py-2 text-xs font-mono cursor-pointer transition select-none ${
                isSelected
                  ? 'bg-slate-800/90 border-l-4'
                  : 'hover:bg-slate-800/40 border-l-4 border-l-transparent'
              }`}
              style={{
                borderLeftColor: isSelected ? driver.color : undefined,
              }}
            >
              {/* Position / Index */}
              <span className="w-5 text-slate-500 font-bold">{idx + 1}</span>

              {/* Team Color Pill */}
              <span
                className="w-1.5 h-4 rounded-sm mr-2"
                style={{ backgroundColor: driver.color }}
              />

              {/* Driver Code & Number */}
              <div className="flex-1 flex flex-col">
                <div className="flex items-center gap-1.5">
                  <span className={`font-bold ${isSelected ? 'text-white' : 'text-slate-200'}`}>
                    {driver.code}
                  </span>
                  <span className="text-[10px] text-slate-500">#{driver.driver_number}</span>
                </div>
                <span className="text-[10px] text-slate-400 truncate max-w-[90px]">
                  {driver.team}
                </span>
              </div>

              {/* Live Speed & Gear */}
              <div className="flex flex-col items-end">
                <span className="font-bold text-amber-400">
                  {speed !== null ? `${speed} km/h` : '—'}
                </span>
                <span className="text-[10px] text-slate-400">
                  {gear !== null ? `G${gear}` : ''}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
