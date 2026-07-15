/*
  타워크레인 안전 시스템 - 아두이노
  라즈베리파이에서 시리얼 신호 수신
  DANGER → 모터 정지 + 빨간LED + 부저
  SAFE   → 모터 가동 + 초록LED
*/

// ========== 핀 설정 ==========
const int MOTOR_IN1 = 8;
const int MOTOR_IN2 = 9;
const int MOTOR_ENA = 10;
const int LED_DANGER = 5;
const int LED_SAFE   = 6;
const int BUZZER     = 7;

// ========== 상태 변수 ==========
bool isDanger = false;
unsigned long lastBuzzerTime = 0;
bool buzzerState = false;

void setup() {
  Serial.begin(9600);

  pinMode(MOTOR_IN1, OUTPUT);
  pinMode(MOTOR_IN2, OUTPUT);
  pinMode(MOTOR_ENA, OUTPUT);
  pinMode(LED_DANGER, OUTPUT);
  pinMode(LED_SAFE,   OUTPUT);
  pinMode(BUZZER,     OUTPUT);

  motorStart();
  safeMode();
  Serial.println("아두이노 초기화 완료");
}

void loop() {
  // ========== 시리얼 수신 ==========
  if (Serial.available() > 0) {
    String signal = Serial.readStringUntil('\n');
    signal.trim();

    if (signal == "DANGER" && !isDanger) {
      isDanger = true;
      motorStop();
      dangerMode();
      Serial.println("DANGER 수신 → 모터 정지");
    }
    else if (signal == "SAFE" && isDanger) {
      isDanger = false;
      motorStart();
      safeMode();
      Serial.println("SAFE 수신 → 모터 재가동");
    }
  }

  // ========== 부저 논블로킹 처리 ==========
  // delay() 대신 millis() 사용 → 시리얼 수신 지연 없음
  if (isDanger) {
    unsigned long now = millis();
    if (!buzzerState && now - lastBuzzerTime >= 400) {
      tone(BUZZER, 1000, 200);
      buzzerState = true;
      lastBuzzerTime = now;
    }
    else if (buzzerState && now - lastBuzzerTime >= 200) {
      buzzerState = false;
      lastBuzzerTime = now;
    }
  }
}

// ========== 모터 제어 ==========
void motorStart() {
  // 부드럽게 시작 (0 → 200)
  digitalWrite(MOTOR_IN1, HIGH);
  digitalWrite(MOTOR_IN2, LOW);
  for (int speed = 0; speed <= 200; speed += 10) {
    analogWrite(MOTOR_ENA, speed);
    delay(20);
  }
}

void motorStop() {
  // 즉시 정지
  analogWrite(MOTOR_ENA, 0);
  digitalWrite(MOTOR_IN1, LOW);
  digitalWrite(MOTOR_IN2, LOW);
}

// ========== LED 제어 ==========
void dangerMode() {
  digitalWrite(LED_DANGER, HIGH);
  digitalWrite(LED_SAFE,   LOW);
}

void safeMode() {
  digitalWrite(LED_DANGER, LOW);
  digitalWrite(LED_SAFE,   HIGH);
  noTone(BUZZER);
  buzzerState = false;
}
