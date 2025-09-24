/*
  ESP32 Robot with Serial2 (GPIO16/17) - Fixed Version
  Compatible with Pi GPIO14/15 wiring
*/

#include <Arduino.h>
#include <ctype.h>

// ===== CONFIG =====
const int SAFE_DISTANCE = 30;                
const unsigned long SENSOR_INTERVAL = 40UL;  
const int NUM_SAMPLES = 2;                   
const unsigned long PULSE_TIMEOUT = 6000UL;  

// ===== MOTOR PINS =====
const int LEFT_PIN_A  = 21;
const int LEFT_PIN_B  = 22;
const int RIGHT_PIN_A = 23;
const int RIGHT_PIN_B = 19;
const int TRIG_PIN = 32;
const int ECHO_PIN = 33;

// ===== STATUS PANEL PINS =====
const int LED_FWD   = 25;
const int LED_BACK  = 26;
const int LED_LEFT  = 27;
const int LED_RIGHT = 14;
const int LED_RX    = 12;
const int LED_OBS   = 13;

// ===== UART PINS (for Pi communication) =====
const int UART_RX_PIN = 16;  // Connect to Pi GPIO14 (TX)
const int UART_TX_PIN = 17;  // Connect to Pi GPIO15 (RX)

// ===== STATE =====
enum MotorState { MS_STOP, MS_FORWARD, MS_BACKWARD, MS_LEFT, MS_RIGHT };
MotorState currentState = MS_STOP;
MotorState requestedState = MS_STOP;
bool autoReverseActive = false;

int lastDistance = 999;
unsigned long lastSensorMillis = 0;
const bool DEBUG = true;

// ===== MOTOR HELPERS =====
void setLeftForward()  { digitalWrite(LEFT_PIN_A, HIGH); digitalWrite(LEFT_PIN_B, LOW); }
void setLeftBackward() { digitalWrite(LEFT_PIN_A, LOW);  digitalWrite(LEFT_PIN_B, HIGH); }
void setLeftStop()     { digitalWrite(LEFT_PIN_A, LOW);  digitalWrite(LEFT_PIN_B, LOW); }

void setRightForward()  { digitalWrite(RIGHT_PIN_A, HIGH); digitalWrite(RIGHT_PIN_B, LOW); }
void setRightBackward() { digitalWrite(RIGHT_PIN_A, LOW);  digitalWrite(RIGHT_PIN_B, HIGH); }
void setRightStop()     { digitalWrite(RIGHT_PIN_A, LOW);  digitalWrite(RIGHT_PIN_B, LOW); }

void applyMotorState(MotorState s) {
  if (s == currentState) return;

  switch (s) {
    case MS_STOP:    setLeftStop(); setRightStop(); break;
    case MS_FORWARD: setLeftForward(); setRightForward(); break;
    case MS_BACKWARD:setLeftBackward(); setRightBackward(); break;
    case MS_LEFT:    setLeftBackward(); setRightForward(); break;
    case MS_RIGHT:   setLeftForward(); setRightBackward(); break;
  }

  currentState = s;
  if (DEBUG) {
    Serial.print("Motor state -> ");
    switch (s) {
      case MS_STOP: Serial.println("STOP"); break;
      case MS_FORWARD: Serial.println("FORWARD"); break;
      case MS_BACKWARD: Serial.println("BACKWARD"); break;
      case MS_LEFT: Serial.println("LEFT"); break;
      case MS_RIGHT: Serial.println("RIGHT"); break;
    }
  }
}

void updateDirectionLEDs(MotorState s) {
  digitalWrite(LED_FWD,   (s == MS_FORWARD));
  digitalWrite(LED_BACK,  (s == MS_BACKWARD));
  digitalWrite(LED_LEFT,  (s == MS_LEFT));
  digitalWrite(LED_RIGHT, (s == MS_RIGHT));
}

// ===== ULTRASONIC =====
int getDistanceRaw() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  unsigned long dur = pulseIn(ECHO_PIN, HIGH, PULSE_TIMEOUT);
  if (dur == 0UL) return -1;
  return (int)(dur * 0.0343f / 2.0f);
}

int getDistanceFiltered() {
  long sum = 0;
  int valid = 0;
  for (int i = 0; i < NUM_SAMPLES; i++) {
    int d = getDistanceRaw();
    if (d > 0 && d < 100) {
      sum += d;
      valid++;
    }
    delayMicroseconds(300);
  }
  if (valid == 0) return 999;
  return (int)(sum / valid);
}

// ===== SETUP =====
void setup() {
  // Initialize Serial for debugging (USB)
  Serial.begin(115200);
  
  // Initialize Serial2 for Pi communication at 9600 baud (GPIO16/17)
  Serial2.begin(9600, SERIAL_8N1, UART_RX_PIN, UART_TX_PIN);

  pinMode(LEFT_PIN_A, OUTPUT);
  pinMode(LEFT_PIN_B, OUTPUT);
  pinMode(RIGHT_PIN_A, OUTPUT);
  pinMode(RIGHT_PIN_B, OUTPUT);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  pinMode(LED_FWD, OUTPUT);
  pinMode(LED_BACK, OUTPUT);
  pinMode(LED_LEFT, OUTPUT);
  pinMode(LED_RIGHT, OUTPUT);
  pinMode(LED_RX, OUTPUT);
  pinMode(LED_OBS, OUTPUT);

  digitalWrite(LED_FWD, LOW);
  digitalWrite(LED_BACK, LOW);
  digitalWrite(LED_LEFT, LOW);
  digitalWrite(LED_RIGHT, LOW);
  digitalWrite(LED_RX, LOW);
  digitalWrite(LED_OBS, LOW);

  applyMotorState(MS_STOP);

  lastDistance = getDistanceFiltered();
  lastSensorMillis = millis();

  if (DEBUG) {
    Serial.println("🚗 ESP32 Robot with Serial2 (GPIO16/17) ready");
    Serial.println("📡 Pi communication on Serial2 at 9600 baud");
    Serial.print("Initial distance: "); Serial.println(lastDistance);
  }
}

// ===== LOOP =====
void loop() {
  unsigned long now = millis();

  // 1) Handle Pi commands via Serial2
  while (Serial2.available()) {
    char c = toupper(Serial2.read());
    if (c == '\n' || c == '\r') continue;

    MotorState newRequest = requestedState;
    if (c == 'F') newRequest = MS_FORWARD;
    else if (c == 'B') newRequest = MS_BACKWARD;
    else if (c == 'L') newRequest = MS_LEFT;
    else if (c == 'R') newRequest = MS_RIGHT;
    else if (c == 'S') newRequest = MS_STOP;

    if (newRequest != requestedState) {
      requestedState = newRequest;
      
      // Send acknowledgment back to Pi
      Serial2.print("ESP32_ACK:");
      Serial2.println(c);
      
      if (DEBUG) { 
        Serial.print("Pi command received: "); 
        Serial.println(c); 
      }

      // RX LED blink
      digitalWrite(LED_RX, HIGH);
      delay(20);
      digitalWrite(LED_RX, LOW);

      updateDirectionLEDs(requestedState);

      if (newRequest != MS_FORWARD) {
        autoReverseActive = false;
        applyMotorState(newRequest);
      }
    }
  }

  // 2) Update distance sensor
  if (now - lastSensorMillis >= SENSOR_INTERVAL) {
    lastSensorMillis = now;
    lastDistance = getDistanceFiltered();
    if (DEBUG) {
      Serial.print("Distance: ");
      Serial.println(lastDistance);
    }
  }

  // 3) Obstacle avoidance (always active)
  if (lastDistance < SAFE_DISTANCE) {
    autoReverseActive = true;
    applyMotorState(MS_BACKWARD);
    digitalWrite(LED_OBS, HIGH);
  } else if (autoReverseActive) {
    autoReverseActive = false;
    applyMotorState(MS_STOP);
    digitalWrite(LED_OBS, LOW);
  } else {
    if (requestedState == MS_FORWARD) {
      applyMotorState(MS_FORWARD);
    }
    digitalWrite(LED_OBS, LOW);
  }

  delay(2);
}