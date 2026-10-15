"""
NezaMateriales — Router para la Calculadora de Materiales (Muros y Losas).
"""

from fastapi import APIRouter
from backend.app.schemas.calculator import (
    CalculationResponse,
    SlabInput,
    WallInput,
)
from backend.app.services.calculator import calculate_slab, calculate_wall

router = APIRouter(prefix="/api/calculator", tags=["calculadora"])


@router.post("/wall", response_model=CalculationResponse)
def calculate_wall_materials(input_data: WallInput):
    """
    Calcula los materiales requeridos para un muro de tabique rojo (por m²).
    Incluye tabiques, cemento, arena y % de desperdicio.
    """
    return calculate_wall(input_data)


@router.post("/slab", response_model=CalculationResponse)
def calculate_slab_materials(input_data: SlabInput):
    """
    Calcula los materiales requeridos para una losa o piso de concreto (por m³).
    Incluye bultos de cemento, m³ de arena, m³ de grava, litros de agua y % de desperdicio según f'c.
    """
    return calculate_slab(input_data)
