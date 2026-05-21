"""
main.py - SEAVS 차량 콕핏 대시보드
좌: 운전자석(카메라 고정)  |  우: 센터 디스플레이(상태+로그)  |  하: 단일 에어컨 제어판
"""

import customtkinter as ctk
from PIL import Image
import threading
import winsound
import time

from core.config_manager import ConfigManager
from core.safety_system import SafetyManager
from core.vehicle_env import VehicleEnvironment
from vision.camera import VideoCamera


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

        self._config = ConfigManager()
        self._safety = SafetyManager()
        self._env = VehicleEnvironment()
        self._camera = VideoCamera(device_index=self._config.get("camera_index", 0))

        self._sim_state = "stopped"
        self._audio_enabled = ctk.BooleanVar(value=self._config.get("audio_alert", False))
        self._auto_mode_var = ctk.BooleanVar(value=False)
        self._last_ai_log = ""
        
        # 애니메이션용 목표값
        self._target_temp = self._env.ac_temp
        self._target_fan = self._env.ac_fan_speed
        
        # 애니메이션 타이머 (초 단위 기록)
        self._last_anim_time = time.time()

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ═══════════════════════════════════════
    # UI
    # ═══════════════════════════════════════

    def _build_ui(self):
        self._build_header()

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=12, pady=(5, 0))
        body.grid_columnconfigure(0, weight=5) # 카메라 영역 비중
        body.grid_columnconfigure(1, weight=4) # 정보 영역 비중
        body.grid_rowconfigure(0, weight=1)

        self._build_driver_seat(body)
        self._build_center_display(body)
        self._build_ac_panel()

    # ── 헤더 ──

    def _build_header(self):
        h = ctk.CTkFrame(self, height=46, corner_radius=0, fg_color="#080812")
        h.pack(fill="x")
        h.pack_propagate(False)

        ctk.CTkLabel(h, text="◈ SEAVS",
                     font=ctk.CTkFont(family="Consolas", size=18, weight="bold"),
                     text_color=self._ACCENT).pack(side="left", padx=15)

        right = ctk.CTkFrame(h, fg_color="transparent")
        right.pack(side="right", padx=15)

        self._auto_badge = ctk.CTkLabel(right, text="● MANUAL",
                                        font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
                                        text_color="#888")
        self._auto_badge.pack(side="left", padx=(0, 10))

        self._auto_switch = ctk.CTkSwitch(right, text="AI 모드", variable=self._auto_mode_var,
                                          command=self._on_auto_toggle, width=50,
                                          progress_color=self._ACCENT, button_color="#fff",
                                          font=ctk.CTkFont(size=12, weight="bold"))
        self._auto_switch.pack(side="left", padx=(0, 15))

        self._audio_switch = ctk.CTkSwitch(right, text="🔊", variable=self._audio_enabled,
                                           command=self._on_audio_toggle, width=40,
                                           font=ctk.CTkFont(size=12))
        self._audio_switch.pack(side="left")

    # ── 좌: 운전자석 ──

    def _build_driver_seat(self, parent):
        seat = ctk.CTkFrame(parent, corner_radius=14, fg_color=self._PANEL,
                            border_width=1, border_color="#22223b")
        seat.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        seat.grid_rowconfigure(1, weight=1)
        seat.grid_columnconfigure(0, weight=1)

        # 타이틀
        tf = ctk.CTkFrame(seat, fg_color="#0d0d18", height=34, corner_radius=0)
        tf.grid(row=0, column=0, sticky="ew")
        tf.grid_propagate(False)
        ctk.CTkLabel(tf, text="👤 DRIVER VIEW",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=self._DIM).pack(side="left", padx=12, pady=5)

        # 카메라 - 크기 고정을 위해 프레임에 propagate False 설정
        # 부모인 seat의 1번 row가 expand되므로, cam 프레임도 expand됨
        self._cam_frame = ctk.CTkFrame(seat, fg_color=self._SCREEN, corner_radius=10)
        self._cam_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=8)
        self._cam_frame.grid_propagate(False) # 자식 위젯에 의해 크기 변형 방지
        self._cam_frame.grid_rowconfigure(0, weight=1)
        self._cam_frame.grid_columnconfigure(0, weight=1)

        self._cam_label = ctk.CTkLabel(self._cam_frame, text="카메라 대기 중\n\n▶ 시작 버튼을 누르세요",
                                       font=ctk.CTkFont(size=13), text_color="#3e4a56")
        self._cam_label.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        # 운전자 상태 바
        strip = ctk.CTkFrame(seat, fg_color=self._SCREEN, corner_radius=8, height=60)
        strip.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 6))
        strip.grid_propagate(False)
        strip.grid_columnconfigure((0, 1), weight=1)

        ef = ctk.CTkFrame(strip, fg_color="transparent")
        ef.grid(row=0, column=0, padx=12, pady=4, sticky="w")
        ctk.CTkLabel(ef, text="EMOTION", font=ctk.CTkFont(size=9), text_color=self._DIM).pack(anchor="w")
        self._emo_lbl = ctk.CTkLabel(ef, text="😐 Neutral",
                                     font=ctk.CTkFont(size=16, weight="bold"), text_color=self._MAIN)
        self._emo_lbl.pack(anchor="w")

        rf = ctk.CTkFrame(strip, fg_color="transparent")
        rf.grid(row=0, column=1, padx=12, pady=4, sticky="w")
        ctk.CTkLabel(rf, text="EAR (FATIGUE)", font=ctk.CTkFont(size=9), text_color=self._DIM).pack(anchor="w")
        rr = ctk.CTkFrame(rf, fg_color="transparent")
        rr.pack(anchor="w")
        self._ear_bar = ctk.CTkProgressBar(rr, width=100, height=10, progress_color="#2ecc71")
        self._ear_bar.pack(side="left")
        self._ear_bar.set(0)
        self._ear_val = ctk.CTkLabel(rr, text="0.00",
                                     font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
                                     text_color=self._MAIN)
        self._ear_val.pack(side="left", padx=(6, 0))

        # 버튼
        bf = ctk.CTkFrame(seat, fg_color="transparent")
        bf.grid(row=3, column=0, pady=(0, 6))

        self._btn_start = ctk.CTkButton(bf, text="▶ 시작", width=90, height=30,
                                        command=self._on_start,
                                        fg_color="#2ecc71", hover_color="#27ae60",
                                        font=ctk.CTkFont(size=11, weight="bold"))
        self._btn_start.grid(row=0, column=0, padx=3)
        self._btn_pause = ctk.CTkButton(bf, text="⏸", width=50, height=30,
                                        command=self._on_pause, state="disabled",
                                        fg_color="#f39c12", hover_color="#e67e22",
                                        font=ctk.CTkFont(size=11, weight="bold"))
        self._btn_pause.grid(row=0, column=1, padx=3)
        self._btn_stop = ctk.CTkButton(bf, text="⏹", width=50, height=30,
                                       command=self._on_stop, state="disabled",
                                       fg_color="#e74c3c", hover_color="#c0392b",
                                       font=ctk.CTkFont(size=11, weight="bold"))
        self._btn_stop.grid(row=0, column=2, padx=3)

        # 카메라 선택
        devs = self._get_camera_devices()
        names = [f"{i}: {n}" for i, n in devs.items()] or ["0: 기본 카메라"]
        self._cam_sel = ctk.CTkOptionMenu(seat, values=names, command=self._on_camera_change,
                                          width=200, font=ctk.CTkFont(size=10), fg_color="#1a1a2e")
        self._cam_sel.grid(row=4, column=0, pady=(0, 10))
        cur = self._config.get("camera_index", 0)
        for n in names:
            if n.startswith(str(cur) + ":"):
                self._cam_sel.set(n)
                break

    # ── 우: 센터 디스플레이 ──

    def _build_center_display(self, parent):
        disp = ctk.CTkFrame(parent, corner_radius=14, fg_color=self._PANEL,
                            border_width=1, border_color="#22223b")
        disp.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        disp.grid_columnconfigure(0, weight=1)
        disp.grid_rowconfigure(1, weight=1)
        disp.grid_rowconfigure(2, weight=2)

        # 타이틀
        tf = ctk.CTkFrame(disp, fg_color="#0d0d18", height=34, corner_radius=0)
        tf.grid(row=0, column=0, sticky="ew")
        tf.grid_propagate(False)
        ctk.CTkLabel(tf, text="🖥 CENTER DISPLAY",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=self._DIM).pack(side="left", padx=12, pady=5)

        # 상태 카드
        status = ctk.CTkFrame(disp, fg_color=self._SCREEN, corner_radius=10)
        status.grid(row=1, column=0, sticky="nsew", padx=10, pady=(8, 4))
        status.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(status, text="DRIVER STATUS",
                     font=ctk.CTkFont(family="Consolas", size=10),
                     text_color=self._ACCENT).grid(row=0, column=0, padx=15, pady=(10, 2), sticky="w")

        self._emo_main = ctk.CTkLabel(status, text="😐 Neutral",
                                      font=ctk.CTkFont(size=28, weight="bold"), text_color=self._MAIN)
        self._emo_main.grid(row=1, column=0, padx=15, sticky="w")

        self._emo_scores = ctk.CTkLabel(status, text="분석 대기 중...",
                                        font=ctk.CTkFont(family="Consolas", size=11), text_color=self._DIM)
        self._emo_scores.grid(row=2, column=0, padx=15, sticky="w", pady=(0, 4))

        # 경고판
        self._alert_f = ctk.CTkFrame(status, corner_radius=8, fg_color="transparent", height=44)
        self._alert_f.grid(row=3, column=0, padx=15, pady=(4, 10), sticky="ew")
        self._alert_lbl = ctk.CTkLabel(self._alert_f, text="",
                                       font=ctk.CTkFont(size=14, weight="bold"))
        self._alert_lbl.pack(pady=6, padx=10)

        # 로그
        log_f = ctk.CTkFrame(disp, fg_color=self._SCREEN, corner_radius=10)
        log_f.grid(row=2, column=0, sticky="nsew", padx=10, pady=(4, 10))
        log_f.grid_columnconfigure(0, weight=1)
        log_f.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(log_f, text="🤖 AI SYSTEM LOG",
                     font=ctk.CTkFont(family="Consolas", size=10),
                     text_color=self._ACCENT).grid(row=0, column=0, padx=15, pady=(8, 2), sticky="w")

        self._log = ctk.CTkTextbox(log_f, activate_scrollbars=True, wrap="word",
                                   font=ctk.CTkFont(family="Consolas", size=11),
                                   text_color=self._MAIN, fg_color="#08080f")
        self._log.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self._log.configure(state="disabled")

    # ── 하: 에어컨 제어판 ──

    def _build_ac_panel(self):
        self._ac_frame = ctk.CTkFrame(self, height=140, corner_radius=14,
                                      fg_color=self._PANEL, border_width=2, border_color="#22223b")
        self._ac_frame.pack(fill="x", padx=12, pady=(5, 10))
        self._ac_frame.pack_propagate(False)
        self._ac_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # 좌: 온도 표시
        temp_zone = ctk.CTkFrame(self._ac_frame, fg_color="#0d0d1a", corner_radius=10)
        temp_zone.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=8)

        ctk.CTkLabel(temp_zone, text="TEMPERATURE",
                     font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
                     text_color=self._ACCENT).pack(pady=(12, 2))

        self._temp_val = ctk.CTkLabel(temp_zone, text="22°C",
                                      font=ctk.CTkFont(size=42, weight="bold"), text_color=self._MAIN)
        self._temp_val.pack(pady=(5, 0))

        # 중앙: 온도 / 전원 슬라이더
        ctrl_zone = ctk.CTkFrame(self._ac_frame, fg_color="#0d0d1a", corner_radius=10)
        ctrl_zone.grid(row=0, column=1, sticky="nsew", padx=4, pady=8)

        self._ac_var = ctk.BooleanVar(value=False)
        self._ac_switch = ctk.CTkSwitch(ctrl_zone, text="A/C 전원", variable=self._ac_var,
                                        command=self._on_ac_toggle,
                                        progress_color="#2ecc71",
                                        font=ctk.CTkFont(size=12, weight="bold"))
        self._ac_switch.pack(pady=(12, 10))
        
        tf = ctk.CTkFrame(ctrl_zone, fg_color="transparent")
        tf.pack(fill="x", padx=20)
        ctk.CTkLabel(tf, text="16°C", font=ctk.CTkFont(size=10)).pack(side="left")
        ctk.CTkLabel(tf, text="30°C", font=ctk.CTkFont(size=10)).pack(side="right")
        
        self._temp_slider = ctk.CTkSlider(ctrl_zone, from_=16, to=30, number_of_steps=14,
                                          command=self._on_temp_change, width=220, height=16,
                                          button_color=self._ACCENT)
        self._temp_slider.set(22)
        self._temp_slider.pack(pady=5)

        # 우: 풍량 제어
        fan_zone = ctk.CTkFrame(self._ac_frame, fg_color="#0d0d1a", corner_radius=10)
        fan_zone.grid(row=0, column=2, sticky="nsew", padx=(4, 8), pady=8)

        ctk.CTkLabel(fan_zone, text="FAN SPEED",
                     font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
                     text_color=self._ACCENT).pack(pady=(12, 2))

        self._fan_val = ctk.CTkLabel(fan_zone, text="1 단",
                                     font=ctk.CTkFont(size=24, weight="bold"), text_color=self._MAIN)
        self._fan_val.pack(pady=(5, 5))
        
        self._fan_slider = ctk.CTkSlider(fan_zone, from_=0, to=5, number_of_steps=5,
                                         command=self._on_fan_change, width=180, height=16,
                                         button_color=self._ACCENT)
        self._fan_slider.set(1)
        self._fan_slider.pack(pady=5)


    # ═══════════════════════════════════════
    # 에어컨 콜백 (수동 조작 시)
    # ═══════════════════════════════════════

    def _on_ac_toggle(self):
        self._env.ac_on = self._ac_var.get()

    def _on_temp_change(self, v):
        t = int(round(v))
        self._env.ac_temp = t
        self._temp_val.configure(text=f"{t}°C")
        self._target_temp = t # 목표값 갱신

    def _on_fan_change(self, v):
        f = int(round(v))
        self._env.ac_fan_speed = f
        self._fan_val.configure(text=f"{f} 단")
        self._target_fan = f

    # ═══════════════════════════════════════
    # AI 모드
    # ═══════════════════════════════════════

    def _on_auto_toggle(self):
        is_auto = self._auto_mode_var.get()
        self._env.auto_mode = is_auto
        state = "disabled" if is_auto else "normal"

        for w in [self._ac_switch, self._fan_slider, self._temp_slider]:
            w.configure(state=state)

        if is_auto:
            self._auto_badge.configure(text="● AI ACTIVE", text_color=self._ACCENT)
            self._ac_frame.configure(border_color=self._ACCENT)
            self._log_write("🤖 AI 에어컨 자동 제어 모드 시작", self._ACCENT)
            # 현재값을 목표값으로 일치시킴
            self._target_temp = self._env.ac_temp
            self._target_fan = self._env.ac_fan_speed
        else:
            self._auto_badge.configure(text="● MANUAL", text_color="#888")
            self._ac_frame.configure(border_color="#22223b")
            self._log_write("⚙ 수동 모드로 전환", "#aaa")

    def _apply_auto(self):
        """AI 분석 결과를 가져와서 애니메이션 목표값을 갱신한다."""
        res = self._safety.get_auto_environment(self._camera.is_drowsy, self._camera.emotion)
        p = res["preset"]
        
        self._env.ac_on = p["ac_on"]
        self._ac_var.set(self._env.ac_on)
        
        # 목표값 갱신
        self._target_temp = p["ac_temp"]
        self._target_fan = p["ac_fan_speed"]

        if self._last_ai_log != res["log"]:
            self._last_ai_log = res["log"]
            self._log_write(res["log"], res["log_color"])

    def _animate_sliders(self):
        """AI가 설정한 목표값으로 슬라이더를 부드럽게(1칸씩) 이동시킨다."""
        now = time.time()
        # 0.2초마다 1칸씩 자연스럽게 이동
        if now - self._last_anim_time > 0.2:
            moved = False
            
            # 온도 이동
            if self._env.ac_temp < self._target_temp:
                self._env.ac_temp += 1
                moved = True
            elif self._env.ac_temp > self._target_temp:
                self._env.ac_temp -= 1
                moved = True
                
            # 풍량 이동
            if self._env.ac_fan_speed < self._target_fan:
                self._env.ac_fan_speed += 1
                moved = True
            elif self._env.ac_fan_speed > self._target_fan:
                self._env.ac_fan_speed -= 1
                moved = True
                
            if moved:
                # 슬라이더 및 라벨 갱신
                self._temp_slider.set(self._env.ac_temp)
                self._temp_val.configure(text=f"{self._env.ac_temp}°C")
                self._fan_slider.set(self._env.ac_fan_speed)
                self._fan_val.configure(text=f"{self._env.ac_fan_speed} 단")
                self._last_anim_time = now

    # ═══════════════════════════════════════
    # 로그
    # ═══════════════════════════════════════

    def _log_write(self, text, color):
        ts = time.strftime("%H:%M:%S")
        tag = f"t_{ts}_{id(text)}"
        self._log.configure(state="normal")
        self._log.insert("end", f"[{ts}] ", "dim")
        self._log.insert("end", f"{text}\n", tag)
        self._log.tag_config("dim", foreground=self._DIM)
        self._log.tag_config(tag, foreground=color)
        self._log.see("end")
        self._log.configure(state="disabled")

    # ═══════════════════════════════════════
    # 시뮬레이션
    # ═══════════════════════════════════════

    def _on_start(self):
        if self._sim_state == "paused":
            self._camera.resume()
            self._sim_state = "running"
            self._log_write("▶ 시스템 재개", self._ACCENT)
        else:
            try:
                self._camera.start()
            except RuntimeError as e:
                self._alert_f.configure(fg_color="#e74c3c")
                self._alert_lbl.configure(text=str(e), text_color="white")
                return
            self._sim_state = "running"
            self._log_write("▶ 시스템 시작", "#2ecc71")
            self._update_loop()

        self._btn_start.configure(state="disabled")
        self._btn_pause.configure(state="normal")
        self._btn_stop.configure(state="normal")

    def _on_pause(self):
        self._camera.pause()
        self._sim_state = "paused"
        self._btn_start.configure(state="normal", text="▶ 재개")
        self._btn_pause.configure(state="disabled")
        self._log_write("⏸ 일시정지", "#f39c12")

    def _on_stop(self):
        self._camera.stop()
        self._sim_state = "stopped"
        self._last_ai_log = ""

        self._cam_label.configure(image=None, text="카메라 대기 중\n\n▶ 시작 버튼을 누르세요")
        self._emo_lbl.configure(text="😐 Neutral")
        self._emo_main.configure(text="😐 Neutral")
        self._emo_scores.configure(text="분석 대기 중...")
        self._ear_bar.set(0)
        self._ear_bar.configure(progress_color="#2ecc71")
        self._ear_val.configure(text="0.00")
        self._alert_f.configure(fg_color="transparent")
        self._alert_lbl.configure(text="")

        self._btn_start.configure(state="normal", text="▶ 시작")
        self._btn_pause.configure(state="disabled")
        self._btn_stop.configure(state="disabled")
        self._log_write("⏹ 시스템 정지", "#e74c3c")

    def _update_loop(self):
        if self._sim_state == "stopped":
            return
        if self._sim_state == "running":
            self._refresh()
        self.after(self._UPDATE_MS, self._update_loop)

    def _refresh(self):
        # 카메라 갱신
        frame = self._camera.get_frame_rgb()
        if frame is not None:
            # 부모 프레임의 크기를 기반으로 리사이징 (propagate=False 덕분에 고정됨)
            lw, lh = self._cam_frame.winfo_width(), self._cam_frame.winfo_height()
            if lw > 10 and lh > 10:
                pil = Image.fromarray(frame)
                iw, ih = pil.size
                r = min(lw / iw, lh / ih)
                new_w, new_h = int(iw * r), int(ih * r)
                pil = pil.resize((new_w, new_h), Image.LANCZOS)
                img = ctk.CTkImage(light_image=pil, dark_image=pil, size=pil.size)
                self._cam_label.configure(image=img, text="")
                self._cam_label._ctk_image = img

        # 감정
        emo = self._camera.emotion
        dom = emo.get("dominant", "neutral")
        emojis = {"neutral": "😐", "happy": "😊", "sad": "😢",
                  "angry": "😡", "fear": "😰", "surprise": "😲", "disgust": "🤢"}
        txt = f"{emojis.get(dom, '😐')} {dom.capitalize()}"
        self._emo_lbl.configure(text=txt)
        self._emo_main.configure(text=txt)

        scores = emo.get("scores", {})
        if scores:
            top = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
            self._emo_scores.configure(text="  ".join(f"{k}:{v:.0f}%" for k, v in top))

        # EAR
        ear = self._camera.ear_value
        self._ear_bar.set(min(ear / 0.4, 1.0))
        self._ear_val.configure(text=f"{ear:.2f}")
        self._ear_bar.configure(progress_color="#e74c3c" if (0 < ear < 0.22) else "#2ecc71")

        # 안전 판단
        d = self._safety.evaluate(self._camera.is_drowsy, emo)
        if d["message"]:
            self._alert_f.configure(fg_color=d["color"])
            self._alert_lbl.configure(text=d["message"], text_color="white")
        else:
            self._alert_f.configure(fg_color="transparent")
            self._alert_lbl.configure(text="")

        if d["should_beep"] and self._audio_enabled.get():
            threading.Thread(target=lambda: winsound.Beep(1000, 300), daemon=True).start()

        # AI 모드
        if self._auto_mode_var.get():
            self._apply_auto()          # 목표값 갱신
            self._animate_sliders()     # 슬라이더 애니메이션 처리

    # ═══════════════════════════════════════
    # 설정
    # ═══════════════════════════════════════

    def _get_camera_devices(self):
        try:
            from pygrabber.dshow_graph import FilterGraph
            return {i: n for i, n in enumerate(FilterGraph().get_input_devices())}
        except Exception:
            return {0: "기본 카메라"}

    def _on_camera_change(self, sel):
        try:
            idx = int(sel.split(":")[0])
        except Exception:
            idx = 0
        self._camera.change_device(idx)
        self._config.set_and_save("camera_index", idx)

    def _on_audio_toggle(self):
        self._config.set_and_save("audio_alert", self._audio_enabled.get())

    def _on_close(self):
        self._sim_state = "stopped"
        self._camera.stop()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
