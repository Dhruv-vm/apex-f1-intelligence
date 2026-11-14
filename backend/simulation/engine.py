"""APEX — Discrete-Lap Race Simulation Engine (Phase 7.1 / EXP-0006-R2).

Coordinates driver states, lap-time generation, tyre degradation, pit execution,
safety car deployments, traffic overtaking, and regulatory compliance lap by lap.
Fully supports decoupled Common Random Numbers via ExogenousScenario.
"""
from typing import Dict, List, Optional, Tuple
import numpy as np

from backend.simulation.lap_time import LapTimeModel
from backend.simulation.pit_stop import PitStopModel
from backend.simulation.reliability import ReliabilityModel
from backend.simulation.safety_car import SafetyCarModel
from backend.simulation.scenario import ExogenousScenario, ScenarioGenerator
from backend.simulation.state import (
    DriverState,
    DriverStatus,
    RaceEventRecord,
    RaceState,
    SafetyCarState,
    TrackCondition,
    TyreCompound,
)
from backend.simulation.strategy import BaseStrategyPolicy, FixedReferenceStrategy, OneStopStrategy
from backend.simulation.traffic import TrafficOvertakingModel
from backend.simulation.tyre import TyreDegradationModel
from backend.simulation.weather import WeatherModel


class RaceSimulationEngine:
    """Simulates a complete Formula 1 Grand Prix at discrete lap transitions."""

    def __init__(
        self,
        tyre_model: Optional[TyreDegradationModel] = None,
        lap_time_model: Optional[LapTimeModel] = None,
        pit_stop_model: Optional[PitStopModel] = None,
        safety_car_model: Optional[SafetyCarModel] = None,
        weather_model: Optional[WeatherModel] = None,
        reliability_model: Optional[ReliabilityModel] = None,
        traffic_model: Optional[TrafficOvertakingModel] = None,
    ):
        self.tyre_model = tyre_model or TyreDegradationModel()
        self.lap_time_model = lap_time_model or LapTimeModel(self.tyre_model)
        self.pit_stop_model = pit_stop_model or PitStopModel()
        self.safety_car_model = safety_car_model or SafetyCarModel()
        self.weather_model = weather_model or WeatherModel()
        self.reliability_model = reliability_model or ReliabilityModel()
        self.traffic_model = traffic_model or TrafficOvertakingModel()

    def run_race(
        self,
        race_state: RaceState,
        strategies: Dict[str, BaseStrategyPolicy],
        seed: Optional[int] = None,
        scenario: Optional[ExogenousScenario] = None,
        is_race_suspended: bool = False,
    ) -> RaceState:
        """
        Executes a deterministic or stochastic simulation of the full race distance.
        If an ExogenousScenario is provided, draws environmental randomness from it,
        guaranteeing strict Common Random Numbers (CRN) invariance across policies.
        """
        driver_ids = list(race_state.drivers.keys())
        if scenario is None:
            gen = ScenarioGenerator(master_seed=seed or 42)
            scenario = gen.generate_scenario(run_index=0, total_laps=race_state.total_laps, driver_ids=driver_ids)

        rng = np.random.default_rng(seed or scenario.master_seed)

        # Initialize starting order by grid position
        sorted_drivers = sorted(race_state.drivers.values(), key=lambda d: d.starting_grid)
        for i, d in enumerate(sorted_drivers):
            d.current_position = i + 1
            d.accumulated_race_time = (d.starting_grid - 1) * 0.15  # Nominal grid stagger
            d.current_lap = 0
            d.current_tyre_age = 0
            d.current_stint = 1
            if d.current_compound not in d.compounds_used:
                d.compounds_used.append(d.current_compound)

        # Stint-level noise per driver from scenario
        stint_noise_map = {
            d_id: scenario.get_stint_noise(d_id, stint_number=1) for d_id in driver_ids
        }

        laps_since_sc_restart = 999

        # Step through laps 1 to total_laps
        for current_lap in range(1, race_state.total_laps + 1):
            race_state.current_lap = current_lap
            laps_since_sc_restart += 1

            # 1. Weather update using scenario draw
            rain_roll, temp_drift = scenario.get_weather_draws(current_lap)
            if race_state.weather_state == "RAIN_HAZARD" and rain_roll < 0.15:
                new_cond = TrackCondition.WET
            else:
                new_cond = race_state.track_condition

            if new_cond != race_state.track_condition:
                race_state.events_log.append(
                    RaceEventRecord(
                        lap=current_lap,
                        event_type="WEATHER_CHANGE",
                        description=f"Track condition changed from {race_state.track_condition.value} to {new_cond.value}",
                    )
                )
            race_state.track_condition = new_cond
            race_state.air_temp_celsius = round(race_state.air_temp_celsius + temp_drift * 0.1, 2)
            race_state.track_temp_celsius = round(race_state.track_temp_celsius + temp_drift * 0.15, 2)

            # 2. Safety Car lifecycle update using scenario draws
            sc_restart_this_lap = False
            if race_state.safety_car_state != SafetyCarState.NONE:
                # Check for explicit VSC -> SC escalation while VSC is active (using orthogonal escalation stream)
                if (
                    race_state.safety_car_state == SafetyCarState.VSC
                    and getattr(self.safety_car_model, "enable_vsc_escalation", True)
                    and not race_state.vsc_escalation_checked
                ):
                    race_state.vsc_escalation_checked = True
                    esc_roll = scenario.get_vsc_escalation_draw(current_lap)
                    escalated, sc_dur, desc = self.safety_car_model.check_vsc_escalation(
                        current_state=race_state.safety_car_state,
                        escalation_roll_override=esc_roll,
                    )
                    if escalated:
                        race_state.safety_car_state = SafetyCarState.FULL_SC
                        race_state.sc_laps_remaining = sc_dur
                        race_state.events_log.append(
                            RaceEventRecord(
                                lap=current_lap,
                                event_type="SAFETY_CAR",
                                description=desc or f"Virtual Safety Car escalated to Full Safety Car (Duration: {sc_dur} laps)",
                            )
                        )

                race_state.sc_laps_remaining -= 1
                if race_state.sc_laps_remaining <= 0:
                    prev_sc = race_state.safety_car_state
                    race_state.safety_car_state = SafetyCarState.NONE
                    race_state.vsc_escalation_checked = False
                    laps_since_sc_restart = 0
                    if prev_sc == SafetyCarState.FULL_SC:
                        sc_restart_this_lap = True
                    race_state.events_log.append(
                        RaceEventRecord(
                            lap=current_lap,
                            event_type="SAFETY_CAR",
                            description=f"{prev_sc.value} ended; normal racing resumed.",
                        )
                    )
            else:
                # Stochastic incident hazard check from scenario (strictly evaluated only when race is under green flag)
                incident_roll, sc_dur, vsc_dur = scenario.get_incident_draw(current_lap)
                lap_mult = 2.5 if current_lap == 1 else (1.5 if current_lap == 2 else 1.0)
                weather_mult = 2.5 if race_state.track_condition == TrackCondition.WET else (
                    1.5 if race_state.track_condition == TrackCondition.DAMP else 1.0
                )
                p_sc = self.safety_car_model.base_sc_hazard * lap_mult * weather_mult
                p_vsc = self.safety_car_model.base_vsc_hazard * lap_mult * weather_mult

                if incident_roll < p_sc:
                    race_state.safety_car_state = SafetyCarState.FULL_SC
                    race_state.sc_laps_remaining = sc_dur
                    race_state.vsc_escalation_checked = False
                    race_state.events_log.append(
                        RaceEventRecord(
                            lap=current_lap,
                            event_type="SAFETY_CAR",
                            description=f"Full Safety Car deployed (Duration: {sc_dur} laps)",
                        )
                    )
                elif incident_roll < p_sc + p_vsc:
                    race_state.safety_car_state = SafetyCarState.VSC
                    race_state.sc_laps_remaining = vsc_dur
                    race_state.vsc_escalation_checked = False
                    race_state.events_log.append(
                        RaceEventRecord(
                            lap=current_lap,
                            event_type="SAFETY_CAR",
                            description=f"Virtual Safety Car deployed (Duration: {vsc_dur} laps)",
                        )
                    )

            # 3. Strategy & Pit Stop Evaluation
            constructor_pit_stops: Dict[str, List[str]] = {}
            for d_id, drv in race_state.drivers.items():
                if not drv.is_active():
                    continue
                pol = strategies.get(d_id, OneStopStrategy())
                decision = pol.evaluate_strategy(drv, race_state)
                if decision.should_pit and decision.target_compound:
                    constructor_pit_stops.setdefault(drv.constructor_id, []).append(d_id)

            # 4. Lap Time Simulation & Execution
            raw_lap_times: Dict[str, float] = {}
            pitted_drivers: Dict[str, float] = {}

            for d_id, drv in race_state.drivers.items():
                if not drv.is_active():
                    continue

                drv.current_lap = current_lap
                drv.current_tyre_age += 1

                # Check if pitting this lap
                if d_id in constructor_pit_stops.get(drv.constructor_id, []):
                    team_list = constructor_pit_stops[drv.constructor_id]
                    is_double_stacked = bool(len(team_list) > 1 and team_list[1] == d_id)

                    pol = strategies.get(d_id, OneStopStrategy())
                    decision = pol.evaluate_strategy(drv, race_state)
                    target_comp = decision.target_compound or TyreCompound.HARD

                    service_override = scenario.get_pit_service_time(d_id, stop_index=drv.pit_stop_count)
                    pit_rec = self.pit_stop_model.execute_pit_stop(
                        lap=current_lap,
                        stint_completed=drv.current_stint,
                        target_compound=target_comp,
                        safety_car_state=race_state.safety_car_state,
                        is_double_stacked=is_double_stacked,
                        rng=rng,
                        service_override=service_override,
                    )
                    drv.pit_stop_history.append(pit_rec)
                    drv.pit_stop_count += 1
                    drv.current_compound = target_comp
                    if target_comp not in drv.compounds_used:
                        drv.compounds_used.append(target_comp)
                    drv.current_tyre_age = 0
                    drv.current_stint += 1
                    stint_noise_map[d_id] = scenario.get_stint_noise(d_id, stint_number=drv.current_stint)

                    pitted_drivers[d_id] = pit_rec.total_pit_loss_seconds
                    race_state.events_log.append(
                        RaceEventRecord(
                            lap=current_lap,
                            event_type="PIT_STOP",
                            driver_id=d_id,
                            description=(
                                f"{drv.driver_name} pit on lap {current_lap} for {target_comp.value} "
                                f"({pit_rec.stationary_duration_seconds:.2f}s service, total loss: {pit_rec.total_pit_loss_seconds:.2f}s)"
                            ),
                        )
                    )

                # Compute baseline lap time using deterministic pace noise from scenario
                pace_noise = scenario.get_driver_pace_noise(d_id, current_lap, drv.driver_pace_sigma)
                raw_lap = self.lap_time_model.compute_single_lap_time(
                    driver=drv,
                    race_state=race_state,
                    stint_noise=stint_noise_map[d_id],
                    rng=rng,
                )

                # Standing start physical launch delay on Lap 1 (from 0 km/h standstill to racing speed)
                standing_start_loss = 4.8 if current_lap == 1 else 0.0

                if d_id in pitted_drivers:
                    raw_lap += pitted_drivers[d_id]

                raw_lap += standing_start_loss
                raw_lap_times[d_id] = raw_lap

                # 5. Reliability / Retirement Check using scenario
                c_mult = self.reliability_model.constructor_multipliers.get(drv.constructor_id.lower(), 1.0)
                mech_hazard = self.reliability_model.base_mech_hazard * c_mult
                retired = scenario.check_mechanical_failure(d_id, current_lap, mech_hazard)
                if current_lap == 1 and not retired:
                    retired = scenario.check_lap1_collision(d_id, self.reliability_model.lap1_collision_hazard)

                if retired:
                    reason = "Power Unit / Mechanical Failure" if current_lap > 1 else "Lap 1 Collision Damage"
                    drv.status = DriverStatus.RETIRED
                    drv.retirement_lap = current_lap
                    drv.retirement_reason = reason
                    race_state.events_log.append(
                        RaceEventRecord(
                            lap=current_lap,
                            event_type="RETIREMENT",
                            driver_id=d_id,
                            description=f"{drv.driver_name} retired on lap {current_lap}: {reason}",
                        )
                    )

            # 6. Traffic, DRS & Overtaking (FIA Art 22.1)
            active_list = [d for d in race_state.drivers.values() if d.is_active()]
            active_list.sort(key=lambda d: d.accumulated_race_time)

            effective_laps: Dict[str, float] = {}
            for i, drv in enumerate(active_list):
                my_raw = raw_lap_times[drv.driver_id]
                if i == 0:
                    effective_laps[drv.driver_id] = my_raw
                else:
                    ahead_drv = active_list[i - 1]
                    overtake_roll = scenario.get_overtake_roll(drv.driver_id, current_lap)
                    eff_lap, passed = self.traffic_model.evaluate_pairwise_interaction(
                        chaser=drv,
                        leader=ahead_drv,
                        overtaking_difficulty_index=race_state.circuit.overtaking_difficulty_index,
                        chaser_raw_lap=my_raw,
                        leader_raw_lap=raw_lap_times[ahead_drv.driver_id],
                        safety_car_state=race_state.safety_car_state,
                        current_lap=current_lap,
                        laps_since_sc_restart=laps_since_sc_restart,
                        track_condition=race_state.track_condition,
                        drs_zone_fraction=race_state.circuit.drs_zone_lap_fraction,
                        rng=rng,
                        overtake_roll_override=overtake_roll,
                    )
                    effective_laps[drv.driver_id] = eff_lap
                    if passed:
                        race_state.events_log.append(
                            RaceEventRecord(
                                lap=current_lap,
                                event_type="OVERTAKE",
                                driver_id=drv.driver_id,
                                description=f"{drv.driver_name} overtook {ahead_drv.driver_name} on lap {current_lap}",
                            )
                        )

            # 7. Advance Accumulated Race Time
            for drv in active_list:
                lap_t = effective_laps[drv.driver_id]
                drv.last_lap_time = round(lap_t, 3)
                if drv.fastest_lap_time is None or lap_t < drv.fastest_lap_time:
                    drv.fastest_lap_time = round(lap_t, 3)
                drv.accumulated_race_time += lap_t

            # 8. Re-sort running drivers by accumulated race time
            active_list.sort(key=lambda d: d.accumulated_race_time)
            leader_time = active_list[0].accumulated_race_time if active_list else 0.0

            for pos_idx, drv in enumerate(active_list):
                drv.current_position = pos_idx + 1
                drv.gap_to_leader = round(drv.accumulated_race_time - leader_time, 3)
                if pos_idx == 0:
                    drv.gap_to_ahead = 0.0
                    drv.laps_led += 1
                else:
                    drv.gap_to_ahead = round(drv.accumulated_race_time - active_list[pos_idx - 1].accumulated_race_time, 3)

            # 9. Apply field compression if Full SC restarted this lap
            if sc_restart_this_lap:
                self.safety_car_model.apply_restart_field_compression(active_list, rng=rng)

        # Race conclusion: assign final finishing statuses & validate FIA Sporting Regulations Art 30.5
        for d in race_state.drivers.values():
            if d.is_active():
                compliance = self.pit_stop_model.validate_sporting_tyre_rules(
                    compounds_used=d.compounds_used,
                    track_condition=race_state.track_condition,
                    is_race_suspended_and_not_restarted=is_race_suspended,
                    season=race_state.season,
                )
                if compliance.is_compliant:
                    d.status = DriverStatus.FINISHED
                else:
                    if compliance.penalty_type == "TIME_PENALTY_30S":
                        d.status = DriverStatus.FINISHED
                        d.accumulated_race_time += 30.0
                        race_state.events_log.append(
                            RaceEventRecord(
                                lap=race_state.total_laps,
                                event_type="PENALTY",
                                driver_id=d.driver_id,
                                description=f"30s Post-race penalty to {d.driver_name}: {compliance.description}",
                            )
                        )
                    else:
                        d.status = DriverStatus.DISQUALIFIED
                        d.retirement_reason = compliance.description
                        race_state.events_log.append(
                            RaceEventRecord(
                                lap=race_state.total_laps,
                                event_type="DISQUALIFICATION",
                                driver_id=d.driver_id,
                                description=f"{d.driver_name} Disqualified: {compliance.description}",
                            )
                        )

        # Final classification sort: Finished drivers by race time, then retired by laps completed, then DSQ
        finished_list = [d for d in race_state.drivers.values() if d.status == DriverStatus.FINISHED]
        finished_list.sort(key=lambda d: d.accumulated_race_time)

        retired_list = [d for d in race_state.drivers.values() if d.status == DriverStatus.RETIRED]
        retired_list.sort(key=lambda d: (-(d.retirement_lap or 0), d.accumulated_race_time))

        dsq_list = [d for d in race_state.drivers.values() if d.status == DriverStatus.DISQUALIFIED]
        dsq_list.sort(key=lambda d: d.driver_id)

        # 1. Classified Finishers receive official finishing positions (1 .. N_finished)
        for pos_idx, d in enumerate(finished_list, start=1):
            d.current_position = pos_idx
            d.classified_position = pos_idx
            d.classification_display = f"P{pos_idx}"
            d.is_classified = True

        # 2. Retired entrants (DNF): Do not receive ordinary classified rank; ordered by laps completed
        dnf_rank = len(finished_list) + 1
        for d in retired_list:
            d.current_position = dnf_rank
            d.classified_position = None
            d.classification_display = f"DNF (Lap {d.retirement_lap or 0})"
            d.is_classified = False
            dnf_rank += 1

        # 3. Disqualified entrants (DSQ): Strictly unranked; NOT assigned ordinary finishing position
        for d in dsq_list:
            d.current_position = None
            d.classified_position = None
            d.classification_display = "DSQ"
            d.is_classified = False

        return race_state
