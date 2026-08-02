#!/bin/bash
set -e
if [ ! -d venv ]; then
    echo "먼저 ./setup.sh 를 실행해서 설치를 완료해주세요."
    exit 1
fi
source venv/bin/activate
python app.py
