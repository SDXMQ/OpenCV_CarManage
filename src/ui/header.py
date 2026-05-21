"""
header.py - 상단 헤더 UI 컴포넌트
"""

import customtkinter as ctk

class HeaderFrame(ctk.CTkFrame):
    def __init__(self, master, auto_mode_var, audio_enabled_var, on_auto_toggle, on_audio_toggle, accent_color="#00d2ff"):
        super().__init__(master, height=46, corner_radius=0, fg_color="#080812")
        self.pack_propagate(False)
        self._accent = accent_color

        # 타이틀
        ctk.CTkLabel(self, text="◈ SEAVS",
                     font=ctk.CTkFont(family="Consolas", size=18, weight="bold"),
                     text_color=self._accent).pack(side="left", padx=15)

        # 우측 컨트롤 그룹
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.pack(side="right", padx=15)

        # AI 작동 상태 배지
        self._auto_badge = ctk.CTkLabel(right, text="● MANUAL",
                                        font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
                                        text_color="#888")
        self._auto_badge.pack(side="left", padx=(0, 10))

        # AI 모드 토글 스위치
        self._auto_switch = ctk.CTkSwitch(right, text="AI 모드", variable=auto_mode_var,
                                          command=on_auto_toggle, width=50,
                                          progress_color=self._accent, button_color="#fff",
                                          font=ctk.CTkFont(size=12, weight="bold"))
        self._auto_switch.pack(side="left", padx=(0, 15))

        # 오디오 스위치
        self._audio_switch = ctk.CTkSwitch(right, text="🔊", variable=audio_enabled_var,
                                           command=on_audio_toggle, width=40,
                                           font=ctk.CTkFont(size=12))
        self._audio_switch.pack(side="left")

    def update_badge(self, is_auto):
        if is_auto:
            self._auto_badge.configure(text="● AI ACTIVE", text_color=self._accent)
        else:
            self._auto_badge.configure(text="● MANUAL", text_color="#888")
