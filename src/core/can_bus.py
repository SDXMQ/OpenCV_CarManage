"""
can_bus.py - 가상 CAN 통신 인터페이스
python-can 라이브러리를 이용하여 시뮬레이션 내부의 ECU 간 메시지 기반 통신을 구현합니다.
"""

import can
import logging

logger = logging.getLogger(__name__)

class VirtualCANBus:
    """가상 CAN 버스 통신을 담당하는 래퍼 클래스"""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(VirtualCANBus, cls).__new__(cls)
        return cls._instance

    def __init__(self, channel="seavs_can"):
        if not hasattr(self, "_initialized"):
            try:
                # 윈도우 환경에서도 동작하는 in-memory virtual CAN bus 생성
                self.bus = can.interface.Bus(bustype='virtual', channel=channel, bitrate=500000)
                logger.info(f"가상 CAN 버스 '{channel}' 활성화 완료.")
            except Exception as e:
                logger.error(f"가상 CAN 버스 생성 실패: {e}")
                self.bus = None
            self._initialized = True

    def send(self, arbitration_id, data_bytes):
        """
        CAN 메시지를 가상 버스로 전송한다.
        :param arbitration_id: CAN ID (예: 0x110)
        :param data_bytes: 전송할 데이터 바이트 배열 (최대 8바이트, list of int)
        """
        if not self.bus:
            return

        # 8바이트 패딩
        payload = list(data_bytes)
        if len(payload) < 8:
            payload.extend([0] * (8 - len(payload)))
        elif len(payload) > 8:
            payload = payload[:8]

        msg = can.Message(
            arbitration_id=arbitration_id,
            data=payload,
            is_extended_id=False
        )
        try:
            self.bus.send(msg)
        except can.CanError as e:
            logger.warning(f"CAN 전송 오류 (ID: {hex(arbitration_id)}): {e}")

    def receive(self, timeout=0.01):
        """
        가상 버스에서 CAN 메시지를 수신한다.
        :param timeout: 수신 대기 시간 (초)
        :return: can.Message 객체 또는 None
        """
        if not self.bus:
            return None
            
        try:
            return self.bus.recv(timeout=timeout)
        except Exception:
            return None
