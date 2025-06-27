#include <Servo.h>

Servo myservo;
int angle = 90;

void setup() {
  Serial.begin(9600);
  myservo.attach(9);
  myservo.write(angle);
}

void loop() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    angle = input.toInt();
    angle = constrain(angle, 0, 180);
    myservo.write(angle);
  }
}
