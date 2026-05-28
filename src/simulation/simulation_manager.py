"""
simulation_manager.py - 시뮬레이션 제어 및 AI 연동 상태 관리자
CAN 버스 송수신, MQTT 관제 퍼블리시 및 멀티 오브젝티브 최적화 기능을 포함합니다.
"""

import logging
import threading
import time
import winsound
import json
import random
import paho.mqtt.client as mqtt

from core.can_bus import VirtualCANBus
from core.safety_system import SafetyState

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

        # 차량 식별자 생성
        self.vehicle_id = f"SEAVS-EV-{random.randint(1000, 9999)}"

        # CAN 버스 초기화
        self.can_bus = VirtualCANBus(channel="seavs_can")
        
        # MQTT 클라이언트 초기화
        self.mqtt_client = mqtt.Client(client_id=self.vehicle_id)
        self.mqtt_topic = f"seavs/fleet/{self.vehicle_id}/telemetry"

        # 스레드 제어 변수
        self._can_thread = None
        self._mqtt_thread = None

        # 최적화 솔버 상태 (UI 전달용)
        self.solver_active = False
        self.solver_weights = (0.5, 0.5)

    def start(self):
        if self.sim_state == "paused":
            self._camera.resume()
            self.sim_state = "running"
            log_msg = "▶ 시스템 재개"
            log_color = "#00d2ff"  # ACCENT
        else:
            self._camera.start()
            self.sim_state = "running"
            
            # 스레드 시작
            if not self._can_thread or not self._can_thread.is_alive():
                self._can_thread = threading.Thread(target=self._can_receive_loop, daemon=True)
                self._can_thread.start()
            
            if not self._mqtt_thread or not self._mqtt_thread.is_alive():
                self._mqtt_thread = threading.Thread(target=self._mqtt_publish_loop, daemon=True)
                self._mqtt_thread.start()

            log_msg = f"▶ 시스템 시작 (ID: {self.vehicle_id})"
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
        
        # 연결 종료 처리
        if self.mqtt_client.is_connected():
            self.mqtt_client.disconnect()
            
        return "⏹ 시스템 정지", "#e74c3c"

    def _can_receive_loop(self):
        """가상 CAN 버스로부터 제어 명령(0x210) 등을 수신하는 루프"""
        while self.sim_state != "stopped":
            msg = self.can_bus.receive(timeout=0.1)
            if msg and msg.arbitration_id == 0x210:
                # 0x210: 공조 및 다감각 제어 명령 처리
                try:
                    self._env.power_on = bool(msg.data[0])
                    self._env.ac_on = bool(msg.data[1])
                    self.target_temp = msg.data[2]
                    self.target_fan = msg.data[3]
                    self._env.ventilation_mode = "external" if msg.data[4] == 1 else "internal"
                    self._env.window_tilting = bool(msg.data[5])
                    self._env.airflow_direction = "direct" if msg.data[6] == 1 else "indirect"
                    self._env.haptic_vibration = bool(msg.data[7])
                except IndexError:
                    pass

    def _mqtt_publish_loop(self):
        """실시간 텔레메트리 데이터를 MQTT 퍼블릭 브로커로 발행하는 루프"""
        try:
            self.mqtt_client.connect("broker.hivemq.com", 1883, 60)
            self.mqtt_client.loop_start()
            logger.info("MQTT 브로커 연결 성공")
        except Exception as e:
            logger.error(f"MQTT 연결 실패: {e}")
            return

        while self.sim_state != "stopped":
            if self.sim_state == "running":
                payload = {
                    "vehicle_id": self.vehicle_id,
                    "timestamp": time.time(),
                    "driver_state": self._safety.current_state.value,
                    "ear_value": self._camera.ear_value,
                    "mar_value": self._camera.mar_value,
                    "cabin_temp": round(self._env.cabin_temp, 2),
                    "target_temp": self._env.ac_temp,
                    "power_consumption": round(self._env.ac_power_draw, 3),
                    "battery_soc": round(self._env.soc, 2),
                    "co2_level": round(self._env.co2_level, 1),
                    "speed": round(self._env.speed, 1)
                }
                self.mqtt_client.publish(self.mqtt_topic, json.dumps(payload))
            time.sleep(1.0)
            
        self.mqtt_client.loop_stop()

    def update_step(self, auto_mode_active, audio_enabled):
        if self.sim_state != "running":
            return None

        # 1. 카메라 프레임 및 상태 데이터 획득
        frame_rgb = self._camera.get_frame_rgb()
        emotion = self._camera.emotion
        ear_value = self._camera.ear_value
        mar_value = self._camera.mar_value
        is_drowsy = self._camera.is_drowsy
        is_yawning = self._camera.is_yawning

        # 2. 안전 평가
        safety_eval = self._safety.evaluate(
            is_drowsy, is_yawning, emotion,
            sunlight_glare=self._env.sunlight_glare
        )

        # 3. CAN 버스 데이터 퍼블리싱 (Sensor Data)
        # ID: 0x120 -> Biometrics
        self.can_bus.send(0x120, [
            min(255, int(ear_value * 100)),
            min(255, int(mar_value * 100)),
            1 if is_drowsy else 0,
            1 if is_yawning else 0,
            0, 0, 0, 0
        ])
        
        # ID: 0x130 -> Env Sensor
        co2_int = int(self._env.co2_level)
        self.can_bus.send(0x130, [
            (co2_int >> 8) & 0xFF,
            co2_int & 0xFF,
            int(self._env.speed),
            1 if self._env.sunlight_glare else 0,
            1 if self._env.tunnel_entry else 0,
            0, 0, 0
        ])

        # 오디오 비프음
        if safety_eval["should_beep"] and audio_enabled:
            threading.Thread(target=lambda: winsound.Beep(1000, 300), daemon=True).start()

        # 4. AI 다감각 자동 제어 로직 적용
        ai_state_key = None
        ai_adjustments = None
        ai_preset = None
        
        self.solver_active = False # 매 프레임 초기화
        if auto_mode_active:
            ai_state_key, ai_adjustments, ai_preset = self._apply_auto(emotion)
            self._animate_sliders()

        # 5. CO2 물리 시뮬레이션
        self._simulate_co2()

        # 6. 차량 실내 온도 물리 시뮬레이션
        ambient_temp = 28.0
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

        # 7. 배터리 소모 계산 (업데이트 주기 33ms = 0.033초 가정)
        dt = 0.033
        # 속도 비례 구동 저항 + 공기 저항(속도 세제곱 비례) 물리 계산 모델링
        # 창문(틸팅) 개방 시 공기 저항이 추가되어 전력 소모 25% 가중치 적용
        drag_factor = 1.25 if self._env.window_tilting else 1.0
        v = self._env.speed
        p_drive = 0.05 * v + (0.00001 * (v ** 3)) * drag_factor
        p_ac = 0.0
        if self._env.power_on:
            if self._env.ac_on:
                # 냉방 모드 (콤프레셔 작동)
                p_ac = 0.2 + (0.8 * self._env.ac_fan_speed / 5.0) + max(0, self._env.cabin_temp - self._env.ac_temp) * 0.6
            elif self._env.ac_temp > self._env.cabin_temp:
                # 난방 모드 (PTC 히터 가동)
                p_ac = 0.2 + (0.8 * self._env.ac_fan_speed / 5.0) + (self._env.ac_temp - self._env.cabin_temp) * 1.2
            else:
                # 단순 송풍 모드
                p_ac = 0.15 + (0.5 * self._env.ac_fan_speed / 5.0)
                
        self._env.ac_power_draw = p_ac
        
        # SOC 감소 로직 (에너지 = 전력 * 시간)
        # 10배속 속도 조절
        SIM_SPEED_UP = 10.0
        energy_consumed = (p_drive + p_ac) * ((dt * SIM_SPEED_UP) / 3600.0)
        soc_decrease = (energy_consumed / self._env.battery_capacity) * 100.0
        self._env.soc = max(0.0, self._env.soc - soc_decrease)

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
            "co2_level": self._env.co2_level,
            "soc": self._env.soc,
            "ac_power_draw": self._env.ac_power_draw,
            "solver_active": self.solver_active,
            "solver_weights": self.solver_weights
        }

    def _solve_multi_objective_hvac(self, haptic_bonus=0):
        """배터리 SOC와 운전자 각성도를 고려한 멀티 오브젝티브 최적화 솔버"""
        # 가중치 결정
        if self._env.soc >= 50.0:
            w1, w2 = 0.2, 0.8
        elif self._env.soc >= 20.0:
            w1, w2 = 0.5, 0.5
        else:
            w1, w2 = 0.85, 0.15
            
        self.solver_weights = (w1, w2)
        
        best_cost = float('inf')
        best_temp = 22
        best_fan = 1
        best_ac_on = True

        for temp in range(16, 31):
            for fan in range(1, 6):
                # 전력 소모 예측 (냉방 기준)
                p_ac = 0.2 + (0.8 * fan / 5.0) + max(0, self._env.cabin_temp - temp) * 0.6
                
                # 각성도(Alertness) 점수 (0 ~ 10)
                # 온도가 낮을수록, 풍속이 높을수록 각성도 증가
                alertness = 0
                if temp <= 22:
                    alertness += (22 - temp) * 0.5
                alertness += fan * 0.8
                alertness += haptic_bonus # 햅틱 진동시 2점 추가
                
                alertness = min(10, alertness)
                
                cost = w1 * p_ac - w2 * alertness
                if cost < best_cost:
                    best_cost = cost
                    best_temp = temp
                    best_fan = fan
                    
        return best_temp, best_fan, True

    def _apply_auto(self, emotion):
        res = self._safety.get_auto_environment(
            emotion,
            sunlight_glare=self._env.sunlight_glare,
            tunnel_entry=self._env.tunnel_entry,
            co2_level=self._env.co2_level,
            speed=self._env.speed
        )
        preset = dict(res["preset"])

        # 최적화 적용 여부 판단
        # 위험(Danger) 또는 경고(Warning) 상태일 때 솔버 작동
        if self._safety.current_state in (SafetyState.DANGER, SafetyState.WARNING):
            self.solver_active = True
            haptic_bonus = 2 if preset.get("haptic_vibration", False) else 0
            opt_temp, opt_fan, opt_ac = self._solve_multi_objective_hvac(haptic_bonus)
            preset["ac_temp"] = opt_temp
            preset["ac_fan_speed"] = opt_fan
            preset["ac_on"] = opt_ac

        # 직접 변수에 접근하지 않고 CAN 버스로 명령 전송
        cmd_data = [
            1 if preset.get("power_on", True) else 0,
            1 if preset.get("ac_on", False) else 0,
            preset.get("ac_temp", 22),
            preset.get("ac_fan_speed", 1),
            1 if preset.get("ventilation_mode", "internal") == "external" else 0,
            1 if preset.get("window_tilting", False) else 0,
            1 if preset.get("airflow_direction", "indirect") == "direct" else 0,
            1 if preset.get("haptic_vibration", False) else 0
        ]
        self.can_bus.send(0x210, cmd_data)
        
        # 다감각 제어 상태는 환경 변수와 디스플레이에 즉각 업데이트할 항목들(여기서는 직접 반영)
        # (CAN을 통해 수신 처리할 수도 있지만, 로컬 지연 보상을 위해)
        self._env.audio_genre = preset.get("audio_genre", "None")
        self._env.audio_volume = preset.get("audio_volume", 30)
        self._env.ambient_light = preset.get("ambient_light", "Off")
        self._env.display_dark_mode = preset.get("display_dark_mode", False)
        self._env.display_brightness = preset.get("display_brightness", 80)
        self._env.seat_ventilation = preset.get("seat_ventilation", 0)
        self._env.seat_heater = preset.get("seat_heater", 0)

        current_key = (res["state_key"], tuple(sorted(res["adjustments"])))
        if self._last_ai_key != current_key or self.solver_active:
            self._last_ai_key = current_key
            return res["state_key"], res["adjustments"], preset

        return None, None, None

    def _simulate_co2(self):
        if self._env.ventilation_mode == "external" or self._env.window_tilting:
            self._env.co2_level -= 0.1 * (self._env.co2_level - 450.0) * 0.01
        else:
            self._env.co2_level += 0.3
        self._env.co2_level = max(400.0, min(2500.0, self._env.co2_level))

    def _animate_sliders(self):
        now = time.time()
        if now - self._last_anim_time > 0.2:
            moved = False
            if self._env.ac_temp < self.target_temp:
                self._env.ac_temp += 1
                moved = True
            elif self._env.ac_temp > self.target_temp:
                self._env.ac_temp -= 1
                moved = True

            if self._env.ac_fan_speed < self.target_fan:
                self._env.ac_fan_speed += 1
                moved = True
            elif self._env.ac_fan_speed > self.target_fan:
                self._env.ac_fan_speed -= 1
                moved = True

            if moved:
                self._last_anim_time = now
