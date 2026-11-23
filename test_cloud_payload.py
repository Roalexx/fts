import unittest

from entegration import BambuCloudFilamentClient


class CloudPayloadTest(unittest.TestCase):
    def test_sku_is_never_sent_as_filament_type(self):
        client = BambuCloudFilamentClient(token="test-token")
        captured = {}

        def capture_request(method, endpoint, payload=None):
            captured["method"] = method
            captured["endpoint"] = endpoint
            captured["payload"] = payload
            return {"setting_id": "test-setting"}

        client._request = capture_request
        client.add_filament_to_cloud({
            "brand": "Polymaker",
            "material": "PFEXPLA1SYH1751KG",
            "sku": "PFEXPLA1SYH1751KG",
            "color": "Siyah",
            "hex_color": "#000000",
        })

        setting = captured["payload"]["setting"]
        self.assertEqual(setting["filament_type"], '"PLA"')
        self.assertNotIn("PFEXPLA1SYH1751KG", setting["filament_type"])

    def test_spool_payload_keeps_sku_out_of_visible_material_type(self):
        client = BambuCloudFilamentClient(token="test-token")
        captured = {}

        client.list_cloud_filaments = lambda: {
            "filament": {
                "private": [{
                    "name": "PFPLAPSP1BBM1751KG - Siyah",
                    "filament_id": "GFL99",
                }]
            }
        }
        client.get_cloud_filament = lambda setting_id: {
            "filament_id": "GFL99",
        }

        def capture_request(method, endpoint, payload=None):
            captured["method"] = method
            captured["endpoint"] = endpoint
            captured["payload"] = payload
            return {"success": True}

        client._request = capture_request
        client.add_spool_to_filament_manager({
            "brand": "Polymaker",
            "material": "PFPLAPSP1BBM1751KG",
            "sku": "PFPLAPSP1BBM1751KG",
            "color": "Siyah",
            "hex_color": "#000000",
            "weight_g": 1000,
        })

        payload = captured["payload"]
        self.assertEqual(payload["filamentType"], "PLA")
        self.assertEqual(payload["filamentName"], "PLA")
        self.assertIn("PFPLAPSP1BBM1751KG", payload["note"])

    def test_spool_payload_preserves_variant_in_visible_material_type(self):
        client = BambuCloudFilamentClient(token="test-token")
        client.list_cloud_filaments = lambda: {
            "filament": {
                "private": [{
                    "name": "PLA Pastel SKU - Pembe",
                    "filament_id": "GFL99",
                }]
            }
        }
        captured = {}
        client._request = lambda method, endpoint, payload=None: (
            captured.update(payload=payload) or {"success": True}
        )

        client.add_spool_to_filament_manager({
            "material": "PLA Pastel",
            "sku": "PLA Pastel SKU",
            "color": "Pembe",
            "hex_color": "#FFC0CB",
            "weight_g": 1000,
        })

        self.assertEqual(captured["payload"]["filamentType"], "PLA")
        self.assertEqual(captured["payload"]["filamentName"], "PLA Pastel")


if __name__ == "__main__":
    unittest.main()
