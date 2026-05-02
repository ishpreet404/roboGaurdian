#include <Arduino.h>

#include "gps.h"
#include "imu.h"
#include "motor.h"
#include "odometry.h"
#include "sonar.h"
#include "telemetry.h"

static const int PI_RX_PIN = 16;
static const int PI_TX_PIN = 17;
static const int GPS_RX_PIN = 32;
static const int GPS_TX_PIN = 4;
static const int SONAR_TRIG_PIN = 5;
static const int SONAR_ECHO_PIN = 18;

static const float MAX_SPEED_MPS = 0.45f;
static const float SAFE_DISTANCE_CM = 35.0f;

static const unsigned long TELEMETRY_INTERVAL_MS = 200;
static const unsigned long SENSOR_INTERVAL_MS = 60;

HardwareSerial PiSerial(2);
HardwareSerial GPSSerial(1);

static String commandBuffer;
static MotorCommand currentCommand = MOTOR_STOP;
static bool autoAvoidActive = false;
static unsigned long autoAvoidUntil = 0;

static ImuReading imuReading{};
static GPSState gpsState{};
static OdomState odomState{};

static float sonarCm = -1.0f;
static unsigned long lastSensorMs = 0;
static unsigned long lastTelemetryMs = 0;
static unsigned long lastOdomMs = 0;

static MotorCommand parseCommand(const String &cmd)
{
    String trimmed = cmd;
    trimmed.trim();
    trimmed.toLowerCase();

    if (trimmed.startsWith("cmd:"))
    {
        trimmed = trimmed.substring(4);
        trimmed.trim();
    }

    if (trimmed == "forward" || trimmed == "f")
        return MOTOR_FORWARD;
    if (trimmed == "backward" || trimmed == "b")
        return MOTOR_BACKWARD;
    if (trimmed == "left" || trimmed == "l")
        return MOTOR_LEFT;
    if (trimmed == "right" || trimmed == "r")
        return MOTOR_RIGHT;
    if (trimmed == "stop" || trimmed == "s")
        return MOTOR_STOP;

    return MOTOR_STOP;
}

static const char *commandName(MotorCommand cmd)
{
    switch (cmd)
    {
    case MOTOR_FORWARD:
        return "forward";
    case MOTOR_BACKWARD:
        return "backward";
    case MOTOR_LEFT:
        return "left";
    case MOTOR_RIGHT:
        return "right";
    case MOTOR_STOP:
    default:
        return "stop";
    }
}

static void applyCommand(MotorCommand cmd)
{
    currentCommand = cmd;
    int speed = (cmd == MOTOR_STOP) ? 0 : 180;
    motorSetCommand(cmd, speed);
}

static void handleIncomingCommands()
{
    while (PiSerial.available())
    {
        char c = PiSerial.read();
        if (c == '\n' || c == '\r')
        {
            if (commandBuffer.length() > 0)
            {
                MotorCommand cmd = parseCommand(commandBuffer);
                applyCommand(cmd);
                commandBuffer = "";
            }
        }
        else if (commandBuffer.length() < 32)
        {
            commandBuffer += c;
        }
    }
}

static void updateOdometry(float headingDeg, float dt)
{
    float speed = (motorGetSpeed() / 255.0f) * MAX_SPEED_MPS;
    if (currentCommand == MOTOR_BACKWARD)
    {
        speed = -speed;
    }
    odomUpdate(&odomState, speed, headingDeg, dt);
}

static void sendAlert(const char *message)
{
    String json = "{\"id\":\"obs-" + String(millis()) + "\",";
    json += "\"level\":\"warning\",";
    json += "\"message\":\"" + String(message) + "\"}";
    PiSerial.print("AL:");
    PiSerial.println(json);
}

void setup()
{
    Serial.begin(115200);
    PiSerial.begin(115200, SERIAL_8N1, PI_RX_PIN, PI_TX_PIN);
    gpsInit(GPSSerial, GPS_RX_PIN, GPS_TX_PIN, 9600);

    motorInit();
    sonarInit(SONAR_TRIG_PIN, SONAR_ECHO_PIN);
    imuInit();
    odomInit(&odomState);

    lastOdomMs = millis();
}

void loop()
{
    handleIncomingCommands();

    unsigned long now = millis();
    if (now - lastSensorMs >= SENSOR_INTERVAL_MS)
    {
        lastSensorMs = now;
        imuRead(&imuReading);
        gpsUpdate(&gpsState);
        sonarCm = sonarReadCm();
    }

    float headingDeg = imuReading.yaw_deg;
    if (now - lastOdomMs >= 40)
    {
        float dt = (now - lastOdomMs) / 1000.0f;
        lastOdomMs = now;
        updateOdometry(headingDeg, dt);
    }

    if (!autoAvoidActive && sonarCm > 0.0f && sonarCm < SAFE_DISTANCE_CM && currentCommand == MOTOR_FORWARD)
    {
        autoAvoidActive = true;
        autoAvoidUntil = now + 350;
        motorSetCommand(MOTOR_BACKWARD, 170);
        sendAlert("Obstacle detected, reversing");
    }

    if (autoAvoidActive && now > autoAvoidUntil)
    {
        autoAvoidActive = false;
        applyCommand(MOTOR_STOP);
    }

    if (now - lastTelemetryMs >= TELEMETRY_INTERVAL_MS)
    {
        lastTelemetryMs = now;
        TelemetryData data{};
        data.imu = imuReading;
        data.gps = gpsState;
        data.odom = odomState;
        data.sonar_cm = sonarCm;
        data.battery_v = 0.0f;
        data.battery_pct = 0.0f;
        data.motor_state = commandName(currentCommand);
        data.motor_speed = static_cast<float>(motorGetSpeed());
        data.heading_deg = headingDeg;

        String payload = telemetryToJson(data);
        PiSerial.print("TL:");
        PiSerial.println(payload);
    }
}
