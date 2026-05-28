"""
center_display.py - 센터 디스플레이 정보, 환경 시뮬레이터 및 로그 UI 컴포넌트
"""

import time
import customtkinter as ctk

class CenterDisplayFrame(ctk.CTkFrame):
    def __init__(self, master, panel_color="#12121c", screen_color="#0b0c10", accent_color="#00d2ff",
                 dim_color="#5f6f81", main_color="#ecf0f1",
                 glare_var=None, tunnel_var=None, co2_var=None, speed_var=None,
                 on_glare_toggle=None, on_tunnel_toggle=None,
                 on_co2_change=None, on_speed_change=None, on_charge_click=None):
        super().__init__(master, corner_radius=14, fg_color=panel_color, border_width=1, border_color="#22223b")
        
        self._screen_color = screen_color
        self._accent = accent_color
        self._dim_color = dim_color
        self._main_color = main_color

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=1)
        self.grid_rowconfigure(4, weight=2)

        # 1. 타이틀
        tf = ctk.CTkFrame(self, fg_color="#0d0d18", height=34, corner_radius=0)
        tf.grid(row=0, column=0, sticky="ew")
        tf.grid_propagate(False)
        ctk.CTkLabel(tf, text="🖥 CENTER DISPLAY",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=self._dim_color).pack(side="left", padx=12, pady=5)

        # 2. 운전자 상태 상세 카드
        status = ctk.CTkFrame(self, fg_color=self._screen_color, corner_radius=10)
        status.grid(row=1, column=0, sticky="nsew", padx=10, pady=(8, 4))
        status.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(status, text="DRIVER STATE",
                     font=ctk.CTkFont(family="Consolas", size=10),
                     text_color=self._accent).grid(row=0, column=0, padx=15, pady=(10, 2), sticky="w")

        self._state_main = ctk.CTkLabel(status, text="😐 정상",
                                      font=ctk.CTkFont(size=28, weight="bold"), text_color=self._main_color)
        self._state_main.grid(row=1, column=0, padx=15, sticky="w")

        self._state_scores = ctk.CTkLabel(status, text="분석 대기 중...",
                                        font=ctk.CTkFont(family="Consolas", size=11), text_color=self._dim_color)
        self._state_scores.grid(row=2, column=0, padx=15, sticky="w", pady=(0, 4))

        # 경고 알림판
        self._alert_f = ctk.CTkFrame(status, corner_radius=8, fg_color="transparent", height=44)
        self._alert_f.grid(row=3, column=0, padx=15, pady=(4, 10), sticky="ew")
        self._alert_lbl = ctk.CTkLabel(self._alert_f, text="",
                                       font=ctk.CTkFont(size=14, weight="bold"))
        self._alert_lbl.pack(pady=6, padx=10)

        # 3. 환경 시뮬레이터 패널
        env_f = ctk.CTkFrame(self, fg_color=self._screen_color, corner_radius=10)
        env_f.grid(row=2, column=0, sticky="nsew", padx=10, pady=(4, 4))
        env_f.grid_columnconfigure(0, weight=1)
        env_f.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(env_f, text="🌍 ENVIRONMENT SIMULATOR",
                     font=ctk.CTkFont(family="Consolas", size=10),
                     text_color=self._accent).grid(row=0, column=0, columnspan=2, padx=15, pady=(8, 4), sticky="w")

        # 좌측: 스위치 (눈부심, 터널)
        sw_f = ctk.CTkFrame(env_f, fg_color="transparent")
        sw_f.grid(row=1, column=0, padx=15, pady=(0, 8), sticky="w")

        self._glare_sw = ctk.CTkSwitch(sw_f, text="☀ 눈부심",
                                       variable=glare_var, command=on_glare_toggle,
                                       progress_color="#f39c12",
                                       font=ctk.CTkFont(size=11))
        self._glare_sw.pack(anchor="w", pady=2)

        self._tunnel_sw = ctk.CTkSwitch(sw_f, text="🌑 터널/야간",
                                        variable=tunnel_var, command=on_tunnel_toggle,
                                        progress_color="#95a5a6",
                                        font=ctk.CTkFont(size=11))
        self._tunnel_sw.pack(anchor="w", pady=2)

        # 우측: 슬라이더 (CO2, 속도)
        sl_f = ctk.CTkFrame(env_f, fg_color="transparent")
        sl_f.grid(row=1, column=1, padx=(0, 15), pady=(0, 8), sticky="ew")

        co2_row = ctk.CTkFrame(sl_f, fg_color="transparent")
        co2_row.pack(fill="x", pady=2)
        ctk.CTkLabel(co2_row, text="CO₂", font=ctk.CTkFont(size=10), text_color=self._dim_color).pack(side="left")
        self._co2_lbl = ctk.CTkLabel(co2_row, text="800 ppm",
                                     font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
                                     text_color=self._main_color)
        self._co2_lbl.pack(side="right")
        self._co2_slider = ctk.CTkSlider(sl_f, from_=400, to=2500, number_of_steps=42,
                                         command=on_co2_change, height=14,
                                         button_color="#e67e22")
        self._co2_slider.set(800)
        self._co2_slider.pack(fill="x", pady=(0, 4))

        spd_row = ctk.CTkFrame(sl_f, fg_color="transparent")
        spd_row.pack(fill="x", pady=2)
        ctk.CTkLabel(spd_row, text="속도", font=ctk.CTkFont(size=10), text_color=self._dim_color).pack(side="left")
        self._spd_lbl = ctk.CTkLabel(spd_row, text="80 km/h",
                                     font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
                                     text_color=self._main_color)
        self._spd_lbl.pack(side="right")
        self._spd_slider = ctk.CTkSlider(sl_f, from_=0, to=200, number_of_steps=40,
                                         command=on_speed_change, height=14,
                                         button_color="#3498db")
        self._spd_slider.set(80)
        self._spd_slider.pack(fill="x")



        # 4. 배터리 및 최적화 상태 (BATTERY & OPTIMIZER STATUS)
        bat_f = ctk.CTkFrame(self, fg_color=self._screen_color, corner_radius=10)
        bat_f.grid(row=3, column=0, sticky="nsew", padx=10, pady=(4, 4))
        bat_f.grid_columnconfigure(0, weight=1)
        bat_f.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(bat_f, text="🔋 BATTERY & OPTIMIZER",
                     font=ctk.CTkFont(family="Consolas", size=10),
                     text_color=self._accent).grid(row=0, column=0, columnspan=2, padx=15, pady=(8, 4), sticky="w")
                     
        soc_frame = ctk.CTkFrame(bat_f, fg_color="transparent")
        soc_frame.grid(row=1, column=0, padx=15, sticky="w", pady=(0, 8))
        self._soc_bar = ctk.CTkProgressBar(soc_frame, width=150, height=12, progress_color="#2ecc71")
        self._soc_bar.set(1.0)
        self._soc_bar.pack(side="left", padx=(0, 10))
        self._soc_lbl = ctk.CTkLabel(soc_frame, text="100.0%", font=ctk.CTkFont(size=12, weight="bold"))
        self._soc_lbl.pack(side="left")

        self._power_lbl = ctk.CTkLabel(bat_f, text="Draw: 0.00 kW", font=ctk.CTkFont(size=11), text_color=self._dim_color)
        self._power_lbl.grid(row=2, column=0, padx=15, sticky="w", pady=(0, 8))

        self._charge_btn = ctk.CTkButton(bat_f, text="⚡ 급속 충전", width=80, height=24, font=ctk.CTkFont(size=11, weight="bold"),
                                         fg_color="#e67e22", hover_color="#d35400", command=on_charge_click)
        self._charge_btn.grid(row=1, column=1, padx=15, sticky="e")

        self._opt_lbl = ctk.CTkLabel(bat_f, text="Opt: Standby", font=ctk.CTkFont(family="Consolas", size=10), text_color="#f39c12")
        self._opt_lbl.grid(row=2, column=1, padx=15, sticky="e", pady=(0, 8))

        # 5. AI 시스템 로그 창
        log_f = ctk.CTkFrame(self, fg_color=self._screen_color, corner_radius=10)
        log_f.grid(row=4, column=0, sticky="nsew", padx=10, pady=(4, 10))
        log_f.grid_columnconfigure(0, weight=1)
        log_f.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(log_f, text="🤖 AI SYSTEM LOG",
                     font=ctk.CTkFont(family="Consolas", size=10),
                     text_color=self._accent).grid(row=0, column=0, padx=15, pady=(8, 2), sticky="w")

        self._log = ctk.CTkTextbox(log_f, activate_scrollbars=True, wrap="word",
                                   font=ctk.CTkFont(family="Consolas", size=11),
                                   text_color=self._main_color, fg_color="#08080f")
        self._log.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self._log.configure(state="disabled")

    def update_state_display(self, state_text, top_scores_text):
        self._state_main.configure(text=state_text)
        if top_scores_text:
            self._state_scores.configure(text=top_scores_text)

    def update_speed_label(self, speed):
        self._spd_lbl.configure(text=f"{int(speed)} km/h")

    def update_co2_label(self, co2):
        self._co2_lbl.configure(text=f"{int(co2)} ppm")

    def update_alert(self, message, bg_color):
        if message:
            self._alert_f.configure(fg_color=bg_color)
            self._alert_lbl.configure(text=message, text_color="white")
        else:
            self._alert_f.configure(fg_color="transparent")
            self._alert_lbl.configure(text="")

    def update_env_display(self, co2_level):
        """CO2 시뮬레이션 물리 변화를 슬라이더 및 라벨에 실시간으로 반영한다."""
        self._co2_slider.set(co2_level)
        self._co2_lbl.configure(text=f"{int(co2_level)} ppm")

    def write_log(self, text, color):
        ts = time.strftime("%H:%M:%S")
        tag = f"t_{ts}_{id(text)}"
        self._log.configure(state="normal")
        self._log.insert("end", f"[{ts}] ", "dim")
        self._log.insert("end", f"{text}\n", tag)
        self._log.tag_config("dim", foreground=self._dim_color)
        self._log.tag_config(tag, foreground=color)
        self._log.see("end")
        self._log.configure(state="disabled")

    def update_battery_status(self, soc, power_draw, solver_active, weights):
        self._soc_bar.set(soc / 100.0)
        self._soc_lbl.configure(text=f"{soc:.1f}%")
        
        soc_color = "#e74c3c" if soc < 20 else "#f39c12" if soc < 50 else "#2ecc71"
        self._soc_bar.configure(progress_color=soc_color)
        
        self._power_lbl.configure(text=f"Draw: {power_draw:.2f} kW")
        
        if solver_active:
            self._opt_lbl.configure(text=f"Opt Active (w1={weights[0]:.2f}, w2={weights[1]:.2f})")
        else:
            self._opt_lbl.configure(text="Opt: Standby")

    def reset_ui(self):
        self._state_main.configure(text="😐 정상")
        self._state_scores.configure(text="분석 대기 중...")
        self._alert_f.configure(fg_color="transparent")
        self._alert_lbl.configure(text="")
        self._co2_slider.set(800)
        self._co2_lbl.configure(text="800 ppm")
        self._spd_slider.set(80)
        self._spd_lbl.configure(text="80 km/h")
        
        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        self._log.configure(state="disabled")
