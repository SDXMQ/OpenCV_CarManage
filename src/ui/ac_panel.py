"""
ac_panel.py - 하단 에어컨 제어판 UI 컴포넌트 (실시간 팬 & 바람 애니메이션 포함)
"""

import math
import customtkinter as ctk

class AcPanelFrame(ctk.CTkFrame):
    def __init__(self, master, power_var, ac_var, on_power_toggle, on_ac_toggle, on_temp_change, on_fan_change,
                 panel_color="#12121c", accent_color="#00d2ff", main_color="#ecf0f1"):
        super().__init__(master, height=140, corner_radius=14,
                         fg_color=panel_color, border_width=2, border_color="#22223b")
        self.pack_propagate(False)
        self.grid_columnconfigure((0, 1, 2), weight=1)

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

        # 전원/AC 스위치 가로 배치 프레임
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

        # 3. 우: 풍량 제어 슬라이더 및 팬/바람 애니메이션 구역
        fan_zone = ctk.CTkFrame(self, fg_color="#0d0d1a", corner_radius=10)
        fan_zone.grid(row=0, column=2, sticky="nsew", padx=(4, 8), pady=8)

        ctk.CTkLabel(fan_zone, text="FAN SPEED",
                     font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
                     text_color=self._accent).pack(pady=(10, 0))

        # 실시간 그래픽 캔버스 생성
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

        # 초기 애니메이션 상태 렌더링
        self.animate_step()


    def update_ac_state(self, cabin_temp, ac_temp, ac_fan_speed, power_on, ac_on):
        self._cabin_temp = cabin_temp
        self._ac_temp = ac_temp
        self._ac_fan_speed = ac_fan_speed
        self._power_on = power_on
        self._ac_on = ac_on

        # UI 라벨 갱신
        self._cabin_val.configure(text=f"{cabin_temp:.1f}°C")
        self._set_val.configure(text=f"{ac_temp}°C")
        self._temp_slider.set(ac_temp)
        self._fan_val.configure(text=f"{ac_fan_speed} 단")
        self._fan_slider.set(ac_fan_speed)

        # 실내 온도에 따른 동적 컬러 설정
        # Cool (<21°C): #00d2ff, Comfort (21°C ~ 25.9°C): #2ecc71, Hot (>=26°C): #e74c3c
        color = "#2ecc71"
        if cabin_temp >= 26.0:
            color = "#e74c3c"
        elif cabin_temp < 21.0:
            color = "#00d2ff"

        self._cabin_val.configure(text_color=color)
        self._cabin_title.configure(text_color=color)

    def set_interactive_state(self, power_on, auto_mode):
        self._power_switch.configure(state="normal")
        
        if not power_on:
            self._ac_switch.configure(state="disabled")
            self._temp_slider.configure(state="disabled")
            self._fan_slider.configure(state="disabled")
        else:
            if auto_mode:
                self._ac_switch.configure(state="disabled")
                self._temp_slider.configure(state="disabled")
                self._fan_slider.configure(state="disabled")
            else:
                self._ac_switch.configure(state="normal")
                self._temp_slider.configure(state="normal")
                self._fan_slider.configure(state="normal")

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

        # 1. 목표 속도 계산
        target_speed = fan_speed * 12.0 if (power_on and fan_speed > 0) else 0.0
        self._current_speed += (target_speed - self._current_speed) * 0.15

        # 각도 및 바람 물결 오프셋 업데이트
        self._fan_angle = (self._fan_angle + self._current_speed) % 360
        self._wind_offset = (self._wind_offset + self._current_speed * 0.12) % 100

        # 2. 캔버스 초기화
        self._canvas.delete("all")

        cx, cy = 40, 28 # 캔버스 중앙점
        r = 15          # 팬 반지름

        # 3. 공조 모드에 따른 바람/팬 색상 동적 결정
        if power_on and fan_speed > 0:
            if not ac_on and ac_temp > cabin_temp:
                wind_color = "#e67e22"  # 히터 (온풍): 주황색 (A/C 꺼져있을 때)
            elif ac_on and ac_temp < cabin_temp:
                wind_color = "#00d2ff"  # 냉방 (에어컨): 하늘색
            else:
                wind_color = "#aaaaaa"  # 송풍 (바람만): 회색
        else:
            wind_color = self._accent

        # 4. 바람 물결선 그리기
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

        # 5. 팬 날개 3개 그리기
        fan_color = wind_color if (power_on and fan_speed > 0) else self._accent
        for offset in [0, 120, 240]:
            start_ang = (self._fan_angle + offset) % 360
            self._canvas.create_arc(
                cx - r, cy - r, cx + r, cy + r,
                start=start_ang, extent=45,
                fill=fan_color, outline=""
            )

        # 6. 중앙 코어 그리기
        self._canvas.create_oval(cx - 4, cy - 4, cx + 4, cy + 4, fill=self._main, outline="")

    def reset_ui(self):
        self.update_ac_state(25.0, 22, 1, False, False)
        self.set_interactive_state(False, False)
        self.set_accent_border(False)
        self._current_speed = 0.0
        self.animate_step()

