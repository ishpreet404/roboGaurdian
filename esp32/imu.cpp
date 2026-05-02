#include "imu.h"

#include <Wire.h>

static const uint8_t kMpuAddress = 0x68;
static const uint8_t kPwrMgmt1 = 0x6B;
static const uint8_t kAccelConfig = 0x1C;
static const uint8_t kGyroConfig = 0x1B;
static const uint8_t kAccelXoutH = 0x3B;

static float yawDeg = 0.0f;
static float pitchDeg = 0.0f;
static float rollDeg = 0.0f;
static unsigned long lastUpdateMs = 0;

static void writeRegister(uint8_t reg, uint8_t value)
{
    Wire.beginTransmission(kMpuAddress);
    Wire.write(reg);
    Wire.write(value);
    Wire.endTransmission(true);
}

void imuInit()
{
    Wire.begin();
    writeRegister(kPwrMgmt1, 0x00);
    writeRegister(kAccelConfig, 0x00);
    writeRegister(kGyroConfig, 0x00);
    lastUpdateMs = millis();
}

static bool readRaw(int16_t *values, size_t count)
{
    Wire.beginTransmission(kMpuAddress);
    Wire.write(kAccelXoutH);
    if (Wire.endTransmission(false) != 0)
    {
        return false;
    }
    Wire.requestFrom(kMpuAddress, static_cast<uint8_t>(count * 2), true);
    for (size_t i = 0; i < count; ++i)
    {
        if (Wire.available() < 2)
        {
            return false;
        }
        values[i] = (Wire.read() << 8) | Wire.read();
    }
    return true;
}

bool imuRead(ImuReading *reading)
{
    if (!reading)
    {
        return false;
    }

    int16_t raw[7] = {0};
    if (!readRaw(raw, 7))
    {
        return false;
    }

    float ax = raw[0] / 16384.0f;
    float ay = raw[1] / 16384.0f;
    float az = raw[2] / 16384.0f;
    float gx = raw[4] / 131.0f;
    float gy = raw[5] / 131.0f;
    float gz = raw[6] / 131.0f;

    unsigned long now = millis();
    float dt = (now - lastUpdateMs) / 1000.0f;
    lastUpdateMs = now;
    if (dt <= 0.0f)
    {
        dt = 0.01f;
    }

    float pitchAcc = atan2(ay, sqrt(ax * ax + az * az)) * 57.2958f;
    float rollAcc = atan2(-ax, az) * 57.2958f;

    pitchDeg = 0.98f * (pitchDeg + gx * dt) + 0.02f * pitchAcc;
    rollDeg = 0.98f * (rollDeg + gy * dt) + 0.02f * rollAcc;
    yawDeg += gz * dt;

    reading->ax = ax;
    reading->ay = ay;
    reading->az = az;
    reading->gx = gx;
    reading->gy = gy;
    reading->gz = gz;
    reading->yaw_deg = yawDeg;
    reading->pitch_deg = pitchDeg;
    reading->roll_deg = rollDeg;
    return true;
}
