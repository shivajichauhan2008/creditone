"""Report pipeline: unlock -> text layer or OCR -> detect bureau -> adapter -> validate."""
from ..models import ParsedReport
from . import cibil
from .detect import SUPPORTED, UnsupportedBureau, detect_bureau
from .pdf import PasswordRequired, WrongPassword, extract_lines, unlock
from .validate import validate

ADAPTERS = {"cibil": cibil.parse}

__all__ = ["parse_report", "PasswordRequired", "WrongPassword", "UnsupportedBureau"]


def parse_report(data: bytes, password: str | None = None) -> ParsedReport:
    plain = unlock(data, password)
    lines, used_ocr = extract_lines(plain)
    first_page = " ".join(ln.text for ln in lines if ln.page == 0)
    bureau = detect_bureau(first_page)
    if bureau not in SUPPORTED:
        raise UnsupportedBureau(bureau)
    report = ADAPTERS[bureau](lines, used_ocr=used_ocr)
    report.issues = validate(report)
    return report
