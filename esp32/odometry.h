#pragma once

#include <Arduino.h>

struct OdomState
{
    float x;
    float y;
    float distance_m;
    float speed_mps;
    float heading_deg;
};

void odomInit(OdomState *state);
void odomUpdate(OdomState *state, float speed_mps, float heading_deg, float dt);
