from flask import Blueprint, request
from flask_jwt_extended import create_access_token
from app.services.supabase_service import get_supabase
from app.utils.response_helper import success_response, error_response
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta

auth_bp = Blueprint("auth", __name__)

# ==========================
# REGISTER
# ==========================
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.json
    supabase = get_supabase()

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return error_response("All fields are required")

    # cek apakah email sudah ada
    existing = supabase.table("users") \
        .select("*") \
        .eq("email", email) \
        .execute()

    if existing.data:
        return error_response("Email already registered")

    hashed_password = generate_password_hash(password)

    response = supabase.table("users").insert({
        "username": username,
        "email": email,
        "password": hashed_password
    }).execute()

    return success_response("User registered successfully")


# ==========================
# LOGIN
# ==========================
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json
    supabase = get_supabase()

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return error_response("Email and password are required")

    # cek user
    user = supabase.table("users").select("*").eq("email", email).execute()
    if not user.data:
        return error_response("Invalid credentials")

    user_data = user.data[0]
    if not check_password_hash(user_data["password"], password):
        return error_response("Invalid credentials")

    # identity harus string
    access_token = create_access_token(
        identity=str(user_data["id"]),  # pastikan string
        expires_delta=timedelta(hours=12)
    )

    return success_response("Login successful", {"access_token": access_token})
