"""
NezaMateriales — Motor de cálculo de rendimiento de materiales.

Implementa las fórmulas de rendimiento para:
  • Muros de tabique rojo (por m²)
  • Losas / pisos de concreto (por m³)

Fuente de rendimientos: tablas estándar CMIC / BIMSA para obra civil en México.

⚠️  REGLA DE SEGURIDAD (AGENTS.md):
    No modificar las fórmulas matemáticas sin previa confirmación
    de parámetros técnicos de construcción.
"""

import math

from backend.app.schemas.calculator import (
    CalculationResponse,
    FcResistance,
    MaterialResult,
    SlabInput,
    WallInput,
)


# ═══════════════════════════════════════════════════════════════════════════
# CONSTANTES DE RENDIMIENTO — MUROS
# ═══════════════════════════════════════════════════════════════════════════

# Tabique rojo estándar: 6 cm × 12 cm × 24 cm
BRICK_HEIGHT_M = 0.06        # alto de la pieza en metros
BRICK_LENGTH_M = 0.24        # largo de la pieza en metros
MORTAR_JOINT_M = 0.015       # junta de mortero estándar: 1.5 cm

# Piezas por m² (incluye junta)
BRICKS_PER_M2 = 1.0 / (
    (BRICK_LENGTH_M + MORTAR_JOINT_M) * (BRICK_HEIGHT_M + MORTAR_JOINT_M)
)
# ≈ 52.36 piezas/m²

# Mortero proporción 1:5 (cemento:arena) por m² de muro
MORTAR_VOLUME_PER_M2 = 0.025   # m³ de mortero por m²
CEMENT_RATIO_MORTAR = 1 / 6    # 1 parte cemento en mezcla 1:5 (total 6 partes)
SAND_RATIO_MORTAR = 5 / 6      # 5 partes arena

# Un bulto de cemento de 50 kg ≈ 0.033 m³
CEMENT_BAG_VOLUME_M3 = 0.033


# ═══════════════════════════════════════════════════════════════════════════
# CONSTANTES DE RENDIMIENTO — LOSAS / CONCRETO
# ═══════════════════════════════════════════════════════════════════════════

# Dosificación volumétrica por m³ de concreto (tabla CMIC estándar)
CONCRETE_MIX: dict[int, dict[str, float]] = {
    150: {
        "cement_bags":  6.5,     # bultos de 50 kg por m³
        "sand_m3":      0.56,    # m³ de arena por m³
        "gravel_m3":    0.63,    # m³ de grava por m³
        "water_liters": 205.0,   # litros de agua por m³
    },
    200: {
        "cement_bags":  7.5,
        "sand_m3":      0.54,
        "gravel_m3":    0.62,
        "water_liters": 195.0,
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# FUNCIONES DE CÁLCULO
# ═══════════════════════════════════════════════════════════════════════════

def calculate_wall(data: WallInput) -> CalculationResponse:
    """
    Calcula los materiales requeridos para un muro de tabique rojo.

    Parámetros de rendimiento por m²:
        - ~52 piezas de tabique (junta de 1.5 cm)
        - ~0.30 bultos de cemento (mortero 1:5)
        - ~0.021 m³ de arena

    El desperdicio se aplica al final (default 5 %).
    """
    area = data.length * data.height  # m²
    waste = 1.0 + data.waste_pct

    # --- Tabiques ---
    raw_bricks = BRICKS_PER_M2 * area
    bricks = math.ceil(raw_bricks * waste)

    # --- Mortero ---
    mortar_volume = MORTAR_VOLUME_PER_M2 * area  # m³ total de mortero

    cement_volume = mortar_volume * CEMENT_RATIO_MORTAR  # m³ de cemento
    cement_bags = (cement_volume / CEMENT_BAG_VOLUME_M3) * waste

    sand_volume = (mortar_volume * SAND_RATIO_MORTAR) * waste  # m³ de arena

    materials = [
        MaterialResult(
            material="Tabique rojo 6×12×24 cm",
            quantity=bricks,
            unit="piezas",
            notes=f"{BRICKS_PER_M2:.2f} pzas/m² × {area:.2f} m² + {data.waste_pct:.0%} desperdicio",
        ),
        MaterialResult(
            material="Cemento (mortero 1:5)",
            quantity=round(cement_bags, 2),
            unit="bultos 50 kg",
            notes=f"Mortero proporción 1:5, {MORTAR_VOLUME_PER_M2} m³/m²",
        ),
        MaterialResult(
            material="Arena (mortero 1:5)",
            quantity=round(sand_volume, 4),
            unit="m³",
            notes="Arena para mortero de junta",
        ),
    ]

    return CalculationResponse(
        element_type="muro",
        area_or_volume=round(area, 4),
        waste_pct=data.waste_pct,
        materials=materials,
    )


def calculate_slab(data: SlabInput) -> CalculationResponse:
    """
    Calcula los materiales requeridos para una losa o piso de concreto.

    Dosificación volumétrica según resistencia f'c (150 o 200 kg/cm²).
    El desperdicio se aplica al final (default 7 %).
    """
    volume = data.length * data.width * data.thickness  # m³
    waste = 1.0 + data.waste_pct

    mix = CONCRETE_MIX[data.fc_resistance.value]

    cement_bags = mix["cement_bags"] * volume * waste
    sand_m3 = mix["sand_m3"] * volume * waste
    gravel_m3 = mix["gravel_m3"] * volume * waste
    water_liters = mix["water_liters"] * volume * waste

    fc_label = f"f'c={data.fc_resistance.value} kg/cm²"

    materials = [
        MaterialResult(
            material="Cemento Portland 50 kg",
            quantity=round(cement_bags, 2),
            unit="bultos",
            notes=f"Dosificación {fc_label}: {mix['cement_bags']} bultos/m³",
        ),
        MaterialResult(
            material="Arena",
            quantity=round(sand_m3, 4),
            unit="m³",
            notes=f"Dosificación {fc_label}: {mix['sand_m3']} m³/m³",
        ),
        MaterialResult(
            material="Grava 3/4\"",
            quantity=round(gravel_m3, 4),
            unit="m³",
            notes=f"Dosificación {fc_label}: {mix['gravel_m3']} m³/m³",
        ),
        MaterialResult(
            material="Agua",
            quantity=round(water_liters, 2),
            unit="litros",
            notes=f"Dosificación {fc_label}: {mix['water_liters']} L/m³",
        ),
    ]

    return CalculationResponse(
        element_type="losa",
        area_or_volume=round(volume, 4),
        waste_pct=data.waste_pct,
        materials=materials,
    )
