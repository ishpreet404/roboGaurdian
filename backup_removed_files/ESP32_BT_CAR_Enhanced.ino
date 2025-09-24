/*
  Enhanced ESP32 Robot Controller with Improved Bluetooth
  ======================================================
  
  Upload this to your ESP32 to fix connection issues.
  This version has better connection handling and debugging.
  
  Hardware connections:
  - Motor pins can be adjusted in the defines below
  - Built-in LED will indicate Bluetooth status
*/

#include "BluetoothSerial.h"

BluetoothSerial SerialBT;

// Motor pins - adjust these to match your robot wiring
#define MOTOR_LEFT_FWD   2   // Left motor forward
#define MOTOR_LEFT_BWD   4   // Left motor backward  
#define MOTOR_RIGHT_FWD  16  // Right motor forward
#define MOTOR_RIGHT_BWD  17  // Right motor backward

// Built-in LED for status indication
#define LED_PIN 2

// Bluetooth connection status
bool bluetoothConnected = false;
unsigned long lastHeartbeat = 0;
unsigned long lastCommandTime = 0;

void setup() {
  Serial.begin(115200);
  
  // Initialize LED
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  
  // Initialize motor pins
  pinMode(MOTOR_LEFT_FWD, OUTPUT);
  pinMode(MOTOR_LEFT_BWD, OUTPUT);
  pinMode(MOTOR_RIGHT_FWD, OUTPUT);
  pinMode(MOTOR_RIGHT_BWD, OUTPUT);
  
  // Stop all motors initially
  stopMotors();
  
  Serial.println("🤖 ESP32 Robot Controller Starting...");
  Serial.println("=" * 40);
  
  // Initialize Bluetooth with improved settings
  if (!SerialBT.begin("BT_CAR_32")) {
    Serial.println("❌ Bluetooth initialization failed!");
    // Blink LED rapidly if Bluetooth fails
    for(int i = 0; i < 10; i++) {
      digitalWrite(LED_PIN, HIGH);
      delay(100);
      digitalWrite(LED_PIN, LOW);
      delay(100);
    }
  } else {
    Serial.println("✅ Bluetooth initialized successfully");
    Serial.println("📡 Device name: BT_CAR_32");
    Serial.println("📍 MAC Address: " + SerialBT.getMacString());
    Serial.println("🔗 Waiting for connection...");
    
    // Slow blink to indicate ready for pairing
    digitalWrite(LED_PIN, HIGH);
    delay(500);
    digitalWrite(LED_PIN, LOW);
  }
  
  // Set Bluetooth callback functions
  SerialBT.onConnect(bluetoothConnected_callback);
  SerialBT.onDisconnect(bluetoothDisconnected_callback);
  
  Serial.println("🚀 Robot ready for commands!");
  Serial.println("Commands: F=Forward, B=Backward, L=Left, R=Right, S=Stop");
}

void loop() {
  // Handle Bluetooth commands
  if (SerialBT.available()) {
    String command = SerialBT.readStringUntil('\n');
    command.trim(); // Remove whitespace
    
    if (command.length() > 0) {
      handleCommand(command[0]); // Use first character
      lastCommandTime = millis();
    }
  }
  
  // Handle Serial commands (for debugging)
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command.length() > 0) {
      Serial.println("Debug command: " + command);
      handleCommand(command[0]);
    }
  }
  
  // Safety: Auto-stop if no command received for 5 seconds
  if (millis() - lastCommandTime > 5000 && lastCommandTime > 0) {
    stopMotors();
    lastCommandTime = 0; // Reset to avoid repeated stops
    Serial.println("⚠️ Auto-stop: No commands for 5 seconds");
  }
  
  // Heartbeat and LED status
  updateStatusLED();
  
  // Send periodic heartbeat if connected
  if (bluetoothConnected && millis() - lastHeartbeat > 10000) {
    SerialBT.println("HEARTBEAT:OK");
    lastHeartbeat = millis();
  }
  
  delay(50); // Small delay to prevent overwhelming the processor
}

void handleCommand(char cmd) {
  Serial.print("📥 Received command: ");
  Serial.println(cmd);
  
  // Convert to uppercase for consistency
  cmd = toupper(cmd);
  
  switch(cmd) {
    case 'F': // Forward
      moveForward();
      break;
      
    case 'B': // Backward
      moveBackward();
      break;
      
    case 'L': // Left
      turnLeft();
      break;
      
    case 'R': // Right
      turnRight();
      break;
      
    case 'S': // Stop
      stopMotors();
      break;
      
    case 'T': // Test command
      testMotors();
      break;
      
    default:
      Serial.println("❌ Unknown command: " + String(cmd));
      stopMotors(); // Safety: stop on unknown command
      SerialBT.println("ERROR:UNKNOWN_COMMAND");
      return;
  }
  
  // Send acknowledgment
  SerialBT.print("OK:");
  SerialBT.println(cmd);
  
  Serial.println("✅ Command executed successfully");
}

void moveForward() {
  digitalWrite(MOTOR_LEFT_FWD, HIGH);
  digitalWrite(MOTOR_LEFT_BWD, LOW);
  digitalWrite(MOTOR_RIGHT_FWD, HIGH);
  digitalWrite(MOTOR_RIGHT_BWD, LOW);
  Serial.println("🏃 Moving forward");
}

void moveBackward() {
  digitalWrite(MOTOR_LEFT_FWD, LOW);
  digitalWrite(MOTOR_LEFT_BWD, HIGH);
  digitalWrite(MOTOR_RIGHT_FWD, LOW);
  digitalWrite(MOTOR_RIGHT_BWD, HIGH);
  Serial.println("🔙 Moving backward");
}

void turnLeft() {
  digitalWrite(MOTOR_LEFT_FWD, LOW);
  digitalWrite(MOTOR_LEFT_BWD, HIGH);
  digitalWrite(MOTOR_RIGHT_FWD, HIGH);
  digitalWrite(MOTOR_RIGHT_BWD, LOW);
  Serial.println("↩️ Turning left");
}

void turnRight() {
  digitalWrite(MOTOR_LEFT_FWD, HIGH);
  digitalWrite(MOTOR_LEFT_BWD, LOW);
  digitalWrite(MOTOR_RIGHT_FWD, LOW);
  digitalWrite(MOTOR_RIGHT_BWD, HIGH);
  Serial.println("↪️ Turning right");
}

void stopMotors() {
  digitalWrite(MOTOR_LEFT_FWD, LOW);
  digitalWrite(MOTOR_LEFT_BWD, LOW);
  digitalWrite(MOTOR_RIGHT_FWD, LOW);
  digitalWrite(MOTOR_RIGHT_BWD, LOW);
  Serial.println("🛑 Motors stopped");
}

void testMotors() {
  Serial.println("🧪 Testing all motors...");
  
  Serial.println("Testing forward...");
  moveForward();
  delay(1000);
  
  Serial.println("Testing backward...");
  moveBackward();
  delay(1000);
  
  Serial.println("Testing left...");
  turnLeft();
  delay(1000);
  
  Serial.println("Testing right...");
  turnRight();
  delay(1000);
  
  Serial.println("Stopping...");
  stopMotors();
  
  Serial.println("✅ Motor test completed");
  SerialBT.println("TEST:COMPLETED");
}

void bluetoothConnected_callback(uint16_t handle) {
  bluetoothConnected = true;
  Serial.println("🔗 Bluetooth client connected!");
  SerialBT.println("CONNECTED:BT_CAR_32");
  
  // Fast blink to indicate connection
  for(int i = 0; i < 6; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(100);
    digitalWrite(LED_PIN, LOW);
    delay(100);
  }
}

void bluetoothDisconnected_callback(uint16_t handle) {
  bluetoothConnected = false;
  Serial.println("📱 Bluetooth client disconnected");
  
  // Safety: Stop motors when disconnected
  stopMotors();
  
  // Slow blink to indicate ready for new connection
  digitalWrite(LED_PIN, LOW);
}

void updateStatusLED() {
  static unsigned long lastLedUpdate = 0;
  static bool ledState = false;
  
  if (millis() - lastLedUpdate > 1000) { // Update every second
    if (bluetoothConnected) {
      // Solid on when connected
      digitalWrite(LED_PIN, HIGH);
    } else {
      // Slow blink when waiting for connection
      ledState = !ledState;
      digitalWrite(LED_PIN, ledState);
    }
    lastLedUpdate = millis();
  }
}

// Debug function to print status
void printStatus() {
  Serial.println("\n📊 ESP32 Status:");
  Serial.println("Bluetooth: " + String(bluetoothConnected ? "Connected" : "Waiting"));
  Serial.println("MAC: " + SerialBT.getMacString());
  Serial.println("Name: BT_CAR_32");
  Serial.println("Uptime: " + String(millis() / 1000) + "s");
  Serial.println("========================\n");
}