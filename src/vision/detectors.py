"""
detectors.py - 졸음 및 감정 분석 모듈 (AI)
Python 3.14 호환을 위해 mediapipe.tasks API와 OpenCV DNN 모듈을 활용합니다.
"""

import os
import urllib.request
import ssl
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np


class DrowsinessDetector:
    """MediaPipe Tasks API를 사용하여 양안 EAR(Eye Aspect Ratio) 및 얼굴 랜드마크를 추출하는 클래스."""
    
    # MediaPipe Face Landmarker 랜드마크 인덱스 (눈)
    _LEFT_EYE = [33, 160, 158, 133, 153, 144]
    _RIGHT_EYE = [362, 385, 387, 263, 373, 380]

    # MediaPipe Face Landmarker 랜드마크 인덱스 (입 - MAR용)
    _MOUTH = [78, 81, 311, 308, 402, 178]

    _MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
    _MODEL_FILE = os.path.join(os.path.dirname(__file__), "face_landmarker.task")

    def __init__(self):
        self._detector = None
        self._load_model()

    def _load_model(self):
        """Face Landmarker 모델 파일을 검사하고 없으면 다운로드한 뒤 로드한다."""
        if not os.path.exists(self._MODEL_FILE):
            print(f"[SEAVS] 얼굴 랜드마크 모델이 없습니다. 다운로드 중 (약 5.6MB): {self._MODEL_URL}")
            try:
                context = ssl._create_unverified_context()
                with urllib.request.urlopen(self._MODEL_URL, context=context) as response, open(self._MODEL_FILE, 'wb') as out_file:
                    out_file.write(response.read())
                print("[SEAVS] 랜드마크 모델 다운로드 성공.")
            except Exception as e:
                print(f"[SEAVS] 랜드마크 모델 다운로드 실패: {e}")
                return

        try:
            with open(self._MODEL_FILE, 'rb') as f:
                model_data = f.read()
            base_options = python.BaseOptions(model_asset_buffer=model_data)
            options = vision.FaceLandmarkerOptions(
                base_options=base_options,
                output_face_blendshapes=False,
                output_facial_transformation_matrixes=False,
                num_faces=1
            )
            self._detector = vision.FaceLandmarker.create_from_options(options)
            print("[SEAVS] MediaPipe Tasks 얼굴 분석 엔진 활성화 완료.")
        except Exception as e:
            print(f"[SEAVS] MediaPipe 얼굴 분석 엔진 초기화 실패: {e}")

    def process(self, frame_rgb):
        """RGB 프레임을 입력받아 (EAR, MAR, landmarks)를 반환한다."""
        if self._detector is None:
            return 0.0, 0.0, None

        # mp.Image 형식으로 변환
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        
        try:
            detection_result = self._detector.detect(mp_image)
            
            if detection_result.face_landmarks:
                landmarks = detection_result.face_landmarks[0]
                h, w = frame_rgb.shape[:2]
                ear = self._compute_ear(landmarks, w, h)
                mar = self._compute_mar(landmarks, w, h)
                return ear, mar, landmarks
        except Exception as e:
            print(f"[SEAVS] 얼굴 랜드마크 검출 중 오류 발생: {e}")
            
        return 0.0, 0.0, None

    def _compute_ear(self, landmarks, w, h):
        left_ear = self._aspect_ratio(landmarks, self._LEFT_EYE, w, h)
        right_ear = self._aspect_ratio(landmarks, self._RIGHT_EYE, w, h)
        return (left_ear + right_ear) / 2.0

    def _compute_mar(self, landmarks, w, h):
        return self._aspect_ratio(landmarks, self._MOUTH, w, h)

    @staticmethod
    def _aspect_ratio(landmarks, indices, w, h):
        pts = []
        for idx in indices:
            lm = landmarks[idx]
            pts.append(np.array([lm.x * w, lm.y * h]))

        p1, p2, p3, p4, p5, p6 = pts
        vertical1 = np.linalg.norm(p2 - p6)
        vertical2 = np.linalg.norm(p3 - p5)
        horizontal = np.linalg.norm(p1 - p4)
        if horizontal == 0:
            return 0.0
        return (vertical1 + vertical2) / (2.0 * horizontal)


class EmotionDetector:
    """OpenCV DNN 모듈로 ONNX 모델을 로드하여 감정을 분석하는 클래스 (TensorFlow 미사용)."""

    # ONNX 모델 다운로드 정보
    _MODEL_URL = "https://github.com/onnx/models/raw/main/validated/vision/body_analysis/emotion_ferplus/model/emotion-ferplus-8.onnx"
    _MODEL_FILE = os.path.join(os.path.dirname(__file__), "emotion_ferplus.onnx")
    
    # FER+ 감정 카테고리 매핑 (neutral, happiness, surprise, sadness, anger, disgust, fear, contempt)
    _EMOTIONS = ["neutral", "happy", "surprise", "sad", "angry", "disgust", "fear", "neutral"]

    def __init__(self):
        self._net = None
        self._load_model()

    def _load_model(self):
        """로컬에서 ONNX 모델을 찾아보고 없으면 다운로드한 뒤 로드한다."""
        if not os.path.exists(self._MODEL_FILE):
            print(f"[SEAVS] 감정 인식 모델이 없습니다. 다운로드 중 (약 6.4MB): {self._MODEL_URL}")
            try:
                context = ssl._create_unverified_context()
                with urllib.request.urlopen(self._MODEL_URL, context=context) as response, open(self._MODEL_FILE, 'wb') as out_file:
                    out_file.write(response.read())
                print("[SEAVS] 모델 다운로드 성공.")
            except Exception as e:
                print(f"[SEAVS] 모델 다운로드 실패: {e}")
                return

        try:
            model_data = np.fromfile(self._MODEL_FILE, dtype=np.uint8)
            self._net = cv2.dnn.readNetFromONNX(model_data)
            print("[SEAVS] ONNX 감정 분석 엔진 활성화 완료.")
        except Exception as e:
            print(f"[SEAVS] ONNX 모델 로딩 중 오류 발생: {e}")

    def analyze(self, frame_rgb, landmarks):
        """얼굴 랜드마크 정보를 이용하여 얼굴 영역을 크롭하고 감정을 분석한다."""
        if self._net is None or landmarks is None:
            return {"dominant": "neutral", "scores": {}}

        h, w = frame_rgb.shape[:2]
        
        # 랜드마크 전체의 최솟값/최댓값으로 바운딩 박스(얼굴 크롭 영역) 획득
        x_coords = [lm.x * w for lm in landmarks]
        y_coords = [lm.y * h for lm in landmarks]
        
        x_min, x_max = max(0, int(min(x_coords))), min(w, int(max(x_coords)))
        y_min, y_max = max(0, int(min(y_coords))), min(h, int(max(y_coords)))
        
        # 유효한 크롭 범위 검증
        if (x_max - x_min) < 10 or (y_max - y_min) < 10:
            return {"dominant": "neutral", "scores": {}}
            
        # 얼굴 크롭 및 전처리 (64x64 흑백 이미지)
        face_crop = frame_rgb[y_min:y_max, x_min:x_max]
        face_gray = cv2.cvtColor(face_crop, cv2.COLOR_RGB2GRAY)
        face_gray = cv2.resize(face_gray, (64, 64))
        
        # ONNX Blob 생성
        blob = cv2.dnn.blobFromImage(face_gray, scalefactor=1.0, size=(64, 64), mean=0, swapRB=False, crop=False)
        
        try:
            self._net.setInput(blob)
            preds = self._net.forward()
            
            # Softmax 기법으로 신뢰 지수 생성
            exp_preds = np.exp(preds[0] - np.max(preds[0]))
            probs = exp_preds / np.sum(exp_preds)
            
            # 점수 및 Dominant 감정 매핑
            scores = {}
            for i, emo_name in enumerate(self._EMOTIONS):
                scores[emo_name] = scores.get(emo_name, 0.0) + (probs[i] * 100)
                
            dominant = max(scores, key=scores.get)
            return {
                "dominant": dominant,
                "scores": scores
            }
        except Exception as e:
            print(f"[SEAVS] 감정 분석 실패: {e}")
            return {"dominant": "neutral", "scores": {}}
