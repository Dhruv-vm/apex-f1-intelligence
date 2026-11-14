/**
 * APEX Replay & Circuit Geometry Types
 */

export interface Point2D {
  x: number;
  y: number;
}

export interface CircuitBounds {
  min_x: number;
  max_x: number;
  min_y: number;
  max_y: number;
  width: number;
  height: number;
}

export interface SectorSplit {
  sector: number;
  point: Point2D;
  distance_pct: number;
}

export interface CornerMarker {
  number: number;
  name?: string | null;
  point: Point2D;
  turn_type?: string | null;
}

export interface CircuitGeometry {
  circuit_ref: string;
  name: string;
  alt_names?: string[];
  country: string;
  length_meters: number;
  corners_count?: number;
  bounds: CircuitBounds;
  centerline: Point2D[];
  normalized_centerline: Point2D[];
  sectors: SectorSplit[];
  start_finish: Point2D;
  corners?: CornerMarker[];
  rotation_deg: number;
  provenance?: string;
  geometry_version?: string;
  validation_status?: string;
}

export interface ReplayDriver {
  driver_number: number;
  code: string;
  name: string;
  team: string;
  color: string;
}

export interface ReplayManifest {
  session_id: number;
  session_name: string;
  circuit_ref: string;
  circuit_name: string;
  t_start: string;
  t_end: string;
  start_epoch_ms: number;
  end_epoch_ms: number;
  duration_seconds: number;
  sample_rate_hz: number;
  driver_count: number;
  drivers: ReplayDriver[];
  coverage_type?: string;
  coverage_ratio_pct?: number;
}

export interface CarState {
  driver_number: number;
  x: number;
  y: number;
  norm_x: number;
  norm_y: number;
  speed: number | null;
  throttle: number | null;
  brake: number | null;
  gear: number | null;
  rpm: number | null;
  drs: number | null;
}

export interface ReplayFrame {
  timestamp_ms: number;
  timestamp_iso: string;
  cars: Record<string, CarState>;
}

export interface ReplayFramesResponse {
  session_id: number;
  start_ms: number;
  end_ms: number;
  frame_count: number;
  frames: ReplayFrame[];
}

export interface TelemetryPoint {
  timestamp_ms: number;
  timestamp_iso: string;
  driver_number: number;
  speed: number;
  throttle: number;
  brake: number;
  gear: number;
  rpm: number;
  drs: number;
}

export interface TelemetryResponse {
  session_id: number;
  driver_number: number;
  point_count: number;
  data: TelemetryPoint[];
}
