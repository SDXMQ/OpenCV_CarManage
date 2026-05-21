"""
simulation_manager.py - 시뮬레이션 제어 및 AI 연동 상태 관리자
"""

import threading
import time
import winsound
from PIL import Image

class SimulationManager:
    def __init__(self, config, safety, env, camera):
        self._config = config
        self._safety = safety
        self._env = env
        self._camera = camera

        self.sim_state = "stopped"
        self._last_ai_log = ""

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
        self._last_ai_log = ""
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
        is_drowsy = self._camera.is_drowsy

        # 2. 안전 평가
        safety_eval = self._safety.evaluate(is_drowsy, emotion)

        # 3. 오디오 비프음 재생 트리거
        if safety_eval["should_beep"] and audio_enabled:
            threading.Thread(target=lambda: winsound.Beep(1000, 300), daemon=True).start()

        # 4. AI 에어컨 자동 제어 로직 적용
        ai_log = None
        ai_log_color = None
        if auto_mode_active:
            ai_log, ai_log_color = self._apply_auto(is_drowsy, emotion)
            self._animate_sliders()

        # 5. 차량 실내 온도 물리 시뮬레이션
        ambient_temp = 28.0  # 실외 온도
        if self._env.power_on:
            # 전원이 켜진 경우
            if not self._env.ac_on and self._env.ac_temp > self._env.cabin_temp:
                # 1) 온풍 기능(히터) 가동: A/C 꺼짐 + 설정 온도가 실내 온도보다 높음
                diff = self._env.ac_temp - self._env.cabin_temp
                self._env.cabin_temp += 0.001 * self._env.ac_fan_speed * diff
            elif self._env.ac_on and self._env.ac_temp < self._env.cabin_temp:
                # 2) 냉방 기능 가동: A/C 켜짐 + 설정 온도가 실내 온도보다 낮음
                diff = self._env.cabin_temp - self._env.ac_temp
                self._env.cabin_temp -= 0.001 * self._env.ac_fan_speed * diff
            else:
                # 3) 송풍 상태 (설정 온도가 낮지만 A/C 가 꺼져있거나, A/C 켜져있는데 설정 온도가 높은 경우 등)
                # 자연스럽게 실외 온도로 수렴함
                self._env.cabin_temp += 0.0003 * (ambient_temp - self._env.cabin_temp)
        else:
            # 전원이 꺼진 경우: 엔진 열 및 외부 복사열로 실외 온도로 자연 수렴
            self._env.cabin_temp += 0.0006 * (ambient_temp - self._env.cabin_temp)

        # 온도 상하한 제한 [15.0, 35.0]
        self._env.cabin_temp = max(15.0, min(35.0, self._env.cabin_temp))

        return {
            "frame_rgb": frame_rgb,
            "emotion": emotion,
            "ear_value": ear_value,
            "is_drowsy": is_drowsy,
            "safety_eval": safety_eval,
            "ai_log": ai_log,
            "ai_log_color": ai_log_color,
            "power_on": self._env.power_on,
            "ac_on": self._env.ac_on,
            "ac_temp": self._env.ac_temp,
            "ac_fan_speed": self._env.ac_fan_speed,
            "cabin_temp": self._env.cabin_temp
        }


    def _apply_auto(self, is_drowsy, emotion):
        """AI 분석 결과를 가져와서 에어컨 목표 상태값을 갱신한다."""
        res = self._safety.get_auto_environment(is_drowsy, emotion)
        preset = res["preset"]

        self._env.power_on = preset.get("power_on", True)
        self._env.ac_on = preset["ac_on"]

        # 목표값 갱신
        self.target_temp = preset["ac_temp"]
        self.target_fan = preset["ac_fan_speed"]

        # 로그 메시지가 변경된 경우에만 반환하여 기록하게 함
        if self._last_ai_log != res["log"]:
            self._last_ai_log = res["log"]
            return res["log"], res["log_color"]

        return None, None


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
