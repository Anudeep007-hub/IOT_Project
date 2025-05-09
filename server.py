import io
from flask import Flask, render_template, request, jsonify, send_file, redirect
from flask_cors import CORS
import os
from dotenv import load_dotenv
from functools import wraps
import smtplib

# Local functions import
from predict_face import predict_faces 
from register_faces import register_faces
from db_helper import DatabaseHelper

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Admin credentials
ADMIN_CREDENTIALS = {
    "username": "admin",
    "password": "admin123"
}

# Hardcoded authorization decorator
def hardcoded_auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        username = request.headers.get("Username")
        password = request.headers.get("Password")
        if username != ADMIN_CREDENTIALS["username"] or password != ADMIN_CREDENTIALS["password"]:
            return jsonify({"status": "error", "message": "Unauthorized"}), 403
        return f(*args, **kwargs)
    return decorated

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if username == ADMIN_CREDENTIALS["username"] and password == ADMIN_CREDENTIALS["password"]:
        return jsonify({"status": "success", "message": "Login successful"})
    return jsonify({"status": "error", "message": "Invalid username or password"}), 401

# Main page route
@app.route('/')
def index():
    return render_template('index.html')

# Login page route
@app.route('/login')
def login_page():
    return render_template('login.html')


@app.route('/api/register_face', methods=['GET'])
def register():
    # Get the 'name' from the query parameters
    name = request.args.get('name')
    
    if name:
        register_faces(name)
        return jsonify({"status": "success", "message": f"Face registered for {name}"})
    else:
        return jsonify({"status": "error", "message": "Name parameter is missing"})
    
    
@app.route('/api/predict_face', methods=['POST'])
def predict():
    try:
        name, image_name = predict_faces()
        if image_name is None:
            return jsonify({
                "status": "error",
                "message": "Failed to capture image"
            }), 500
            
        label = "safe" if name != "Unknown" else "Intruder"
        return jsonify({
            "status": "success",
            "name": name,
            "label": label,
            "image_path": f"api/image/{image_name}"  # Update path to use MongoDB route
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# Add this route to serve images directly from MongoDB if needed
@app.route('/api/image/<image_name>')
def get_image(image_name):
    db_helper = DatabaseHelper()
    image_data = db_helper.get_image(image_name)
    if image_data:
        return send_file(
            io.BytesIO(image_data),
            mimetype='image/jpeg'
        )
    return jsonify({"error": "Image not found"}), 404


@app.route('/api/clear_data', methods=['POST'])
def clear_data():
    try:
        db_helper = DatabaseHelper()
        db_helper.clear_all_data()
        return jsonify({"status": "success", "message": "All face data cleared successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/user_history/<name>', methods=['GET'])
def get_user_history(name):
    db_helper = DatabaseHelper()
    history = db_helper.get_user_history(name)
    if history:
        # Convert timestamps to string format for JSON serialization
        history['timestamps'] = [ts.strftime('%Y-%m-%d %H:%M:%S') 
                               for ts in history['timestamps']]
        return jsonify({
            'status': 'success',
            'data': history
        })
    return jsonify({
        'status': 'error',
        'message': 'User not found'
    }), 404
    
## For opening the gate
@app.route('/api/open_gate', methods=['POST']) 
def open_gate():
    return jsonify({
            "status": "success",
            "name": 'Owner',
            "label": 'safe',
        })
    
@app.route('/api/logout', methods=['POST'])
def logout():
    return jsonify({"status": "success", "message": "Logged out successfully"})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)