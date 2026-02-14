#!/bin/bash
# Django 개발 서버 실행
cd "$(dirname "$0")"
source venv/bin/activate
set -a
source .env
set +a
exec python manage.py runserver 0.0.0.0:8001
