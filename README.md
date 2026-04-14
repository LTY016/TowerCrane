# # 타워크레인 AI 안전 시스템
created to ensure the stability of tower cranes using AI

AI를 사용하여 타워 크레인으로 인한 인명피해의 안정성을 확보하기 위해 개발되었습니다.

## 프로젝트 소개
레고 피규어(사람 대체)를 딥러닝으로 학습시켜 사람을 감지하면
타워크레인 DC모터를 자동으로 정지시키는 시스템입니다.

## 사용 기술
- Python (YOLOv8 객체감지)
- Razpberry5 pi
- L298N 모터 드라이버(불필요 가능성 있음)
- DC 모터

## 동작 방식
1. AI 카메라가 사람(레고 피규어) 감지
2. 감지 시 → 아두이노로 신호 전송
3. 아두이노 → 모터 즉시 정지
4. 사람 사라짐 → 컨트롤러 버튼 누르면 재가동

## 설치 방법
pip install ultralytics
pip install requests

## 파일 구성
├── arduino/
│   └── motor_control.ino
├── python/
│   └── detect.py
└── model/
    └── best.pt
