# 타워크레인 AI 안전 시스템

created to ensure the safety of tower cranes using AI

AI를 사용하여 타워크레인으로 인한 인명피해를 방지하기 위해 개발되었습니다.

---

## 프로젝트 소개

레고 피규어(사람 대신)를 YOLOv8로 학습시켜 위험 구역 내 감지 시  
타워크레인 DC모터를 자동으로 정지시키는 안전 시스템입니다.

---

## 사용 기술

- Python 3 (YOLOv8 객체 감지)
- Raspberry Pi 5
- Raspberry Pi Camera Module 3
- Arduino
- L298N 모터 드라이버
- DC 모터

---

## 동작 방식

1. 카메라 모듈3가 위험 구역을 실시간 촬영
2. YOLOv8이 레고 피규어(사람) 감지
3. 위험 구역 진입 감지 → 라즈베리파이가 아두이노로 `DANGER` 신호 전송
4. 아두이노 수신 → 모터 즉시 정지 + LED/부저 경고
5. 위험 구역 벗어남 → `SAFE` 신호 전송 → 모터 자동 재가동

---

## 설치 방법

```bash
# 시스템 패키지
sudo apt update
sudo apt install python3-pip python3-opencv python3-picamera2 -y

# 파이썬 패키지
pip3 install ultralytics gpiozero pyserial
```

---

## 파일 구성

```
├── arduino/
│   └── motor_control.ino   # 아두이노 모터/LED/부저 제어
├── python/
│   └── detect.py           # 라즈베리파이 AI 감지 + 시리얼 송신
└── model/
    └── best.pt             # YOLOv8 레고 학습 모델
```

---

## 배선

| 아두이노 핀 | 연결 부품 |
|---|---|
| PIN 8 | L298N IN1 |
| PIN 9 | L298N IN2 |
| PIN 10 (PWM) | L298N ENA |
| PIN 5 | 빨간 LED |
| PIN 6 | 초록 LED |
| PIN 7 | 부저 |

> 라즈베리파이 ↔ 아두이노 : USB 케이블 1개로 연결 (전원 + 시리얼 통신)
