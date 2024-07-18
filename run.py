from functools import wraps
from flask import Flask, redirect, render_template, Response, request, url_for, flash, session
import time
import mediapipe as mp
import os
import cv2
import json
from functions import *

# set validasi pinggul kiri
minPinggulKiri = 105
maxPinggulKiri = 165
# set validasi lutut kiri
minLututKiri = 50
maxLututKiri = 110
# file json
fileJson = 'hasil_situp2.json'
usersJson = 'users.json'

app = Flask(__name__)
app.secret_key = 'your_secret_key'
camera = 0

def gen(file_path, realtime=False, upload=False, nama=None, waktu=None):
    if file_path == str(camera):
        file_path = int(file_path)

    cap = cv2.VideoCapture(file_path)
    situp_count = 0
    start_situp = False
    end_situp = False
    point_11 = point_23 = point_25 = point_27 = None
    start_time = time.time()
    initial_position_verified = False

    if upload:
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        video_duration = total_frames / fps
        waktu = int(video_duration)

    while True:
        success, img = cap.read()

        if not success or img is None:
            break

        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = pose.process(imgRGB)

        if results.pose_landmarks:
            mpDraw.draw_landmarks(img, results.pose_landmarks, mpPose.POSE_CONNECTIONS)

            point_11, point_23, point_25, point_27, cx, cy = draw_landmark_points(img, results.pose_landmarks.landmark)

            # Menghitung besar sudut antara tiga titik
            if 'point_11' in locals() and 'point_23' in locals() and 'point_25' in locals():
                angle_23 = calculate_angle(point_11, point_23, point_25)
                cv2.putText(img, f"{round(angle_23, 2)}", (point_23[0] + 20, point_23[1] - 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, green, 2)

            if 'point_23' in locals() and 'point_25' in locals() and 'point_27' in locals():
                angle_25 = calculate_angle(point_23, point_25, point_27)
                cv2.putText(img, f"{round(angle_25, 2)}", (point_25[0] + 20, point_25[1] - 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, green, 2)

                if not initial_position_verified:
                    # Validasi posisi awal sit up
                    if validate_initial_position(angle_23, angle_25):
                        draw_correct_position(img)
                        initial_position_verified = True
                        start_situp = True
                    else:
                        draw_wrong_position(img)
                        initial_position_verified = False
                else:
                    # Cek perubahan sudut dan hitung sit-up
                    if validate_initial_sit_up(angle_25, initial_position_verified):
                        draw_correct_position(img)
                        if angle_23 < minLututKiri:
                            end_situp = True
                        if start_situp and end_situp:
                            situp_count += 1
                            start_situp = False
                            end_situp = False
                        if angle_23 > minPinggulKiri:
                            start_situp = True
                    else:
                        draw_wrong_position(img)
                        initial_position_verified = False

            img = cv2.line(img, (cx, cy - 20), (cx, cy + 20), green, 1)
            img = cv2.line(img, (cx - 20, cy), (cx + 20, cy), green, 1)

        elapsed_time = time.time() - start_time
        if realtime:
            remaining_time = max(0, waktu - elapsed_time)
            draw_remaining_time(img, remaining_time)

            if remaining_time <= 0:
                break

        draw_count_sit_up(img, situp_count)

        ret, jpeg = cv2.imencode('.jpg', img)
        frame = jpeg.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    data_to_save = {'nama': nama, 'waktu': waktu, 'jumlah_situp': situp_count // 2}
    json_file_path = fileJson
    try:
        with open(json_file_path, 'r') as file:
            existing_data = json.load(file)
    except FileNotFoundError:
        existing_data = []

    existing_data.append(data_to_save)

    with open(json_file_path, 'w') as file:
        json.dump(existing_data, file)

    users_file_path = 'users.json'
    user_data = None
    try:
        with open(users_file_path, 'r') as file:
            users = json.load(file)
            for user in users:
                if user['username'] == nama:
                    user_data = user
                    break
    except FileNotFoundError:
        pass

    if user_data:
        json_file_path = f"{user_data['username']}.json"
        try:
            with open(json_file_path, 'r') as file:
                existing_data = json.load(file)
        except FileNotFoundError:
            existing_data = []

        existing_data.append(data_to_save)

        with open(json_file_path, 'w') as file:
            json.dump(existing_data, file)
    else:
        # Handle case where user data is not found
        print("User not found.")

def save_users(data):
    try:
        with open(usersJson, 'w') as file:
            json.dump(data, file)
    except FileNotFoundError:
        with open(usersJson, 'w') as file:
            json.dump([], file)

def load_users():
    try:
        with open(usersJson, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()
        if any(user['username'] == username for user in users):
            flash('Username already exists!')
            return redirect(url_for('register'))
        users.append({'username': username, 'password': password})
        save_users(users)
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()
        user = next((user for user in users if user['username'] == username and user['password'] == password), None)
        if user is None:
            flash('Invalid username or password!')
            return redirect(url_for('login'))
        session['user'] = username
        flash('Login successful!')
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/latihan')
@login_required
def latihan():
    return render_template('latihan.html')

@app.route('/peringkat')
@login_required
def peringkat():
    with open(fileJson, 'r') as file:
        users = json.load(file)
    return render_template('peringkat.html', users=users, convert_to_hms=convert_to_hms)

@app.route('/data')
@login_required
def data():
    user_file_path = f"{session['user']}.json"
    try:
        with open(user_file_path, 'r') as file:
            records = json.load(file)
    except FileNotFoundError:
        records = []

    return render_template('data.html', records=records, convert_to_hms=convert_to_hms)

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    nama = request.form['nama']
    if file.filename == '':
        return redirect(request.url)

    old_file_path = request.args.get('file_path', None)

    if old_file_path:
        try:
            os.remove(old_file_path)
        except OSError as e:
            print(f"Error deleting old file: {e}")

    file_path = "temp_video.mp4"
    file.save(file_path)

    return {'file_path': file_path, 'nama': nama}

@app.route('/video_feed_upload')
@login_required
def video_feed_upload():
    file_path = request.args.get('file_path', camera)
    nama = request.args.get('nama', 'Anonymous')
    return Response(gen(file_path, upload=True, nama=nama), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed')
@login_required
def video_feed():
    return Response(gen(camera), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed_realtime')
@login_required
def video_feed_realtime():
    nama = request.args.get('nama', 'Anonymous')
    waktu = request.args.get('waktu', 60)
    return Response(gen(camera, realtime=True, nama=nama, waktu=int(waktu)), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True)
