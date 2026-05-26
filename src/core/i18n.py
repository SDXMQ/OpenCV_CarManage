"""
i18n.py - 현지화(다국어 지원) 모듈
새로운 언어 추가 시 TRANSLATIONS 딕셔너리에 언어 코드를 추가하기만 하면 됩니다.
"""

TRANSLATIONS = {
    "ko": {
        "title": "SEAVS - 스마트 감정 인식 차량 시스템",
        "btn_auto_on": "🤖 AI 자동제어 모드 켜짐",
        "btn_auto_off": "🤖 AI 자동제어 모드 꺼짐",
        "btn_audio_on": "🔊 음성 알림 켜짐",
        "btn_audio_off": "🔇 음성 알림 꺼짐",
        "btn_settings": "⚙ 설정",
        "lbl_camera": "카메라 입력",
        "btn_start": "▶ 시작",
        "btn_pause": "⏸ 일시정지",
        "btn_stop": "⏹ 정지",
        "lbl_status_analysis": "운전자 상태 분석",
        "lbl_ear": "양안 EAR (눈 감김):",
        "lbl_mar": "구강 MAR (하품):",
        "lbl_emotion": "지배적 감정:",
        "lbl_state": "현재 상태:",
        "lbl_ai_log": "AI 다감각 제어 로그",
        "lbl_env_sim": "환경 시뮬레이터",
        "lbl_glare": "☀ 직사광선 눈부심",
        "lbl_tunnel": "🌑 터널 진입 (어두움)",
        "lbl_co2": "💨 실내 CO2 농도 (ppm)",
        "lbl_speed": "🚗 차량 속도 (km/h)",
        "lbl_ac_panel": "다감각 제어 패널 (공조 / 조명 / 시트 / 오디오)",
        "btn_power": "전원",
        "btn_ac": "A/C",
        "lbl_temp": "설정 온도",
        "lbl_fan": "풍량",
        "btn_vent_internal": "내기순환",
        "btn_vent_external": "외기유입",
        "btn_window_close": "창문 닫힘",
        "btn_window_tilt": "창문 틸트",
        "btn_air_direct": "직접바람",
        "btn_air_indirect": "간접바람",
        "btn_audio_none": "오디오 끄기",
        "btn_audio_pop": "Pop 음악",
        "btn_audio_dance": "Dance 음악",
        "btn_audio_classic": "Classic 음악",
        "btn_seat_none": "시트 끄기",
        "btn_seat_heat": "열선 시트",
        "btn_seat_vent": "통풍 시트",
        "btn_haptic": "햅틱 진동",
        
        # State Labels
        "state_danger": "🚨 졸음 위험",
        "state_warning": "🥱 하품 감지",
        "state_glare": "☀ 눈부심 피로",
        "state_stress": "😤 스트레스/피로",
        "state_low_eng": "😶 집중력 저하",
        "state_normal": "😐 정상",
        
        # State Messages
        "msg_danger": "⚠ 졸음 감지! 즉시 주의하십시오!",
        "msg_warning": "🥱 하품 감지 → 졸음 전조 증상",
        "msg_glare": "☀ 눈부심이 감지되었습니다. 선바이저를 내릴까요?",
        "msg_stress": "😤 스트레스/피로도 누적 감지",
        "msg_low_eng": "😶 집중력 저하 상태 감지",
        "msg_normal": "",

        # Settings Window
        "settings_title": "⚙ SEAVS 설정",
        "lbl_profile": "👤 운전자 프로필 설정",
        "lbl_select_profile": "프로필 선택:",
        "btn_add_profile": "새 프로필 추가",
        "btn_calibrate": "🎯 캘리브레이션 시작 (3초간 무표정 유지)",
        "lbl_lang": "🌐 언어 (Language)",
        "lbl_camera_settings": "📷 카메라 설정",
        "chk_mirror": "카메라 좌우 반전",
        "btn_save_close": "저장 및 닫기",
        "msg_calibrating": "캘리브레이션 중... (정면을 보고 무표정을 유지하세요)",
        "msg_calib_done": "캘리브레이션 완료!"
    },
    "en": {
        "title": "SEAVS - Smart Emotion-Aware Vehicle System",
        "btn_auto_on": "🤖 AI Auto Mode ON",
        "btn_auto_off": "🤖 AI Auto Mode OFF",
        "btn_audio_on": "🔊 Audio Alert ON",
        "btn_audio_off": "🔇 Audio Alert OFF",
        "btn_settings": "⚙ Settings",
        "lbl_camera": "Camera Input",
        "btn_start": "▶ Start",
        "btn_pause": "⏸ Pause",
        "btn_stop": "⏹ Stop",
        "lbl_status_analysis": "Driver Status Analysis",
        "lbl_ear": "Eyes EAR:",
        "lbl_mar": "Mouth MAR:",
        "lbl_emotion": "Dominant Emotion:",
        "lbl_state": "Current State:",
        "lbl_ai_log": "AI Multi-Sensory Control Log",
        "lbl_env_sim": "Environment Simulator",
        "lbl_glare": "☀ Sunlight Glare",
        "lbl_tunnel": "🌑 Tunnel Entry",
        "lbl_co2": "💨 Cabin CO2 (ppm)",
        "lbl_speed": "🚗 Vehicle Speed (km/h)",
        "lbl_ac_panel": "Multi-Sensory Panel (HVAC / Light / Seat / Audio)",
        "btn_power": "Power",
        "btn_ac": "A/C",
        "lbl_temp": "Set Temp",
        "lbl_fan": "Fan Speed",
        "btn_vent_internal": "Internal",
        "btn_vent_external": "External",
        "btn_window_close": "Win Close",
        "btn_window_tilt": "Win Tilt",
        "btn_air_direct": "Direct Air",
        "btn_air_indirect": "Indirect Air",
        "btn_audio_none": "Audio OFF",
        "btn_audio_pop": "Pop Music",
        "btn_audio_dance": "Dance Music",
        "btn_audio_classic": "Classic Music",
        "btn_seat_none": "Seat OFF",
        "btn_seat_heat": "Seat Heat",
        "btn_seat_vent": "Seat Vent",
        "btn_haptic": "Haptic Vib",
        
        # State Labels
        "state_danger": "🚨 Drowsiness Danger",
        "state_warning": "🥱 Yawning Detected",
        "state_glare": "☀ Glare Fatigue",
        "state_stress": "😤 Stress/Fatigue",
        "state_low_eng": "😶 Low Engagement",
        "state_normal": "😐 Normal",
        
        # State Messages
        "msg_danger": "⚠ Drowsiness detected! Pay attention immediately!",
        "msg_warning": "🥱 Yawn detected → Sign of drowsiness",
        "msg_glare": "☀ Sun glare detected. Lower the sun visor?",
        "msg_stress": "😤 Accumulated stress/fatigue detected",
        "msg_low_eng": "😶 Low engagement state detected",
        "msg_normal": "",

        # Settings Window
        "settings_title": "⚙ SEAVS Settings",
        "lbl_profile": "👤 Driver Profile",
        "lbl_select_profile": "Select Profile:",
        "btn_add_profile": "Add New Profile",
        "btn_calibrate": "🎯 Start Calibration (Hold neutral face for 3s)",
        "lbl_lang": "🌐 Language",
        "lbl_camera_settings": "📷 Camera Settings",
        "chk_mirror": "Mirror Camera",
        "btn_save_close": "Save & Close",
        "msg_calibrating": "Calibrating... (Look straight and stay neutral)",
        "msg_calib_done": "Calibration Done!"
    }
}

# 기본 언어 설정
_current_lang = "ko"

def set_language(lang_code):
    global _current_lang
    if lang_code in TRANSLATIONS:
        _current_lang = lang_code

def get_language():
    return _current_lang

def get_available_languages():
    return list(TRANSLATIONS.keys())

def t(key, **kwargs):
    """지정된 키에 해당하는 번역 텍스트를 반환한다. 포매팅도 지원한다."""
    text = TRANSLATIONS.get(_current_lang, TRANSLATIONS["ko"]).get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except KeyError:
            return text
    return text
