"""
center_display.py - 센터 디스플레이 정보 및 로그 UI 컴포넌트
"""

import time
import customtkinter as ctk

class CenterDisplayFrame(ctk.CTkFrame):
    def __init__(self, master, panel_color="#12121c", screen_color="#0b0c10", accent_color="#00d2ff",
                 dim_color="#5f6f81", main_color="#ecf0f1"):
        super().__init__(master, corner_radius=14, fg_color=panel_color, border_width=1, border_color="#22223b")
        
        self._screen_color = screen_color
        self._accent = accent_color
        self._dim_color = dim_color
        self._main_color = main_color

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=2)

        # 1. 타이틀
        tf = ctk.CTkFrame(self, fg_color="#0d0d18", height=34, corner_radius=0)
        tf.grid(row=0, column=0, sticky="ew")
        tf.grid_propagate(False)
        ctk.CTkLabel(tf, text="🖥 CENTER DISPLAY",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=self._dim_color).pack(side="left", padx=12, pady=5)

        # 2. 운전자 상태 상세 카드 (감정 점수 및 경고 배너)
        status = ctk.CTkFrame(self, fg_color=self._screen_color, corner_radius=10)
        status.grid(row=1, column=0, sticky="nsew", padx=10, pady=(8, 4))
        status.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(status, text="DRIVER STATUS",
                     font=ctk.CTkFont(family="Consolas", size=10),
                     text_color=self._accent).grid(row=0, column=0, padx=15, pady=(10, 2), sticky="w")

        self._emo_main = ctk.CTkLabel(status, text="😐 Neutral",
                                      font=ctk.CTkFont(size=28, weight="bold"), text_color=self._main_color)
        self._emo_main.grid(row=1, column=0, padx=15, sticky="w")

        self._emo_scores = ctk.CTkLabel(status, text="분석 대기 중...",
                                        font=ctk.CTkFont(family="Consolas", size=11), text_color=self._dim_color)
        self._emo_scores.grid(row=2, column=0, padx=15, sticky="w", pady=(0, 4))

        # 경고 알림판
        self._alert_f = ctk.CTkFrame(status, corner_radius=8, fg_color="transparent", height=44)
        self._alert_f.grid(row=3, column=0, padx=15, pady=(4, 10), sticky="ew")
        self._alert_lbl = ctk.CTkLabel(self._alert_f, text="",
                                       font=ctk.CTkFont(size=14, weight="bold"))
        self._alert_lbl.pack(pady=6, padx=10)

        # 3. AI 시스템 로그 창
        log_f = ctk.CTkFrame(self, fg_color=self._screen_color, corner_radius=10)
        log_f.grid(row=2, column=0, sticky="nsew", padx=10, pady=(4, 10))
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

    def update_emotion(self, emotion_text, top_scores_text):
        self._emo_main.configure(text=emotion_text)
        if top_scores_text:
            self._emo_scores.configure(text=top_scores_text)

    def update_alert(self, message, bg_color):
        if message:
            self._alert_f.configure(fg_color=bg_color)
            self._alert_lbl.configure(text=message, text_color="white")
        else:
            self._alert_f.configure(fg_color="transparent")
            self._alert_lbl.configure(text="")

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

    def reset_ui(self):
        self._emo_main.configure(text="😐 Neutral")
        self._emo_scores.configure(text="분석 대기 중...")
        self._alert_f.configure(fg_color="transparent")
        self._alert_lbl.configure(text="")
        
        # 로그 초기화 (필요시 비움, 또는 정지 메시지만 추가)
        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        self._log.configure(state="disabled")
