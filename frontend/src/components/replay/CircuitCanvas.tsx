'use client';

import React, { useEffect, useRef, useState } from 'react';
import { CircuitGeometry, ReplayDriver, CarState } from '../../types/replay';

interface CircuitCanvasProps {
  geometry: CircuitGeometry | null;
  cars: Record<string, CarState>;
  drivers: Record<number, ReplayDriver>;
  selectedDriverNumber: number | null;
  onSelectDriver: (driverNumber: number) => void;
  width?: number;
  height?: number;
}

export const CircuitCanvas: React.FC<CircuitCanvasProps> = ({
  geometry,
  cars,
  drivers,
  selectedDriverNumber,
  onSelectDriver,
  width = 620,
  height = 650,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [zoom, setZoom] = useState<number>(1.0);
  const [followDriver, setFollowDriver] = useState<boolean>(false);
  const [showCorners, setShowCorners] = useState<boolean>(true);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Handle high-DPI displays
    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);

    // 1. Clear background
    ctx.fillStyle = '#0b0f19'; // Deep asphalt navy
    ctx.fillRect(0, 0, width, height);

    // Grid lines for high-tech telemetry aesthetic
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.03)';
    ctx.lineWidth = 1;
    const gridSize = 40;
    for (let x = 0; x < width; x += gridSize) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }
    for (let y = 0; y < height; y += gridSize) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }

    if (!geometry || !geometry.normalized_centerline || geometry.normalized_centerline.length === 0) {
      ctx.fillStyle = '#64748b';
      ctx.font = '14px monospace';
      ctx.textAlign = 'center';
      ctx.fillText('Awaiting circuit geometry...', width / 2, height / 2);
      return;
    }

    // Determine focus center for zoom/follow
    let centerX = 0.5;
    let centerY = 0.5;
    if (followDriver && selectedDriverNumber && cars[selectedDriverNumber.toString()]) {
      const targetCar = cars[selectedDriverNumber.toString()];
      centerX = targetCar.norm_x;
      centerY = targetCar.norm_y;
    }

    // Helper to map normalized [0, 1] coords to Canvas pixel coords with zoom/pan
    const toPx = (normX: number, normY: number) => {
      const localX = (normX - centerX) * zoom + 0.5;
      const localY = (normY - centerY) * zoom + 0.5;
      return {
        x: localX * width,
        y: (1.0 - localY) * height,
      };
    };

    const pts = geometry.normalized_centerline;

    // 2. Draw Track Border / Kerb Glow
    ctx.save();
    ctx.beginPath();
    const p0 = toPx(pts[0].x, pts[0].y);
    ctx.moveTo(p0.x, p0.y);
    for (let i = 1; i < pts.length; i++) {
      const p = toPx(pts[i].x, pts[i].y);
      ctx.lineTo(p.x, p.y);
    }
    ctx.closePath();
    ctx.strokeStyle = 'rgba(56, 189, 248, 0.15)'; // Cyan ambient glow
    ctx.lineWidth = 16 * zoom;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.stroke();

    // 3. Draw Track Asphalt Ribbon
    ctx.strokeStyle = '#1e293b'; // Slate track surface
    ctx.lineWidth = 9 * zoom;
    ctx.stroke();

    // 4. Draw Racing Line / Centerline
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.4)';
    ctx.lineWidth = Math.max(1, 2 * zoom);
    ctx.setLineDash([4 * zoom, 4 * zoom]);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.restore();

    // 5. Draw Sector Splits (S1, S2)
    geometry.sectors.forEach((sec) => {
      const sp = toPx(sec.point.x, sec.point.y);
      ctx.save();
      ctx.fillStyle = '#f59e0b';
      ctx.strokeStyle = '#f59e0b';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(sp.x, sp.y, Math.max(3, 4 * zoom), 0, Math.PI * 2);
      ctx.fill();

      ctx.font = '10px monospace';
      ctx.fillStyle = '#fbbf24';
      ctx.fillText(`S${sec.sector}`, sp.x + 8, sp.y - 6);
      ctx.restore();
    });

    // 6. Draw Corner / Turn Markers
    if (showCorners && geometry.corners) {
      geometry.corners.forEach((c) => {
        const cp = toPx(c.point.x, c.point.y);
        ctx.save();
        ctx.fillStyle = 'rgba(148, 163, 184, 0.8)';
        ctx.font = '9px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(`T${c.number}`, cp.x, cp.y - 8);
        ctx.restore();
      });
    }

    // 7. Draw Start / Finish Line
    if (geometry.start_finish) {
      const sf = toPx(geometry.start_finish.x, geometry.start_finish.y);
      ctx.save();
      ctx.fillStyle = '#ef4444';
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(sf.x, sf.y, Math.max(4, 5 * zoom), 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
      ctx.font = 'bold 10px monospace';
      ctx.fillStyle = '#ffffff';
      ctx.fillText('FINISH', sf.x + 8, sf.y + 4);
      ctx.restore();
    }

    // 8. Draw Active Cars
    const carList = Object.values(cars);
    carList.forEach((car) => {
      const pos = toPx(car.norm_x, car.norm_y);
      const driver = drivers[car.driver_number];
      const color = driver ? driver.color : '#e2e8f0';
      const code = driver ? driver.code : `${car.driver_number}`;
      const isSelected = selectedDriverNumber === car.driver_number;

      ctx.save();

      // Selected halo
      if (isSelected) {
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, 14 * zoom, 0, Math.PI * 2);
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.setLineDash([3, 3]);
        ctx.stroke();
        ctx.setLineDash([]);

        ctx.fillStyle = `${color}33`;
        ctx.fill();
      }

      // Outer team ring
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, Math.max(6, 8 * zoom), 0, Math.PI * 2);
      ctx.fillStyle = '#0f172a';
      ctx.fill();
      ctx.strokeStyle = color;
      ctx.lineWidth = isSelected ? 3 : 2;
      ctx.stroke();

      // Inner dot
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, Math.max(3, 4 * zoom), 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();

      // Driver Acronym Tag
      ctx.font = isSelected ? 'bold 11px monospace' : '9px monospace';
      ctx.fillStyle = isSelected ? '#ffffff' : 'rgba(255, 255, 255, 0.85)';
      ctx.textAlign = 'center';
      ctx.fillText(code, pos.x, pos.y - 10 * zoom);

      ctx.restore();
    });
  }, [geometry, cars, drivers, selectedDriverNumber, width, height, zoom, followDriver, showCorners]);

  // Click on canvas to select driver closest to cursor
  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;

    let centerX = 0.5;
    let centerY = 0.5;
    if (followDriver && selectedDriverNumber && cars[selectedDriverNumber.toString()]) {
      const targetCar = cars[selectedDriverNumber.toString()];
      centerX = targetCar.norm_x;
      centerY = targetCar.norm_y;
    }

    let closestDriver: number | null = null;
    let minDistance = 25; // 25px hit target radius

    Object.values(cars).forEach((car) => {
      const localX = (car.norm_x - centerX) * zoom + 0.5;
      const localY = (car.norm_y - centerY) * zoom + 0.5;
      const carPxX = localX * width;
      const carPxY = (1.0 - localY) * height;
      const dist = Math.hypot(clickX - carPxX, clickY - carPxY);
      if (dist < minDistance) {
        minDistance = dist;
        closestDriver = car.driver_number;
      }
    });

    if (closestDriver !== null) {
      onSelectDriver(closestDriver);
    }
  };

  return (
    <div className="relative inline-block border border-slate-800 rounded-xl overflow-hidden shadow-2xl bg-slate-950">
      <canvas
        ref={canvasRef}
        style={{ width: `${width}px`, height: `${height}px` }}
        onClick={handleCanvasClick}
        className="cursor-crosshair block"
      />

      {/* Top Left: Circuit Details & Validation Pill */}
      <div className="absolute top-3 left-3 bg-slate-900/90 backdrop-blur-md px-3 py-1.5 rounded-lg border border-slate-700 text-xs font-mono text-slate-300 flex items-center gap-2">
        <span className="font-semibold text-white">{geometry?.name || 'Circuit'}</span>
        <span className="text-amber-400 font-bold">{geometry?.length_meters || 0}m</span>
        <span className="px-1.5 py-0.5 rounded text-[10px] bg-emerald-500/20 text-emerald-400 border border-emerald-500/40">
          {geometry?.validation_status || 'VERIFIED'}
        </span>
      </div>

      {/* Top Right: Zoom & Follow Controls */}
      <div className="absolute top-3 right-3 bg-slate-900/90 backdrop-blur-md p-1 rounded-lg border border-slate-700 flex items-center gap-1">
        <button
          onClick={() => setZoom((z) => Math.min(2.5, z + 0.25))}
          className="px-2 py-0.5 rounded text-xs font-mono text-slate-300 hover:bg-slate-800"
          title="Zoom In"
        >
          +
        </button>
        <button
          onClick={() => setZoom((z) => Math.max(0.75, z - 0.25))}
          className="px-2 py-0.5 rounded text-xs font-mono text-slate-300 hover:bg-slate-800"
          title="Zoom Out"
        >
          -
        </button>
        <button
          onClick={() => {
            setZoom(1.0);
            setFollowDriver(false);
          }}
          className="px-2 py-0.5 rounded text-[10px] font-mono text-slate-400 hover:bg-slate-800"
          title="Reset View"
        >
          Reset
        </button>
        <div className="h-3 w-px bg-slate-700 mx-0.5" />
        <button
          onClick={() => setFollowDriver(!followDriver)}
          className={`px-2 py-0.5 rounded text-[10px] font-mono transition ${
            followDriver
              ? 'bg-red-600 text-white font-bold'
              : 'text-slate-400 hover:bg-slate-800'
          }`}
          title="Follow Selected Driver"
        >
          Follow {followDriver ? 'ON' : 'OFF'}
        </button>
        <button
          onClick={() => setShowCorners(!showCorners)}
          className={`px-2 py-0.5 rounded text-[10px] font-mono transition ${
            showCorners
              ? 'bg-slate-800 text-amber-400'
              : 'text-slate-500 hover:bg-slate-800'
          }`}
          title="Toggle Turn Markers"
        >
          Turns
        </button>
      </div>

      {/* Bottom Info Bar */}
      <div className="absolute bottom-3 left-3 right-3 bg-slate-900/85 backdrop-blur-md px-3 py-1.5 rounded border border-slate-800 text-[10px] font-mono text-slate-400 flex items-center justify-between">
        <span className="truncate max-w-[400px]">
          {geometry?.provenance || 'Verified multi-driver telemetry'}
        </span>
        <span className="text-slate-500">Click car marker to inspect</span>
      </div>
    </div>
  );
};
