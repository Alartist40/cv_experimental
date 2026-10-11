# Changelog

All notable changes to the Vision Hub project are documented in this file.

## [Interactive 3D Holographic CAD Viewport & Touchless Control] - 2026-10-11

### Added
- **Touchless 3D Holographic CAD Viewer (`ui/index.html`)**:
  - Implemented real-time Three.js WebGL viewport featuring an explodable multi-component turbofan jet engine (central shaft, compressor discs, turbofan blades, outer nacelle cowlings, exhaust cone).
  - Direct hand motion tracking: Natural orbital rotation mapping (`threeTargetRotY`, `threeTargetRotX`) with horizontal coordinate mirror inversion for intuitive webcam manipulation.
  - Exploded view disassembly: Continuous extension factor calculation mapping closed fist to compacted (`0%`) and open palm to fully exploded (`100%`) component disassembly along component axes.
  - Scale & zoom: Two-hand distance tracking scaling the 3D model dynamically from 0.5x to 2.5x.
  - Dual-pipeline resilience: Seamless telemetry synchronization between client-side WebAssembly MediaPipe Hands and backend Python MediaPipe ONNX inference with timestamp decay clearing to prevent phantom skeleton latching.

### Changed & Calibrated
- **Hand Detector Threshold Calibration (`crates/hand_detector.py`)**:
  - Calibrated palm detector score threshold to `0.45` and hand pose confidence to `0.38` for responsive hand capture across wide webcam angles while rejecting torso and background curtain contours.

## [Pathfinder EYE & Japanese Sign Language] - 2026-10-09

### Added
- **Rebranding & UX Overhaul**: Rebranded system to **Pathfinder EYE** (`PATHFINDER // EYE`).
- **Telemetry Stabilization**: Replaced dynamic-width latency and FPS badge layouts with fixed-width containers and `tabular-nums` formatting to completely eliminate navigation bar jitter.
- **Concise Navigation Switcher**: Shortened navigation tabs to `OBJECT_RECOGNITION`, `FACIAL_RECOGNITION`, `HAND_GESTURES`, and `INTERACTIVE_3D`.
- **Standby Placeholder**: Updated hand gesture canvas standby placeholder from peace/palm hint to clean `PRESENT HANDS`.
- **Dynamic JSL & Universal Gesture Dictionary**: Added real-time 12-gesture menu in right sidebar highlighting active gestures (✌️ Peace/2, 🖐️ Palm/5, ☝️ Pointing/1, 🤟 Three/3, 🖖 Four/4, 👍 Thumbs Up, 👌 OK/Money, 🦊 Kitsune/Fox, 🤙 Pinky Promise, 🤙 Call Me, 🤘 Rock, ✊ Fist/0).
- **Decoupled 30 FPS Stream Pipeline**: Camera ingest loop decoupled from YOLOv11M background inference worker with atomic file writes preventing race conditions.
- **Mazzaroth Multi-Theme Engine**: 4 design themes (Midnight Gold, Synth Magenta, Obsidian Mono, Technical Paper) with full canvas and HUD synchronization.
- **3D Biometric Facial Reticle**: 468-point head tracking mesh following user movement with live pitch/yaw telemetry.

### Added
- **Deep Wireframe Matrix HUD (`ui/index.html`)**:
  - Implemented multi-layered 2D optical bounding frames with cyan outer edges, magenta/amber nested sub-boxes, and corner alignment brackets matching radar matrix aesthetics.
  - Implemented dynamic object classification and confidence pill badges (`PERSON 94%`) with automated canvas edge clamping.
  - Added procedural `+` and `*` targeting reticle glyphs at perimeter anchors with zero CPU overhead.
  - Added animated, rolling Arch Linux / Cyber Matrix kernel log stream directly embedded into the top-left HUD corner.
  - Clean non-colliding coordinate indicators (`XY:[x,y]` and `DIM:WxH`).
- **Project Documentation**:
  - Created root `README.md` documenting architecture, components, and startup procedure.
  - Created `CHANGELOG.md` logging all developmental milestones and performance breakthroughs.

### Changed & Optimized
- **Major Thermal & CPU Optimization (`crates/detect_service.py`)**:
  - Clamped ONNX Runtime and PyTorch global thread pools (`ort.set_global_thread_pool_sizes(2, 1)`, `torch.set_num_threads(2)`), eliminating multi-core thread spin. CPU usage dropped from >1100% to under 20%.
  - Completely removed OpenCV `ORB_create()` keypoint gradient extraction and grayscale loops, eliminating memory thrashing and CPU bottlenecks.
  - Throttled disk file I/O by rate-limiting live JPEG writes to 15 FPS with quality compression.
  - Set target loop pacing to 15-18 FPS, keeping laptops quiet and cool.
- **UI Simplification**:
  - Removed obsolete bottom timeline event stream table to streamline focus on live video feed.
  - Removed style switcher buttons; unified layout around the Deep Wireframe Matrix aesthetic.

### Fixed
- Fixed text overlapping and coordinate collisions on target boxes.
- Fixed 3D wireframe distortion by shifting to crisp, lightweight 2D isometric-free frames.

## [Facial Recognition & Authority Matrix] - 2026-10-07

### Added
- **YuNet & SFace Biometric Pipeline (`crates/face_service.py`)**:
  - Integrated OpenCV Zoo's lightweight `YuNet` (228 KB) face detector and `SFace` (37 MB) 128-dimensional embedding extractor.
  - Built JSON-backed facial embedding database (`data/faces/database.json`) storing biometric vectors, roles, and security clearance levels.
  - Added CLI operations: `scan`, `enroll`, `list`, `delete`.
- **Axum API Integration (`crates/hubd`)**:
  - Added `/api/face/scan`: Performs on-demand biometric vector match against current frame.
  - Added `/api/face/enroll`: Extracts face from current frame and stores in authority registry.
  - Added `/api/face/list`: Retrieves registered subjects with roles and clearance.
  - Added `/api/face/delete`: Revokes authorization and deletes biometric vector.
- **Cybernetic Authority UI (`ui/index.html`)**:
  - Added dedicated **Facial Recognition & Authority Matrix** console under the AI chat card.
  - Interactive "SCAN & VERIFY" button that scans on demand with zero continuous CPU overhead.
  - "Capture Current Frame & Enroll" form to register new entities with custom roles (`COMMANDER`, `OPERATOR`, `VIP`, `GUEST`) and clearance (`LEVEL-3` to `LEVEL-5`).
  - Active biometric HUD target brackets (green `ACCESS GRANTED` vs red `UNAUTHORIZED SUBJECT`).

## [Cyber Hand Gesture Control Console] - 2026-10-07

### Added
- **Optical Hand Gesture Module (`crates/hand_detector.py`)**:
  - Implemented high-speed YCrCb skin segmentation with convexity defect finger valley analysis.
  - Recognizes `peace` (✌️ index + middle extended) and `palm` (🖐️ 5-finger spread).
- **Internal Action Execution (`ui/index.html` & `crates/detect_service.py`)**:
  - `peace` (✌️): Hands-free biometric trigger (initiates Facial Recognition and Authority scan automatically).
  - `palm` (🖐️): Toggles computer vision (CV) bounding tracking overlay on/off inside the viewport.
  - Debounce timer (2.5 seconds) prevents accidental double-triggers.
  - Zero system-level commands executed; all actions are kept strictly inside the application.
- **On-Demand Arm/Disarm Console (`ui/index.html`)**:
  - Dedicated Cyber Hand Gesture card with active LED status and one-click ARM / DISARM toggle.
  - Consumes 0% extra CPU when disarmed.
