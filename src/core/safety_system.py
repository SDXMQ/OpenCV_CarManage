"""
safety_system.py - 안전 통제 및 비즈니스 로직 룰 엔진
운전자 상태(Driver State)에 따라 경고 레벨 판정 및 다감각 차량 제어 규칙을 정의한다.
"""


class SafetyManager:

    def __init__(self):
        self.current_state = "normal"
        self.message = ""
        self.color = "#3498db"
        self.should_beep = False
        self.co2_vent_active = False

    def evaluate(self, is_drowsy, is_yawning, emotion, sunlight_glare=False):
        """운전자 상태를 평가하고 경고 메시지를 반환한다."""
        self.should_beep = False
        dominant = emotion.get("dominant", "neutral")

        if is_drowsy:
            self.current_state = "danger"
            self.message = "⚠ 졸음 감지! 즉시 주의하십시오!"
            self.color = "#e74c3c"
            self.should_beep = True
        elif is_yawning:
            self.current_state = "warning"
            self.message = "🥱 하품 감지 → 졸음 전조 증상"
            self.color = "#e67e22"
            self.should_beep = True
        elif sunlight_glare and dominant in ("angry", "disgust"):
            self.current_state = "glare"
            self.message = "☀ 눈부심이 감지되었습니다. 선바이저를 내릴까요?"
            self.color = "#f39c12"
        elif dominant in ("angry", "disgust"):
            self.current_state = "stress"
            self.message = "😤 스트레스/피로도 누적 감지"
            self.color = "#e67e22"
        elif dominant in ("fear", "sad"):
            self.current_state = "low_engagement"
            self.message = "😶 집중력 저하 상태 감지"
            self.color = "#9b59b6"
        elif dominant == "happy":
            self.current_state = "normal"
            self.message = "😊 쾌적한 주행 중"
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

    def get_auto_environment(self, is_drowsy, is_yawning, emotion,
                             sunlight_glare=False, tunnel_entry=False,
                             co2_level=800.0, speed=80.0):
        """운전자 상태에 따른 다감각 차량 자동 제어 프리셋과 로그를 반환한다."""
        dominant = emotion.get("dominant", "neutral")

        # 1. 기본 감정/신체 상태별 프리셋 결정
        if is_drowsy:
            preset = {
                "power_on": True,
                "ac_on": True,
                "ac_temp": 17,
                "ac_fan_speed": 5,
                "ventilation_mode": "external",
                "window_tilting": True,
                "airflow_direction": "direct",
                "audio_genre": "Dance",
                "audio_volume": 80,
                "ambient_light": "Flashing Red",
                "display_dark_mode": False,
                "display_brightness": 100,
                "seat_ventilation": 3,
                "seat_heater": 0,
                "haptic_vibration": True,
            }
            log = "😪 졸음 감지 → 쿨링 펀치(17°C/최대풍), 외기유입, 창문 틸팅, 직바람, 댄스곡 80%, 시트 통풍 3단, 햅틱 진동 ON"
            log_color = "#e74c3c"
        elif is_yawning:
            preset = {
                "power_on": True,
                "ac_on": True,
                "ac_temp": 19,
                "ac_fan_speed": 4,
                "ventilation_mode": "external",
                "window_tilting": False,
                "airflow_direction": "direct",
                "audio_genre": "Pop",
                "audio_volume": 60,
                "ambient_light": "Blue",
                "display_dark_mode": False,
                "display_brightness": 90,
                "seat_ventilation": 2,
                "seat_heater": 0,
                "haptic_vibration": False,
            }
            log = "🥱 하품 감지 → 냉각 강화(19°C/4단), 외기유입, 직바람, 팝곡 60%, 시트 통풍 2단"
            log_color = "#e67e22"
        elif dominant in ("angry", "disgust"):
            preset = {
                "power_on": True,
                "ac_on": True,
                "ac_temp": 21,
                "ac_fan_speed": 3,
                "ventilation_mode": "external",
                "window_tilting": False,
                "airflow_direction": "indirect",
                "audio_genre": "Classic",
                "audio_volume": 35,
                "ambient_light": "Amber",
                "display_dark_mode": False,
                "display_brightness": 70,
                "seat_ventilation": 1,
                "seat_heater": 0,
                "haptic_vibration": False,
            }
            log = "😤 스트레스 감지 → 21°C 외기 간접풍, 앰버 무드등, 클래식 35%, 시트 통풍 1단"
            log_color = "#e67e22"
        elif dominant in ("fear", "sad"):
            preset = {
                "power_on": True,
                "ac_on": True,
                "ac_temp": 24,
                "ac_fan_speed": 2,
                "ventilation_mode": "external",
                "window_tilting": False,
                "airflow_direction": "indirect",
                "audio_genre": "Classic",
                "audio_volume": 25,
                "ambient_light": "Green",
                "display_dark_mode": False,
                "display_brightness": 75,
                "seat_ventilation": 0,
                "seat_heater": 1,
                "haptic_vibration": False,
            }
            log = "😶 집중력 저하 → 24°C 외기 간접풍, 그린 무드등, 클래식 25%, 시트 열선 1단"
            log_color = "#9b59b6"
        else:
            preset = {
                "power_on": True,
                "ac_on": True,
                "ac_temp": 22,
                "ac_fan_speed": 1,
                "ventilation_mode": "internal",
                "window_tilting": False,
                "airflow_direction": "indirect",
                "audio_genre": "None",
                "audio_volume": 30,
                "ambient_light": "Off",
                "display_dark_mode": False,
                "display_brightness": 80,
                "seat_ventilation": 0,
                "seat_heater": 0,
                "haptic_vibration": False,
            }
            if dominant == "happy":
                log = "😊 쾌적 → 22°C 표준 유지, 그린 무드등"
                preset["ambient_light"] = "Green"
                log_color = "#2ecc71"
            else:
                log = "😐 평온 → 22°C 표준 유지"
                log_color = "#3498db"

        # 2. 외부 환경 조건에 따른 다감각 피드백 누적 보정 (오버라이드)
        adjustments = []

        # (1) 눈부심 발생 시 보정 (독립 조건)
        if sunlight_glare:
            preset["display_dark_mode"] = True
            preset["display_brightness"] = 40
            preset["airflow_direction"] = "indirect"
            preset["ambient_light"] = "Amber"
            adjustments.append("☀눈부심 차광 제어(다크 40%, 앰버 무드등)")

        # (2) 터널/야간 진입 시 보정
        if tunnel_entry:
            preset["ventilation_mode"] = "internal"
            preset["window_tilting"] = False
            preset["display_dark_mode"] = True
            preset["display_brightness"] = 50
            preset["ambient_light"] = "Amber"
            adjustments.append("🌑터널 자동 감광/내기순환")

        # (3) CO2 농도 과다 시 환기 제어 보정 (히스테리시스 적용: 1800ppm 초과 시 시작, 1000ppm 미만 시 종료)
        if not self.co2_vent_active and co2_level > 1800.0:
            self.co2_vent_active = True
        elif self.co2_vent_active and co2_level < 1000.0:
            self.co2_vent_active = False

        if self.co2_vent_active:
            preset["ventilation_mode"] = "external"
            # 고속 주행(100km/h 초과) 중이 아닌 경우에만 안전을 위해 창문 개방 환기 실행
            if speed <= 100.0:
                preset["window_tilting"] = True
                adjustments.append("💨이산화탄소 환기(외기유입+창문 개방)")
            else:
                adjustments.append("💨이산화탄소 환기(외기유입 강제)")

        # (4) 고속 주행 시 창문 닫힘 안전 보정
        if speed > 100.0:
            # 졸음 상태(danger)인 경우는 환기가 중요하므로 창문을 열어둘 수 있지만, 일반적인 경우에는 풍절음 및 위험 방지를 위해 닫는다.
            if not is_drowsy:
                preset["window_tilting"] = False
                adjustments.append("🚗고속 안전 제어(창문 닫힘)")
            # 고속 주행 시 환기를 위해 송풍 속도를 최소 3단 이상 확보
            preset["ac_fan_speed"] = max(3, preset["ac_fan_speed"])

        # 보정된 경우 로그 메시지 보완
        if adjustments:
            log += " + [" + ", ".join(adjustments) + "]"
            if log_color not in ("#e74c3c", "#e67e22"):
                log_color = "#f39c12"

        return {"preset": preset, "log": log, "log_color": log_color}
