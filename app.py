from flask import Flask, render_template, Response
from flask_socketio import SocketIO
import gps
import cv2

app = Flask(__name__)
socketio = SocketIO(app)

# Initialize GPS session
session = gps.gps(mode=gps.WATCH_ENABLE)

# Initialize webcam
camera = cv2.VideoCapture(0)  # Use default camera (USB Webcam)

@app.route('/')
def index():
    return render_template('index.html')

def get_gps_data():
    while True:
        report = session.next()
        if report['class'] == 'TPV':
            latitude = getattr(report, 'lat', 0.0)
            longitude = getattr(report, 'lon', 0.0)
            socketio.emit('gps_data', {'lat': latitude, 'lon': longitude})
            socketio.sleep(1)

def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@socketio.on('connect')
def handle_connect():
    print("Client connected!")

if __name__ == '__main__':
    socketio.start_background_task(target=get_gps_data)  # Run GPS data in the background
    socketio.run(app, host='0.0.0.0', port=5000)  # Accessible from anywhere

