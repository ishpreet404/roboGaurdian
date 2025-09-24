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

// ===== CONFIG WITH MOVEMENT TIMING =====
const int SAFE_DISTANCE = 50;                // cm - increased for better safety
const unsigned long SENSOR_INTERVAL = 40UL;  // ms between sensor updates
const int NUM_SAMPLES = 2;                   // fewer samples for speed
const unsigned long PULSE_TIMEOUT = 6000UL;  // µs (~1 m max range)
const unsigned long MOVEMENT_DURATION = 200; // ms - how long to execute each movement
const unsigned long STOP_DURATION = 100;     // ms - pause between movements
const unsigned long SEARCH_TURN_DURATION = 150; // ms - slower turns for 360 search

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

// ===== STATE WITH MOVEMENT TIMING =====
enum MotorState { MS_STOP, MS_FORWARD, MS_BACKWARD, MS_LEFT, MS_RIGHT };
MotorState currentState = MS_STOP;
MotorState requestedState = MS_STOP;
bool autoReverseActive = false;
bool isSearchMode = false; // For 360-degree search when no person found

int lastDistance = 999;
unsigned long lastSensorMillis = 0;
unsigned long movementStartTime = 0;
bool isExecutingMovement = false;
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

// ===== ULTRASONIC WITH ENHANCED DEBUGGING =====
int getDistanceRaw() {
  // Ensure clean trigger pulse
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(5);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(12);
  digitalWrite(TRIG_PIN, LOW);

  // Wait for echo with timeout
  unsigned long dur = pulseIn(ECHO_PIN, HIGH, PULSE_TIMEOUT);
  if (dur == 0UL) {
    if (DEBUG) {
      static int noEchoCount = 0;
      noEchoCount++;
      if(noEchoCount % 50 == 1) { // Log every 50th failure
        Serial.println("⚠️ NO ECHO - Check HC-SR04 wiring/power");
      }
    }
    return -1; // no echo
  }
  
  // Convert to distance (speed of sound = 343 m/s)
  float distance = (dur * 0.0343f) / 2.0f;
  return (int)distance;
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
    Serial.print("TRIG_PIN: "); Serial.println(TRIG_PIN);
    Serial.print("ECHO_PIN: "); Serial.println(ECHO_PIN);
    Serial.print("Initial distance: "); 
    Serial.println(lastDistance);
    
    // Test ultrasonic pins
    Serial.println("Testing ultrasonic sensor...");
    for(int i = 0; i < 5; i++) {
      int raw = getDistanceRaw();
      Serial.print("Test "); Serial.print(i+1); Serial.print(": ");
      if(raw == -1) {
        Serial.println("NO ECHO");
      } else {
        Serial.print(raw); Serial.println(" cm");
      }
      delay(200);
    }
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
    
    if (c == 'F') { newRequest = MS_FORWARD; validCommand = true; isSearchMode = false; }
    else if (c == 'B') { newRequest = MS_BACKWARD; validCommand = true; isSearchMode = false; }
    else if (c == 'L') { newRequest = MS_LEFT; validCommand = true; isSearchMode = false; }
    else if (c == 'R') { newRequest = MS_RIGHT; validCommand = true; isSearchMode = false; }
    else if (c == 'S') { newRequest = MS_STOP; validCommand = true; isSearchMode = false; }
    else if (c == 'X') { // Search mode - slow 360 turn
      newRequest = MS_RIGHT; 
      validCommand = true; 
      isSearchMode = true;
      if (DEBUG) Serial.println("🔍 Search mode activated");
    }

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

      // Start timed movement execution
      if (newRequest == MS_STOP) {
        // Stop immediately
        autoReverseActive = false;
        applyMotorState(MS_STOP);
        isExecutingMovement = false;
      } else {
        // Start timed movement
        movementStartTime = millis();
        isExecutingMovement = true;
        if (newRequest != MS_FORWARD) {
          autoReverseActive = false;
          applyMotorState(newRequest);
        }
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

  // 2) Update distance fast with enhanced debugging
  if (now - lastSensorMillis >= SENSOR_INTERVAL) {
    lastSensorMillis = now;
    int rawDist = getDistanceRaw();
    lastDistance = getDistanceFiltered();
    
    // Enhanced distance debug
    if (DEBUG) {
      static int debugCounter = 0;
      debugCounter++;
      if(debugCounter % 25 == 0) { // Every ~1 second at 40ms intervals
        Serial.print("Raw: "); Serial.print(rawDist);
        Serial.print(" cm, Filtered: "); Serial.print(lastDistance);
        if(rawDist == -1) Serial.print(" [NO_ECHO]");
        if(lastDistance == 999) Serial.print(" [INVALID]");
        Serial.println();
      }
    }
  }

  // 3) Handle timed movements
  if (isExecutingMovement && !autoReverseActive) {
    unsigned long elapsed = millis() - movementStartTime;
    unsigned long targetDuration = isSearchMode ? SEARCH_TURN_DURATION : MOVEMENT_DURATION;
    
    if (elapsed >= targetDuration) {
      // Movement time completed, stop and wait
      applyMotorState(MS_STOP);
      isExecutingMovement = false;
      
      if (DEBUG) {
        if (isSearchMode) {
          Serial.println("🔍 Search turn completed, pausing");
        } else {
          Serial.print("Movement completed, stopping for ");
          Serial.print(STOP_DURATION);
          Serial.println("ms");
        }
      }
      
      // Brief pause for frame processing (longer for search mode)
      unsigned long pauseDuration = isSearchMode ? (STOP_DURATION + 50) : STOP_DURATION;
      delay(pauseDuration);
    }
  }

  // 4) Obstacle avoidance (overrides timed movements)
  if (lastDistance < SAFE_DISTANCE) {
    if (!autoReverseActive) {
      if (DEBUG) Serial.println("OBSTACLE!");
    }
    autoReverseActive = true;
    isExecutingMovement = false; // Cancel any timed movement
    applyMotorState(MS_BACKWARD);
    digitalWrite(LED_OBS, HIGH);
  } else if (autoReverseActive) {
    if (DEBUG) Serial.println("CLEAR");
    autoReverseActive = false;
    applyMotorState(MS_STOP);
    digitalWrite(LED_OBS, LOW);
  } else {
    // No obstacle in safe zone - handle forward movement
    if (requestedState == MS_FORWARD && isExecutingMovement) {
      applyMotorState(MS_FORWARD);
    }
    digitalWrite(LED_OBS, LOW);
  }

  delay(2); // tiny yield
}