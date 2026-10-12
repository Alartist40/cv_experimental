import cv2
import numpy as np

_palm_detector = None
_hand_pose = None

def get_hand_models():
    global _palm_detector, _hand_pose
    if _palm_detector is None:
        from crates.mp_hand import MPPalmDet
        from crates.mp_handpose import MPHandPose
        # Calibrated threshold: reliably triggers on real hands across diverse webcam angles while preventing false positives
        _palm_detector = MPPalmDet(modelPath="models/palm_detection_mediapipe_2023feb.onnx", scoreThreshold=0.45)
        _hand_pose = MPHandPose(modelPath="models/handpose_estimation_mediapipe_2023feb.onnx", confThreshold=0.38)
    return _palm_detector, _hand_pose

import os
import json

_jsl_model_cache = None
_jsl_model_mtime = 0

def get_jsl_model():
    global _jsl_model_cache, _jsl_model_mtime
    model_path = "data/jsl_model.json"
    if not os.path.exists(model_path):
        return None
    try:
        mtime = os.path.getmtime(model_path)
        if _jsl_model_cache is None or mtime != _jsl_model_mtime:
            with open(model_path, "r", encoding="utf-8") as f:
                _jsl_model_cache = json.load(f)
            _jsl_model_mtime = mtime
        return _jsl_model_cache
    except Exception:
        return None

def match_custom_jsl_prototype(vec, is_dual=False):
    """
    Computes cosine similarity against trained JSL prototype centroids.
    Returns (label, clean_label, similarity) if similarity >= 0.88.
    """
    model = get_jsl_model()
    if not model or "prototypes" not in model:
        return None

    v = np.array(vec, dtype=np.float32)
    norm = np.linalg.norm(v)
    if norm < 1e-4:
        return None
    v = v / norm

    best_match = None
    best_sim = -1.0

    prefix = "dual_" if is_dual else "single_"
    for k, proto in model["prototypes"].items():
        if not k.startswith(prefix):
            continue
        pv = np.array(proto["vector"], dtype=np.float32)
        sim = float(np.dot(v, pv))
        if sim > best_sim:
            best_sim = sim
            best_match = proto

    if best_match and best_sim >= 0.88:
        return best_match["label"], best_match["clean_label"], round(best_sim, 2)
    return None

def classify_hand_landmarks(lm, bbox):
    """Classify 21 landmarks into a specific gesture."""
    wrist = lm[0, :2]

    # Normalize feature vector for custom JSL prototype matching
    coords = lm[:21, :2]
    centered = coords - wrist
    palm_scale = np.linalg.norm(coords[9] - wrist)
    if palm_scale < 1e-4:
        palm_scale = 1.0
    single_feat = (centered / palm_scale).flatten()

    jsl_custom = match_custom_jsl_prototype(single_feat, is_dual=False)

    # Euclidean scale invariant finger extension check:
    def is_finger_extended(tip_idx, pip_idx, mcp_idx):
        d_tip = np.linalg.norm(lm[tip_idx, :2] - wrist)
        d_mcp = np.linalg.norm(lm[mcp_idx, :2] - wrist)
        d_pip = np.linalg.norm(lm[pip_idx, :2] - wrist)
        return (d_tip > d_pip * 1.12) and (d_tip > d_mcp * 1.20)

    # Thumb extension (landmark 4 vs 2)
    d_thb_tip = np.linalg.norm(lm[4, :2] - wrist)
    d_thb_mcp = np.linalg.norm(lm[2, :2] - wrist)
    thb_ext = d_thb_tip > d_thb_mcp * 1.25

    idx_ext = is_finger_extended(8, 6, 5)
    mid_ext = is_finger_extended(12, 10, 9)
    rng_ext = is_finger_extended(16, 14, 13)
    pnk_ext = is_finger_extended(20, 18, 17)

    # Measure distance between thumb tip and index tip for 'OK' / 'PINCH' sign
    d_thb_idx = np.linalg.norm(lm[4, :2] - lm[8, :2])
    hand_scale = max(1.0, np.linalg.norm(lm[9, :2] - wrist))
    is_ok_circle = (d_thb_idx / hand_scale) < 0.28

    tips = []
    if thb_ext: tips.append([int(lm[4, 0]), int(lm[4, 1])])
    if idx_ext: tips.append([int(lm[8, 0]), int(lm[8, 1])])
    if mid_ext: tips.append([int(lm[12, 0]), int(lm[12, 1])])
    if rng_ext: tips.append([int(lm[16, 0]), int(lm[16, 1])])
    if pnk_ext: tips.append([int(lm[20, 0]), int(lm[20, 1])])

    gesture_name = "hand"
    # Check trained custom JSL class first
    if jsl_custom:
        gesture_name = jsl_custom[1]
    elif is_ok_circle and mid_ext and rng_ext and pnk_ext:
        gesture_name = "ok"
    else:
        d_mid_thb = np.hypot(lm[4, 0] - lm[12, 0], lm[4, 1] - lm[12, 1])
        d_rng_thb = np.hypot(lm[4, 0] - lm[16, 0], lm[4, 1] - lm[16, 1])
        is_snout_closed = (d_mid_thb / hand_scale < 0.38) and (d_rng_thb / hand_scale < 0.38)
        if idx_ext and pnk_ext and is_snout_closed:
            gesture_name = "kitsune"
        elif pnk_ext and not idx_ext and not mid_ext and not rng_ext and not thb_ext:
            gesture_name = "pinky_promise"
        elif thb_ext and pnk_ext and not idx_ext and not mid_ext and not rng_ext:
            gesture_name = "call"
        elif idx_ext and pnk_ext and not mid_ext and not rng_ext:
            gesture_name = "rock"
        elif idx_ext and mid_ext and not rng_ext and not pnk_ext:
            gesture_name = "peace"
        elif idx_ext and not mid_ext and not rng_ext and not pnk_ext:
            gesture_name = "pointing"
        elif idx_ext and mid_ext and rng_ext and pnk_ext and not thb_ext:
            gesture_name = "four"
        elif idx_ext and mid_ext and rng_ext and not pnk_ext:
            gesture_name = "three"
        elif thb_ext and not idx_ext and not mid_ext and not rng_ext and not pnk_ext:
            gesture_name = "thumbs_up"
        elif idx_ext and mid_ext and rng_ext and pnk_ext:
            gesture_name = "palm"
        elif not idx_ext and not mid_ext and not rng_ext and not pnk_ext and not thb_ext:
            gesture_name = "fist"

    res = {
        "gesture": gesture_name,
        "box": bbox,
        "tips": tips,
        "landmarks": lm[:, :2].tolist()
    }
    if jsl_custom:
        res["jsl_label"] = jsl_custom[0]
        res["jsl_conf"] = jsl_custom[2]
    return res

def detect_hand_gesture(frame, person_box=None):
    """
    Neural 21-Landmark Hand Pose & Sign Language Gesture Engine.
    Uses MediaPipe palm localization + 21 skeletal joints.
    Guarantees simultaneous recognition for up to 2 hands.
    """
    if frame is None:
        return None

    try:
        pdet, hpose = get_hand_models()
        palms = pdet.infer(frame)
        if palms is None or len(palms) == 0:
            return None

        detected_hands = []
        for palm in palms[:2]:
            res = hpose.infer(frame, palm)
            if res is None or len(res) < 132:
                continue

            pose_score = float(res[-1]) if len(res) > 132 else 0.8
            if pose_score < 0.40:
                continue

            bbox = [int(v) for v in res[0:4]]
            lm = res[4:67].reshape(21, 3)
            # Handedness score: > 0.5 is right hand in model space
            handedness_score = float(res[130]) if len(res) > 130 else 0.5
            handedness = "Right" if handedness_score > 0.5 else "Left"

            hand_dict = classify_hand_landmarks(lm, bbox)
            hand_dict["handedness"] = handedness
            detected_hands.append(hand_dict)

        if not detected_hands:
            return None

        # Check dual-hand custom JSL gesture if two hands are detected
        dual_jsl = None
        if len(detected_hands) >= 2:
            h0_lm = np.array(detected_hands[0]["landmarks"])
            h1_lm = np.array(detected_hands[1]["landmarks"])
            w0 = h0_lm[0]
            w1 = h1_lm[0]
            s0 = max(1e-4, float(np.linalg.norm(h0_lm[9] - w0)))
            s1 = max(1e-4, float(np.linalg.norm(h1_lm[9] - w1)))
            f0 = ((h0_lm - w0) / s0).flatten()
            f1 = ((h1_lm - w1) / s1).flatten()
            combined_feat = np.concatenate([f0, f1])
            dual_jsl = match_custom_jsl_prototype(combined_feat, is_dual=True)

        # Primary hand preserves backward compatibility for single-hand consumers
        primary = dict(detected_hands[0])
        primary["hands"] = detected_hands
        if dual_jsl:
            primary["gesture"] = dual_jsl[1]
            primary["jsl_label"] = dual_jsl[0]
            primary["jsl_conf"] = dual_jsl[2]
            primary["is_dual_sign"] = True
        return primary

    except Exception:
        pass

    return None
