#pragma once

#include <Arduino.h>

void sonarInit(int trigPin, int echoPin);
float sonarReadCm();
