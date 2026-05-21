"""
camera.py - 웹캠 입출력 및 AI 분석 오케스트레이션 모듈
순수 캡처 스레드 역할을 하며 분석은 detectors.py에, 그리기는 visualizer.py에 위임한다.
"""

import cv2
import threading
import time

from .detectors import DrowsinessDetector, EmotionDetector
from .visualizer import FrameVisualizer


class VideoCamera:
    def __init__(self, device_index=0, ear_threshold=0.22, drowsy_seconds=3.0, emotion_interval=1.0):
        self._device_index = device_index
        self._ear_threshold = ear_threshold
        self._drowsy_seconds = drowsy_seconds
        self._emotion_interval = emotion_interval

        self._cap = None
        self._running = False
        self._paused = False
        self._lock = threading.Lock()

        # 분석 모듈 연동
        self._drowsiness_detector = DrowsinessDetector()
        self._emotion_detector = EmotionDetector()
        
        # 상태 관리
        self._current_frame = None       # 원본이 아닌 '그려진' 프레임
        self._ear_value = 0.0
        self._is_drowsy = False
        self._drowsy_start = None
        self._emotion = {"dominant": "neutral", "scores": {}}

        # 스레드 버퍼
        self._capture_thread = None
        self._emotion_thread = None
        self._latest_rgb_for_emotion = None
        self._latest_landmarks = None  # 감정 분석용 랜드마크 데이터 저장

    @property
    def ear_value(self):
        with self._lock:
            return self._ear_value

    @property
    def is_drowsy(self):
        with self._lock:
            return self._is_drowsy

    @property
    def emotion(self):
        with self._lock:
            return self._emotion.copy()

    def start(self):
        if self._running:
            return
        self._cap = cv2.VideoCapture(self._device_index, cv2.CAP_DSHOW)
        if not self._cap.isOpened():
            raise RuntimeError(f"카메라 장치({self._device_index})를 열 수 없습니다.")
        self._running = True
        self._paused = False

        self._capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._capture_thread.start()

        self._emotion_thread = threading.Thread(target=self._emotion_loop, daemon=True)
        self._emotion_thread.start()

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def stop(self):
        self._running = False
        self._paused = False
        if self._capture_thread:
            self._capture_thread.join(timeout=2)
        if self._emotion_thread:
            self._emotion_thread.join(timeout=2)
        if self._cap and self._cap.isOpened():
            self._cap.release()
        self._cap = None
        with self._lock:
            self._current_frame = None
            self._is_drowsy = False
            self._ear_value = 0.0
            self._drowsy_start = None
            self._emotion = {"dominant": "neutral", "scores": {}}
            self._latest_landmarks = None

    def change_device(self, device_index):
        was_running = self._running
        if was_running:
            self.stop()
        self._device_index = device_index
        if was_running:
            self.start()

    def get_frame_rgb(self):
        with self._lock:
            if self._current_frame is not None:
                return cv2.cvtColor(self._current_frame, cv2.COLOR_BGR2RGB)
            return None

    def _capture_loop(self):
        """프레임을 캡처하고 분석(Drowsiness) 및 그리기(Visualizer)를 호출한다."""
        while self._running:
            if self._paused:
                time.sleep(0.05)
                continue

            ret, frame = self._cap.read()
            if not ret:
                time.sleep(0.01)
                continue

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self._latest_rgb_for_emotion = rgb.copy()

            # EAR 계산 (detectors)
            ear, landmarks = self._drowsiness_detector.process(rgb)
            self._latest_landmarks = landmarks

            now = time.time()
            with self._lock:
                self._ear_value = ear
                if ear > 0 and ear < self._ear_threshold:
                    if self._drowsy_start is None:
                        self._drowsy_start = now
                    elif now - self._drowsy_start >= self._drowsy_seconds:
                        self._is_drowsy = True
                else:
                    self._drowsy_start = None
                    self._is_drowsy = False

                # 오버레이 그리기 (visualizer)
                drawn_frame = FrameVisualizer.draw_overlays(
                    frame.copy(), 
                    self._ear_value, 
                    self._emotion, 
                    self._is_drowsy
                )
                self._current_frame = drawn_frame

            time.sleep(0.01)

    def _emotion_loop(self):
        """백그라운드에서 감정 분석(EmotionDetector)을 호출한다."""
        while self._running:
            if self._paused or self._latest_rgb_for_emotion is None or self._latest_landmarks is None:
                time.sleep(0.1)
                continue

            frame_rgb = self._latest_rgb_for_emotion
            landmarks = self._latest_landmarks
            emotion_data = self._emotion_detector.analyze(frame_rgb, landmarks)
            
            with self._lock:
                self._emotion = emotion_data

            time.sleep(self._emotion_interval)
