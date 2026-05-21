"""
simulator.py - 가상 차량 센서 데이터 시뮬레이터
"""
import threading
import time
import random


class VehicleSimulator:
    def __init__(self, update_interval=0.5):
        self._update_interval = update_interval
        self._running = False
        self._paused = False
        self._lock = threading.Lock()
        self._thread = None

        self._speed = 0.0       
        self._rpm = 800.0       
        self._brake = 0.0       
        self._rapid_accel = False
        self._target_speed = 0.0

    @property
    def speed(self):
        with self._lock: return self._speed

    @property
    def rpm(self):
        with self._lock: return self._rpm

    @property
    def brake(self):
        with self._lock: return self._brake

    @property
    def rapid_accel(self):
        with self._lock: return self._rapid_accel

    def get_all(self):
        with self._lock:
            return {
                "speed": round(self._speed, 1),
                "rpm": round(self._rpm),
                "brake": round(self._brake, 1),
                "rapid_accel": self._rapid_accel,
            }

    def start(self):
        if self._running: return
        self._running = True
        self._paused = False
        self._thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self._thread.start()

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def stop(self):
        self._running = False
        self._paused = False
        if self._thread:
            self._thread.join(timeout=2)
        with self._lock:
            self._speed, self._rpm, self._brake, self._rapid_accel, self._target_speed = 0.0, 800.0, 0.0, False, 0.0

    def _simulation_loop(self):
        while self._running:
            if self._paused:
                time.sleep(0.05)
                continue

            with self._lock:
                if random.random() < 0.1:
                    self._target_speed = random.uniform(0, 120)

                diff = self._target_speed - self._speed
                accel_step = diff * 0.15
                prev_speed = self._speed
                
                self._speed = max(0.0, min(180.0, self._speed + accel_step + random.uniform(-1, 1)))
                self._rapid_accel = (self._speed - prev_speed) > 10.0
                
                self._rpm = max(800, min(8000, 800 + self._speed * 30 + random.uniform(-100, 100)))

                if diff < -5:
                    self._brake = min(100, abs(diff) * 2 + random.uniform(0, 10))
                else:
                    self._brake = max(0, self._brake - 5)

            time.sleep(self._update_interval)
