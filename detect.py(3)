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
time.sleep(2)

# ========== 위험 구역 좌표 설정 (원하는 대로 조절하세요) ==========
ZONE_X1, ZONE_Y1 = 150, 100   # 위험 구역 좌상단
ZONE_X2, ZONE_Y2 = 500, 400   # 위험 구역 우하단

def is_in_zone(x1, y1, x2, y2):
    """person 박스의 중심점이 위험 구역 안에 있는지 확인"""
    cx = (x1 + x2) // 2
    cy = (y1 + y2) // 2
    return ZONE_X1 < cx < ZONE_X2 and ZONE_Y1 < cy < ZONE_Y2

while True:
    ret, frame = cap.read()
    if not ret:
        print("웹캠 연결 오류!")
        break

    height, width = frame.shape[:2]
    results = model(frame, conf=0.5, verbose=False)

    person_count = 0
    person_in_zone = False  # 위험 구역 내 person 여부

    for result in results:
        for box in result.boxes:
            cls_name = model.names[int(box.cls)]
            if cls_name == "person":
                person_count += 1
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                confidence = float(box.conf)

                # 위험 구역 안에 있는지 확인
                in_zone = is_in_zone(x1, y1, x2, y2)
                if in_zone:
                    person_in_zone = True
                    box_color = (0, 0, 255)   # 빨간색 (구역 내)
                else:
                    box_color = (255, 165, 0) # 주황색 (구역 밖)

                # 감지 박스
                cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
                cv2.putText(frame, f"person {confidence:.0%}",
                            (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7, box_color, 2)

    # ========== 위험 구역 사각형 그리기 ==========
    zone_color = (0, 0, 255) if person_in_zone else (0, 255, 0)
    cv2.rectangle(frame, (ZONE_X1, ZONE_Y1), (ZONE_X2, ZONE_Y2), zone_color, 3)
    cv2.putText(frame, "DANGER ZONE", (ZONE_X1, ZONE_Y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, zone_color, 2)

    # ========== 왼쪽 위 : person 몇 명 ==========
    cv2.putText(frame, f"person : {person_count}명", (10, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)

    # ========== 오른쪽 위 : 위험 / 안전 ==========
    if person_in_zone:
        status = "위험"
        color  = (0, 0, 255)
    else:
        status = "안전"
        color  = (0, 255, 0)

    text_size = cv2.getTextSize(status, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 2)[0]
    text_x    = width - text_size[0] - 20
    cv2.putText(frame, status, (text_x, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 2)

    cv2.imshow("타워크레인 AI 감지", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
