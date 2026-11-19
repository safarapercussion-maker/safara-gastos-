"""Regresiones del arranque: la pantalla de acceso no debe escribir datos."""

from pathlib import Path
import unittest


APP_SOURCE = (
    Path(__file__).resolve().parents[1] / "app_safara_test.py"
).read_text(encoding="utf-8")


class BootSequenceTests(unittest.TestCase):
    def test_working_data_loads_only_after_authentication(self):
        initializers = APP_SOURCE.split("# --- INICIALIZACIÓN DE VOTOS ---", 1)[1].split(
            "def guardar_gastos_persistentes", 1
        )[0]
        for dataset in (
            "votos_historial",
            "actuaciones",
            "confesionario_mensajes",
            "gastos",
            "saldo_caja",
        ):
            marker = f'"{dataset}" not in st.session_state'
            position = initializers.index(marker)
            section = initializers[position: position + 520]
            self.assertIn("usuario_autenticado_en_sesion()", section)

    def test_boot_does_not_write_actuaciones(self):
        section = APP_SOURCE.split(
            'if (\n    "actuaciones" not in st.session_state', 1
        )[1].split("# --- CONFESIONARIO PERSISTENTE ---", 1)[0]
        self.assertNotIn("guardar_actuaciones_excel()", section)

    def test_google_return_reloads_after_restoring_the_session(self):
        marker = "st.session_state.usuario_autenticado = usuario_retorno"
        section = APP_SOURCE.split(marker, 1)[1].split(
            "if st.session_state.usuario_autenticado:", 1
        )[0]
        self.assertIn("st.rerun()", section)

    def test_login_checks_pending_google_reports_without_opening_admin(self):
        marker = "usuario_actual = st.session_state.usuario_autenticado"
        section = APP_SOURCE.split(marker, 1)[1].split(
            'hoy_act = datetime.datetime.now', 1
        )[0]
        self.assertIn("actualizar_informes_y_copias_en_segundo_plano()", section)
        self.assertIn("mantenimiento_google_comprobado", section)
        self.assertIn("version_mantenimiento_google = version_backend_supabase()", section)

    def test_admin_status_is_safe_when_a_previous_cached_connection_is_present(self):
        marker = "# Estado breve y seguro: ayuda a comprobar el circuito completo"
        section = APP_SOURCE.split(marker, 1)[1].split("if estado_google:", 1)[0]
        self.assertIn('getattr(estado_seguro, "estado_mantenimiento_google", None)', section)
        self.assertIn("except (AttributeError, SupabaseStorageOperationError):", section)

    def test_supabase_cache_key_tracks_the_backend_source(self):
        marker = "def version_backend_supabase():"
        section = APP_SOURCE.split(marker, 1)[1].split(
            "@st.cache_resource", 1
        )[0]
        self.assertIn("safara_supabase_storage.py", section)
        self.assertIn("os.stat(source).st_mtime_ns", section)

    def test_vote_read_is_safe_during_an_external_return(self):
        marker = "def obtener_todos_votos_encuesta(encuesta_id):"
        section = APP_SOURCE.split(marker, 1)[1].split("def sincronizar_historial_ensayos", 1)[0]
        self.assertIn('st.session_state.get(\n      "votos_historial"', section)


if __name__ == "__main__":
    unittest.main()
