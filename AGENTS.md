# AGENTS.md

## Project
Pathfinder EYE (ESP32-S3 Vision Hub): Pure, specialized edge Computer Vision (CV) system with zero external cloud/LLM dependencies. Features local camera feed ingest over USB NCM / UVC, high-performance binary WebSocket streaming, decoupled asynchronous YOLOv11M detection with tactical decaying trajectory ribbons and lead velocity vectors, 3D facial biometric tracking with dynamic holographic visor HUD and biometric vault auto-profile switching / red-alert quarantine, Japanese Sign Language (JSL) & 21-joint skeletal hand gesture dictionary with continuous visual sentence ribbon buffer, touchless interactive 3D WebGL CAD viewer (turbofan, robotic arm, planetary gearbox, drone) with pinch zoom, holographic hand depth occlusion, inspection shaders (Thermal Stress / X-Ray Wireframe), zero-asset Web Audio procedural sound FX, 45,000 GPU particle galaxy flow, Avian perimeter defense radar, live expressive cute robot avatar emotion mimicry, append-only JSONL log, and responsive multi-theme web UI.

## Structure
- `crates/hubd`: Axum web server, binary WebSocket stream (`/ws/stream`) & HTTP JPEG/telemetry streaming, API routing, and daemon orchestration.
- `crates/detect_service.py`: Decoupled multi-threaded camera ingest, YOLOv11M background inference, YuNet 3D face tracking, and MediaPipe hand gesture pipeline.
- `crates/face_service.py`: YuNet face detection & SFace 128-d biometric enrollment registry.
- `crates/hand_detector.py`: MediaPipe 21-landmark neural hand geometry & Japanese Sign Language (JSL) gesture classifier.
- `crates/jsl_service.py`: Japanese Sign Language (JSL) dataset recorder, geometric prototype training engine, and class registry.
- `crates/vision`: MJPEG reader & frame boundary extraction.
- `crates/detect`: ONNX YOLO inference & temporal debounce filtering.
- `crates/store`: JSONL persistence & daily aggregation.
- `ui`: Hardware-accelerated frontend with theme synchronization, 3D face mesh wiring, interactive CAD models with inspection shaders and depth occlusion, procedural cyber audio, continuous JSL sentence buffer, tactical trajectories, GPU particle flow, and live expressive avatar puppeteering.
- `firmware`: ESP-IDF v5.3+ NCM + camera firmware.

## Permissions & Rules
- Allowed: modifying files inside repo, executing cargo and test commands.
- Prohibited: unrequested dependencies, heavy abstractions, unverified completion claims, editing files outside repository.
