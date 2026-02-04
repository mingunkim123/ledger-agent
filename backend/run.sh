#!/bin/bash
# 실제 기기에서 접속하려면 --host 0.0.0.0 필요 (errno=103 방지)
cd "$(dirname "$0")"
set -a
# .env 값을 환경변수로 로드 (python-dotenv 미설치 시에도 적용)
source .env
set +a
exec uvicorn app.main:app --reload --port 8001 --host 0.0.0.0
