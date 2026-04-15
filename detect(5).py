#!/usr/bin/env python3
"""
타워크레인 안전 시스템 - 라즈베리파이5
카메라모듈3 → YOLOv8 레고 감지 → 아두이노 시리얼 신호 전송
모니터 없이 백그라운드 실행
"""

import time
import sys
import logging
import serial
from ultralytics import YOLO

# ========== 로그 설정 ==========
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("safety_log.txt"),
    ]
)
log = logging.getLogger(__name__)

# ========== 아두이노 시리얼 연결 ==========
# 라즈베리파이에서 아두이노 연결 시 포트 확인:
# ls /dev/ttyUSB* 또는 ls /dev/ttyACM*
try:
    arduino = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
    time.sleep(2)  # 아두이노 초기화 대기
    log.info("아두이노 시리얼 연결 완료 (/dev/ttyUSB0)")
except Exception as e:
    log.error(f"아두이노 연결 실패: {e}")
    log.error("포트 확인: ls /dev/ttyUSB* 또는 ls /dev/ttyACM*")
    sys.exit(1)

# ========== 카메라 모듈3 (Picamera2) ==========
try:
    from picamera2 import Picamera2
    import cv2

    picam2 = Picamera2()
    picam2.configure(picam2.create_preview_configuration(
        main={"size": (640, 480), "format": "RGB888"}
    ))
    picam2.start()
    time.sleep(2)
    log.info("카메라 모듈3 초기화 완료")

    def get_frame():
        frame = picam2.capture_array()
        return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

except ImportError:
    log.error("Picamera2 없음! 설치: sudo apt install python3-picamera2")
    sys.exit(1)

# ========== YOLOv8 모델 로드 ==========
# 레고 학습 완료 후 → "lego_best.pt" 로 교체
MODEL_PATH   = "lego_best.pt"
TARGET_CLASS = "lego"

try:
    model = YOLO(MODEL_PATH)
    log.info(f"모델 로드 완료: {MODEL_PATH}")
except Exception:
    log.warning(f"{MODEL_PATH} 없음 → yolov8n.pt(person) 로 대체")
    model        = YOLO("yolov8n.pt")
    TARGET_CLASS = "person"

log.info(f"감지 클래스: {TARGET_CLASS}")

# ========== 위험 구역 좌표 ==========
ZONE_X1, ZONE_Y1 = 150, 100
ZONE_X2, ZONE_Y2 = 500, 400

# ========== 상태 변수 ==========
FRAME_SKIP   = 2
frame_count  = 0
last_results = []
prev_danger  = False  # 상태 변화 있을 때만 신호 전송

def is_in_zone(x1, y1, x2, y2):
    """바운딩박스 중심이 위험 구역 안인지 확인"""
    cx = (x1 + x2) // 2
    cy = (y1 + y2) // 2
    return ZONE_X1 < cx < ZONE_X2 and ZONE_Y1 < cy < ZONE_Y2

def send_signal(danger: bool):
    """상태 변화 시에만 아두이노로 신호 전송"""
    global prev_danger
    if danger == prev_danger:
        return  # 같은 상태면 전송 생략
    prev_danger = danger

    signal = b'DANGER\n' if danger else b'SAFE\n'
    try:
        arduino.write(signal)
        log.warning(f"▶ 신호 전송: {'DANGER → 모터 정지' if danger else 'SAFE → 모터 재가동'}")
    except Exception as e:
        log.error(f"시리얼 전송 오류: {e}")

# ========== 메인 루프 ==========
log.info("===== 타워크레인 안전 시스템 시작 =====")
log.info("종료: Ctrl+C")

try:
    while True:
        frame = get_frame()
        frame_count += 1

        # FRAME_SKIP마다 추론 실행
        if frame_count % FRAME_SKIP == 0:
            last_results = model(frame, conf=0.5, verbose=False)
        results = last_results

        obj_count       = 0
        danger_detected = False

        for result in results:
            for box in result.boxes:
                if model.names[int(box.cls)] == TARGET_CLASS:
                    obj_count += 1
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    if is_in_zone(x1, y1, x2, y2):
                        danger_detected = True

        # 아두이노로 신호 전송
        send_signal(danger_detected)

        # 10프레임마다 상태 로그
        if frame_count % 10 == 0:
            status = "위험" if danger_detected else "안전"
            log.info(f"[{status}] 감지: {obj_count}개  |  프레임: {frame_count}")

except KeyboardInterrupt:
    log.info("사용자 종료 (Ctrl+C)")

finally:
    arduino.write(b'SAFE\n')  # 종료 시 안전 신호 전송
    arduino.close()
    picam2.stop()
    log.info("===== 시스템 종료 =====")
