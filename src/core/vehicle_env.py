"""
vehicle_env.py - 차량 환경 상태 관리 모듈
에어컨 제어 상태 및 다감각 차량 제어기 장치 상태를 관리한다.
"""


class VehicleEnvironment:
    """차량 내부 환경 상태를 보관하는 데이터 클래스."""

    def __init__(self):
        # === 기존 에어컨 상태 ===
        self.power_on = False
        self.ac_on = False
        self.ac_temp = 22     # 온도 (16~30 °C)
        self.ac_fan_speed = 1      # 풍량 (0~5)
        self.cabin_temp = 25.0  # 차량 내부 실시간 실제 온도 (초기값 25.0°C)
        self.auto_mode = False

        # === 환경 센서 시뮬레이션 입력값 ===
        self.sunlight_glare = False       # 강한 햇빛 눈부심
        self.co2_level = 800.0            # 실내 CO2 농도 (ppm), 기본 800
        self.tunnel_entry = False         # 터널/야간 진입 여부
        self.speed = 80.0                 # 주행 속도 (km/h)

        # === 배터리 및 전력 소비 상태 ===
        self.soc = 100.0                  # 배터리 잔량 (State of Charge, %)
        self.battery_capacity = 20.0      # 총 배터리 용량 (kWh, 빠른 테스트를 위해 축소)
        self.ac_power_draw = 0.0          # 실시간 공조 전력 소비율 (kW)

        # === 다감각 차량 제어기 출력 상태 ===
        self.ventilation_mode = "internal"    # "internal"(내기순환) / "external"(외기유입)
        self.window_tilting = False           # 창문/선루프 틸팅 개방
        self.airflow_direction = "indirect"   # "direct"(직바람) / "indirect"(간접풍)
        self.audio_genre = "None"             # "Classic" / "Pop" / "Dance" / "None"
        self.audio_volume = 30                # 스피커 볼륨 (0~100)
        self.ambient_light = "Off"            # "Amber" / "Green" / "Blue" / "Flashing Red" / "Off"
        self.display_dark_mode = False        # 고대비 다크 모드
        self.display_brightness = 80          # 화면 밝기 (0~100)
        self.seat_ventilation = 0             # 시트 통풍 단계 (0~3)
        self.seat_heater = 0                  # 시트 열선 단계 (0~3)
        self.haptic_vibration = False         # 핸들/시트 햅틱 진동 경고

    def apply_preset(self, preset: dict):
        for key, value in preset.items():
            if hasattr(self, key):
                setattr(self, key, value)
