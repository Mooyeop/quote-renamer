# 견적서 PDF 자동 리네이밍 도구

[![Download latest release](https://img.shields.io/github/v/release/Mooyeop/quote-renamer?label=%E2%AC%87%EF%B8%8F%20Download&style=for-the-badge&color=4f46e5)](https://github.com/Mooyeop/quote-renamer/releases/latest)

> **그냥 쓰기만 하실 거라면 (일반 사용자)**
> 아래 설치 방법은 개발자용입니다. Python 설치 없이 바로 쓰려면
> 위 **Download** 배지를 누르거나 **[여기서 설치 파일 다운로드](https://github.com/Mooyeop/quote-renamer/releases/latest)**
> 하셔서 `견적서리네이머_설치.exe`를 실행하세요. 관리자 권한 없이 설치되고,
> 바탕화면/시작메뉴에 아이콘이 생겨서 다른 Windows 앱처럼 바로 실행할 수 있습니다.
>
> [이전 버전들은 여기서](https://github.com/Mooyeop/quote-renamer/releases) — 버전별로 계속 남아있으니 필요하면 옛날 버전도 받을 수 있습니다.
> 버전별로 뭐가 바뀌었는지는 **[CHANGELOG.md](CHANGELOG.md)**에서 볼 수 있습니다.

견적서 PDF를 읽어서 아래 규칙으로 파일명을 제안/변경합니다.

```
[견적서]회사이름_날짜_첫번째항목_외_N종.pdf
```
- 항목이 1개뿐이면 `_외_N종` 부분은 붙지 않습니다.
- 날짜는 `YYYYMMDD` (예: `20260731`) 형식입니다.

두 가지 방식으로 쓸 수 있습니다.
- **`app.py`** — 창을 띄워서 PDF를 드래그&드롭하면 미리보기 후 적용하는 데스크탑 앱 (추천)
- **`quote_renamer.py`** — 폴더 전체를 한 번에 처리하는 커맨드라인 도구 (CSV 검토 → 적용)

둘 다 같은 인식 로직(`quote_renamer.py`)을 공유하므로 결과는 동일합니다.

## 설치 (개발자용 — 코드를 고치거나 exe를 직접 빌드할 사람만)

**딱 이 두 가지만 하면 됩니다.**

1. `setup.bat` 더블클릭 (최초 1회)
2. `run.bat` 더블클릭 (그다음부터 실행할 때마다)

이게 끝입니다. 가상환경 생성, 패키지 설치 다 `setup.bat`이 알아서 처리합니다.

<details>
<summary>+@ 참고사항 (몰라도 정상적으로 동작합니다)</summary>

- 개발자들이 보통 그렇게 하듯, 이 프로젝트도 전역 파이썬을 건드리지 않고
  독립된 가상환경(venv)에 패키지를 설치합니다.
- Mac/Linux는 `setup.sh` / `run.sh` (최초 1회 `chmod +x setup.sh run.sh` 필요).
- 수동으로 하고 싶다면:
  ```bash
  python -m venv venv
  venv\Scripts\activate      # Mac/Linux는 source venv/bin/activate
  pip install -r requirements.txt
  ```
  (`pdfplumber`는 필수, `tkinterdnd2`는 데스크탑 앱의 드래그&드롭 기능에 필요,
  `pytesseract`는 스캔본 PDF 처리에 필요 — 없어도 각 기능만 빠질 뿐 나머지는 동작합니다.)
- Windows/Mac 표준 Python 설치본에는 `tkinter`가 기본 포함되어 있어 따로 설치할
  필요가 없습니다. (Linux에서 `ModuleNotFoundError: No module named 'tkinter'`가
  뜨면 `sudo apt install python3-tk`)
- 스캔본(이미지) PDF까지 처리하려면 시스템에 OCR 엔진도 필요합니다.
  ```bash
  # Ubuntu/Debian 예시. Windows는 tesseract 공식 설치 프로그램 사용.
  sudo apt-get install tesseract-ocr tesseract-ocr-kor poppler-utils
  ```

</details>

## 사용법 — 데스크탑 앱 (`app.py`)

```bash
python app.py
```
1. 창 상단의 드롭존에 견적서 PDF를 끌어다 놓거나, "+ 파일 선택" / "+ 폴더 전체 추가"로 넣습니다.
2. 표에 원본 파일명과 자동 제안된 파일명이 나타납니다. 이상하면 "제안 파일명" 칸을
   더블클릭해서 직접 고칠 수 있습니다.
3. 결과를 새 폴더에 복사할지, 원본 이름을 바로 바꿀지 라디오 버튼으로 고른 뒤
   "적용"을 누르면 실제로 반영됩니다.

## 사내 배포용 설치 프로그램 만들기 (다른 사람 PC에 Python/Tesseract 설치 없이 바로 실행)

두 단계입니다.

**1단계 — `build_release.bat`** 더블클릭 한 번으로:
- `app.py`를 PyInstaller로 exe 하나에 패키징 (아이콘 포함)
- `company_aliases.json` 복사 (`company_aliases.local.json`이 있으면 그걸 우선 사용 — 아래 "회사명 별칭 사전" 참고)
- 이 PC에 설치된 Tesseract-OCR(엔진 + 한국어/영어 언어팩)을 포터블 형태로 복사

해서 `release/` 폴더를 만들어줍니다. (사전에 `setup.bat`으로 개발용 venv가
준비되어 있어야 하고, OCR까지 배포하려면 이 PC에 Tesseract-OCR이 설치되어
있어야 합니다 — 설치 안내는 위 "스캔본 처리" 항목 참고.)

**2단계 — `build_installer.bat`** 더블클릭 한 번으로, `release/` 폴더를
정식 Windows 설치 프로그램(`installer_output/견적서리네이머_설치.exe`)으로
묶어줍니다. ([Inno Setup](https://jrsoftware.org/isdl.php) 필요 — 처음
한 번만 설치하면 됨)

받는 사람은 이 설치 파일 하나만 실행하면 됩니다:
- **관리자 권한 불필요** (현재 사용자 계정에만 설치 — 회사 PC 권한 제한과 무관하게 동작)
- 설치 중 바탕화면 + 시작메뉴에 아이콘 자동 생성 → 이후로는 다른 Windows 앱처럼 아이콘 더블클릭으로 실행
- 제어판(앱 및 기능)에 제거 항목도 자동으로 생김
- 이미 설치돼 있는 상태에서 새 버전 설치 파일을 실행하면 그 자리에서 업데이트됨
  (이때 `company_aliases.json`은 사용자가 직접 수정했을 수 있으니 덮어쓰지 않고 그대로 둡니다)

코드나 아이콘(`icon.ico`)을 고친 뒤에는 `build_release.bat` → `build_installer.bat`
순서로 다시 실행하면 최신 상태로 갱신됩니다.

<details>
<summary>설치 프로그램 없이 포터블 zip으로만 쓰고 싶다면</summary>

`build_release.bat`까지만 실행한 뒤 `release` 폴더를 탐색기에서 우클릭 →
"보내기 → 압축(ZIP) 폴더"(또는 PowerShell `Compress-Archive`)로 압축해서
나눠줘도 됩니다. 다른 압축 도구는 파일이 많고 큰 배치(tesseract dll 수십 개
포함)에서 간혹 손상된 zip을 만들 수 있으니 표준 도구를 쓰세요.

</details>

## 사용법 — 커맨드라인 (`quote_renamer.py`)

**1단계 — 미리보기 (dry-run)**
```bash
python quote_renamer.py "견적서_폴더"
```
`견적서_폴더/rename_proposal.csv` 에 원본파일명 / 제안파일명 / 회사명 / 날짜 /
첫항목 / 항목수 / 경고 목록이 저장됩니다. 엑셀로 열어서 확인하세요.

**2단계 — CSV 검토 및 필요시 수정**
`⚠` 경고가 붙은 행, 또는 결과가 이상해 보이는 행은 `제안파일명` 칸을 직접
고치면 됩니다. (예: 회사명 인식 실패, 품목명이 이상하게 잘린 경우 등)

**3단계 — 실제 반영**
```bash
# 원본 파일 이름을 그대로 바꾸고 싶을 때
python quote_renamer.py "견적서_폴더" --apply

# 원본은 보존하고 새 폴더에 복사본만 만들고 싶을 때 (권장)
python quote_renamer.py "견적서_폴더" --apply --out "리네임_결과"
```
같은 이름이 이미 있으면 `_2`, `_3` 을 붙여 덮어쓰지 않습니다.

## 회사명 별칭 사전 (`company_aliases.json`)

일부 견적서는 회사명이 로고 이미지로만 들어있어 텍스트로 추출되지 않거나
(예: 삼성전자 → 이메일 도메인 `samsung`으로 대체 인식), 축약 표기를
쓰고 싶은 경우(예: "주식회사 엘지전자" → "LG전자")가 있습니다.
이런 경우를 위한 사용자 편집용 매핑 파일입니다.

```json
{
  "로보티즈": "로보티즈",
  "삼성전자": "삼성전자",
  "LG전자": "LG전자",
  "samsung": "삼성전자"
}
```
새 거래처를 만나서 회사명이 이상하게 나오면, 이 파일에 `"원본에서 뽑힌 이름": "원하는 표기"`
한 줄만 추가하면 다음부터 자동으로 적용됩니다.

