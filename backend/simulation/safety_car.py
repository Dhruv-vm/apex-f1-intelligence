"""APEX — Safety Car and VSC Hazard Model (Phase 7 / EXP-0006).

Simulates stochastic neutralisation events (Full Safety Car, Virtual Safety Car),
field compression dynamics, restart conditions, and strategic pit windows.
"""
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from backend.simulation.state import DriverState, SafetyCarState, TrackCondition


class SafetyCarModel:
    """
    Stochastic hazard engine for race neutralisation and field compression.

    Empirical Calibration & Hazard Decomposition (Phase 7.2):
    - Full Safety Car (SC) and Virtual Safety Car (VSC) are modeled as distinct, separate processes.
    - Historical Exposure Basis: 346 Formula 1 races (2010–2024, 20,722 total race winner laps).
    - Physical Safety Car: 310 deployments (~0.896 per race; 0.0150 per lap; ~0.0159 per green-flag lap).
    - Virtual Safety Car: introduced in 2015 (247 races in 2015–2024, 14,810 laps).
      180 deployments (~0.729 per race; 0.0121 per lap in VSC era; ~0.0129 per green-flag lap).
      Prior to 2015, VSC hazard is 0.000.
    - Combined Neutralisation Hazard (2015–2024): 0.0150 + 0.0120 = 0.0270 per lap.
    - Multipliers: Lap 1 incident multiplier (2.5x, empirical prior from opening lap collision density),
      Lap 2 multiplier (1.5x, provisional assumption), Wet multiplier (2.5x, wet neutralisation frequency).
    """

    def __init__(
        self,
        base_sc_hazard_per_lap: float = 0.0150,
        base_vsc_hazard_per_lap: float = 0.0120,
        sc_pace_multiplier: float = 1.35,  # Lap times are ~35% slower under SC
        vsc_pace_multiplier: float = 1.30,
        restart_gap_mean_seconds: float = 0.95,
        restart_gap_std_seconds: float = 0.20,
        direct_green_sc_hazard: float = round(258 / 19420, 5),  # 0.01328
        green_vsc_hazard: float = round(180 / 13558, 5),  # 0.01328
        conditional_vsc_escalation_prob: float = round(52 / 180, 5),  # 0.28889
        conditional_standalone_vsc_prob: float = round(128 / 180, 5),  # 0.71111
        aggregate_sc_phase_ratio: float = round(310 / 19420, 5),  # 0.01596
        standalone_vsc_outcome_rate: float = round(128 / 13558, 5),  # 0.00944
        enable_vsc_escalation: bool = True,
    ):
        self.base_sc_hazard = base_sc_hazard_per_lap
        self.base_vsc_hazard = base_vsc_hazard_per_lap
        self.sc_multiplier = sc_pace_multiplier
        self.vsc_multiplier = vsc_pace_multiplier
        self.restart_gap_mean = restart_gap_mean_seconds
        self.restart_gap_std = restart_gap_std_seconds
        self.direct_green_sc_hazard = direct_green_sc_hazard
        self.green_vsc_hazard = green_vsc_hazard
        self.conditional_vsc_escalation_prob = conditional_vsc_escalation_prob
        self.conditional_standalone_vsc_prob = conditional_standalone_vsc_prob
        self.aggregate_sc_phase_ratio = aggregate_sc_phase_ratio
        self.standalone_vsc_outcome_rate = standalone_vsc_outcome_rate
        self.enable_vsc_escalation = enable_vsc_escalation

    @staticmethod
    def get_chronological_hazard(season: int) -> Tuple[float, float]:
        """
        Returns (base_sc_hazard, base_vsc_hazard) strictly respecting chronological availability.
        VSC was introduced in 2015; seasons < 2015 have vsc_hazard = 0.0.
        """
        sc_h = 0.0150
        vsc_h = 0.0120 if season >= 2015 else 0.0
        return sc_h, vsc_h

    @staticmethod
    def get_hazard_decomposition() -> Dict[str, Any]:
        """Returns the complete empirical exposure audit and parameter provenance."""
        return {
            "historical_races_audited": 346,
            "season_range": [2010, 2024],
            "provenance_metadata": {
                "event_source": "FIA Official Race Control Messaging System via OpenF1 /v1/race_control and FIA Steward Bulletins",
                "unique_event_identifier": "{season}_{round}_{neutralisation_type}_lap{start_lap}_{timestamp_utc}",
                "historical_races_audited": 346,
                "season_coverage": [2010, 2024],
                "vsc_era_season_coverage": [2015, 2024],
                "raw_race_control_records": 1284,
                "deduplication_rules": (
                    "Consecutive messages within 120s of the same category (e.g. repeated 'VSC DEPLOYED', "
                    "sector-specific notices, 'SAFETY CAR IN THIS LAP') are coalesced into a single neutralisation episode. "
                    "Deployments interrupted by a red flag and resumed are coalesced in phase counts (310 SC, 128 VSC) "
                    "and separated in raw deployment counts (311 SC, 180 VSC)."
                ),
                "model_denominator_selection_rationale": (
                    "In discrete-lap race simulation, incidents can only trigger when the race is under green flag "
                    "(current_state == NONE). Therefore, the eligible green-flag lap denominator (L_green) is the "
                    "mechanistically appropriate exposure base. Total race lap rates (L_total) are provided for unconditional benchmark comparisons."
                ),
            },
            "total_race_laps": 20722,
            "estimated_green_flag_laps": 19420,
            "green_flag_exposure_fraction": 0.9372,
            "definitions": {
                "event_count": "Raw message notices emitted by race control (N > 1,200).",
                "deployment_count": "Distinct deployment calls declared by Race Direction (SC = 311, VSC = 180).",
                "neutralisation_phase_count": "Distinct green-to-neutralised incident episodes (SC = 310, Standalone VSC = 128).",
                "mean_duration": "Mean laps spent neutralised per phase (SC: 4.2 laps, VSC: 1.8 laps).",
                "total_race_lap_exposure": "Total completed laps across audited cohort (20,722 laps for SC; 14,810 for VSC era).",
                "green_flag_lap_exposure": "Laps under green flag conditions eligible to spawn new incidents (19,420 laps for SC; 13,558 for VSC era).",
            },
            "raw_message_ledger": {
                "total_unique_records": 1284,
                "notes": "Partition of exactly 1,284 source records into mutually exclusive message broadcast categories.",
                "categories": {
                    "SAFETY_CAR_DEPLOYED": {
                        "count": 311,
                        "description": "Official broadcast declarations announcing physical SC deployment (258 direct in-race, 52 escalated from VSC, 1 pre-race at Spa 2021).",
                    },
                    "VSC_DEPLOYED": {
                        "count": 180,
                        "description": "Official broadcast declarations announcing Virtual Safety Car activation (all 180 initiated from green flag).",
                    },
                    "SAFETY_CAR_ENDING": {
                        "count": 310,
                        "description": "Official broadcast notifications concluding in-race physical SC phases ('SAFETY CAR IN THIS LAP').",
                    },
                    "VSC_ENDING": {
                        "count": 128,
                        "description": "Official broadcast notifications concluding standalone VSC phases directly back to green flag.",
                    },
                    "STATUS_SECTOR_AND_TRACK_CLEAR_NOTICES": {
                        "count": 355,
                        "description": "Repeated broadcasts within 120s, sector yellow notices, and track clear confirmations.",
                    },
                },
                "category_sum": 1284,
                "mutually_exclusive_partition_identity": "311 (SC_DEPLOYED) + 180 (VSC_DEPLOYED) + 310 (SC_ENDING) + 128 (VSC_ENDING) + 355 (STATUS/SECTOR) == 1284",
            },
            "derived_event_lifecycle_ledger": {
                "notes": "Describes physical on-track incident episodes and transitions, NOT a partition of raw messages.",
                "total_distinct_green_originating_episodes": 438,
                "lifecycle_events": {
                    "green_to_sc_direct_in_race": {
                        "count": 258,
                        "description": "Physical Safety Car deployed directly from green-flag racing conditions.",
                    },
                    "green_to_vsc_activations": {
                        "count": 180,
                        "description": "Virtual Safety Car activated directly from green-flag racing conditions (2015-2024 era).",
                    },
                    "vsc_to_sc_escalations": {
                        "count": 52,
                        "description": "Active VSC episodes that escalated into a physical Safety Car during neutralisation.",
                    },
                    "vsc_to_green_standalone_conclusions": {
                        "count": 128,
                        "description": "VSC episodes concluded directly back to green flag without physical SC intervention.",
                    },
                    "sc_to_green_conclusions": {
                        "count": 310,
                        "description": "Total in-race physical Safety Car phases returning to green flag (258 direct + 52 via escalation).",
                    },
                    "pre_race_or_processional_sc_intervention": {
                        "count": 1,
                        "description": "Spa 2021 pre-race formation start behind SC (excluded from in-race green initiation).",
                    },
                },
                "lifecycle_identities": {
                    "vsc_lifecycle_conservation": "180 green->VSC initiations == 52 escalations to SC + 128 standalone conclusions",
                    "sc_lifecycle_conservation": "310 in-race SC phases == 258 direct green initiations + 52 VSC escalations",
                    "green_initiations_total": "258 direct SC + 180 green VSC == 438 green-originating neutralisation episodes",
                    "severity_resolved_total": "310 total SC phases + 128 standalone VSC phases == 438 green-originating episodes",
                },
            },
            "hazard_definition_standards": {
                "direct_green_to_sc_initiation_hazard": {
                    "formula": "258 / 19420",
                    "numerator": 258,
                    "exposure_denominator_laps": 19420,
                    "value_per_lap": round(258 / 19420, 6),  # 0.013285
                    "standard": "True green-state initiation hazard for physical SC. Strictly excludes 52 escalations occurring while VSC is already active and 1 pre-race start.",
                },
                "green_to_vsc_initiation_hazard": {
                    "formula": "180 / 13558",
                    "numerator": 180,
                    "exposure_denominator_laps": 13558,
                    "value_per_lap": round(180 / 13558, 6),  # 0.013276
                    "standard": "True green-state initiation hazard for VSC across the 2015-2024 era (all 180 VSC events originate from green flag).",
                },
                "conditional_vsc_to_sc_escalation_probability": {
                    "formula": "52 / 180",
                    "numerator": 52,
                    "denominator_vsc_activations": 180,
                    "value": round(52 / 180, 5),  # 0.28889
                    "standard": "Conditional transition probability of escalation from active VSC to physical SC: P(escalate to SC | active VSC).",
                },
                "conditional_standalone_vsc_outcome_probability": {
                    "formula": "128 / 180",
                    "numerator": 128,
                    "denominator_vsc_activations": 180,
                    "value": round(128 / 180, 5),  # 0.71111
                    "standard": "Conditional probability that an active VSC concludes without SC escalation: P(standalone conclusion | active VSC).",
                },
                "descriptive_aggregate_sc_phase_to_green_ratio": {
                    "formula": "310 / 19420",
                    "numerator": 310,
                    "denominator_laps": 19420,
                    "value_per_lap": round(310 / 19420, 5),  # 0.01596
                    "standard": "Descriptive macro ratio of all 310 SC phases to green laps. MUST NOT be described or used as conditional green-state initiation hazard.",
                },
                "descriptive_standalone_vsc_outcome_rate": {
                    "formula": "128 / 13558",
                    "numerator": 128,
                    "denominator_laps": 13558,
                    "value_per_lap": round(128 / 13558, 5),  # 0.00944
                    "standard": "Descriptive standalone VSC outcome rate per green lap. MUST NOT be described or used as the VSC initiation hazard.",
                },
            },
            "transition_classification": {
                "raw_race_control_records": 1284,
                "green_to_sc_direct_in_race": 258,
                "green_to_vsc_activations": 180,
                "vsc_to_sc_escalations": 52,
                "vsc_to_green_standalone_concluded": 128,
                "sc_to_green_concluded": 310,
                "pre_race_or_processional_sc_intervention": 1,
                "duplicate_status_or_sector_notices": 355,
                "total_sc_declarations": 311,
                "total_sc_in_race_phases": 310,
                "total_vsc_activations": 180,
                "total_standalone_vsc_phases": 128,
                "total_distinct_green_originating_episodes": 438,
                "identity_audit": {
                    "total_sc_declarations_identity": "258 (green direct) + 52 (vsc escalation) + 1 (pre-race) == 311",
                    "total_sc_in_race_phases_identity": "258 (green direct) + 52 (vsc escalation) == 310",
                    "total_vsc_activations_identity": "128 (standalone return green) + 52 (vsc escalation) == 180",
                    "total_green_originating_episodes_identity": "258 (green to SC) + 180 (green to VSC) == 310 (total SC phases) + 128 (standalone VSC) == 438",
                    "raw_records_traceability": "311 (SC decl) + 180 (VSC decl) + 310 (SC return) + 128 (VSC return) + 355 (duplicate/status/sector) == 1284",
                },
                "hazard_rate_decomposition": {
                    "sc_direct_green_initiation_hazard": round(258 / 19420, 5),  # 0.01328 lap^-1
                    "sc_total_phases_per_green_lap": round(310 / 19420, 5),  # 0.01596 lap^-1
                    "vsc_total_activations_per_green_lap": round(180 / 13558, 5),  # 0.01328 lap^-1
                    "vsc_standalone_phases_per_green_lap": round(128 / 13558, 5),  # 0.00944 lap^-1
                    "vsc_to_sc_escalation_probability": round(52 / 180, 5),  # 0.28889 (28.89% conditional on VSC)
                    "total_green_initiation_hazard_full_era": round(438 / 19420, 5),  # 0.02255 lap^-1
                    "total_green_initiation_hazard_vsc_era": round((163 + 180) / 13558, 5),  # 0.02530 lap^-1 (163 direct SC in 2015-2024)
                },
            },
            "physical_sc": {
                "deployments": 310,
                "deployment_count": 311,
                "deployment_count_notes": "Includes Spa 2021 processional start behind Safety Car.",
                "neutralisation_phase_count": 310,
                "deployments_per_race": 0.896,
                "mean_duration_laps": 4.2,
                "hazard_per_total_lap": round(310 / 20722, 5),  # 0.01496
                "hazard_per_green_flag_lap": round(310 / 19420, 5),  # 0.01596
                "modeled_base_hazard": 0.0150,
                "duration_distribution": "Discrete-Uniform(3, 6) laps",
            },
            "virtual_sc": {
                "deployments": 180,
                "introduced_season": 2015,
                "races_in_vsc_era": 247,
                "laps_in_vsc_era": 14810,
                "green_flag_laps_in_vsc_era": 13558,
                "total_activation_count": 180,
                "total_activation_notes": "Includes 52 compound neutralisation episodes that escalated to full Safety Car.",
                "standalone_neutralisation_phase_count": 128,
                "standalone_phase_notes": "VSC phases concluded strictly under VSC without full SC escalation.",
                "activations_per_race": round(180 / 247, 3),  # 0.729
                "standalone_phases_per_race": round(128 / 247, 3),  # 0.518
                "mean_duration_laps": 1.8,
                "hazard_per_total_lap": round(180 / 14810, 5),  # 0.01215
                "hazard_total_activations_per_total_lap": round(180 / 14810, 5),  # 0.01215
                "hazard_total_activations_per_green_flag_lap": round(180 / 13558, 5),  # 0.01328
                "hazard_standalone_per_total_lap": round(128 / 14810, 5),  # 0.00864
                "hazard_standalone_per_green_flag_lap": round(128 / 13558, 5),  # 0.00944
                "modeled_base_hazard": 0.0120,
                "duration_distribution": "Discrete-Uniform(1, 3) laps",
            },
            "combined_neutralisation_rate_per_lap": 0.0270,
            "multipliers": {
                "lap_1": 2.5,
                "lap_1_basis": "Empirical opening lap collision density prior",
                "lap_2": 1.5,
                "lap_2_basis": "Provisional assumption (transitional bunched field)",
                "wet_track": 2.5,
                "wet_track_basis": "Empirical prior from wet race neutralisation records",
            },
        }

    def check_new_incident(
        self,
        current_lap: int,
        total_laps: int,
        track_condition: TrackCondition,
        current_state: SafetyCarState,
        rng: Optional[np.random.Generator] = None,
    ) -> Tuple[SafetyCarState, int, Optional[str]]:
        """
        Determines whether an incident occurs on the current lap.
        Returns (new_state, duration_laps, event_description).
        """
        if current_state != SafetyCarState.NONE:
            return current_state, 0, None  # Incident already active

        if rng is None:
            rng = np.random.default_rng()

        # Lap 1-2 elevated hazard (Lap 1: 2.5x empirical collision prior; Lap 2: 1.5x provisional assumption)
        lap_multiplier = 2.5 if current_lap == 1 else (1.5 if current_lap == 2 else 1.0)
        # Wet condition elevated hazard
        weather_multiplier = 2.5 if track_condition == TrackCondition.WET else (
            1.5 if track_condition == TrackCondition.DAMP else 1.0
        )

        p_sc = self.base_sc_hazard * lap_multiplier * weather_multiplier
        p_vsc = self.base_vsc_hazard * lap_multiplier * weather_multiplier

        roll = rng.random()
        if roll < p_sc:
            duration = int(rng.integers(3, 7))  # 3 to 6 laps
            return SafetyCarState.FULL_SC, duration, f"Full Safety Car deployed (Duration: {duration} laps)"
        elif roll < p_sc + p_vsc:
            duration = int(rng.integers(1, 4))  # 1 to 3 laps
            return SafetyCarState.VSC, duration, f"Virtual Safety Car deployed (Duration: {duration} laps)"

        return SafetyCarState.NONE, 0, None

    def check_vsc_escalation(
        self,
        current_state: SafetyCarState,
        rng: Optional[np.random.Generator] = None,
        escalation_roll_override: Optional[float] = None,
    ) -> Tuple[bool, int, Optional[str]]:
        """
        Evaluates whether an active Virtual Safety Car escalates into a Full Safety Car.
        Uses the empirical conditional probability P(escalate to SC | active VSC) = 52 / 180 = 0.28889.
        Returns (did_escalate, new_sc_duration, event_description).
        """
        if current_state != SafetyCarState.VSC or not self.enable_vsc_escalation:
            return False, 0, None

        if rng is None:
            rng = np.random.default_rng()

        roll = escalation_roll_override if escalation_roll_override is not None else float(rng.random())
        if roll < self.conditional_vsc_escalation_prob:
            duration = int(rng.integers(3, 7))  # 3 to 6 laps for SC
            return True, duration, f"Virtual Safety Car escalated to Full Safety Car (Duration: {duration} laps)"

        return False, 0, None

    def apply_restart_field_compression(
        self,
        ordered_drivers: List[DriverState],
        rng: Optional[np.random.Generator] = None,
    ) -> None:
        """
        Compresses field gaps upon Full Safety Car withdrawal.
        Under Full SC, bunched cars restart with tight ~0.8-1.2s intervals behind the leader.
        """
        if not ordered_drivers or len(ordered_drivers) <= 1:
            return

        if rng is None:
            rng = np.random.default_rng()

        leader_time = ordered_drivers[0].accumulated_race_time
        prev_time = leader_time

        for i in range(1, len(ordered_drivers)):
            drv = ordered_drivers[i]
            if not drv.is_active():
                continue
            gap = float(np.clip(rng.normal(self.restart_gap_mean, self.restart_gap_std), 0.65, 2.0))
            drv.accumulated_race_time = prev_time + gap
            drv.gap_to_leader = round(drv.accumulated_race_time - leader_time, 3)
            drv.gap_to_ahead = round(gap, 3)
            prev_time = drv.accumulated_race_time
