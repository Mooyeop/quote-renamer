"""
견적서/거래명세서/세금계산서 PDF 자동 리네이밍 도구
==============================
[문서종류]회사이름_날짜_첫번째항목_외_N종.pdf 형식으로 파일명을 제안합니다.
문서종류는 PDF 안의 제목 텍스트를 보고 자동으로 판별합니다.
"""
import re
import sys
import json
import csv
from pathlib import Path
import pdfplumber

# ── 설정 ──────────────────────────────────────────────────────────
# 날짜 형식은 extract_date() 마지막 줄에서 직접 조정 (기본: YYYYMMDD, 예 20260731)
MAX_ITEM_LEN = 40               # 파일명에 들어갈 첫 항목명 최대 길이
SELF_COMPANY_PATTERNS = ["로보티즈", "ROBOTIS"]   # 우리 회사(수신자) - 후보에서 제외


def get_app_dir() -> Path:
    """실행 파일(또는 스크립트)이 위치한 폴더. PyInstaller로 exe를 만들면
    __file__이 임시 압축해제 폴더를 가리키게 되므로, company_aliases.json이나
    번들된 tesseract처럼 exe 옆에 실제로 있어야 하는 파일을 찾을 때는
    이 함수를 써야 한다."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


ALIASES_PATH = get_app_dir() / "company_aliases.json"
LOCAL_ALIASES_PATH = get_app_dir() / "company_aliases.local.json"


def load_aliases() -> dict:
    # company_aliases.local.json은 git에 올라가지 않는 실제 거래처 매핑 파일 -
    # 존재하면 이걸 우선 사용한다 (공개 저장소의 company_aliases.json은 예시일 뿐).
    if LOCAL_ALIASES_PATH.exists():
        return json.loads(LOCAL_ALIASES_PATH.read_text(encoding="utf-8"))
    if ALIASES_PATH.exists():
        return json.loads(ALIASES_PATH.read_text(encoding="utf-8"))
    return {}


def strip_corp_prefix(name: str) -> str:
    name = name.strip()
    name = re.sub(r"^(㈜|\(주\)|주식회사)\s*", "", name)
    name = re.sub(r"\s*(㈜|\(주\)|주식회사)$", "", name)
    return name.strip()


# ── PDF에서 텍스트/표 읽기 (텍스트 없으면 OCR) ─────────────────────
def read_pdf(path: Path):
    full_text_parts = []
    all_tables = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            if not text.strip():
                # 스캔본(텍스트 레이어 없음) -> OCR
                text = ocr_page(page)
            full_text_parts.append(text)
            all_tables.extend(page.extract_tables() or [])
    return "\n".join(full_text_parts), all_tables


def _configure_tesseract_cmd(pytesseract) -> None:
    """Tesseract 실행 파일 위치를 찾아 pytesseract에 알려준다. 우선순위:
    1) exe 옆에 번들된 tesseract/ 폴더 (배포판 - 아무 설치 없이 바로 동작)
    2) 시스템 PATH
    3) Windows 기본 설치 경로 (PATH 등록을 놓치고 수동 설치한 경우)"""
    import os
    import shutil as _shutil

    bundled = get_app_dir() / "tesseract" / "tesseract.exe"
    if bundled.exists():
        pytesseract.pytesseract.tesseract_cmd = str(bundled)
        tessdata = bundled.parent / "tessdata"
        if tessdata.exists():
            os.environ["TESSDATA_PREFIX"] = str(tessdata)
        return

    if _shutil.which("tesseract"):
        return

    for candidate in (
        Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
        Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
    ):
        if candidate.exists():
            pytesseract.pytesseract.tesseract_cmd = str(candidate)
            return


def ocr_page(page) -> str:
    try:
        import pytesseract
    except ImportError:
        return ""
    _configure_tesseract_cmd(pytesseract)
    img = page.to_image(resolution=300).original
    try:
        return pytesseract.image_to_string(img, lang="kor+eng")
    except Exception:
        # Tesseract 엔진 미설치, 한국어 언어팩 누락 등 - 이 페이지만 텍스트 없이 넘어가고
        # 나머지 파일 처리는 계속 진행 (extract_* 쪽에서 "추출 실패" 경고로 처리됨)
        return ""


# ── 문서 종류 판별 (견적서 / 거래명세서 / 세금계산서) ─────────────────
# 순서가 우선순위: 개수가 같으면 앞쪽이 이김. 거래명세서 본문에 "세금계산서는
# 익일 발송됩니다" 같은 안내문이 섞여 있어도, 실제 제목은 반복 등장하므로
# 거래명세서를 먼저 두면 이런 본문 언급에 오탐하지 않는다.
DOC_TYPE_PATTERNS = [
    ("거래명세서", re.compile(r"거\s*래\s*명\s*세\s*[서표]")),
    ("세금계산서", re.compile(r"세\s*금\s*계\s*산\s*서")),
    ("견적서", re.compile(r"견\s*적\s*(?:의\s*뢰\s*서|서)")),
]


def detect_doc_type(text: str) -> tuple[str, str]:
    """반환: (문서종류, 경고메시지 or '')"""
    counts = [(label, len(pat.findall(text))) for label, pat in DOC_TYPE_PATTERNS]
    best_label, best_count = max(counts, key=lambda x: x[1])
    if best_count == 0:
        return "견적서", "⚠ 문서 종류를 확인하지 못해 [견적서]로 표시함 - 확인 필요"
    return best_label, ""


# ── 회사명 추출 ───────────────────────────────────────────────────
LABEL_PATTERNS = {"상호", "상호(법인명)", "회사명"}
REGNUM_RE = re.compile(r"\d{3}-\d{2}-\d{5}")


def normalize_cell(cell) -> str:
    if cell is None:
        return ""
    return re.sub(r"\s+", "", str(cell))


def extract_company(text: str, tables: list, aliases: dict) -> tuple[str, str]:
    """반환: (표시할_회사이름, 경고메시지 or '')"""
    candidates = []
    for table in tables:
        table_text = " ".join(normalize_cell(c) for row in table for c in row)
        has_regnum = bool(REGNUM_RE.search(table_text))
        for row in table:
            for i, cell in enumerate(row):
                norm = normalize_cell(cell)
                if norm in LABEL_PATTERNS:
                    for value in row[i + 1:]:
                        if value and str(value).strip():
                            candidates.append((str(value).strip(), has_regnum))
                            break
    # 자기 회사명 후보 제외
    filtered = [
        (v, hr) for v, hr in candidates
        if not any(p in v for p in SELF_COMPANY_PATTERNS)
    ]
    # 등록번호가 같은 표에 있는 후보 우선
    filtered.sort(key=lambda x: not x[1])

    if filtered:
        raw_name = strip_corp_prefix(filtered[0][0])
        display = aliases.get(raw_name, raw_name)
        warn = "" if raw_name in aliases else f"⚠ 별칭 미등록('{raw_name}') - company_aliases.json에 추가 권장"
        return display, warn

    # 폴백: 이메일 도메인에서 추출 (로고만 있고 텍스트 라벨이 없는 경우)
    email_match = re.search(r"@([a-zA-Z0-9\-]+)\.", text)
    if email_match:
        domain = email_match.group(1)
        display = aliases.get(domain, domain)
        warn = f"⚠ 회사명을 텍스트에서 찾지 못해 이메일 도메인('{domain}')으로 대체함 - 확인 필요"
        return display, warn

    return "UNKNOWN", "⚠ 회사명 추출 실패 - 수동 확인 필요"


# ── 날짜 추출 ─────────────────────────────────────────────────────
DATE_PATTERNS = [
    re.compile(r"(20\d{2})[-.](\d{1,2})[-.](\d{1,2})"),
    re.compile(r"(20\d{2})년\s*(\d{1,2})월\s*(\d{1,2})일"),
]
DATE_LABELS = ["일자", "날짜", "DATE", "Date"]


def extract_date(text: str) -> tuple[str, str]:
    matches = []
    for pat in DATE_PATTERNS:
        for m in pat.finditer(text):
            matches.append(m)
    if not matches:
        return "", "⚠ 날짜 추출 실패 - 수동 확인 필요"

    label_positions = []
    for label in DATE_LABELS:
        idx = text.find(label)
        if idx != -1:
            label_positions.append(idx)

    def score(m):
        if not label_positions:
            return m.start()
        return min(abs(m.start() - lp) for lp in label_positions)

    best = min(matches, key=score)
    y, mo, d = best.group(1), best.group(2), best.group(3)
    return f"{int(y):04d}{int(mo):02d}{int(d):02d}", ""


# ── 항목(품목) 추출 ───────────────────────────────────────────────
ITEM_HEADER_RE = re.compile(r"품\s*명|규\s*격|PART")
NO_HEADER_RE = re.compile(r"^(No\.?|순번|NO)$")
SUMMARY_KEYWORDS = ["합계", "공급가액", "부가세", "소계", "비고"]


def find_item_table(tables: list):
    """표 안의 모든 행을 훑어서 '품명/규격' 헤더 행을 찾는다.
    (안내문/공급자정보와 품목표가 하나의 표로 합쳐져 있는 양식이 많음)"""
    for table in tables:
        if not table:
            continue
        for header_idx, header in enumerate(table):
            for i, cell in enumerate(header):
                if cell and ITEM_HEADER_RE.search(str(cell)):
                    no_col = None
                    for j, hc in enumerate(header):
                        if hc and NO_HEADER_RE.match(normalize_cell(hc)):
                            no_col = j
                            break
                    return table, header_idx, i, no_col
    return None, None, None, None


def extract_items(tables: list) -> tuple[str, int, str]:
    table, header_idx, item_col, no_col = find_item_table(tables)
    if table is None:
        return "", 0, "⚠ 품목 테이블 인식 실패 - 수동 확인 필요"

    rows = table[header_idx + 1:]
    first_item = None
    count = 0

    if no_col is not None:
        seen_no = set()
        for row in rows:
            item_val = row[item_col] if item_col < len(row) else None
            no_val = row[no_col] if no_col < len(row) else None
            item_val = (item_val or "").strip()
            no_val = (no_val or "").strip()
            if no_val and item_val and no_val not in seen_no:
                seen_no.add(no_val)
                count += 1
                if first_item is None:
                    first_item = item_val
    else:
        for row in rows:
            item_val = row[item_col] if item_col < len(row) else None
            item_val = (item_val or "").strip()
            if not item_val:
                continue
            norm_item = normalize_cell(item_val)
            if any(kw in norm_item for kw in SUMMARY_KEYWORDS):
                continue  # "합계 (3건)" 같은 합계 줄은 품목이 아니므로 제외
            has_number = any(
                (c or "").strip().replace(",", "").replace(".", "").isdigit()
                for c in row if c
            )
            if has_number:
                count += 1
                if first_item is None:
                    first_item = item_val

    if first_item is None:
        return "", 0, "⚠ 품목 인식 실패 - 수동 확인 필요"
    return first_item, count, ""


# ── 파일명용 문자열 정리 ────────────────────────────────────────────
INVALID_CHARS_RE = re.compile(r'[\\/:*?"<>|]')


def clean_item_name(name: str, max_len: int = MAX_ITEM_LEN) -> str:
    name = re.sub(r"-GERBER\.zip$", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\.(zip|pdf|dwg)$", "", name, flags=re.IGNORECASE)
    name = name.replace("(", "_").replace(")", "_")
    name = INVALID_CHARS_RE.sub("_", name)
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    if len(name) > max_len:
        cut = name[:max_len]
        if "_" in cut:
            cut = cut.rsplit("_", 1)[0]
        name = cut
    return name


def clean_company_name(name: str) -> str:
    name = INVALID_CHARS_RE.sub("_", name)
    return re.sub(r"\s+", "", name)


# ── 파일명 조합 ───────────────────────────────────────────────────
def build_filename(doc_type: str, company: str, date: str, first_item: str, item_count: int) -> str:
    parts = [f"[{doc_type}]{clean_company_name(company)}"]
    if date:
        parts.append(date)
    parts.append(clean_item_name(first_item))
    name = "_".join(parts)
    if item_count > 1:
        name += f"_외_{item_count - 1}종"
    return name + ".pdf"


# ── 메인: 폴더 내 PDF 처리 ──────────────────────────────────────────
def process_folder(folder: Path, out_csv: Path):
    aliases = load_aliases()
    rows = []
    for pdf_path in sorted(folder.glob("*.pdf")):
        text, tables = read_pdf(pdf_path)
        doc_type, warn0 = detect_doc_type(text)
        company, warn1 = extract_company(text, tables, aliases)
        date, warn2 = extract_date(text)
        first_item, item_count, warn3 = extract_items(tables)
        proposed = build_filename(doc_type, company, date, first_item, item_count)
        warnings = "; ".join(w for w in [warn0, warn1, warn2, warn3] if w)
        rows.append({
            "원본파일명": pdf_path.name,
            "제안파일명": proposed,
            "문서종류": doc_type,
            "회사명": company,
            "날짜": date,
            "첫항목": first_item,
            "항목수": item_count,
            "경고": warnings,
        })

    with open(out_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [])
        writer.writeheader()
        writer.writerows(rows)

    return rows


def apply_from_csv(csv_path: Path, source_folder: Path, out_folder: Path | None):
    """rename_proposal.csv를 검토/수정한 뒤 이 함수로 실제 반영한다.
    out_folder를 지정하면 원본은 두고 새 이름으로 복사, 지정하지 않으면 원본 위치에서 바로 이름 변경."""
    import shutil

    with open(csv_path, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    used_names = set()
    dest_dir = out_folder or source_folder
    dest_dir.mkdir(parents=True, exist_ok=True)

    for row in rows:
        src = source_folder / row["원본파일명"]
        if not src.exists():
            print(f"⚠ 원본 파일을 찾을 수 없음: {src}")
            continue

        target_name = row["제안파일명"]
        stem, ext = target_name.rsplit(".", 1)
        candidate = target_name
        n = 1
        while candidate in used_names or (dest_dir / candidate).exists() and (dest_dir / candidate) != src:
            n += 1
            candidate = f"{stem}_{n}.{ext}"
        used_names.add(candidate)

        dst = dest_dir / candidate
        if out_folder:
            shutil.copy2(src, dst)
            print(f"복사: {src.name} -> {dst.name}")
        else:
            src.rename(dst)
            print(f"이름변경: {src.name} -> {dst.name}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="견적서/거래명세서/세금계산서 PDF 자동 리네이밍 도구")
    parser.add_argument("folder", help="PDF들이 있는 폴더")
    parser.add_argument("--csv", default=None, help="제안 목록 CSV 경로 (기본: <folder>/rename_proposal.csv)")
    parser.add_argument("--apply", action="store_true", help="CSV를 검토/수정한 뒤 실제로 파일명을 반영")
    parser.add_argument("--out", default=None, help="--apply 시 결과를 복사할 폴더 (지정 안 하면 원본 이름을 바로 변경)")
    args = parser.parse_args()

    folder = Path(args.folder)
    out_csv = Path(args.csv) if args.csv else folder / "rename_proposal.csv"

    if args.apply:
        apply_from_csv(out_csv, folder, Path(args.out) if args.out else None)
    else:
        results = process_folder(folder, out_csv)
        for r in results:
            print(f"{r['원본파일명']}\n  -> {r['제안파일명']}")
            if r["경고"]:
                print(f"  {r['경고']}")
        print(f"\n검토용 CSV 저장됨: {out_csv}")
        print("CSV의 '제안파일명' 열을 필요시 직접 수정한 뒤,")
        print(f"  python quote_renamer.py \"{folder}\" --apply")
        print("를 실행하면 실제로 파일명이 반영됩니다. (--out 폴더 로 지정 시 원본은 보존하고 새 폴더에 복사)")
