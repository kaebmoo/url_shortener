from app import create_app, socketio

app = create_app('default')  # ใช้ config ตามความเหมาะสม

if __name__ == '__main__':
    socketio.run(app)
