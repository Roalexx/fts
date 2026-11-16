import argparse
import json
import logging
from pathlib import Path
from typing import Optional, Sequence, Union
from dotenv import load_dotenv
from google import genai
from google.genai import errors, types
from pydantic import BaseModel, Field

from filament_profiles import get_filament_profile
from ocr import OCRComponent, OCRResult

load_dotenv()

logger = logging.getLogger(__name__)
_RETRYABLE_API_STATUS_CODES = [408, 429, 500, 502, 503, 504]


class FilamentLabel(BaseModel):
    material: str = Field(
        description="Filament hammaddesi (ör: PLA, PLA+, PETG, ABS, TPU, ASA). Tespit edilemezse 'UNKNOWN'."
    )
    color: str = Field(
        description="Etiketteki renk adı (ör: 'Kaan', 'Orange', 'Matte Black'). 'Color:' etiketi olmasa bile bağlamdan ve SKU ipuçlarından rengi tespit et."
    )
    hex_color: str = Field(
        description="Renk adından çıkarılan temsilî sRGB HEX renk kodu; tam olarak #RRGGBB biçiminde olmalı. Renk belirlenemiyorsa '#808080' yaz."
    )
    sku: Optional[str] = Field(
        default=None,
        description="Varsa ürün kodu / SKU.",
    )
    brand: str = Field(
        default="Generic",
        description="Marka logosunun tüm parçalarını birleştir; örneğin 'APEX' + '3DTECH' -> 'APEX3DTECH'. Tespit edilemez veya boşsa 'Generic' yaz.",
    )


class FilamentLabelParser:
    def __init__(
        self,
        model_name: str = "gemini-3.5-flash-lite",
        fallback_model_name: Optional[str] = "gemini-3.8-flash",
    ):
        # GEMINI_API_KEY ortam değişkenini otomatik okur
        self.client = genai.Client(
            http_options=types.HttpOptions(
                retry_options=types.HttpRetryOptions(
                    attempts=3,
                    initial_delay=1.0,
                    max_delay=8.0,
                    exp_base=2.0,
                    http_status_codes=_RETRYABLE_API_STATUS_CODES,
                )
            )
        )
        self.model_name = model_name
        self.fallback_model_name = fallback_model_name
        self.system_instruction = (
            "Sen 3D yazıcı filament etiketlerini ayrıştıran bir uzmansın. "
            "Sana verilen ham OCR metinlerinde yazım hataları veya düzensiz satır yapıları olabilir. "
            "Farklı markaların etiket formatlarını anlayarak hammaddeyi (PLA, PETG vb.) ve rengi doğru tespit et. "
            "Örneğin 'Color: Orange' yazıyorsa rengi 'Orange' olarak al; açıkça 'Color' yazmıyorsa "
            "materyal dışındaki özel renk/seri isimlerini (örneğin 'KAAN') ve SKU kısaltmalarını değerlendirerek rengi belirle. "
            "Marka için etiketteki/logodaki adın tamamını kullan; OCR metni markayı ayrı parçalara veya kutulara bölmüş olabilir. "
            "Bu parçaları birleştir ve baştaki marka kısmını atlama: 'APEX' ve '3DTECH' birlikteyse brand alanını 'APEX3DTECH' yaz, "
            "'3DTECH' olarak eksik bırakma. Marka bilgisinin bir kısmı okunabiliyorsa bunu koru; yalnızca hiç tespit edilemiyorsa 'Generic' kullan. "
            "Markayı tespit edemezsen veya marka bilgisi boşsa brand alanına 'Generic' yaz. "
            "Renk adına dayanarak hex_color alanına en yakın temsilî sRGB HEX kodunu üret; biçim tam olarak #RRGGBB olmalı "
            "(örneğin Orange için #FFA500, Black için #000000). Alpha kanalı veya kısa biçim kullanma. "
            "Renk adından çıkarım yapılamıyorsa hex_color için #808080 kullan."
        )

    def _generate_content(self, raw_ocr_text: str) -> types.GenerateContentResponse:
        contents = f"Aşağıdaki filament etiketi OCR çıktısını ayrıştır:\n\n{raw_ocr_text}"
        config = types.GenerateContentConfig(
            system_instruction=self.system_instruction,
            response_mime_type="application/json",
            response_schema=FilamentLabel,
            temperature=0.1,
        )
        try:
            return self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config,
            )
        except errors.APIError as exc:
            if (
                self.fallback_model_name is None
                or self.fallback_model_name == self.model_name
                or exc.code not in _RETRYABLE_API_STATUS_CODES
            ):
                raise

            logger.warning(
                "Ana model %s geçici API hatası verdi (HTTP %s); yedek model %s deneniyor.",
                self.model_name,
                exc.code,
                self.fallback_model_name,
            )
            return self.client.models.generate_content(
                model=self.fallback_model_name,
                contents=contents,
                config=config,
            )

    def parse(self, ocr_output: Union[str, Sequence[OCRResult]]) -> str:
        if isinstance(ocr_output, str):
            raw_ocr_text = ocr_output.strip()
        else:
            raw_ocr_text = "\n".join(
                result.text.strip() for result in ocr_output if result.text.strip()
            )

        if not raw_ocr_text:
            raise ValueError("OCR çıktısı boş; ayrıştırılacak metin bulunamadı.")

        response = self._generate_content(raw_ocr_text)
        if response.parsed is None:
            raise RuntimeError("Model, filament etiketi için yapılandırılmış çıktı üretmedi.")
        response.parsed.brand = response.parsed.brand.strip() or "Generic"
        label = response.parsed.model_dump()
        label["filament_id"] = get_filament_profile(label["material"]).filament_id
        return json.dumps(label, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser(
        description="Bir filament etiketi görselini OCR ile okuyup JSON çıktısı üretir."
    )
    argument_parser.add_argument(
        "image",
        nargs="?",
        type=Path,
        default=Path(__file__).with_name("ornek_belge.jpg"),
        help="İşlenecek görselin yolu (varsayılan: ornek_belge.jpg).",
    )
    args = argument_parser.parse_args()

    ocr = OCRComponent(languages=["tr", "en"], use_gpu=False)
    ocr_results = ocr.extract_from_path(str(args.image))
    print(FilamentLabelParser().parse(ocr_results))