/*
 * 타워크레인 DC모터 제어 시스템
 * - L298N 모터 드라이버
 * - 버튼(컨트롤러) 입력
 * - 시리얼 통신으로 AI 객체감지 신호 수신
 * 
 * [핀 연결]
 * IN1  → 아두이노 D5
 * IN2  → 아두이노 D6
 * ENA  → 아두이노 D9 (PWM)
 * 버튼 → 아두이노 D2
 * LED  → 아두이노 D13 (상태 표시)
 */

// ========== 핀 정의 ==========
const int IN1_PIN     = 5;   // L298N IN1
const int IN2_PIN     = 6;   // L298N IN2
const int ENA_PIN     = 9;   // L298N ENA (PWM 속도제어)
const int BUTTON_PIN  = 2;   // 컨트롤러 버튼
const int LED_PIN     = 13;  // 상태 LED

// ========== 모터 설정 ==========
const int MOTOR_SPEED = 200; // 모터 속도 (0~255)

// ========== 상태 변수 ==========
bool humanDetected   = false; // AI 감지 상태
bool motorRunning    = false; // 모터 동작 상태
bool motorAllowed    = false; // 사람 사라진 후 컨트롤러 승인 여부
bool lastButtonState = HIGH;  // 버튼 이전 상태 (풀업)

// ========== 시리얼 수신 버퍼 ==========
String serialBuffer = "";

void setup() {
  Serial.begin(9600);

  pinMode(IN1_PIN,    OUTPUT);
  pinMode(IN2_PIN,    OUTPUT);
  pinMode(ENA_PIN,    OUTPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP); // 내부 풀업 저항
  pinMode(LED_PIN,    OUTPUT);

  motorStop();

  Serial.println("=== 타워크레인 모터 제어 시스템 시작 ===");
  Serial.println("AI 신호: 'PERSON_ON'  → 사람 감지됨");
  Serial.println("AI 신호: 'PERSON_OFF' → 사람 벗어남");
}

void loop() {
  // 1. AI 감지 신호 수신 (시리얼)
  receiveAISignal();

  // 2. 컨트롤러 버튼 읽기
  checkButton();

  // 3. 모터 제어 로직
  controlMotor();

  // 4. LED 상태 표시
  updateLED();

  delay(50);
}

// ========== AI 신호 수신 ==========
void receiveAISignal() {
  while (Serial.available() > 0) {
    char c = Serial.read();

    if (c == '\n') {
      serialBuffer.trim();

      if (serialBuffer == "PERSON_ON") {
        humanDetected = true;
        motorAllowed  = false; // 승인 초기화
        Serial.println("[AI] 사람 감지 → 모터 즉시 정지");
      }
      else if (serialBuffer == "PERSON_OFF") {
        humanDetected = false;
        Serial.println("[AI] 사람 벗어남 → 버튼 누르면 재가동");
      }

      serialBuffer = "";
    } else {
      serialBuffer += c;
    }
  }
}

// ========== 버튼 입력 (엣지 감지) ==========
void checkButton() {
  bool currentButtonState = digitalRead(BUTTON_PIN);

  // 버튼 눌림 감지 (HIGH→LOW, 풀업 기준)
  if (lastButtonState == HIGH && currentButtonState == LOW) {
    if (!humanDetected) {
      // 사람 없을 때만 버튼으로 승인
      motorAllowed = !motorAllowed; // 토글
      Serial.print("[CTRL] 버튼 입력 → 모터 ");
      Serial.println(motorAllowed ? "가동 승인" : "정지 명령");
    } else {
      Serial.println("[CTRL] 버튼 입력 무시 → 사람 감지 중");
    }
  }

  lastButtonState = currentButtonState;
}

// ========== 모터 제어 로직 ==========
void controlMotor() {
  if (humanDetected) {
    // 최우선: 사람 감지 → 즉시 정지
    if (motorRunning) {
      motorStop();
      motorRunning = false;
    }
  }
  else if (motorAllowed && !motorRunning) {
    // 사람 없음 + 버튼 승인 → 모터 가동
    motorForward();
    motorRunning = true;
  }
  else if (!motorAllowed && motorRunning) {
    // 버튼으로 정지 명령
    motorStop();
    motorRunning = false;
  }
}

// ========== 모터 드라이버 함수 ==========
void motorForward() {
  digitalWrite(IN1_PIN, HIGH);
  digitalWrite(IN2_PIN, LOW);
  analogWrite(ENA_PIN, MOTOR_SPEED);
  Serial.println("[MOTOR] 정방향 회전 시작 (360° 연속)");
}

void motorStop() {
  digitalWrite(IN1_PIN, LOW);
  digitalWrite(IN2_PIN, LOW);
  analogWrite(ENA_PIN, 0);
  Serial.println("[MOTOR] 정지");
}

// ========== LED 상태 표시 ==========
void updateLED() {
  if (humanDetected) {
    // 사람 감지 → 빠른 점멸 (경고)
    digitalWrite(LED_PIN, (millis() / 200) % 2);
  } else if (motorRunning) {
    // 모터 동작 중 → 켜짐
    digitalWrite(LED_PIN, HIGH);
  } else {
    // 대기 중 → 느린 점멸
    digitalWrite(LED_PIN, (millis() / 800) % 2);
  }
}
```

---

## 동작 흐름 요약
```
[AI 카메라]
    │
    ├─ 사람 감지 → "PERSON_ON\n" 전송 → 모터 즉시 OFF ❌
    │
    └─ 사람 사라짐 → "PERSON_OFF\n" 전송
                         │
                         └─ 대기 상태 (모터 여전히 OFF)
                               │
                        [버튼 누름] 
                               │
                               └─ 모터 ON ✅ (360° 연속 회전)
