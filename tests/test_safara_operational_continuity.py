from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / ".github" / "workflows" / "safara-daily-health.yml").read_text(
    encoding="utf-8"
)


class OperationalContinuityTests(unittest.TestCase):
    def test_health_check_runs_more_than_once_a_day(self):
        self.assertIn('cron: "17 2,8,14,20 * * *"', WORKFLOW)

    def test_health_check_tolerates_a_cold_start(self):
        self.assertIn("--max-time 120", WORKFLOW)
        self.assertIn("--retry-all-errors", WORKFLOW)
        self.assertIn("https://safara-test-seguridad.streamlit.app/", WORKFLOW)


if __name__ == "__main__":
    unittest.main()
