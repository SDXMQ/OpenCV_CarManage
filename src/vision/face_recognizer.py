"""
face_recognizer.py - 딥러닝 기반 얼굴 인식 (SFace) 모듈
최초 1회 모델 다운로드 및 오프라인 구동을 지원하며, 128차원 얼굴 임베딩을 추출하고 코사인 유사도를 계산합니다.
"""

import os
import urllib.request
import ssl
import logging
import cv2
import numpy as np

logger = logging.getLogger(__name__)

# SFace ONNX 모델 정보
MODEL_URL = "https://huggingface.co/opencv/face_recognition_sface/resolve/main/face_recognition_sface_2021dec.onnx"
MODEL_FILENAME = "face_recognition_sface_2021dec.onnx"
MODEL_PATH = os.path.join(os.path.dirname(__file__), MODEL_FILENAME)


def download_model(url, save_path):
    """지정한 URL에서 모델 가중치 파일을 다운로드합니다."""
    logger.info("얼굴 인식 SFace 모델 다운로드 시작: %s -> %s", url, save_path)
    
    # SSL 인증서 문제를 우회하기 위한 안전한 컨텍스트 정의 (인증서 에러 방지 fallback)
    ctx = ssl.create_default_context()
    try:
        # 먼저 안전한 SSL 컨텍스트로 시도
        with urllib.request.urlopen(url, context=ctx, timeout=30) as response, open(save_path, 'wb') as out_file:
            out_file.write(response.read())
        logger.info("SFace 모델 다운로드 완료.")
    except Exception as e:
        logger.warning("기본 SSL 연결 실패, 비검증 컨텍스트로 재시도합니다: %s", e)
        try:
            unverified_ctx = ssl._create_unverified_context()
            with urllib.request.urlopen(url, context=unverified_ctx, timeout=30) as response, open(save_path, 'wb') as out_file:
                out_file.write(response.read())
            logger.info("비검증 컨텍스트를 통한 SFace 모델 다운로드 완료.")
        except Exception as e2:
            logger.error("SFace 모델 다운로드 실패: %s", e2)
            if os.path.exists(save_path):
                os.remove(save_path)
            raise e2


class FaceRecognizer:
    """OpenCV DNN 모듈을 사용하여 SFace 기반 얼굴 임베딩을 추출하고 유사도를 판단하는 클래스."""
    
    def __init__(self):
        self._net = None
        self._load_model()

    def _load_model(self):
        """SFace 모델 파일을 로드합니다. 파일이 없는 경우 다운로드합니다."""
        if not os.path.exists(MODEL_PATH):
            try:
                download_model(MODEL_URL, MODEL_PATH)
            except Exception as e:
                logger.error("얼굴 인식 모델 로딩 실패 (다운로드 불가): %s", e)
                return

        try:
            # OpenCV DNN을 사용하여 ONNX 로드
            model_data = np.fromfile(MODEL_PATH, dtype=np.uint8)
            self._net = cv2.dnn.readNetFromONNX(model_data)
            logger.info("SFace 얼굴 인식 DNN 모듈 로드 완료.")
        except cv2.error as e:
            logger.error("SFace ONNX 모델 파일 읽기 실패: %s", e)

    def is_loaded(self):
        return self._net is not None

    def get_embedding(self, frame_bgr, bounding_box):
        """
        주어진 BGR 이미지와 바운딩 박스로부터 128차원 얼굴 임베딩을 추출합니다.
        bounding_box: (xmin, ymin, xmax, ymax) 형식 (정수 픽셀값)
        """
        if self._net is None:
            return None

        h, w = frame_bgr.shape[:2]
        xmin, ymin, xmax, ymax = bounding_box
        
        # 바운딩 박스 유효성 검사 및 정방형 크롭 확보 (SFace는 112x112 정방형을 선호함)
        xmin = max(0, int(xmin))
        ymin = max(0, int(ymin))
        xmax = min(w, int(xmax))
        ymax = min(h, int(ymax))

        box_w = xmax - xmin
        box_h = ymax - ymin
        if box_w < 10 or box_h < 10:
            return None

        # 얼굴 크롭 및 112x112 리사이즈
        face_img = frame_bgr[ymin:ymax, xmin:xmax]
        face_img = cv2.resize(face_img, (112, 112))

        # Blob 생성 (SFace 전처리는 swapRB=False로 BGR 형태 유지, scale=1.0)
        blob = cv2.dnn.blobFromImage(face_img, scalefactor=1.0, size=(112, 112), mean=(0, 0, 0), swapRB=False, crop=False)
        
        try:
            self._net.setInput(blob)
            feature = self._net.forward()  # shape: (1, 128)
            # L2 정규화 수행
            norm = np.linalg.norm(feature)
            if norm > 0:
                feature = feature / norm
            return feature[0]
        except cv2.error as e:
            logger.error("얼굴 임베딩 추출 에러: %s", e)
            return None

    @staticmethod
    def compute_similarity(embedding1, embedding2):
        """두 128차원 정규화 임베딩 간의 코사인 유사도(Cosine Similarity)를 계산합니다."""
        if embedding1 is None or embedding2 is None:
            return 0.0
        # 두 벡터가 이미 L2 정규화되어 있으므로 내적이 코사인 유사도와 같습니다.
        return float(np.dot(embedding1, embedding2))
