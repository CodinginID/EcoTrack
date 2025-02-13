#!/bin/bash

# Aktifkan virtual environment
#source env/bin/activate  # Untuk Linux/MacOS
# source venv/Scripts/activate  # Untuk Windows (gunakan di cmd atau Git Bash)

# Set environment variables untuk mode development
export FLASK_APP=app.py
export FLASK_ENV=development

# Jalankan aplikasi Flask
flask run --host=0.0.0.0 --port=9000 --reload

# Konfigurasi Firebase
export FIREBASE_CONFIG="firebase_config.json"
