'use client';

import React, { useEffect, useState } from 'react';
import { apexApi } from '../lib/api-client';
import { Event, Session, RaceResult, HealthResponse } from '../types/api';

export default function HomePage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [events, setEvents] = useState<Event[]>([]);
  const [selectedEventId, setSelectedEventId] = useState<number | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [results, setResults] = useState<RaceResult[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadInitial() {
      try {
        setLoading(true);
        const [healthData, eventsData] = await Promise.all([
          apexApi.getHealth().catch(() => null),
          apexApi.getEvents(),
        ]);
        setHealth(healthData);
        setEvents(eventsData);
        if (eventsData.length > 0) {
          setSelectedEventId(eventsData[0].id);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to connect to APEX Backend');
      } finally {
        setLoading(false);
      }
    }
    loadInitial();
  }, []);

  useEffect(() => {
    if (selectedEventId === null) return;
    const eventId = selectedEventId;

    async function loadEventData() {
      try {
        const [sessData, resData] = await Promise.all([
          apexApi.getEventSessions(eventId),
          apexApi.getEventResults(eventId),
        ]);
        setSessions(sessData);
        setResults(resData);
      } catch (err: any) {
        console.error('Failed to load event data:', err);
      }
    }
    loadEventData();
  }, [selectedEventId]);

  const selectedEvent = events.find((e) => e.id === selectedEventId);

  return (
    <main style={{ maxWidth: 1200, margin: '0 auto', padding: '32px 24px' }}>
      {/* Header */}
      <header
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderBottom: '1px solid #1e293b',
          paddingBottom: 20,
          marginBottom: 32,
        }}
      >
        <div>
          <h1 style={{ margin: 0, fontSize: 28, fontWeight: 700, color: '#f8fafc' }}>
            APEX <span style={{ color: '#e10600', fontSize: 20 }}>// F1 INTELLIGENCE</span>
          </h1>
          <p style={{ margin: '4px 0 0 0', color: '#94a3b8', fontSize: 14 }}>
            Phase 1 & 2: Backend Foundation & Historical Race Replay Engine
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <a
            href="/simulation"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              backgroundColor: '#e10600',
              color: '#ffffff',
              padding: '6px 14px',
              borderRadius: 6,
              fontSize: 12,
              fontWeight: 600,
              textDecoration: 'none',
              fontFamily: 'monospace',
            }}
          >
            Strategy Simulator →
          </a>
          <a
            href="/replay"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              backgroundColor: '#1e293b',
              color: '#f8fafc',
              border: '1px solid #334155',
              padding: '6px 14px',
              borderRadius: 6,
              fontSize: 12,
              fontWeight: 600,
              textDecoration: 'none',
              fontFamily: 'monospace',
            }}
          >
            Race Replay →
          </a>
          {health ? (
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                backgroundColor: '#064e3b',
                color: '#6ee7b7',
                padding: '6px 12px',
                borderRadius: 9999,
                fontSize: 12,
                fontWeight: 600,
              }}
            >
              <span
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  backgroundColor: '#10b981',
                }}
              />
              API v{health.version} ({health.database})
            </div>
          ) : (
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                backgroundColor: '#7f1d1d',
                color: '#fca5a5',
                padding: '6px 12px',
                borderRadius: 9999,
                fontSize: 12,
                fontWeight: 600,
              }}
            >
              Backend Offline
            </div>
          )}
        </div>
      </header>

      {error && (
        <div
          style={{
            backgroundColor: '#450a0a',
            border: '1px solid #991b1b',
            color: '#fecaca',
            padding: '12px 16px',
            borderRadius: 8,
            marginBottom: 24,
            fontSize: 14,
          }}
        >
          {error}
        </div>
      )}

      {/* Event Selector */}
      <section style={{ marginBottom: 32 }}>
        <h2 style={{ fontSize: 18, color: '#cbd5e1', marginBottom: 12 }}>
          Select Grand Prix Event
        </h2>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          {events.map((ev) => (
            <button
              key={ev.id}
              onClick={() => setSelectedEventId(ev.id)}
              style={{
                backgroundColor: selectedEventId === ev.id ? '#e10600' : '#1e293b',
                color: '#ffffff',
                border: 'none',
                borderRadius: 6,
                padding: '10px 18px',
                cursor: 'pointer',
                fontWeight: 600,
                fontSize: 14,
                transition: 'background-color 0.15s',
              }}
            >
              {ev.season_year} R{ev.round}: {ev.event_name}
            </button>
          ))}
          {events.length === 0 && !loading && (
            <p style={{ color: '#64748b' }}>No events persisted in database yet.</p>
          )}
        </div>
      </section>

      {selectedEvent && (
        <>
          {/* Circuit Info Card */}
          <div
            style={{
              backgroundColor: '#0f172a',
              border: '1px solid #1e293b',
              borderRadius: 8,
              padding: 20,
              marginBottom: 28,
            }}
          >
            <h3 style={{ margin: '0 0 8px 0', fontSize: 20, color: '#f1f5f9' }}>
              {selectedEvent.event_name} ({selectedEvent.season_year})
            </h3>
            <p style={{ margin: 0, color: '#94a3b8', fontSize: 14 }}>
              Circuit: <strong style={{ color: '#f8fafc' }}>{selectedEvent.circuit.name}</strong> ({selectedEvent.circuit.location}, {selectedEvent.circuit.country})
              {' — '}Date: {selectedEvent.date} {selectedEvent.time || ''}
            </p>
          </div>

          {/* Sessions Overview */}
          <section style={{ marginBottom: 32 }}>
            <h3 style={{ fontSize: 18, color: '#cbd5e1', marginBottom: 14 }}>
              Grand Prix Sessions ({sessions.length})
            </h3>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: 12,
              }}
            >
              {sessions.map((s) => (
                <div
                  key={s.id}
                  style={{
                    backgroundColor: '#111827',
                    border: '1px solid #1f2937',
                    borderRadius: 6,
                    padding: 14,
                  }}
                >
                  <div style={{ color: '#e10600', fontSize: 12, fontWeight: 700, textTransform: 'uppercase' }}>
                    {s.session_type}
                  </div>
                  <div style={{ color: '#f9fafb', fontSize: 16, fontWeight: 600, margin: '4px 0' }}>
                    {s.session_name}
                  </div>
                  <div style={{ color: '#9ca3af', fontSize: 12 }}>
                    {s.date_start ? new Date(s.date_start).toLocaleString() : 'Date TBD'}
                  </div>
                  {s.source_session_key && (
                    <div style={{ color: '#6b7280', fontSize: 11, marginTop: 4 }}>
                      OpenF1 Key: {s.source_session_key}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>

          {/* Race Results Table */}
          <section>
            <h3 style={{ fontSize: 18, color: '#cbd5e1', marginBottom: 14 }}>
              Race Classification ({results.length} Drivers)
            </h3>
            <div
              style={{
                overflowX: 'auto',
                backgroundColor: '#0f172a',
                borderRadius: 8,
                border: '1px solid #1e293b',
              }}
            >
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: 14 }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #334155', color: '#94a3b8' }}>
                    <th style={{ padding: '12px 16px' }}>Pos</th>
                    <th style={{ padding: '12px 16px' }}>No</th>
                    <th style={{ padding: '12px 16px' }}>Driver</th>
                    <th style={{ padding: '12px 16px' }}>Constructor</th>
                    <th style={{ padding: '12px 16px' }}>Grid</th>
                    <th style={{ padding: '12px 16px' }}>Laps</th>
                    <th style={{ padding: '12px 16px' }}>Time / Status</th>
                    <th style={{ padding: '12px 16px' }}>Points</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((res) => (
                    <tr
                      key={res.id}
                      style={{
                        borderBottom: '1px solid #1e293b',
                        backgroundColor: res.position === 1 ? 'rgba(225, 6, 0, 0.08)' : 'transparent',
                      }}
                    >
                      <td style={{ padding: '12px 16px', fontWeight: 700, color: res.position === 1 ? '#ef4444' : '#f8fafc' }}>
                        {res.position_text}
                      </td>
                      <td style={{ padding: '12px 16px', color: '#94a3b8' }}>
                        {res.number || '—'}
                      </td>
                      <td style={{ padding: '12px 16px', fontWeight: 600, color: '#f1f5f9' }}>
                        {res.driver.full_name} {res.driver.code && `(${res.driver.code})`}
                      </td>
                      <td style={{ padding: '12px 16px', color: '#cbd5e1' }}>
                        {res.constructor.name}
                      </td>
                      <td style={{ padding: '12px 16px', color: '#94a3b8' }}>
                        {res.grid_position}
                      </td>
                      <td style={{ padding: '12px 16px', color: '#94a3b8' }}>
                        {res.laps}
                      </td>
                      <td style={{ padding: '12px 16px', color: '#94a3b8' }}>
                        {res.time_string || res.status}
                      </td>
                      <td style={{ padding: '12px 16px', fontWeight: 700, color: res.points > 0 ? '#10b981' : '#64748b' }}>
                        {res.points}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </main>
  );
}
