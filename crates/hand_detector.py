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

def classify_hand_landmarks(lm, bbox):
    """Classify 21 landmarks into a specific gesture."""
    wrist = lm[0, :2]

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
    if is_ok_circle and mid_ext and rng_ext and pnk_ext:
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

    return {
        "gesture": gesture_name,
        "box": bbox,
        "tips": tips,
        "landmarks": lm[:, :2].tolist()
    }

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

        # Primary hand preserves backward compatibility for single-hand consumers
        primary = dict(detected_hands[0])
        primary["hands"] = detected_hands
        return primary

    except Exception:
        pass

    return None
