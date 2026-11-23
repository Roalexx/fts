import argparse
import base64
import binascii
import ipaddress
import json
import logging
import math
import os
import ssl
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlsplit

import cv2
import numpy as np
from google.genai import errors

from filament_profiles import (
    get_filament_id_map,
    get_filament_profile,
    resolve_filament_label_fields,
)
from filament_weights import calculate_spool_weights
from filament_catalog import (
    find_product_by_sku,
    initialize_catalog,
    upsert_product,
)
from https_certificates import discover_local_addresses, ensure_local_tls_certificates
from labeling import FilamentLabelParser
from ocr import OCRComponent


LOGGER = logging.getLogger(__name__)
initialize_catalog()
MAX_IMAGE_BYTES = 12 * 1024 * 1024
MAX_REQUEST_BYTES = 17 * 1024 * 1024
PAGE_PATH = Path(__file__).with_name("mainPage.html")
ALLOWED_CLIENT_NETWORKS = tuple(
    ipaddress.ip_network(network)
    for network in (
        "127.0.0.0/8",
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "169.254.0.0/16",
        "::1/128",
        "fc00::/7",
        "fe80::/10",
    )
)

_components: Optional[Tuple[OCRComponent, FilamentLabelParser]] = None
_components_lock = threading.Lock()


def _is_allowed_network_address(address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return any(
        address.version == network.version and address in network
        for network in ALLOWED_CLIENT_NETWORKS
    )


class RequestValidationError(Exception):
    pass


class FilamentHTTPServer(ThreadingHTTPServer):
    def handle_error(self, request: object, client_address: Tuple[str, int]) -> None:
        exception = sys.exc_info()[1]
        if isinstance(exception, (ConnectionResetError, ConnectionAbortedError, BrokenPipeError)):
            LOGGER.debug("Client %s closed its connection early: %s", client_address, exception)
            return
        super().handle_error(request, client_address)


def _get_components() -> Tuple[OCRComponent, FilamentLabelParser]:
    global _components
    if _components is None:
        with _components_lock:
            if _components is None:
                _components = (
                    OCRComponent(languages=["tr", "en"], use_gpu=False),
                    FilamentLabelParser(),
                )
    return _components


def _label_image(payload: object) -> dict:
    if not isinstance(payload, dict):
        raise RequestValidationError("Geçersiz istek verisi.")

    image_data_url = payload.get("image")
    if not isinstance(image_data_url, str):
        raise RequestValidationError("Bir filament görseli seçin veya çekin.")

    header, separator, encoded_image = image_data_url.partition(",")
    if (
        not separator
        or not header.startswith("data:image/")
        or ";base64" not in header
    ):
        raise RequestValidationError("Görsel verisi geçersiz.")

    try:
        image_bytes = base64.b64decode(encoded_image, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise RequestValidationError("Görsel verisi çözümlenemedi.") from exc

    if not image_bytes or len(image_bytes) > MAX_IMAGE_BYTES:
        raise RequestValidationError("Görsel boş veya 12 MB sınırını aşıyor.")

    weight_g = payload.get("weight_g")
    if (
        isinstance(weight_g, bool)
        or not isinstance(weight_g, (int, float))
        or not math.isfinite(weight_g)
        or not float(weight_g).is_integer()
        or weight_g <= 0
    ):
        raise RequestValidationError("Gram bilgisi pozitif bir tam sayı olmalı.")

    image = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise RequestValidationError("Görsel açılamadı; başka bir görsel deneyin.")

    ocr, parser = _get_components()
    ocr_results = ocr.extract_from_array(image)
    if not ocr_results:
        raise RequestValidationError("Görselde okunabilir etiket metni bulunamadı.")

    label = json.loads(parser.parse(ocr_results))
    label["weight_g"] = int(weight_g)
    label.update(calculate_spool_weights(int(weight_g))._asdict())
    return label


def _add_to_filament_manager(payload: object) -> dict:
    if not isinstance(payload, dict) or not isinstance(payload.get("label"), dict):
        raise RequestValidationError("Filament bilgileri geçersiz.")

    label = dict(payload["label"])
    for field in ("material", "color", "hex_color"):
        value = label.get(field)
        if not isinstance(value, str) or not value.strip():
            raise RequestValidationError(f"{field} alanı boş olamaz.")
        label[field] = value.strip()

    hex_color = label["hex_color"]
    if (
        len(hex_color) != 7
        or not hex_color.startswith("#")
        or any(char not in "0123456789abcdefABCDEF" for char in hex_color[1:])
    ):
        raise RequestValidationError("HEX renk kodu #RRGGBB biçiminde olmalı.")

    brand = label.get("brand", "")
    if not isinstance(brand, str):
        raise RequestValidationError("Marka metin olmalı.")
    label["brand"] = brand.strip() or "Generic"

    sku = label.get("sku")
    if sku is not None and not isinstance(sku, str):
        raise RequestValidationError("SKU metin olmalı.")
    if isinstance(sku, str):
        label["sku"] = sku.strip() or None

    try:
        label["material"], label["sku"] = resolve_filament_label_fields(
            label["material"],
            label.get("sku"),
        )
    except ValueError as exc:
        raise RequestValidationError(str(exc)) from exc

    expected_filament_id = get_filament_profile(label["material"]).filament_id
    provided_filament_id = label.get("filament_id")
    if provided_filament_id is not None and provided_filament_id != expected_filament_id:
        raise RequestValidationError(
            f"{label['material']} için filament_id {expected_filament_id} olmalı."
        )
    label["filament_id"] = expected_filament_id

    weight_g = label.get("weight_g")
    if (
        isinstance(weight_g, bool)
        or not isinstance(weight_g, (int, float))
        or not math.isfinite(weight_g)
        or not float(weight_g).is_integer()
        or weight_g <= 0
    ):
        raise RequestValidationError("Gram bilgisi pozitif bir tam sayı olmalı.")
    label["weight_g"] = int(weight_g)
    calculated_weights = calculate_spool_weights(label["weight_g"])._asdict()
    for field, expected_value in calculated_weights.items():
        if field in label and label[field] != expected_value:
            raise RequestValidationError(f"{field} değeri girilen gramla uyuşmuyor.")
        label[field] = expected_value

    from entegration import BambuCloudFilamentClient

    client = BambuCloudFilamentClient()
    existing_product = find_product_by_sku(label.get("sku"))
    if existing_product is not None:
        matches = all(
            existing_product.get(field) == label.get(field)
            for field in ("brand", "material", "filament_id", "color", "hex_color")
        )
        if not matches:
            raise RequestValidationError(
                "Bu SKU katalogda farklı marka, malzeme veya renkle kayıtlı. "
                "SKU’yu kontrol edip düzelterek tekrar deneyin."
            )

    result = client.add_spool_to_filament_manager(label)
    profile = get_filament_profile(label["material"])
    catalog_product = {
        **label,
        "parent_template": profile.parent_template,
        "base_id": profile.base_id,
        "filament_id": profile.filament_id,
    }
    saved_product = upsert_product(catalog_product)
    return {
        "result": result,
        "catalog_saved": True,
        "catalog_existing": existing_product is not None,
        "catalog_product": saved_product,
    }


class LabelingRequestHandler(BaseHTTPRequestHandler):
    https_port = 8443
    ca_certificate_path: Optional[Path] = None

    def _is_allowed_client(self) -> bool:
        try:
            address = ipaddress.ip_address(self.client_address[0])
        except ValueError:
            return False
        return _is_allowed_network_address(address)

    def _reject_untrusted_client(self) -> bool:
        if self._is_allowed_client():
            return False
        self._send_json(403, {"error": "Yalnızca yerel veya özel ağ cihazlarına izin verilir."})
        return True

    def _send_json(self, status_code: int, data: dict) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self._reject_untrusted_client():
            return
        request_path = urlsplit(self.path).path
        if request_path == "/root-ca.crt":
            if self.ca_certificate_path is None:
                self._send_json(503, {"error": "HTTPS sertifikası henüz hazır değil."})
                return
            try:
                certificate = self.ca_certificate_path.read_bytes()
            except OSError:
                LOGGER.exception("Yerel CA sertifikası okunamadı")
                self._send_json(500, {"error": "Sertifika sunucuda bulunamadı."})
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/x-x509-ca-cert")
            self.send_header("Content-Length", str(len(certificate)))
            self.send_header("Content-Disposition", 'attachment; filename="filament-local-ca.crt"')
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(certificate)
            return

        if request_path not in ("/", "/mainPage.html"):
            self._send_json(404, {"error": "Sayfa bulunamadı."})
            return

        try:
            page_text = PAGE_PATH.read_text(encoding="utf-8")
        except OSError:
            LOGGER.exception("mainPage.html okunamadı")
            self._send_json(500, {"error": "Web sayfası sunucuda bulunamadı."})
            return

        template_values = {
            "/*FILAMENT_ID_MAP*/ {}": json.dumps(get_filament_id_map(), ensure_ascii=False),
            "/*HTTPS_PORT*/ 8443": str(self.https_port),
        }
        for placeholder, value in template_values.items():
            if placeholder not in page_text:
                LOGGER.error("mainPage.html içinde şablon alanı bulunamadı: %s", placeholder)
                self._send_json(500, {"error": "Web sayfası yapılandırması tamamlanamadı."})
                return
            page_text = page_text.replace(placeholder, value)
        page = page_text.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(page)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        self.wfile.write(page)

    def do_POST(self) -> None:
        if self._reject_untrusted_client():
            return
        path = urlsplit(self.path).path
        if path not in (
            "/api/label",
            "/api/add-to-filament-manager",
        ):
            self._send_json(404, {"error": "API yolu bulunamadı."})
            return

        if not self.headers.get("Content-Type", "").startswith("application/json"):
            self._send_json(415, {"error": "İstek JSON biçiminde olmalı."})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json(400, {"error": "İstek boyutu geçersiz."})
            return

        if content_length <= 0:
            self._send_json(400, {"error": "İstek gövdesi boş."})
            return
        if content_length > MAX_REQUEST_BYTES:
            self._send_json(413, {"error": "Görsel 12 MB sınırını aşıyor."})
            return

        try:
            payload = json.loads(self.rfile.read(content_length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_json(400, {"error": "İstek JSON olarak okunamadı."})
            return

        if path == "/api/add-to-filament-manager":
            try:
                result = _add_to_filament_manager(payload)
            except RequestValidationError as exc:
                self._send_json(400, {"error": str(exc)})
                return
            except PermissionError as exc:
                self._send_json(401, {"error": str(exc)})
                return
            except (OSError, RuntimeError, ValueError) as exc:
                LOGGER.exception("Filament Yönetimi'ne ekleme başarısız oldu")
                self._send_json(502, {"error": str(exc)})
                return

            self._send_json(200, {"result": result})
            return

        try:
            label = _label_image(payload)
        except RequestValidationError as exc:
            self._send_json(400, {"error": str(exc)})
            return
        except errors.APIError as exc:
            LOGGER.exception("Etiket modeli isteği başarısız oldu")
            self._send_json(502, {"error": f"Etiket modeli yanıt vermedi: {exc}"})
            return
        except (OSError, RuntimeError, ValueError, cv2.error):
            LOGGER.exception("Görsel etiketleme başarısız oldu")
            self._send_json(
                500,
                {"error": "Etiketleme başarısız oldu. Sunucu terminalindeki hata kaydını kontrol edin."},
            )
            return

        self._send_json(200, {"label": label})


    def log_message(self, format_string: str, *args: object) -> None:
        LOGGER.info("%s - %s", self.address_string(), format_string % args)


def main() -> None:
    argument_parser = argparse.ArgumentParser(
        description="Filament etiketleme web uygulamasını yerel ağda başlatır."
    )
    argument_parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Dinlenecek adres (varsayılan: 0.0.0.0; yalnızca yerel kullanım için 127.0.0.1).",
    )
    argument_parser.add_argument("--port", type=int, default=8000)
    argument_parser.add_argument("--https-port", type=int, default=8443)
    args = argument_parser.parse_args()

    if args.port == args.https_port:
        argument_parser.error("--port ve --https-port farklı olmalı.")

    dns_names, ip_addresses = discover_local_addresses()
    app_data_directory = Path(
        os.environ.get("APPDATA", str(Path.home() / ".config"))
    ) / "FilamentEtiketleyici" / "certificates"
    certificate_files = ensure_local_tls_certificates(
        app_data_directory,
        dns_names,
        ip_addresses,
    )
    LabelingRequestHandler.https_port = args.https_port
    LabelingRequestHandler.ca_certificate_path = certificate_files.ca_certificate

    http_server = FilamentHTTPServer((args.host, args.port), LabelingRequestHandler)
    https_server: Optional[FilamentHTTPServer] = None
    try:
        https_server = FilamentHTTPServer(
            (args.host, args.https_port),
            LabelingRequestHandler,
        )
        tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        tls_context.minimum_version = ssl.TLSVersion.TLSv1_2
        tls_context.load_cert_chain(
            certificate_files.server_certificate,
            certificate_files.server_key,
        )
        https_server.socket = tls_context.wrap_socket(
            https_server.socket,
            server_side=True,
        )
    except (OSError, ssl.SSLError) as exc:
        http_server.server_close()
        if https_server is not None:
            https_server.server_close()
        raise RuntimeError(f"HTTPS sunucusu başlatılamadı: {exc}") from exc

    assert https_server is not None
    http_thread = threading.Thread(target=http_server.serve_forever, daemon=True)
    http_thread.start()
    if args.host == "0.0.0.0":
        print(f"Bu bilgisayarda: http://127.0.0.1:{args.port}", flush=True)
        print(f"Telefon kamerası için HTTPS: https://127.0.0.1:{args.https_port}", flush=True)
        addresses = {
            address
            for address in ip_addresses
            if not ipaddress.ip_address(address).is_loopback
            and not ipaddress.ip_address(address).is_link_local
        }
        if addresses:
            for address in sorted(addresses):
                print(f"Aynı Wi-Fi/ağdaki cihazlar: http://{address}:{args.port}", flush=True)
                print(f"Telefon kamerası HTTPS: https://{address}:{args.https_port}", flush=True)
                print(f"İlk kurulum CA sertifikası: http://{address}:{args.port}/root-ca.crt", flush=True)
        else:
            print("Ağ adresi otomatik bulunamadı; bilgisayarın IPv4 adresini ipconfig ile öğrenin.", flush=True)
        print("İlk kullanımda CA sertifikasını telefona yükleyin. Erişim özel ağ IP'leriyle sınırlıdır.", flush=True)
        print("Windows Güvenlik Duvarı'nda Python için Özel ağ erişimine izin verin.", flush=True)
        print(f"CA SHA-256 parmak izi: {certificate_files.ca_fingerprint}", flush=True)
    else:
        print(f"Uygulama HTTP: http://{args.host}:{args.port}", flush=True)
        print(f"Uygulama HTTPS: https://{args.host}:{args.https_port}", flush=True)
        print(f"CA sertifikası: http://{args.host}:{args.port}/root-ca.crt", flush=True)
        print(f"CA SHA-256 parmak izi: {certificate_files.ca_fingerprint}", flush=True)
    try:
        https_server.serve_forever()
    except KeyboardInterrupt:
        print("\nSunucu kapatılıyor.")
    finally:
        https_server.shutdown()
        http_server.shutdown()
        https_server.server_close()
        http_server.server_close()
        http_thread.join()


if __name__ == "__main__":
    main()
