"""
vehicle_env.py - 차량 환경 상태 관리 모듈
에어컨 제어 상태만 관리한다.
"""


class VehicleEnvironment:
    """차량 내부 에어컨 환경 상태를 보관하는 데이터 클래스."""

    def __init__(self):
        self.power_on = False
        self.ac_on = False
        self.ac_temp = 22     # 온도 (16~30 °C)
        self.ac_fan_speed = 1      # 풍량 (0~5)
        self.cabin_temp = 25.0  # 차량 내부 실시간 실제 온도 (초기값 25.0°C)
        self.auto_mode = False

    def apply_preset(self, preset: dict):
        for key, value in preset.items():
            if hasattr(self, key):
                setattr(self, key, value)

