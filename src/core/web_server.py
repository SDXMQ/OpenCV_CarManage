"""
web_server.py - 모바일 카메라 스트리밍을 위한 백그라운드 Flask & ngrok 서버
"""

import logging
import threading
import os
import cv2
import numpy as np
from flask import Flask, render_template, request, jsonify
from pyngrok import ngrok, exception as ngrok_exceptions
from dotenv import load_dotenv
import socket

# .env 로드
load_dotenv()

def get_local_ip():
    try:
        # 외부 DNS 서버 연결을 통해 실제 외부 인터페이스 IP를 식별
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder="../ui/templates")

# Flask Werkzeug 자체 로그(개발 서버 경고 및 매 프레임 접속 로그) 출력 억제
import logging
logging.getLogger('werkzeug').setLevel(logging.ERROR)

# 최신 프레임을 저장할 글로벌 버퍼
_latest_frame_lock = threading.Lock()
_latest_frame = None

@app.route('/mobile')
def mobile_view():
    return render_template("mobile_stream.html")

@app.route('/upload_frame', methods=['POST'])
def upload_frame():
    global _latest_frame
    try:
        file = request.files['image']
        npimg = np.frombuffer(file.read(), np.uint8)
        # 이미지 디코딩
        img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
        if img is not None:
            with _latest_frame_lock:
                _latest_frame = img
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        logger.error(f"Frame upload error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

class MobileStreamServer:
    def __init__(self, port=5000):
        self.port = port
        self._flask_thread = None
        self.public_url = None
        self._running = False
        self._ngrok_tunnel = None

    def start(self):
        if self._running:
            return True, self.public_url
            
        self._running = True
        
        # ngrok 시작 시도
        try:
            # 안전장치: 백그라운드에 잔존하는 구 버전의 세션 및 충돌 요소를 모두 정리하고 시작
            try:
                ngrok.kill()
            except Exception:
                pass

            auth_token = os.getenv("NGROK_AUTHTOKEN")
            if auth_token:
                ngrok.set_auth_token(auth_token)
                
            self._ngrok_tunnel = ngrok.connect(self.port, bind_tls=True)
            self.public_url = self._ngrok_tunnel.public_url
            logger.info(f"ngrok 터널 생성 완료: {self.public_url}")
        except ngrok_exceptions.PyngrokNgrokError as e:
            logger.warning(f"ngrok 실행 실패 (오프라인이거나 토큰 오류): {e}")
            self.public_url = f"http://{get_local_ip()}:{self.port}"
        except Exception as e:
            logger.error(f"예기치 않은 터널링 오류: {e}")
            self.public_url = f"http://{get_local_ip()}:{self.port}"
            
        # Flask 서버 스레드 시작
        # 개발용 서버이므로 debug=False, use_reloader=False 설정
        self._flask_thread = threading.Thread(
            target=lambda: app.run(host='0.0.0.0', port=self.port, debug=False, use_reloader=False),
            daemon=True
        )
        self._flask_thread.start()
        logger.info(f"Flask 스트리밍 서버가 포트 {self.port}에서 시작되었습니다.")
        
        return self._ngrok_tunnel is not None, self.public_url

    def stop(self):
        self._running = False
        if self._ngrok_tunnel:
            try:
                ngrok.disconnect(self._ngrok_tunnel.public_url)
                ngrok.kill()
            except Exception as e:
                logger.error(f"ngrok 종료 중 오류: {e}")
        self._ngrok_tunnel = None
        self.public_url = None
        # Flask 개발 서버는 데몬 스레드이므로 메인 프로세스 종료 시 자동 종료됨.
        # 명시적 종료가 필요하다면 werkzeug shutdown 함수 사용해야 함.

    def get_latest_frame(self):
        global _latest_frame
        with _latest_frame_lock:
            if _latest_frame is not None:
                return _latest_frame.copy()
            return None
