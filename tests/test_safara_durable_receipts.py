"""Regresiones del circuito de justificantes sin depender de Google externo."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
APP_SOURCE = (ROOT / "app_safara_test.py").read_text(encoding="utf-8")
STORAGE_SOURCE = (ROOT / "safara_google_storage.py").read_text(encoding="utf-8")
MIGRATION_SOURCE = (
    ROOT / "supabase" / "migrations" / "20261119100500_add_durable_receipt_queue.sql"
).read_text(encoding="utf-8")


class DurableReceiptTests(unittest.TestCase):
    def test_schema_keeps_pending_receipts_private(self):
        self.assertIn("safara.justificantes_pendientes", MIGRATION_SOURCE)
        self.assertIn("enable row level security", MIGRATION_SOURCE)
        self.assertIn("using (false)", MIGRATION_SOURCE)
        self.assertIn("octet_length(contenido) between 1 and 10485760", MIGRATION_SOURCE)

    def test_expense_is_protected_before_drive_upload(self):
        saved = APP_SOURCE.index("crear_gasto_con_justificante_pendiente")
        uploaded = APP_SOURCE.index("almacenamiento_drive.upload_receipt", saved)
        self.assertLess(saved, uploaded)
        self.assertIn("REINTENTAR JUSTIFICANTES PENDIENTES", APP_SOURCE)

    def test_ticket_form_never_falls_back_to_the_legacy_writer(self):
        ticket_form = APP_SOURCE.split('with tab_sub_reg:', 1)[1].split(
            'with tab_sub_hist:', 1
        )[0]
        self.assertNotIn("guardar_gastos_persistentes()", ticket_form)
        self.assertIn("la base segura de Supabase no está disponible", ticket_form)

    def test_ticket_registration_requests_a_safe_google_report_refresh(self):
        ticket_form = APP_SOURCE.split('with tab_sub_reg:', 1)[1].split(
            'with tab_sub_hist:', 1
        )[0]
        self.assertIn("actualizar_informes_y_copias_en_segundo_plano()", ticket_form)

    def test_admin_keeps_google_refresh_as_an_explicit_fast_action(self):
        admin_panel = APP_SOURCE.split('if seccion_activa == "Administración":', 1)[1]
        initial_admin = admin_panel.split('st.markdown("#### Autorizar justificantes', 1)[0]
        self.assertNotIn("actualizar_informes_y_copias_en_segundo_plano()", initial_admin)
        self.assertIn("ACTUALIZAR INFORMES AHORA", admin_panel)
        self.assertIn("actualizar_informes_y_copias_en_segundo_plano()", admin_panel)

    def test_admin_retries_protected_receipts_only_on_explicit_request(self):
        admin_panel = APP_SOURCE.split('if seccion_activa == "Administración":', 1)[1]
        self.assertIn("reintentar_justificantes_pendientes_sin_interrumpir", admin_panel)
        self.assertIn("REINTENTAR JUSTIFICANTES PENDIENTES", admin_panel)
        before_button = admin_panel.split('if st.button("REINTENTAR JUSTIFICANTES PENDIENTES")', 1)[0]
        self.assertNotIn("reintentar_justificantes_pendientes_sin_interrumpir(", before_button)

    def test_google_reporting_is_scheduled_without_blocking_the_screen(self):
        maintenance = APP_SOURCE.split("def actualizar_informes_y_copias_en_segundo_plano():", 1)[1].split(
            "def reintentar_justificantes_pendientes_sin_interrumpir", 1
        )[0]
        self.assertIn("ThreadPoolExecutor", APP_SOURCE)
        self.assertIn(".submit(", maintenance)
        self.assertNotIn("return run_google_maintenance", maintenance)

    def test_primary_sections_are_loaded_only_when_opened(self):
        self.assertIn('seccion_activa = st.radio(', APP_SOURCE)
        self.assertNotIn('tab_movidas, tab_eventos, tab_gastos_app, tab_admin_app = st.tabs(', APP_SOURCE)
        self.assertIn('if seccion_activa == "Caja & Finanzas":', APP_SOURCE)

    def test_votes_request_an_isolated_google_report_refresh(self):
        vote_handler = APP_SOURCE.split("def registrar_voto_backend", 1)[1].split(
            "def obtener_voto_usuario", 1
        )[0]
        self.assertIn("actualizar_informes_y_copias_en_segundo_plano()", vote_handler)

    def test_supabase_detection_survives_a_streamlit_code_reload(self):
        self.assertIn("version_backend_supabase", APP_SOURCE)
        self.assertIn("safara_supabase_storage.py", APP_SOURCE)
        self.assertIn('"__name__", "") == "SupabaseSafaraStorage"', APP_SOURCE)
        self.assertIn("diagnostico_supabase_para_administracion", APP_SOURCE)

    def test_drive_does_not_initialize_sheets(self):
        start = STORAGE_SOURCE.index("def _drive_client")
        end = STORAGE_SOURCE.index("def crear_carpeta_justificantes_propietaria", start)
        self.assertNotIn("gspread", STORAGE_SOURCE[start:end])
        self.assertIn("crear_carpeta_justificantes_propietaria", STORAGE_SOURCE)


if __name__ == "__main__":
    unittest.main()
