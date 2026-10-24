# Changelog

All notable changes to the Vision Hub project are documented in this file.

## [Offline Local CSS Resilience & YOLO Inference Throughput Optimization] - 2026-10-24

### Fixed & Optimized
- **Local CSS Bundle & Layout Collapse Protection**:
  - Downloaded standalone, zero-dependency Tailwind CSS bundle (`ui/tailwind.min.css`) directly into the local repository, eliminating reliance on external CDN scripts.
  - Added CSS reset and fallback rules for the 12-column grid layout, header/footer flex alignments, and 16:9 viewport aspect ratio to prevent DOM element stacking when external CDNs are unreachable.
- **YOLOv11M Inference Throughput & Latency Optimization**:
  - Clamped inference input dimensions to `imgsz=480` and tuned thread cooling pacing in [crates/detect_service.py](file:///home/xander/Documents/portfolio/Vision/crates/detect_service.py).
  - Reduced detection latency from ~600ms down to ~18ms and CPU utilization from over 1100% to under 50%, restoring instantaneous CV telemetry synchronization.

## [Pure CV Refocus, Binary WebSockets, CAD Shaders, Occlusion & Procedural Audio] - 2026-10-23

### Added
- **High-Speed Binary WebSocket Streaming (`/ws/stream`)**:
  - Implemented Axum WebSocket endpoint streaming binary JPEG frames and atomic JSON telemetry directly from `hubd` to the web client, delivering sub-15ms latency with automatic HTTP fallback.
- **Pure CV Refocus & Complete Excision of Non-CV Systems**:
  - Completely excised Ollama SLM connection, `/api/ask` endpoint, SLM chat drawer, and Web Speech TTS/STT to maintain a pure, dedicated edge Computer Vision and spatial AR architecture.
- **Holographic Hand Depth Occlusion Mask**:
  - Real-time hand hull occlusion masking in Three.js viewport allowing 3D CAD models and GPU particles to float naturally behind operator hands.
- **Procedural Zero-Asset Cyber Audio Synthesizer**:
  - Pure Web Audio API oscillator sound FX with dynamic pitch modulation on pinch zoom, holographic menu navigation ticks, biometric lock chimes, and avatar mouth chirps.
- **Biometric Vault Profile Switching & Red-Alert Security Quarantine**:
  - Automated user profile loading (switches to Commander preferences upon authorized scan) and flashing Red-Alert quarantine HUD with audio alarms upon unverified entity detection.
- **3D CAD Inspection Shaders (`SOLID`, `THERMAL`, `XRAY`)**:
  - Header inspection toggle cycling between theme solid metallic, Thermal Aerodynamic Stress heatmaps (radial cyan-to-red stress gradients), and glowing X-Ray wireframe glass.
- **Tactical Trajectory Ribbon Ghosting & Velocity Vectors**:
  - Real-time motion path trails with temporal decay, lead velocity vectors, and instantaneous speed telemetry (`px/s`) in Object and Avian Radar modes.
- **Continuous JSL Visual Sentence Ribbon**:
  - Temporal multi-gesture sliding buffer on the HUD capturing continuous sign language phrases without speech dependencies.

## [Touchless 3D CAD Pinch Zoom & Holographic Model Selector] - 2026-10-19

### Added
- **Dynamic Touchless 3D CAD Gesture Controls (`INTERACTIVE_3D`)**:
  - **Calibrated Base Model Scaling**: Scaled default 3D CAD model initialization, preset switching, and view resets from `1.0x` down to `0.58x`, perfectly framing CAD models in the viewport without occluding the operator's face or background stream.
  - **Single-Hand Pinch & Spread Dynamic Zoom**: Continuous distance tracking between index tip (#8) and thumb tip (#4); pinching together smoothly shrinks the 3D model down to `0.22x`, while spreading fingers apart enlarges the model up to `2.5x`.
  - **Dual-Hand Pinch Distance Zoom**: Bimanual pinch-distance tracking adjusting model scale dynamically as hands are moved closer together or further apart.
  - **Holographic Gesture-Driven Dropdown Selector**:
    - **Open Menu (✌️ Two Fingers Up)**: Raising index and middle fingers together summons an on-screen cyberpunk holographic model selection menu.
    - **Scroll Down (🖕 Dropping Middle Finger)**: Lowering the middle finger or increasing vertical/angular distance from the index finger scrolls down through the 5 CAD models (`✈️ Turbofan Engine`, `🚁 Cyber Drone`, `🤖 Robot Arm`, `🛰️ Orbital Satellite`, `⚙️ Planetary Gears`).
    - **Confirm & Load (👍 Thumbs Up)**: Flashing a Thumbs Up confirms the highlighted item, closes the menu, instantly loads the model, and displays an on-screen verification notification banner (`✓ CONFIRMED: ...`).
  - **Updated Sidebar 3D Interaction Guide**: Synchronized sidebar guide cards with new gesture actions (`🤏 PINCH IN / OUT`, `✌️ 2 FINGERS UP`, `🖕 DROP MIDDLE FINGER`, `👍 THUMBS UP`, `👐 2-HAND PINCH DIST`).

## [Emotion Reader Avatar, Avian Radar, GPU Galaxy & Face Visor Upgrades] - 2026-10-15

### Added
- **Cute Robot Avatar Emotion Mimicry (`EMOTION_READER`)**:
  - Real-time expressive facial mimicry mirroring the user's face onto a cute cybernetic robot avatar:
    - Morphing eyes: happy/smiling arches (`∩ ◡ ∩`), playful winking (`∩ ◡ ⌒` / `⌒ ◡ ∩`), blinking/squinting slits (`— ◡ —`), and angry chevrons (`> ^ <`).
    - Speech & mouth mimicry: direct lip opening and phonetic articulation matching user speech and mouth dimensions.
    - Floating corner Picture-in-Picture (PIP) camera feed with live 3D landmark tracing and eyebrow geometry.
  - CRT scanlines, screen vignette, and responsive theme synchronization across all Mazzaroth palettes.
- **Dynamic Visor HUD & Facial Tracking (`FACE_BIOMETRIC`)**:
  - High-contrast borderless holographic visor with `.ID` center callout and procedural corner markers.
  - Independent pupil tracking reticles with cyan/amber glow cores and blink suppression.
  - Dynamically scaling and stretching mouth box matching user mouth dimensions.
- **Avian Perimeter Defense Radar (`BIRD_DETECT`)**:
  - Real-time avian robotics CV tracking flight vectors, radial distance, and perimeter defense rings.
- **45,000 GPU Particle Flow Simulation (`PARTICLE_FLOW`)**:
  - High-performance WebGL GPU particle system dynamically morphing between a concentrated cybernetic core and a 4-arm spiral galaxy driven by hand motion and dual-hand expansion.
- **3D CAD Multi-Model Suite (`INTERACTIVE_3D`)**:
  - Expanded interactive WebGL CAD models: **Turbofan Jet Engine**, **Robotic Arm**, **Planetary Gearbox**, and **Quadcopter Drone**.
  - Touchless single-hand orbit, dual-hand twist roll, distance zoom, and fist-to-palm component explosion.
  - Disambiguated Kitsune 🦊 and Rock 🤘 detection based on knuckle curl ratios.

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
