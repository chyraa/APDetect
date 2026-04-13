from flask import Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.supabase_service import get_supabase
from app.utils.response_helper import success_response

report_bp = Blueprint("report", __name__)

@report_bp.route("/history", methods=["GET"])
@jwt_required()
def history():
    user_id = get_jwt_identity()
    supabase = get_supabase()

    response = supabase.table("detections") \
        .select("*") \
        .eq("user_id", user_id) \
        .order("created_at", desc=True) \
        .execute()

    return success_response("History fetched", response.data)