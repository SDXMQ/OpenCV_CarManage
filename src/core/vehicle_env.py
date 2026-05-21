"""
vehicle_env.py - 차량 환경 상태 관리 모듈
에어컨, 실내 조명, 오디오 등 차량 인테리어 환경의 현재 상태를 관리한다.
"""


class VehicleEnvironment:
    """차량 내부 환경(에어컨, 조명, 오디오) 상태를 보관하는 데이터 클래스."""

    MUSIC_GENRES = ["없음", "클래식", "Lo-Fi", "Jazz", "Pop", "자연 소리"]
    LIGHT_PRESETS = {
        "기본 (파랑)": "#3498db",
        "따뜻함 (주황)": "#e67e22",
        "편안함 (녹색)": "#2ecc71",
        "집중 (보라)": "#9b59b6",
        "경고 (빨강)": "#e74c3c",
        "차분함 (하늘)": "#1abc9c",
    }

    def __init__(self):
        # 에어컨
        self.ac_on = False
        self.ac_temp = 22        # 16~30 °C
        self.ac_fan_speed = 1    # 0~5

        # 실내 조명
        self.light_color_name = "기본 (파랑)"
        self.light_color_hex = "#3498db"
        self.light_brightness = 50  # 0~100

        # 오디오
        self.music_genre = "없음"
        self.music_volume = 50   # 0~100

        # 자동 모드
        self.auto_mode = False

    def apply_preset(self, preset: dict):
        """딕셔너리 형태의 환경 프리셋을 일괄 적용한다."""
        for key, value in preset.items():
            if hasattr(self, key):
                setattr(self, key, value)

    @property
    def light_hex(self):
        return self.LIGHT_PRESETS.get(self.light_color_name, self.light_color_hex)
