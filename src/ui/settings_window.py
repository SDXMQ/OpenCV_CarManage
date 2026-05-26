import json
import os
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from core.i18n import t, set_language, get_available_languages, get_language

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, master, config_manager, camera, safety_manager, on_settings_saved_callback):
        super().__init__(master)
        
        self.config = config_manager
        self.camera = camera
        self.safety = safety_manager
        self.on_saved_callback = on_settings_saved_callback
        
        # 최상단으로 설정
        self.title(t("settings_title"))
        self.geometry("500x550")
        self.minsize(500, 550)
        self.grab_set()  # 모달
        
        self.profiles_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "core", "profiles.json")
        self.profiles = self._load_profiles()
        
        # 내부 변수
        self.current_lang_var = ctk.StringVar(value=self.config.get("language", "ko"))
        self.mirror_var = ctk.BooleanVar(value=self.config.get("mirror_camera", False))
        self.selected_profile_var = ctk.StringVar(value=self.config.get("current_profile", "default"))
        
        self._build_ui()
        
    def _load_profiles(self):
        try:
            with open(self.profiles_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"default": {"name": "Default Profile", "base_ear": 0.28, "base_mar": 0.12, "base_emotions": {}, "face_embedding": None}}

    def _save_profiles(self):
        with open(self.profiles_path, "w", encoding="utf-8") as f:
            json.dump(self.profiles, f, ensure_ascii=False, indent=4)

    def _build_ui(self):
        # 1. 프로필 관리 구역
        prof_frame = ctk.CTkFrame(self)
        prof_frame.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(prof_frame, text=t("lbl_profile"), font=("Arial", 16, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        # 프로필 선택
        sel_frame = ctk.CTkFrame(prof_frame, fg_color="transparent")
        sel_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(sel_frame, text=t("lbl_select_profile")).pack(side="left", padx=(0, 10))
        
        profile_names = list(self.profiles.keys())
        self.profile_combo = ctk.CTkComboBox(sel_frame, values=profile_names, variable=self.selected_profile_var)
        self.profile_combo.pack(side="left", fill="x", expand=True)

        # 새 프로필 추가 & 캘리브레이션
        calib_frame = ctk.CTkFrame(prof_frame, fg_color="transparent")
        calib_frame.pack(fill="x", padx=10, pady=10)
        
        self.new_profile_entry = ctk.CTkEntry(calib_frame, placeholder_text="New Profile Name")
        self.new_profile_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.calib_btn = ctk.CTkButton(calib_frame, text=t("btn_calibrate"), command=self._start_calibration)
        self.calib_btn.pack(side="left")
        
        self.calib_status_label = ctk.CTkLabel(prof_frame, text="", text_color="orange")
        self.calib_status_label.pack(pady=(0, 10))

        # 2. 다국어 설정 구역
        lang_frame = ctk.CTkFrame(self)
        lang_frame.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(lang_frame, text=t("lbl_lang"), font=("Arial", 16, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        langs = get_available_languages()
        # 라디오 버튼으로 표시
        for lang in langs:
            rb = ctk.CTkRadioButton(lang_frame, text=lang.upper(), variable=self.current_lang_var, value=lang, command=self._on_lang_change)
            rb.pack(anchor="w", padx=20, pady=5)

        # 3. 카메라 설정 구역
        cam_frame = ctk.CTkFrame(self)
        cam_frame.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(cam_frame, text=t("lbl_camera_settings"), font=("Arial", 16, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
        ctk.CTkSwitch(cam_frame, text=t("chk_mirror"), variable=self.mirror_var).pack(anchor="w", padx=20, pady=10)

        # 4. 저장 및 닫기 버튼
        save_btn = ctk.CTkButton(self, text=t("btn_save_close"), height=40, command=self._save_and_close)
        save_btn.pack(side="bottom", fill="x", padx=15, pady=15)

    def _on_lang_change(self):
        new_lang = self.current_lang_var.get()
        set_language(new_lang)
        # UI 업데이트 (자신의 창 텍스트만 일단 갱신. 완전한 갱신은 창을 다시 열거나 콜백으로 해결)
        self.title(t("settings_title"))
        self.calib_btn.configure(text=t("btn_calibrate"))

    def _start_calibration(self):
        new_name = self.new_profile_entry.get().strip()
        prof_key = self.selected_profile_var.get()
        
        if new_name:
            prof_key = new_name
            
        self.calib_btn.configure(state="disabled")
        self.calib_status_label.configure(text=t("msg_calibrating"), text_color="orange")
        
        # 3초 수집 (30프레임) 시작
        self.camera.start_calibration(frames=30, on_done=lambda data: self._on_calibration_done(prof_key, data))

    def _on_calibration_done(self, prof_key, data):
        # data = list of dicts {"ear": float, "mar": float, "emotion": dict, "face_embedding": list}
        if not data:
            self._update_calib_ui("Failed to collect data", "red")
            return
            
        avg_ear = sum(d["ear"] for d in data) / len(data)
        avg_mar = sum(d["mar"] for d in data) / len(data)
        
        base_emotions = {}
        for d in data:
            for emo, score in d["emotion"].items():
                base_emotions[emo] = base_emotions.get(emo, 0.0) + score
                
        for emo in base_emotions:
            base_emotions[emo] /= len(data)
            
        # 얼굴 임베딩 평균 연산
        import numpy as np
        valid_embeddings = [d["face_embedding"] for d in data if d.get("face_embedding") is not None]
        if valid_embeddings:
            avg_embedding = np.mean(valid_embeddings, axis=0).tolist()
        else:
            avg_embedding = None

        # 프로필 저장
        self.profiles[prof_key] = {
            "name": prof_key,
            "base_ear": avg_ear,
            "base_mar": avg_mar,
            "base_emotions": base_emotions,
            "face_embedding": avg_embedding
        }
        self._save_profiles()
        
        # 콤보박스 갱신
        self.profile_combo.configure(values=list(self.profiles.keys()))
        self.selected_profile_var.set(prof_key)
        self.new_profile_entry.delete(0, 'end')
        
        self._update_calib_ui(t("msg_calib_done"), "green")

    def _update_calib_ui(self, msg, color):
        # 쓰레드 안전성을 위해
        self.after(0, lambda: self.calib_status_label.configure(text=msg, text_color=color))
        self.after(0, lambda: self.calib_btn.configure(state="normal"))

    def _save_and_close(self):
        # 언어 
        self.config.set_and_save("language", self.current_lang_var.get())
        set_language(self.current_lang_var.get())
        
        # 좌우반전
        self.config.set_and_save("mirror_camera", self.mirror_var.get())
        self.camera.mirror_camera = self.mirror_var.get()
        
        # 프로필 반영
        sel_prof = self.selected_profile_var.get()
        self.config.set_and_save("current_profile", sel_prof)
        prof_data = self.profiles.get(sel_prof)
        if prof_data:
            self.camera.set_active_profile(prof_data)
            self.safety.active_profile_data = prof_data

        if self.on_saved_callback:
            self.on_saved_callback()
            
        self.destroy()
