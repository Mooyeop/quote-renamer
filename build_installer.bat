@echo off
if not exist release\견적서리네이머.exe (
    echo 먼저 build_release.bat 을 실행해서 release 폴더부터 준비해주세요.
    pause
    exit /b 1
)

set ISCC="%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %ISCC% (
    echo [오류] Inno Setup이 설치되어 있지 않습니다.
    echo https://jrsoftware.org/isdl.php 에서 설치 후 다시 실행해주세요.
    pause
    exit /b 1
)

echo.
echo === 설치 프로그램 빌드 중 ===
%ISCC% installer.iss
if errorlevel 1 (
    echo [오류] 설치 프로그램 빌드 실패
    pause
    exit /b 1
)

echo.
echo === 완료! ===
echo installer_output\견적서리네이머_설치.exe 를 나눠주면, 받는 사람은 실행만 하면
echo 관리자 권한 없이 설치되고 바탕화면/시작메뉴에 바로가기가 자동으로 생깁니다.
pause
