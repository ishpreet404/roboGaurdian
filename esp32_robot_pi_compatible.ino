/*
  ESP32 Simple & Reliable Serial Car (NO PWM) - Pi Compatible Version
  - Serial UART commands: F, B, L, R, S (from Raspberry Pi)
  - Obstacle avoidance logic UNCHANGED (works perfectly)
  - Motor control is pure digital (no PWM)
  - Added STATUS PANEL with LEDs
  - Compatible with Pi /dev/ttyS0 communication
  
  Hardware Setup:
  - Pi GPIO14 (/dev/ttyS0 TX) → ESP32 GPIO3 (RX0)
  - Pi GPIO15 (/dev/ttyS0 RX) ← ESP32 GPIO1 (TX0)
  - Pi GND → ESP32 GND
  
  Serial Ports:
  - Serial (GPIO1/3): Pi communication at 9600 baud
  - Serial Monitor: Use USB for debugging if needed
*/

#include <Arduino.h>
#include <ctype.h>

// ===== CONFIG (UNCHANGED) =====
const int SAFE_DISTANCE = 30;                // cm
const unsigned long SENSOR_INTERVAL = 40UL;  // ms between sensor updates
const int NUM_SAMPLES = 2;                   // fewer samples for speed
const unsigned long PULSE_TIMEOUT = 6000UL;  // µs (~1 m max range)

// ===== MOTOR PINS (UNCHANGED) =====
const int LEFT_PIN_A  = 21;
const int LEFT_PIN_B  = 22;
const int RIGHT_PIN_A = 23;
const int RIGHT_PIN_B = 19;
const int TRIG_PIN = 32;
const int ECHO_PIN = 33;

// ===== STATUS PANEL PINS (UNCHANGED) =====
const int LED_FWD   = 25;
const int LED_BACK  = 26;
const int LED_LEFT  = 27;
const int LED_RIGHT = 14;
const int LED_RX    = 12;
const int LED_OBS   = 13;
// Power LED: connect directly to 3.3V or 5V (no code needed)

// ===== PI COMMUNICATION PINS =====
// Using UART0 (default Serial) - GPIO1/3
// GPIO3 = RX0, GPIO1 = TX0 (built-in Serial)

// ===== STATE (UNCHANGED) =====
enum MotorState { MS_STOP, MS_FORWARD, MS_BACKWARD, MS_LEFT, MS_RIGHT };
MotorState currentState = MS_STOP;
MotorState requestedState = MS_STOP;
bool autoReverseActive = false;

int lastDistance = 999;
unsigned long lastSensorMillis = 0;
const bool DEBUG = true;

// ===== MOTOR HELPERS (UNCHANGED) =====
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

// ===== STATUS PANEL HELPERS (UNCHANGED) =====
void updateDirectionLEDs(MotorState s) {
  digitalWrite(LED_FWD,   (s == MS_FORWARD));
  digitalWrite(LED_BACK,  (s == MS_BACKWARD));
  digitalWrite(LED_LEFT,  (s == MS_LEFT));
  digitalWrite(LED_RIGHT, (s == MS_RIGHT));
}

// ===== ULTRASONIC (COMPLETELY UNCHANGED) =====
int getDistanceRaw() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  unsigned long dur = pulseIn(ECHO_PIN, HIGH, PULSE_TIMEOUT);
  if (dur == 0UL) return -1; // no echo
  return (int)(dur * 0.0343f / 2.0f);
}

int getDistanceFiltered() {
  long sum = 0;
  int valid = 0;
  for (int i = 0; i < NUM_SAMPLES; i++) {
    int d = getDistanceRaw();
    if (d > 0 && d < 100) { // only trust up to 100 cm
      sum += d;
      valid++;
    }
    delayMicroseconds(300); // tiny pause between samples
  }
  if (valid == 0) return 999;
  return (int)(sum / valid);
}

// ===== SETUP =====
void setup() {
  // Serial (UART0) for Pi communication at 9600 baud (GPIO1/3)
  Serial.begin(9600);

  pinMode(LEFT_PIN_A, OUTPUT);
  pinMode(LEFT_PIN_B, OUTPUT);
  pinMode(RIGHT_PIN_A, OUTPUT);
  pinMode(RIGHT_PIN_B, OUTPUT);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  // Status panel pins
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
    Serial.println("ESP32 Robot Ready - UART0 (GPIO1/3) at 9600 baud");
    Serial.print("Initial distance: "); 
    Serial.println(lastDistance);
  }
  
  // Send ready signal to Pi
  Serial.println("ESP32_READY");
}

// ===== LOOP =====
void loop() {
  unsigned long now = millis();

  // 1) Handle Pi commands via Serial (UART0 - GPIO1/3)
  while (Serial.available()) {
    char c = toupper(Serial.read());
    if (c == '\n' || c == '\r') continue;

    MotorState newRequest = requestedState;
    bool validCommand = false;
    
    if (c == 'F') { newRequest = MS_FORWARD; validCommand = true; }
    else if (c == 'B') { newRequest = MS_BACKWARD; validCommand = true; }
    else if (c == 'L') { newRequest = MS_LEFT; validCommand = true; }
    else if (c == 'R') { newRequest = MS_RIGHT; validCommand = true; }
    else if (c == 'S') { newRequest = MS_STOP; validCommand = true; }

    if (validCommand && newRequest != requestedState) {
      requestedState = newRequest;
      
      // Send acknowledgment to Pi via UART0
      Serial.print("ACK:");
      Serial.println(c);
      
      if (DEBUG) { 
        // Debug output will go to Pi, but that's OK for this simple setup
        Serial.print("Pi cmd: "); 
        Serial.println(c);
      }

      // RX activity pulse
      digitalWrite(LED_RX, HIGH);
      delay(20);
      digitalWrite(LED_RX, LOW);

      // Update direction LEDs
      updateDirectionLEDs(requestedState);

      // Apply command immediately if not forward (forward is handled by obstacle logic)
      if (newRequest != MS_FORWARD) {
        autoReverseActive = false;
        applyMotorState(newRequest);
      }
    } else if (!validCommand) {
      if (DEBUG) {
        Serial.print("⚠️ Invalid command from Pi: ");
        Serial.println(c);
      }
      Serial.print("NAK:");
      Serial.println(c);
    }
  }

  // 2) Update distance fast (UNCHANGED ULTRASONIC LOGIC)
  if (now - lastSensorMillis >= SENSOR_INTERVAL) {
    lastSensorMillis = now;
    lastDistance = getDistanceFiltered();
    // Distance debug (will go to Pi via UART, but minimal output)
    if (DEBUG && (lastDistance < 40 || lastDistance > 200)) {
      Serial.print("Dist: ");
      Serial.println(lastDistance);
    }
  }

  // 3) Obstacle avoidance (COMPLETELY UNCHANGED LOGIC)
  if (lastDistance < SAFE_DISTANCE) {
    if (!autoReverseActive) {
      if (DEBUG) Serial.println("OBSTACLE!");
    }
    autoReverseActive = true;
    applyMotorState(MS_BACKWARD);
    digitalWrite(LED_OBS, HIGH);
  } else if (autoReverseActive) {
    if (DEBUG) Serial.println("CLEAR");
    autoReverseActive = false;
    applyMotorState(MS_STOP);
    digitalWrite(LED_OBS, LOW);
  } else {
    // No obstacle in safe zone
    if (requestedState == MS_FORWARD) {
      applyMotorState(MS_FORWARD);
    }
    digitalWrite(LED_OBS, LOW);
  }

  delay(2); // tiny yield
}