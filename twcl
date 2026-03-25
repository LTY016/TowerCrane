import serial
import time
import requests
import torch
from ultralytics import YOLO

# ========== GitHub에서 모델 다운로드 ==========
MODEL_URL = "https://raw.githubusercontent.com/유저명/타워크레인/main/best.pt"
MODEL_PATH = "best.pt"

def download_model():
    print("모델 다운로드 중...")
    response = requests.get(MODEL_URL)
    with open(MODEL_PATH, "wb") as f:
        f.write(response.content)
    print("모델 다운로드 완료!")

# ========== 아두이노 시리얼 연결 ==========
# Windows: "COM3", Mac/Linux: "/dev/ttyUSB0"
SERIAL_PORT = "COM3"
BAUD_RATE   = 9600

def connect_arduino():
    try:
        arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)  # 연결 안정화 대기
        print(f"아두이노 연결 완료: {SERIAL_PORT}")
        return arduino
    except Exception as e:
        print(f"아두이노 연결 실패: {e}")
        return None

# ========== 메인 실행 ==========
def main():
    # 1. 모델 다운로드
    download_model()

    # 2. YOLO 모델 로드
    model = YOLO(MODEL_PATH)
    print("AI 모델 로드 완료!")

    # 3. 아두이노 연결
    arduino = connect_arduino()

    # 4. 웹캠 실행 (0 = 기본 카메라)
    import cv2
    cap = cv2.VideoCapture(0)

    person_detected = False

    print("감지 시작! 'q' 누르면 종료")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 5. YOLO로 객체 감지
        results = model(frame, conf=0.5)  # 신뢰도 50% 이상만

        detected_now = False

        for result in results:
            for box in result.boxes:
                cls_name = model.names[int(box.cls)]

                # 레고 피규어 클래스 이름에 맞게 수정!
                if cls_name == "person" or cls_name == "lego":
                    detected_now = True

                    # 감지 박스 그리기
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(frame, f"{cls_name} 감지!", (x1, y1-10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        # 6. 상태 변화 시에만 아두이노로 신호 전송
        if detected_now and not person_detected:
            print("🚨 사람 감지 → 모터 정지 신호 전송")
            if arduino:
                arduino.write(b"PERSON_ON\n")
            person_detected = True

        elif not detected_now and person_detected:
            print("✅ 사람 사라짐 → 대기 신호 전송")
            if arduino:
                arduino.write(b"PERSON_OFF\n")
            person_detected = False

        # 7. 화면 표시
        status = "🚨 사람 감지!" if person_detected else "✅ 안전"
        cv2.putText(frame, status, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
        cv2.imshow("타워크레인 AI 감지", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    if arduino:
        arduino.close()

if __name__ == "__main__":
    main()
