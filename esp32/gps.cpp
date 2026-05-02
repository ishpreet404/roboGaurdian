#include "gps.h"

#include <TinyGPSPlus.h>

static TinyGPSPlus gps;
static HardwareSerial *gpsSerial = nullptr;

void gpsInit(HardwareSerial &serial, int rxPin, int txPin, uint32_t baud)
{
    gpsSerial = &serial;
    gpsSerial->begin(baud, SERIAL_8N1, rxPin, txPin);
}

bool gpsUpdate(GPSState *state)
{
    if (!gpsSerial || !state)
    {
        return false;
    }

    while (gpsSerial->available())
    {
        gps.encode(gpsSerial->read());
    }

    state->fix = gps.location.isValid();
    if (state->fix)
    {
        state->lat = gps.location.lat();
        state->lon = gps.location.lng();
    }

    state->speed_mps = gps.speed.isValid() ? gps.speed.mps() : 0.0f;
    state->sats = gps.satellites.isValid() ? gps.satellites.value() : 0;
    return state->fix;
}
