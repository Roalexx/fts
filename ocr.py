from dataclasses import dataclass
from typing import List, Optional
import cv2
import easyocr
import numpy as np


@dataclass
class OCRResult:
    text: str
    confidence: float
    bbox: List[List[int]]  # [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]


@dataclass
class _OCRLine:
    top: int
    bottom: int
    items: List[OCRResult]

    @property
    def height(self) -> int:
        return max(self.bottom - self.top, 1)


class OCRComponent:
    def __init__(self, languages: List[str] = None, use_gpu: bool = False):
        if languages is None:
            languages = ["tr", "en"]
        # Model ilk çalıştırmada ağırlıkları indirir ve belleğe yükler
        self.reader = easyocr.Reader(languages, gpu=use_gpu)

    def __call__(self, image_path: str) -> str:
        """Görüntü yolunu alıp OCR sonucunu düz metin olarak döner."""
        return self.get_plain_text(image_path)

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Okuma doğruluğunu artırmak için temel görüntü iyileştirme."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Hafif gürültü temizleme
        denoised = cv2.fastNlMeansDenoising(gray, h=10)
        return denoised

    def extract_from_array(
        self,
        image: np.ndarray,
        preprocess: bool = True,
        min_confidence: float = 0.4,
    ) -> List[OCRResult]:
        """NumPy array (OpenCV görüntüsü) üzerinden metin ve koordinat çıkarır."""
        processed_img = self.preprocess_image(image) if preprocess else image
        raw_results = self.reader.readtext(processed_img)

        parsed_results: List[OCRResult] = []
        for bbox, text, conf in raw_results:
            if conf >= min_confidence:
                clean_bbox = [[int(pt[0]), int(pt[1])] for pt in bbox]
                parsed_results.append(
                    OCRResult(
                        text=text.strip(),
                        confidence=round(float(conf), 4),
                        bbox=clean_bbox,
                    )
                )
        return parsed_results

    def extract_from_path(
        self,
        image_path: str,
        preprocess: bool = True,
        min_confidence: float = 0.4,
    ) -> List[OCRResult]:
        """Dosya yolundan görüntüyü okuyup OCR uygular."""
        try:
            image_data = np.fromfile(image_path, dtype=np.uint8)
        except OSError as exc:
            raise FileNotFoundError(
                f"Görüntü dosyası bulunamadı veya okunamadı: {image_path}"
            ) from exc

        image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
        if image is None:
            raise FileNotFoundError(f"Görüntü dosyası bulunamadı veya okunamadı: {image_path}")
        return self.extract_from_array(image, preprocess, min_confidence)

    def get_plain_text(self, image_path: str, **kwargs) -> str:
        """Tespitleri dikey konumlarına göre satırlara ayırıp düz metin döner."""
        results = self.extract_from_path(image_path, **kwargs)
        lines: List[_OCRLine] = []

        for item in sorted(results, key=lambda result: min(point[1] for point in result.bbox)):
            top = min(point[1] for point in item.bbox)
            bottom = max(point[1] for point in item.bbox)
            height = max(bottom - top, 1)

            matching_line: Optional[_OCRLine] = None
            best_overlap = 0.0
            for line in lines:
                overlap = min(bottom, line.bottom) - max(top, line.top)
                min_height = min(height, line.height)
                if overlap > 0 and overlap / min_height >= 0.5 and overlap > best_overlap:
                    matching_line = line
                    best_overlap = overlap

            if matching_line is None:
                lines.append(_OCRLine(top=top, bottom=bottom, items=[item]))
            else:
                matching_line.top = min(matching_line.top, top)
                matching_line.bottom = max(matching_line.bottom, bottom)
                matching_line.items.append(item)

        lines.sort(key=lambda line: line.top)
        return "\n".join(
            " ".join(
                item.text
                for item in sorted(
                    line.items,
                    key=lambda result: min(point[0] for point in result.bbox),
                )
            )
            for line in lines
        )


# Örnek Kullanım
if __name__ == "__main__":
    ocr = OCRComponent(languages=["tr", "en"], use_gpu=False)
    text = ocr("ornek_belge.jpg")
    print(text)