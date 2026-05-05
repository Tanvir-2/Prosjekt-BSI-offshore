"""
Test fixture paths — both synthetic and real BSI files.

Synthetic files are in tests/fixtures/ (small, created programmatically).
Real BSI files are paths into tilgang/ (used for integration tests).
"""
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
DATA_ROOT = Path(__file__).resolve().parent.parent.parent / "tilgang" / "tilgang"


# ── Synthetic test files ───────────────────────────────────
SAMPLE_PDF = str(FIXTURES_DIR / "sample.pdf")
SAMPLE_DOCX = str(FIXTURES_DIR / "sample.docx")
SAMPLE_DOTX = str(FIXTURES_DIR / "sample.dotx")
SAMPLE_XLSX = str(FIXTURES_DIR / "sample.xlsx")
SAMPLE_XLSM = str(FIXTURES_DIR / "sample.xlsm")
SAMPLE_PPTX = str(FIXTURES_DIR / "sample.pptx")
SAMPLE_JPG = str(FIXTURES_DIR / "sample.jpg")
SAMPLE_ZIP = str(FIXTURES_DIR / "sample.zip")

EMPTY_PDF = str(FIXTURES_DIR / "empty.pdf")
EMPTY_DOCX = str(FIXTURES_DIR / "empty.docx")
EMPTY_XLSX = str(FIXTURES_DIR / "empty.xlsx")

CORRUPTED_PDF = str(FIXTURES_DIR / "corrupted.pdf")

# ── Real BSI files (for integration tests) ─────────────────
REAL_PDF = str(DATA_ROOT / "Prosjekt/Prosjekter 2023/3086 Transocean Encourage/07 Hms/Weber_Swedac_Visco_damping_layer_DG-U1_green__Component_A.pdf")
REAL_DOCX = str(DATA_ROOT / "Prosjekt/Prosjekter 2023/3086 Transocean Encourage/07 Hms/Maler/BSI-KS-314 HMS instruks for prosjekter.docx")
REAL_XLSX = str(DATA_ROOT / "Prosjekt/Prosjekter 2023/3086 Transocean Encourage/05 Tilbud/Kalkyle.xlsx")
REAL_XLS = str(DATA_ROOT / "Prosjekt/Prosjekter 2023/2912 KCA Askeladden - Flooring issues/03 Timelister/Maler/Mal CCB Daily timesheet.xls")
REAL_PPTX = str(DATA_ROOT / "Prosjekt/Prosjekter 2023/3048 Odfjell Drilling - DSS - Reparasjon av Isolasjon/Survey/Powerpoint DSS NY_Nummerert.pptx")
REAL_MSG = str(DATA_ROOT / "Prosjekt/Prosjekter 2023/2912 KCA Askeladden - Flooring issues/06 Fremdriftsplaner/rapport/week 46-47-48, 6th/Report 25_11_2023 - project no_ 2912 - week 46-48.msg")
REAL_JPG = str(DATA_ROOT / "Prosjekt/Prosjekter 2023/3086 Transocean Encourage/04 Personal/screenshot_20230425_112158_drive.jpg")
REAL_HEIC = str(DATA_ROOT / "Prosjekt/Prosjekter 2023/3086 Transocean Encourage/08 Bilder-tegninger/Bilder fra survey 2022/20230130_141753221_iOS.heic")
REAL_DOC = str(DATA_ROOT / "Prosjekt/Prosjekter 2023/3086 Transocean Encourage/10 Fraktbrev og pakksedler/IMDG.doc")
REAL_MOV = str(DATA_ROOT / "Prosjekt/Prosjekter 2023/3086 Transocean Encourage/08 Bilder-tegninger/Bilder fra survey 2022/video fra lugar A454.MOV")
REAL_ZIP = str(DATA_ROOT / "Prosjekt/Prosjekter 2023/3065 Deepsea Mira-Semco/08 Bilder-tegninger/check list 22 doors.zip")
REAL_LNK = str(DATA_ROOT / "Prosjekt/Prosjekter 2023/2912 KCA Askeladden - Flooring issues/05 Tilbud/3136 KCA ASL REQ-311009, CCR windows - Shortcut.lnk")
