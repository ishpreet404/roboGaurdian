/*
 * 🔧 ESP32 Ultrasonic Sensor Test - HC-SR04
 * ========================================
 * 
 * This is a standalone test for your ultrasonic sensor.
 * Upload this to your ESP32 to diagnose HC-SR04 issues.
 * 
 * Hardware Setup:
 * - HC-SR04 VCC → ESP32 5V (or 3.3V)
 * - HC-SR04 GND → ESP32 GND  
 * - HC-SR04 TRIG → ESP32 GPIO32
 * - HC-SR04 ECHO → ESP32 GPIO33
 * 
 * Open Serial Monitor at 115200 baud to see results
 */

const int TRIG_PIN = 32;
const int ECHO_PIN = 33;
const int LED_PIN = 2; // Built-in LED for visual feedback

void setup() {
  Serial.begin(115200);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);
  
  digitalWrite(TRIG_PIN, LOW);
  digitalWrite(LED_PIN, LOW);
  
  delay(1000);
  Serial.println();
  Serial.println("🔧 ESP32 Ultrasonic Sensor Test");
  Serial.println("===============================");
  Serial.println("Hardware Check:");
  Serial.print("TRIG_PIN: "); Serial.println(TRIG_PIN);
  Serial.print("ECHO_PIN: "); Serial.println(ECHO_PIN);
  Serial.println();
  Serial.println("Expected Wiring:");
  Serial.println("HC-SR04 VCC → ESP32 5V (or 3.3V)");
  Serial.println("HC-SR04 GND → ESP32 GND");
  Serial.println("HC-SR04 TRIG → ESP32 GPIO32");
  Serial.println("HC-SR04 ECHO → ESP32 GPIO33");
  Serial.println();
  Serial.println("Starting continuous test...");
  Serial.println("============================");
}

float getDistance() {
  // Send clean trigger pulse
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(5);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(12);
  digitalWrite(TRIG_PIN, LOW);
  
  // Measure echo pulse duration
  unsigned long duration = pulseIn(ECHO_PIN, HIGH, 30000); // 30ms timeout (~5m max)
  
  if (duration == 0) {
    return -1; // No echo received
  }
  
  // Convert to distance in cm (speed of sound = 343 m/s)
  float distance = (duration * 0.0343) / 2.0;
  return distance;
}

void loop() {
  float distance = getDistance();
  
  // Visual feedback with built-in LED
  if (distance > 0 && distance < 100) {
    digitalWrite(LED_PIN, HIGH); // LED ON for valid reading
  } else {
    digitalWrite(LED_PIN, LOW);  // LED OFF for invalid reading
  }
  
  // Print results
  Serial.print("Distance: ");
  if (distance == -1) {
    Serial.println("NO ECHO - Check wiring/power!");
  } else if (distance > 400) {
    Serial.println("OUT OF RANGE (>4m)");
  } else {
    Serial.print(distance, 1);
    Serial.println(" cm");
  }
  
  // Test pin states for debugging
  static int testCounter = 0;
  testCounter++;
  if (testCounter % 10 == 0) { // Every 10th reading
    Serial.print("Pin States - TRIG: ");
    Serial.print(digitalRead(TRIG_PIN));
    Serial.print(", ECHO: ");
    Serial.println(digitalRead(ECHO_PIN));
  }
  
  delay(500); // Test every 500ms
}