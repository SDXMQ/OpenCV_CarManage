"""
config_manager.py - 설정값 영구 저장 및 로드 관리자
"""

import os


class ConfigManager:
    """settings.txt 파일을 읽고 쓰며 설정값을 메모리에 관리하는 유틸리티."""

    def __init__(self, filepath="../settings.txt"):
        self.filepath = filepath
        self.config = {
            "camera_index": 0,
            "audio_alert": False,
            "language": "ko",
            "mirror_camera": False,
            "current_profile": "default"
        }
        self.load()

    def load(self):
        """설정 파일에서 값을 읽어온다. 파일이 없으면 기본값 유지."""
        if not os.path.exists(self.filepath):
            self.save_all()
            return

        with open(self.filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip()

                    if key == "camera_index":
                        self.config[key] = int(val) if val.isdigit() else 0
                    elif key == "audio_alert":
                        self.config[key] = (val.lower() == "true")
                    elif key == "mirror_camera":
                        self.config[key] = (val.lower() == "true")
                    elif key == "language":
                        self.config[key] = val
                    elif key == "current_profile":
                        self.config[key] = val

    def save_all(self):
        """현재 메모리의 설정값을 파일에 쓴다."""
        with open(self.filepath, "w", encoding="utf-8") as f:
            for key, val in self.config.items():
                f.write(f"{key}={val}\n")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set_and_save(self, key, value):
        """설정값을 업데이트하고 즉시 파일에 저장한다."""
        if key in self.config and self.config[key] == value:
            return  # 값이 같으면 불필요한 I/O 스킵
        self.config[key] = value
        self.save_all()
