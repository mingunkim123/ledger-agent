#!/bin/bash
# ROS2 플러그인 충돌 방지 — PYTHONDONTWRITEBYTECODE + PYTHONPATH 격리
cd "$(dirname "$0")"
source venv/bin/activate
set -a
source .env
set +a

# ROS2의 launch_testing 플러그인이 pytest와 충돌하므로
# PYTHONPATH에서 ROS2 경로를 제거하고 실행
CLEAN_PATH=""
IFS=':' read -ra PARTS <<< "$PYTHONPATH"
for p in "${PARTS[@]}"; do
    if [[ "$p" != */opt/ros/* ]] && [[ "$p" != */ros2/* ]]; then
        if [ -z "$CLEAN_PATH" ]; then
            CLEAN_PATH="$p"
        else
            CLEAN_PATH="$CLEAN_PATH:$p"
        fi
    fi
done

PYTHONPATH="$CLEAN_PATH" exec pytest "$@"
