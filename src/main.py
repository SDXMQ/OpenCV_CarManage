"""
main.py - SEAVS 차량 콕핏 대시보드
"""

import logging
import os
import customtkinter as ctk

from core.config_manager import ConfigManager
from core.safety_system import SafetyManager, SafetyState
from core.vehicle_env import VehicleEnvironment
from vision.camera import VideoCamera
from simulation.simulation_manager import SimulationManager
from core.i18n import t, set_language

# UI 컴포넌트 임포트
from ui.header import HeaderFrame
from ui.driver_seat import DriverSeatFrame
from ui.center_display import CenterDisplayFrame
from ui.ac_panel import AcPanelFrame
from ui.settings_window import SettingsWindow

# 로깅 초기화 (콘솔 + 파일)
_LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "seavs.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(_LOG_FILE, encoding="utf-8"),
    ]
)
logger = logging.getLogger(__name__)


class App(ctk.CTk):
    _UPDATE_MS = 33

    _BG = "#0a0a0f"
    _PANEL = "#12121c"
    _SCREEN = "#0b0c10"
    _ACCENT = "#00d2ff"
    _DIM = "#5f6f81"
    _MAIN = "#ecf0f1"

    def _get_state_ui_info(self):
        return {
            SafetyState.DANGER: {"label": t("state_danger"), "message": t("msg_danger"), "color": "#e74c3c"},
            SafetyState.WARNING: {"label": t("state_warning"), "message": t("msg_warning"), "color": "#e67e22"},
            SafetyState.GLARE: {"label": t("state_glare"), "message": t("msg_glare"), "color": "#f39c12"},
            SafetyState.STRESS: {"label": t("state_stress"), "message": t("msg_stress"), "color": "#e67e22"},
            SafetyState.LOW_ENGAGEMENT: {"label": t("state_low_eng"), "message": t("msg_low_eng"), "color": "#9b59b6"},
            SafetyState.NORMAL: {"label": t("state_normal"), "message": t("msg_normal"), "color": "#3498db"},
        }

    # AI 자동제어 로그 템플릿 (state_key → 포맷 문자열)
    _AUTO_LOG_TEMPLATES = {
        "danger": "😪 졸음 감지 → 쿨링 펀치({ac_temp}°C/{ac_fan_speed}단), 외기유입, 창문 틸팅, 직바람, {audio_genre} {audio_volume}%, 시트 통풍 {seat_ventilation}단, 햅틱 진동 ON",
        "warning": "🥱 하품 감지 → 냉각 강화({ac_temp}°C/{ac_fan_speed}단), 외기유입, 직바람, {audio_genre} {audio_volume}%, 시트 통풍 {seat_ventilation}단",
        "stress": "😤 스트레스 감지 → {ac_temp}°C 외기 간접풍, 앰버 무드등, {audio_genre} {audio_volume}%, 시트 통풍 {seat_ventilation}단",
        "low_engagement": "😶 집중력 저하 → {ac_temp}°C 외기 간접풍, 그린 무드등, {audio_genre} {audio_volume}%, 시트 열선 {seat_heater}단",
        "happy": "😊 쾌적 → {ac_temp}°C 표준 유지, 그린 무드등",
        "normal": "😐 평온 → {ac_temp}°C 표준 유지",
    }

    _AUTO_LOG_COLORS = {
        "danger": "#e74c3c",
        "warning": "#e67e22",
        "stress": "#e67e22",
        "low_engagement": "#9b59b6",
        "happy": "#2ecc71",
        "normal": "#3498db",
    }

    _ADJUSTMENT_LABELS = {
        "glare": "☀눈부심 차광 제어(다크 40%, 앰버 무드등)",
        "tunnel": "🌑터널 자동 감광/내기순환",
        "co2_window": "💨이산화탄소 환기(외기유입+창문 개방)",
        "co2_external": "💨이산화탄소 환기(외기유입 강제)",
        "high_speed_window": "🚗고속 안전 제어(창문 닫힘)",
    }

    def __init__(self):
        super().__init__()
        self.title("SEAVS - Smart Emotion-Aware Vehicle System")
        self.geometry("1200x820")
        self.minsize(1100, 750)
        self.configure(fg_color=self._BG)
        ctk.set_appearance_mode("dark")

        # 1. 코어 매니저 초기화 및 설정 적용
        self._config = ConfigManager()
        set_language(self._config.get("language", "ko"))
        
        self.title(t("title"))
        
        # 프로필 로드 설정
        current_prof = self._config.get("current_profile", "default")
        self._safety = SafetyManager(current_profile=current_prof)
        self._env = VehicleEnvironment()
        self._camera = VideoCamera(
            device_index=self._config.get("camera_index", 0),
            mirror_camera=self._config.get("mirror_camera", False)
        )
        # 카메라에 초기 프로필 데이터 주입
        self._camera.set_active_profile(self._safety.active_profile_data)
        
        self._sim = SimulationManager(self._config, self._safety, self._env, self._camera)

        # 2. UI 변수 바인딩
        self._audio_enabled = ctk.BooleanVar(value=self._config.get("audio_alert", False))
        self._auto_mode_var = ctk.BooleanVar(value=False)
        self._power_var = ctk.BooleanVar(value=False)
        self._ac_var = ctk.BooleanVar(value=False)

        # 환경 시뮬레이터 변수
        self._glare_var = ctk.BooleanVar(value=False)
        self._tunnel_var = ctk.BooleanVar(value=False)
        self._co2_var = ctk.DoubleVar(value=800.0)
        self._speed_var = ctk.DoubleVar(value=80.0)


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
            on_settings_click=self._on_settings_click,
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
            main_color=self._MAIN,
            glare_var=self._glare_var,
            tunnel_var=self._tunnel_var,
            co2_var=self._co2_var,
            speed_var=self._speed_var,
            on_glare_toggle=self._on_glare_toggle,
            on_tunnel_toggle=self._on_tunnel_toggle,
            on_co2_change=self._on_co2_change,
            on_speed_change=self._on_speed_change,
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
            on_vent_click=self._on_vent_click,
            on_win_click=self._on_win_click,
            on_air_click=self._on_air_click,
            on_audio_click=self._on_audio_click,
            on_seat_click=self._on_seat_click,
            on_haptic_click=self._on_haptic_click,
            panel_color=self._PANEL,
            accent_color=self._ACCENT,
            main_color=self._MAIN
        )
        self._ac_panel.pack(fill="x", padx=12, pady=(5, 10))


    # ═══════════════════════════════════════
    # 로그 출력 도우미
    # ═══════════════════════════════════════

    def _write_log(self, text, color, force=False):
        if force or self._sim.sim_state != "stopped":
            self._center_disp.write_log(text, color)

    # ═══════════════════════════════════════
    # 에어컨/헤더 조작 콜백
    # ═══════════════════════════════════════

    def _on_settings_click(self):
        # 모달창 열기
        SettingsWindow(self, self._config, self._camera, self._safety, self._on_settings_saved)

    def _on_settings_saved(self):
        # 설정창에서 저장이 완료되었을 때 호출 (다국어 등 갱신)
        self.title(t("title"))
        # 모든 정적 UI 업데이트
        self._header._settings_btn.configure(text=t("btn_settings"))
        self._driver_seat._start_btn.configure(text=t("btn_start"))
        self._driver_seat._pause_btn.configure(text=t("btn_pause"))
        self._driver_seat._stop_btn.configure(text=t("btn_stop"))
        
        # 재렌더링 시 현재 상태 UI 강제 갱신
        self._refresh_static_texts()

    def _refresh_static_texts(self):
        # 헤더 등은 동적 렌더링되지만 고정 라벨들은 여기서 갱신해준다
        pass # 전체 프레임을 다 뜯어고치기보단 최소한의 갱신만 수행

    def _on_power_toggle(self):
        self._env.power_on = self._power_var.get()
        self._ac_panel.set_interactive_state(self._env.power_on, self._env.auto_mode)
        if self._env.power_on:
            self._write_log("🔌 공조 시스템 메인 전원 ON", "#2ecc71")
        else:
            self._write_log("🔌 공조 시스템 메인 전원 OFF", "#aaa")
            self._ac_panel.update_ac_state(
                self._env.cabin_temp, self._env.ac_temp, self._env.ac_fan_speed,
                self._env.power_on, self._env.ac_on
            )

    def _on_ac_toggle(self):
        self._env.ac_on = self._ac_var.get()
        if self._env.ac_on:
            self._write_log("❄ A/C 냉각 기능 활성화", "#00d2ff")
        else:
            self._write_log("💨 A/C 냉각 기능 비활성화 (히터/송풍 가동)", "#aaa")

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

        self._ac_panel.set_interactive_state(self._env.power_on, is_auto)
        self._ac_panel.set_accent_border(is_auto)
        self._header.update_badge(is_auto)

        if is_auto:
            self._write_log("🤖 AI 다감각 자동 제어 모드 시작", self._ACCENT)
            self._sim.target_temp = self._env.ac_temp
            self._sim.target_fan = self._env.ac_fan_speed
        else:
            self._write_log("⚙ 수동 모드로 전환", "#aaa")


    def _on_audio_toggle(self):
        self._config.set_and_save("audio_alert", self._audio_enabled.get())

    def _on_vent_click(self):
        self._env.ventilation_mode = "external" if self._env.ventilation_mode == "internal" else "internal"
        mode_str = "💨 외기유입" if self._env.ventilation_mode == "external" else "♻ 내기순환"
        self._write_log(f"⚙ [수동 제어] 환기 모드 변경 ➔ {mode_str}", "#00d2ff")

    def _on_win_click(self):
        self._env.window_tilting = not self._env.window_tilting
        win_str = "🪟 틸팅 개방" if self._env.window_tilting else "🪟 닫힘"
        self._write_log(f"⚙ [수동 제어] 창문 상태 변경 ➔ {win_str}", "#f39c12")

    def _on_air_click(self):
        self._env.airflow_direction = "direct" if self._env.airflow_direction == "indirect" else "indirect"
        air_str = "🌀 직바람" if self._env.airflow_direction == "direct" else "🍃 간접풍"
        self._write_log(f"⚙ [수동 제어] 풍향 변경 ➔ {air_str}", "#e74c3c")

    def _on_audio_click(self):
        genres = ["None", "Classic", "Pop", "Dance"]
        current = self._env.audio_genre
        idx = (genres.index(current) + 1) % len(genres)
        next_genre = genres[idx]
        
        self._env.audio_genre = next_genre
        vols = {"None": 0, "Classic": 30, "Pop": 60, "Dance": 80}
        self._env.audio_volume = vols[next_genre]
        
        self._write_log(f"⚙ [수동 제어] 오디오 장르 변경 ➔ 🎵 {next_genre} (볼륨: {self._env.audio_volume}%)", "#2ecc71")

    def _on_seat_click(self):
        v = self._env.seat_ventilation
        h = self._env.seat_heater
        
        if v == 0 and h == 0:
            self._env.seat_heater = 1
            self._env.seat_ventilation = 0
            log_str = "♨ 열선 1단"
        elif h == 1:
            self._env.seat_heater = 2
            self._env.seat_ventilation = 0
            log_str = "♨ 열선 2단"
        elif h == 2:
            self._env.seat_heater = 0
            self._env.seat_ventilation = 1
            log_str = "💺 통풍 1단"
        elif v == 1:
            self._env.seat_heater = 0
            self._env.seat_ventilation = 2
            log_str = "💺 통풍 2단"
        elif v == 2:
            self._env.seat_heater = 0
            self._env.seat_ventilation = 3
            log_str = "💺 통풍 3단"
        else:
            self._env.seat_heater = 0
            self._env.seat_ventilation = 0
            log_str = "💺 OFF"
            
        self._write_log(f"⚙ [수동 제어] 운전석 시트 변경 ➔ {log_str}", "#e67e22")

    def _on_haptic_click(self):
        self._env.haptic_vibration = not self._env.haptic_vibration
        haptic_str = "📳 진동 ON" if self._env.haptic_vibration else "📳 OFF"
        self._write_log(f"⚙ [수동 제어] 햅틱 진동 변경 ➔ {haptic_str}", "#e74c3c")

    def _on_camera_change(self, sel):
        try:
            idx = int(sel.split(":")[0])
        except (ValueError, IndexError):
            idx = 0
        self._camera.change_device(idx)
        self._config.set_and_save("camera_index", idx)

    # ═══════════════════════════════════════
    # 환경 시뮬레이터 콜백
    # ═══════════════════════════════════════

    def _on_glare_toggle(self):
        self._env.sunlight_glare = self._glare_var.get()

    def _on_tunnel_toggle(self):
        self._env.tunnel_entry = self._tunnel_var.get()

    def _on_co2_change(self, v):
        val = float(v)
        self._env.co2_level = val
        self._center_disp.update_co2_label(val)

    def _on_speed_change(self, v):
        val = float(v)
        self._env.speed = val
        self._center_disp.update_speed_label(val)

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
        
        self._write_log(log_msg, log_color, force=True)
        self._driver_seat.set_button_states("disabled", "normal", "normal")

        if not was_paused:
            self._update_loop()

    def _on_pause(self):
        log_msg, log_color = self._sim.pause()
        self._driver_seat.set_start_button_text("▶ 재개")
        self._driver_seat.set_button_states("normal", "disabled", "normal")
        self._write_log(log_msg, log_color, force=True)

    def _on_stop(self):
        log_msg, log_color = self._sim.stop()

        # UI 요소 전체 리셋
        self._driver_seat.reset_ui()
        self._center_disp.reset_ui()
        self._ac_panel.reset_ui()
        self._power_var.set(False)
        self._ac_var.set(False)
        self._glare_var.set(False)
        self._tunnel_var.set(False)
        self._env.sunlight_glare = False
        self._env.tunnel_entry = False

        self._write_log(log_msg, log_color, force=True)


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

        # 2. 운전자 상태 텍스트 매핑
        safety = data["safety_eval"]
        state = safety["state"]  # SafetyState enum
        ui_info = self._get_state_ui_info()[state]

        # happy 감정일 때는 별도 UI 표시
        emo = data["emotion"]
        dominant = emo.get("dominant", "neutral")
        if state == SafetyState.NORMAL and dominant == "happy":
            state_str = "😊 쾌적"
            alert_msg = "😊 쾌적한 주행 중"
            alert_color = "#2ecc71"
        else:
            state_str = ui_info["label"]
            alert_msg = ui_info["message"]
            alert_color = ui_info["color"]

        self._driver_seat.update_driver_state(state_str, data["ear_value"], data["mar_value"])

        # 3. 상세 감정 확률 텍스트 갱신
        scores = emo.get("scores", {})
        top_scores_text = ""
        if scores:
            top = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
            top_scores_text = "  ".join(f"{k}:{v:.0f}%" for k, v in top)
        self._center_disp.update_state_display(state_str, top_scores_text)

        # 4. 경고 배너 갱신
        self._center_disp.update_alert(alert_msg, alert_color)

        # 5. CO2 물리 시뮬레이션 UI 동기화
        self._center_disp.update_env_display(data["co2_level"])

        # 6. AI 연동 에어컨 상태 UI 동기화
        if self._auto_mode_var.get():
            if data["ai_state_key"]:
                log_text = self._build_auto_log(
                    data["ai_state_key"], data["ai_adjustments"], data["ai_preset"]
                )
                log_color = self._get_auto_log_color(
                    data["ai_state_key"], data["ai_adjustments"]
                )
                self._write_log(log_text, log_color)

            self._power_var.set(data["power_on"])
            self._ac_var.set(data["ac_on"])
            self._ac_panel.set_interactive_state(data["power_on"], True)

        # 에어컨 상태 UI 동적 피드백 동기화 (자동/수동 공통)
        self._ac_panel.update_ac_state(
            data["cabin_temp"], data["ac_temp"], data["ac_fan_speed"],
            data["power_on"], data["ac_on"]
        )

        # 7. 다감각 차량 제어 상태 배지 업데이트
        self._ac_panel.update_vehicle_status(
            data["ventilation_mode"],
            data["window_tilting"],
            data["airflow_direction"],
            data["audio_genre"],
            data["audio_volume"],
            data["seat_ventilation"],
            data["seat_heater"],
            data["haptic_vibration"]
        )

        # 8. 에어컨 팬 및 바람 실시간 애니메이션 프레임 업데이트
        self._ac_panel.animate_step()


    # ═══════════════════════════════════════
    # 시스템 디바이스 쿼리
    # ═══════════════════════════════════════

    def _get_camera_devices(self):
        try:
            from pygrabber.dshow_graph import FilterGraph
            return {i: n for i, n in enumerate(FilterGraph().get_input_devices())}
        except ImportError:
            logger.info("pygrabber 미설치 - 기본 카메라 사용")
            return {0: "기본 카메라"}
        except RuntimeError as e:
            logger.warning("카메라 장치 조회 실패: %s", e)
            return {0: "기본 카메라"}

    # ═══════════════════════════════════════
    # AI 자동제어 로그 빌더 (UI 레이어)
    # ═══════════════════════════════════════

    def _build_auto_log(self, state_key, adjustments, preset):
        """AI 자동제어 상태 변경 시 UI 로그 문자열을 조립한다."""
        template = self._AUTO_LOG_TEMPLATES.get(state_key, "")
        log = template.format(**preset)
        if adjustments:
            adj_labels = [self._ADJUSTMENT_LABELS.get(a, a) for a in adjustments]
            log += " + [" + ", ".join(adj_labels) + "]"
        return log

    def _get_auto_log_color(self, state_key, adjustments):
        """상태와 보정 조건에 따라 로그 색상을 결정한다."""
        base_color = self._AUTO_LOG_COLORS.get(state_key, "#3498db")
        if adjustments and base_color not in ("#e74c3c", "#e67e22"):
            return "#f39c12"
        return base_color

    def _on_close(self):
        self._sim.stop()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
