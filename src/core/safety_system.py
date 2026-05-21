"""
safety_system.py - 안전 통제 및 비즈니스 로직 룰 엔진 (SafetyManager)
운전자 상태에 따라 경고 레벨 판정 + 자동 모드 시 차량 환경 프리셋 결정
"""


class SafetyManager:
    """AI 비전 데이터와 차량 센서 데이터를 종합하여 위기 상황을 판정하는 클래스."""

    def __init__(self):
        self.current_state = "normal"
        self.message = ""
        self.color = "#3498db"
        self.should_beep = False

    def evaluate(self, is_drowsy, emotion, rapid_accel):
        """복합 조건을 평가하여 경고 레벨을 결정한다."""
        self.should_beep = False
        dominant_emotion = emotion.get("dominant", "neutral")

        if is_drowsy:
            self.current_state = "danger"
            self.message = "⚠ 졸음 감지! 주의하세요!"
            self.color = "#e74c3c"
            self.should_beep = True
        elif dominant_emotion == "angry" and rapid_accel:
            self.current_state = "danger"
            self.message = "⚠ 위험 운전 감지! (분노 + 급가속)"
            self.color = "#e74c3c"
            self.should_beep = True
        elif dominant_emotion in ("angry", "fear", "disgust"):
            self.current_state = "warning"
            self.message = f"😤 {dominant_emotion.capitalize()} 상태 감지"
            self.color = "#e67e22" if dominant_emotion in ("angry", "disgust") else "#9b59b6"
        elif dominant_emotion == "happy":
            self.current_state = "normal"
            self.message = ""
            self.color = "#2ecc71"
        else:
            self.current_state = "normal"
            self.message = ""
            self.color = "#3498db"

        return {
            "state": self.current_state,
            "message": self.message,
            "color": self.color,
            "should_beep": self.should_beep,
        }

    def get_auto_environment(self, is_drowsy, emotion):
        """현재 운전자 상태에 따라 자동 차량 환경 프리셋을 반환한다."""
        dominant = emotion.get("dominant", "neutral")

        if is_drowsy:
            return {
                "ac_on": True,
                "ac_temp": 18,
                "ac_fan_speed": 5,
                "light_color_name": "경고 (빨강)",
                "light_color_hex": "#e74c3c",
                "light_brightness": 100,
                "music_genre": "없음",
                "music_volume": 0,
            }
        elif dominant in ("angry", "disgust"):
            return {
                "ac_on": True,
                "ac_temp": 22,
                "ac_fan_speed": 2,
                "light_color_name": "기본 (파랑)",
                "light_color_hex": "#3498db",
                "light_brightness": 60,
                "music_genre": "클래식",
                "music_volume": 60,
            }
        elif dominant in ("fear", "sad"):
            return {
                "ac_on": True,
                "ac_temp": 24,
                "ac_fan_speed": 2,
                "light_color_name": "집중 (보라)",
                "light_color_hex": "#9b59b6",
                "light_brightness": 50,
                "music_genre": "Lo-Fi",
                "music_volume": 50,
            }
        elif dominant == "happy":
            return {
                "ac_on": True,
                "ac_temp": 22,
                "ac_fan_speed": 2,
                "light_color_name": "편안함 (녹색)",
                "light_color_hex": "#2ecc71",
                "light_brightness": 60,
                "music_genre": "Jazz",
                "music_volume": 50,
            }
        else:  # neutral / surprise
            return {
                "ac_on": True,
                "ac_temp": 22,
                "ac_fan_speed": 2,
                "light_color_name": "차분함 (하늘)",
                "light_color_hex": "#1abc9c",
                "light_brightness": 50,
                "music_genre": "Lo-Fi",
                "music_volume": 40,
            }
