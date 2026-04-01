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
 */

// ========== 핀 정의 ==========
const int IN1_PIN     = 5;   // L298N IN1 (모터 드라이버 입력 1)
const int IN2_PIN     = 6;   // L298N IN2 (모터 드라이버 입력 2)
const int ENA_PIN     = 9;   // L298N ENA (PWM 속도제어 핀)
const int BUTTON_PIN  = 2;   // 컨트롤러 버튼 핀

// ========== 모터 설정 ==========
const int MOTOR_SPEED = 200; // 모터 속도 (0~255, ENA 핀에 적용)

// ========== 상태 변수 ==========
bool humanDetected   = false; // AI 감지 상태 (Python에서 PERSON_ON/OFF 신호로 제어)
bool motorRunning    = false; // 모터 동작 상태
bool motorAllowed    = false; // 사람 사라진 후 컨트롤러 버튼으로 모터 가동 승인 여부
bool lastButtonState = HIGH;  // 버튼 이전 상태 (풀업 저항 사용 시 초기 HIGH)

// ========== 시리얼 수신 버퍼 ==========
String serialBuffer = ""; // Python에서 오는 시리얼 데이터를 임시 저장

void setup() {
  Serial.begin(9600); // Python과 동일한 보드레이트 설정

  // 핀 모드 설정
  pinMode(IN1_PIN,    OUTPUT);
  pinMode(IN2_PIN,    OUTPUT);
  pinMode(ENA_PIN,    OUTPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP); // 내부 풀업 저항 사용

  motorStop(); // 초기 모터 정지

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

  delay(50); // 짧은 지연으로 안정적인 동작 유지
}

// ========== AI 신호 수신 ==========
void receiveAISignal() {
  while (Serial.available() > 0) { // 시리얼 데이터가 있을 때까지 읽기
    char c = Serial.read(); // 한 글자씩 읽기

    if (c == '\n') { // 개행 문자(newline)가 오면 메시지 끝
      serialBuffer.trim(); // 수신된 문자열의 앞뒤 공백 제거

      if (serialBuffer == "PERSON_ON") {
        humanDetected = true; // 사람 감지 상태로 변경
        motorAllowed  = false; // 사람이 감지되면 모터 가동 승인 초기화 (안전 최우선)
        Serial.println("[AI] 사람 감지 → 모터 즉시 정지");
      }
      else if (serialBuffer == "PERSON_OFF") {
        humanDetected = false; // 사람 미감지 상태로 변경
        Serial.println("[AI] 사람 벗어남 → 버튼 누르면 재가동");
      }

      serialBuffer = ""; // 버퍼 초기화
    } else {
      serialBuffer += c; // 버퍼에 문자 추가
    }
  }
}

// ========== 버튼 입력 (엣지 감지) ==========
void checkButton() {
  bool currentButtonState = digitalRead(BUTTON_PIN);

  // 버튼 눌림 감지 (HIGH→LOW, 풀업 기준)
  if (lastButtonState == HIGH && currentButtonState == LOW) {
    if (!humanDetected) { // 사람이 감지되지 않았을 때만 버튼 동작 허용
      motorAllowed = !motorAllowed; // 모터 가동 승인 상태 토글
      Serial.print("[CTRL] 버튼 입력 → 모터 ");
      Serial.println(motorAllowed ? "가동 승인" : "정지 명령");
    } else {
      Serial.println("[CTRL] 버튼 입력 무시 → 사람 감지 중");
    }
  }

  lastButtonState = currentButtonState; // 현재 버튼 상태 저장
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
    // 사람 없음 + 버튼 승인 + 모터 정지 상태 → 모터 가동
    motorForward();
    motorRunning = true;
  }
  else if (!motorAllowed && motorRunning) {
    // 버튼으로 정지 명령 (motorAllowed가 false가 되면)
    motorStop();
    motorRunning = false;
  }
}

// ========== 모터 드라이버 함수 ==========
void motorForward() {
  digitalWrite(IN1_PIN, HIGH); // 모터 정방향 회전
  digitalWrite(IN2_PIN, LOW);
  analogWrite(ENA_PIN, MOTOR_SPEED); // 설정된 속도로 모터 회전
  Serial.println("[MOTOR] 정방향 회전 시작 (360° 연속)");
}

void motorStop() {
  digitalWrite(IN1_PIN, LOW); // 모터 정지
  digitalWrite(IN2_PIN, LOW);
  analogWrite(ENA_PIN, 0); // 모터 속도 0
  Serial.println("[MOTOR] 정지");
}
