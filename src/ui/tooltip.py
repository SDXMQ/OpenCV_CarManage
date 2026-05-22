"""
tooltip.py - Tkinter/customtkinter용 툴팁 헬퍼
"""
import customtkinter as ctk

class ToolTip:
    """마우스 포인터를 위젯 위에 올렸을 때 말풍선 설명을 띄워주는 클래스"""
    def __init__(self, widget, text):
        self._widget = widget
        self._text = text
        self._tw = None
        
        # 엔터/리브 이벤트 바인딩
        self._widget.bind("<Enter>", self._show)
        self._widget.bind("<Leave>", self._hide)

    def _show(self, event=None):
        # 이미 툴팁이 활성화되어 있거나 위젯이 비활성화 상태이면 띄우지 않음 (선택사항)
        # 단, 비활성화된 위젯도 마우스 호버 설명을 표시해주기 위해 위젯 상태 검사는 생략함
        if self._tw:
            return
            
        x = self._widget.winfo_rootx() + 15
        y = self._widget.winfo_rooty() + self._widget.winfo_height() + 5
        
        # 툴팁을 최상위 윈도우로 생성
        self._tw = ctk.CTkToplevel(self._widget)
        self._tw.wm_overrideredirect(True)  # 테두리 및 타이틀바 제거
        self._tw.wm_geometry(f"+{x}+{y}")
        self._tw.attributes("-topmost", True)
        
        label = ctk.CTkLabel(
            self._tw,
            text=self._text,
            fg_color="#1e1e2e",
            text_color="#ffffff",
            corner_radius=6,
            font=ctk.CTkFont(family="Malgun Gothic", size=10),
            padx=8,
            pady=4
        )
        label.pack()

    def _hide(self, event=None):
        if self._tw:
            self._tw.destroy()
            self._tw = None
