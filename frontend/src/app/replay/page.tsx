'use client';

import React, { useEffect, useState, useRef, useMemo } from 'react';
import Link from 'next/link';
import { apexApi } from '../../lib/api-client';
import { CircuitGeometry, ReplayManifest, ReplayFrame, ReplayDriver, CarState } from '../../types/replay';
import { CircuitCanvas } from '../../components/replay/CircuitCanvas';
import { ReplayControls } from '../../components/replay/ReplayControls';
import { TimingTower } from '../../components/replay/TimingTower';
import { TelemetryHUD } from '../../components/replay/TelemetryHUD';

interface EventOption {
  id: number;
  name: string;
  circuitRef: string;
  circuitName: string;
  sessionId: number;
  sessionName: string;
}

const AVAILABLE_REPLAY_EVENTS: EventOption[] = [
  {
    id: 1,
    name: '2024 Abu Dhabi Grand Prix (Round 24)',
    circuitRef: 'yas_marina',
    circuitName: 'Yas Marina Circuit',
    sessionId: 9662,
    sessionName: 'Race (Opening Lap Replay)',
  },
  {
    id: 2,
    name: '2024 British Grand Prix (Round 12)',
    circuitRef: 'silverstone',
    circuitName: 'Silverstone Circuit',
    sessionId: 9558,
    sessionName: 'Race (Opening Lap Replay)',
  },
];

export default function ReplayPage() {
  const [selectedEventId, setSelectedEventId] = useState<number>(AVAILABLE_REPLAY_EVENTS[0].id);
  const [geometry, setGeometry] = useState<CircuitGeometry | null>(null);
  const [manifest, setManifest] = useState<ReplayManifest | null>(null);
  const [frames, setFrames] = useState<ReplayFrame[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Playback state
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [currentTimeMs, setCurrentTimeMs] = useState<number>(0);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1.0);
  const [selectedDriverNumber, setSelectedDriverNumber] = useState<number | null>(4); // Norris by default

  const lastAnimTimeRef = useRef<number | null>(null);
  const animFrameIdRef = useRef<number | null>(null);

  const currentEvent = useMemo(
    () => AVAILABLE_REPLAY_EVENTS.find((e) => e.id === selectedEventId) || AVAILABLE_REPLAY_EVENTS[0],
    [selectedEventId]
  );

  // Load Event Geometry, Manifest, and Frames when event changes
  useEffect(() => {
    let isMounted = true;
    setIsPlaying(false);
    setFrames([]);
    setGeometry(null);
    setManifest(null);

    async function loadEventData() {
      try {
        setLoading(true);
        setError(null);

        // Fetch circuit geometry & manifest in parallel
        const [geomData, manifestData] = await Promise.all([
          apexApi.getCircuitGeometry(currentEvent.circuitRef),
          apexApi.getReplayManifest(currentEvent.sessionId),
        ]);

        if (!isMounted) return;
        setGeometry(geomData);
        setManifest(manifestData);
        setCurrentTimeMs(manifestData.start_epoch_ms);

        // Select first driver or Norris if present
        if (manifestData.drivers.length > 0) {
          const hasNorris = manifestData.drivers.some((d) => d.driver_number === 4);
          setSelectedDriverNumber(hasNorris ? 4 : manifestData.drivers[0].driver_number);
        }

        // Fetch full frame sequence
        const framesData = await apexApi.getReplayFrames(
          currentEvent.sessionId,
          manifestData.start_epoch_ms,
          manifestData.end_epoch_ms,
          250 // 4.0 Hz smooth frame resolution
        );

        if (!isMounted) return;
        setFrames(framesData.frames);
      } catch (err: unknown) {
        if (!isMounted) return;
        console.error('Failed to load replay data:', err);
        setError(err instanceof Error ? err.message : 'Unknown error loading replay');
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    loadEventData();
    return () => {
      isMounted = false;
    };
  }, [currentEvent]);

  // Map drivers dictionary by driver_number for quick lookup
  const driversMap = useMemo<Record<number, ReplayDriver>>(() => {
    if (!manifest) return {};
    const map: Record<number, ReplayDriver> = {};
    manifest.drivers.forEach((d) => {
      map[d.driver_number] = d;
    });
    return map;
  }, [manifest]);

  // Find the closest frame at or before currentTimeMs (strict causal ordering)
  const currentFrame = useMemo<ReplayFrame | null>(() => {
    if (!frames || frames.length === 0) return null;

    let bestFrame: ReplayFrame = frames[0];
    for (let i = 0; i < frames.length; i++) {
      if (frames[i].timestamp_ms <= currentTimeMs) {
        bestFrame = frames[i];
      } else {
        break; // Frames are sorted monotonically
      }
    }
    return bestFrame;
  }, [frames, currentTimeMs]);

  const activeCars = useMemo<Record<string, CarState>>(() => {
    return currentFrame ? currentFrame.cars : {};
  }, [currentFrame]);

  // High-Precision Animation Loop
  useEffect(() => {
    if (!isPlaying || !manifest) {
      lastAnimTimeRef.current = null;
      if (animFrameIdRef.current) {
        cancelAnimationFrame(animFrameIdRef.current);
        animFrameIdRef.current = null;
      }
      return;
    }

    const animate = (perfTime: number) => {
      if (lastAnimTimeRef.current === null) {
        lastAnimTimeRef.current = perfTime;
      }

      const deltaMs = (perfTime - lastAnimTimeRef.current) * playbackSpeed;
      lastAnimTimeRef.current = perfTime;

      setCurrentTimeMs((prev) => {
        const nextTime = prev + deltaMs;
        if (nextTime >= manifest.end_epoch_ms) {
          setIsPlaying(false);
          return manifest.end_epoch_ms;
        }
        return nextTime;
      });

      animFrameIdRef.current = requestAnimationFrame(animate);
    };

    animFrameIdRef.current = requestAnimationFrame(animate);

    return () => {
      if (animFrameIdRef.current) {
        cancelAnimationFrame(animFrameIdRef.current);
      }
    };
  }, [isPlaying, playbackSpeed, manifest]);

  const selectedDriver = selectedDriverNumber !== null ? driversMap[selectedDriverNumber] || null : null;
  const selectedCarState = selectedDriverNumber !== null ? activeCars[selectedDriverNumber.toString()] || null : null;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Navbar */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50 px-6 py-3 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <Link
            href="/"
            className="text-xs font-mono text-slate-400 hover:text-white px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 transition"
          >
            ← Overview
          </Link>
          <div className="h-4 w-px bg-slate-700" />
          <div>
            <h1 className="text-base font-bold font-mono text-white flex items-center gap-2">
              <span className="text-red-500 font-black">APEX</span>
              <span className="text-slate-400 font-light">/</span>
              <span>HISTORICAL RACE REPLAY</span>
            </h1>
            <p className="text-[11px] font-mono text-slate-400">
              Multi-Circuit Coordinate Calibration & High-Frequency Multi-Car Replay
            </p>
          </div>
        </div>

        {/* Grand Prix & Session Selector */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 shadow-sm">
            <span className="text-[11px] font-mono text-slate-400 uppercase font-bold">Event:</span>
            <select
              value={selectedEventId}
              onChange={(e) => setSelectedEventId(Number(e.target.value))}
              className="bg-transparent text-xs font-mono text-white font-semibold focus:outline-none cursor-pointer"
            >
              {AVAILABLE_REPLAY_EVENTS.map((ev) => (
                <option key={ev.id} value={ev.id} className="bg-slate-900 text-white">
                  {ev.name} — {ev.circuitName}
                </option>
              ))}
            </select>
          </div>

          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-[11px] font-mono text-emerald-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            Causal Replay Active
          </span>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 p-6 flex flex-col gap-6 max-w-7xl mx-auto w-full">
        {loading && (
          <div className="flex items-center justify-center p-16 text-slate-400 font-mono text-sm">
            <div className="flex flex-col items-center gap-3">
              <div className="w-8 h-8 border-2 border-red-500 border-t-transparent rounded-full animate-spin" />
              <span>
                Loading {currentEvent.circuitName} geometry and analytical replay frames...
              </span>
            </div>
          </div>
        )}

        {error && (
          <div className="p-4 rounded-xl bg-red-950/60 border border-red-800 text-red-300 font-mono text-xs">
            Error loading replay: {error}
          </div>
        )}

        {!loading && !error && manifest && (
          <>
            {/* Interactive Grid: Timing Tower + Circuit Canvas + Telemetry HUD */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
              {/* Timing Tower (3 cols) */}
              <div className="lg:col-span-3">
                <TimingTower
                  drivers={driversMap}
                  cars={activeCars}
                  selectedDriverNumber={selectedDriverNumber}
                  onSelectDriver={(num) => setSelectedDriverNumber(num)}
                />
              </div>

              {/* Center Stage: Circuit Canvas (6 cols) */}
              <div className="lg:col-span-6 flex flex-col items-center gap-4">
                <CircuitCanvas
                  geometry={geometry}
                  cars={activeCars}
                  drivers={driversMap}
                  selectedDriverNumber={selectedDriverNumber}
                  onSelectDriver={(num) => setSelectedDriverNumber(num)}
                  width={620}
                  height={650}
                />
              </div>

              {/* Right Stage: Driver Telemetry HUD (3 cols) */}
              <div className="lg:col-span-3">
                <TelemetryHUD driver={selectedDriver} carState={selectedCarState} />
              </div>
            </div>

            {/* Bottom: Playback Controls */}
            <div className="w-full">
              <ReplayControls
                isPlaying={isPlaying}
                currentTimeMs={currentTimeMs}
                startMs={manifest.start_epoch_ms}
                endMs={manifest.end_epoch_ms}
                playbackSpeed={playbackSpeed}
                onTogglePlay={() => setIsPlaying(!isPlaying)}
                onSeek={(targetMs) => setCurrentTimeMs(targetMs)}
                onChangeSpeed={(s) => setPlaybackSpeed(s)}
                onStep={(deltaMs) => {
                  setCurrentTimeMs((prev) =>
                    Math.max(manifest.start_epoch_ms, Math.min(manifest.end_epoch_ms, prev + deltaMs))
                  );
                }}
              />
            </div>
          </>
        )}
      </main>
    </div>
  );
}
