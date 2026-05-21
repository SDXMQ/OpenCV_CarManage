"""
visualizer.py - 비디오 프레임 시각화 유틸리티
"""
import cv2

class FrameVisualizer:
    """분석된 EAR 및 감정 데이터를 원본 OpenCV 프레임 위에 그리는 유틸리티."""

    @staticmethod
    def draw_overlays(frame, ear_value, emotion_data, is_drowsy):
        """프레임에 각종 정보와 경고를 그린다 (In-place 연산)."""
        
        # EAR 오버레이
        cv2.putText(frame, f"EAR: {ear_value:.2f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
        # 감정 오버레이
        dominant = emotion_data.get("dominant", "")
        if dominant:
            color = (0, 0, 255) if dominant in ("angry", "fear") else (0, 255, 0)
            cv2.putText(frame, f"Emotion: {dominant}", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                        
        # 졸음 경고창 오버레이
        if is_drowsy:
            cv2.putText(frame, "!! DROWSY !!", (10, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
                        
        return frame
