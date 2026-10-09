# AGENTS.md

## Project
Pathfinder EYE (ESP32-S3 Vision Hub): Local camera feed ingest over USB NCM / UVC, decoupled asynchronous YOLOv11M detection, 3D facial biometric tracking, JSL & 21-joint skeletal hand gesture dictionary, append-only JSONL log, Ollama timeline interrogation, and responsive multi-theme web UI.

## Structure
- `crates/hubd`: Axum web server, live JPEG/telemetry streaming, API routing, and daemon orchestration.
- `crates/detect_service.py`: Decoupled multi-threaded camera ingest, YOLOv11M background inference, YuNet 3D face tracking, and MediaPipe hand gesture pipeline.
- `crates/face_service.py`: YuNet face detection & SFace 128-d biometric enrollment registry.
- `crates/hand_detector.py`: MediaPipe 21-landmark neural hand geometry & Japanese Sign Language (JSL) gesture classifier.
- `crates/vision`: MJPEG reader & frame boundary extraction.
- `crates/detect`: ONNX YOLO inference & temporal debounce filtering.
- `crates/store`: JSONL persistence & daily aggregation.
- `ui`: Hardware-accelerated frontend with theme synchronization, 3D face mesh wiring, and live gesture telemetry.
- `firmware`: ESP-IDF v5.3+ NCM + camera firmware.

## Permissions & Rules
- Allowed: modifying files inside repo, executing cargo and test commands.
- Prohibited: unrequested dependencies, heavy abstractions, unverified completion claims, editing files outside repository.
