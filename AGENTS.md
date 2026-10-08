# AGENTS.md

## Project
ESP32-S3 Vision Hub: local camera feed ingest over USB NCM, YOLO detection, JSONL append log, Ollama timeline interrogation, and web UI.

## Structure
- `crates/hubd`: axum server & orchestration.
- `crates/vision`: MJPEG reader & frame queue.
- `crates/detect`: ONNX YOLO inference & temporal debounce.
- `crates/store`: JSONL persistence & daily aggregation.
- `ui`: Static UI frontend.
- `firmware`: ESP-IDF v5.3+ NCM + camera firmware.

## Permissions & Rules
- Allowed: modifying files inside repo, executing cargo and test commands.
- Prohibited: unrequested dependencies, heavy abstractions, unverified completion claims.
