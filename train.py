# train.py
from ultralytics import YOLO

# YOLOv8 기본 모델 불러오기 (처음엔 이걸로 시작)
model = YOLO("yolov8n.pt")

# 학습 시작
model.train(
    data="dataset/data.yaml",  # Roboflow에서 받은 파일 경로
    epochs=50,                 # 학습 횟수 (많을수록 정확해짐)
    imgsz=640,                 # 이미지 크기
    batch=16,                  # 한번에 처리할 이미지 수
    name="lego_model"          # 저장 폴더 이름
)

print("학습 완료!")
print("best.pt 위치: runs/detect/lego_model/weights/best.pt")
```

---

## Step 4. 학습 후 best.pt 위치
```
runs/
└── detect/
    └── lego_model/
        └── weights/
            └── best.pt  ← 이걸 GitHub에 올리면 됨!
