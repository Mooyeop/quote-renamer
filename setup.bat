@echo off
echo === 견적서 리네이머 - 최초 설치 ===
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [오류] 파이썬이 설치되어 있지 않거나 PATH에 등록되지 않았습니다.
    echo https://www.python.org/downloads/ 에서 설치 후, "Add python.exe to PATH"를 체크해주세요.
    pause
    exit /b 1
)

if not exist venv (
    echo 가상환경 생성 중...
    python -m venv venv
)

echo 가상환경 활성화 및 패키지 설치 중...
call venv\Scripts\activate.bat
pip install -r requirements.txt

echo.
echo === 설치 완료! 이제부터는 run.bat 을 더블클릭해서 실행하세요 ===
pause
