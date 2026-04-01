import cv2
import time
from ultralytics import YOLO

print("코드 시작!")

# ========== 모델 로드 ==========
model = YOLO("yolov8n.pt")

print("AI 모델 로드 완료!")
print("웹캠 실행 중... 'q' 누르면 종료")

# ========== 웹캠 실행 ==========
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

time.sleep(2)  # 웹캠 안정화 대기

while True:
    ret, frame = cap.read()
    if not ret:
        print("웹캠 연결 오류!")
        break

    height, width = frame.shape[:2]

    results = model(frame, conf=0.5, verbose=False)

    person_count = 0

    for result in results:
        for box in result.boxes:
            cls_name = model.names[int(box.cls)]

            if cls_name == "person":
                person_count += 1

                x1, y1, x2, y2 = map(int, box.xyxy[0])
                confidence = float(box.conf)

                # 감지 박스
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.putText(frame, f"person {confidence:.0%}",
                            (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7, (0, 0, 255), 2)

    # ========== 왼쪽 위 : person 몇 명 ==========
    cv2.putText(frame, f"person : {person_count}명", (10, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)

    # ========== 오른쪽 위 : 위험 / 안전 ==========
    if person_count > 0:
        status = "위험"
        color  = (0, 0, 255)   # 빨간색
    else:
        status = "안전"
        color  = (0, 255, 0)   # 초록색

    # 오른쪽 정렬
    text_size = cv2.getTextSize(status, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 2)[0]
    text_x    = width - text_size[0] - 20

    cv2.putText(frame, status, (text_x, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 2)

    cv2.imshow("타워크레인 AI 감지", frame)