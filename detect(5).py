#!/usr/bin/env python3
"""
Tower Crane Safety System - Raspberry Pi 5
Camera Module 3 -> YOLOv8 LEGO Detection -> Arduino Serial Signal
"""
 
import time
import sys
import logging
import serial
import cv2
from picamera2 import Picamera2
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
try:
    arduino = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
    time.sleep(2)
    log.info("Arduino connected (/dev/ttyACM0)")
except Exception as e:
    log.error(f"Arduino connection failed: {e}")
    sys.exit(1)
 
# ========== 카메라 모듈3 초기화 ==========
picam2 = Picamera2()
config = picam2.create_preview_configuration(
    main={"size": (640, 480), "format": "RGB888"}
)
picam2.configure(config)
picam2.start()
time.sleep(1)
log.info("Camera Module 3 ready")
 
# ========== YOLOv8 모델 로드 ==========
MODEL_PATH   = "best.pt"
TARGET_CLASS = "lego"
 
try:
    model = YOLO(MODEL_PATH)
    log.info(f"Model loaded: {MODEL_PATH}")
except Exception:
    log.warning(f"{MODEL_PATH} not found -> using yolov8n.pt (person)")
    model        = YOLO("yolov8n.pt")
    TARGET_CLASS = "person"
 
log.info(f"Target class: {TARGET_CLASS}")
 
# ========== 위험 구역 좌표 ==========
ZONE_X1, ZONE_Y1 = 150, 100
ZONE_X2, ZONE_Y2 = 500, 400
 
# ========== 상태 변수 ==========
FRAME_SKIP   = 2
frame_count  = 0
last_results = []
prev_danger  = False
 
def is_in_zone(x1, y1, x2, y2):
    cx = (x1 + x2) // 2
    cy = (y1 + y2) // 2
    return ZONE_X1 < cx < ZONE_X2 and ZONE_Y1 < cy < ZONE_Y2
 
def send_signal(danger: bool):
    global prev_danger
    if danger == prev_danger:
        return
    prev_danger = danger
    signal = b'DANGER\n' if danger else b'SAFE\n'
    try:
        arduino.write(signal)
        log.warning(f"Signal: {'DANGER -> Motor STOP' if danger else 'SAFE -> Motor RUN'}")
    except Exception as e:
        log.error(f"Serial error: {e}")
 
# ========== 메인 루프 ==========
log.info("===== Tower Crane Safety System START =====")
log.info("Press 'q' to quit")
 
try:
    while True:
        # 카메라에서 프레임 읽기
        frame = picam2.capture_array()
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        frame_count += 1
        height, width = frame.shape[:2]
 
        # 추론
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
                    confidence      = float(box.conf)
                    in_zone = is_in_zone(x1, y1, x2, y2)
                    if in_zone:
                        danger_detected = True
                        box_color = (0, 0, 255)
                    else:
                        box_color = (255, 165, 0)
 
                    cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
                    cv2.putText(frame, f"LEGO {confidence:.0%}",
                                (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.7, box_color, 2)
 
        # 아두이노 신호 전송
        send_signal(danger_detected)
 
        # 위험 구역 표시
        zone_color = (0, 0, 255) if danger_detected else (0, 255, 0)
        cv2.rectangle(frame, (ZONE_X1, ZONE_Y1), (ZONE_X2, ZONE_Y2), zone_color, 3)
        cv2.putText(frame, "DANGER ZONE", (ZONE_X1, ZONE_Y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, zone_color, 2)
 
        # 왼쪽 위: 감지 수
        cv2.putText(frame, f"LEGO: {obj_count}", (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
 
        # 오른쪽 위: 위험/안전
        status, color = ("DANGER! STOP", (0, 0, 255)) if danger_detected else ("SAFE", (0, 255, 0))
        text_size = cv2.getTextSize(status, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)[0]
        text_x    = width - text_size[0] - 20
        cv2.putText(frame, status, (text_x, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)
 
        # 화면 출력
        cv2.imshow("Tower Crane AI", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
 
except KeyboardInterrupt:
    log.info("Stopped by user")
 
finally:
    arduino.write(b'SAFE\n')
    arduino.close()
    picam2.stop()
    cv2.destroyAllWindows()
    log.info("===== System Stopped =====")
 
