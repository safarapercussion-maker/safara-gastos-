"""Regresiones de planificación, pausa y puntos de ensayos."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    ROOT / "supabase" / "migrations" / "20261120103000_add_rehearsal_planning_and_attendance.sql"
).read_text(encoding="utf-8")
STORAGE = (ROOT / "safara_supabase_storage.py").read_text(encoding="utf-8")
APP = (ROOT / "app_safara_test.py").read_text(encoding="utf-8")


class RehearsalPlanningTests(unittest.TestCase):
    def test_database_keeps_plans_pauses_and_confirmed_attendance(self):
        self.assertIn("safara.ensayos_planificacion", MIGRATION)
        self.assertIn("'PAUSADO'", MIGRATION)
        self.assertIn("safara.ensayos_asistencias", MIGRATION)
        self.assertIn("'CONFIRMADO', 'NO_REALIZADO', 'PAUSADO'", MIGRATION)

    def test_rotation_uses_the_last_active_location_not_a_paused_week(self):
        start = STORAGE.index("def obtener_o_crear_plan_ensayo")
        end = STORAGE.index("def actualizar_plan_ensayo", start)
        source = STORAGE[start:end]
        self.assertIn("estado='ACTIVO'", source)
        self.assertIn("order by lunes desc", source)
        self.assertIn("Baragazte (Barañain)", source)
        self.assertIn("Gaztetxe de Zizur", source)

    def test_points_are_derived_from_confirmed_attendance(self):
        self.assertIn("def confirmar_asistencias_ensayo", STORAGE)
        self.assertIn("delete from safara.ensayos_asistencias", STORAGE)
        self.assertIn("def obtener_puntuacion_ensayos", STORAGE)
        self.assertIn("count(a.ciclo_id)::integer as puntos", STORAGE)

    def test_administration_exposes_manual_plan_and_attendance_confirmation(self):
        self.assertIn("GUARDAR PLAN DEL ENSAYO", APP)
        self.assertIn("Esta semana no hay ensayo", APP)
        self.assertIn("CONFIRMAR ASISTENCIA Y SUMAR PUNTOS", APP)


if __name__ == "__main__":
    unittest.main()
