# app/services/detection_service.py
import cv2
import os
import time
from app.models.detection_model import yolo_model, CONF_THRESHOLD

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
RESULT_FOLDER = os.path.join(BASE_DIR, "results")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

def process_detection_with_bbox(image_path: str):
    """
    Proses deteksi YOLO + gambar bounding box
    Returns: (result_image_path, summary_dict)
    """

    start_time = time.time()
    results = yolo_model.predict(source=image_path, conf=CONF_THRESHOLD)

    img = cv2.imread(image_path)

    helmet_count = 0
    vest_count = 0
    highest_conf = 0
    detections = []

    for r in results:
        for box, cls_id, conf in zip(r.boxes.xyxy, r.boxes.cls, r.boxes.conf):
            cls_id = int(cls_id)
            conf = float(conf)
            if conf < CONF_THRESHOLD:
                continue

            label = yolo_model.names[cls_id]
            x1, y1, x2, y2 = map(int, box)

            if label == "helmet":
                color = (0, 255, 0)
                helmet_count += 1
            elif label == "vest":
                color = (0, 0, 255)
                vest_count += 1
            else:
                color = (255, 0, 0)

            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            cv2.putText(img, f"{label} {conf:.2f}", (x1, y1-5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            detections.append({"label": label, "confidence": round(conf, 3)})

            if conf > highest_conf:
                highest_conf = conf

    # ✅ Fix: patuh jika helm > 0 DAN vest > 0 (tidak harus sama jumlahnya)
    compliance_status = "Compliant" if helmet_count > 0 and vest_count > 0 and helmet_count == vest_count else "Non-Compliant"
    filename = f"detected_{os.path.basename(image_path)}"
    result_image_path = os.path.join(RESULT_FOLDER, filename)
    cv2.imwrite(result_image_path, img)

    inference_time = round(time.time() - start_time, 3)
    summary = {
        "helmet": helmet_count,
        "vest": vest_count,
        "compliance_status": compliance_status,
        "highest_confidence": round(highest_conf, 3),
        "inference_time_sec": inference_time
    }

    # ✅ Fix: ganti backslash jadi forward slash agar URL valid di browser
    result_image_path = result_image_path.replace("\\", "/")

    return result_image_path, summary