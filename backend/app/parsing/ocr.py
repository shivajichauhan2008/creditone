"""Self-hosted OCR for image-only reports (Tesseract + OpenCV clean-up).

Page images stay in memory on our own servers. Swap in PaddleOCR later behind
`words_from_image` if accuracy needs it.
"""
import numpy as np


def preprocess(image) -> np.ndarray:
    """Binarise and strip table rules, coloured bars and the light watermark.

    - threshold at 180: light backgrounds (yellow headers, watermark, the two combined) turn white,
      text stays black;
    - solid filled shapes are inverted so light-on-dark text becomes readable;
    - long horizontal strokes (grid rules) are removed so Tesseract doesn't merge table rows.
    """
    import cv2

    rgb = np.array(image.convert("RGB"))
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    _, binary = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
    ink = 255 - binary
    h, w = ink.shape
    # Solid filled shapes (section bars, the score badge) usually carry light text on a dark
    # fill. Inverting inside each such shape turns that text into normal dark-on-light text.
    n, _, stats, _ = cv2.connectedComponentsWithStats(ink, connectivity=8)
    for x, y, bw, bh, area in stats[1:]:
        # big enough to be a bar or badge, never a letter (letters are < ~0.04 of page width)
        if bw >= 0.06 * w and bh >= 0.02 * h and area / (bw * bh) >= 0.6 and bw * bh < 0.25 * w * h:
            ink[y:y + bh, x:x + bw] = 255 - ink[y:y + bh, x:x + bw]
    horiz = cv2.morphologyEx(ink, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (max(60, w // 25), 1)))
    # Vertical grid rules are left in place: removing them also cuts strokes out of large digits
    # (the score). Tesseract reads them as '|', which words_from_image strips.
    lines = cv2.dilate(horiz, np.ones((3, 3), np.uint8))
    cleaned = cv2.bitwise_and(ink, cv2.bitwise_not(lines))
    return 255 - cleaned


def words_from_image(image, scale: float) -> list[dict]:
    """Return words with PDF-point coordinates: text, x0, x1, top, bottom."""
    import pytesseract  # imported lazily so text-layer PDFs need no OCR install

    clean = preprocess(image)
    px = _tesseract_words(clean, "--psm 6")
    px = _refine_payment_grids(clean, px)
    px = _refine_account_headers(clean, px)
    return [{"text": w["text"], "x0": w["x0"] * scale, "x1": w["x1"] * scale,
             "top": w["top"] * scale, "bottom": w["bottom"] * scale} for w in px]


GRID_CHARS = "0123456789STDMAUBLX"


def _tesseract_words(img, config: str, dx: int = 0, dy: int = 0) -> list[dict]:
    import pytesseract

    if img is None or img.size == 0 or min(img.shape[:2]) < 8:
        return []
    try:
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, config=config)
    except pytesseract.TesseractError:
        return []  # a bad crop must never sink the whole report
    out = []
    for i, text in enumerate(data["text"]):
        text = (text or "").strip().strip("|[]{}").strip()
        if not text or float(data["conf"][i]) < 0:
            continue
        x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
        out.append({"text": text, "x0": x + dx, "x1": x + w + dx, "top": y + dy, "bottom": y + h + dy})
    return out


MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def _is_month(t: str) -> bool:
    import difflib

    u = t.upper().replace("0", "O")[:3]
    return u in MONTHS or bool(difflib.get_close_matches(u, MONTHS, n=1, cutoff=0.6))


def _refine_payment_grids(img, words: list[dict]) -> list[dict]:
    """Re-read each payment-history row with a restricted alphabet.

    General OCR confuses '000' with 'ooo' and 'DBT' with 'ppt' in these small grids, so every
    row that starts with a year under a month header (DEC .. JAN) is cropped and read again
    with only digits and the classification letters allowed. The header is found by its month
    names, because the 'MONTH / YEAR' corner cell is often unreadable.
    """
    import re
    from statistics import median

    by_line: list[list[dict]] = []
    for wd in sorted(words, key=lambda w: (w["top"], w["x0"])):
        if by_line and abs(by_line[-1][0]["top"] - wd["top"]) < 0.5 * (wd["bottom"] - wd["top"]):
            by_line[-1].append(wd)
        else:
            by_line.append([wd])
    headers = []
    for ln in by_line:
        months = sorted([w for w in ln if _is_month(w["text"])], key=lambda w: w["x0"])
        year_word = next((w for w in ln if w["text"].upper() == "YEAR"), None)
        if year_word and len(ln) >= 10:
            # a readable 'YEAR' corner cell gives the year column directly
            headers.append({"x0": year_word["x0"], "x1": year_word["x1"] + 20,
                            "top": year_word["top"], "bottom": year_word["bottom"]})
        elif len(months) >= 9:
            gap = median(b["x0"] - a["x0"] for a, b in zip(months, months[1:]))
            headers.append({"x0": months[0]["x0"] - 1.8 * gap, "x1": months[0]["x0"] - 4,
                            "top": min(w["top"] for w in months), "bottom": max(w["bottom"] for w in months)})
    replace_ids: set[int] = set()
    added: list[dict] = []
    for hdr in headers:
        row_h = hdr["bottom"] - hdr["top"]
        cursor = hdr["bottom"]
        left = max(0, int(hdr["x0"]) - 10)
        while True:
            # the next row's year token sits in the column left of DEC
            cands = [w for w in words if hdr["x0"] - 20 <= w["x0"] <= hdr["x1"]
                     and cursor < w["top"] < cursor + 3.2 * row_h and re.fullmatch(r"[0-9oO]{3,4}", w["text"])]
            if not cands:
                break
            year = min(cands, key=lambda w: w["top"])
            y0, y1 = int(year["top"] - row_h * 0.45), int(year["bottom"] + row_h * 0.45)
            mid = lambda w: (w["top"] + w["bottom"]) / 2
            row = [i for i, w in enumerate(words)
                   if year["top"] - 3 <= mid(w) <= year["bottom"] + 3 and w["x0"] >= left]
            crop = _strip_vertical_rules(img[max(0, y0):y1, left:])
            fresh = _tesseract_words(crop, f"--psm 7 -c tessedit_char_whitelist={GRID_CHARS}", dx=left, dy=max(0, y0))
            if fresh and re.fullmatch(r"(19|20)\d\d", fresh[0]["text"]):
                replace_ids.update(row)
                added.extend(fresh)
            cursor = year["bottom"]
    return [w for i, w in enumerate(words) if i not in replace_ids] + added


def _strip_vertical_rules(crop):
    """Inside a grid row (small text only) the cell borders can be erased safely."""
    import cv2

    ink = 255 - crop
    k = max(10, int(crop.shape[0] * 0.6))
    vert = cv2.morphologyEx(ink, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, k)))
    vert = cv2.dilate(vert, np.ones((1, 3), np.uint8))
    return 255 - cv2.bitwise_and(ink, cv2.bitwise_not(vert))


def _refine_account_headers(img, words: list[dict]) -> list[dict]:
    """Re-read the lender / type / number / ownership band above each '(MEMBER NAME)' row.

    These names wrap across two lines in mixed column heights, which page-level OCR
    (block mode) handles poorly; sparse-text mode on just that band reads them reliably.
    """
    labels = [w for w in words if w["text"].upper().startswith("(MEMBER")]
    out = list(words)
    for lab in labels:
        row_h = lab["bottom"] - lab["top"]
        y0, y1 = int(max(0, lab["top"] - 4.2 * row_h)), int(lab["top"] - 2)
        fresh = _tesseract_words(img[y0:y1, :], "--psm 11", dy=y0)
        if len(fresh) >= 3:
            out = [w for w in out if not (y0 <= (w["top"] + w["bottom"]) / 2 <= y1)] + fresh
    return out
