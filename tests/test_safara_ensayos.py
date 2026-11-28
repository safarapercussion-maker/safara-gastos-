import datetime as dt
import unittest
from zoneinfo import ZoneInfo

from safara_ensayos import (
    UBICACION_BARA,
    UBICACION_ZIZUR,
    ciclos_que_deben_cerrarse,
    informacion_ensayo,
    resultado_quorum,
)


MADRID = ZoneInfo("Europe/Madrid")


class CicloEnsayosTests(unittest.TestCase):
    def test_lunes_antes_de_las_ocho_mantiene_la_semana_anterior(self):
        info = informacion_ensayo(dt.datetime(2026, 11, 23, 7, 59, tzinfo=MADRID))
        self.assertEqual(info["ciclo_id"], "2026-W47")
        self.assertFalse(info["votacion_abierta"])
        self.assertEqual(info["ubicacion_nombre"], UBICACION_ZIZUR)

    def test_lunes_a_las_ocho_abre_nueva_encuesta_en_bara(self):
        info = informacion_ensayo(dt.datetime(2026, 11, 23, 8, 0, tzinfo=MADRID))
        self.assertEqual(info["ciclo_id"], "2026-W48")
        self.assertTrue(info["votacion_abierta"])
        self.assertEqual(info["ubicacion_nombre"], UBICACION_BARA)

    def test_viernes_a_las_diecinueve_treinta_cierra_la_encuesta(self):
        antes = informacion_ensayo(dt.datetime(2026, 11, 20, 19, 29, tzinfo=MADRID))
        self.assertTrue(antes["votacion_abierta"])
        info = informacion_ensayo(dt.datetime(2026, 11, 20, 19, 30, tzinfo=MADRID))
        self.assertFalse(info["votacion_abierta"])
        self.assertEqual(info["hora"], "19:30h")

    def test_quorum_exige_personas_repenike_y_caja(self):
        self.assertEqual(resultado_quorum(6, 1, 1), "CONFIRMADO")
        self.assertEqual(resultado_quorum(5, 1, 1), "NO_REALIZADO")
        self.assertEqual(resultado_quorum(6, 0, 1), "NO_REALIZADO")
        self.assertEqual(resultado_quorum(6, 1, 0), "NO_REALIZADO")

    def test_cierre_del_viernes_incluye_semana_actual(self):
        ciclos = ciclos_que_deben_cerrarse(dt.datetime(2026, 11, 20, 19, 31, tzinfo=MADRID))
        self.assertEqual(ciclos[0]["ciclo_id"], "2026-W47")


if __name__ == "__main__":
    unittest.main()
