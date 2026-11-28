import unittest

from safara_poll_display import agrupar_por_instrumento


class PollInstrumentDisplayTests(unittest.TestCase):
    def test_confirmations_are_grouped_without_losing_unknown_instruments(self):
        users = {
            "Ana": {"instrumento": "Caja"},
            "Beto": {"instrumento": "Repenike"},
            "Celia": {},
        }
        groups = agrupar_por_instrumento(["Ana", "Beto", "Ana", "Celia"], users)
        self.assertEqual(groups["Caja"], ["Ana"])
        self.assertEqual(groups["Repenike"], ["Beto"])
        self.assertEqual(groups["Sin instrumento asignado"], ["Celia"])
        self.assertEqual(groups["Surdo"], [])


if __name__ == "__main__":
    unittest.main()
