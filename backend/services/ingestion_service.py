"""APEX — Idempotent Historical Ingestion Service."""

from datetime import datetime, date, timezone
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from backend.exceptions import IngestionError, ProviderError
from backend.models import (
    Season,
    Circuit,
    Event,
    Session as F1Session,
    Driver,
    Constructor,
    RaceResult,
    IngestionLog,
)
from backend.providers.jolpica import JolpicaProvider
from backend.providers.openf1 import OpenF1Provider

logger = logging.getLogger(__name__)


class IngestionService:
    """Orchestrates multi-provider ingestion into canonical relational tables with idempotency."""

    def __init__(
        self,
        jolpica: Optional[JolpicaProvider] = None,
        openf1: Optional[OpenF1Provider] = None,
    ):
        self.jolpica = jolpica or JolpicaProvider()
        self.openf1 = openf1 or OpenF1Provider()

    def ingest_event(
        self,
        db: Session,
        season_year: int,
        round_num: int,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """Idempotently ingests or updates a Grand Prix event, circuit, sessions, and race results."""
        logger.info(f"Beginning ingestion for season {season_year} round {round_num}")
        identifier = f"{season_year}_{round_num}"

        try:
            race_data = self.jolpica.get_race_results(season_year, round_num, force_refresh=force_refresh)
        except Exception as e:
            logger.error(f"Failed to fetch race data from Jolpica: {e}")
            self._log_ingestion(db, "jolpica", "event", identifier, "FAILED", 0, "", str(e))
            raise IngestionError(f"Could not retrieve Jolpica race results: {e}", details={"season": season_year, "round": round_num})

        payload_hash = self.jolpica.compute_payload_hash(race_data)

        # 1. Upsert Season
        season = db.query(Season).filter(Season.year == season_year).first()
        if not season:
            season = Season(year=season_year, url=race_data.get("url"))
            db.add(season)
            db.flush()

        # 2. Upsert Circuit
        circuit_data = race_data.get("Circuit", {})
        circuit_ref = circuit_data.get("circuitId", "unknown")
        location_data = circuit_data.get("Location", {})

        circuit = db.query(Circuit).filter(Circuit.circuit_ref == circuit_ref).first()
        if not circuit:
            circuit = Circuit(
                circuit_ref=circuit_ref,
                name=circuit_data.get("circuitName", "Unknown Circuit"),
                location=location_data.get("locality"),
                country=location_data.get("country"),
                latitude=float(location_data.get("lat")) if location_data.get("lat") else None,
                longitude=float(location_data.get("long")) if location_data.get("long") else None,
                url=circuit_data.get("url"),
                source_provider="jolpica",
            )
            db.add(circuit)
            db.flush()
        else:
            circuit.name = circuit_data.get("circuitName", circuit.name)
            circuit.location = location_data.get("locality", circuit.location)
            circuit.country = location_data.get("country", circuit.country)
            db.flush()

        # 3. Upsert Event
        event_date_str = race_data.get("date", str(date.today()))
        try:
            event_date = datetime.strptime(event_date_str, "%Y-%m-%d").date()
        except ValueError:
            event_date = date.today()

        event = (
            db.query(Event)
            .filter(Event.season_year == season_year, Event.round == round_num)
            .first()
        )
        if not event:
            event = Event(
                season_year=season_year,
                round=round_num,
                event_name=race_data.get("raceName", f"Round {round_num}"),
                circuit_id=circuit.id,
                date=event_date,
                time=race_data.get("time"),
                url=race_data.get("url"),
                source_provider="jolpica",
                source_id=f"{season_year}_{round_num}",
            )
            db.add(event)
            db.flush()
        else:
            event.event_name = race_data.get("raceName", event.event_name)
            event.circuit_id = circuit.id
            event.date = event_date
            event.time = race_data.get("time", event.time)
            db.flush()

        # 4. Ingest Sessions (from OpenF1 if available, fallback to Jolpica schedule)
        sessions_count = self._ingest_sessions(db, event, circuit, season_year, race_data, force_refresh)

        # 5. Ingest Drivers, Constructors, and Race Results
        results_list = race_data.get("Results", [])
        drivers_upserted = 0
        constructors_upserted = 0
        results_upserted = 0

        for res in results_list:
            # Driver
            driver_data = res.get("Driver", {})
            driver_ref = driver_data.get("driverId")
            if not driver_ref:
                continue

            driver = db.query(Driver).filter(Driver.driver_ref == driver_ref).first()
            dob = None
            if driver_data.get("dateOfBirth"):
                try:
                    dob = datetime.strptime(driver_data["dateOfBirth"], "%Y-%m-%d").date()
                except ValueError:
                    pass

            perm_num = None
            if driver_data.get("permanentNumber"):
                try:
                    perm_num = int(driver_data["permanentNumber"])
                except ValueError:
                    pass

            if not driver:
                driver = Driver(
                    driver_ref=driver_ref,
                    code=driver_data.get("code"),
                    permanent_number=perm_num,
                    first_name=driver_data.get("givenName", ""),
                    last_name=driver_data.get("familyName", ""),
                    date_of_birth=dob,
                    nationality=driver_data.get("nationality"),
                    url=driver_data.get("url"),
                    source_provider="jolpica",
                )
                db.add(driver)
                db.flush()
                drivers_upserted += 1
            else:
                if driver_data.get("code"):
                    driver.code = driver_data.get("code")
                if perm_num:
                    driver.permanent_number = perm_num
                db.flush()

            # Constructor
            const_data = res.get("Constructor", {})
            const_ref = const_data.get("constructorId")
            if not const_ref:
                continue

            constructor = db.query(Constructor).filter(Constructor.constructor_ref == const_ref).first()
            if not constructor:
                constructor = Constructor(
                    constructor_ref=const_ref,
                    name=const_data.get("name", const_ref),
                    nationality=const_data.get("nationality"),
                    url=const_data.get("url"),
                    source_provider="jolpica",
                )
                db.add(constructor)
                db.flush()
                constructors_upserted += 1
            else:
                constructor.name = const_data.get("name", constructor.name)
                db.flush()

            # Race Result
            pos = None
            try:
                pos = int(res.get("position"))
            except (ValueError, TypeError):
                pos = None

            grid_pos = 0
            try:
                grid_pos = int(res.get("grid", 0))
            except (ValueError, TypeError):
                grid_pos = 0

            pos_order = int(res.get("positionOrder", pos or 99))
            points_val = float(res.get("points", 0.0))
            laps_val = int(res.get("laps", 0))
            car_num = None
            if res.get("number"):
                try:
                    car_num = int(res.get("number"))
                except ValueError:
                    pass

            time_dict = res.get("Time", {})
            time_str = time_dict.get("time") if isinstance(time_dict, dict) else None
            time_ms = None
            if isinstance(time_dict, dict) and time_dict.get("millis"):
                try:
                    time_ms = int(time_dict["millis"])
                except ValueError:
                    pass

            fastest_lap = res.get("FastestLap", {})
            fl_rank = None
            fl_lap = None
            fl_time = None
            fl_speed = None
            if isinstance(fastest_lap, dict):
                try:
                    fl_rank = int(fastest_lap.get("rank")) if fastest_lap.get("rank") else None
                    fl_lap = int(fastest_lap.get("lap")) if fastest_lap.get("lap") else None
                    fl_time = fastest_lap.get("Time", {}).get("time")
                    fl_speed = float(fastest_lap.get("AverageSpeed", {}).get("speed")) if fastest_lap.get("AverageSpeed", {}).get("speed") else None
                except (ValueError, TypeError):
                    pass

            race_result = (
                db.query(RaceResult)
                .filter(RaceResult.event_id == event.id, RaceResult.driver_id == driver.id)
                .first()
            )
            if not race_result:
                race_result = RaceResult(
                    event_id=event.id,
                    driver_id=driver.id,
                    constructor_id=constructor.id,
                    number=car_num,
                    grid_position=grid_pos,
                    position=pos,
                    position_text=res.get("positionText", str(pos or "")),
                    position_order=pos_order,
                    points=points_val,
                    laps=laps_val,
                    status=res.get("status", "Finished"),
                    time_millis=time_ms,
                    time_string=time_str,
                    fastest_lap_rank=fl_rank,
                    fastest_lap_lap=fl_lap,
                    fastest_lap_time=fl_time,
                    fastest_lap_speed=fl_speed,
                    source_provider="jolpica",
                )
                db.add(race_result)
            else:
                race_result.constructor_id = constructor.id
                race_result.number = car_num
                race_result.grid_position = grid_pos
                race_result.position = pos
                race_result.position_text = res.get("positionText", str(pos or ""))
                race_result.position_order = pos_order
                race_result.points = points_val
                race_result.laps = laps_val
                race_result.status = res.get("status", race_result.status)
                race_result.time_millis = time_ms
                race_result.time_string = time_str
                race_result.fastest_lap_rank = fl_rank
                race_result.fastest_lap_lap = fl_lap
                race_result.fastest_lap_time = fl_time
                race_result.fastest_lap_speed = fl_speed

            results_upserted += 1

        db.flush()

        # Ingestion Log
        self._log_ingestion(
            db,
            "jolpica+openf1",
            "event",
            identifier,
            "SUCCESS",
            results_upserted,
            payload_hash,
            None,
        )
        db.commit()

        logger.info(
            f"Successfully ingested {event.event_name} ({season_year} R{round_num}): "
            f"{results_upserted} results, {sessions_count} sessions"
        )

        return {
            "status": "SUCCESS",
            "event_id": event.id,
            "season": season_year,
            "round": round_num,
            "event_name": event.event_name,
            "records_ingested": {
                "results": results_upserted,
                "sessions": sessions_count,
                "drivers_new": drivers_upserted,
                "constructors_new": constructors_upserted,
            },
            "message": f"Successfully ingested {event.event_name} ({season_year} R{round_num})",
        }

    def _ingest_sessions(
        self,
        db: Session,
        event: Event,
        circuit: Circuit,
        season_year: int,
        race_data: Dict[str, Any],
        force_refresh: bool,
    ) -> int:
        """Fetches session metadata from OpenF1 (or Jolpica timetable fallback) and upserts them."""
        openf1_sessions = []
        try:
            # Query OpenF1 by year and country / circuit
            country = circuit.country
            if country == "UAE":
                country = "United Arab Emirates"
            openf1_sessions = self.openf1.get_sessions(
                year=season_year,
                country_name=country,
                force_refresh=force_refresh,
            )
        except Exception as e:
            logger.warning(f"OpenF1 session query failed: {e}. Falling back to Jolpica timetable.")

        count = 0
        if openf1_sessions:
            # Map OpenF1 session types to canonical types
            type_mapping = {
                "Practice 1": "fp1",
                "Practice 2": "fp2",
                "Practice 3": "fp3",
                "Qualifying": "qualifying",
                "Sprint": "sprint",
                "Sprint Qualifying": "sprint_qualifying",
                "Sprint Shootout": "sprint_qualifying",
                "Race": "race",
            }
            for s in openf1_sessions:
                s_name = s.get("session_name", "")
                stype = type_mapping.get(s_name, s.get("session_type", "").lower())
                if not stype:
                    continue

                d_start = None
                d_end = None
                if s.get("date_start"):
                    try:
                        d_start = datetime.fromisoformat(s["date_start"])
                    except ValueError:
                        pass
                if s.get("date_end"):
                    try:
                        d_end = datetime.fromisoformat(s["date_end"])
                    except ValueError:
                        pass

                existing_sess = (
                    db.query(F1Session)
                    .filter(F1Session.event_id == event.id, F1Session.session_type == stype)
                    .first()
                )
                if not existing_sess:
                    sess = F1Session(
                        event_id=event.id,
                        session_type=stype,
                        session_name=s_name,
                        date_start=d_start,
                        date_end=d_end,
                        source_provider="openf1",
                        source_session_key=s.get("session_key"),
                    )
                    db.add(sess)
                else:
                    existing_sess.session_name = s_name
                    existing_sess.date_start = d_start
                    existing_sess.date_end = d_end
                    existing_sess.source_session_key = s.get("session_key", existing_sess.source_session_key)
                count += 1
        else:
            # Jolpica schedule fallback
            session_types = [
                ("FirstPractice", "fp1", "Practice 1"),
                ("SecondPractice", "fp2", "Practice 2"),
                ("ThirdPractice", "fp3", "Practice 3"),
                ("Qualifying", "qualifying", "Qualifying"),
                ("Sprint", "sprint", "Sprint"),
            ]
            for key, stype, sname in session_types:
                s_obj = race_data.get(key)
                if s_obj and isinstance(s_obj, dict):
                    dt_str = f"{s_obj.get('date')}T{s_obj.get('time', '00:00:00Z')}".replace("Z", "+00:00")
                    try:
                        dt = datetime.fromisoformat(dt_str)
                    except ValueError:
                        dt = None

                    existing_sess = (
                        db.query(F1Session)
                        .filter(F1Session.event_id == event.id, F1Session.session_type == stype)
                        .first()
                    )
                    if not existing_sess:
                        db.add(
                            F1Session(
                                event_id=event.id,
                                session_type=stype,
                                session_name=sname,
                                date_start=dt,
                                source_provider="jolpica",
                            )
                        )
                    count += 1

            # Grand Prix Race session
            race_dt_str = f"{race_data.get('date')}T{race_data.get('time', '00:00:00Z')}".replace("Z", "+00:00")
            try:
                race_dt = datetime.fromisoformat(race_dt_str)
            except ValueError:
                race_dt = None

            race_sess = (
                db.query(F1Session)
                .filter(F1Session.event_id == event.id, F1Session.session_type == "race")
                .first()
            )
            if not race_sess:
                db.add(
                    F1Session(
                        event_id=event.id,
                        session_type="race",
                        session_name="Race",
                        date_start=race_dt,
                        source_provider="jolpica",
                    )
                )
            count += 1

        db.flush()
        return count

    def _log_ingestion(
        self,
        db: Session,
        provider: str,
        entity_type: str,
        identifier: str,
        status: str,
        records_ingested: int,
        payload_hash: str,
        error_message: Optional[str] = None,
    ) -> None:
        """Records ingestion attempt in ingestion_logs table."""
        log = IngestionLog(
            provider=provider,
            entity_type=entity_type,
            identifier=identifier,
            status=status,
            records_ingested=records_ingested,
            payload_hash=payload_hash or "none",
            error_message=error_message,
            created_at=datetime.now(timezone.utc),
        )
        db.add(log)
        db.flush()
