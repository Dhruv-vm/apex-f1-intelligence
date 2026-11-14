"""Circuit geometry endpoints."""
from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from backend.geometry import CircuitGeometry, CircuitRegistry, get_circuit_registry

router = APIRouter(prefix="/circuits", tags=["circuits"])


@router.get("", response_model=List[Dict[str, str]])
def list_circuits(registry: CircuitRegistry = Depends(get_circuit_registry)):
    """List all registered circuits and their geometry validation status."""
    return registry.list_available_circuits()


@router.get("/{circuit_ref}/geometry", response_model=CircuitGeometry)
def get_circuit_geometry(
    circuit_ref: str,
    registry: CircuitRegistry = Depends(get_circuit_registry),
):
    """Retrieve normalized track geometry, centerline, corners, and sectors for a circuit."""
    geometry = registry.get_circuit_geometry(circuit_ref)
    if not geometry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Geometry for circuit '{circuit_ref}' not found",
        )
    return geometry
