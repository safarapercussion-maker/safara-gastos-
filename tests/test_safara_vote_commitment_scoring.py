"""Regresiones para los puntos automáticos de compromiso Safarer."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    ROOT / "supabase" / "migrations" / "20261122170754_add_vote_commitment_scoring.sql"
).read_text(encoding="utf-8")
STORAGE = (ROOT / "safara_supabase_storage.py").read_text(encoding="utf-8")


class VoteCommitmentScoringTests(unittest.TestCase):
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
