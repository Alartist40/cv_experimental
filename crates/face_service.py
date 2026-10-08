import sys
import json
import os
import cv2
import numpy as np

DB_FILE = "data/faces/database.json"
IMG_PATH = "data/live_frame.jpg"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_db(db):
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)

def get_face_models(w=640, h=480):
    # Lower threshold from 0.6 to 0.35 so facial detection succeeds reliably even in difficult lighting
    det = cv2.FaceDetectorYN.create("models/face_detection_yunet_2023mar.onnx", "", (w, h), score_threshold=0.35, nms_threshold=0.3)
    rec = cv2.FaceRecognizerSF.create("models/face_recognition_sface_2021dec.onnx", "")
    return det, rec

def normalize_lighting(img):
    """Normalize lighting using adaptive CLAHE on lightness channel to prevent washed out or dim failure."""
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    limg = cv2.merge((cl, a, b))
    return cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

def cmd_scan():
    if not os.path.exists(IMG_PATH):
        return {"status": "error", "message": "No live camera frame found."}
    
    img = cv2.imread(IMG_PATH)
    if img is None:
        return {"status": "error", "message": "Failed to decode camera frame."}

    h, w = img.shape[:2]
    det, rec = get_face_models(w, h)
    det.setInputSize((w, h))
    _, faces = det.detect(img)

    # If first pass missed due to lighting, try normalized lighting pass
    if faces is None or len(faces) == 0:
        norm_img = normalize_lighting(img)
        _, faces = det.detect(norm_img)
        if faces is not None and len(faces) > 0:
            img = norm_img

    if faces is None or len(faces) == 0:
        return {"status": "no_face", "message": "No human face detected in frame."}

    face = faces[0]
    aligned = rec.alignCrop(img, face)
    feature = rec.feature(aligned)

    db = load_db()
    best_match = None
    best_score = -1.0
    threshold = 0.363  # Cosine similarity threshold for SFace (0.363 is official threshold)

    for name, data in db.items():
        stored_feat = np.array(data["embedding"], dtype=np.float32)
        score = rec.match(feature, stored_feat, cv2.FaceRecognizerSF_FR_COSINE)
        if score > best_score:
            best_score = float(score)
            best_match = name

    # Bounding box of face
    fx, fy, fw, fh = [int(v) for v in face[:4]]

    if best_match and best_score >= threshold:
        user_info = db[best_match]
        return {
            "status": "authorized",
            "name": best_match,
            "clearance": user_info.get("clearance", "LEVEL-5"),
            "role": user_info.get("role", "OPERATOR"),
            "confidence": round(best_score * 100, 1),
            "face_box": [fx, fy, fw, fh]
        }
    else:
        return {
            "status": "unauthorized",
            "name": "UNKNOWN SUBJECT",
            "clearance": "RESTRICTED",
            "role": "TRESPASSER",
            "confidence": round(max(0.0, best_score) * 100, 1),
            "face_box": [fx, fy, fw, fh]
        }

def cmd_enroll(name, role="OPERATOR", clearance="LEVEL-5"):
    if not name or not name.strip():
        return {"status": "error", "message": "Name cannot be empty."}

    name = name.strip().upper()
    if not os.path.exists(IMG_PATH):
        return {"status": "error", "message": "No live camera frame found."}

    img = cv2.imread(IMG_PATH)
    if img is None:
        return {"status": "error", "message": "Failed to decode camera frame."}

    h, w = img.shape[:2]
    det, rec = get_face_models(w, h)
    det.setInputSize((w, h))
    _, faces = det.detect(img)

    if faces is None or len(faces) == 0:
        norm_img = normalize_lighting(img)
        _, faces = det.detect(norm_img)
        if faces is not None and len(faces) > 0:
            img = norm_img

    if faces is None or len(faces) == 0:
        return {"status": "error", "message": "No face found to enroll. Look directly at the camera."}

    face = faces[0]
    aligned = rec.alignCrop(img, face)
    feature = rec.feature(aligned)

    db = load_db()
    db[name] = {
        "embedding": feature.tolist(),
        "role": role.upper(),
        "clearance": clearance.upper(),
        "registered_at": cv2.getTickCount()
    }
    save_db(db)

    return {"status": "enrolled", "name": name, "message": f"Successfully enrolled {name} into security matrix."}

def cmd_list():
    db = load_db()
    users = []
    for name, d in db.items():
        users.append({
            "name": name,
            "role": d.get("role", "OPERATOR"),
            "clearance": d.get("clearance", "LEVEL-5")
        })
    return {"status": "ok", "users": users}

def cmd_delete(name):
    name = name.strip().upper()
    db = load_db()
    if name in db:
        del db[name]
        save_db(db)
        return {"status": "deleted", "message": f"Removed {name} from registry."}
    return {"status": "error", "message": f"{name} not found in database."}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Missing command"}))
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "scan":
        res = cmd_scan()
    elif cmd == "enroll":
        name = sys.argv[2] if len(sys.argv) > 2 else "XANDER"
        role = sys.argv[3] if len(sys.argv) > 3 else "COMMANDER"
        clearance = sys.argv[4] if len(sys.argv) > 4 else "LEVEL-5"
        res = cmd_enroll(name, role, clearance)
    elif cmd == "list":
        res = cmd_list()
    elif cmd == "delete":
        name = sys.argv[2] if len(sys.argv) > 2 else ""
        res = cmd_delete(name)
    else:
        res = {"error": f"Unknown command {cmd}"}

    print(json.dumps(res))
