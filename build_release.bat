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
pyinstaller --onefile --windowed --name "견적서리네이머" --distpath dist --workpath build --specpath . app.py
if errorlevel 1 (
    echo [오류] 빌드 실패
    pause
    exit /b 1
)

if not exist release mkdir release
if not exist release\tesseract\tessdata mkdir release\tesseract\tessdata

copy /Y "dist\견적서리네이머.exe" release\ >nul
copy /Y company_aliases.json release\ >nul

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
echo release 폴더를 통째로 압축(zip)해서 나눠주면, 받는 사람은 압축만 풀고
echo 견적서리네이머.exe 를 더블클릭하면 바로 실행됩니다 (Python/Tesseract 설치 불필요).
pause
