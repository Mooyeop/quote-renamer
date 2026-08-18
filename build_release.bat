@echo off
if not exist venv (
    echo 먼저 setup.bat 을 실행해서 개발용 가상환경을 만들어주세요.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

where pyinstaller >nul 2>nul
if errorlevel 1 (
    echo pyinstaller 설치 중...
    pip install pyinstaller
)

echo.
echo === exe 빌드 중 (몇 분 걸릴 수 있음) ===
pyinstaller --onefile --windowed --icon icon.ico --name "견적서리네이머" --distpath dist --workpath build --specpath . app.py
if errorlevel 1 (
    echo [오류] 빌드 실패
    pause
    exit /b 1
)

if not exist release mkdir release
if not exist release\tesseract\tessdata mkdir release\tesseract\tessdata

copy /Y "dist\견적서리네이머.exe" release\ >nul

if exist company_aliases.local.json (
    echo company_aliases.local.json 발견 - 실제 거래처 매핑을 배포판에 담습니다.
    copy /Y company_aliases.local.json "release\company_aliases.json" >nul
) else (
    echo company_aliases.local.json 이 없어 예시용 company_aliases.json 을 담습니다.
    copy /Y company_aliases.json release\ >nul
)

set TESS_DIR=C:\Program Files\Tesseract-OCR
if not exist "%TESS_DIR%\tesseract.exe" (
    echo.
    echo [경고] "%TESS_DIR%" 에서 Tesseract를 찾지 못해 release\tesseract 를 채우지 못했습니다.
    echo         이 PC에 Tesseract-OCR이 설치되어 있어야 배포판에 OCR 엔진을 담을 수 있습니다.
    echo         exe와 company_aliases.json 은 정상적으로 release 폴더에 준비되었습니다.
    pause
    exit /b 0
)

copy /Y "%TESS_DIR%\tesseract.exe" release\tesseract\ >nul
copy /Y "%TESS_DIR%\*.dll" release\tesseract\ >nul
copy /Y "%TESS_DIR%\tessdata\eng.traineddata" release\tesseract\tessdata\ >nul
copy /Y "%TESS_DIR%\tessdata\kor.traineddata" release\tesseract\tessdata\ >nul

echo.
echo === 완료! ===
echo release 폴더가 준비됐습니다.
echo 이어서 build_installer.bat 을 실행하면 이 폴더로 설치 프로그램(exe)을 만듭니다.
pause
