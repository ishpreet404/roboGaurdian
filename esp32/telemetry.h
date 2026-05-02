#pragma once

#include <Arduino.h>

#include "gps.h"
#include "imu.h"
#include "odometry.h"

struct TelemetryData
{
    ImuReading imu;
    GPSState gps;
    OdomState odom;
    float sonar_cm;
    float battery_v;
    float battery_pct;
    const char *motor_state;
    float motor_speed;
    float heading_deg;
};

String telemetryToJson(const TelemetryData &data);
