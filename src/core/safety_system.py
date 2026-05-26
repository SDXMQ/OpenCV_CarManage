"""
safety_system.py - 안전 통제 및 비즈니스 로직 룰 엔진
운전자 상태(Driver State)에 따라 경고 레벨 판정 및 다감각 차량 제어 규칙을 정의한다.
"""

import json
import os
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class SafetyState(Enum):
    """운전자 안전 상태 코드"""
    DANGER = "danger"
    WARNING = "warning"
    GLARE = "glare"
    STRESS = "stress"
    LOW_ENGAGEMENT = "low_engagement"
    NORMAL = "normal"


class SafetyManager:

    _RULES_FILE = os.path.join(os.path.dirname(__file__), "rules.json")

    def __init__(self, rules_path=None):
        self.current_state = SafetyState.NORMAL
        self.should_beep = False
        self.co2_vent_active = False
        self._rules = self._load_rules(rules_path or self._RULES_FILE)

    def _load_rules(self, path):
        """외부 rules.json 파일에서 제어 규칙을 로드한다."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                rules = json.load(f)
            logger.info("제어 규칙 파일 로드 완료: %s", path)
            return rules
        except FileNotFoundError:
            logger.error("제어 규칙 파일을 찾을 수 없습니다: %s", path)
            raise
        except json.JSONDecodeError as e:
            logger.error("제어 규칙 파일 파싱 실패: %s", e)
            raise

    def evaluate(self, is_drowsy, is_yawning, emotion, sunlight_glare=False):
        """운전자 상태를 평가하고 SafetyState를 반환한다."""
        self.should_beep = False
        dominant = emotion.get("dominant", "neutral")

        if is_drowsy:
            self.current_state = SafetyState.DANGER
            self.should_beep = True
        elif is_yawning:
            self.current_state = SafetyState.WARNING
            self.should_beep = True
        elif sunlight_glare and dominant in ("angry", "disgust"):
            self.current_state = SafetyState.GLARE
        elif dominant in ("angry", "disgust"):
            self.current_state = SafetyState.STRESS
        elif dominant in ("fear", "sad"):
            self.current_state = SafetyState.LOW_ENGAGEMENT
        else:
            self.current_state = SafetyState.NORMAL

        return {
            "state": self.current_state,
            "should_beep": self.should_beep,
        }

    def get_auto_environment(self, is_drowsy, is_yawning, emotion,
                             sunlight_glare=False, tunnel_entry=False,
                             co2_level=800.0, speed=80.0):
        """운전자 상태에 따른 다감각 차량 자동 제어 프리셋을 반환한다."""
        dominant = emotion.get("dominant", "neutral")
        presets = self._rules["presets"]
        thresholds = self._rules["thresholds"]
        adj_rules = self._rules["adjustments"]

        # 1. 기본 감정/신체 상태별 프리셋 결정
        if is_drowsy:
            state_key = "danger"
        elif is_yawning:
            state_key = "warning"
        elif dominant in ("angry", "disgust"):
            state_key = "stress"
        elif dominant in ("fear", "sad"):
            state_key = "low_engagement"
        elif dominant == "happy":
            state_key = "happy"
        else:
            state_key = "normal"

        preset = dict(presets[state_key])

        # 2. 외부 환경 조건에 따른 다감각 피드백 누적 보정 (오버라이드)
        adjustments = []

        # (1) 눈부심 발생 시 보정 (독립 조건)
        if sunlight_glare:
            preset.update(adj_rules["glare"])
            adjustments.append("glare")

        # (2) 터널/야간 진입 시 보정
        if tunnel_entry:
            preset.update(adj_rules["tunnel"])
            adjustments.append("tunnel")

        # (3) CO2 농도 과다 시 환기 제어 보정 (히스테리시스 적용)
        if not self.co2_vent_active and co2_level > thresholds["co2_vent_on"]:
            self.co2_vent_active = True
        elif self.co2_vent_active and co2_level < thresholds["co2_vent_off"]:
            self.co2_vent_active = False

        if self.co2_vent_active:
            preset["ventilation_mode"] = "external"
            # 고속 주행 중이 아닌 경우에만 창문 개방 환기 실행
            if speed <= thresholds["high_speed"]:
                preset["window_tilting"] = True
                adjustments.append("co2_window")
            else:
                adjustments.append("co2_external")

        # (4) 고속 주행 시 창문 닫힘 안전 보정
        if speed > thresholds["high_speed"]:
            # 졸음 상태(danger)인 경우는 환기가 중요하므로 창문을 열어둘 수 있지만, 일반적인 경우에는 풍절음 및 위험 방지를 위해 닫는다.
            if not is_drowsy:
                preset["window_tilting"] = False
                adjustments.append("high_speed_window")
            # 고속 주행 시 환기를 위해 송풍 속도를 최소 N단 이상 확보
            preset["ac_fan_speed"] = max(
                thresholds["min_fan_speed_high_speed"],
                preset["ac_fan_speed"]
            )

        return {"preset": preset, "state_key": state_key, "adjustments": adjustments}
