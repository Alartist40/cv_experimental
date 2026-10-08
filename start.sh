#!/usr/bin/env bash
set -e
cd /home/xander/Documents/portfolio/Vision

# Ensure clean ports
fuser -k 8085/tcp 2>/dev/null || true
pkill -f "detect_service.py" 2>/dev/null || true
pkill -f "target/release/hubd" 2>/dev/null || true
pkill -f "target/debug/hubd" 2>/dev/null || true
sleep 1

# Start unified hubd
if [ -f "./target/release/hubd" ]; then
    exec ./target/release/hubd
else
    exec ./target/debug/hubd
fi
