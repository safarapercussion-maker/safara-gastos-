from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
APP_SOURCE = (ROOT / "app_safara_test.py").read_text(encoding="utf-8")
STORAGE_SOURCE = (ROOT / "safara_supabase_storage.py").read_text(encoding="utf-8")


class ResponsivePollsTests(unittest.TestCase):
    def test_poll_results_use_a_short_shared_cache(self):
        self.assertIn('@st.cache_data(ttl=15, show_spinner=False, max_entries=1)', APP_SOURCE)
        self.assertIn('def cargar_votos_remotos', APP_SOURCE)
        self.assertIn('def invalidar_votos_compartidos', APP_SOURCE)

    def test_poll_control_refreshes_independently(self):
        self.assertIn('@st.fragment(run_every="15s")', APP_SOURCE)
        self.assertIn('def render_control_encuesta_en_vivo', APP_SOURCE)
        self.assertIn('recargar_votos_sin_bloquear()', APP_SOURCE)
        self.assertIn('st.rerun(scope="fragment")', APP_SOURCE)

    def test_balance_adjustment_does_not_reload_administration(self):
        self.assertIn('@st.fragment\ndef render_ajuste_saldo_rapido', APP_SOURCE)
        self.assertIn('render_ajuste_saldo_rapido(usuario_actual)', APP_SOURCE)
        self.assertIn('st.session_state["_saldo_guardado"]', APP_SOURCE)

    def test_event_votes_share_the_lightweight_poll_control(self):
        self.assertIn('f"encuesta_bolo_{bolo_id}"', APP_SOURCE)
        self.assertIn('st-key-vote_positive_', APP_SOURCE)
        self.assertIn('st-key-vote_negative_', APP_SOURCE)
        self.assertIn('"A tope, se le da"', APP_SOURCE)
        self.assertIn('"No puedo, tengo lío"', APP_SOURCE)
        self.assertNotIn('"CONFIRMAR"', APP_SOURCE)

    def test_administration_prioritizes_event_launch_and_clean_download(self):
        self.assertIn('def render_lanzador_bolo_prioritario', APP_SOURCE)
        self.assertIn('render_lanzador_bolo_prioritario(usuario_actual)', APP_SOURCE)
        self.assertIn('key="financial-download"', APP_SOURCE)

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
