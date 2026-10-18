"""PDF handling: unlock, text-layer check, OCR fallback, and line building.

Raw PDF bytes and page images stay in memory only; nothing here writes to disk.
"""
import io
import re
from dataclasses import dataclass, field

import pdfplumber
import pikepdf

from . import ocr


class PasswordRequired(Exception):
    pass


class WrongPassword(Exception):
    pass


@dataclass
class Word:
    text: str
    x0: float
    x1: float
    top: float
    bottom: float

    @property
    def cx(self) -> float:
        return (self.x0 + self.x1) / 2


@dataclass
class Line:
    page: int
    top: float
    page_height: float
    words: list[Word] = field(default_factory=list)

    @property
    def text(self) -> str:
        t = " ".join(w.text for w in self.words)
        t = re.sub(r"\s+", " ", t)
        return re.sub(r"\s+\(", "(", t) if "AMOUNT (" in t else t


def unlock(data: bytes, password: str | None = None) -> bytes:
    """Return an unencrypted copy of the PDF (in memory)."""
    try:
        pdf = pikepdf.open(io.BytesIO(data), password=password or "")
    except pikepdf.PasswordError:
        raise WrongPassword() if password else PasswordRequired()
    out = io.BytesIO()
    pdf.save(out)
    return out.getvalue()


def extract_lines(data: bytes, ocr_fallback: bool = True, min_words: int = 5) -> tuple[list[Line], bool]:
    """Words grouped into visual lines for every page. OCR is used for pages without a text layer."""
    lines: list[Line] = []
    used_ocr = False
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for i, page in enumerate(pdf.pages):
            raw = page.extract_words(x_tolerance=1.5, y_tolerance=2)
            if len(raw) < min_words and ocr_fallback:
                dpi = 300
                image = page.to_image(resolution=dpi).original
                raw = ocr.words_from_image(image, scale=72 / dpi)
                used_ocr = True
            words = [Word(w["text"], w["x0"], w["x1"], w["top"], w["bottom"]) for w in raw if w["text"].strip()]
            lines.extend(_group_lines(words, i, float(page.height)))
    return lines, used_ocr


def _group_lines(words: list[Word], page: int, height: float, tol: float = 3.5) -> list[Line]:
    """A word joins the current line when its vertical middle falls inside the line's band.

    OCR places short marks such as '-' a few points lower than the words beside them,
    so a plain top-coordinate match would split them onto their own line.
    """
    words = sorted(words, key=lambda w: (w.top, w.x0))
    out: list[Line] = []
    bands: list[tuple[float, float]] = []
    for w in words:
        mid = (w.top + w.bottom) / 2
        if out and (abs(out[-1].top - w.top) <= tol or bands[-1][0] - 1 <= mid <= bands[-1][1] + 1):
            out[-1].words.append(w)
            bands[-1] = (min(bands[-1][0], w.top), max(bands[-1][1], w.bottom))
        else:
            out.append(Line(page=page, top=w.top, page_height=height, words=[w]))
            bands.append((w.top, w.bottom))
    for ln in out:
        ln.words.sort(key=lambda w: w.x0)
    return out
