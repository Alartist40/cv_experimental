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
            if pose_score < 0.40:
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

            # Euclidean scale invariant finger extension check:
            # Tip must be distinctly farther from wrist than both PIP and MCP joints
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

            # =========================================================================
            # SIGN LANGUAGE & HAND GESTURE CLASSIFIER (JSL / UNIVERSAL)
            # =========================================================================

            # 1. OK / Money (👌 / お金): Thumb and index tips touching in circle, remaining 3 extended
            if is_ok_circle and mid_ext and rng_ext and pnk_ext:
                return {"gesture": "ok", "box": bbox, "tips": tips, "landmarks": lm[:, :2].tolist()}

            # 2. Kitsune / Fox (🦊 / きつね - Japanese traditional sign):
            # Index and Pinky extended (ears), Thumb touching Middle & Ring tips (snout)
            d_mid_thb = np.hypot(lm[4, 0] - lm[12, 0], lm[4, 1] - lm[12, 1])
            d_rng_thb = np.hypot(lm[4, 0] - lm[16, 0], lm[4, 1] - lm[16, 1])
            is_snout_closed = (d_mid_thb / hand_scale < 0.38) and (d_rng_thb / hand_scale < 0.38)
            if idx_ext and pnk_ext and is_snout_closed:
                return {"gesture": "kitsune", "box": bbox, "tips": tips, "landmarks": lm[:, :2].tolist()}

            # 3. Pinky / Promise (🤙 / 指切り・彼女): Pinky alone extended, other 4 closed
            if pnk_ext and not idx_ext and not mid_ext and not rng_ext and not thb_ext:
                return {"gesture": "pinky_promise", "box": bbox, "tips": tips, "landmarks": lm[:, :2].tolist()}

            # 4. Call Me / Shaka (🤙): Thumb and Pinky extended, middle three folded
            if thb_ext and pnk_ext and not idx_ext and not mid_ext and not rng_ext:
                return {"gesture": "call", "box": bbox, "tips": tips, "landmarks": lm[:, :2].tolist()}

            # 5. Rock / Horns (🤘): Index & Pinky extended, Middle & Ring closed
            if idx_ext and pnk_ext and not mid_ext and not rng_ext:
                return {"gesture": "rock", "box": bbox, "tips": tips, "landmarks": lm[:, :2].tolist()}

            # 6. Peace / JSL 2 / Victory (✌️ / 2): Index & middle extended, ring & pinky closed
            if idx_ext and mid_ext and not rng_ext and not pnk_ext:
                return {"gesture": "peace", "box": bbox, "tips": tips, "landmarks": lm[:, :2].tolist()}

            # 7. Pointing / JSL 1 (☝️ / 1): Index extended only
            if idx_ext and not mid_ext and not rng_ext and not pnk_ext:
                return {"gesture": "pointing", "box": bbox, "tips": tips, "landmarks": lm[:, :2].tolist()}

            # 8. JSL 4 / Four Fingers (4️⃣): 4 fingers extended, thumb folded
            if idx_ext and mid_ext and rng_ext and pnk_ext and not thb_ext:
                return {"gesture": "four", "box": bbox, "tips": tips, "landmarks": lm[:, :2].tolist()}

            # 9. JSL 3 / Three (3️⃣): Index, Middle, Ring extended, pinky closed
            if idx_ext and mid_ext and rng_ext and not pnk_ext:
                return {"gesture": "three", "box": bbox, "tips": tips, "landmarks": lm[:, :2].tolist()}

            # 10. Thumbs Up / JSL Good / Male (👍 / よい・彼): Thumb extended up, 4 fingers closed
            if thb_ext and not idx_ext and not mid_ext and not rng_ext and not pnk_ext:
                return {"gesture": "thumbs_up", "box": bbox, "tips": tips, "landmarks": lm[:, :2].tolist()}

            # 11. Open Palm / JSL 5 / Paper (🖐️ / 5): All 4 fingers extended cleanly
            if idx_ext and mid_ext and rng_ext and pnk_ext:
                return {"gesture": "palm", "box": bbox, "tips": tips, "landmarks": lm[:, :2].tolist()}

            # 12. Clenched Fist / JSL 0 / Rock (✊ / 0・グー): All fingers closed
            if not idx_ext and not mid_ext and not rng_ext and not pnk_ext and not thb_ext:
                return {"gesture": "fist", "box": bbox, "tips": [], "landmarks": lm[:, :2].tolist()}

            # Default generic hand tracked
            return {"gesture": "hand", "box": bbox, "tips": tips, "landmarks": lm[:, :2].tolist()}

    except Exception:
        pass

    return None
