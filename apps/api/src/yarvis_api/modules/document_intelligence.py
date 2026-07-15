from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DocumentIntelligenceResult:
    text: str
    provider: str
    method: str
    confidence: float


class OCRAdapter:
    def available(self) -> bool:
        try:
            import pytesseract  # type: ignore
            return hasattr(pytesseract, "image_to_string")
        except Exception:
            return False

    def extract_text(self, binary: bytes) -> DocumentIntelligenceResult:
        if not self.available():
            return DocumentIntelligenceResult(text="", provider="none", method="ocr_unavailable", confidence=0.0)
        # OCR execution is intentionally optional and conservative in Sprint 7.1A.
        return DocumentIntelligenceResult(text="", provider="tesseract", method="ocr_attempted", confidence=0.2)


class DocumentIntelligenceProvider:
    def __init__(self):
        self.ocr = OCRAdapter()

    def analyze_digital_pdf(self, extracted_text: str | None) -> DocumentIntelligenceResult:
        text = (extracted_text or "").strip()
        confidence = 0.98 if text else 0.0
        return DocumentIntelligenceResult(text=text, provider="local_pdf", method="digital_pdf", confidence=confidence)

    def analyze_document(self, *, mime_type: str, extracted_text: str | None, enable_ocr: bool, binary: bytes | None = None) -> DocumentIntelligenceResult:
        if mime_type == "application/pdf":
            result = self.analyze_digital_pdf(extracted_text)
            if result.text:
                return result
        if enable_ocr:
            return self.ocr.extract_text(binary or b"")
        return DocumentIntelligenceResult(text="", provider="none", method="no_extraction", confidence=0.0)
