# Flask Web Interface for Pothole Detection using YOLOv4-tiny

from flask import Flask, request, render_template, redirect, url_for, jsonify
import os
from werkzeug.utils import secure_filename
import imageDetector, videoDetector  # Use your existing detector logic with inference wrappers

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'mp4'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return "Invalid file type"

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    if filename.endswith(('.jpg', '.jpeg', '.png')):
        count, details = imageDetector.detectPotholeonImage(file_path)
        return render_template("result.html", count=count, details=details, file_path=file_path)

    elif filename.endswith('.mp4'):
        output_video_path, count, details = videoDetector.detectPotholeonVideo(file_path)
        return render_template("result_video.html", count=count, details=details, video_path=output_video_path)

    return "Unsupported file format"

if __name__ == '__main__':
    app.run(debug=True)
