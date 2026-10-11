import os
os.environ["OMP_NUM_THREADS"] = "2"
os.environ["MKL_NUM_THREADS"] = "2"
os.environ["OPENBLAS_NUM_THREADS"] = "2"
os.environ["VECLIB_MAXIMUM_THREADS"] = "2"
os.environ["NUMEXPR_NUM_THREADS"] = "2"

import cv2
cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_ERROR)
import numpy as np
import json
import time
import torch
from datetime import datetime
from ultralytics import YOLO

torch.set_num_threads(2)
import sys
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

# Load models once at startup for instant, zero-allocation per-frame tracking
model = YOLO("models/yolo11m.onnx", task="detect")

from crates.face_service import get_face_models
from crates.hand_detector import detect_hand_gesture

face_det, _ = get_face_models(640, 480)
face_det.setInputSize((640, 480))

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Asynchronous YOLO inference state (keeps video feed silky smooth 30+ FPS)
import threading
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import supervision as sv

tracker = sv.ByteTrack(track_activation_threshold=0.35, lost_track_buffer=30, minimum_matching_threshold=0.7)

yolo_lock = threading.Lock()
yolo_frame_to_process = None
yolo_last_results = []
yolo_last_latency = 0.0
yolo_running = True

def yolo_worker():
    global yolo_last_results, yolo_last_latency, yolo_frame_to_process
    while yolo_running:
        frame_copy = None
        with yolo_lock:
            if yolo_frame_to_process is not None:
                frame_copy = yolo_frame_to_process.copy()
                yolo_frame_to_process = None  # Reset so we don't re-infer identical frames
        if frame_copy is not None:
            t0 = time.time()
            try:
                results = model(frame_copy, verbose=False, conf=0.45)
                raw_boxes = []
                raw_confs = []
                raw_cids = []
                raw_names = []

                for r in results:
                    for box in r.boxes:
                        cid = int(box.cls[0])
                        cname = model.names[cid]
                        cconf = float(box.conf[0])
                        xyxy = [float(v) for v in box.xyxy[0].tolist()]
                        raw_boxes.append(xyxy)
                        raw_confs.append(cconf)
                        raw_cids.append(cid)
                        raw_names.append(cname)

                det_list = []
                if raw_boxes:
                    sv_dets = sv.Detections(
                        xyxy=np.array(raw_boxes, dtype=np.float32),
                        confidence=np.array(raw_confs, dtype=np.float32),
                        class_id=np.array(raw_cids, dtype=int),
                        data={"class_name": np.array(raw_names)}
                    )
                    tracked_dets = tracker.update_with_detections(sv_dets)

                    if len(tracked_dets) > 0:
                        for xy, conf, cid, tid in zip(tracked_dets.xyxy, tracked_dets.confidence, tracked_dets.class_id, tracked_dets.tracker_id):
                            cname = model.names.get(int(cid), "object")
                            x1, y1, x2, y2 = [int(v) for v in xy]
                            det_list.append({
                                "track_id": int(tid) if tid is not None else None,
                                "class": cname,
                                "confidence": round(float(conf), 2),
                                "box": [x1, y1, x2, y2]
                            })
                    else:
                        # Fallback to untracked detections if tracks are still initializing
                        for xy, conf, cid, cname in zip(raw_boxes, raw_confs, raw_cids, raw_names):
                            x1, y1, x2, y2 = [int(v) for v in xy]
                            det_list.append({
                                "track_id": None,
                                "class": cname,
                                "confidence": round(float(conf), 2),
                                "box": [x1, y1, x2, y2]
                            })
                else:
                    # Update tracker with empty detections to maintain track state
                    tracker.update_with_detections(sv.Detections.empty())

                with yolo_lock:
                    yolo_last_results = det_list
                    yolo_last_latency = round((time.time() - t0) * 1000, 1)
            except Exception:
                pass
            time.sleep(0.06)  # Paced cooling delay prevents 100% continuous CPU burn
        else:
            time.sleep(0.05)

yolo_thread = threading.Thread(target=yolo_worker, daemon=True)
yolo_thread.start()

last_log_time = 0
last_frame_write = 0
frame_count = 0
last_detections = []
last_latency = 0.0
last_gesture = None
last_gesture_time = 0.0
last_mode_read_time = 0.0
current_mode = "OBJECT_DETECT"

# Target frame interval: ~30-33 FPS (fluid, responsive video ingest)
TARGET_INTERVAL = 0.030

while True:
    try:
        t_start = time.time()
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.05)
            continue

        frame_count += 1
        now = time.time()

        # Check operating mode from data/current_mode.txt every 0.5s
        if now - last_mode_read_time > 0.5:
            last_mode_read_time = now
            if os.path.exists("data/current_mode.txt"):
                try:
                    with open("data/current_mode.txt", "r") as mf:
                        current_mode = mf.read().strip().upper()
                except Exception:
                    pass
            else:
                current_mode = "OBJECT_DETECT"

        # Read active lighting filter / exposure bias setting from data/lighting_filter.txt
        lighting_mode = "NORMAL"
        if os.path.exists("data/lighting_filter.txt"):
            try:
                with open("data/lighting_filter.txt", "r") as lf:
                    lighting_mode = lf.read().strip().upper()
            except Exception:
                pass

        # Manual / Adaptive Optical Lighting Normalization
        proc_frame = frame
        if lighting_mode == "TOO_BRIGHT":
            # Darken overexposed / blown out lighting with high gamma reduction and contrast compress
            inv_gamma = 1.6
            lut = np.array([((i / 255.0) ** inv_gamma) * 230 for i in range(256)]).astype('uint8')
            proc_frame = cv2.LUT(frame, lut)
        elif lighting_mode == "TOO_DARK":
            # Brighten dark / dim lighting with boost curve
            inv_gamma = 0.55
            lut = np.array([((i / 255.0) ** inv_gamma) * 255 for i in range(256)]).astype('uint8')
            proc_frame = cv2.LUT(frame, lut)
        elif lighting_mode == "AUTO":
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            mean_lum = np.mean(gray) / 255.0
            if mean_lum > 0.05:
                gamma = float(np.clip(np.log(0.5) / np.log(mean_lum + 1e-6), 0.45, 2.2))
                inv_gamma = 1.0 / gamma
                lut = np.array([((i / 255.0) ** inv_gamma) * 255 for i in range(256)]).astype('uint8')
                proc_frame = cv2.LUT(frame, lut)
        elif lighting_mode == "CLAHE":
            clahe = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8, 8))
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            lab[:, :, 0] = clahe.apply(lab[:, :, 0])
            proc_frame = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

        # Write JPEG for browser feed at a fluid 30 FPS rate
        if now - last_frame_write >= 0.033:
            last_frame_write = now
            ret_jpg, jpeg = cv2.imencode(".jpg", proc_frame, [cv2.IMWRITE_JPEG_QUALITY, 72])
            if ret_jpg:
                with open("data/live_frame.jpg", "wb") as f:
                    f.write(jpeg.tobytes())

        frame = proc_frame

        detections = []
        person_box = None
        active_gesture_out = None
        face_scan_result = None

        # =========================================================================
        # TASK ISOLATION: Run ONLY the model selected by the user to save RAM & CPU
        # =========================================================================

        if current_mode == "OBJECT_DETECT":
            # Mode 1: Real-time Decoupled YOLO (Camera streams at full 30 FPS, worker infers async)
            with yolo_lock:
                yolo_frame_to_process = frame
                detections = list(yolo_last_results)
                last_latency = yolo_last_latency or 18.0

        elif current_mode in ("HAND_GESTURE", "INTERACTIVE_3D"):
            # Hand Pose CV: runs 21-joint tracking (YOLO paused, low compute)
            t0 = time.time()
            try:
                current_g = detect_hand_gesture(frame, None)
                if current_g:
                    last_gesture = current_g
                    last_gesture_time = time.time()
                    active_gesture_out = current_g
                else:
                    active_gesture_out = None
                    last_gesture = None
            except Exception:
                active_gesture_out = None
                last_gesture = None

            last_latency = round((time.time() - t0) * 1000, 1)

        elif current_mode == "FACE_BIOMETRIC":
            # Mode 2: Biometric Face Tracking (Tracks face bounding box and facial points in real-time)
            t0 = time.time()
            try:
                _, faces = face_det.detect(frame)
                if faces is not None and len(faces) > 0:
                    f = faces[0]
                    fx, fy, fw, fh = [int(v) for v in f[:4]]
                    # 5 facial landmarks (right_eye, left_eye, nose_tip, right_mouth, left_mouth)
                    pts = [[int(f[4 + 2*i]), int(f[5 + 2*i])] for i in range(5)]
                    face_scan_result = {
                        "box": [fx, fy, fw, fh],
                        "landmarks": pts,
                        "score": round(float(f[14]), 2)
                    }
            except Exception:
                pass
            last_latency = round((time.time() - t0) * 1000, 1)

        telemetry = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "latency_ms": last_latency,
            "mode": current_mode,
            "detections": detections,
            "gesture": active_gesture_out,
            "face": face_scan_result
        }

        tmp_file = "data/live_detections.json.tmp"
        with open(tmp_file, "w") as f:
            json.dump(telemetry, f)
        os.replace(tmp_file, "data/live_detections.json")

        # Log daily events every 3s if detections are present
        if detections and (now - last_log_time > 3.0):
            last_log_time = now
            date_str = datetime.now().strftime("%Y-%m-%d")
            time_str = datetime.now().strftime("%H:%M:%S")
            iso_str = datetime.now().isoformat()
            for det in detections:
                evt = {
                    "ts": iso_str,
                    "cls": det["class"],
                    "conf": det["confidence"],
                    "frames": 10,
                    "first": time_str,
                    "last": time_str,
                    "zone": "center"
                }
                with open(f"data/detections/{date_str}.jsonl", "a") as f:
                    f.write(json.dumps(evt) + "\n")

        # Sleep remaining time to guarantee low CPU temperature
        elapsed = time.time() - t_start
        if elapsed < TARGET_INTERVAL:
            time.sleep(TARGET_INTERVAL - elapsed)

    except Exception as e:
        time.sleep(0.05)

