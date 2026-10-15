"""
NezaMateriales — Pruebas unitarias del motor de cálculo de materiales.

Verifica que los cálculos matemáticos de rendimiento de obra
devuelvan los insumos correctos para:
  • 10 m² de muro de tabique rojo
  • 5 m³ de losa de concreto (f'c 150 y f'c 200)
  • Validación de entradas inválidas (Pydantic)

Se ejecuta con: pytest tests/test_calculator.py -v
No requiere conexión a MySQL (lógica pura).
"""

import math

import pytest
from pydantic import ValidationError

from backend.app.schemas.calculator import FcResistance, SlabInput, WallInput
from backend.app.services.calculator import (
    BRICKS_PER_M2,
    CEMENT_BAG_VOLUME_M3,
    CEMENT_RATIO_MORTAR,
    CONCRETE_MIX,
    MORTAR_VOLUME_PER_M2,
    SAND_RATIO_MORTAR,
    calculate_slab,
    calculate_wall,
)


# ═══════════════════════════════════════════════════════════════════════════
# MURO — 10 m²
# ═══════════════════════════════════════════════════════════════════════════

class TestWall10m2:
    """Pruebas para un muro de 5 m × 2 m = 10 m² con 5 % de desperdicio."""

    @pytest.fixture()
    def wall_result(self):
        data = WallInput(length=5.0, height=2.0)
        return calculate_wall(data)

    def test_element_type(self, wall_result):
        assert wall_result.element_type == "muro"

    def test_area(self, wall_result):
        assert wall_result.area_or_volume == 10.0

    def test_bricks_count(self, wall_result):
        """
        Piezas esperadas:
            52.36 pzas/m² × 10 m² = 523.6 → × 1.05 = 549.78 → ceil = 550
        """
        expected = math.ceil(BRICKS_PER_M2 * 10.0 * 1.05)
        bricks = next(
            m for m in wall_result.materials
            if "Tabique" in m.material
        )
        assert bricks.quantity == expected

    def test_cement_bags(self, wall_result):
        """
        Cemento esperado:
            0.025 m³/m² × 10 m² × (1/6) / 0.033 m³/bulto × 1.05
        """
        mortar = MORTAR_VOLUME_PER_M2 * 10.0
        cement_vol = mortar * CEMENT_RATIO_MORTAR
        expected = round((cement_vol / CEMENT_BAG_VOLUME_M3) * 1.05, 2)

        cement = next(
            m for m in wall_result.materials
            if "Cemento" in m.material
        )
        assert cement.quantity == expected

    def test_sand_volume(self, wall_result):
        """
        Arena esperada:
            0.025 m³/m² × 10 m² × (5/6) × 1.05
        """
        mortar = MORTAR_VOLUME_PER_M2 * 10.0
        expected = round(mortar * SAND_RATIO_MORTAR * 1.05, 4)

        sand = next(
            m for m in wall_result.materials
            if "Arena" in m.material
        )
        assert sand.quantity == expected

    def test_waste_percentage(self, wall_result):
        assert wall_result.waste_pct == 0.05


# ═══════════════════════════════════════════════════════════════════════════
# LOSA — 5 m³, f'c 150
# ═══════════════════════════════════════════════════════════════════════════

class TestSlab5m3Fc150:
    """Pruebas para una losa de 5 m × 2 m × 0.5 m = 5 m³, f'c=150, 7 % desperdicio."""

    @pytest.fixture()
    def slab_result(self):
        data = SlabInput(
            length=5.0,
            width=2.0,
            thickness=0.5,
            fc_resistance=FcResistance.FC_150,
        )
        return calculate_slab(data)

    def test_element_type(self, slab_result):
        assert slab_result.element_type == "losa"

    def test_volume(self, slab_result):
        assert slab_result.area_or_volume == 5.0

    def test_cement_bags(self, slab_result):
        """Cemento: 6.5 bultos/m³ × 5 m³ × 1.07 = 34.775 → round = 34.78"""
        mix = CONCRETE_MIX[150]
        expected = round(mix["cement_bags"] * 5.0 * 1.07, 2)
        cement = next(
            m for m in slab_result.materials
            if "Cemento" in m.material
        )
        assert cement.quantity == expected

    def test_sand(self, slab_result):
        """Arena: 0.56 m³/m³ × 5 m³ × 1.07"""
        mix = CONCRETE_MIX[150]
        expected = round(mix["sand_m3"] * 5.0 * 1.07, 4)
        sand = next(
            m for m in slab_result.materials
            if "Arena" in m.material
        )
        assert sand.quantity == expected

    def test_gravel(self, slab_result):
        """Grava: 0.63 m³/m³ × 5 m³ × 1.07"""
        mix = CONCRETE_MIX[150]
        expected = round(mix["gravel_m3"] * 5.0 * 1.07, 4)
        gravel = next(
            m for m in slab_result.materials
            if "Grava" in m.material
        )
        assert gravel.quantity == expected

    def test_water(self, slab_result):
        """Agua: 205 L/m³ × 5 m³ × 1.07"""
        mix = CONCRETE_MIX[150]
        expected = round(mix["water_liters"] * 5.0 * 1.07, 2)
        water = next(
            m for m in slab_result.materials
            if "Agua" in m.material
        )
        assert water.quantity == expected

    def test_waste_percentage(self, slab_result):
        assert slab_result.waste_pct == 0.07


# ═══════════════════════════════════════════════════════════════════════════
# LOSA — 5 m³, f'c 200
# ═══════════════════════════════════════════════════════════════════════════

class TestSlab5m3Fc200:
    """Pruebas para una losa de 5 m³ con f'c=200 kg/cm²."""

    @pytest.fixture()
    def slab_result(self):
        data = SlabInput(
            length=5.0,
            width=2.0,
            thickness=0.5,
            fc_resistance=FcResistance.FC_200,
        )
        return calculate_slab(data)

    def test_cement_bags_fc200(self, slab_result):
        """Cemento: 7.5 bultos/m³ × 5 m³ × 1.07"""
        mix = CONCRETE_MIX[200]
        expected = round(mix["cement_bags"] * 5.0 * 1.07, 2)
        cement = next(
            m for m in slab_result.materials
            if "Cemento" in m.material
        )
        assert cement.quantity == expected

    def test_sand_fc200(self, slab_result):
        mix = CONCRETE_MIX[200]
        expected = round(mix["sand_m3"] * 5.0 * 1.07, 4)
        sand = next(
            m for m in slab_result.materials
            if "Arena" in m.material
        )
        assert sand.quantity == expected

    def test_gravel_fc200(self, slab_result):
        mix = CONCRETE_MIX[200]
        expected = round(mix["gravel_m3"] * 5.0 * 1.07, 4)
        gravel = next(
            m for m in slab_result.materials
            if "Grava" in m.material
        )
        assert gravel.quantity == expected

    def test_water_fc200(self, slab_result):
        mix = CONCRETE_MIX[200]
        expected = round(mix["water_liters"] * 5.0 * 1.07, 2)
        water = next(
            m for m in slab_result.materials
            if "Agua" in m.material
        )
        assert water.quantity == expected


# ═══════════════════════════════════════════════════════════════════════════
# VALIDACIÓN DE ENTRADAS INVÁLIDAS (Pydantic)
# ═══════════════════════════════════════════════════════════════════════════

class TestInvalidInputs:
    """Verifica que Pydantic rechace entradas fuera de rango."""

    def test_wall_negative_length(self):
        with pytest.raises(ValidationError):
            WallInput(length=-1.0, height=2.0)

    def test_wall_zero_height(self):
        with pytest.raises(ValidationError):
            WallInput(length=5.0, height=0.0)

    def test_slab_negative_thickness(self):
        with pytest.raises(ValidationError):
            SlabInput(length=5.0, width=2.0, thickness=-0.1)

    def test_slab_invalid_fc_resistance(self):
        """f'c=180 no es un valor válido (solo 150 o 200)."""
        with pytest.raises(ValidationError):
            SlabInput(
                length=5.0,
                width=2.0,
                thickness=0.5,
                fc_resistance=180,
            )

    def test_wall_excessive_waste(self):
        """Desperdicio > 50 % no es razonable."""
        with pytest.raises(ValidationError):
            WallInput(length=5.0, height=2.0, waste_pct=0.60)
