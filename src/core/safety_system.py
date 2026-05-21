"""
safety_system.py - 안전 통제 및 비즈니스 로직 룰 엔진
운전자 상태에 따라 경고 레벨 판정 및 에어컨 자동 제어 규칙을 정의한다.
"""


class SafetyManager:

    def __init__(self):
        self.current_state = "normal"
        self.message = ""
        self.color = "#3498db"
        self.should_beep = False

    def evaluate(self, is_drowsy, emotion):
        self.should_beep = False
        dominant = emotion.get("dominant", "neutral")

        if is_drowsy:
            self.current_state = "danger"
            self.message = "⚠ 졸음 감지! 주의하십시오!"
            self.color = "#e74c3c"
            self.should_beep = True
        elif dominant in ("angry", "disgust"):
            self.current_state = "warning"
            self.message = f"😡 분노/불쾌 상태 감지 ({dominant.capitalize()})"
            self.color = "#e67e22"
        elif dominant in ("fear", "sad"):
            self.current_state = "warning"
            self.message = f"😰 불안/우울 상태 감지 ({dominant.capitalize()})"
            self.color = "#9b59b6"
        elif dominant == "happy":
            self.current_state = "normal"
            self.message = "😊 즐거운 주행 중"
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
        """운전자 상태에 따른 단일 에어컨 자동 제어 프리셋과 로그를 반환한다."""
        dominant = emotion.get("dominant", "neutral")

        if is_drowsy:
            return {
                "preset": {
                    "power_on": True,
                    "ac_on": True,
                    "ac_temp": 17,
                    "ac_fan_speed": 5,
                },
                "log": "😪 졸음 감지 → 온도를 17°C로 낮추고 바람을 최대로 틉니다.",
                "log_color": "#e74c3c",
            }
        elif dominant in ("angry", "disgust"):
            return {
                "preset": {
                    "power_on": True,
                    "ac_on": True,
                    "ac_temp": 21,
                    "ac_fan_speed": 3,
                },
                "log": "😡 분노 감지 → 21°C 냉풍으로 열기를 진정시킵니다.",
                "log_color": "#e67e22",
            }
        elif dominant in ("fear", "sad"):
            return {
                "preset": {
                    "power_on": True,
                    "ac_on": True,
                    "ac_temp": 24,
                    "ac_fan_speed": 2,
                },
                "log": "😰 불안/우울 감지 → 따뜻한 24°C 온풍으로 안정화합니다.",
                "log_color": "#9b59b6",
            }
        elif dominant == "happy":
            return {
                "preset": {
                    "power_on": True,
                    "ac_on": True,
                    "ac_temp": 22,
                    "ac_fan_speed": 1,
                },
                "log": "😊 행복 감지 → 쾌적한 22°C 상태를 유지합니다.",
                "log_color": "#2ecc71",
            }
        else:
            return {
                "preset": {
                    "power_on": True,
                    "ac_on": True,
                    "ac_temp": 22,
                    "ac_fan_speed": 1,
                },
                "log": "😐 평온 → 표준 22°C 상태를 유지합니다.",
                "log_color": "#3498db",
            }

