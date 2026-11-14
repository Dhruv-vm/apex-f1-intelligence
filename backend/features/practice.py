"""Practice session intelligence and sequential checkpoint snapshots.

Extracts single-lap pace, sector times, long-run tyre degradation slopes,
and constructs immutable sequential snapshots (T1: Post-FP1, T2: Post-FP2, T3: Post-FP3)
strictly enforcing point-in-time information cutoffs with zero forward lookahead.
"""
import logging
import math
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

logger = logging.getLogger("apex.features.practice")


class TemporalLeakageError(Exception):
    """Raised when an observation past the checkpoint information cutoff is encountered."""
    pass


class SingleLapMetrics(BaseModel):
    """Driver single-lap pace and sector performance metrics."""
    driver_number: int
    is_session_participant: bool = True
    session_driver_name: Optional[str] = None
    session_driver_number: Optional[int] = None
    is_replacement_driver: bool = False
    replacement_reason: Optional[str] = None
    best_lap_time: Optional[float] = None  # In seconds
    median_lap_time: Optional[float] = None
    trimmed_mean_lap_time: Optional[float] = None  # 10% trimmed mean of valid flying laps
    lap_count_total: int = 0
    lap_count_clean: int = 0
    invalid_laps_count: int = 0
    out_in_laps_count: int = 0
    sector_1_best: Optional[float] = None
    sector_2_best: Optional[float] = None
    sector_3_best: Optional[float] = None
    theoretical_best_lap: Optional[float] = None  # S1_best + S2_best + S3_best
    speed_trap_max: Optional[float] = None
    pace_variance: Optional[float] = None
    delta_to_benchmark: Optional[float] = None


class LongRunStintMetrics(BaseModel):
    """Stint-level tyre degradation and race-simulation pace."""
    stint_number: int
    compound: str
    stint_length_laps: int
    tyre_age_start: int
    mean_pace: float
    median_pace: float
    degradation_slope_sec_per_lap: float  # Linear regression slope (sec/lap)
    is_race_simulation: bool
    fuel_confounding_note: str = (
        "Raw observed pace. Fuel load is unmeasured in open timing telemetry; linear degradation "
        "slopes are confounded by fuel mass burn-off and run-plan variations. No assumed fuel correction is applied."
    )


class DriverPracticeSummary(BaseModel):
    """Combined driver practice intelligence for a session or snapshot."""
    driver_number: int
    single_lap: SingleLapMetrics
    stints: List[LongRunStintMetrics] = Field(default_factory=list)
    primary_race_sim_stint: Optional[LongRunStintMetrics] = None


class SequentialPracticeSnapshot(BaseModel):
    """
    Immutable point-in-time practice snapshot at a specific weekend checkpoint.
    Prepares HYP-0001 (Sequential Information Superiority).
    """
    season: int
    event_id: int
    event_name: str
    checkpoint: str  # T1_POST_FP1, T2_POST_FP2, T3_POST_FP3
    cutoff_timestamp: str  # ISO 8601 UTC
    included_sessions: List[str]
    driver_features: Dict[str, DriverPracticeSummary]  # driver_number string -> summary
    session_benchmark_lap: Optional[float] = None
    extraction_version: str = "v1.0"
    provenance: str = "Derived from validated OpenF1 telemetry laps & stints"


def compute_linear_slope(x_vals: List[float], y_vals: List[float]) -> float:
    """Compute ordinary least squares linear regression slope."""
    n = len(x_vals)
    if n < 2:
        return 0.0
    mean_x = sum(x_vals) / n
    mean_y = sum(y_vals) / n
    denom = sum((x - mean_x) ** 2 for x in x_vals)
    if denom == 0:
        return 0.0
    numer = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_vals, y_vals))
    return round(numer / denom, 4)


def extract_session_practice_features(
    session_laps: List[dict],
    session_stints: List[dict],
    max_flying_lap_duration: float = 120.0,
    min_flying_lap_duration: float = 60.0,
    driver_substitutions: Optional[Dict[int, Dict[str, Any]]] = None,
) -> Dict[int, DriverPracticeSummary]:
    """
    Extract reproducible single-lap pace and stint degradation features for all drivers in a session.
    
    Supports explicit driver substitution handling:
    driver_substitutions: mapping of regular driver_number -> {
        "participated": bool,
        "replacement_number": Optional[int],
        "replacement_name": Optional[str],
        "reason": Optional[str]
    }
    """
    drivers = sorted(list(set(l["driver_number"] for l in session_laps if "driver_number" in l)))
    summaries: Dict[int, DriverPracticeSummary] = {}

    for drv in drivers:
        drv_laps = [l for l in session_laps if l.get("driver_number") == drv]
        drv_stints = [s for s in session_stints if s.get("driver_number") == drv]
        drv_stints.sort(key=lambda x: x.get("stint_number", 0))

        clean_times: List[float] = []
        out_in_count = 0
        invalid_count = 0
        s1_times: List[float] = []
        s2_times: List[float] = []
        s3_times: List[float] = []
        st_speeds: List[float] = []

        for lap in drv_laps:
            dur = lap.get("lap_duration")
            is_out = lap.get("is_pit_out_lap", False)

            if is_out or dur is None:
                out_in_count += 1
                continue

            if dur < min_flying_lap_duration or dur > max_flying_lap_duration:
                invalid_count += 1
                continue

            clean_times.append(dur)

            # Sectors
            s1 = lap.get("duration_sector_1")
            s2 = lap.get("duration_sector_2")
            s3 = lap.get("duration_sector_3")
            st = lap.get("st_speed")

            if s1 and s1 > 0:
                s1_times.append(s1)
            if s2 and s2 > 0:
                s2_times.append(s2)
            if s3 and s3 > 0:
                s3_times.append(s3)
            if st and st > 0:
                st_speeds.append(st)

        # Single-lap aggregation
        best_lap = min(clean_times) if clean_times else None
        median_lap = None
        trimmed_mean = None
        variance = None

        if clean_times:
            sorted_times = sorted(clean_times)
            mid = len(sorted_times) // 2
            median_lap = (
                (sorted_times[mid - 1] + sorted_times[mid]) / 2.0
                if len(sorted_times) % 2 == 0
                else sorted_times[mid]
            )

            # 10% Trimmed Mean
            k = max(1, int(len(sorted_times) * 0.10)) if len(sorted_times) >= 10 else 0
            trimmed_slice = sorted_times[k : len(sorted_times) - k] if k > 0 else sorted_times
            trimmed_mean = round(sum(trimmed_slice) / len(trimmed_slice), 3)

            # Pace Variance
            mean_val = sum(clean_times) / len(clean_times)
            variance = round(sum((t - mean_val) ** 2 for t in clean_times) / len(clean_times), 4)

        s1_best = min(s1_times) if s1_times else None
        s2_best = min(s2_times) if s2_times else None
        s3_best = min(s3_times) if s3_times else None
        theo_best = (
            round(s1_best + s2_best + s3_best, 3)
            if s1_best and s2_best and s3_best
            else None
        )
        st_max = max(st_speeds) if st_speeds else None

        single_lap = SingleLapMetrics(
            driver_number=drv,
            best_lap_time=best_lap,
            median_lap_time=round(median_lap, 3) if median_lap else None,
            trimmed_mean_lap_time=trimmed_mean,
            lap_count_total=len(drv_laps),
            lap_count_clean=len(clean_times),
            invalid_laps_count=invalid_count,
            out_in_laps_count=out_in_count,
            sector_1_best=round(s1_best, 3) if s1_best else None,
            sector_2_best=round(s2_best, 3) if s2_best else None,
            sector_3_best=round(s3_best, 3) if s3_best else None,
            theoretical_best_lap=theo_best,
            speed_trap_max=st_max,
            pace_variance=variance,
            delta_to_benchmark=None,  # Populated after full-session benchmark is known
        )

        # Stint-level analysis
        stint_metrics_list: List[LongRunStintMetrics] = []
        for stint in drv_stints:
            s_num = stint.get("stint_number", 0)
            comp = stint.get("compound", "UNKNOWN")
            l_start = stint.get("lap_start", 0)
            l_end = stint.get("lap_end", 0)
            age_start = stint.get("tyre_age_at_start", 0)

            # Find clean laps strictly within this stint
            stint_laps = [
                l for l in drv_laps
                if l_start <= l.get("lap_number", -1) <= l_end
                and not l.get("is_pit_out_lap", False)
                and l.get("lap_duration") is not None
                and min_flying_lap_duration <= l.get("lap_duration") <= max_flying_lap_duration
            ]

            if not stint_laps:
                continue

            times = [l["lap_duration"] for l in stint_laps]
            lap_indices = [float(l["lap_number"]) for l in stint_laps]
            stint_len = len(times)

            mean_p = round(sum(times) / stint_len, 3)
            sorted_p = sorted(times)
            med_p = round(sorted_p[stint_len // 2], 3)
            slope = compute_linear_slope(lap_indices, times)

            # A stint qualifies as a candidate race simulation if >= 7 clean flying laps
            is_race_sim = stint_len >= 7

            stint_metrics_list.append(
                LongRunStintMetrics(
                    stint_number=s_num,
                    compound=comp,
                    stint_length_laps=stint_len,
                    tyre_age_start=age_start,
                    mean_pace=mean_p,
                    median_pace=med_p,
                    degradation_slope_sec_per_lap=slope,
                    is_race_simulation=is_race_sim,
                )
            )

        # Identify primary race simulation stint (longest stint with is_race_simulation=True)
        race_sims = [s for s in stint_metrics_list if s.is_race_simulation]
        primary_sim = max(race_sims, key=lambda s: s.stint_length_laps) if race_sims else None

        summaries[drv] = DriverPracticeSummary(
            driver_number=drv,
            single_lap=single_lap,
            stints=stint_metrics_list,
            primary_race_sim_stint=primary_sim,
        )

    # Benchmark lap calculation
    all_bests = [
        s.single_lap.best_lap_time
        for s in summaries.values()
        if s.single_lap.best_lap_time is not None
    ]
    if all_bests:
        benchmark = min(all_bests)
        for s in summaries.values():
            if s.single_lap.best_lap_time is not None:
                s.single_lap.delta_to_benchmark = round(
                    s.single_lap.best_lap_time - benchmark, 3
                )

    # Handle explicit substitutions or absent regular entrants
    if driver_substitutions:
        for reg_drv, sub_info in driver_substitutions.items():
            if not sub_info.get("participated", True) and reg_drv not in summaries:
                rep_num = sub_info.get("replacement_number")
                rep_name = sub_info.get("replacement_name")
                reason = sub_info.get("reason", "Driver substitution / did not participate")
                summaries[reg_drv] = DriverPracticeSummary(
                    driver_number=reg_drv,
                    single_lap=SingleLapMetrics(
                        driver_number=reg_drv,
                        is_session_participant=False,
                        session_driver_name=rep_name,
                        session_driver_number=rep_num,
                        is_replacement_driver=True,
                        replacement_reason=reason,
                        best_lap_time=None,
                        median_lap_time=None,
                        trimmed_mean_lap_time=None,
                        lap_count_total=0,
                        lap_count_clean=0,
                        invalid_laps_count=0,
                        out_in_laps_count=0,
                        delta_to_benchmark=None,
                    ),
                    stints=[],
                    primary_race_sim_stint=None,
                )

    return summaries


def build_practice_snapshot(
    season: int,
    event_id: int,
    event_name: str,
    checkpoint: str,
    cutoff_iso: str,
    sessions_data: Dict[str, Tuple[List[dict], List[dict], str]],  # session_label -> (laps, stints, session_end_iso)
) -> SequentialPracticeSnapshot:
    """
    Construct an immutable sequential practice snapshot strictly enforcing point-in-time cutoffs.
    
    Args:
        season: Championship year
        event_id: Canonical event ID
        event_name: Canonical event name
        checkpoint: One of T1_POST_FP1, T2_POST_FP2, T3_POST_FP3
        cutoff_iso: ISO 8601 cutoff timestamp. Any observation after this raises TemporalLeakageError.
        sessions_data: Dict of session_key -> (laps, stints, session_end_iso)
    """
    allowed_sessions: List[str] = []
    if checkpoint == "T1_POST_FP1":
        allowed_sessions = ["FP1"]
    elif checkpoint == "T2_POST_FP2":
        allowed_sessions = ["FP1", "FP2"]
    elif checkpoint == "T3_POST_FP3":
        allowed_sessions = ["FP1", "FP2", "FP3"]
    else:
        raise ValueError(f"Unsupported practice checkpoint '{checkpoint}'")

    cumulative_driver_summaries: Dict[str, DriverPracticeSummary] = {}
    included: List[str] = []

    # Process allowed sessions in chronological sequence
    for sess_label in allowed_sessions:
        if sess_label not in sessions_data:
            logger.warning("Session %s data not supplied for checkpoint %s", sess_label, checkpoint)
            continue

        laps, stints, session_end_iso = sessions_data[sess_label]

        # Strict Temporal Anti-Leakage Check
        if session_end_iso > cutoff_iso:
            raise TemporalLeakageError(
                f"Temporal leakage detected: {sess_label} end timestamp {session_end_iso} > "
                f"checkpoint cutoff {cutoff_iso}"
            )

        sess_features = extract_session_practice_features(laps, stints)
        included.append(sess_label)

        # Update cumulative best features per driver
        for drv, summary in sess_features.items():
            drv_key = str(drv)
            if drv_key not in cumulative_driver_summaries:
                cumulative_driver_summaries[drv_key] = summary
            else:
                existing = cumulative_driver_summaries[drv_key]
                # Compare and take better lap time
                if summary.single_lap.best_lap_time is not None:
                    if (
                        existing.single_lap.best_lap_time is None
                        or summary.single_lap.best_lap_time < existing.single_lap.best_lap_time
                    ):
                        existing.single_lap.best_lap_time = summary.single_lap.best_lap_time

                # Merge theoretical best
                if summary.single_lap.sector_1_best:
                    existing.single_lap.sector_1_best = min(
                        filter(None, [existing.single_lap.sector_1_best, summary.single_lap.sector_1_best])
                    )
                if summary.single_lap.sector_2_best:
                    existing.single_lap.sector_2_best = min(
                        filter(None, [existing.single_lap.sector_2_best, summary.single_lap.sector_2_best])
                    )
                if summary.single_lap.sector_3_best:
                    existing.single_lap.sector_3_best = min(
                        filter(None, [existing.single_lap.sector_3_best, summary.single_lap.sector_3_best])
                    )
                if (
                    existing.single_lap.sector_1_best
                    and existing.single_lap.sector_2_best
                    and existing.single_lap.sector_3_best
                ):
                    existing.single_lap.theoretical_best_lap = round(
                        existing.single_lap.sector_1_best
                        + existing.single_lap.sector_2_best
                        + existing.single_lap.sector_3_best,
                        3,
                    )

                # Merge stints
                existing.stints.extend(summary.stints)
                if summary.primary_race_sim_stint:
                    existing.primary_race_sim_stint = summary.primary_race_sim_stint

    # Overall benchmark
    bests = [
        s.single_lap.best_lap_time
        for s in cumulative_driver_summaries.values()
        if s.single_lap.best_lap_time is not None
    ]
    benchmark = min(bests) if bests else None
    if benchmark:
        for s in cumulative_driver_summaries.values():
            if s.single_lap.best_lap_time is not None:
                s.single_lap.delta_to_benchmark = round(
                    s.single_lap.best_lap_time - benchmark, 3
                )

    return SequentialPracticeSnapshot(
        season=season,
        event_id=event_id,
        event_name=event_name,
        checkpoint=checkpoint,
        cutoff_timestamp=cutoff_iso,
        included_sessions=included,
        driver_features=cumulative_driver_summaries,
        session_benchmark_lap=benchmark,
        extraction_version="v1.0",
        provenance="OpenF1 verified practice telemetry",
    )
