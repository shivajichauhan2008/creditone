"""Work out which bureau produced a report, from the first page's text."""


class UnsupportedBureau(Exception):
    def __init__(self, bureau: str):
        super().__init__(bureau)
        self.bureau = bureau


SUPPORTED = {"cibil"}


def detect_bureau(first_page_text: str) -> str:
    t = first_page_text.upper()
    if "CIBIL" in t or "TRANSUNION" in t:
        return "cibil"
    if "SAMPLE BUREAU" in t:  # synthetic fixtures use the CIBIL layout
        return "cibil"
    if "EXPERIAN" in t:
        return "experian"
    if "EQUIFAX" in t:
        return "equifax"
    if "CRIF" in t or "HIGH MARK" in t:
        return "crif"
    return "unknown"
