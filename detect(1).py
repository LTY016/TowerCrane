import cv2
from ultralytics import YOLO

# ========== 모델 로드 ==========
# 기본 YOLOv8 모델 사용 (best.pt 없어도 됨!)
model = YOLO("yolov8n.pt")  # 자동 다운로드됨

print("AI 모델 로드 완료!")
print("웹캠 실행 중... 'q' 누르면 종료")

# ========== 웹캠 실행 ==========
cap = cv2.VideoCapture(0)  # 0 = 기본 웹캠

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # ========== YOLO 감지 ==========
    results = model(frame, conf=0.5, verbose=False)

    person_detected = False

    for result in results:
        for box in result.boxes:
            cls_id   = int(box.cls)
            cls_name = model.names[cls_id]

            # 사람만 감지
            if cls_name == "person":
                person_detected = True

                # 감지 박스 그리기
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                confidence = float(box.conf)

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.putText(frame, f"사람 {confidence:.0%}",
                            (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8, (0, 0, 255), 2)

    # ========== 상태 표시 ==========
    if person_detected:
        status     = "🚨 사람 감지!"
        color = (0, 0, 255)   # 빨강
    else:
        status     = "✅ 안전"
        color = (0, 255, 0)   # 초록

    cv2.putText(frame, status, (10, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.2, color, 3)

    cv2.imshow("타워크레인 AI 감지", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()