#include <Servo.h>

// Pin definitions
const int SERVO_PIN = 9;
const int LED_PIN = 13;  // Built-in LED on most Arduinos

// Servo and state
Servo myservo;
int currentAngle = 90;
int targetAngle = 90;

// Smoothing: average last N commands (simple moving average)
const int SMOOTH_WINDOW = 3;
int angleHistory[SMOOTH_WINDOW];
int historyIndex = 0;
bool historyFull = false;

// LED states
enum LedState { IDLE, TRACKING, SEARCHING };
LedState ledState = IDLE;

void setup() {
  Serial.begin(9600);
  while (!Serial) {
    ; // Wait for serial port to connect (for native USB only)
  }

  myservo.attach(SERVO_PIN);
  pinMode(LED_PIN, OUTPUT);

  // Initialize history
  for (int i = 0; i < SMOOTH_WINDOW; i++) {
    angleHistory[i] = 90;
  }

  Serial.println("READY");  // Signal that Arduino is ready
  digitalWrite(LED_PIN, HIGH);
  delay(100);
  digitalWrite(LED_PIN, LOW);

  setLedState(IDLE);
}

void loop() {
  // Check for serial commands
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();

    if (input.startsWith("ANGLE:")) {
      // New format: ANGLE:90
      int newAngle = input.substring(6).toInt();
      setTargetAngle(newAngle);
    } else if (input.length() <= 3 && input.toInt() >= 0 && input.toInt() <= 180) {
      // Legacy: just send angle directly
      setTargetAngle(input.toInt());
    }
  }

  // Smooth and update servo
  smoothAndMove();

  delay(10);  // Small delay to prevent overwhelming serial
}

void setTargetAngle(int angle) {
  // Constrain angle
  angle = constrain(angle, 0, 180);
  targetAngle = angle;

  // Update LED based on angle movement
  if (abs(targetAngle - currentAngle) > 2) {
    setLedState(TRACKING);
  } else {
    setLedState(IDLE);
  }
}

void smoothAndMove() {
  // Add to history
  angleHistory[historyIndex] = targetAngle;
  historyIndex = (historyIndex + 1) % SMOOTH_WINDOW;
  if (historyIndex == 0) historyFull = true;

  // Calculate average
  long sum = 0;
  int count = historyFull ? SMOOTH_WINDOW : historyIndex;
  for (int i = 0; i < count; i++) {
    sum += angleHistory[i];
  }

  int avgAngle = sum / count;
  avgAngle = constrain(avgAngle, 0, 180);

  // Only move if difference is significant (<0.5 degree)
  if (abs(avgAngle - currentAngle) >= 0.5) {
    myservo.write(avgAngle);
    currentAngle = avgAngle;
  }
}

void setLedState(LedState state) {
  if (ledState == state) return;  // No change
  ledState = state;

  switch (state) {
    case IDLE:
      digitalWrite(LED_PIN, LOW);  // Off
      break;
    case TRACKING:
      digitalWrite(LED_PIN, HIGH);  // Solid on
      break;
    case SEARCHING:
      // Blink slowly (handled in loop if needed)
      digitalWrite(LED_PIN, HIGH);
      break;
  }
}

// Optional: Blink LED for debugging
void blinkLed(int times, int delayMs = 100) {
  for (int i = 0; i < times; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(delayMs);
    digitalWrite(LED_PIN, LOW);
    delay(delayMs);
  }
}
