"""
NezaMateriales — Esquemas Pydantic para la calculadora de materiales.

Valida todas las medidas de obra recibidas antes de procesarlas,
según la convención definida en AGENTS.md.
"""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Tipos de resistencia permitidos para concreto
# ---------------------------------------------------------------------------
class FcResistance(int, Enum):
    """Resistencia f'c válida en kg/cm²."""
    FC_150 = 150
    FC_200 = 200


# ---------------------------------------------------------------------------
# Esquemas de entrada
# ---------------------------------------------------------------------------
class WallInput(BaseModel):
    """Datos de entrada para calcular materiales de un muro de tabique."""

    length: float = Field(
        ..., gt=0, description="Largo del muro en metros"
    )
    height: float = Field(
        ..., gt=0, description="Alto del muro en metros"
    )
    thickness: float = Field(
        default=14.0,
        gt=0,
        description="Espesor del muro en centímetros (default: 14 cm)"
    )
    waste_pct: float = Field(
        default=0.05,
        ge=0,
        le=0.50,
        description="Porcentaje de desperdicio (0.05 = 5%)"
    )


class SlabInput(BaseModel):
    """Datos de entrada para calcular materiales de una losa/piso de concreto."""

    length: float = Field(
        ..., gt=0, description="Largo de la losa en metros"
    )
    width: float = Field(
        ..., gt=0, description="Ancho de la losa en metros"
    )
    thickness: float = Field(
        ..., gt=0, description="Espesor de la losa en metros"
    )
    fc_resistance: FcResistance = Field(
        default=FcResistance.FC_150,
        description="Resistencia f'c del concreto: 150 o 200 kg/cm²"
    )
    waste_pct: float = Field(
        default=0.07,
        ge=0,
        le=0.50,
        description="Porcentaje de desperdicio (0.07 = 7%)"
    )


# ---------------------------------------------------------------------------
# Esquemas de salida
# ---------------------------------------------------------------------------
class MaterialResult(BaseModel):
    """Resultado de un material individual dentro del cálculo."""

    material: str = Field(..., description="Nombre del material")
    quantity: float = Field(..., description="Cantidad calculada")
    unit: str = Field(..., description="Unidad de medida")
    notes: str = Field(default="", description="Notas adicionales")


class CalculationResponse(BaseModel):
    """Respuesta completa del motor de cálculo."""

    element_type: Literal["muro", "losa"] = Field(
        ..., description="Tipo de elemento constructivo"
    )
    area_or_volume: float = Field(
        ..., description="Área (m²) o volumen (m³) calculado"
    )
    waste_pct: float = Field(
        ..., description="Porcentaje de desperdicio aplicado"
    )
    materials: list[MaterialResult] = Field(
        ..., description="Lista de materiales requeridos"
    )
