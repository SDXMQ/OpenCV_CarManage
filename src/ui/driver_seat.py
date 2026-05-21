"""
driver_seat.py - 운전자석 카메라 및 제어판 UI 컴포넌트
"""

import customtkinter as ctk
from PIL import Image

class DriverSeatFrame(ctk.CTkFrame):
    def __init__(self, master, on_start, on_pause, on_stop, on_camera_change, camera_devices, current_camera_index,
                 panel_color="#12121c", screen_color="#0b0c10", dim_color="#5f6f81", main_color="#ecf0f1"):
        super().__init__(master, corner_radius=14, fg_color=panel_color, border_width=1, border_color="#22223b")
        
        self._screen_color = screen_color
        self._dim_color = dim_color
        self._main_color = main_color

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. 타이틀
        tf = ctk.CTkFrame(self, fg_color="#0d0d18", height=34, corner_radius=0)
        tf.grid(row=0, column=0, sticky="ew")
        tf.grid_propagate(False)
        ctk.CTkLabel(tf, text="👤 DRIVER VIEW",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=self._dim_color).pack(side="left", padx=12, pady=5)

        # 2. 카메라 화면 프레임
        self._cam_frame = ctk.CTkFrame(self, fg_color=self._screen_color, corner_radius=10)
        self._cam_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=8)
        self._cam_frame.grid_propagate(False)
        self._cam_frame.grid_rowconfigure(0, weight=1)
        self._cam_frame.grid_columnconfigure(0, weight=1)

        self._cam_label = ctk.CTkLabel(self._cam_frame, text="카메라 대기 중\n\n▶ 시작 버튼을 누르세요",
                                       font=ctk.CTkFont(size=13), text_color="#3e4a56")
        self._cam_label.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        # 3. 운전자 상태 요약 스트립
        strip = ctk.CTkFrame(self, fg_color=self._screen_color, corner_radius=8, height=60)
        strip.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 6))
        strip.grid_propagate(False)
        strip.grid_columnconfigure((0, 1), weight=1)

        # 감정 요약
        ef = ctk.CTkFrame(strip, fg_color="transparent")
        ef.grid(row=0, column=0, padx=12, pady=4, sticky="w")
        ctk.CTkLabel(ef, text="EMOTION", font=ctk.CTkFont(size=9), text_color=self._dim_color).pack(anchor="w")
        self._emo_lbl = ctk.CTkLabel(ef, text="😐 Neutral",
                                     font=ctk.CTkFont(size=16, weight="bold"), text_color=self._main_color)
        self._emo_lbl.pack(anchor="w")

        # 피로도 (EAR) 요약
        rf = ctk.CTkFrame(strip, fg_color="transparent")
        rf.grid(row=0, column=1, padx=12, pady=4, sticky="w")
        ctk.CTkLabel(rf, text="EAR (FATIGUE)", font=ctk.CTkFont(size=9), text_color=self._dim_color).pack(anchor="w")
        rr = ctk.CTkFrame(rf, fg_color="transparent")
        rr.pack(anchor="w")
        self._ear_bar = ctk.CTkProgressBar(rr, width=100, height=10, progress_color="#2ecc71")
        self._ear_bar.pack(side="left")
        self._ear_bar.set(0)
        self._ear_val = ctk.CTkLabel(rr, text="0.00",
                                     font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
                                     text_color=self._main_color)
        self._ear_val.pack(side="left", padx=(6, 0))

        # 4. 제어 버튼
        bf = ctk.CTkFrame(self, fg_color="transparent")
        bf.grid(row=3, column=0, pady=(0, 6))

        self._btn_start = ctk.CTkButton(bf, text="▶ 시작", width=90, height=30,
                                        command=on_start,
                                        fg_color="#2ecc71", hover_color="#27ae60",
                                        font=ctk.CTkFont(size=11, weight="bold"))
        self._btn_start.grid(row=0, column=0, padx=3)
        self._btn_pause = ctk.CTkButton(bf, text="⏸", width=50, height=30,
                                        command=on_pause, state="disabled",
                                        fg_color="#f39c12", hover_color="#e67e22",
                                        font=ctk.CTkFont(size=11, weight="bold"))
        self._btn_pause.grid(row=0, column=1, padx=3)
        self._btn_stop = ctk.CTkButton(bf, text="⏹", width=50, height=30,
                                       command=on_stop, state="disabled",
                                       fg_color="#e74c3c", hover_color="#c0392b",
                                       font=ctk.CTkFont(size=11, weight="bold"))
        self._btn_stop.grid(row=0, column=2, padx=3)

        # 5. 카메라 선택 옵션 메뉴
        names = [f"{i}: {n}" for i, n in camera_devices.items()] or ["0: 기본 카메라"]
        self._cam_sel = ctk.CTkOptionMenu(self, values=names, command=on_camera_change,
                                          width=200, font=ctk.CTkFont(size=10), fg_color="#1a1a2e")
        self._cam_sel.grid(row=4, column=0, pady=(0, 10))
        
        for n in names:
            if n.startswith(str(current_camera_index) + ":"):
                self._cam_sel.set(n)
                break

    def update_camera_frame(self, frame_rgb):
        if frame_rgb is not None:
            lw, lh = self._cam_frame.winfo_width(), self._cam_frame.winfo_height()
            if lw > 10 and lh > 10:
                pil = Image.fromarray(frame_rgb)
                iw, ih = pil.size
                r = min(lw / iw, lh / ih)
                new_w, new_h = int(iw * r), int(ih * r)
                pil = pil.resize((new_w, new_h), Image.LANCZOS)
                img = ctk.CTkImage(light_image=pil, dark_image=pil, size=pil.size)
                self._cam_label.configure(image=img, text="")
                self._cam_label._ctk_image = img

    def update_driver_state(self, emotion_text, ear_value):
        self._emo_lbl.configure(text=emotion_text)
        self._ear_bar.set(min(ear_value / 0.4, 1.0))
        self._ear_val.configure(text=f"{ear_value:.2f}")
        self._ear_bar.configure(progress_color="#e74c3c" if (0 < ear_value < 0.22) else "#2ecc71")

    def set_button_states(self, start_state, pause_state, stop_state):
        self._btn_start.configure(state=start_state)
        self._btn_pause.configure(state=pause_state)
        self._btn_stop.configure(state=stop_state)

    def set_start_button_text(self, text):
        self._btn_start.configure(text=text)

    def reset_ui(self):
        self._cam_label.configure(image=None, text="카메라 대기 중\n\n▶ 시작 버튼을 누르세요")
        self._emo_lbl.configure(text="😐 Neutral")
        self._ear_bar.set(0)
        self._ear_bar.configure(progress_color="#2ecc71")
        self._ear_val.configure(text="0.00")
        self.set_button_states("normal", "disabled", "disabled")
        self.set_start_button_text("▶ 시작")
