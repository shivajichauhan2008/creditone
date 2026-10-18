"""OCR slip handling learned from real report layouts (no real data in these tests)."""
from app.parsing.cibil import norm_dpd, parse_kv, sanity_check_dpd


def test_dpd_code_normalisation():
    assert norm_dpd("000") == "000"
    assert norm_dpd("ooo") == "000"
    assert norm_dpd("oo00") == "000"
    assert norm_dpd("o90") == "090"
    assert norm_dpd("stp") == "STD"
    assert norm_dpd("srp") == "STD"
    assert norm_dpd("st") == "STD"
    assert norm_dpd("xx") == "XXX"
    assert norm_dpd("DBT") == "DBT"
    assert norm_dpd("VALUE") is None


def test_lone_spike_is_corrected_and_reported():
    dpd = {"2019-10": "000", "2019-11": "900", "2019-12": "000"}
    fixed, notes = sanity_check_dpd(dpd)
    assert fixed["2019-11"] == "000" and len(notes) == 1


def test_real_delinquency_is_kept():
    dpd = {"2020-05": "000", "2020-06": "030", "2020-07": "060", "2020-08": "090"}
    fixed, notes = sanity_check_dpd(dpd)
    assert fixed == dpd and notes == []


def test_kv_tolerates_ocr_spacing():
    kv = parse_kv("CURRENT BALANCE 3,12,450 EMI AMOUNT -")
    assert kv["balance"] == "3,12,450" and kv["emi"] == "-"
