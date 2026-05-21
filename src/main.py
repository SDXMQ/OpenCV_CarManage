"""
main.py - SEAVS 차량 콕핏 대시보드
"""

import customtkinter as ctk

from core.config_manager import ConfigManager
from core.safety_system import SafetyManager
from core.vehicle_env import VehicleEnvironment
from vision.camera import VideoCamera
from simulation.simulation_manager import SimulationManager

# UI 컴포넌트 임포트
from ui.header import HeaderFrame
from ui.driver_seat import DriverSeatFrame
from ui.center_display import CenterDisplayFrame
from ui.ac_panel import AcPanelFrame


class App(ctk.CTk):
    _UPDATE_MS = 33

    _BG = "#0a0a0f"
    _PANEL = "#12121c"
    _SCREEN = "#0b0c10"
    _ACCENT = "#00d2ff"
    _DIM = "#5f6f81"
    _MAIN = "#ecf0f1"

    def __init__(self):
        super().__init__()
        self.title("SEAVS - Smart Emotion-Aware Vehicle System")
        self.geometry("1200x820")
        self.minsize(1100, 750)
        self.configure(fg_color=self._BG)
        ctk.set_appearance_mode("dark")

        # 1. 코어 매니저 초기화
        self._config = ConfigManager()
        self._safety = SafetyManager()
        self._env = VehicleEnvironment()
        self._camera = VideoCamera(device_index=self._config.get("camera_index", 0))
        self._sim = SimulationManager(self._config, self._safety, self._env, self._camera)

        # 2. UI 변수 바인딩
        self._audio_enabled = ctk.BooleanVar(value=self._config.get("audio_alert", False))
        self._auto_mode_var = ctk.BooleanVar(value=False)
        self._power_var = ctk.BooleanVar(value=False)
        self._ac_var = ctk.BooleanVar(value=False)


        # 3. UI 그리기 및 장착
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        # 헤더 장착
        self._header = HeaderFrame(
            master=self,
            auto_mode_var=self._auto_mode_var,
            audio_enabled_var=self._audio_enabled,
            on_auto_toggle=self._on_auto_toggle,
            on_audio_toggle=self._on_audio_toggle,
            accent_color=self._ACCENT
        )
        self._header.pack(fill="x")

        # 바디 레이아웃
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=12, pady=(5, 0))
        body.grid_columnconfigure(0, weight=5)
        body.grid_columnconfigure(1, weight=4)
        body.grid_rowconfigure(0, weight=1)

        # 운전자석 장착
        devs = self._get_camera_devices()
        self._driver_seat = DriverSeatFrame(
            master=body,
            on_start=self._on_start,
            on_pause=self._on_pause,
            on_stop=self._on_stop,
            on_camera_change=self._on_camera_change,
            camera_devices=devs,
            current_camera_index=self._config.get("camera_index", 0),
            panel_color=self._PANEL,
            screen_color=self._SCREEN,
            dim_color=self._DIM,
            main_color=self._MAIN
        )
        self._driver_seat.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        # 센터 디스플레이 장착
        self._center_disp = CenterDisplayFrame(
            master=body,
            panel_color=self._PANEL,
            screen_color=self._SCREEN,
            accent_color=self._ACCENT,
            dim_color=self._DIM,
            main_color=self._MAIN
        )
        self._center_disp.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        # 에어컨 조작판 장착
        self._ac_panel = AcPanelFrame(
            master=self,
            power_var=self._power_var,
            ac_var=self._ac_var,
            on_power_toggle=self._on_power_toggle,
            on_ac_toggle=self._on_ac_toggle,
            on_temp_change=self._on_temp_change,
            on_fan_change=self._on_fan_change,
            panel_color=self._PANEL,
            accent_color=self._ACCENT,
            main_color=self._MAIN
        )
        self._ac_panel.pack(fill="x", padx=12, pady=(5, 10))


    # ═══════════════════════════════════════
    # 에어컨/헤더 조작 콜백
    # ═══════════════════════════════════════

    def _on_power_toggle(self):
        self._env.power_on = self._power_var.get()
        # 인터락 상태 업데이트
        self._ac_panel.set_interactive_state(self._env.power_on, self._env.auto_mode)
        # 로그 출력
        if self._env.power_on:
            self._center_disp.write_log("🔌 공조 시스템 메인 전원 ON", "#2ecc71")
        else:
            self._center_disp.write_log("🔌 공조 시스템 메인 전원 OFF", "#aaa")
            # 전원이 꺼지면 A/C 변수도 내부적으론 변경됨에 따라 UI 싱크
            self._ac_panel.update_ac_state(
                self._env.cabin_temp, self._env.ac_temp, self._env.ac_fan_speed,
                self._env.power_on, self._env.ac_on
            )

    def _on_ac_toggle(self):
        self._env.ac_on = self._ac_var.get()
        if self._env.ac_on:
            self._center_disp.write_log("❄ A/C 냉각 기능 활성화", "#00d2ff")
        else:
            self._center_disp.write_log("💨 A/C 냉각 기능 비활성화 (히터/송풍 가동)", "#aaa")

    def _on_temp_change(self, v):
        t = int(round(v))
        self._env.ac_temp = t
        self._ac_panel.update_ac_state(
            self._env.cabin_temp, t, self._env.ac_fan_speed,
            self._env.power_on, self._env.ac_on
        )
        self._sim.target_temp = t

    def _on_fan_change(self, v):
        f = int(round(v))
        self._env.ac_fan_speed = f
        self._ac_panel.update_ac_state(
            self._env.cabin_temp, self._env.ac_temp, f,
            self._env.power_on, self._env.ac_on
        )
        self._sim.target_fan = f

    def _on_auto_toggle(self):
        is_auto = self._auto_mode_var.get()
        self._env.auto_mode = is_auto

        # 에어컨 위젯들의 활성화 제어 및 테마 색상 갱신
        self._ac_panel.set_interactive_state(self._env.power_on, is_auto)
        self._ac_panel.set_accent_border(is_auto)
        self._header.update_badge(is_auto)

        if is_auto:
            self._center_disp.write_log("🤖 AI 에어컨 자동 제어 모드 시작", self._ACCENT)
            self._sim.target_temp = self._env.ac_temp
            self._sim.target_fan = self._env.ac_fan_speed
        else:
            self._center_disp.write_log("⚙ 수동 모드로 전환", "#aaa")


    def _on_audio_toggle(self):
        self._config.set_and_save("audio_alert", self._audio_enabled.get())

    def _on_camera_change(self, sel):
        try:
            idx = int(sel.split(":")[0])
        except Exception:
            idx = 0
        self._camera.change_device(idx)
        self._config.set_and_save("camera_index", idx)

    # ═══════════════════════════════════════
    # 시뮬레이션 라이프사이클 제어
    # ═══════════════════════════════════════

    def _on_start(self):
        was_paused = (self._sim.sim_state == "paused")
        try:
            log_msg, log_color = self._sim.start()
        except RuntimeError as e:
            self._center_disp.update_alert(str(e), "#e74c3c")
            return
        
        self._center_disp.write_log(log_msg, log_color)
        self._driver_seat.set_button_states("disabled", "normal", "normal")

        if not was_paused:
            self._update_loop()

    def _on_pause(self):
        log_msg, log_color = self._sim.pause()
        self._driver_seat.set_start_button_text("▶ 재개")
        self._driver_seat.set_button_states("normal", "disabled", "normal")
        self._center_disp.write_log(log_msg, log_color)

    def _on_stop(self):
        log_msg, log_color = self._sim.stop()

        # UI 요소 전체 리셋
        self._driver_seat.reset_ui()
        self._center_disp.reset_ui()
        self._ac_panel.reset_ui()
        self._power_var.set(False)
        self._ac_var.set(False)

        self._center_disp.write_log(log_msg, log_color)


    def _update_loop(self):
        if self._sim.sim_state == "stopped":
            return
        if self._sim.sim_state == "running":
            self._refresh()
        self.after(self._UPDATE_MS, self._update_loop)

    def _refresh(self):
        data = self._sim.update_step(
            auto_mode_active=self._auto_mode_var.get(),
            audio_enabled=self._audio_enabled.get()
        )
        if not data:
            return

        # 1. 비디오 프레임 렌더링
        self._driver_seat.update_camera_frame(data["frame_rgb"])

        # 2. 운전자 감정 및 EAR 갱신
        emo = data["emotion"]
        dom = emo.get("dominant", "neutral")
        emojis = {"neutral": "😐", "happy": "😊", "sad": "😢",
                  "angry": "😡", "fear": "😰", "surprise": "😲", "disgust": "🤢"}
        emotion_str = f"{emojis.get(dom, '😐')} {dom.capitalize()}"

        self._driver_seat.update_driver_state(emotion_str, data["ear_value"])

        # 3. 상세 감정 확률 텍스트 갱신
        scores = emo.get("scores", {})
        top_scores_text = ""
        if scores:
            top = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
            top_scores_text = "  ".join(f"{k}:{v:.0f}%" for k, v in top)
        self._center_disp.update_emotion(emotion_str, top_scores_text)

        # 4. 경고 배너 갱신
        safety = data["safety_eval"]
        self._center_disp.update_alert(safety["message"], safety["color"])

        # 5. AI 연동 에어컨 상태 UI 동기화
        if self._auto_mode_var.get():
            if data["ai_log"]:
                self._center_disp.write_log(data["ai_log"], data["ai_log_color"])

            self._power_var.set(data["power_on"])
            self._ac_var.set(data["ac_on"])
            self._ac_panel.set_interactive_state(data["power_on"], True)

        # 에어컨 상태 UI 동적 피드백 동기화 (자동/수동 공통)
        self._ac_panel.update_ac_state(
            data["cabin_temp"], data["ac_temp"], data["ac_fan_speed"],
            data["power_on"], data["ac_on"]
        )

        # 6. 에어컨 팬 및 바람 실시간 애니메이션 프레임 업데이트
        self._ac_panel.animate_step()


    # ═══════════════════════════════════════
    # 시스템 디바이스 쿼리
    # ═══════════════════════════════════════

    def _get_camera_devices(self):
        try:
            from pygrabber.dshow_graph import FilterGraph
            return {i: n for i, n in enumerate(FilterGraph().get_input_devices())}
        except Exception:
            return {0: "기본 카메라"}

    def _on_close(self):
        self._sim.stop()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
