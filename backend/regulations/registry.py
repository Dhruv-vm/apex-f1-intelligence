"""Effective-dated 2026 Formula 1 Regulation Registry.

Audited against official FIA 2026 Formula 1 Technical Regulations (Issue 21, 19 October 2026)
and WMSC statutory decisions / technical directives (FIA Category 2182).
"""
import logging
from datetime import date
from typing import Dict, List, Optional

from backend.regulations.models import RegulationRecord

logger = logging.getLogger("apex.regulations")


CANONICAL_2026_REGULATIONS: List[RegulationRecord] = [
    # 1. Power Unit Architecture & MGU-H Elimination
    RegulationRecord(
        regulation_id="REG-2026-PU-001",
        season=2026,
        category="POWER_UNIT",
        parameter_name="pu_architecture",
        parameter_value="1.6L V6 90deg turbocharged ICE with MGU-K only; MGU-H eliminated",
        units=None,
        description="Internal combustion engine remains 1.6-litre V6 turbocharged, but the Motor Generator Unit - Heat (MGU-H) is permanently eliminated to reduce complexity and supply barriers.",
        official_source="FIA 2026 Formula 1 Technical Regulations (Issue 21)",
        source_url="https://www.fia.com/regulation/category/2182",
        document_issue="Issue 21",
        relevant_article="Article 5.1.2",
        publication_date="2026-10-19",
        approval_date="2024-06-05",
        effective_from="2026-01-01",
        effective_until=None,
        session_applicability=["FP1", "FP2", "FP3", "QUALIFYING", "SPRINT", "RACE"],
        approval_status="APPROVED",
        provenance_notes="Ratified by World Motor Sport Council (WMSC). Formally codified in Issue 21.",
    ),

    # 2. Fuel Energy Flow (NOT Fuel Mass Flow)
    RegulationRecord(
        regulation_id="REG-2026-PU-002",
        season=2026,
        category="POWER_UNIT",
        parameter_name="fuel_energy_flow_cap",
        parameter_value="3000",
        units="MJ/h",
        description="Maximum fuel energy flow rate into the ICE is restricted to 3,000 MJ/h (reducing maximum ICE thermal output to ~400 kW / 536 bhp). Replaces previous 100 kg/h gravimetric limit.",
        official_source="FIA 2026 Formula 1 Technical Regulations (Issue 21)",
        source_url="https://www.fia.com/regulation/category/2182",
        document_issue="Issue 21",
        relevant_article="Article 5.4.1",
        publication_date="2026-10-19",
        approval_date="2024-06-05",
        effective_from="2026-01-01",
        effective_until=None,
        session_applicability=["FP1", "FP2", "FP3", "QUALIFYING", "SPRINT", "RACE"],
        approval_status="APPROVED",
        provenance_notes="Strictly an energy flow limit (MJ/h). Verified per Article 5.4.1.",
    ),

    # 3. MGU-K Maximum Electrical Power Output
    RegulationRecord(
        regulation_id="REG-2026-PU-003",
        season=2026,
        category="POWER_UNIT",
        parameter_name="mgu_k_power_output",
        parameter_value="350",
        units="kW",
        description="MGU-K maximum electrical deployment tripled from 120 kW (2022-2025 era) to 350 kW (~469 bhp), establishing a ~50/50 thermal/electrical power split (~1,000 bhp combined).",
        official_source="FIA 2026 Formula 1 Technical Regulations (Issue 21)",
        source_url="https://www.fia.com/regulation/category/2182",
        document_issue="Issue 21",
        relevant_article="Article 5.3.3",
        publication_date="2026-10-19",
        approval_date="2024-06-05",
        effective_from="2026-01-01",
        effective_until=None,
        session_applicability=["FP1", "FP2", "FP3", "QUALIFYING", "SPRINT", "RACE"],
        approval_status="APPROVED",
        provenance_notes="Substantially increases state-of-charge dependence across a lap.",
    ),

    # 4. Energy Recovery Ceiling (Technical Harvesting Limit)
    RegulationRecord(
        regulation_id="REG-2026-ENERGY-001",
        season=2026,
        category="ENERGY_MANAGEMENT",
        parameter_name="max_regen_energy_technical_ceiling",
        parameter_value="8.5",
        units="MJ",
        description="Technical ceiling: Maximum energy that may be recovered by the MGU-K into the Energy Store per lap is capped at 8.5 MJ.",
        official_source="FIA 2026 Formula 1 Technical Regulations (Issue 21)",
        source_url="https://www.fia.com/regulation/category/2182",
        document_issue="Issue 21",
        relevant_article="Article 5.5.2",
        publication_date="2026-10-19",
        approval_date="2024-06-05",
        effective_from="2026-01-01",
        effective_until=None,
        session_applicability=["FP1", "FP2", "FP3", "QUALIFYING", "SPRINT", "RACE"],
        approval_status="APPROVED",
        provenance_notes="Distinguished from tactical recharge limits under Article 5.5.3.",
    ),

    # 5. Permitted In-Race Recharge Limit (Pre-Miami: 8.0 MJ)
    RegulationRecord(
        regulation_id="REG-2026-ENERGY-RECHARGE-PRE",
        season=2026,
        category="ENERGY_MANAGEMENT",
        parameter_name="max_permitted_recharge_per_lap",
        parameter_value="8.0",
        units="MJ",
        description="Initial in-session permitted recharge limit: maximum 8.0 MJ of energy harvested into the Energy Store per lap. Superseded from Miami GP onwards.",
        official_source="FIA 2026 Formula 1 Technical Regulations (Issue 6)",
        source_url="https://www.fia.com/regulation/category/2182",
        document_issue="Issue 6",
        relevant_article="Article 5.5.3",
        publication_date="2024-06-06",
        approval_date="2024-06-05",
        effective_from="2026-01-01",
        effective_until="2026-04-30",
        session_applicability=["SPRINT", "RACE"],
        approval_status="SUPERSEDED",
        provenance_notes="Applicable to early-season rounds prior to Miami GP amendment.",
    ),

    # 6. Permitted In-Race Recharge Limit (Miami GP Onwards: 7.0 MJ)
    RegulationRecord(
        regulation_id="REG-2026-ENERGY-RECHARGE-MIA",
        season=2026,
        category="ENERGY_MANAGEMENT",
        parameter_name="max_permitted_recharge_per_lap",
        parameter_value="7.0",
        units="MJ",
        description="Miami GP Energy Amendment: Maximum permitted in-race recharge reduced from 8.0 MJ to 7.0 MJ per lap to tighten battery cycling and prevent excessive lift-and-coast recharge strategies.",
        official_source="FIA 2026 Formula 1 Technical Regulations (Issue 21)",
        source_url="https://www.fia.com/regulation/category/2182",
        document_issue="Issue 21",
        relevant_article="Article 5.5.3",
        publication_date="2026-10-19",
        approval_date="2026-04-18",
        effective_from="2026-05-01",
        effective_until=None,
        session_applicability=["SPRINT", "RACE"],
        approval_status="APPROVED",
        provenance_notes="Introduced from Miami Grand Prix (Round 6). Replaces REG-2026-ENERGY-RECHARGE-PRE.",
    ),

    # 7. Peak Superclip Harvesting Power (Pre-Miami: 250 kW)
    RegulationRecord(
        regulation_id="REG-2026-ENERGY-SUPERCLIP-PRE",
        season=2026,
        category="ENERGY_MANAGEMENT",
        parameter_name="peak_superclip_harvesting_power",
        parameter_value="250",
        units="kW",
        description="Initial straight-line superclip harvesting power limit: MGU-K harvesting while throttle is fully applied on straights capped at 250 kW.",
        official_source="FIA 2026 Formula 1 Technical Regulations (Issue 6)",
        source_url="https://www.fia.com/regulation/category/2182",
        document_issue="Issue 6",
        relevant_article="Article 5.4.10",
        publication_date="2024-06-06",
        approval_date="2024-06-05",
        effective_from="2026-01-01",
        effective_until="2026-04-30",
        session_applicability=["QUALIFYING", "SPRINT", "RACE"],
        approval_status="SUPERSEDED",
        provenance_notes="Superseded from Miami GP to align with 350 kW maximum MGU-K power.",
    ),

    # 8. Peak Superclip Harvesting Power (Miami GP Onwards: 350 kW)
    RegulationRecord(
        regulation_id="REG-2026-ENERGY-SUPERCLIP-MIA",
        season=2026,
        category="ENERGY_MANAGEMENT",
        parameter_name="peak_superclip_harvesting_power",
        parameter_value="350",
        units="kW",
        description="Miami GP Amendment: Peak superclip harvesting power increased from 250 kW to 350 kW, enabling full MGU-K generation capacity during partial-throttle or high-speed straight phases.",
        official_source="FIA 2026 Formula 1 Technical Regulations (Issue 21)",
        source_url="https://www.fia.com/regulation/category/2182",
        document_issue="Issue 21",
        relevant_article="Article 5.4.10",
        publication_date="2026-10-19",
        approval_date="2026-04-18",
        effective_from="2026-05-01",
        effective_until=None,
        session_applicability=["QUALIFYING", "SPRINT", "RACE"],
        approval_status="APPROVED",
        provenance_notes="Effective from May 1, 2026 (Miami GP onwards).",
    ),

    # 9. Electrical Deployment Tapering (Speed Derating)
    RegulationRecord(
        regulation_id="REG-2026-ENERGY-002",
        season=2026,
        category="ENERGY_MANAGEMENT",
        parameter_name="mgu_k_speed_derating_curve",
        parameter_value="350kW up to 290km/h; linear derate to 0kW at 345km/h",
        units=None,
        description="Standard deployment curve: MGU-K power delivery maintains full 350 kW up to vehicle speed of 290 km/h, then derates linearly down to 0 kW at 345 km/h to avoid rapid battery exhaustion.",
        official_source="FIA 2026 Formula 1 Technical Regulations (Issue 21)",
        source_url="https://www.fia.com/regulation/category/2182",
        document_issue="Issue 21",
        relevant_article="Article 5.4.8 & Appendix 3",
        publication_date="2026-10-19",
        approval_date="2024-06-05",
        effective_from="2026-01-01",
        effective_until=None,
        session_applicability=["QUALIFYING", "SPRINT", "RACE"],
        approval_status="APPROVED",
        provenance_notes="Standard power derate verified per Article 5.4.8.",
    ),

    # 10. Manual Override Mode (MOM) / Race Boost
    RegulationRecord(
        regulation_id="REG-2026-OVERTAKE-001",
        season=2026,
        category="OVERTAKE_MODE",
        parameter_name="manual_override_mode",
        parameter_value="350kW sustained up to 337km/h + 0.5MJ additional deployment energy",
        units=None,
        description="Driver within 1.0 second of car ahead at designated detection point can activate Manual Override Mode (MOM / Race Boost), extending 350 kW deployment up to 337 km/h with 0.5 MJ supplemental energy.",
        official_source="FIA 2026 Formula 1 Technical Regulations (Issue 21)",
        source_url="https://www.fia.com/regulation/category/2182",
        document_issue="Issue 21",
        relevant_article="Article 5.4.9 & Appendix 4",
        publication_date="2026-10-19",
        approval_date="2024-06-05",
        effective_from="2026-01-01",
        effective_until=None,
        session_applicability=["SPRINT", "RACE"],
        approval_status="APPROVED",
        provenance_notes="Electrical overtake mechanism replacing conventional aerodynamic DRS.",
    ),

    # 11. Active Aerodynamics: Straight Mode & Corner Mode
    RegulationRecord(
        regulation_id="REG-2026-AERO-001",
        season=2026,
        category="AERODYNAMICS",
        parameter_name="active_aero_modes",
        parameter_value="Dual mode: Corner Mode (High-Downforce) & Straight Mode (Low-Drag); X/Z-mode aliases",
        units=None,
        description="Active front and rear wing flaps with two official states: 'Corner Mode' (baseline flap deployment maximizing downforce, formerly Z-Mode) and 'Straight Mode' (feathered flaps on designated straight zones reducing overall drag by ~55%, formerly X-Mode).",
        official_source="FIA 2026 Formula 1 Technical Regulations (Issue 21)",
        source_url="https://www.fia.com/regulation/category/2182",
        document_issue="Issue 21",
        relevant_article="Article 3.12.1",
        publication_date="2026-10-19",
        approval_date="2024-06-05",
        effective_from="2026-01-01",
        effective_until=None,
        session_applicability=["FP1", "FP2", "FP3", "QUALIFYING", "SPRINT", "RACE"],
        approval_status="APPROVED",
        provenance_notes="Official FIA terminology: Corner Mode and Straight Mode (Issue 21, Art. 3.12).",
    ),

    # 12. Minimum Weight & Vehicle Dimensions
    RegulationRecord(
        regulation_id="REG-2026-CHASSIS-001",
        season=2026,
        category="CHASSIS",
        parameter_name="minimum_weight",
        parameter_value="768",
        units="kg",
        description="Minimum car mass without fuel reduced by 30 kg to 768 kg. Wheelbase capped at 3,400 mm (-200 mm); maximum overall width reduced to 1,900 mm (-100 mm).",
        official_source="FIA 2026 Formula 1 Technical Regulations (Issue 21)",
        source_url="https://www.fia.com/regulation/category/2182",
        document_issue="Issue 21",
        relevant_article="Article 4.1 & Article 3.2",
        publication_date="2026-10-19",
        approval_date="2024-06-05",
        effective_from="2026-01-01",
        effective_until=None,
        session_applicability=["FP1", "FP2", "FP3", "QUALIFYING", "SPRINT", "RACE"],
        approval_status="APPROVED",
        provenance_notes="Codified in Issue 21 Art 4.1.",
    ),

    # 13. Geometric Compression Ratio: Ambient Measurement Phase (Through 31 May 2026)
    RegulationRecord(
        regulation_id="REG-2026-TECH-CR-001",
        season=2026,
        category="POWER_UNIT",
        parameter_name="compression_ratio_ceiling_ambient",
        parameter_value="16.0:1 max geometric compression ratio measured under ambient conditions",
        units="ratio",
        description="Phase 1: Geometric cylinder compression ratio ceiling fixed at 16.0:1, verified exclusively under ambient conditions through 31 May 2026.",
        official_source="FIA World Motor Sport Council Decisions / Tech Directive",
        source_url="https://www.fia.com/regulation/category/2182",
        document_issue="WMSC 2026-02 / Issue 21",
        relevant_article="Article 5.1.8",
        publication_date="2026-02-14",
        approval_date="2026-02-12",
        effective_from="2026-01-01",
        effective_until="2026-05-31",
        session_applicability=["FP1", "FP2", "FP3", "QUALIFYING", "SPRINT", "RACE"],
        approval_status="SUPERSEDED",
        provenance_notes="Effective through 31 May 2026 under ambient measurement protocol.",
    ),

    # 14. Geometric Compression Ratio: Ambient & 130°C Measurement Phase (From 1 June 2026)
    RegulationRecord(
        regulation_id="REG-2026-TECH-CR-002",
        season=2026,
        category="POWER_UNIT",
        parameter_name="compression_ratio_ceiling_dual_temp",
        parameter_value="16.0:1 max geometric compression ratio measured under ambient conditions and at 130degC",
        units="ratio",
        description="Phase 2: From 1 June 2026, compliance with the 16.0:1 geometric compression ratio ceiling applies both under ambient conditions AND elevated operating temperature at 130degC to prevent thermal expansion manipulation.",
        official_source="FIA 2026 Formula 1 Technical Regulations (Issue 21)",
        source_url="https://www.fia.com/regulation/category/2182",
        document_issue="Issue 21",
        relevant_article="Article 5.1.8",
        publication_date="2026-10-19",
        approval_date="2026-02-12",
        effective_from="2026-06-01",
        effective_until=None,
        session_applicability=["FP1", "FP2", "FP3", "QUALIFYING", "SPRINT", "RACE"],
        approval_status="APPROVED",
        provenance_notes="Dual-temperature measurement effective from 1 June 2026 per Art. 5.1.8.",
    ),

    # 15. 100% Sustainable Advanced Drop-In Fuel
    RegulationRecord(
        regulation_id="REG-2026-FUEL-001",
        season=2026,
        category="POWER_UNIT",
        parameter_name="sustainable_fuel_specification",
        parameter_value="100% second-generation advanced bio-waste or non-bio synthetic e-fuel with zero fossil carbon",
        units=None,
        description="All power units must run exclusively on 100% sustainable drop-in fuel certified according to strict GHG life-cycle savings thresholds (>85% reduction vs fossil baseline).",
        official_source="FIA 2026 Formula 1 Technical Regulations (Issue 21)",
        source_url="https://www.fia.com/regulation/category/2182",
        document_issue="Issue 21",
        relevant_article="Article 16.1",
        publication_date="2026-10-19",
        approval_date="2024-06-05",
        effective_from="2026-01-01",
        effective_until=None,
        session_applicability=["FP1", "FP2", "FP3", "QUALIFYING", "SPRINT", "RACE"],
        approval_status="APPROVED",
        provenance_notes="Verified against Article 16 fuel standards.",
    ),
]


class RegulationRegistry:
    """Registry maintaining effective-dated regulations with point-in-time temporal queries."""

    def __init__(self):
        self._records: Dict[str, RegulationRecord] = {
            r.regulation_id: r for r in CANONICAL_2026_REGULATIONS
        }

    def get_regulation(self, regulation_id: str) -> Optional[RegulationRecord]:
        """Retrieve single regulation by identifier."""
        return self._records.get(regulation_id)

    def list_all_regulations(self, season: Optional[int] = None) -> List[RegulationRecord]:
        """List all regulations, optionally filtered by season (including superseded versions)."""
        recs = list(self._records.values())
        if season is not None:
            recs = [r for r in recs if r.season == season]
        return sorted(recs, key=lambda x: x.regulation_id)

    def get_applicable_regulations(
        self,
        season: int,
        event_date: str,
        session_type: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[RegulationRecord]:
        """
        Query applicable regulations enforcing strict effective dates.
        
        Args:
            season: Championship season (e.g. 2026)
            event_date: ISO date string YYYY-MM-DD of the event/session
            session_type: Optional session (e.g. 'FP1', 'QUALIFYING', 'RACE')
            category: Optional category filter (e.g. 'POWER_UNIT', 'AERODYNAMICS')
        """
        try:
            q_date = date.fromisoformat(event_date)
        except Exception as e:
            logger.error("Invalid event_date format '%s': %s", event_date, e)
            return []

        applicable: List[RegulationRecord] = []
        for r in self._records.values():
            # 1. Season match
            if r.season != season:
                continue

            # 2. Status match: only active rules on query date (ignore proposed)
            if r.approval_status not in ("APPROVED", "AMENDED", "SUPERSEDED"):
                continue

            # 3. Effective date boundaries: rule must be in effect on q_date
            eff_from = date.fromisoformat(r.effective_from)
            if q_date < eff_from:
                continue  # Rule not yet in effect

            if r.effective_until is not None:
                eff_until = date.fromisoformat(r.effective_until)
                if q_date > eff_until:
                    continue  # Rule has expired / superseded by newer version

            # 4. Session applicability
            if session_type is not None:
                norm_sess = session_type.upper().strip()
                if norm_sess not in r.session_applicability:
                    continue

            # 5. Category filter
            if category is not None:
                if r.category.upper() != category.upper():
                    continue

            applicable.append(r)

        return sorted(applicable, key=lambda x: x.regulation_id)


registry = RegulationRegistry()


def get_regulation_registry() -> RegulationRegistry:
    return registry
