"""Regresiones para los puntos automáticos de compromiso Safarer."""

from pathlib import Path
import ast
import unittest


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    ROOT / "supabase" / "migrations" / "20261122170754_add_vote_commitment_scoring.sql"
).read_text(encoding="utf-8")
STORAGE = (ROOT / "safara_supabase_storage.py").read_text(encoding="utf-8")
APP = (ROOT / "app_safara_test.py").read_text(encoding="utf-8")


class VoteCommitmentScoringTests(unittest.TestCase):
    def test_score_read_failure_does_not_escape_to_main_page(self):
        function = next(
            node for node in ast.parse(APP).body
            if isinstance(node, ast.FunctionDef)
            and node.name == "cargar_puntuacion_asistencia_remota"
        )
        function.decorator_list = []
        namespace = {}
        exec(compile(ast.Module(body=[function], type_ignores=[]), "<score-read>", "exec"), namespace)

        class UnavailableStorage:
            def obtener_puntuacion_asistencia(self):
                raise RuntimeError("connection temporarily closed")

        class ReadyStorage:
            def obtener_puntuacion_asistencia(self):
                return [{"nombre": "Safarer", "puntos": 2}]

        self.assertEqual(
            namespace["cargar_puntuacion_asistencia_remota"](UnavailableStorage()),
            {"disponible": False, "puntos": []},
        )
        self.assertEqual(
            namespace["cargar_puntuacion_asistencia_remota"](ReadyStorage()),
            {"disponible": True, "puntos": [{"nombre": "Safarer", "puntos": 2}]},
        )

    def test_scoring_starts_when_the_feature_is_activated(self):
        self.assertIn("puntuacion_asistencia_configuracion", MIGRATION)
        self.assertIn("votos_confirmados_desde", MIGRATION)
        self.assertIn("activada_en", MIGRATION)

    def test_only_current_yes_votes_score_points(self):
        section = STORAGE.split("def obtener_puntuacion_asistencia", 1)[1].split(
            "def crear_actuacion", 1
        )[0]
        self.assertIn("v.respuesta = 'SI'", section)
        self.assertIn("v.actualizado_en >= c.activada_en", section)
        self.assertIn("v.encuesta_id = 'ensayo_proximo'", section)
        self.assertIn("v.encuesta_id like 'bolo_%'", section)
        self.assertNotIn("cena_proxima", section)


if __name__ == "__main__":
    unittest.main()
