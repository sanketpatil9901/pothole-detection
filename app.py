from flask import Flask, request, render_template, redirect, url_for, session, flash, jsonify
from werkzeug.utils import secure_filename
import os
import uuid
import time
import json
import ast
import math
import psycopg2
import psycopg2.extras
from datetime import timedelta
import imageDetector

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['SESSION_PERMANENT'] = True
app.permanent_session_lifetime = timedelta(minutes=30)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# ---------- DATABASE CONFIG ----------
db_config = {
    'host': os.getenv('DB_HOST', 'dpg-d128a8be5dus73f26o10-a'),
    'user': os.getenv('DB_USER', 'pothole_db_rldm_user'),
    'password': os.getenv('DB_PASSWORD', ''),
    'dbname': os.getenv('DB_NAME', 'pothole_db_rldm'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'sslmode': 'require' 
}

def get_db_connection():
    return psycopg2.connect(**db_config, cursor_factory=psycopg2.extras.RealDictCursor)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS potholes (
                id SERIAL PRIMARY KEY,
                latitude DOUBLE PRECISION NOT NULL,
                longitude DOUBLE PRECISION NOT NULL,
                image BYTEA,  -- Changed from image_path TEXT
                count INTEGER DEFAULT 1,
                details JSONB,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS complaints (
                id SERIAL PRIMARY KEY,
                user_name VARCHAR(100),
                user_email VARCHAR(100),
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        conn.close()
        print("✅ Tables created successfully.")
    except Exception as e:
        print("❌ Error creating tables:", e)


# ---------- ROUTES ----------

@app.route('/')
def index():
    if session.get('admin_logged_in'):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM potholes ORDER BY id DESC")
            pothole_history = cursor.fetchall()
            cursor.execute("SELECT name, email, created_at FROM users ORDER BY id DESC")
            users = cursor.fetchall()
            cursor.execute("SELECT user_name, user_email, message, created_at FROM complaints ORDER BY id DESC")
            complaints = cursor.fetchall()
            conn.close()
        except Exception as e:
            flash("Database error: " + str(e), "error")
            return redirect(url_for('login'))
        for p in pothole_history:
            try:
                p['details_parsed'] = json.loads(p['details'])
            except Exception:
                try:
                    p['details_parsed'] = ast.literal_eval(p['details'])
                except Exception:
                    p['details_parsed'] = []
        return render_template('admin_dashboard.html', pothole_history=pothole_history, users=users, complaints=complaints)
    elif session.get('user_logged_in'):
        return redirect(url_for('user_dashboard'))
    return redirect(url_for('login'))

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1 = math.radians(float(lat1))
    phi2 = math.radians(float(lat2))
    dphi = math.radians(float(lat2) - float(lat1))
    dlambda = math.radians(float(lon2) - float(lon1))
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

@app.route('/user-dashboard')
def user_dashboard():
    if session.get('user_logged_in'):
        return render_template('user_dashboard.html', user_name=session.get('user_name'), user_email=session.get('user_email'))
    return redirect(url_for('login'))

@app.route('/api/potholes_nearby')
def potholes_nearby():
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    if lat is None or lon is None:
        return jsonify([])
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM potholes")
    potholes = cursor.fetchall()
    conn.close()
    result = []
    for p in potholes:
        distance = haversine(lat, lon, p['latitude'], p['longitude'])
        if distance <= 200:
            result.append({
                'latitude': p['latitude'],
                'longitude': p['longitude'],
                'image_url': url_for('pothole_image', pothole_id=p['id']),
                'description': f"Pothole (confidence: {p.get('count', 1)})",
                'distance_meters': distance
            })
    result.sort(key=lambda x: x['distance_meters'])
    return jsonify(result)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_type = request.form.get('login_type')
        if login_type == 'user':
            email = request.form.get('email')
            password = request.form.get('password')
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                user = cursor.fetchone()
                conn.close()
            except Exception as e:
                flash("Database error: " + str(e), "error")
                return redirect(url_for('login'))
            if user and user['password'] == password:
                session.update({'user_logged_in': True, 'user_email': user['email'], 'user_name': user['name']})
                session.permanent = True
                flash('Logged in successfully as user.', 'success')
                return redirect(url_for('user_dashboard'))
            else:
                flash('Invalid user credentials.', 'error')
                return redirect(url_for('register'))
        elif login_type == 'admin':
            username = request.form.get('username')
            password = request.form.get('password')
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM admins WHERE username = %s", (username,))
                admin = cursor.fetchone()
                conn.close()
            except Exception as e:
                flash("Database error: " + str(e), "error")
                return redirect(url_for('login'))
            if admin and admin['password'] == password:
                session.update({'admin_logged_in': True, 'admin_username': admin['username']})
                session.permanent = True
                flash('Logged in successfully as admin.', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid admin credentials.', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        if not name or not email or not password or not confirm_password:
            flash('Please fill all the fields.', 'error')
            return redirect(url_for('register'))
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('register'))
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                flash('User already exists with this email.', 'error')
                conn.close()
                return redirect(url_for('register'))
            cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, password))
            conn.commit()
            conn.close()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash("Database error: " + str(e), 'error')
            return redirect(url_for('register'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if not session.get('admin_logged_in'):
        flash('Please login as admin to upload.', 'error')
        return redirect(url_for('login'))
    if request.method == 'POST':
        file = request.files.get('file')
        description = request.form.get('description')
        lat = request.form.get('latitude')
        lon = request.form.get('longitude')
        if not file or file.filename == '' or not allowed_file(file.filename):
            flash('Invalid or missing file.', 'error')
            return redirect(url_for('index'))
        if not lat or not lon:
            flash('Please select a location on the map.', 'error')
            return redirect(url_for('index'))
        # Read image as binary
        image_data = file.read()
        image_mime = file.mimetype

        count, details, output_path = imageDetector.detectPotholeonImage(filepath, (float(lat), float(lon)))
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO potholes (latitude, longitude, image, image_mime, count, details, description)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (lat, lon, psycopg2.Binary(image_data), image_mime, count, json.dumps(details), description))
            conn.commit()
            conn.close()
        except Exception as e:
            flash("Database error: " + str(e), 'error')
            return redirect(url_for('index'))
        flash('Pothole uploaded successfully!', 'success')
        return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM potholes ORDER BY id DESC")
    pothole_history = cursor.fetchall()
    conn.close()
    return render_template('admin_dashboard.html', pothole_history=pothole_history)

@app.route('/submit_complaint', methods=['POST'])
def submit_complaint():
    if not session.get('user_logged_in'):
        return redirect(url_for('login'))
    name = request.form.get('name')
    email = request.form.get('email')
    message = request.form.get('message')
    if not name or not email or not message:
        flash('All fields are required.', 'error')
        return redirect(url_for('user_dashboard'))
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO complaints (user_name, user_email, message)
            VALUES (%s, %s, %s)
        """, (name, email, message))
        conn.commit()
        conn.close()
        flash('Complaint submitted successfully!', 'success')
    except Exception as e:
        flash('Error submitting complaint: ' + str(e), 'error')
    return redirect(url_for('user_dashboard'))

@app.route('/pothole_image/<int:pothole_id>')
def pothole_image(pothole_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT image, image_mime FROM potholes WHERE id = %s", (pothole_id,))
    row = cursor.fetchone()
    conn.close()
    if row and row.get('image'):
        mimetype = row.get('image_mime') or 'image/jpeg'
        return app.response_class(row['image'], mimetype=mimetype)
    else:
        return '', 404

if __name__ == '__main__':
    init_db()
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
