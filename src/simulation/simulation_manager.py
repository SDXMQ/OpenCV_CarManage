"""
simulation_manager.py - 시뮬레이션 제어 및 AI 연동 상태 관리자
"""

import logging
import threading
import time
import winsound
from PIL import Image

logger = logging.getLogger(__name__)

class SimulationManager:
    def __init__(self, config, safety, env, camera):
        self._config = config
        self._safety = safety
        self._env = env
        self._camera = camera

        self.sim_state = "stopped"
        self._last_ai_key = None

        # 애니메이션용 목표값
        self.target_temp = self._env.ac_temp
        self.target_fan = self._env.ac_fan_speed

        # 애니메이션 타이머
        self._last_anim_time = time.time()

    def start(self):
        if self.sim_state == "paused":
            self._camera.resume()
            self.sim_state = "running"
            log_msg = "▶ 시스템 재개"
            log_color = "#00d2ff"  # ACCENT
        else:
            self._camera.start()
            self.sim_state = "running"
            log_msg = "▶ 시스템 시작"
            log_color = "#2ecc71"  # GREEN
        return log_msg, log_color

    def pause(self):
        self._camera.pause()
        self.sim_state = "paused"
        return "⏸ 일시정지", "#f39c12"

    def stop(self):
        self._camera.stop()
        self.sim_state = "stopped"
        self._last_ai_key = None
        self.target_temp = self._env.ac_temp
        self.target_fan = self._env.ac_fan_speed
        return "⏹ 시스템 정지", "#e74c3c"

    def update_step(self, auto_mode_active, audio_enabled):
        """매 프레임 업데이트 시 실행될 시뮬레이션 및 데이터 분석 단계."""
        if self.sim_state != "running":
            return None

        # 1. 카메라 프레임 및 상태 데이터 획득
        frame_rgb = self._camera.get_frame_rgb()
        emotion = self._camera.emotion
        ear_value = self._camera.ear_value
        mar_value = self._camera.mar_value
        is_drowsy = self._camera.is_drowsy
        is_yawning = self._camera.is_yawning

        # 2. 안전 평가 (환경 맥락 포함)
        safety_eval = self._safety.evaluate(
            is_drowsy, is_yawning, emotion,
            sunlight_glare=self._env.sunlight_glare
        )

        # 3. 오디오 비프음 재생 트리거
        if safety_eval["should_beep"] and audio_enabled:
            threading.Thread(target=lambda: winsound.Beep(1000, 300), daemon=True).start()

        # 4. AI 다감각 자동 제어 로직 적용
        ai_state_key = None
        ai_adjustments = None
        ai_preset = None
        if auto_mode_active:
            ai_state_key, ai_adjustments, ai_preset = self._apply_auto(emotion)
            self._animate_sliders()

        # 5. CO2 물리 시뮬레이션
        self._simulate_co2()

        # 6. 차량 실내 온도 물리 시뮬레이션
        ambient_temp = 28.0  # 실외 온도
        if self._env.power_on:
            if not self._env.ac_on and self._env.ac_temp > self._env.cabin_temp:
                diff = self._env.ac_temp - self._env.cabin_temp
                self._env.cabin_temp += 0.001 * self._env.ac_fan_speed * diff
            elif self._env.ac_on and self._env.ac_temp < self._env.cabin_temp:
                diff = self._env.cabin_temp - self._env.ac_temp
                self._env.cabin_temp -= 0.001 * self._env.ac_fan_speed * diff
            else:
                self._env.cabin_temp += 0.0003 * (ambient_temp - self._env.cabin_temp)
        else:
            self._env.cabin_temp += 0.0006 * (ambient_temp - self._env.cabin_temp)

        self._env.cabin_temp = max(15.0, min(35.0, self._env.cabin_temp))

        return {
            "frame_rgb": frame_rgb,
            "emotion": emotion,
            "ear_value": ear_value,
            "mar_value": mar_value,
            "is_drowsy": is_drowsy,
            "is_yawning": is_yawning,
            "safety_eval": safety_eval,
            "ai_state_key": ai_state_key,
            "ai_adjustments": ai_adjustments,
            "ai_preset": ai_preset,
            "power_on": self._env.power_on,
            "ac_on": self._env.ac_on,
            "ac_temp": self._env.ac_temp,
            "ac_fan_speed": self._env.ac_fan_speed,
            "cabin_temp": self._env.cabin_temp,
            # 다감각 제어 상태
            "ventilation_mode": self._env.ventilation_mode,
            "window_tilting": self._env.window_tilting,
            "airflow_direction": self._env.airflow_direction,
            "audio_genre": self._env.audio_genre,
            "audio_volume": self._env.audio_volume,
            "ambient_light": self._env.ambient_light,
            "display_dark_mode": self._env.display_dark_mode,
            "display_brightness": self._env.display_brightness,
            "seat_ventilation": self._env.seat_ventilation,
            "seat_heater": self._env.seat_heater,
            "haptic_vibration": self._env.haptic_vibration,
            # 환경 시뮬레이션
            "co2_level": self._env.co2_level,
        }


    def _apply_auto(self, emotion):
        """AI 분석 결과를 가져와서 다감각 차량 목표 상태값을 갱신한다."""
        res = self._safety.get_auto_environment(
            emotion,
            sunlight_glare=self._env.sunlight_glare,
            tunnel_entry=self._env.tunnel_entry,
            co2_level=self._env.co2_level,
            speed=self._env.speed
        )
        preset = res["preset"]

        # HVAC 기본 상태 적용
        self._env.power_on = preset.get("power_on", True)
        self._env.ac_on = preset["ac_on"]
        self.target_temp = preset["ac_temp"]
        self.target_fan = preset["ac_fan_speed"]

        # 다감각 제어 상태 즉시 적용
        self._env.ventilation_mode = preset.get("ventilation_mode", "internal")
        self._env.window_tilting = preset.get("window_tilting", False)
        self._env.airflow_direction = preset.get("airflow_direction", "indirect")
        self._env.audio_genre = preset.get("audio_genre", "None")
        self._env.audio_volume = preset.get("audio_volume", 30)
        self._env.ambient_light = preset.get("ambient_light", "Off")
        self._env.display_dark_mode = preset.get("display_dark_mode", False)
        self._env.display_brightness = preset.get("display_brightness", 80)
        self._env.seat_ventilation = preset.get("seat_ventilation", 0)
        self._env.seat_heater = preset.get("seat_heater", 0)
        self._env.haptic_vibration = preset.get("haptic_vibration", False)

        # 상태가 변경된 경우에만 반환하여 UI에서 로그를 기록하게 함
        current_key = (res["state_key"], tuple(sorted(res["adjustments"])))
        if self._last_ai_key != current_key:
            self._last_ai_key = current_key
            return res["state_key"], res["adjustments"], preset

        return None, None, None

    def _simulate_co2(self):
        """내기/외기 순환 및 창문 상태에 따른 CO2 농도 변화 시뮬레이션."""
        if self._env.ventilation_mode == "external" or self._env.window_tilting:
            # 외기유입 또는 창문 개방 → CO2 서서히 하락 (현실적인 속도로 보정)
            self._env.co2_level -= 0.1 * (self._env.co2_level - 450.0) * 0.01
        else:
            # 내기순환 → CO2 서서히 상승 (승객 호흡)
            self._env.co2_level += 0.3

        self._env.co2_level = max(400.0, min(2500.0, self._env.co2_level))

    def _animate_sliders(self):
        """AI가 설정한 목표값으로 슬라이더 값을 0.2초마다 1단씩 부드럽게 조정한다."""
        now = time.time()
        if now - self._last_anim_time > 0.2:
            moved = False

            # 온도 보간
            if self._env.ac_temp < self.target_temp:
                self._env.ac_temp += 1
                moved = True
            elif self._env.ac_temp > self.target_temp:
                self._env.ac_temp -= 1
                moved = True

            # 풍량 보간
            if self._env.ac_fan_speed < self.target_fan:
                self._env.ac_fan_speed += 1
                moved = True
            elif self._env.ac_fan_speed > self.target_fan:
                self._env.ac_fan_speed -= 1
                moved = True

            if moved:
                self._last_anim_time = now
