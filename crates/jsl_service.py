import os
import json
import numpy as np

DATASET_DIR = "data/jsl_dataset"
MODEL_FILE = "data/jsl_model.json"

def ensure_dataset_dir():
    os.makedirs(DATASET_DIR, exist_ok=True)

def normalize_landmarks(lm_list):
    """
    Takes a list of [x, y, z] or [x, y] coordinates for 21 landmarks.
    Centers at wrist (index 0) and normalizes by palm scale (norm of wrist to middle MCP joint 9).
    Returns flattened float list (42 values).
    """
    pts = np.array(lm_list, dtype=np.float32)
    if pts.shape[0] < 21:
        return None
    coords = pts[:21, :2]
    wrist = coords[0]
    centered = coords - wrist
    palm_scale = np.linalg.norm(coords[9] - wrist)
    if palm_scale < 1e-4:
        palm_scale = 1.0
    normalized = centered / palm_scale
    return normalized.flatten().tolist()

def record_sample(label, hands_data, notes=""):
    """
    hands_data: list of dicts with keys:
      - 'landmarks': 21 points
      - 'handedness': 'Right' or 'Left'
    """
    ensure_dataset_dir()
    clean_label = "".join([c if c.isalnum() or c in ("_", "-") else "_" for c in label.strip().lower()])
    file_path = os.path.join(DATASET_DIR, f"{clean_label}.jsonl")

    processed_hands = []
    for h in hands_data:
        norm_feat = normalize_landmarks(h.get("landmarks", []))
        if norm_feat is not None:
            processed_hands.append({
                "handedness": h.get("handedness", "Right"),
                "features": norm_feat
            })

    if not processed_hands:
        return {"status": "error", "message": "No valid landmarks found"}

    sample = {
        "label": label.strip(),
        "clean_label": clean_label,
        "is_dual": len(processed_hands) >= 2,
        "hands": processed_hands,
        "notes": notes
    }

    with open(file_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(sample, ensure_ascii=False) + "\n")

    return {"status": "ok", "label": label, "clean_label": clean_label}

def get_dataset_summary():
    ensure_dataset_dir()
    summary = []
    if not os.path.exists(DATASET_DIR):
        return summary

    for fname in sorted(os.listdir(DATASET_DIR)):
        if fname.endswith(".jsonl"):
            clean_label = fname[:-6]
            path = os.path.join(DATASET_DIR, fname)
            count = 0
            label_name = clean_label
            is_dual = False
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            item = json.loads(line)
                            count += 1
                            label_name = item.get("label", label_name)
                            is_dual = item.get("is_dual", False)
                        except Exception:
                            pass
            if count > 0:
                summary.append({
                    "clean_label": clean_label,
                    "label": label_name,
                    "count": count,
                    "is_dual": is_dual
                })
    return summary

def train_jsl_model():
    """
    Aggregates recorded landmark vectors per class into normalized geometric prototype centroids.
    Saves to data/jsl_model.json.
    """
    ensure_dataset_dir()
    prototypes = {}

    for fname in os.listdir(DATASET_DIR):
        if not fname.endswith(".jsonl"):
            continue
        path = os.path.join(DATASET_DIR, fname)
        samples_single = []
        samples_dual = []
        display_label = None

        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                    display_label = item.get("label", fname[:-6])
                    hands = item.get("hands", [])
                    if len(hands) >= 2:
                        f0 = np.array(hands[0]["features"])
                        f1 = np.array(hands[1]["features"])
                        samples_dual.append(np.concatenate([f0, f1]))
                    elif len(hands) == 1:
                        samples_single.append(np.array(hands[0]["features"]))
                except Exception:
                    continue

        if samples_dual:
            mean_vec = np.mean(samples_dual, axis=0)
            norm = np.linalg.norm(mean_vec)
            if norm > 1e-4:
                mean_vec = mean_vec / norm
            prototypes[f"dual_{fname[:-6]}"] = {
                "label": display_label,
                "clean_label": fname[:-6],
                "is_dual": True,
                "vector": mean_vec.tolist(),
                "sample_count": len(samples_dual)
            }

        if samples_single:
            mean_vec = np.mean(samples_single, axis=0)
            norm = np.linalg.norm(mean_vec)
            if norm > 1e-4:
                mean_vec = mean_vec / norm
            prototypes[f"single_{fname[:-6]}"] = {
                "label": display_label,
                "clean_label": fname[:-6],
                "is_dual": False,
                "vector": mean_vec.tolist(),
                "sample_count": len(samples_single)
            }

    model_data = {
        "version": "1.0",
        "prototypes": prototypes,
        "class_count": len(prototypes)
    }

    with open(MODEL_FILE, "w", encoding="utf-8") as f:
        json.dump(model_data, f, indent=2, ensure_ascii=False)

    return model_data

def delete_sign(clean_label):
    file_path = os.path.join(DATASET_DIR, f"{clean_label}.jsonl")
    if os.path.exists(file_path):
        os.remove(file_path)
        train_jsl_model()
        return {"status": "ok", "deleted": clean_label}
    return {"status": "error", "message": "Sign not found"}

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "summary"
    if cmd == "train":
        res = train_jsl_model()
        print(json.dumps({"status": "ok", "classes": res["class_count"]}))
    elif cmd == "summary":
        print(json.dumps(get_dataset_summary(), ensure_ascii=False))
    elif cmd == "delete" and len(sys.argv) > 2:
        print(json.dumps(delete_sign(sys.argv[2]), ensure_ascii=False))
    elif cmd == "record":
        raw = sys.stdin.read()
        payload = json.loads(raw)
        res = record_sample(payload.get("label", "unknown"), payload.get("hands", []), payload.get("notes", ""))
        print(json.dumps(res, ensure_ascii=False))
