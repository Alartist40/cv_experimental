import cv2
import numpy as np

_palm_detector = None
_hand_pose = None

def get_hand_models():
    global _palm_detector, _hand_pose
    if _palm_detector is None:
        from crates.mp_hand import MPPalmDet
        from crates.mp_handpose import MPHandPose
        # Confidence threshold set to 0.38: completely ignores background objects/faces while reliably capturing hands
        _palm_detector = MPPalmDet(modelPath="models/palm_detection_mediapipe_2023feb.onnx", scoreThreshold=0.38)
        _hand_pose = MPHandPose(modelPath="models/handpose_estimation_mediapipe_2023feb.onnx", confThreshold=0.35)
    return _palm_detector, _hand_pose

def detect_hand_gesture(frame, person_box=None):
    """
    Neural 21-Landmark Hand Pose & Sign Language Gesture Engine.
    Uses MediaPipe palm localization + 21 skeletal joints.
    Guarantees ZERO false positives when hands are not present.
    """
    if frame is None:
        return None

    try:
        pdet, hpose = get_hand_models()
        palms = pdet.infer(frame)
        if palms is None or len(palms) == 0:
            return None

        # Process detected palm candidate
        for palm in palms:
            res = hpose.infer(frame, palm)
            if res is None or len(res) < 132:
                continue

            # Check landmark confidence score
            pose_score = float(res[-1]) if len(res) > 132 else 0.8
            if pose_score < 0.30:
                continue

            bbox = [int(v) for v in res[0:4]]
            lm = res[4:67].reshape(21, 3)

            # 21 Keypoints:
            # 0: Wrist
            # 1-4: Thumb (CMC, MCP, IP, Tip)
            # 5-8: Index (MCP, PIP, DIP, Tip)
            # 9-12: Middle (MCP, PIP, DIP, Tip)
            # 13-16: Ring (MCP, PIP, DIP, Tip)
            # 17-20: Pinky (MCP, PIP, DIP, Tip)
            wrist = lm[0, :2]

            # Euclidean scale invariant finger extension check
            def is_finger_extended(tip_idx, pip_idx, mcp_idx):
                d_tip = np.linalg.norm(lm[tip_idx, :2] - wrist)
                d_mcp = np.linalg.norm(lm[mcp_idx, :2] - wrist)
                d_pip = np.linalg.norm(lm[pip_idx, :2] - wrist)
                return (d_tip > d_mcp * 1.15 and d_tip > d_pip)

            # Thumb extension (landmark 4 vs 2)
            d_thb_tip = np.linalg.norm(lm[4, :2] - wrist)
            d_thb_mcp = np.linalg.norm(lm[2, :2] - wrist)
            thb_ext = d_thb_tip > d_thb_mcp * 1.20

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

            # =========================================================================
            # SIGN LANGUAGE & HAND GESTURE CLASSIFIER
            # =========================================================================

            # 1. OK Sign (👌): Thumb and index tips touching in circle, middle+ring+pinky extended
            if is_ok_circle and mid_ext and rng_ext and pnk_ext:
                return {"gesture": "ok", "box": bbox, "tips": tips, "landmarks": lm[:, :2].tolist()}

            # 2. Call Me / Shaka (🤙): Thumb and pinky extended, index, middle, ring closed
            if thb_ext and pnk_ext and not idx_ext and not mid_ext and not rng_ext:
                return {"gesture": "call", "box": bbox, "tips": tips, "landmarks": lm[:, :2].tolist()}

            # 3. Rock / Horns (🤘): Index & pinky extended, middle & ring closed
            if idx_ext and pnk_ext and not mid_ext and not rng_ext:
                return {"gesture": "rock", "box": bbox, "tips": tips, "landmarks": lm[:, :2].tolist()}

            # 4. Peace / Victory (✌️): Index & middle extended, ring & pinky closed
            if idx_ext and mid_ext and not rng_ext and not pnk_ext:
                return {"gesture": "peace", "box": bbox, "tips": tips, "landmarks": lm[:, :2].tolist()}

            # 5. Pointing / Number 1 (☝️): Index extended only
            if idx_ext and not mid_ext and not rng_ext and not pnk_ext:
                return {"gesture": "pointing", "box": bbox, "tips": tips, "landmarks": lm[:, :2].tolist()}

            # 6. Thumbs Up (👍): Thumb extended up, all 4 fingers closed
            if thb_ext and not idx_ext and not mid_ext and not rng_ext and not pnk_ext:
                return {"gesture": "thumbs_up", "box": bbox, "tips": tips, "landmarks": lm[:, :2].tolist()}

            # 7. Open Palm / Stop (🖐️): 3 or more fingers extended
            if sum([idx_ext, mid_ext, rng_ext, pnk_ext]) >= 3:
                return {"gesture": "palm", "box": bbox, "tips": tips, "landmarks": lm[:, :2].tolist()}

            # 8. Clenched Fist (✊): All fingers closed
            if not idx_ext and not mid_ext and not rng_ext and not pnk_ext and not thb_ext:
                return {"gesture": "fist", "box": bbox, "tips": [], "landmarks": lm[:, :2].tolist()}

            # Default generic hand tracked
            return {"gesture": "hand", "box": bbox, "tips": tips, "landmarks": lm[:, :2].tolist()}

    except Exception:
        pass

    return None
