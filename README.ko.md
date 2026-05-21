-# 🤖 이 프로그램은 AI(Antigravity)에 의해 작성된 스마트 차량 제어 시스템입니다.

# 🚗 SEAVS: Smart Emotion-Aware Vehicle System
> **AI 감정 분석 및 졸음 감지 기술 기반 스마트 차량 콕핏 대시보드 시뮬레이터**

[🌐 Read in English](README.md)

---

## 🌟 주요 기능 (Key Features)

* **🧠 실시간 AI 감정 분석 (Emotion Detection)**
  - ONNX 기반의 **FER+ 모델**(`emotion_ferplus.onnx`)을 활용하여 운전자의 감정을 실시간으로 분석합니다.
  - 감정 카테고리: `Angry`(분노), `Happy`(기쁨), `Sad`(슬픔), `Neutral`(평온), `Surprise`(놀람), `Disgust`(불쾌), `Fear`(공포)
  - 지배적인 감정(Dominant Emotion) 분석 및 상위 3개 감정 확률 점수 실시간 차트 제공.

* **👁️ 정밀 졸음 감지 (Drowsiness Detection)**
  - **MediaPipe Face Mesh (468 Landmarks)** 기술을 탑재하여 운전자의 양쪽 눈 특징점을 실시간으로 추출합니다.
  - 눈 깜박임 비율인 **EAR(Eye Aspect Ratio)** 수식을 계산하여 운전자의 졸음 여부를 지속적으로 진단합니다.
  - 운전자가 설정 임계값 이하로 3초 이상 눈을 감고 있을 경우 졸음(`Drowsy`) 상태로 판정하고 즉각적인 안전 인터락을 가동합니다.

* **❄️ 스마트 공조 및 조작계 연동 (Smart HVAC Interlock)**
  - **AI 자동 모드(Auto Mode)** 활성화 시, 졸음 감지 혹은 급격한 감정 변화에 반응하여 실내 온도, 에어컨(A/C) 전원 및 풍량을 최적의 상태로 조정합니다.
  - 예: **졸음(Drowsy) 감지 시** 공조기 전원을 강제로 ON으로 전환하고 냉각(A/C) 기능을 켜며, 풍량을 최대로 올려 운전자의 졸음을 깨우는 긴급 제어를 실행합니다.

* **📊 프리미엄 어두운 테마 UI 대시보드 (Premium Cockpit GUI)**
  - **CustomTkinter**를 사용하여 세련된 다크 모드 기반 스마트 콕핏 디자인을 구현하였습니다.
  - **실시간 비디오 피드**: 운전자의 얼굴 바운딩 박스 및 특징 랜드마크가 시각화되어 출력됩니다.
  - **차량 로그 및 경고 디스플레이**: 실시간 상태 업데이트와 직관적인 시스템 경고 메시지가 다채로운 색상 코드로 출력됩니다.
  - **에어컨 애니메이션**: 바람세기 및 냉방 상태에 따라 반응형 바람 그래픽 및 팬 애니메이션 효과가 가동됩니다.

---

## 🛠️ 기술 스택 (Tech Stack)

* **언어:** `Python 3.10+`
* **UI 프레임워크:** `CustomTkinter`, `Pillow`
* **인공지능 및 컴퓨터 비전:** `OpenCV (opencv-python)`, `MediaPipe`, `ONNX Runtime`
* **유틸리티 및 하드웨어 통신 연동용 프로토콜:** `paho-mqtt` (시뮬레이션 통신용), `pygrabber` (카메라 장치 자동 검색)

---

## 📂 프로젝트 구조 (Project Folder Structure)

```text
OpenCV_CarManage/
│
├── requirements.txt      # 프로젝트 의존성 라이브러리 목록
├── run.bat              # 가상환경 구축 및 원클릭 실행 스크립트
├── plan.txt             # 개발 설계 기획서
│
└── src/
    ├── main.py          # 애플리케이션 메인 엔트리 포인트 (UI 빌드 및 메인 루프)
    │
    ├── core/            # 비즈니스 로직 및 구성 관리
    │   ├── config_manager.py  # 시스템 설정 및 저장 기능
    │   ├── safety_system.py   # 졸음 및 이상 상태 분석 안전 관리자
    │   └── vehicle_env.py     # 차량 가상 실내 환경 변수 데이터
    │
    ├── vision/          # AI 및 컴퓨터 비전 처리 파이프라인
    │   ├── camera.py          # 카메라 디바이스 스레드 및 이미지 버퍼링
    │   ├── detectors.py       # MediaPipe Face Mesh 및 ONNX 감정 분석 백엔드
    │   ├── visualizer.py      # 비디오 프레임용 시각 보조 라이브러리
    │   ├── face_landmarker.task  # MediaPipe 랜드마크 모델 데이터
    │   └── emotion_ferplus.onnx  # 딥러닝 감정 분석 ONNX 가중치 파일
    │
    ├── simulation/      # 가상 연동 시뮬레이션
    │   └── simulation_manager.py # 차량 환경 피드백 및 시뮬레이션 메인 연산
    │
    └── ui/              # CustomTkinter 대시보드 컴포넌트
        ├── header.py          # AI 자동모드/오디오 토글 헤더 바
        ├── driver_seat.py     # 웹캠 영상 프레임 및 운전자 모니터링 패널
        ├── center_display.py  # 감정 디테일, 안전 경고 및 시스템 로그 스크린
        └── ac_panel.py        # 스마트 에어컨 컨트롤 및 바람 애니메이션 패널
```

---

## 🚀 시작하기 (How to Run)

본 프로젝트는 Windows 환경에서 가상환경(`venv`) 생성부터 실행까지 자동으로 완료하는 원클릭 배치 스크립트를 제공합니다.

### 1. 요구사항
* 웹캠(Webcam)이 연결된 PC
* Python 3.10 이상 설치 필수 (환경 변수 PATH 등록 권장)

### 2. 실행 방법
프로젝트 루트 디렉토리에서 **`run.bat`** 파일을 실행(더블 클릭)합니다.
```bash
# 또는 터미널(Command Prompt / PowerShell)에서 직접 실행
./run.bat
```
* **동작 과정:**
  1. 루트 디렉토리에 가상환경(`venv`)이 없는 경우 자동으로 생성합니다.
  2. 가상환경을 활성화하고 `requirements.txt`에 명시된 필수 패키지들을 무음 설치합니다.
  3. `src/main.py`를 실행하여 스마트 콕핏 대시보드 GUI를 구동합니다.

---

## 🛡️ 복합 위험 대응 시나리오 (Safety Scenario)

시스템이 백그라운드에서 실시간 센서 및 인공지능 분석 결과를 종합하여 최적의 안전 반응 동작을 취합니다.

| 상황 (Driver State) | 시스템 진단 (Safety Evaluation) | 차량 대응 제어 (Vehicle Action) |
| :--- | :--- | :--- |
| **정상 (Neutral / Happy)** | 안전 운전 상태 유지 | 수동 또는 현재 공조 설정 유지 |
| **분노 감지 (Angry)** | 주의 운전 요망 | 경고 메시지 배너 출력 및 차분한 음악/환경 제공 제안 |
| **졸음 감지 (Drowsy, EAR 저하)** | **⚠️ 위험! 졸음 감지** | 대시보드 황색 경고 점멸, 경고음 재생, 에어컨 자동 ON, 냉방 및 풍량 최대 기동 |
| **카메라 이탈 (얼굴 미검지)** | **⚠️ 운전자 감지 안됨** | 경고 배너 및 안전 운행 점검 메시지 송출 |

---

## 💡 참고 사항
* **카메라 장치 선택:** 드라이버 모니터링 패널 내의 카메라 선택 드롭다운 메뉴를 이용해 원하는 카메라(웹캠) 디바이스로 즉각 전환할 수 있습니다.
* **오디오 알림:** 헤더의 오디오 토글 스위치로 졸음 감지 시의 경고음 알림 기능을 켜고 끌 수 있으며, 설정값은 프로그램 재시작 시에도 유지됩니다.
