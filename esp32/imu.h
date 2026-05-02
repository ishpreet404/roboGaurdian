#pragma once

#include <Arduino.h>

struct ImuReading
{
    float ax;
    float ay;
    float az;
    float gx;
    float gy;
    float gz;
    float yaw_deg;
    float pitch_deg;
    float roll_deg;
};

void imuInit();
bool imuRead(ImuReading *reading);
