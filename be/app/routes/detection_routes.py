from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from app.services.detection_service import process_detection_with_bbox
from app.services.supabase_service import get_supabase
import os
import uuid

detection_bp = Blueprint("detection", __name__)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
RESULT_FOLDER = os.path.join(BASE_DIR, "results")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)


@detection_bp.route("/predict", methods=["POST"])
@jwt_required()
def predict():
    supabase = get_supabase()

    # ================= JWT =================
    user_id = get_jwt_identity()
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"error": "Invalid user id"}), 400

    # ================= CEK FILE =================
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    # ================= SIMPAN FILE =================
    filename = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4()}_{filename}"
    file_path = os.path.join(UPLOAD_FOLDER, unique_name)
    file.save(file_path)

    print("IMAGE SAVED:", file_path)

    # ================= YOLO DETECTION =================
    try:
        result_image_path, result_summary = process_detection_with_bbox(file_path)
        print("DETECTION RESULT:", result_summary)
        print("RESULT IMAGE PATH:", result_image_path)
    except Exception as e:
        print("DETECTION ERROR:", e)
        return jsonify({"error": "Detection failed"}), 500

    # ================= SIMPAN DATABASE =================
    area = request.form.get("area_proyek", "realtime")
    try:
        supabase.table("detections").insert({
            "user_id": user_id,
            "area_proyek": area,
            "helmet_count": int(result_summary["helmet"]),
            "vest_count": int(result_summary["vest"]),
            "keterangan": "detected"
        }).execute()
    except Exception as e:
        print("DATABASE ERROR:", e)

    # ================= RETURN JSON =================
    if not os.path.exists(result_image_path):
        print("FILE NOT FOUND:", result_image_path)
        return jsonify({"error": "Detection image not found"}), 500

    # AMBIL HANYA NAMA FILENYA SAJA
    # os.path.basename akan mengubah 'C:\...\be\results\gambar.jpg' jadi 'gambar.jpg'
    filename_only = os.path.basename(result_image_path)

    # RAKIT URL AGAR BISA DIAKSES BROWSER
    result_image_url = f"http://127.0.0.1:5000/results/{filename_only}"

    print("URL YANG DIKIRIM KE WEB:", result_image_url) # Cek ini di terminal nanti

    return jsonify({
        "helmet": int(result_summary["helmet"]),
        "vest": int(result_summary["vest"]),
        "compliance_status": result_summary["compliance_status"],
        "highest_confidence": result_summary["highest_confidence"],
        "inference_time_sec": result_summary["inference_time_sec"],
        "result_image_path": result_image_url # Mengirim URL, bukan path lokal
    })


@detection_bp.route("/history", methods=["GET"])
@jwt_required()
def get_history():
    """Ambil data deteksi dari database dengan filter tanggal (opsional)"""
    supabase = get_supabase()
    
    # ================= JWT =================
    user_id = get_jwt_identity()
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"error": "Invalid user id"}), 400

    # ================= AMBIL PARAMETER FILTER =================
    date_from = request.args.get("date_from")  # Format: YYYY-MM-DD
    date_to = request.args.get("date_to")      # Format: YYYY-MM-DD
    
    try:
        query = supabase.table("detections").select("*")
        
        # Filter tanggal jika ada
        if date_from:
            query = query.gte("created_at", date_from + "T00:00:00")
        if date_to:
            query = query.lte("created_at", date_to + "T23:59:59")
        
        # Urutkan dari terbaru
        data = query.order("created_at", desc=True).execute()
        
        print(f"HISTORY QUERY - From: {date_from}, To: {date_to}")
        print(f"TOTAL RECORDS: {len(data.data)}")
        
        return jsonify({"success": True, "data": data.data}), 200
        
    except Exception as e:
        print("HISTORY ERROR:", e)
        return jsonify({"error": str(e)}), 500


