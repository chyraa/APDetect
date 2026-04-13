# app/models/detection_model.py
from ultralytics import YOLO

MODEL_PATH = "app/ml_models/best.pt"
CONF_THRESHOLD = 0.5

# Load YOLO sekali saat server start
yolo_model = YOLO(MODEL_PATH)