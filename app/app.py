from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import firebase_admin
from firebase_admin import credentials, auth, firestore
import requests
import os
import logging
import json


# Setup logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Konfigurasi Firebase
cred = credentials.Certificate("firebase_config.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Google OAuth Konfigurasi
GOOGLE_CLIENT_ID = str(os.getenv("GOOGLE_CLIENT_ID"))
GOOGLE_CLIENT_SECRET = str(os.getenv("GOOGLE_CLIENT_SECRET"))
GOOGLE_REDIRECT_URI = str(os.getenv("GOOGLE_REDIRECT_URI"))

API_URL = "https://sipsn.menlhk.go.id/sipsn/public/home/get_chart_data_sampah"

# API Route Home
@app.route('/')
def home():
    return render_template("index2.html")

@app.route('/jejak-angka')
def jejak_angka():

    with open("static/data_chart.json") as f:
        chart_data = json.load(f)


    with open("static/data.json") as f:
        data = json.load(f)  # Load data dari file JSON
    return render_template("jejak_angka.html", data=data["data"], chart_data=chart_data)

@app.route('/form-question')
def form_quest():
    return render_template("form_question.html")

@app.route('/lokal-sampah')
def lokal_sampah():
    return render_template("lokal_sampah.html")

# Route Login dengan Google
@app.route("/login")
def login():
    """Redirect ke halaman login Google"""
    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=email%20profile"
    )
    return redirect(google_auth_url)

# Callback setelah login Google
@app.route("/callback")
def callback():
    """Menangani respon dari Google setelah login"""
    code = request.args.get("code")
    
    if not code:
        return "Login gagal!", 400
    
    # Tukarkan kode dengan token akses
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    token_response = requests.post(token_url, data=token_data)
    token_json = token_response.json()

    if "access_token" not in token_json:
        return "Gagal mendapatkan token!", 400

    access_token = token_json["access_token"]
    id_token = token_json["id_token"]

    # Ambil data pengguna dari Google
    userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    userinfo_response = requests.get(userinfo_url, headers={"Authorization": f"Bearer {access_token}"})
    user_info = userinfo_response.json()

    if "email" not in user_info:
        return "Gagal mendapatkan informasi pengguna!", 400

    email = user_info["email"]
    name = user_info.get("name", "")
    picture = user_info.get("picture", "")

    # Cek apakah user sudah ada di Firebase
    try:
        user = auth.get_user_by_email(email)
    except:
        # Jika belum ada, buat user di Firebase
        user = auth.create_user(email=email, display_name=name, photo_url=picture)

    # Simpan sesi login
    session["user"] = {
        "uid": user.uid,
        "email": user.email,
        "name": user.display_name,
        "picture": user.photo_url,
    }

    return redirect(url_for("dashboard"))

# Dashboard setelah login
@app.route('/dashboard')
def dashboard():
    if "user" in session:
        return render_template("dashboard.html", user=session["user"])
    return redirect(url_for("home"))


@app.route('/register', methods=['POST'])
def register():
    data = request.json
    id_token = data.get("id_token")

    user_info = verify_google_token(id_token)
    if user_info is None:
        return jsonify({"error": "Invalid Google Token"}), 400

    user_id = user_info["uid"]
    email = user_info["email"]
    name = user_info.get("name", "")

    try:
        # Periksa apakah user sudah ada di Firebase
        user = auth.get_user(user_id)
        return jsonify({"message": "User already exists", "uid": user.uid}), 200
    except:
        # Buat user baru di Firebase
        user = auth.create_user(uid=user_id, email=email, display_name=name)
        return jsonify({"message": "User registered successfully", "uid": user.uid}), 201


# Logout
@app.route('/logout')
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))


# Integrasi Google Form
@app.route('/submit_form', methods=["POST"])
def submit_form():
    idForm = "1FAIpQLSdEJr9RRTU4O0EVlj_cADF4ZxVNMdRMmCmQWrth9tI_mDnaNA"
    google_form_url = f"https://docs.google.com/forms/d/e/{idForm}/formResponse"
    form_data = {
        "entry.YOUR_ENTRY_ID": request.form["name"],
        "entry.YOUR_OTHER_ENTRY_ID": request.form["email"]
    }
    response = requests.post(google_form_url, data=form_data)
    return jsonify({"message": "Form submitted successfully!"})

# tools
def verify_google_token(id_token):
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        return None
    
@app.route("/get_data", methods=["POST"])
def get_data():
    try:
        # Mengambil data dari body JSON request
        data = request.get_json()
        tahun = data.get("tahun", "2024")
        id_propinsi = data.get("id_propinsi", "ALL")
        id_district = data.get("id_district", "")

        params = {
            "jenis": "timbulan",
            "tahun": tahun,
            "id_propinsi": id_propinsi,
            "id_district": id_district,
            "id_das": 0
        }

        logger.info(f"Requesting data with params: {params}")  # Log parameter permintaan

        response = requests.post(API_URL, json=params)  # Menggunakan POST
        response.raise_for_status()  # Raise error jika response gagal

        if response.text:
            logger.info(f"API response received successfully: {response.status_code}")
            logger.debug(f"Response JSON: {response.json()}")  # Log JSON response for debugging
            return jsonify(response.json())  # Kirim data ke frontend
        else:
            logger.warning("Received empty response from API.")
            return jsonify({"error": "Empty response from API"}), 500

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}", exc_info=True)  # Log error dengan stack trace
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)