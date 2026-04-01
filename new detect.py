import serial
import time
import requests
import torch
from ultralytics import YOLO
import cv2

# ========== GitHub에서 모델 다운로드 ==========
# 주의: 현재 GitHub 저장소(LTY016/TowerCrane) 메인에 best.pt 파일이 업로드되어 있어야 합니다.
# 파일명이 다르다면 아래 URL의 'best.pt' 부분을 실제 파일명으로 변경해주세요.
MODEL_URL = "https://raw.githubusercontent.com/LTY016/TowerCrane/main/best.pt"
MODEL_PATH = "best.pt"

def download_model( ):
    print("모델 다운로드 중...")
    try:
        response = requests.get(MODEL_URL)
        response.raise_for_status() # 다운로드 실패 시 예외 발생
        with open(MODEL_PATH, "wb") as f:
            f.write(response.content)
        print("모델 다운로드 완료!")
    except Exception as e:
        print(f"모델 다운로드 실패: {e}")
        print("로컬에 이미 모델이 있다면 그대로 진행합니다.")

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
    try:
        model = YOLO(MODEL_PATH)
        print("AI 모델 로드 완료!")
    except Exception as e:
        print(f"모델 로드 실패! {MODEL_PATH} 파일이 존재하는지 확인해주세요. 에러: {e}")
        return

    # 3. 아두이노 연결
    arduino = connect_arduino()

    # 4. 웹캠 실행 (0 = 기본 카메라)
    cap = cv2.VideoCapture(0)

    person_detected = False

    print("감지 시작! 'q' 누르면 종료")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("웹캠 프레임을 읽어올 수 없습니다.")
            break

        # 5. YOLO로 객체 감지
        results = model(frame, conf=0.5)  # 신뢰도 50% 이상만

        detected_now = False

        for result in results:
            for box in result.boxes:
                cls_name = model.names[int(box.cls)]

                # 모델이 'lego'로 인식하더라도 'person'으로 간주하여 처리
                if cls_name == "lego" or cls_name == "person":
                    detected_now = True
                    
                    # 화면에 표시할 이름은 'person'으로 통일
                    display_name = "person"

                    # 감지 박스 그리기
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(frame, f"{display_name} 감지!", (x1, y1-10),
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
