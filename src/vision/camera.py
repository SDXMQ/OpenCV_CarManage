"""
camera.py - 웹캠 입출력 및 AI 분석 오케스트레이션 모듈
순수 캡처 스레드 역할을 하며 분석은 detectors.py에, 그리기는 visualizer.py에 위임한다.
"""

import cv2
import threading
import time
import numpy as np

from .detectors import DrowsinessDetector, EmotionDetector
from .visualizer import FrameVisualizer
from .face_recognizer import FaceRecognizer


def compute_iou(boxA, boxB):
    """두 바운딩 박스 간의 IoU(Intersection over Union)를 계산합니다."""
    if not boxA or not boxB:
        return 0.0
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0, xB - xA) * max(0, yB - yA)
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

    unionArea = float(boxAArea + boxBArea - interArea)
    if unionArea == 0:
        return 0.0
    return interArea / unionArea


class VideoCamera:
    def __init__(self, device_index=0, mirror_camera=False, ear_threshold=0.22, drowsy_seconds=3.0, emotion_interval=1.0):
        self._device_index = device_index
        self.mirror_camera = mirror_camera
        self._base_ear_threshold = ear_threshold  # 기본 임계값
        self._current_ear_threshold = ear_threshold  # 프로필 보정된 임계값
        self._drowsy_seconds = drowsy_seconds
        self._emotion_interval = emotion_interval

        self._cap = None
        self._running = False
        self._paused = False
        self._lock = threading.Lock()

        # 분석 모듈 연동
        self._drowsiness_detector = DrowsinessDetector()
        self._emotion_detector = EmotionDetector()
        self._face_recognizer = FaceRecognizer()
        
        # 상태 관리
        self._current_frame = None       # 원본이 아닌 '그려진' 프레임
        self._ear_value = 0.0
        self._mar_value = 0.0
        self._is_drowsy = False
        self._is_yawning = False
        self._drowsy_start = None
        self._yawn_start = None
        self._emotion = {"dominant": "neutral", "scores": {}}

        self._capture_thread = None
        self._emotion_thread = None
        self._latest_rgb_for_emotion = None
        self._latest_landmarks = None  # 감정 분석용 랜드마크 데이터 저장

        # 얼굴 추적 및 프로필 데이터 변수
        self._tracked_bbox = None       # 이전 프레임의 바운딩 박스 (xmin, ymin, xmax, ymax)
        self._active_profile_data = {}  # 활성화된 프로필 데이터

        # 캘리브레이션(프로필 보정) 변수
        self._calibrating = False
        self._calib_frames_needed = 30
        self._calib_data = []
        self._on_calib_done = None

    def set_active_profile(self, profile_data):
        """프로필 데이터를 받아 눈 크기(EAR) 임계값을 동적으로 조절한다."""
        with self._lock:
            self._active_profile_data = profile_data or {}
            base_ear = self._active_profile_data.get("base_ear", 0.28)
            # 기준(0.28) 대비 비율로 임계값 스케일링
            scale = min(1.2, max(0.6, base_ear / 0.28))
            self._current_ear_threshold = self._base_ear_threshold * scale

    def start_calibration(self, frames=30, on_done=None):
        """캘리브레이션 캡처 모드를 시작한다."""
        with self._lock:
            self._calibrating = True
            self._calib_frames_needed = frames
            self._calib_data = []
            self._on_calib_done = on_done

    @property
    def ear_value(self):
        with self._lock:
            return self._ear_value

    @property
    def mar_value(self):
        with self._lock:
            return self._mar_value

    @property
    def is_drowsy(self):
        with self._lock:
            return self._is_drowsy

    @property
    def is_yawning(self):
        with self._lock:
            return self._is_yawning

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
            self._is_yawning = False
            self._ear_value = 0.0
            self._mar_value = 0.0
            self._drowsy_start = None
            self._yawn_start = None
            self._emotion = {"dominant": "neutral", "scores": {}}
            self._latest_landmarks = None
            self._tracked_bbox = None

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
        """프레임을 캡처하고 다중 얼굴 중 타겟을 트래킹 및 분석한다."""
        while self._running:
            if self._paused:
                time.sleep(0.05)
                continue

            ret, frame = self._cap.read()
            if not ret:
                time.sleep(0.01)
                continue

            if self.mirror_camera:
                frame = cv2.flip(frame, 1)

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self._latest_rgb_for_emotion = rgb.copy()

            # 다중 얼굴 검출
            faces = self._drowsiness_detector.process_multi(rgb)
            
            now = time.time()
            with self._lock:
                if not faces:
                    # 얼굴이 검출되지 않는 경우 상태 리셋
                    self._tracked_bbox = None
                    self._ear_value = 0.0
                    self._mar_value = 0.0
                    self._latest_landmarks = None
                    self._is_drowsy = False
                    self._is_yawning = False
                    self._drowsy_start = None
                    self._yawn_start = None
                    
                    # 빈 화면 오버레이
                    drawn_frame = FrameVisualizer.draw_overlays(
                        frame.copy(),
                        0.0, 0.0,
                        self._emotion,
                        False, False,
                        all_bboxes=[],
                        target_bbox=None
                    )
                    self._current_frame = drawn_frame
                    time.sleep(0.01)
                    continue

                # 1. 감지된 모든 얼굴의 임베딩 추출
                face_embeddings = []
                for _, _, _, bbox in faces:
                    emb = None
                    if self._face_recognizer.is_loaded():
                        emb = self._face_recognizer.get_embedding(frame, bbox)
                    face_embeddings.append(emb)

                # 2. 타겟 매칭 수행
                target_idx = -1
                
                # 우선순위 1: 프로필 얼굴 매칭
                profile_emb = self._active_profile_data.get("face_embedding")
                if profile_emb is not None and self._face_recognizer.is_loaded():
                    profile_emb = np.array(profile_emb)
                    best_sim = -1.0
                    for idx, emb in enumerate(face_embeddings):
                        if emb is not None:
                            sim = FaceRecognizer.compute_similarity(emb, profile_emb)
                            if sim > best_sim:
                                best_sim = sim
                                target_idx = idx
                    # 프로필 매칭 임계값 0.6 이상이어야 인정
                    if best_sim < 0.60:
                        target_idx = -1

                # 우선순위 2: 이전 프레임 트래킹 매칭 (IoU)
                if target_idx == -1 and self._tracked_bbox is not None:
                    best_iou = -1.0
                    for idx, (_, _, _, bbox) in enumerate(faces):
                        iou = compute_iou(bbox, self._tracked_bbox)
                        if iou > best_iou:
                            best_iou = iou
                            target_idx = idx
                    # IoU 임계값 0.3 이상이어야 트래킹 유지
                    if best_iou < 0.30:
                        target_idx = -1

                # 우선순위 3: 매칭 실패 시 화면 중앙과 가장 가까운 얼굴 매칭
                if target_idx == -1:
                    h, w = frame.shape[:2]
                    cx, cy = w / 2, h / 2
                    min_dist = float('inf')
                    for idx, (_, _, _, bbox) in enumerate(faces):
                        bcx = (bbox[0] + bbox[2]) / 2
                        bcy = (bbox[1] + bbox[3]) / 2
                        dist = (bcx - cx)**2 + (bcy - cy)**2
                        if dist < min_dist:
                            min_dist = dist
                            target_idx = idx

                # 3. 매칭된 타겟 정보 갱신 및 상태 업데이트
                target_face = faces[target_idx]
                target_emb = face_embeddings[target_idx]
                ear, mar, landmarks, bbox = target_face
                
                self._tracked_bbox = bbox
                self._ear_value = ear
                self._mar_value = mar
                self._latest_landmarks = landmarks

                # 캘리브레이션 데이터 수집
                if self._calibrating:
                    # 캘리브레이션 데이터에 임베딩 벡터 리스트로 추가
                    emb_list = target_emb.tolist() if target_emb is not None else None
                    self._calib_data.append({
                        "ear": ear,
                        "mar": mar,
                        "emotion": self._emotion.get("scores", {}),
                        "face_embedding": emb_list
                    })
                    if len(self._calib_data) >= self._calib_frames_needed:
                        self._calibrating = False
                        if self._on_calib_done:
                            threading.Thread(target=self._on_calib_done, args=(self._calib_data,)).start()

                # 졸음 판정 (EAR 기반, 프로필 보정된 임계값 사용)
                if ear > 0 and ear < self._current_ear_threshold:
                    if self._drowsy_start is None:
                        self._drowsy_start = now
                    elif now - self._drowsy_start >= self._drowsy_seconds:
                        self._is_drowsy = True
                else:
                    self._drowsy_start = None
                    self._is_drowsy = False

                # 하품 판정 (MAR 기반)
                if mar > 0.50:
                    if self._yawn_start is None:
                        self._yawn_start = now
                    elif now - self._yawn_start >= 1.0:
                        self._is_yawning = True
                else:
                    self._yawn_start = None
                    self._is_yawning = False

                # 오버레이 및 다중 사각형 그리기
                all_bboxes = [face[3] for face in faces]
                drawn_frame = FrameVisualizer.draw_overlays(
                    frame.copy(), 
                    self._ear_value,
                    self._mar_value,
                    self._emotion, 
                    self._is_drowsy,
                    self._is_yawning,
                    all_bboxes=all_bboxes,
                    target_bbox=self._tracked_bbox
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
