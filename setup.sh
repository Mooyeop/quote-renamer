#!/bin/bash
set -e
echo "=== 견적서 리네이머 - 최초 설치 ==="

if ! command -v python3 &> /dev/null; then
    echo "[오류] python3가 설치되어 있지 않습니다."
    echo "Mac: brew install python  /  Ubuntu: sudo apt install python3 python3-venv python3-tk"
    exit 1
fi

if [ ! -d venv ]; then
    echo "가상환경 생성 중..."
    python3 -m venv venv
fi

echo "가상환경 활성화 및 패키지 설치 중..."
source venv/bin/activate
pip install -r requirements.txt

echo ""
echo "=== 설치 완료! 이제부터는 ./run.sh 로 실행하세요 ==="
