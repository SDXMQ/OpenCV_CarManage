"""
ac_panel.py - 하단 에어컨 제어판 및 다감각 차량 제어 상태 UI 컴포넌트
"""

import math
import customtkinter as ctk

class AcPanelFrame(ctk.CTkFrame):
    def __init__(self, master, power_var, ac_var, on_power_toggle, on_ac_toggle, on_temp_change, on_fan_change,
                 on_vent_click, on_win_click, on_air_click, on_audio_click, on_seat_click, on_haptic_click,
                 panel_color="#12121c", accent_color="#00d2ff", main_color="#ecf0f1"):
        super().__init__(master, height=140, corner_radius=14,
                         fg_color=panel_color, border_width=2, border_color="#22223b")
        self.pack_propagate(False)
        self.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self._accent = accent_color
        self._main = main_color

        # 애니메이션 상태 및 환경 임시값
        self._fan_angle = 0.0
        self._wind_offset = 0.0
        self._current_speed = 0.0
        
        self._power_on = False
        self._ac_on = False
        self._cabin_temp = 25.0
        self._ac_temp = 22
        self._ac_fan_speed = 1

        # 1. 좌: 실내 온도 & 설정 온도 텍스트 표시 구역
        temp_zone = ctk.CTkFrame(self, fg_color="#0d0d1a", corner_radius=10)
        temp_zone.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=8)
        
        temp_zone.grid_columnconfigure((0, 1), weight=1)
        temp_zone.grid_rowconfigure((0, 1), weight=1)

        self._cabin_title = ctk.CTkLabel(temp_zone, text="CABIN TEMP",
                                         font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
                                         text_color=self._accent)
        self._cabin_title.grid(row=0, column=0, pady=(12, 0), sticky="s")
        
        self._cabin_val = ctk.CTkLabel(temp_zone, text="25.0°C",
                                       font=ctk.CTkFont(size=28, weight="bold"), text_color=self._main)
        self._cabin_val.grid(row=1, column=0, pady=(0, 12), sticky="n")

        self._set_title = ctk.CTkLabel(temp_zone, text="TARGET TEMP",
                                       font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
                                       text_color="#5f6f81")
        self._set_title.grid(row=0, column=1, pady=(12, 0), sticky="s")

        self._set_val = ctk.CTkLabel(temp_zone, text="22°C",
                                     font=ctk.CTkFont(size=24, weight="bold"), text_color=self._main)
        self._set_val.grid(row=1, column=1, pady=(0, 12), sticky="n")

        # 2. 중앙: 전원 & AC 토글 및 온도 조절 슬라이더 구역
        ctrl_zone = ctk.CTkFrame(self, fg_color="#0d0d1a", corner_radius=10)
        ctrl_zone.grid(row=0, column=1, sticky="nsew", padx=4, pady=8)

        switch_frame = ctk.CTkFrame(ctrl_zone, fg_color="transparent")
        switch_frame.pack(pady=(12, 8))

        self._power_switch = ctk.CTkSwitch(switch_frame, text="POWER", variable=power_var,
                                           command=on_power_toggle,
                                           progress_color="#2ecc71",
                                           font=ctk.CTkFont(size=11, weight="bold"))
        self._power_switch.pack(side="left", padx=10)

        self._ac_switch = ctk.CTkSwitch(switch_frame, text="A/C", variable=ac_var,
                                        command=on_ac_toggle,
                                        progress_color="#00d2ff",
                                        font=ctk.CTkFont(size=11, weight="bold"))
        self._ac_switch.pack(side="left", padx=10)

        tf = ctk.CTkFrame(ctrl_zone, fg_color="transparent")
        tf.pack(fill="x", padx=20)
        ctk.CTkLabel(tf, text="16°C", font=ctk.CTkFont(size=10)).pack(side="left")
        ctk.CTkLabel(tf, text="30°C", font=ctk.CTkFont(size=10)).pack(side="right")

        self._temp_slider = ctk.CTkSlider(ctrl_zone, from_=16, to=30, number_of_steps=14,
                                          command=on_temp_change, width=220, height=16,
                                          button_color=self._accent)
        self._temp_slider.set(22)
        self._temp_slider.pack(pady=4)

        # 3. 풍량 제어 슬라이더 및 팬/바람 애니메이션 구역
        fan_zone = ctk.CTkFrame(self, fg_color="#0d0d1a", corner_radius=10)
        fan_zone.grid(row=0, column=2, sticky="nsew", padx=4, pady=8)

        ctk.CTkLabel(fan_zone, text="FAN SPEED",
                     font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
                     text_color=self._accent).pack(pady=(10, 0))

        self._canvas = ctk.CTkCanvas(fan_zone, width=80, height=56, bg="#0d0d1a", highlightthickness=0)
        self._canvas.pack(pady=(2, 0))

        self._fan_val = ctk.CTkLabel(fan_zone, text="1 단",
                                     font=ctk.CTkFont(size=20, weight="bold"), text_color=self._main)
        self._fan_val.pack(pady=(0, 2))

        self._fan_slider = ctk.CTkSlider(fan_zone, from_=0, to=5, number_of_steps=5,
                                         command=on_fan_change, width=180, height=16,
                                         button_color=self._accent)
        self._fan_slider.set(1)
        self._fan_slider.pack(pady=2)

        # 4. 우: 다감각 차량 제어 상태 (Vehicle Control Status)
        status_zone = ctk.CTkFrame(self, fg_color="#0d0d1a", corner_radius=10)
        status_zone.grid(row=0, column=3, sticky="nsew", padx=(4, 8), pady=8)

        ctk.CTkLabel(status_zone, text="VEHICLE STATUS",
                     font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
                     text_color=self._accent).pack(pady=(8, 4))

        # 상태 버튼 그리드
        badge_f = ctk.CTkFrame(status_zone, fg_color="transparent")
        badge_f.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        badge_f.grid_columnconfigure((0, 1), weight=1)

        # 환기 버튼
        self._vent_lbl = self._make_badge_button(badge_f, "♻ 내기순환", 0, 0, on_vent_click)
        # 창문 버튼
        self._win_lbl = self._make_badge_button(badge_f, "🪟 닫힘", 0, 1, on_win_click)
        # 풍향 버튼
        self._air_lbl = self._make_badge_button(badge_f, "🍃 간접풍", 1, 0, on_air_click)
        # 오디오 버튼
        self._audio_lbl = self._make_badge_button(badge_f, "🎵 None", 1, 1, on_audio_click)
        # 시트 버튼
        self._seat_lbl = self._make_badge_button(badge_f, "💺 OFF", 2, 0, on_seat_click)
        # 햅틱 버튼
        self._haptic_lbl = self._make_badge_button(badge_f, "📳 OFF", 2, 1, on_haptic_click)

        # 초기 애니메이션 상태 렌더링
        self.animate_step()

    def _make_badge_button(self, parent, text, row, col, command):
        btn = ctk.CTkButton(parent, text=text,
                            font=ctk.CTkFont(family="Malgun Gothic", size=10, weight="bold"),
                            text_color="#8899aa",
                            fg_color="#161625", hover_color="#222235",
                            corner_radius=6,
                            width=90, height=24,
                            command=command)
        btn.grid(row=row, column=col, padx=2, pady=2, sticky="ew")
        return btn

    def update_ac_state(self, cabin_temp, ac_temp, ac_fan_speed, power_on, ac_on):
        self._cabin_temp = cabin_temp
        self._ac_temp = ac_temp
        self._ac_fan_speed = ac_fan_speed
        self._power_on = power_on
        self._ac_on = ac_on

        self._cabin_val.configure(text=f"{cabin_temp:.1f}°C")
        self._set_val.configure(text=f"{ac_temp}°C")
        self._temp_slider.set(ac_temp)
        self._fan_val.configure(text=f"{ac_fan_speed} 단")
        self._fan_slider.set(ac_fan_speed)

        color = "#2ecc71"
        if cabin_temp >= 26.0:
            color = "#e74c3c"
        elif cabin_temp < 21.0:
            color = "#00d2ff"

        self._cabin_val.configure(text_color=color)
        self._cabin_title.configure(text_color=color)

    def update_vehicle_status(self, vent_mode, window, airflow, genre, volume,
                              seat_vent, seat_heat, haptic):
        """다감각 제어 상태 배지를 실시간으로 업데이트한다."""
        # 환기
        if vent_mode == "external":
            self._vent_lbl.configure(text="💨 외기유입", text_color="#00d2ff")
        else:
            self._vent_lbl.configure(text="♻ 내기순환", text_color="#8899aa")

        # 창문
        if window:
            self._win_lbl.configure(text="🪟 틸팅 열림", text_color="#f39c12")
        else:
            self._win_lbl.configure(text="🪟 닫힘", text_color="#8899aa")

        # 풍향
        if airflow == "direct":
            self._air_lbl.configure(text="🌀 직바람", text_color="#e74c3c")
        else:
            self._air_lbl.configure(text="🍃 간접풍", text_color="#8899aa")

        # 오디오
        if genre and genre != "None":
            self._audio_lbl.configure(text=f"🎵 {genre} {volume}%", text_color="#2ecc71")
        else:
            self._audio_lbl.configure(text="🎵 None", text_color="#8899aa")

        # 시트
        if seat_vent > 0:
            self._seat_lbl.configure(text=f"💺 통풍 {seat_vent}단", text_color="#00d2ff")
        elif seat_heat > 0:
            self._seat_lbl.configure(text=f"♨ 열선 {seat_heat}단", text_color="#e67e22")
        else:
            self._seat_lbl.configure(text="💺 OFF", text_color="#8899aa")

        # 햅틱
        if haptic:
            self._haptic_lbl.configure(text="📳 진동 ON", text_color="#e74c3c")
        else:
            self._haptic_lbl.configure(text="📳 OFF", text_color="#8899aa")

    def set_interactive_state(self, power_on, auto_mode):
        # 1. HVAC 슬라이더 및 스위치 인터랙션 상태 정의
        if auto_mode:
            self._power_switch.configure(state="disabled")
            self._ac_switch.configure(state="disabled")
            self._temp_slider.configure(state="disabled")
            self._fan_slider.configure(state="disabled")
            
            # 다감각 수동 제어 버튼도 자동 제어 시에는 전부 비활성화
            self._vent_lbl.configure(state="disabled")
            self._win_lbl.configure(state="disabled")
            self._air_lbl.configure(state="disabled")
            self._audio_lbl.configure(state="disabled")
            self._seat_lbl.configure(state="disabled")
            self._haptic_lbl.configure(state="disabled")
        else:
            self._power_switch.configure(state="normal")
            if not power_on:
                self._ac_switch.configure(state="disabled")
                self._temp_slider.configure(state="disabled")
                self._fan_slider.configure(state="disabled")
                
                # 전원 꺼졌을 때는 수동 버튼도 비활성화
                self._vent_lbl.configure(state="disabled")
                self._win_lbl.configure(state="disabled")
                self._air_lbl.configure(state="disabled")
                self._audio_lbl.configure(state="disabled")
                self._seat_lbl.configure(state="disabled")
                self._haptic_lbl.configure(state="disabled")
            else:
                self._ac_switch.configure(state="normal")
                self._temp_slider.configure(state="normal")
                self._fan_slider.configure(state="normal")
                
                # 전원 켜져 있고 수동 제어 모드일 때는 수동 버튼들 전부 활성화
                self._vent_lbl.configure(state="normal")
                self._win_lbl.configure(state="normal")
                self._air_lbl.configure(state="normal")
                self._audio_lbl.configure(state="normal")
                self._seat_lbl.configure(state="normal")
                self._haptic_lbl.configure(state="normal")

    def set_accent_border(self, is_active):
        if is_active:
            self.configure(border_color=self._accent)
        else:
            self.configure(border_color="#22223b")

    def animate_step(self):
        """에어컨 전원 및 풍속에 따른 실시간 프레임 렌더링."""
        power_on = getattr(self, "_power_on", False)
        ac_on = getattr(self, "_ac_on", False)
        cabin_temp = getattr(self, "_cabin_temp", 25.0)
        ac_temp = getattr(self, "_ac_temp", 22)
        fan_speed = getattr(self, "_ac_fan_speed", 1)

        target_speed = fan_speed * 12.0 if (power_on and fan_speed > 0) else 0.0
        self._current_speed += (target_speed - self._current_speed) * 0.15

        self._fan_angle = (self._fan_angle + self._current_speed) % 360
        self._wind_offset = (self._wind_offset + self._current_speed * 0.12) % 100

        self._canvas.delete("all")

        cx, cy = 40, 28
        r = 15

        if power_on and fan_speed > 0:
            if not ac_on and ac_temp > cabin_temp:
                wind_color = "#e67e22"
            elif ac_on and ac_temp < cabin_temp:
                wind_color = "#00d2ff"
            else:
                wind_color = "#aaaaaa"
        else:
            wind_color = self._accent

        if self._current_speed > 0.1:
            for base_y in [cy - 12, cy + 12]:
                points = []
                amplitude = min(self._current_speed * 0.12, 5.0)
                frequency = 0.18
                
                for x in range(5, 76, 3):
                    y = base_y + amplitude * math.sin(x * frequency - self._wind_offset)
                    points.append((x, y))
                
                width = int(min(self._current_speed * 0.05 + 1.0, 2.5))
                self._canvas.create_line(points, fill=wind_color, width=width, smooth=True)

        fan_color = wind_color if (power_on and fan_speed > 0) else self._accent
        for offset in [0, 120, 240]:
            start_ang = (self._fan_angle + offset) % 360
            self._canvas.create_arc(
                cx - r, cy - r, cx + r, cy + r,
                start=start_ang, extent=45,
                fill=fan_color, outline=""
            )

        self._canvas.create_oval(cx - 4, cy - 4, cx + 4, cy + 4, fill=self._main, outline="")

    def reset_ui(self):
        self.update_ac_state(25.0, 22, 1, False, False)
        self.update_vehicle_status("internal", False, "indirect", "None", 30, 0, 0, False)
        self.set_interactive_state(False, False)
        self.set_accent_border(False)
        self._current_speed = 0.0
        self.animate_step()
