/**
 * APEX F1 Intelligence — Backend API Types
 */

export interface Circuit {
  id: number;
  circuit_ref: string;
  name: string;
  location: string | null;
  country: string | null;
  latitude: number | null;
  longitude: number | null;
  altitude: number | null;
  url: string | null;
}

export interface Session {
  id: number;
  event_id: number;
  session_type: string;
  session_name: string;
  date_start: string | null;
  date_end: string | null;
  source_provider: string;
  source_session_key: number | null;
}

export interface Driver {
  id: number;
  driver_ref: string;
  code: string | null;
  permanent_number: number | null;
  first_name: string;
  last_name: string;
  full_name: string;
  nationality: string | null;
}

export interface Constructor {
  id: number;
  constructor_ref: string;
  name: string;
  nationality: string | null;
}

export interface RaceResult {
  id: number;
  event_id: number;
  driver: Driver;
  constructor: Constructor;
  number: number | null;
  grid_position: number;
  position: number | null;
  position_text: string;
  position_order: number;
  points: number;
  laps: number;
  status: string;
  time_millis: number | null;
  time_string: string | null;
  fastest_lap_rank: number | null;
  fastest_lap_time: string | null;
}

export interface Event {
  id: number;
  season_year: number;
  round: number;
  event_name: string;
  official_name: string | null;
  date: string;
  time: string | null;
  url: string | null;
  circuit: Circuit;
}

export interface EventDetail extends Event {
  sessions: Session[];
  results_count: number;
}

export interface HealthResponse {
  status: string;
  environment: string;
  version: string;
  database: string;
}
