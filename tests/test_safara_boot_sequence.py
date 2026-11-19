"""Regresiones del arranque: la pantalla de acceso no debe escribir datos."""

from pathlib import Path
import unittest


APP_SOURCE = (
    Path(__file__).resolve().parents[1] / "app_safara_test.py"
).read_text(encoding="utf-8")


class BootSequenceTests(unittest.TestCase):
    def test_working_data_loads_only_after_authentication(self):
        for dataset in (
            "votos_historial",
            "actuaciones",
            "confesionario_mensajes",
            "gastos",
            "saldo_caja",
        ):
            self.assertIn(
                f'if "{dataset}" not in st.session_state and usuario_autenticado_en_sesion():',
                APP_SOURCE,
            )

    def test_boot_does_not_write_actuaciones(self):
        marker = (
            'if "actuaciones" not in st.session_state and '
            "usuario_autenticado_en_sesion():"
        )
        section = APP_SOURCE.split(marker, 1)[1].split(
            "# --- CONFESIONARIO PERSISTENTE ---", 1
        )[0]
        self.assertNotIn("guardar_actuaciones_excel()", section)

    def test_google_return_reloads_after_restoring_the_session(self):
        marker = "st.session_state.usuario_autenticado = usuario_retorno"
        section = APP_SOURCE.split(marker, 1)[1].split(
            "if st.session_state.usuario_autenticado:", 1
        )[0]
        self.assertIn("st.rerun()", section)

    def test_vote_read_is_safe_during_an_external_return(self):
        marker = "def obtener_todos_votos_encuesta(encuesta_id):"
        section = APP_SOURCE.split(marker, 1)[1].split("def sincronizar_historial_ensayos", 1)[0]
        self.assertIn('st.session_state.get(\n      "votos_historial"', section)


if __name__ == "__main__":
    unittest.main()
