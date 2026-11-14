"""APEX — API v1 Router Aggregator."""
from fastapi import APIRouter
from backend.api.v1.admin import router as admin_router
from backend.api.v1.circuits import router as circuits_router
from backend.api.v1.events import router as events_router
from backend.api.v1.health import router as health_router
from backend.api.v1.predictions import router as predictions_router
from backend.api.v1.regulations import router as regulations_router
from backend.api.v1.replay import router as replay_router
from backend.api.v1.seasons import router as seasons_router
from backend.api.v1.sessions import router as sessions_router
from backend.api.v1.simulation import router as simulation_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(health_router)
api_v1_router.include_router(seasons_router)
api_v1_router.include_router(events_router)
api_v1_router.include_router(sessions_router)
api_v1_router.include_router(circuits_router)
api_v1_router.include_router(replay_router)
api_v1_router.include_router(regulations_router)
api_v1_router.include_router(predictions_router)
api_v1_router.include_router(simulation_router)
api_v1_router.include_router(admin_router)
