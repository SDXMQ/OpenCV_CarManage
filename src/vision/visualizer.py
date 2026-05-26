"""
visualizer.py - 비디오 프레임 시각화 유틸리티
"""
import cv2

class FrameVisualizer:
    """분석된 EAR, MAR 및 감정 데이터를 원본 OpenCV 프레임 위에 그리는 유틸리티."""

    @staticmethod
    def draw_overlays(frame, ear_value, mar_value, emotion_data, is_drowsy, is_yawning, all_bboxes=None, target_bbox=None):
        """프레임에 각종 정보와 경고 및 검출된 얼굴 사각형을 그린다 (In-place 연산)."""
        
        # 다중 얼굴 바운딩 박스 시각화
        if all_bboxes:
            for bbox in all_bboxes:
                xmin, ymin, xmax, ymax = bbox
                # 타겟 운전자(현재 추적 대상)는 초록색, 그 외 인물은 회색 표시
                if target_bbox is not None and bbox == target_bbox:
                    cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
                    cv2.putText(frame, "DRIVER", (xmin, max(ymin - 10, 15)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                else:
                    cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (120, 120, 120), 1)
        
        # EAR 오버레이
        cv2.putText(frame, f"EAR: {ear_value:.2f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # MAR 오버레이
        mar_color = (0, 0, 255) if mar_value > 0.50 else (0, 255, 0)
        cv2.putText(frame, f"MAR: {mar_value:.2f}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, mar_color, 2)
                    
        # 감정 오버레이
        dominant = emotion_data.get("dominant", "")
        if dominant:
            color = (0, 0, 255) if dominant in ("angry", "fear") else (0, 255, 0)
            cv2.putText(frame, f"Emotion: {dominant}", (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                        
        # 졸음 경고창 오버레이
        if is_drowsy:
            cv2.putText(frame, "!! DROWSY !!", (10, 130),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)

        # 하품 경고창 오버레이
        if is_yawning:
            cv2.putText(frame, "!! YAWNING !!", (10, 170),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 100, 255), 3)
                        
        return frame
