from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import firebase_admin
from firebase_admin import credentials, auth, firestore
import requests
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Konfigurasi Firebase
cred = credentials.Certificate("firebase_config.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Route Home
@app.route('/')
def home():
    return render_template("index2.html")

# Route Login dengan Google
@app.route('/login')
def login():
    return redirect("https://accounts.google.com/o/oauth2/auth?client_id=YOUR_GOOGLE_CLIENT_ID&redirect_uri=http://127.0.0.1:5000/callback&scope=email profile&response_type=code")

# Callback setelah login Google
@app.route('/callback')
def callback():
    code = request.args.get("code")
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "code": code,
        "client_id": "YOUR_GOOGLE_CLIENT_ID",
        "client_secret": "YOUR_GOOGLE_CLIENT_SECRET",
        "redirect_uri": "http://127.0.0.1:5000/callback",
        "grant_type": "authorization_code"
    }
    token_response = requests.post(token_url, data=token_data).json()
    user_info_url = "https://www.googleapis.com/oauth2/v1/userinfo?access_token=" + token_response["access_token"]
    user_info = requests.get(user_info_url).json()
    session['user'] = user_info
    return redirect(url_for("dashboard"))

# Dashboard setelah login
@app.route('/dashboard')
def dashboard():
    if "user" in session:
        return render_template("dashboard.html", user=session["user"])
    return redirect(url_for("home"))

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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)