@echo off
if not exist venv (
    echo 먼저 setup.bat 을 실행해서 설치를 완료해주세요.
    pause
    exit /b 1
)
call venv\Scripts\activate.bat
python app.py
if errorlevel 1 pause
