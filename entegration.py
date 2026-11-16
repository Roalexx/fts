import argparse
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import quote

from filament_profiles import MATERIAL_PROFILE_MAP, get_filament_profile
from filament_weights import calculate_spool_weights

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class BambuCloudFilamentClient:
    BAMBU_PARENT_MAP = {
        material: (profile.parent_template, profile.base_id)
        for material, profile in MATERIAL_PROFILE_MAP.items()
    }

    def __init__(
        self,
        printer_suffix: str = "@BBL A1",
        schema_version: str = "2.9.0.75",
        token: Optional[str] = None,
    ):
        self.printer_suffix = printer_suffix
        self.schema_version = schema_version
        self.base_url = "https://api.bambulab.com"
        self.token = self._load_token(token)

    def _load_token(self, explicit_token: Optional[str]) -> str:
        """Token'ı parametreden, ortam değişkeninden veya .env dosyasından okur."""
        raw_token = explicit_token or os.environ.get("BAMBU_TOKEN", "")

        # python-dotenv yüklü değilse .env dosyasını doğrudan oku
        if not raw_token and Path(".env").exists():
            for line in Path(".env").read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("BAMBU_TOKEN="):
                    raw_token = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break

        # Kullanıcı "Bearer eyJ..." şeklinde yapıştırdıysa ön eki temizle
        token = raw_token.strip()
        if token.lower().startswith("bearer "):
            token = token[7:].strip()

        if not token:
            raise ValueError(
                ".env dosyasında BAMBU_TOKEN bulunamadı. Tarayıcıdan kopyaladığınız token'ı ekleyin."
            )
        return token

    def _request(
        self, method: str, endpoint: str, payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        data = json.dumps(payload).encode("utf-8") if payload is not None else None

        req = urllib.request.Request(
            url,
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "bambu_network_agent/01.09.05.01",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else {"status": resp.status}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            if e.code == 401:
                raise PermissionError(
                    "Token geçersiz veya süresi dolmuş (401 Unauthorized). "
                    "Tarayıcı Network sekmesinden 'Authorization: Bearer eyJ...' değerini kopyaladığınızdan emin olun."
                ) from e
            raise RuntimeError(f"Bambu Cloud API Hatası ({e.code}): {err_body}") from e

    def verify_token(self) -> Dict[str, Any]:
        """Token'ın Bambu Cloud API tarafından kabul edilip edilmediğini doğrular."""
        profile = self._request("GET", "/v1/user-service/my/profile")
        print(f"[OK] Token doğrulandı. Hesap: {profile.get('name') or profile.get('uid')}")
        return profile

    def add_filament_to_cloud(self, label_data: Dict[str, Any]) -> Dict[str, Any]:
        """Uygulama JSON çıktısını Bambu Cloud hesabına özel filament olarak ekler."""
        brand = (label_data.get("brand") or "Custom").strip()
        material = (label_data.get("material") or "PLA").strip().upper()
        color = (label_data.get("color") or "Default").strip()
        sku = (label_data.get("sku") or "").strip()
        weight_g = label_data.get("weight_g") or 1000

        hex_color = (label_data.get("hex_color") or "#FFFFFF").strip().upper()
        if not hex_color.startswith("#"):
            hex_color = f"#{hex_color}"

        material_profile = get_filament_profile(material)
        base_template = material_profile.parent_template
        base_id = material_profile.base_id
        parent_profile = f"{base_template} {self.printer_suffix}"
        display_name = f"{sku} - {color}" if sku else f"{brand} {material} - {color}"

        setting_body: Dict[str, str] = {
            "inherits": parent_profile,
            "updated_time": str(int(time.time())),
            "filament_settings_id": json.dumps(display_name, ensure_ascii=False),
            "filament_vendor": json.dumps(brand, ensure_ascii=False),
            "filament_type": json.dumps(material, ensure_ascii=False),
            "default_filament_colour": json.dumps(hex_color),
            "filament_extruder_variant": json.dumps("Direct Drive Standard"),
            "filament_notes": json.dumps(
                f"SKU: {sku} | Marka: {brand} | Ağırlık: {weight_g}g",
                ensure_ascii=False,
            ),
        }

        if label_data.get("nozzle_temp"):
            temp = str(label_data["nozzle_temp"])
            setting_body["nozzle_temperature"] = temp
            setting_body["nozzle_temperature_initial_layer"] = temp

        if label_data.get("bed_temp"):
            bed = str(label_data["bed_temp"])
            setting_body["textured_plate_temp"] = bed
            setting_body["textured_plate_temp_initial_layer"] = bed

        cloud_payload = {
            "type": "filament",
            "name": display_name,
            "version": self.schema_version,
            "base_id": base_id,
            "setting": setting_body,
        }

        result = self._request("POST", "/v1/iot-service/api/slicer/setting", cloud_payload)
        print(f"[OK] Filament Bambu Cloud'a eklendi: {display_name} ({hex_color})")
        return result

    def list_cloud_filaments(self) -> Dict[str, Any]:
        """Bambu Cloud hesabınızdaki kayıtlı özel profilleri listeler."""
        return self._request(
            "GET",
            f"/v1/iot-service/api/slicer/setting?version={self.schema_version}&public=false",
        )

    def get_cloud_filament(self, setting_id: str) -> Dict[str, Any]:
        """Tek bir özel filament presetini ID ile salt okunur olarak getirir."""
        if not setting_id.strip():
            raise ValueError("setting_id boş olamaz.")
        return self._request(
            "GET",
            f"/v1/iot-service/api/slicer/setting/{quote(setting_id, safe='')}",
        )

    def add_spool_to_filament_manager(
        self, label_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Var olan slicer presetine bağlı fiziksel makarayı bulut envanterine ekler."""
        sku = (label_data.get("sku") or "").strip()
        material = (label_data.get("material") or "PLA").strip().upper()
        material_profile = get_filament_profile(material)
        requested_filament_id = label_data.get("filament_id")
        if (
            requested_filament_id is not None
            and requested_filament_id != material_profile.filament_id
        ):
            raise ValueError(
                f"{material} için filament_id {material_profile.filament_id} olmalı; "
                f"JSON'da {requested_filament_id!r} geldi."
            )
        color = (label_data.get("color") or "Default").strip()
        display_name = f"{sku} - {color}" if sku else (
            f"{(label_data.get('brand') or 'Generic').strip()} "
            f"{(label_data.get('material') or 'PLA').strip().upper()} - {color}"
        )

        def find_preset() -> list:
            preset_response = self.list_cloud_filaments()
            filament_data = preset_response.get("filament")
            private_filaments = (
                filament_data.get("private", [])
                if isinstance(filament_data, dict)
                else []
            )
            return [
                preset
                for preset in private_filaments
                if isinstance(preset, dict) and preset.get("name") == display_name
            ]

        matching_presets = find_preset()
        if not matching_presets:
            created_preset = self.add_filament_to_cloud(label_data)
            setting_id = created_preset.get("setting_id")
            if not isinstance(setting_id, str) or not setting_id:
                raise RuntimeError(
                    f"'{display_name}' preset oluşturuldu ancak setting_id dönmedi."
                )
            matching_presets = [self.get_cloud_filament(setting_id)]

        if not matching_presets:
            raise RuntimeError(
                f"'{display_name}' adlı slicer preset bulutta bulunamadı. "
                "Önce presetin oluşturulduğunu doğrulayın."
            )
        if len(matching_presets) > 1:
            raise RuntimeError(
                f"'{display_name}' adıyla birden fazla preset bulundu; "
                "hangi presetin makaraya bağlanacağı belirsiz."
            )

        cloud_filament_id = matching_presets[0].get("filament_id")
        if not isinstance(cloud_filament_id, str) or not cloud_filament_id:
            raise RuntimeError(
                f"'{display_name}' presetinde makara için gerekli filament_id yok."
            )
        if cloud_filament_id != material_profile.filament_id:
            raise RuntimeError(
                f"'{display_name}' presetinin filament_id değeri "
                f"{cloud_filament_id}; {material} için beklenen "
                f"{material_profile.filament_id}."
            )

        try:
            spool_weights = calculate_spool_weights(label_data.get("weight_g"))
        except ValueError as exc:
            raise ValueError("Makara ağırlığı pozitif bir tam sayı olmalıdır.") from exc
        for field, expected_value in spool_weights._asdict().items():
            provided_value = label_data.get(field)
            if provided_value is not None and provided_value != expected_value:
                raise ValueError(f"{field} değeri girilen gramla uyuşmuyor.")

        brand = (label_data.get("brand") or "Generic").strip()
        hex_color = (label_data.get("hex_color") or "#FFFFFF").strip().upper()
        if not hex_color.startswith("#"):
            hex_color = f"#{hex_color}"

        spool_payload = {
            "createType": "manual",
            "filamentVendor": brand,
            "filamentType": material,
            "filamentName": sku or material,
            "filamentId": cloud_filament_id,
            "isSupport": False,
            "color": hex_color,
            "colorType": 2,
            "trayIdName": "",
            "rolls": 1,
            "netWeight": spool_weights.remaining_weight_g,
            "totalNetWeight": spool_weights.total_weight_g,
            "inPrinter": False,
            "note": (
                f"SKU: {sku} | Used: {spool_weights.used_weight_g}g | "
                f"Total: {spool_weights.total_weight_g}g | Color: {color}"
            ),
        }
        result = self._request(
            "POST",
            "/v1/design-user-service/my/filament/v2",
            spool_payload,
        )
        print(f"[OK] Makara Filament Yönetimi'ne eklendi: {display_name}")
        return result


# --- Çalıştırma ve Test ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group()
    action.add_argument(
        "--verify-setting-id",
        help="Belirtilen bulut presetini getirir; yeni kayıt oluşturmaz.",
    )
    action.add_argument(
        "--list-cloud-filaments",
        action="store_true",
        help="Buluttaki özel presetleri listeler; yeni kayıt oluşturmaz.",
    )
    action.add_argument(
        "--add",
        action="store_true",
        help="Yeni slicer filament presetini buluta ekler.",
    )
    action.add_argument(
        "--add-to-filament-manager",
        action="store_true",
        help="Mevcut preset için fiziksel makarayı Filament Yönetimi'ne ekler.",
    )
    args = parser.parse_args()

    app_output = {
        "material": "PLA",
        "color": "KAAN",
        "hex_color": "#707572",
        "sku": "PFPLAARIKN175IKG",
        "brand": "PORIMA",
        "weight_g": 1000,
    }

    client = BambuCloudFilamentClient(printer_suffix="@BBL A1", schema_version="2.9.0.75")

    # 1. Token'ı doğrula
    client.verify_token()

    if args.verify_setting_id:
        response = client.get_cloud_filament(args.verify_setting_id)
    elif args.add:
        response = client.add_filament_to_cloud(app_output)
    elif args.add_to_filament_manager:
        response = client.add_spool_to_filament_manager(app_output)
    else:
        response = client.list_cloud_filaments()

    print("Sunucu Yanıtı:", json.dumps(response, indent=2, ensure_ascii=False))