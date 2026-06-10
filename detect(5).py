#!/usr/bin/env python3
"""
타워크레인 안전 시스템 - 라즈베리파이5
카메라모듈3 x2 → YOLOv8 레고 감지 → 아두이노 시리얼 신호 전송
둘 중 하나라도 위험 감지 시 DANGER 신호 전송
"""
 
import time
import sys
import logging
import serial
import cv2
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
    log.info("아두이노 시리얼 연결 완료 (/dev/ttyACM0)")
except Exception as e:
    log.error(f"아두이노 연결 실패: {e}")
    log.error("포트 확인: ls /dev/ttyUSB* 또는 ls /dev/ttyACM*")
    sys.exit(1)
 
# ========== 카메라 모듈3 x2 (Picamera2) ==========
try:
    from picamera2 import Picamera2
 
    picam2_0 = Picamera2(0)  # 카메라 0번
    picam2_0.configure(picam2_0.create_preview_configuration(
        main={"size": (640, 480), "format": "RGB888"}
    ))
    picam2_0.start()
 
    picam2_1 = Picamera2(1)  # 카메라 1번
    picam2_1.configure(picam2_1.create_preview_configuration(
        main={"size": (640, 480), "format": "RGB888"}
    ))
    picam2_1.start()
 
    time.sleep(2)
    log.info("카메라 모듈3 x2 초기화 완료")
 
    def get_frame(cam):
        frame = cam.capture_array()
        return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
 
except ImportError:
    log.error("Picamera2 없음! 설치: sudo apt install python3-picamera2")
    sys.exit(1)
 
# ========== YOLOv8 모델 로드 ==========
MODEL_PATH   = "best.pt"
TARGET_CLASS = "person"
 
try:
    model = YOLO(MODEL_PATH)
    log.info(f"모델 로드 완료: {MODEL_PATH}")
except Exception:
    log.warning(f"{MODEL_PATH} 없음 → yolov8n.pt(person) 로 대체")
    model        = YOLO("yolov8n.pt")
    TARGET_CLASS = "person"
 
log.info(f"감지 클래스: {TARGET_CLASS}")
 
# ========== 위험 구역 좌표 (두 카메라 동일 적용) ==========
ZONE_X1, ZONE_Y1 = 150, 100
ZONE_X2, ZONE_Y2 = 500, 400
 
# ========== 상태 변수 ==========
FRAME_SKIP   = 2
frame_count  = 0
last_results_0 = []
last_results_1 = []
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
        log.warning(f"▶ 신호 전송: {'DANGER → 모터 정지' if danger else 'SAFE → 모터 재가동'}")
    except Exception as e:
        log.error(f"시리얼 전송 오류: {e}")
 
def process_frame(frame, results):
    """프레임에서 레고 감지 및 화면 그리기"""
    obj_count       = 0
    danger_detected = False
    height, width   = frame.shape[:2]
 
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
 
    # 위험 구역 표시
    zone_color = (0, 0, 255) if danger_detected else (0, 255, 0)
    cv2.rectangle(frame, (ZONE_X1, ZONE_Y1), (ZONE_X2, ZONE_Y2), zone_color, 3)
    cv2.putText(frame, "DANGER ZONE", (ZONE_X1, ZONE_Y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, zone_color, 2)
 
    # 감지 수
    cv2.putText(frame, f"LEGO : {obj_count}개", (10, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
 
    # 위험/안전
    status, color = ("위험! 모터정지", (0, 0, 255)) if danger_detected else ("안전 가동중", (0, 255, 0))
    text_size = cv2.getTextSize(status, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)[0]
    text_x    = width - text_size[0] - 20
    cv2.putText(frame, status, (text_x, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)
 
    return frame, danger_detected
 
# ========== 메인 루프 ==========
log.info("===== 타워크레인 안전 시스템 시작 =====")
log.info("종료: q 키")
 
try:
    while True:
        frame_count += 1
 
        # 두 카메라에서 프레임 읽기
        frame0 = get_frame(picam2_0)
        frame1 = get_frame(picam2_1)
 
        # FRAME_SKIP마다 추론
        if frame_count % FRAME_SKIP == 0:
            last_results_0 = model(frame0, conf=0.5, verbose=False)
            last_results_1 = model(frame1, conf=0.5, verbose=False)
 
        # 각 카메라 프레임 처리
        frame0, danger0 = process_frame(frame0, last_results_0)
        frame1, danger1 = process_frame(frame1, last_results_1)
 
        # 카메라 번호 표시
        cv2.putText(frame0, "CAM 0", (10, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
        cv2.putText(frame1, "CAM 1", (10, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
 
        # 둘 중 하나라도 위험이면 DANGER
        danger_detected = danger0 or danger1
        send_signal(danger_detected)
 
        # 두 화면 가로로 합쳐서 출력
        combined = cv2.hconcat([frame0, frame1])
        cv2.imshow("Tower Crane AI", combined)
 
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
 
except KeyboardInterrupt:
    log.info("사용자 종료 (Ctrl+C)")
 
finally:
    arduino.write(b'SAFE\n')
    arduino.close()
    picam2_0.stop()
    picam2_1.stop()
    cv2.destroyAllWindows()
    log.info("===== 시스템 종료 =====")
 
