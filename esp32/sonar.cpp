#include "sonar.h"

static int trigPinRef = -1;
static int echoPinRef = -1;
static const unsigned long kPulseTimeoutUs = 25000UL;

void sonarInit(int trigPin, int echoPin)
{
    trigPinRef = trigPin;
    echoPinRef = echoPin;
    pinMode(trigPinRef, OUTPUT);
    pinMode(echoPinRef, INPUT);
    digitalWrite(trigPinRef, LOW);
}

float sonarReadCm()
{
    if (trigPinRef < 0 || echoPinRef < 0)
    {
        return -1.0f;
    }

    digitalWrite(trigPinRef, LOW);
    delayMicroseconds(2);
    digitalWrite(trigPinRef, HIGH);
    delayMicroseconds(10);
    digitalWrite(trigPinRef, LOW);

    unsigned long duration = pulseIn(echoPinRef, HIGH, kPulseTimeoutUs);
    if (duration == 0)
    {
        return -1.0f;
    }

    return (duration * 0.0343f) / 2.0f;
}
