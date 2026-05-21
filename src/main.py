"""
main.py - SEAVS 스마트 차량 대시보드 (CustomTkinter GUI)
순수 GUI 컴포넌트. ConfigManager, SafetyManager, VideoCamera, VehicleSimulator를 조율한다.
"""

import customtkinter as ctk
from PIL import Image
import threading
import winsound

from core.config_manager import ConfigManager
from core.safety_system import SafetyManager
from vision.camera import VideoCamera
from simulation.simulator import VehicleSimulator


class App(ctk.CTk):
    _UPDATE_INTERVAL_MS = 33

    def __init__(self):
        super().__init__()
        self.title("SEAVS - Smart Emotion-Aware Vehicle System")
        self.geometry("1100x700")
        self.minsize(900, 600)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # 코어 시스템 로드
        self._config = ConfigManager()
        self._safety = SafetyManager()
        
        # 하드웨어/시뮬레이션 인스턴스
        cam_idx = self._config.get("camera_index", 0)
        self._camera = VideoCamera(device_index=cam_idx)
        self._simulator = VehicleSimulator()

        self._sim_state = "stopped"
        
        # 설정 UI 변수 바인딩
        self._audio_alert_enabled = ctk.BooleanVar(value=self._config.get("audio_alert", False))

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        self._tabview = ctk.CTkTabview(self)
        self._tabview.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        tab_dashboard = self._tabview.add("🚗 운전 화면")
        tab_settings = self._tabview.add("⚙ 환경 설정")

        self._build_dashboard(tab_dashboard)
        self._build_settings(tab_settings)

    def _build_dashboard(self, parent):
        parent.grid_columnconfigure(0, weight=3)
        parent.grid_columnconfigure(1, weight=2)
        parent.grid_rowconfigure(0, weight=1)

        left_frame = ctk.CTkFrame(parent, corner_radius=12)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=0)
        left_frame.grid_rowconfigure(0, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        self._camera_label = ctk.CTkLabel(left_frame, text="카메라 대기 중...", font=ctk.CTkFont(size=16))
        self._camera_label.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        ctrl_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        ctrl_frame.grid(row=1, column=0, pady=(0, 10))

        self._btn_start = ctk.CTkButton(ctrl_frame, text="▶ 시작", width=100, command=self._on_start, fg_color="#2ecc71", hover_color="#27ae60")
        self._btn_start.grid(row=0, column=0, padx=5)

        self._btn_pause = ctk.CTkButton(ctrl_frame, text="⏸ 일시정지", width=100, command=self._on_pause, state="disabled", fg_color="#f39c12", hover_color="#e67e22")
        self._btn_pause.grid(row=0, column=1, padx=5)

        self._btn_stop = ctk.CTkButton(ctrl_frame, text="⏹ 정지", width=100, command=self._on_stop, state="disabled", fg_color="#e74c3c", hover_color="#c0392b")
        self._btn_stop.grid(row=0, column=2, padx=5)

        right_frame = ctk.CTkFrame(parent, corner_radius=12)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=0)
        right_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(right_frame, text="😊 감정 상태", font=ctk.CTkFont(size=15, weight="bold")).grid(row=0, column=0, pady=(10, 5), sticky="w", padx=15)
        self._emotion_label = ctk.CTkLabel(right_frame, text="Neutral", font=ctk.CTkFont(size=28, weight="bold"))
        self._emotion_label.grid(row=1, column=0, pady=(0, 5), padx=15, sticky="w")
        self._emotion_detail = ctk.CTkLabel(right_frame, text="대기 중", font=ctk.CTkFont(size=12), text_color="gray")
        self._emotion_detail.grid(row=2, column=0, padx=15, sticky="w")

        ctk.CTkLabel(right_frame, text="👁 눈 감김 지수 (EAR)", font=ctk.CTkFont(size=15, weight="bold")).grid(row=3, column=0, pady=(15, 5), sticky="w", padx=15)
        self._ear_bar = ctk.CTkProgressBar(right_frame, width=250)
        self._ear_bar.grid(row=4, column=0, padx=15, sticky="ew")
        self._ear_bar.set(0)
        self._ear_value_label = ctk.CTkLabel(right_frame, text="0.00", font=ctk.CTkFont(size=12))
        self._ear_value_label.grid(row=5, column=0, padx=15, sticky="w")

        ctk.CTkLabel(right_frame, text="🚘 차량 센서", font=ctk.CTkFont(size=15, weight="bold")).grid(row=6, column=0, pady=(15, 5), sticky="w", padx=15)
        self._speed_label = ctk.CTkLabel(right_frame, text="속도: 0 km/h", font=ctk.CTkFont(size=13))
        self._speed_label.grid(row=7, column=0, padx=15, sticky="w")
        self._rpm_label = ctk.CTkLabel(right_frame, text="RPM: 800", font=ctk.CTkFont(size=13))
        self._rpm_label.grid(row=8, column=0, padx=15, sticky="w")
        self._brake_label = ctk.CTkLabel(right_frame, text="브레이크: 0%", font=ctk.CTkFont(size=13))
        self._brake_label.grid(row=9, column=0, padx=15, sticky="w")

        self._alert_frame = ctk.CTkFrame(right_frame, corner_radius=8, fg_color="transparent")
        self._alert_frame.grid(row=10, column=0, pady=(15, 10), padx=15, sticky="ew")
        self._alert_label = ctk.CTkLabel(self._alert_frame, text="", font=ctk.CTkFont(size=14, weight="bold"))
        self._alert_label.pack(pady=5, padx=10)

    def _build_settings(self, parent):
        parent.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(parent, text="📷 카메라 선택", font=ctk.CTkFont(size=15, weight="bold")).grid(row=0, column=0, pady=(10, 5), padx=15, sticky="w")
        cam_frame = ctk.CTkFrame(parent, fg_color="transparent")
        cam_frame.grid(row=1, column=0, padx=15, sticky="ew")

        self._camera_devices = self._get_camera_devices()
        device_names = [f"{idx}: {name}" for idx, name in self._camera_devices.items()] or ["0: 기본 카메라"]

        self._cam_selector = ctk.CTkOptionMenu(cam_frame, values=device_names, command=self._on_camera_change, width=350)
        self._cam_selector.grid(row=0, column=0, pady=5)
        
        # 현재 설정된 카메라 번호를 찾아서 표시
        current_cam_idx = self._config.get("camera_index", 0)
        for name in device_names:
            if name.startswith(str(current_cam_idx) + ":"):
                self._cam_selector.set(name)
                break

        ctk.CTkButton(cam_frame, text="🔄", width=40, command=self._refresh_camera_list).grid(row=0, column=1, padx=(5, 0))

        ctk.CTkLabel(parent, text="🔊 오디오 경고", font=ctk.CTkFont(size=15, weight="bold")).grid(row=2, column=0, pady=(20, 5), padx=15, sticky="w")
        audio_frame = ctk.CTkFrame(parent, fg_color="transparent")
        audio_frame.grid(row=3, column=0, padx=15, sticky="ew")

        self._audio_switch = ctk.CTkSwitch(audio_frame, text="졸음/위험 경고음 재생", variable=self._audio_alert_enabled, command=self._on_audio_toggle)
        self._audio_switch.grid(row=0, column=0, pady=5)
        ctk.CTkLabel(parent, text="※ 변경 사항은 자동으로 저장됩니다.", font=ctk.CTkFont(size=11), text_color="gray").grid(row=4, column=0, padx=15, sticky="w")

    def _on_start(self):
        if self._sim_state == "paused":
            self._camera.resume()
            self._simulator.resume()
            self._sim_state = "running"
        else:
            try:
                self._camera.start()
            except RuntimeError as e:
                self._show_alert(str(e), "#e74c3c")
                return
            self._simulator.start()
            self._sim_state = "running"
            self._update_loop()

        self._btn_start.configure(state="disabled")
        self._btn_pause.configure(state="normal")
        self._btn_stop.configure(state="normal")

    def _on_pause(self):
        self._camera.pause()
        self._simulator.pause()
        self._sim_state = "paused"
        self._btn_start.configure(state="normal", text="▶ 재개")
        self._btn_pause.configure(state="disabled")

    def _on_stop(self):
        self._camera.stop()
        self._simulator.stop()
        self._sim_state = "stopped"
        
        self._camera_label.configure(image=None, text="카메라 대기 중...")
        self._camera_label.master.configure(border_width=0)
        self._emotion_label.configure(text="Neutral")
        self._emotion_detail.configure(text="대기 중")
        self._ear_bar.set(0)
        self._ear_value_label.configure(text="0.00")
        self._speed_label.configure(text="속도: 0 km/h")
        self._rpm_label.configure(text="RPM: 800")
        self._brake_label.configure(text="브레이크: 0%")
        self._alert_frame.configure(fg_color="transparent")
        self._alert_label.configure(text="")

        self._btn_start.configure(state="normal", text="▶ 시작")
        self._btn_pause.configure(state="disabled")
        self._btn_stop.configure(state="disabled")

    def _update_loop(self):
        if self._sim_state == "stopped": return
        if self._sim_state == "running":
            self._update_camera_feed()
            self._update_panels_and_logic()
        self.after(self._UPDATE_INTERVAL_MS, self._update_loop)

    def _update_camera_feed(self):
        frame_rgb = self._camera.get_frame_rgb()
        if frame_rgb is None: return

        lw, lh = self._camera_label.winfo_width(), self._camera_label.winfo_height()
        if lw < 10 or lh < 10: return

        pil_img = Image.fromarray(frame_rgb)
        img_w, img_h = pil_img.size
        ratio = min(lw / img_w, lh / img_h)
        pil_img = pil_img.resize((int(img_w * ratio), int(img_h * ratio)), Image.LANCZOS)
        
        ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=pil_img.size)
        self._camera_label.configure(image=ctk_img, text="")
        self._camera_label._ctk_image = ctk_img

    def _update_panels_and_logic(self):
        emotion = self._camera.emotion
        dom = emotion.get("dominant", "neutral")
        self._emotion_label.configure(text=f"{dom.capitalize()}")
        
        ear = self._camera.ear_value
        self._ear_bar.set(min(ear / 0.4, 1.0))
        self._ear_value_label.configure(text=f"{ear:.2f}")

        v_data = self._simulator.get_all()
        self._speed_label.configure(text=f"속도: {v_data['speed']} km/h")
        self._rpm_label.configure(text=f"RPM: {v_data['rpm']}")
        self._brake_label.configure(text=f"브레이크: {v_data['brake']}%")

        # 안전 매니저 판단
        decision = self._safety.evaluate(self._camera.is_drowsy, emotion, v_data["rapid_accel"])
        
        # 렌더링
        if decision["message"]:
            self._show_alert(decision["message"], decision["color"])
        else:
            self._alert_frame.configure(fg_color="transparent")
            self._alert_label.configure(text="")
            
        self._camera_label.master.configure(border_color=decision["color"], border_width=3)
        
        if decision["should_beep"] and self._audio_alert_enabled.get():
            threading.Thread(target=lambda: winsound.Beep(1000, 300), daemon=True).start()

    def _show_alert(self, msg, bg_color):
        self._alert_frame.configure(fg_color=bg_color)
        self._alert_label.configure(text=msg, text_color="white")

    def _get_camera_devices(self):
        try:
            from pygrabber.dshow_graph import FilterGraph
            return {i: name for i, name in enumerate(FilterGraph().get_input_devices())}
        except Exception:
            return {0: "기본 카메라"}

    def _refresh_camera_list(self):
        self._camera_devices = self._get_camera_devices()
        device_names = [f"{idx}: {name}" for idx, name in self._camera_devices.items()] or ["0: 기본 카메라"]
        self._cam_selector.configure(values=device_names)

    def _on_camera_change(self, selection):
        try: idx = int(selection.split(":")[0])
        except Exception: idx = 0
        self._camera.change_device(idx)
        self._config.set_and_save("camera_index", idx)

    def _on_audio_toggle(self):
        self._config.set_and_save("audio_alert", self._audio_alert_enabled.get())

    def _on_close(self):
        self._on_stop()
        self.destroy()

if __name__ == "__main__":
    App().mainloop()
