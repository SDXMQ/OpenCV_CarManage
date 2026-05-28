"""
fleet_monitor.py - MQTT 기반 가상 차량 관제 모니터 (디지털 트윈)
"""

import json
import customtkinter as ctk
import paho.mqtt.client as mqtt

class FleetMonitor(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SEAVS Fleet Monitor")
        self.geometry("600x450")
        ctk.set_appearance_mode("dark")
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # 헤더
        header = ctk.CTkFrame(self, corner_radius=0, fg_color="#1a1a2e")
        header.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(header, text="🌐 SEAVS FLEET CONTROL CENTER", font=ctk.CTkFont(size=16, weight="bold"), text_color="#00d2ff").pack(pady=10)
        
        # 정보 패널
        self.info_frame = ctk.CTkFrame(self, fg_color="#16213e", corner_radius=10)
        self.info_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        self.info_frame.grid_columnconfigure(1, weight=1)
        
        self.labels = {}
        fields = [
            ("Vehicle ID", "대기 중..."),
            ("Driver State", "대기 중..."),
            ("Battery SOC", "0%"),
            ("Power Draw", "0 kW"),
            ("Cabin Temp", "0 °C"),
            ("Target Temp", "0 °C"),
            ("EAR / MAR", "0 / 0"),
            ("Speed / CO2", "0 km/h / 0 ppm")
        ]
        
        for i, (label_text, default_val) in enumerate(fields):
            ctk.CTkLabel(self.info_frame, text=label_text + ":", font=ctk.CTkFont(weight="bold"), text_color="#a8b2d1").grid(row=i, column=0, padx=20, pady=10, sticky="e")
            val_label = ctk.CTkLabel(self.info_frame, text=default_val, font=ctk.CTkFont(family="Consolas", size=14), text_color="#ffffff")
            val_label.grid(row=i, column=1, padx=20, pady=10, sticky="w")
            self.labels[label_text] = val_label
            
        # MQTT 설정
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
        try:
            self.client.connect("broker.hivemq.com", 1883, 60)
            self.client.loop_start()
        except Exception as e:
            self.labels["Vehicle ID"].configure(text=f"MQTT Connection Failed: {e}", text_color="#e74c3c")
            
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            client.subscribe("seavs/fleet/+/telemetry")
            self.labels["Vehicle ID"].configure(text="Connected to Broker. Waiting for data...", text_color="#2ecc71")
            
    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            self.after(0, self.update_ui, payload)
        except Exception:
            pass
            
    def update_ui(self, data):
        self.labels["Vehicle ID"].configure(text=data.get("vehicle_id", "Unknown"), text_color="#00d2ff")
        state = data.get("driver_state", "unknown")
        state_color = "#e74c3c" if state in ["danger", "warning"] else "#2ecc71"
        self.labels["Driver State"].configure(text=state.upper(), text_color=state_color)
        
        soc = data.get("battery_soc", 0)
        soc_color = "#e74c3c" if soc < 20 else "#f39c12" if soc < 50 else "#2ecc71"
        self.labels["Battery SOC"].configure(text=f"{soc}%", text_color=soc_color)
        
        self.labels["Power Draw"].configure(text=f"{data.get('power_consumption', 0):.3f} kW")
        self.labels["Cabin Temp"].configure(text=f"{data.get('cabin_temp', 0):.2f} °C")
        self.labels["Target Temp"].configure(text=f"{data.get('target_temp', 0)} °C")
        self.labels["EAR / MAR"].configure(text=f"{data.get('ear_value', 0):.2f} / {data.get('mar_value', 0):.2f}")
        self.labels["Speed / CO2"].configure(text=f"{data.get('speed', 0)} km/h / {data.get('co2_level', 0)} ppm")

    def on_closing(self):
        self.client.loop_stop()
        self.client.disconnect()
        self.destroy()

if __name__ == "__main__":
    app = FleetMonitor()
    app.mainloop()
