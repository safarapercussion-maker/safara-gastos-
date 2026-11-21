from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
APP_SOURCE = (ROOT / "app_safara_test.py").read_text(encoding="utf-8")
STORAGE_SOURCE = (ROOT / "safara_supabase_storage.py").read_text(encoding="utf-8")


class ResponsivePollsTests(unittest.TestCase):
    def test_poll_results_use_a_short_shared_cache(self):
        self.assertIn('@st.cache_data(ttl=8, show_spinner=False, max_entries=1)', APP_SOURCE)
        self.assertIn('def cargar_votos_remotos', APP_SOURCE)
        self.assertIn('def invalidar_votos_compartidos', APP_SOURCE)

    def test_poll_control_refreshes_independently(self):
        self.assertIn('@st.fragment(run_every="8s")', APP_SOURCE)
        self.assertIn('def render_control_encuesta_en_vivo', APP_SOURCE)
        self.assertIn('recargar_votos_sin_bloquear()', APP_SOURCE)

    def test_dinner_poll_is_a_permanent_visible_weekly_question(self):
        self.assertIn('¿HOY SE CENA DESPUÉS DEL ENSAYO?', APP_SOURCE)
        self.assertIn('"cena_proxima", usuario_actual, "encuesta_cena_actual"', APP_SOURCE)
        self.assertIn('Encuesta semanal permanente', APP_SOURCE)

    def test_vote_upsert_resolves_user_inside_one_statement(self):
        vote_section = STORAGE_SOURCE.split('def guardar_voto', 1)[1].split(
            'def obtener_o_crear_plan_ensayo', 1
        )[0]
        self.assertIn('select %s, %s, id, %s', vote_section)
        self.assertNotIn('self._user_id(cursor, usuario)', vote_section)


if __name__ == "__main__":
    unittest.main()
