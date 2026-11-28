import unittest
from unittest.mock import Mock, patch

from safara_production import PROYECTO_PRUEBAS, conexion_de_produccion_valida
from safara_supabase_storage import SupabaseSafaraStorage


class ProduccionTests(unittest.TestCase):
    def test_solo_acepta_el_proyecto_declarado(self):
        proyecto = "abcdefghijklmnopqrst"
        self.assertTrue(conexion_de_produccion_valida(
            f"postgresql://postgres.{proyecto}:oculta@aws-0-eu-west-1.pooler.supabase.com:5432/postgres?sslmode=require",
            proyecto,
        ))
        self.assertTrue(conexion_de_produccion_valida(
            f"postgresql://postgres:oculta@db.{proyecto}.supabase.co:5432/postgres", proyecto
        ))
        for url in (
            f"postgresql://postgres.{PROYECTO_PRUEBAS}:oculta@aws-0-eu-west-1.pooler.supabase.com:5432/postgres",
            f"postgresql://postgres.{proyecto}:oculta@aws-0-eu-west-1.pooler.supabase.com:6543/postgres",
            f"postgresql://postgres.{proyecto}:oculta@pooler.supabase.com.example.org:5432/postgres",
            "postgresql://postgres:oculta@127.0.0.1:5432/postgres",
        ):
            self.assertFalse(conexion_de_produccion_valida(url, proyecto))
        self.assertFalse(conexion_de_produccion_valida(
            f"postgresql://postgres:oculta@db.{PROYECTO_PRUEBAS}.supabase.co:5432/postgres",
            PROYECTO_PRUEBAS,
        ))

    def storage(self, rows):
        cursor = Mock()
        cursor.fetchone.side_effect = rows
        cursor.fetchall.return_value = [{"id": "invitacion", "codigo_hash": "hash"}]
        cursor.rowcount = 1
        database = object.__new__(SupabaseSafaraStorage)
        database._run = lambda callback: callback(cursor)
        return database, cursor

    def datos(self, rol):
        return {
            "rol": rol, "password_salt": "salt", "password_hash": "hash",
            "email": "prueba@example.org", "tel": "+34612345678", "fnac": "10/06/1998",
            "instrumento": "Caja",
        }

    def test_base_vacia_rechaza_el_alta_sin_activar(self):
        database, cursor = self.storage([{"total": 0}])
        self.assertFalse(database.registrar_usuario("Primera Persona", self.datos("admin")))
        self.assertFalse(any("insert into" in args[0] for args, _ in cursor.execute.call_args_list))

    def test_primera_alta_autorizada_es_admin(self):
        database, cursor = self.storage([{"total": 0}, {"id": "nuevo"}])
        self.assertTrue(database.registrar_usuario(
            "Primera Persona", self.datos("usuario"), bootstrap_autorizado=True
        ))
        self.assertEqual(cursor.execute.call_args.args[1][1], "admin")

    def test_alta_posterior_valida_invitacion_y_siempre_es_usuario(self):
        database, cursor = self.storage([{"total": 1}, {"id": "nuevo"}])
        with patch("safara_supabase_storage.verify_invitation_code", return_value=True):
            self.assertTrue(database.registrar_usuario(
                "Segunda Persona", self.datos("admin"), "invitacion", bootstrap_autorizado=True
            ))
        inserts = [args for args, _ in cursor.execute.call_args_list if "insert into" in args[0]]
        self.assertEqual(inserts[0][1][1], "usuario")
        self.assertIn("update safara.invitaciones", cursor.execute.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
