import unittest
import json

from safara_google_storage import GoogleStorageConfig, StorageConfigurationError, is_enabled


class GoogleStorageConfigTests(unittest.TestCase):
  def test_recognises_explicit_enablement(self):
    self.assertTrue(is_enabled({"enable_google_sheets_sync": True}))
    self.assertTrue(is_enabled({"enable_google_sheets_sync": "sí"}))
    self.assertFalse(is_enabled({"enable_google_sheets_sync": False}))

  def test_accepts_complete_service_account_configuration(self):
    config = GoogleStorageConfig.from_secrets({
        "safara_google_storage": {
            "spreadsheet_id": "1wywxlZ2Uju-EKIK9B7QJ-x1X2AFGS_qGf7HTDIHccvk",
            "receipts_folder_id": "1cv0RifxRqrkiB916A6gXnMuFrKSYWTK7",
        },
        "gcp_service_account": {
            "type": "service_account",
            "project_id": "safarapercussion",
            "private_key": "not-a-real-key-used-only-for-validation",
            "client_email": "test@safarapercussion.iam.gserviceaccount.com",
            "token_uri": "https://oauth2.googleapis.com/token",
        },
    })
    self.assertEqual(config.spreadsheet_id, "1wywxlZ2Uju-EKIK9B7QJ-x1X2AFGS_qGf7HTDIHccvk")

  def test_rejects_missing_service_account_values(self):
    with self.assertRaises(StorageConfigurationError):
      GoogleStorageConfig.from_secrets({
          "safara_google_storage": {"spreadsheet_id": "short", "receipts_folder_id": "short"},
          "gcp_service_account": {},
      })

  def test_accepts_json_service_account_secret(self):
    service_account = {
        "type": "service_account",
        "project_id": "safarapercussion",
        "private_key": "not-a-real-key-used-only-for-validation",
        "client_email": "test@safarapercussion.iam.gserviceaccount.com",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    config = GoogleStorageConfig.from_secrets({
        "safara_google_storage": {
            "spreadsheet_id": "1wywxlZ2Uju-EKIK9B7QJ-x1X2AFGS_qGf7HTDIHccvk",
            "receipts_folder_id": "1cv0RifxRqrkiB916A6gXnMuFrKSYWTK7",
        },
        "gcp_service_account_json": json.dumps(service_account),
    })
    self.assertEqual(config.service_account["client_email"], service_account["client_email"])


if __name__ == "__main__":
  unittest.main()
