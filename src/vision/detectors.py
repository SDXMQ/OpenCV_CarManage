import os
import logging

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np

from .face_recognizer import download_model

logger = logging.getLogger(__name__)


class DrowsinessDetector:
    """MediaPipe Tasks API를 사용하여 양안 EAR(Eye Aspect Ratio) 및 얼굴 랜드마크를 추출하는 클래스."""
    
    # MediaPipe Face Landmarker 랜드마크 인덱스 (눈)
    _LEFT_EYE = [33, 160, 158, 133, 153, 144]
    _RIGHT_EYE = [362, 385, 387, 263, 373, 380]

    # MediaPipe Face Landmarker 랜드마크 인덱스 (입 - MAR용)
    _MOUTH = [78, 81, 311, 308, 402, 178]

    _MODEL_FILE = os.path.join(os.path.dirname(__file__), "face_landmarker.task")
    _MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"

    def __init__(self):
        self._detector = None
        self._load_model()

    def _load_model(self):
        """로컬 Face Landmarker 모델 파일을 로드한다. 파일이 없으면 다운로드한다."""
        if not os.path.exists(self._MODEL_FILE):
            try:
                download_model(self._MODEL_URL, self._MODEL_FILE)
            except Exception as e:
                logger.error("얼굴 랜드마크 모델 다운로드 실패: %s", e)
                raise FileNotFoundError(
                    f"얼굴 랜드마크 모델 파일을 찾을 수 없고 다운로드에 실패했습니다: {self._MODEL_FILE}"
                )

        try:
            with open(self._MODEL_FILE, 'rb') as f:
                model_data = f.read()
            base_options = python.BaseOptions(model_asset_buffer=model_data)
            options = vision.FaceLandmarkerOptions(
                base_options=base_options,
                output_face_blendshapes=False,
                output_facial_transformation_matrixes=False,
                num_faces=4  # 최대 4개 얼굴 검출 허용
            )
            self._detector = vision.FaceLandmarker.create_from_options(options)
            logger.info("MediaPipe Tasks 얼굴 분석 엔진 활성화 완료 (최대 4인).")
        except (OSError, RuntimeError) as e:
            logger.error("MediaPipe 얼굴 분석 엔진 초기화 실패: %s", e)

    def process(self, frame_rgb):
        """RGB 프레임을 입력받아 단일(첫 번째) 얼굴의 (EAR, MAR, landmarks)를 반환한다 (하위 호환용)."""
        multi_results = self.process_multi(frame_rgb)
        if multi_results:
            ear, mar, landmarks, _ = multi_results[0]
            return ear, mar, landmarks
        return 0.0, 0.0, None

    def process_multi(self, frame_rgb):
        """RGB 프레임을 입력받아 감지된 모든 얼굴의 [(ear, mar, landmarks, bbox), ...] 리스트를 반환한다."""
        if self._detector is None:
            return []

        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        results = []
        
        try:
            detection_result = self._detector.detect(mp_image)
            
            if detection_result.face_landmarks:
                h, w = frame_rgb.shape[:2]
                for landmarks in detection_result.face_landmarks:
                    ear = self._compute_ear(landmarks, w, h)
                    mar = self._compute_mar(landmarks, w, h)
                    
                    # 랜드마크로부터 바운딩 박스(xmin, ymin, xmax, ymax) 추출
                    x_coords = [lm.x * w for lm in landmarks]
                    y_coords = [lm.y * h for lm in landmarks]
                    
                    xmin, xmax = max(0, int(min(x_coords))), min(w, int(max(x_coords)))
                    ymin, ymax = max(0, int(min(y_coords))), min(h, int(max(y_coords)))
                    
                    bbox = (xmin, ymin, xmax, ymax)
                    results.append((ear, mar, landmarks, bbox))
        except (RuntimeError, ValueError) as e:
            logger.warning("다중 얼굴 랜드마크 검출 중 오류 발생: %s", e)
            
        return results

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

    _MODEL_FILE = os.path.join(os.path.dirname(__file__), "emotion_ferplus.onnx")
    _MODEL_URL = "https://github.com/onnx/models/raw/main/validated/vision/body_analysis/emotion_ferplus/model/emotion-ferplus-8.onnx"
    
    # FER+ 감정 카테고리 매핑 (neutral, happiness, surprise, sadness, anger, disgust, fear, contempt)
    _EMOTIONS = ["neutral", "happy", "surprise", "sad", "angry", "disgust", "fear", "neutral"]

    def __init__(self):
        self._net = None
        self._load_model()

    def _load_model(self):
        """로컬 ONNX 모델 파일을 로드한다. 파일이 없으면 다운로드한다."""
        if not os.path.exists(self._MODEL_FILE):
            try:
                download_model(self._MODEL_URL, self._MODEL_FILE)
            except Exception as e:
                logger.error("감정 인식 모델 다운로드 실패: %s", e)
                raise FileNotFoundError(
                    f"감정 인식 모델 파일을 찾을 수 없고 다운로드에 실패했습니다: {self._MODEL_FILE}"
                )

        try:
            model_data = np.fromfile(self._MODEL_FILE, dtype=np.uint8)
            self._net = cv2.dnn.readNetFromONNX(model_data)
            logger.info("ONNX 감정 분석 엔진 활성화 완료.")
        except cv2.error as e:
            logger.error("ONNX 모델 로딩 중 오류 발생: %s", e)

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
        except cv2.error as e:
            logger.warning("감정 분석 실패: %s", e)
            return {"dominant": "neutral", "scores": {}}
