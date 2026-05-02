#pragma once

#include <Arduino.h>

struct GPSState
{
    float lat;
    float lon;
    float speed_mps;
    int sats;
    bool fix;
};

void gpsInit(HardwareSerial &serial, int rxPin, int txPin, uint32_t baud);
bool gpsUpdate(GPSState *state);
