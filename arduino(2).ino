/*
  타워크레인 안전 시스템 - 아두이노
  라즈베리파이에서 시리얼 신호 수신
  DANGER → 모터 정지 + 빨간LED + 부저
  SAFE   → 모터 가동 + 초록LED
*/

// ========== 핀 설정 ==========
// L298N 모터 드라이버
const int MOTOR_IN1 = 8;   // 모터 방향 A
const int MOTOR_IN2 = 9;   // 모터 방향 B
const int MOTOR_ENA = 10;  // 모터 속도 (PWM)

// LED / 부저
const int LED_DANGER = 5;  // 빨간 LED
const int LED_SAFE   = 6;  // 초록 LED
const int BUZZER     = 7;  // 부저

// ========== 상태 변수 ==========
bool isDanger = false;

void setup() {
  Serial.begin(9600);  // 라즈베리파이와 통신 속도 (반드시 일치)

  // 핀 모드 설정
  pinMode(MOTOR_IN1, OUTPUT);
  pinMode(MOTOR_IN2, OUTPUT);
  pinMode(MOTOR_ENA, OUTPUT);
  pinMode(LED_DANGER, OUTPUT);
  pinMode(LED_SAFE,   OUTPUT);
  pinMode(BUZZER,     OUTPUT);

  // 시작 시 안전 상태로 초기화
  motorStart();
  safeMode();

  Serial.println("아두이노 초기화 완료");
}

void loop() {
  // 라즈베리파이에서 신호 수신
  if (Serial.available() > 0) {
    String signal = Serial.readStringUntil('\n');
    signal.trim();  // 공백/개행 제거

    if (signal == "DANGER") {
      isDanger = true;
      motorStop();
      dangerMode();
    }
    else if (signal == "SAFE") {
      isDanger = false;
      motorStart();
      safeMode();
    }
  }

  // 위험 상태일 때 부저 반복 (삐삐삐)
  if (isDanger) {
    tone(BUZZER, 1000, 200);   // 200ms 삐
    delay(400);
  }
}

// ========== 모터 제어 ==========
void motorStart() {
  analogWrite(MOTOR_ENA, 200);  // 속도 (0~255)
  digitalWrite(MOTOR_IN1, HIGH);
  digitalWrite(MOTOR_IN2, LOW);
}

void motorStop() {
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
}

