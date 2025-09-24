/*
 * ESP32 Robot Controller - UART Communication at 9600 Baud
 * ========================================================
 * 
 * Receives commands from Raspberry Pi via UART at 9600 baud rate
 * Commands: F (Forward), B (Backward), L (Left), R (Right), S (Stop)
 * 
 * Hardware Connections:
 * - ESP32 RX2 (GPIO16) → Pi TX (GPIO14, Pin 8)
 * - ESP32 TX2 (GPIO17) → Pi RX (GPIO15, Pin 10)  
 * - ESP32 GND → Pi GND (Pin 6)
 * 
 * Motor Driver Connections (L298N):
 * - Motor A: GPIO 12, 13
 * - Motor B: GPIO 14, 27
 * - Enable pins: GPIO 25, 26
 * 
 * Author: Robot Guardian System
 * Date: September 2025
 */

// Motor driver pins (L298N)
const int motorA1 = 12;    // Motor A direction
const int motorA2 = 13;    // Motor A direction  
const int motorB1 = 14;    // Motor B direction
const int motorB2 = 27;    // Motor B direction
const int enableA = 25;    // Motor A speed (PWM)
const int enableB = 26;    // Motor B speed (PWM)

// LED indicator
const int ledPin = 2;      // Built-in LED

// Motor speed settings
const int motorSpeed = 200;     // Default speed (0-255)
const int turnSpeed = 180;      // Turn speed (slightly slower)
const int pwmFreq = 1000;       // PWM frequency
const int pwmResolution = 8;    // PWM resolution (8-bit)

// Command variables
String receivedCommand = "";
String lastCommand = "S";
unsigned long lastCommandTime = 0;
const unsigned long commandTimeout = 1000; // Stop if no command for 1 second

// Statistics
unsigned long commandCount = 0;
unsigned long startTime = 0;

void setup() {
  // Initialize serial communications
  Serial.begin(115200);    // USB serial for debugging
  Serial2.begin(9600, SERIAL_8N1, 16, 17); // UART2 for Pi communication (RX=16, TX=17)
  
  // Initialize motor pins
  pinMode(motorA1, OUTPUT);
  pinMode(motorA2, OUTPUT);
  pinMode(motorB1, OUTPUT);
  pinMode(motorB2, OUTPUT);
  pinMode(enableA, OUTPUT);
  pinMode(enableB, OUTPUT);
  pinMode(ledPin, OUTPUT);
  
  // Setup PWM for motor speed control
  ledcSetup(0, pwmFreq, pwmResolution); // Channel 0 for Motor A
  ledcSetup(1, pwmFreq, pwmResolution); // Channel 1 for Motor B
  ledcAttachPin(enableA, 0);
  ledcAttachPin(enableB, 1);
  
  // Stop motors initially
  stopMotors();
  
  // Startup sequence
  digitalWrite(ledPin, HIGH);
  delay(500);
  digitalWrite(ledPin, LOW);
  delay(500);
  digitalWrite(ledPin, HIGH);
  delay(500);
  digitalWrite(ledPin, LOW);
  
  startTime = millis();
  
  Serial.println("🤖 ESP32 Robot Controller Started");
  Serial.println("================================");
  Serial.println("UART: 9600 baud on Serial2");
  Serial.println("Commands: F=Forward, B=Backward, L=Left, R=Right, S=Stop");
  Serial.println("Motor Driver: L298N");
  Serial.println("Ready for commands...");
  Serial.println();
}

void loop() {
  // Check for commands from Raspberry Pi (UART)
  if (Serial2.available() > 0) {
    char incomingByte = Serial2.read();
    
    // Process single character commands
    if (incomingByte == '\n' || incomingByte == '\r') {
      if (receivedCommand.length() > 0) {
        processCommand(receivedCommand);
        receivedCommand = "";
      }
    } else if (incomingByte >= 32 && incomingByte <= 126) { // Printable characters
      receivedCommand += incomingByte;
    }
  }
  
  // Check for commands from USB serial (debugging)
  if (Serial.available() > 0) {
    String debugCommand = Serial.readStringUntil('\n');
    debugCommand.trim();
    debugCommand.toUpperCase();
    
    if (debugCommand.length() == 1) {
      processCommand(debugCommand);
      Serial.println("Debug command processed: " + debugCommand);
    }
  }
  
  // Safety timeout - stop if no command received for too long
  if (millis() - lastCommandTime > commandTimeout && lastCommand != "S") {
    Serial.println("⚠️ Command timeout - stopping for safety");
    processCommand("S");
  }
  
  // Status LED heartbeat
  static unsigned long lastBlink = 0;
  if (millis() - lastBlink > 1000) {
    digitalWrite(ledPin, !digitalRead(ledPin));
    lastBlink = millis();
    
    // Print status every 10 seconds
    static unsigned long lastStatus = 0;
    if (millis() - lastStatus > 10000) {
      printStatus();
      lastStatus = millis();
    }
  }
  
  delay(10); // Small delay for stability
}

void processCommand(String command) {
  command.trim();
  command.toUpperCase();
  
  if (command.length() != 1) {
    return; // Invalid command
  }
  
  char cmd = command.charAt(0);
  
  // Validate command
  if (cmd != 'F' && cmd != 'B' && cmd != 'L' && cmd != 'R' && cmd != 'S') {
    Serial.println("❌ Invalid command: " + command);
    return;
  }
  
  lastCommand = command;
  lastCommandTime = millis();
  commandCount++;
  
  // Execute command
  switch (cmd) {
    case 'F':
      moveForward();
      break;
    case 'B':
      moveBackward();
      break;
    case 'L':
      turnLeft();
      break;
    case 'R':
      turnRight();
      break;
    case 'S':
      stopMotors();
      break;
  }
  
  // Send acknowledgment back to Pi
  Serial2.println("OK:" + command);
  
  // Debug output
  Serial.println("📤 Command: " + command + " (Count: " + String(commandCount) + ")");
}

void moveForward() {
  Serial.println("🔥 Moving Forward");
  
  // Motor A forward
  digitalWrite(motorA1, HIGH);
  digitalWrite(motorA2, LOW);
  ledcWrite(0, motorSpeed);
  
  // Motor B forward  
  digitalWrite(motorB1, HIGH);
  digitalWrite(motorB2, LOW);
  ledcWrite(1, motorSpeed);
  
  digitalWrite(ledPin, HIGH); // LED on when moving
}

void moveBackward() {
  Serial.println("🔥 Moving Backward");
  
  // Motor A backward
  digitalWrite(motorA1, LOW);
  digitalWrite(motorA2, HIGH);
  ledcWrite(0, motorSpeed);
  
  // Motor B backward
  digitalWrite(motorB1, LOW);
  digitalWrite(motorB2, HIGH);
  ledcWrite(1, motorSpeed);
  
  digitalWrite(ledPin, HIGH); // LED on when moving
}

void turnLeft() {
  Serial.println("🔥 Turning Left");
  
  // Motor A forward (right wheel)
  digitalWrite(motorA1, HIGH);
  digitalWrite(motorA2, LOW);
  ledcWrite(0, turnSpeed);
  
  // Motor B backward (left wheel)
  digitalWrite(motorB1, LOW);
  digitalWrite(motorB2, HIGH);
  ledcWrite(1, turnSpeed);
  
  digitalWrite(ledPin, HIGH); // LED on when moving
}

void turnRight() {
  Serial.println("🔥 Turning Right");
  
  // Motor A backward (right wheel)
  digitalWrite(motorA1, LOW);
  digitalWrite(motorA2, HIGH);
  ledcWrite(0, turnSpeed);
  
  // Motor B forward (left wheel)
  digitalWrite(motorB1, HIGH);
  digitalWrite(motorB2, LOW);
  ledcWrite(1, turnSpeed);
  
  digitalWrite(ledPin, HIGH); // LED on when moving
}

void stopMotors() {
  Serial.println("🛑 Stopping");
  
  // Stop both motors
  digitalWrite(motorA1, LOW);
  digitalWrite(motorA2, LOW);
  ledcWrite(0, 0);
  
  digitalWrite(motorB1, LOW);
  digitalWrite(motorB2, LOW);
  ledcWrite(1, 0);
  
  digitalWrite(ledPin, LOW); // LED off when stopped
}

void printStatus() {
  unsigned long uptime = (millis() - startTime) / 1000;
  
  Serial.println();
  Serial.println("📊 Robot Status Report");
  Serial.println("=====================");
  Serial.println("Uptime: " + String(uptime) + " seconds");
  Serial.println("Commands received: " + String(commandCount));
  Serial.println("Last command: " + lastCommand);
  Serial.println("UART Baud: 9600");
  Serial.println("Motor Speed: " + String(motorSpeed) + "/255");
  Serial.println("Turn Speed: " + String(turnSpeed) + "/255");
  
  // Memory info
  Serial.println("Free heap: " + String(ESP.getFreeHeap()) + " bytes");
  Serial.println();
}

// Test function for motor diagnostics
void testMotors() {
  Serial.println("🔧 Testing Motors...");
  
  Serial.println("Testing Motor A Forward");
  digitalWrite(motorA1, HIGH);
  digitalWrite(motorA2, LOW);
  ledcWrite(0, 150);
  delay(1000);
  
  Serial.println("Testing Motor A Backward");
  digitalWrite(motorA1, LOW);
  digitalWrite(motorA2, HIGH);
  ledcWrite(0, 150);
  delay(1000);
  
  Serial.println("Testing Motor B Forward");
  digitalWrite(motorB1, HIGH);
  digitalWrite(motorB2, LOW);
  ledcWrite(1, 150);
  delay(1000);
  
  Serial.println("Testing Motor B Backward");
  digitalWrite(motorB1, LOW);
  digitalWrite(motorB2, HIGH);
  ledcWrite(1, 150);
  delay(1000);
  
  stopMotors();
  Serial.println("✅ Motor test complete");
}